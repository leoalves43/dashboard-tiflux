"""Postgres side of the description backfill: the pending queue, saves and progress counts."""

from collections.abc import Collection
from datetime import datetime

from sqlalchemy import Engine, func, or_, select
from sqlalchemy.dialects.postgresql import insert

from app.db import ticket_descriptions as d
from app.db import tickets as t
from app.sync.descriptions import PendingTicket


class DescriptionStore:
    """Example: DescriptionStore(engine).pending_descriptions(50, skip=set())"""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def pending_descriptions(self, limit: int, skip: Collection[int]) -> list[PendingTicket]:
        """Never fetched, or the ticket changed in Tiflux after its description was copied."""
        query = (
            select(t.c.ticket_number, t.c.updated_at)
            .select_from(t.outerjoin(d, d.c.ticket_number == t.c.ticket_number))
            .where(or_(d.c.ticket_number.is_(None), t.c.updated_at > d.c.ticket_updated_at))
            .order_by(t.c.updated_at.desc().nulls_last(), t.c.ticket_number.desc())
            .limit(limit)
        )
        if skip:
            query = query.where(t.c.ticket_number.not_in(list(skip)))
        with self._engine.connect() as conn:
            return [PendingTicket(row.ticket_number, row.updated_at) for row in conn.execute(query)]

    def save_description(self, ticket_number: int, description: str | None,
                         ticket_updated_at: datetime | None) -> None:
        values = {"description": description, "ticket_updated_at": ticket_updated_at}
        statement = insert(d).values(ticket_number=ticket_number, **values)
        statement = statement.on_conflict_do_update(
            index_elements=["ticket_number"], set_={**values, "synced_at": func.now()}
        )
        with self._engine.begin() as conn:
            conn.execute(statement)

    def description_progress(self) -> tuple[int, int]:
        """(tickets with a copied description, all tickets)."""
        with self._engine.connect() as conn:
            done = conn.execute(select(func.count()).select_from(d)).scalar_one()
            total = conn.execute(select(func.count()).select_from(t)).scalar_one()
        return done, total
