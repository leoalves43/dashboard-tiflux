"""One ticket's summary for the hover card and the detail modal (local data only)."""

from sqlalchemy import Connection, select

from app.db import tickets as t
from app.queries.metrics import PlainRow, to_plain

SUMMARY_COLUMNS = (
    t.c.ticket_number, t.c.title, t.c.situation, t.c.requestor_name, t.c.requestor_email,
    t.c.client_name, t.c.desk_name, t.c.priority_name, t.c.status_name, t.c.stage_name,
    t.c.responsible_name, t.c.created_at,
)


def ticket_summary(conn: Connection, ticket_number: int) -> PlainRow | None:
    """Example: ticket_summary(conn, 363996) -> {"ticket_number": 363996, "description": "...", ...} or None."""
    # The Tiflux list payload already carries the description, so raw holds it for every synced ticket.
    description = t.c.raw["description"].astext.label("description")
    query = select(*SUMMARY_COLUMNS, description).where(t.c.ticket_number == ticket_number)
    row = conn.execute(query).mappings().first()
    return to_plain(row) if row else None
