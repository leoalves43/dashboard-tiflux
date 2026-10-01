"""Entry point of the `sync` container: runs a sync cycle every SYNC_INTERVAL_MINUTES."""

import logging
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from app.config import Settings
from app.db import build_engine, ensure_schema
from app.sync.description_store import DescriptionStore
from app.sync.descriptions import DescriptionSync
from app.sync.service import TicketSync
from app.sync.store import SyncStore
from app.tiflux.client import TifluxClient

log = logging.getLogger("app.sync")


def _guarded(step: str, action: Callable[[], object]) -> None:
    try:
        action()
    except Exception:  # keep the worker alive; every step resumes from what is stored
        log.exception("%s failed", step)


def run_cycle(sync_tickets: Callable[[], None], sync_descriptions: Callable[[datetime], int],
              interval: timedelta, clock: Callable[[], datetime] = lambda: datetime.now(UTC)) -> timedelta:
    """Tickets first (they must never wait), descriptions in the rest of the cycle; returns the sleep left.

    Example: time.sleep(run_cycle(sync.run_cycle, descriptions.run_until, timedelta(minutes=5)).total_seconds())
    """
    deadline = clock() + interval
    _guarded("sync cycle", sync_tickets)
    _guarded("description backfill", lambda: sync_descriptions(deadline))
    return max(timedelta(0), deadline - clock())


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="level=%(levelname)s logger=%(name)s msg=%(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)  # one line per request drowns the sync log
    settings = Settings()
    engine = build_engine(settings)
    ensure_schema(engine, settings.schema_name)
    store = SyncStore(engine)
    log.info("translated_names=%d", store.translate_stored_names())
    client = TifluxClient(settings.url_tiflux, settings.token_tiflux)
    sync = TicketSync(client, store)
    descriptions = DescriptionSync(client, DescriptionStore(engine))
    interval = timedelta(minutes=settings.sync_interval_minutes)
    while True:
        time.sleep(run_cycle(sync.run_cycle, descriptions.run_until, interval).total_seconds())


if __name__ == "__main__":
    main()
