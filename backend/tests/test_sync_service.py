from datetime import UTC, datetime

from app.sync.service import (
    STATE_BACKFILL_CURSOR,
    STATE_BACKFILL_DONE,
    STATE_LAST_INCREMENTAL,
    TicketSync,
)
from app.tiflux.client import JsonObject
from tests.fakes import FakeSyncStore, FakeTifluxSource, FixedClock, make_ticket

NOW = datetime(2026, 9, 29, 12, 0, tzinfo=UTC)
ALL_TICKETS = [
    make_ticket(3, "2026-09-20T10:00:00Z"),
    make_ticket(2, "2026-06-15T10:00:00Z", is_closed=True, status={"id": 9, "name": "Closed"}),
    make_ticket(1, "2026-01-05T10:00:00Z", is_closed=True, status={"id": 9, "name": "Fechado X"}),
]


def _parse(value: str | int) -> datetime:
    return datetime.fromisoformat(str(value))


def _query_tickets(params: dict[str, str | int]) -> list[JsonObject]:
    """Mimics the API filters used by the sync: created_at window, updated since, canceled."""
    if params.get("filter_by") == "canceled":
        return [ALL_TICKETS[2]]
    selected = ALL_TICKETS
    if "start_datetime" in params:
        selected = [t for t in selected if _parse(t["created_at"]) >= _parse(params["start_datetime"])]
    if "end_datetime" in params:
        selected = [t for t in selected if _parse(t["created_at"]) < _parse(params["end_datetime"])]
    if "update_start_datetime" in params:
        selected = [t for t in selected if _parse(t["updated_at"]) >= _parse(params["update_start_datetime"])]
    return selected


def _sync(store: FakeSyncStore) -> tuple[TicketSync, FakeTifluxSource]:
    source = FakeTifluxSource(_query_tickets, {"/clients": [{"id": 1, "name": "C", "status": True}]})
    return TicketSync(source, store, clock=FixedClock(NOW)), source


def test_backfill_walks_windows_until_no_older_tickets() -> None:
    store = FakeSyncStore()
    sync, _ = _sync(store)
    sync.backfill()
    assert set(store.rows["tickets"]) == {1, 2, 3}
    assert store.state[STATE_BACKFILL_DONE] == "1"
    assert _parse(store.state[STATE_BACKFILL_CURSOR]) < datetime(2026, 1, 5, tzinfo=UTC)


def test_backfill_marks_canceled_tickets_explicitly() -> None:
    store = FakeSyncStore()
    sync, _ = _sync(store)
    sync.backfill()
    assert store.rows["tickets"][1]["situation"] == "canceled"
    assert store.rows["tickets"][2]["situation"] == "closed"


def test_backfill_resumes_from_saved_cursor() -> None:
    store = FakeSyncStore()
    store.state[STATE_BACKFILL_CURSOR] = datetime(2026, 7, 1, tzinfo=UTC).isoformat()
    sync, _ = _sync(store)
    sync.backfill()
    assert 3 not in store.rows["tickets"]


def test_incremental_rereads_overlap_and_advances_marker() -> None:
    store = FakeSyncStore()
    store.state[STATE_LAST_INCREMENTAL] = "2026-09-20T10:05:00Z"
    sync, source = _sync(store)
    sync.incremental()
    assert set(store.rows["tickets"]) == {3, 1}
    first_ticket_call = next(params for path, params in source.calls if path == "/tickets")
    assert first_ticket_call["update_start_datetime"] == "2026-09-20T09:55:00Z"
    assert store.state[STATE_LAST_INCREMENTAL] == "2026-09-29T12:00:00Z"


def test_run_cycle_skips_backfill_when_done() -> None:
    store = FakeSyncStore()
    store.state[STATE_BACKFILL_DONE] = "1"
    sync, source = _sync(store)
    sync.run_cycle()
    assert store.rows["clients"][1]["name"] == "C"
    assert not any("start_datetime" in params for _, params in source.calls)
