from datetime import UTC, datetime

import httpx
import pytest

from app.tiflux.client import PAGE_SIZE, TifluxApiError, TifluxClient, seconds_until_reset
from tests.fakes import FakeSleeper, FakeTifluxHttp


def _page(count: int, remaining: int = 100, total: int = 0) -> httpx.Response:
    headers = {"X-Total-Items": str(total or count), "RateLimit-Remaining": str(remaining),
               "RateLimit-Reset": "2026-09-29T12:01:00Z"}
    return httpx.Response(200, json=[{"id": i} for i in range(count)], headers=headers)


def _client(fake: FakeTifluxHttp, sleeper: FakeSleeper) -> TifluxClient:
    return TifluxClient("https://api.test/api/v2", "token", http=fake.client(), sleep=sleeper)


def test_iter_pages_stops_after_short_page_and_uses_page_number_offset() -> None:
    fake = FakeTifluxHttp([_page(PAGE_SIZE), _page(5)])
    pages = list(_client(fake, FakeSleeper()).iter_pages("/tickets", {"filter_by": "all"}))
    assert [len(page) for page in pages] == [PAGE_SIZE, 5]
    assert [r.url.params["offset"] for r in fake.requests] == ["1", "2"]
    assert fake.requests[0].headers["Authorization"] == "Bearer token"


def test_fetch_page_reads_total_header() -> None:
    fake = FakeTifluxHttp([_page(1, total=164290)])
    assert _client(fake, FakeSleeper()).fetch_page("/tickets", {"limit": 1}).total == 164290


def test_429_waits_until_reset_then_retries() -> None:
    limited = httpx.Response(429, headers={"RateLimit-Reset": "2999-01-01T00:00:00Z"})
    fake, sleeper = FakeTifluxHttp([limited, _page(1)]), FakeSleeper()
    _client(fake, sleeper).fetch_page("/tickets", {})
    assert len(fake.requests) == 2
    assert sleeper.waits and sleeper.waits[0] > 60


def test_exhausted_quota_pauses_before_next_call() -> None:
    fake, sleeper = FakeTifluxHttp([_page(1, remaining=1)]), FakeSleeper()
    _client(fake, sleeper).fetch_page("/tickets", {})
    assert len(sleeper.waits) == 1


def test_client_error_raises_with_status_and_path() -> None:
    fake = FakeTifluxHttp([httpx.Response(422, json={"message": "bad filter"})])
    with pytest.raises(TifluxApiError, match="/tickets.*422"):
        _client(fake, FakeSleeper()).fetch_page("/tickets", {"filter_by": "x"})


def test_seconds_until_reset_falls_back_on_garbage() -> None:
    now = datetime(2026, 9, 29, 12, 0, tzinfo=UTC)
    assert seconds_until_reset("2026-09-29T12:00:30Z", now) == pytest.approx(31.0)
    assert seconds_until_reset("not-a-date", now) == 30.0
    assert seconds_until_reset(None, now) == 30.0
