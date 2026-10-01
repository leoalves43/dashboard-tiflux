from datetime import UTC, datetime, timedelta

from sqlalchemy import Engine, delete, update

from app.db import ticket_descriptions, tickets
from app.sync.description_store import DescriptionStore
from app.sync.descriptions import DescriptionSync
from app.sync.runner import run_cycle
from tests.fakes import FakeDescriptionStore, FakeTicketDetailSource, FixedClock, TickingClock

NOW = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)
LATER = NOW + timedelta(hours=1)
UPDATED = {1: NOW - timedelta(days=3), 2: NOW - timedelta(days=1), 3: NOW - timedelta(days=2)}


def _sync(source: FakeTicketDetailSource, store: FakeDescriptionStore) -> DescriptionSync:
    return DescriptionSync(source, store, FixedClock(NOW))


def test_fetches_most_recently_updated_first_and_saves_each() -> None:
    source, store = FakeTicketDetailSource({1: "um", 2: "dois", 3: "três"}), FakeDescriptionStore(dict(UPDATED))
    assert _sync(source, store).run_until(LATER) == 3
    assert source.fetched == [2, 3, 1]
    assert store.saved[3] == ("três", UPDATED[3])


def test_resumes_without_refetching_saved_tickets() -> None:
    store = FakeDescriptionStore(dict(UPDATED))
    store.saved[2] = ("dois", UPDATED[2])  # copied before an interruption
    source = FakeTicketDetailSource({1: "um", 3: "três"})
    _sync(source, store).run_until(LATER)
    assert source.fetched == [3, 1]


def test_refetches_ticket_changed_after_its_copy() -> None:
    store = FakeDescriptionStore(dict(UPDATED))
    for number, at in UPDATED.items():
        store.saved[number] = ("antiga", at)
    store.tickets_updated_at[1] = NOW  # edited in Tiflux; the incremental sync moved updated_at
    source = FakeTicketDetailSource({1: "nova"})
    _sync(source, store).run_until(LATER)
    assert (source.fetched, store.saved[1]) == ([1], ("nova", NOW))


def test_deleted_ticket_is_saved_empty_and_leaves_the_queue() -> None:
    store = FakeDescriptionStore({7: NOW})
    _sync(FakeTicketDetailSource({}, missing={7}), store).run_until(LATER)
    assert store.saved[7] == (None, NOW)
    assert store.pending_descriptions(10, set()) == []


def test_failure_is_isolated_and_retried_next_run() -> None:
    store = FakeDescriptionStore(dict(UPDATED))
    source = FakeTicketDetailSource({1: "um", 3: "três"}, failing={2})
    assert _sync(source, store).run_until(LATER) == 2
    assert source.fetched.count(2) == 1 and 2 not in store.saved
    assert [p.ticket_number for p in store.pending_descriptions(10, set())] == [2]


def test_stops_at_the_deadline() -> None:
    store = FakeDescriptionStore(dict(UPDATED))
    clock = TickingClock(NOW, timedelta(seconds=1))
    sync = DescriptionSync(FakeTicketDetailSource({1: "um", 2: "dois", 3: "três"}), store, clock)
    sync.run_until(NOW + timedelta(seconds=2))
    assert 0 < len(store.saved) < 3


def test_run_cycle_syncs_tickets_first_and_survives_failures() -> None:
    calls: list[str] = []

    def failing_tickets() -> None:
        calls.append("tickets")
        raise RuntimeError("tiflux down")

    def descriptions(deadline: datetime) -> int:
        calls.append(f"descriptions until {deadline:%H:%M}")
        return 0

    wait = run_cycle(failing_tickets, descriptions, timedelta(minutes=5), FixedClock(NOW))
    assert calls == ["tickets", "descriptions until 12:05"]
    assert wait == timedelta(minutes=5)


def test_description_store_queue_saves_and_requeues(engine: Engine) -> None:
    store = DescriptionStore(engine)
    first = store.pending_descriptions(10, set())[0]
    try:
        pending = store.pending_descriptions(10, set())
        assert len(pending) == 6 and pending[0].updated_at >= pending[-1].updated_at
        store.save_description(first.ticket_number, "<p>x</p>", first.updated_at)
        assert first.ticket_number not in {p.ticket_number for p in store.pending_descriptions(10, set())}
        assert store.description_progress() == (1, 6)
        with engine.begin() as conn:
            conn.execute(update(tickets).where(tickets.c.ticket_number == first.ticket_number)
                         .values(updated_at=first.updated_at + timedelta(days=1)))
        assert first.ticket_number in {p.ticket_number for p in store.pending_descriptions(10, set())}
        skipped = store.pending_descriptions(10, {first.ticket_number})
        assert first.ticket_number not in {p.ticket_number for p in skipped}
    finally:
        with engine.begin() as conn:
            conn.execute(delete(ticket_descriptions))
            conn.execute(update(tickets).where(tickets.c.ticket_number == first.ticket_number)
                         .values(updated_at=first.updated_at))
