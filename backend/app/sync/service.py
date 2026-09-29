"""Sync orchestration: dimensions, one-time backfill in monthly windows, then incremental."""

import logging
from collections.abc import Callable, Sequence
from datetime import UTC, datetime, timedelta
from typing import Protocol

from sqlalchemy import Table

from app.db import clients, desks, technicians, tickets
from app.sync.mapper import Row, map_client, map_desk, map_technician, map_ticket
from app.tiflux.client import JsonObject, TifluxSource

log = logging.getLogger(__name__)

STATE_BACKFILL_CURSOR = "backfill_cursor"  # lower bound (ISO) of the last finished window
STATE_BACKFILL_DONE = "backfill_done"
STATE_LAST_INCREMENTAL = "last_incremental"
# Re-read a margin before the last run so edits racing with pagination are not lost.
INCREMENTAL_OVERLAP = timedelta(minutes=10)
BACKFILL_WINDOW_DAYS = 31


class SyncStorePort(Protocol):
    def upsert(self, table: Table, rows: Sequence[Row], key: str) -> int: ...
    def get_state(self, key: str) -> str | None: ...
    def set_state(self, key: str, value: str) -> None: ...


def iso(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class TicketSync:
    """Example: TicketSync(TifluxClient(...), SyncStore(engine)).run_cycle()"""

    def __init__(
        self,
        source: TifluxSource,
        store: SyncStorePort,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._source = source
        self._store = store
        self._clock = clock

    def run_cycle(self) -> None:
        self.sync_dimensions()
        if self._store.get_state(STATE_BACKFILL_DONE) != "1":
            self.backfill()
        self.incremental()

    def sync_dimensions(self) -> None:
        self._copy_all("/clients", {}, clients, map_client)
        self._copy_all("/desks", {}, desks, map_desk)
        self._copy_all("/technical-users", {}, technicians, map_technician)

    def backfill(self) -> None:
        """Walks created_at windows backwards from now until no older tickets remain (resumable)."""
        if self._store.get_state(STATE_LAST_INCREMENTAL) is None:
            self._store.set_state(STATE_LAST_INCREMENTAL, iso(self._clock()))
        cursor_text = self._store.get_state(STATE_BACKFILL_CURSOR)
        window_end = datetime.fromisoformat(cursor_text) if cursor_text else self._clock() + timedelta(days=1)
        while self._has_tickets_before(window_end):
            window_start = window_end - timedelta(days=BACKFILL_WINDOW_DAYS)
            count = self._copy_tickets(self._window_params(window_start, window_end))
            log.info("backfill window %s..%s tickets=%d", iso(window_start), iso(window_end), count)
            self._store.set_state(STATE_BACKFILL_CURSOR, window_start.isoformat())
            window_end = window_start
        self._copy_tickets({"filter_by": "canceled"}, situation="canceled")
        self._store.set_state(STATE_BACKFILL_DONE, "1")

    def incremental(self) -> None:
        started = self._clock()
        last_text = self._store.get_state(STATE_LAST_INCREMENTAL)
        since = datetime.fromisoformat(last_text) if last_text else started
        params: dict[str, str | int] = {"update_start_datetime": iso(since - INCREMENTAL_OVERLAP)}
        changed = self._copy_tickets({**params, "filter_by": "all"})
        # Runs after "all" so the explicit canceled flag wins over the status-name heuristic.
        self._copy_tickets({**params, "filter_by": "canceled"}, situation="canceled")
        self._store.set_state(STATE_LAST_INCREMENTAL, iso(started))
        log.info("incremental since=%s changed=%d", iso(since), changed)

    def _has_tickets_before(self, moment: datetime) -> bool:
        params: dict[str, str | int] = {
            "filter_by": "all", "date_type": "created_at", "end_datetime": iso(moment), "limit": 1,
        }
        return self._source.fetch_page("/tickets", params).total > 0

    @staticmethod
    def _window_params(start: datetime, end: datetime) -> dict[str, str | int]:
        return {"filter_by": "all", "date_type": "created_at",
                "start_datetime": iso(start), "end_datetime": iso(end)}

    def _copy_tickets(self, params: dict[str, str | int], situation: str | None = None) -> int:
        return self._copy_all("/tickets", params, tickets, lambda item: map_ticket(item, situation))

    def _copy_all(
        self, path: str, params: dict[str, str | int], table: Table, mapper: Callable[[JsonObject], Row]
    ) -> int:
        key = "ticket_number" if table is tickets else "id"
        return sum(
            self._store.upsert(table, [mapper(item) for item in page], key)
            for page in self._source.iter_pages(path, params)
        )
