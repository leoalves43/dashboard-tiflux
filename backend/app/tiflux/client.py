"""Thin read-only client for the Tiflux REST API v2 (pagination + rate limit handling)."""

import logging
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

import httpx

log = logging.getLogger(__name__)

JsonObject = dict[str, Any]
PAGE_SIZE = 200  # API maximum
_MAX_ATTEMPTS = 6
_FALLBACK_WAIT_SECONDS = 30.0


@dataclass(frozen=True)
class Page:
    items: list[JsonObject]
    total: int


class TifluxSource(Protocol):
    """What the sync needs from Tiflux; implemented by TifluxClient and test fakes."""

    def fetch_page(self, path: str, params: dict[str, str | int]) -> Page: ...

    def iter_pages(self, path: str, params: dict[str, str | int]) -> Iterator[list[JsonObject]]: ...


class TifluxApiError(RuntimeError):
    pass


def seconds_until_reset(reset_header: str | None, now: datetime) -> float:
    """RateLimit-Reset is a datetime; returns how long to wait (fallback when absent/unparseable)."""
    if not reset_header:
        return _FALLBACK_WAIT_SECONDS
    try:
        reset_at = datetime.fromisoformat(reset_header)
    except ValueError:
        return _FALLBACK_WAIT_SECONDS
    if reset_at.tzinfo is None:
        reset_at = reset_at.replace(tzinfo=UTC)
    return max(1.0, (reset_at - now).total_seconds() + 1.0)


class TifluxClient:
    """Example: TifluxClient(url, token).iter_pages("/tickets", {"filter_by": "all"})"""

    def __init__(
        self,
        base_url: str,
        token: str,
        http: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._http = http or httpx.Client(timeout=60.0)
        self._base_url = base_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        self._sleep = sleep

    def fetch_page(self, path: str, params: dict[str, str | int]) -> Page:
        response = self._get_with_retry(path, params)
        items = response.json()
        if not isinstance(items, list):
            raise TifluxApiError(f"GET {path} returned {type(items).__name__}; expected JSON list")
        total = int(response.headers.get("X-Total-Items", len(items)))
        return Page(items=items, total=total)

    def iter_pages(self, path: str, params: dict[str, str | int]) -> Iterator[list[JsonObject]]:
        """Yields pages until a short page; Tiflux `offset` is the 1-based page number."""
        offset = 1
        while True:
            page = self.fetch_page(path, {**params, "limit": PAGE_SIZE, "offset": offset})
            if page.items:
                yield page.items
            if len(page.items) < PAGE_SIZE:
                return
            offset += 1

    def _get_with_retry(self, path: str, params: dict[str, str | int]) -> httpx.Response:
        url = f"{self._base_url}{path}"
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            response = self._try_get(url, params)
            if response is not None and response.status_code < 400:
                self._respect_remaining_quota(response)
                return response
            if response is not None and response.status_code not in (429, 500, 502, 503, 504):
                raise TifluxApiError(f"GET {path} params={params} -> {response.status_code}: {response.text[:300]}")
            self._sleep(self._retry_wait(response, attempt))
        raise TifluxApiError(f"GET {path} params={params} failed after {_MAX_ATTEMPTS} attempts")

    def _try_get(self, url: str, params: dict[str, str | int]) -> httpx.Response | None:
        try:
            return self._http.get(url, params=params, headers=self._headers)
        except httpx.TransportError as error:
            log.warning("tiflux transport error url=%s error=%s", url, error)
            return None

    def _retry_wait(self, response: httpx.Response | None, attempt: int) -> float:
        if response is not None and response.status_code == 429:
            return seconds_until_reset(response.headers.get("RateLimit-Reset"), datetime.now(UTC))
        return min(60.0, 2.0**attempt)

    def _respect_remaining_quota(self, response: httpx.Response) -> None:
        remaining = response.headers.get("RateLimit-Remaining")
        if remaining is None or int(remaining) > 1:
            return
        wait = seconds_until_reset(response.headers.get("RateLimit-Reset"), datetime.now(UTC))
        log.info("tiflux rate limit reached; waiting %.0fs", wait)
        self._sleep(wait)
