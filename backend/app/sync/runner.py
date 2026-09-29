"""Entry point of the `sync` container: runs a sync cycle every SYNC_INTERVAL_MINUTES."""

import logging
import time

from app.config import Settings
from app.db import build_engine, ensure_schema
from app.sync.service import TicketSync
from app.sync.store import SyncStore
from app.tiflux.client import TifluxClient

log = logging.getLogger("app.sync")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="level=%(levelname)s logger=%(name)s msg=%(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)  # one line per request drowns the sync log
    settings = Settings()
    engine = build_engine(settings)
    ensure_schema(engine, settings.schema_name)
    sync = TicketSync(TifluxClient(settings.url_tiflux, settings.token_tiflux), SyncStore(engine))
    while True:
        try:
            sync.run_cycle()
        except Exception:  # keep the worker alive; next cycle resumes from sync_state
            log.exception("sync cycle failed")
        time.sleep(settings.sync_interval_minutes * 60)


if __name__ == "__main__":
    main()
