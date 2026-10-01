"""Query tests run against the real Postgres (SQL is the unit under test) in an isolated schema."""

import os
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.exc import OperationalError

from app.config import Settings
from app.db import build_engine, ensure_schema, tickets
from app.sla import QueryContext
from app.sync.mapper import map_ticket
from app.sync.store import SyncStore
from tests.fakes import make_ticket

TEST_SCHEMA = os.environ.get("TEST_SCHEMA_NAME", "dashboard_test")
NOW = datetime(2026, 9, 29, 12, 0, tzinfo=UTC)


def _sla(solve: str | None = None, stage: str | None = None, solved: str | None = None) -> dict[str, object]:
    return {"solve_expiration": solve, "stage_expiration": stage, "solved_in_time": solved,
            "attend_expiration": None, "stopped": False}


CLOSED = {"is_closed": True, "status": {"id": 9, "name": "Closed"}}
SEED = [
    # A: open, 10 days past solve deadline, stage 1 day past
    make_ticket(1, "2026-09-10T12:00:00Z", sla_info=_sla("2026-09-19T12:00:00Z", "2026-09-28T12:00:00Z")),
    # B: open, on time, other desk/client, no responsible
    make_ticket(2, "2026-09-25T12:00:00Z", sla_info=_sla("2026-10-05T12:00:00Z"), responsible=None,
                desk={"id": 11, "name": "INFRA"}, client={"id": 21, "name": "Cliente B"}),
    # C: closed 2 days late, 264h to solve
    make_ticket(3, "2026-09-01T12:00:00Z", sla_info=_sla("2026-09-10T12:00:00Z", solved="2026-09-12T12:00:00Z"),
                **CLOSED),
    # D: closed on time, 24h to solve
    make_ticket(4, "2026-09-04T12:00:00Z", sla_info=_sla("2026-09-08T12:00:00Z", solved="2026-09-05T12:00:00Z"),
                **CLOSED),
    # E: canceled -> no SLA even with a past deadline
    make_ticket(5, "2026-09-15T12:00:00Z", sla_info=_sla("2026-09-16T12:00:00Z"), is_closed=True,
                status={"id": 8, "name": "Canceled"}),
    # F: open without solve deadline, created in August
    make_ticket(6, "2026-08-01T12:00:00Z"),
]


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    settings = Settings(schema_name=TEST_SCHEMA)  # type: ignore[call-arg]  # rest comes from env
    engine = build_engine(settings)
    try:
        with engine.begin() as conn:
            conn.execute(text(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE"))
    except OperationalError as error:
        pytest.skip(f"Postgres unavailable for query tests: {error}")
    ensure_schema(engine, TEST_SCHEMA)
    SyncStore(engine).upsert(tickets, [map_ticket(item) for item in SEED], "ticket_number")
    yield engine
    with engine.begin() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE"))
    engine.dispose()


@pytest.fixture
def ctx() -> QueryContext:
    return QueryContext(now=NOW)
