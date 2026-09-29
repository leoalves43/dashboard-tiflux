"""Persistence for synced rows: idempotent upserts and the sync_state key/value table."""

from collections.abc import Sequence

from sqlalchemy import Engine, Table, delete, func, select
from sqlalchemy.dialects.postgresql import insert

from app.db import sync_state, tickets
from app.sync.mapper import Row


class SyncStore:
    """Example: SyncStore(engine).upsert(tickets, rows, key="ticket_number")"""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def upsert(self, table: Table, rows: Sequence[Row], key: str) -> int:
        if not rows:
            return 0
        statement = insert(table).values(list(_dedupe(rows, key)))
        updates = {col.name: statement.excluded[col.name] for col in table.columns
                   if col.name != key and col.name in rows[0]}
        if "synced_at" in table.columns:
            updates["synced_at"] = func.now()
        with self._engine.begin() as conn:
            conn.execute(statement.on_conflict_do_update(index_elements=[key], set_=updates))
        return len(rows)

    def ticket_numbers(self, situation: str) -> set[int]:
        query = select(tickets.c.ticket_number).where(tickets.c.situation == situation)
        with self._engine.connect() as conn:
            return set(conn.execute(query).scalars())

    def delete_tickets(self, numbers: Sequence[int]) -> int:
        if not numbers:
            return 0
        with self._engine.begin() as conn:
            return conn.execute(delete(tickets).where(tickets.c.ticket_number.in_(numbers))).rowcount

    def get_state(self, key: str) -> str | None:
        with self._engine.connect() as conn:
            return conn.execute(select(sync_state.c.value).where(sync_state.c.key == key)).scalar()

    def set_state(self, key: str, value: str) -> None:
        statement = insert(sync_state).values(key=key, value=value)
        statement = statement.on_conflict_do_update(
            index_elements=["key"], set_={"value": value, "updated_at": func.now()}
        )
        with self._engine.begin() as conn:
            conn.execute(statement)


def _dedupe(rows: Sequence[Row], key: str) -> list[Row]:
    """ON CONFLICT fails if one statement touches the same key twice; keep the last row."""
    return list({row[key]: row for row in rows}.values())

