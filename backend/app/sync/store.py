"""Persistence for synced rows: idempotent upserts and the sync_state key/value table."""

from collections.abc import Sequence

from sqlalchemy import Engine, Table, case, delete, func, select, update
from sqlalchemy.dialects.postgresql import insert

from app.db import sync_state, tickets
from app.sync.mapper import Row
from app.sync.translations import PT_BR_NAMES, TRANSLATED_COLUMNS


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

    def translate_stored_names(self) -> int:
        """Applies the de-para to rows synced before it existed; idempotent, so safe on every start."""
        changed = 0
        with self._engine.begin() as conn:
            for name in TRANSLATED_COLUMNS:
                column = tickets.c[name]
                statement = (update(tickets).where(column.in_(PT_BR_NAMES))
                             .values({name: case(PT_BR_NAMES, value=column)}))
                changed += conn.execute(statement).rowcount
        return changed

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

