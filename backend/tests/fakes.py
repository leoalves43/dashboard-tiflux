"""Named fakes for external I/O: Tiflux HTTP, Tiflux source and the sync store."""

from collections.abc import Callable, Iterator, Sequence
from datetime import datetime
from typing import Any

import httpx
from sqlalchemy import Table

from app.tiflux.client import PAGE_SIZE, JsonObject, Page


class FakeTifluxHttp:
    """Serves queued responses to httpx.MockTransport and records every request."""

    def __init__(self, responses: list[httpx.Response]) -> None:
        self._responses = responses
        self.requests: list[httpx.Request] = []

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self._responses.pop(0)

    def client(self) -> httpx.Client:
        return httpx.Client(transport=httpx.MockTransport(self.handle))


class FakeSleeper:
    def __init__(self) -> None:
        self.waits: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.waits.append(seconds)


def make_ticket(number: int, created_at: str, **overrides: Any) -> JsonObject:
    ticket: JsonObject = {
        "ticket_number": number,
        "title": f"Chamado {number}",
        "is_closed": False,
        "created_at": created_at,
        "updated_at": created_at,
        "status": {"id": 1, "name": "Opened"},
        "stage": {"id": 2, "name": "Pending"},
        "priority": {"id": 3, "name": "Alta"},
        "desk": {"id": 10, "name": "SUPORTE"},
        "client": {"id": 20, "name": "Cliente A"},
        "responsible": {"id": 30, "name": "Técnico X"},
        "requestor": {"id": None, "name": "Fulano", "email": "f@x.test"},
        "services_catalog": None,
        "sla_info": {"solve_expiration": None, "stage_expiration": None, "solved_in_time": None,
                     "attend_expiration": None, "stopped": False},
    }
    ticket.update(overrides)
    return ticket


class FakeTifluxSource:
    """In-memory Tiflux: `tickets_for(params)` decides which tickets a /tickets query returns."""

    def __init__(self, tickets_for: Callable[[dict[str, str | int]], list[JsonObject]],
                 dimensions: dict[str, list[JsonObject]] | None = None) -> None:
        self._tickets_for = tickets_for
        self._dimensions = dimensions or {}
        self.calls: list[tuple[str, dict[str, str | int]]] = []

    def _items(self, path: str, params: dict[str, str | int]) -> list[JsonObject]:
        self.calls.append((path, dict(params)))
        if path == "/tickets":
            return self._tickets_for(params)
        return self._dimensions.get(path, [])

    def fetch_page(self, path: str, params: dict[str, str | int]) -> Page:
        items = self._items(path, params)
        return Page(items=items[: int(params.get("limit", PAGE_SIZE))], total=len(items))

    def iter_pages(self, path: str, params: dict[str, str | int]) -> Iterator[list[JsonObject]]:
        items = self._items(path, params)
        for start in range(0, len(items), PAGE_SIZE):
            yield items[start : start + PAGE_SIZE]


class FakeSyncStore:
    def __init__(self) -> None:
        self.rows: dict[str, dict[Any, dict[str, Any]]] = {}
        self.state: dict[str, str] = {}

    def upsert(self, table: Table, rows: Sequence[dict[str, Any]], key: str) -> int:
        bucket = self.rows.setdefault(table.name, {})
        for row in rows:
            bucket[row[key]] = row
        return len(rows)

    def get_state(self, key: str) -> str | None:
        return self.state.get(key)

    def set_state(self, key: str, value: str) -> None:
        self.state[key] = value


class FixedClock:
    def __init__(self, moment: datetime) -> None:
        self.moment = moment

    def __call__(self) -> datetime:
        return self.moment
