"""One ticket's summary for the hover card and the detail modal (local data only).

The description lives in ticket_descriptions (filled by the sync, spec 003); not-yet-copied ones are read live.
"""

from sqlalchemy import Connection, select

from app.db import ticket_descriptions as d
from app.db import tickets as t
from app.queries.metrics import PlainRow, to_plain

SUMMARY_COLUMNS = (
    t.c.ticket_number, t.c.title, t.c.situation, t.c.requestor_name, t.c.requestor_email,
    t.c.client_name, t.c.desk_name, t.c.priority_name, t.c.status_name, t.c.stage_name,
    t.c.responsible_name, t.c.created_at,
)


def ticket_summary(conn: Connection, ticket_number: int) -> PlainRow | None:
    """Example: ticket_summary(conn, 363996) -> {"ticket_number": 363996, "client_name": "...", ...} or None."""
    query = select(*SUMMARY_COLUMNS).where(t.c.ticket_number == ticket_number)
    row = conn.execute(query).mappings().first()
    return to_plain(row) if row else None


def stored_description(conn: Connection, ticket_number: int) -> tuple[bool, str | None]:
    """(copied?, description). Example: stored_description(conn, 1) -> (True, "<p>...</p>") or (False, None)."""
    row = conn.execute(select(d.c.description).where(d.c.ticket_number == ticket_number)).first()
    return (True, row.description) if row else (False, None)
