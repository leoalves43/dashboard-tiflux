"""Background copy of ticket descriptions (Tiflux list payloads omit them): one detail call per ticket.

Resumable by construction: the store's pending query is the progress, and every ticket is saved
as soon as it is fetched, so an interruption loses at most the ticket in flight (spec 003).
"""

import logging
from collections.abc import Callable, Collection
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from app.tiflux.client import TifluxApiError, TifluxSource

log = logging.getLogger(__name__)

DESCRIPTION_BATCH = 50


@dataclass(frozen=True)
class PendingTicket:
    ticket_number: int
    updated_at: datetime | None  # saved with the description; a newer value later re-queues it


class DescriptionStorePort(Protocol):
    def pending_descriptions(self, limit: int, skip: Collection[int]) -> list[PendingTicket]: ...
    def save_description(self, ticket_number: int, description: str | None,
                         ticket_updated_at: datetime | None) -> None: ...
    def description_progress(self) -> tuple[int, int]: ...


class DescriptionSync:
    """Example: DescriptionSync(client, store).run_until(cycle_start + interval)"""

    def __init__(self, source: TifluxSource, store: DescriptionStorePort,
                 clock: Callable[[], datetime] = lambda: datetime.now(UTC)) -> None:
        self._source = source
        self._store = store
        self._clock = clock

    def run_until(self, deadline: datetime) -> int:
        """Fetches pending descriptions (most recently updated first) until `deadline`; returns how many."""
        failed: set[int] = set()  # skipped for the rest of this run, retried next cycle
        fetched = 0
        while self._clock() < deadline:
            batch = self._store.pending_descriptions(DESCRIPTION_BATCH, failed)
            if not batch:
                break
            fetched += self._fetch_batch(batch, deadline, failed)
            self._log_progress()
        return fetched

    def _fetch_batch(self, batch: list[PendingTicket], deadline: datetime, failed: set[int]) -> int:
        fetched = 0
        for pending in batch:
            if self._clock() >= deadline:
                break
            if self._fetch_one(pending):
                fetched += 1
            else:
                failed.add(pending.ticket_number)
        return fetched

    def _fetch_one(self, pending: PendingTicket) -> bool:
        try:
            detail = self._source.fetch_one(f"/tickets/{pending.ticket_number}")
        except TifluxApiError as error:
            log.warning("description fetch failed ticket=%d error=%s", pending.ticket_number, error)
            return False
        # A deleted ticket (404 -> None) is saved empty so it leaves the queue instead of blocking it.
        description = detail.get("description") if detail else None
        self._store.save_description(pending.ticket_number, description, pending.updated_at)
        return True

    def _log_progress(self) -> None:
        done, total = self._store.description_progress()
        log.info("descriptions progress=%d/%d", done, total)
