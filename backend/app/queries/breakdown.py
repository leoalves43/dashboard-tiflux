"""Metrics grouped by one dimension (client, desk, technician, ...)."""

from dataclasses import dataclass
from typing import Literal

from sqlalchemy import ColumnElement, Connection, func, select

from app.db import tickets as t
from app.filters import UNASSIGNED_ID, TicketFilters, filter_conditions
from app.queries.metrics import PlainRow, metric_expressions, to_plain
from app.sla import QueryContext

Dimension = Literal["client", "desk", "responsible", "priority", "stage", "status", "catalog", "channel"]


# Group by the raw column, not a coalesce with bound literals: Postgres treats those
# as different expressions in SELECT and GROUP BY. Blanks are filled afterwards.
@dataclass(frozen=True)
class DimensionSpec:
    label: str
    group_column: ColumnElement[object]
    name_column: ColumnElement[object]
    empty_name: str
    empty_key: str

    def name(self) -> ColumnElement[str]:
        return func.coalesce(func.max(self.name_column), self.empty_name)


def _by_id(label: str, id_col: ColumnElement[int], name_col: ColumnElement[str], empty: str,
           empty_key: int = -1) -> DimensionSpec:
    return DimensionSpec(label, id_col, name_col, empty, str(empty_key))


def _by_text(label: str, column: ColumnElement[str], empty: str) -> DimensionSpec:
    return DimensionSpec(label, column, column, empty, empty)


DIMENSIONS: dict[str, DimensionSpec] = {
    "client": _by_id("Cliente", t.c.client_id, t.c.client_name, "Sem cliente"),
    "desk": _by_id("Mesa", t.c.desk_id, t.c.desk_name, "Sem mesa"),
    "responsible": _by_id("Técnico", t.c.responsible_id, t.c.responsible_name, "Sem responsável",
                          UNASSIGNED_ID),
    "priority": _by_text("Prioridade", t.c.priority_name, "Sem prioridade"),
    "stage": _by_text("Estágio", t.c.stage_name, "Sem estágio"),
    "status": _by_text("Status", t.c.status_name, "Sem status"),
    "catalog": _by_text("Catálogo de serviço", t.c.services_catalog, "Sem catálogo"),
    "channel": _by_text("Canal de abertura", t.c.created_by_way_of, "Desconhecido"),
}


def breakdown(conn: Connection, dimension: Dimension, filters: TicketFilters,
              ctx: QueryContext) -> list[PlainRow]:
    """Example: breakdown(conn, "desk", TicketFilters(situations=["open"]), ctx)"""
    spec = DIMENSIONS[dimension]
    query = (
        select(spec.group_column.label("key"), spec.name().label("name"), *metric_expressions(ctx))
        .where(*filter_conditions(filters, ctx))
        .group_by(spec.group_column)
        .order_by(func.count().desc())
    )
    return [_with_key(to_plain(row), spec) for row in conn.execute(query).mappings()]


def _with_key(row: PlainRow, spec: DimensionSpec) -> PlainRow:
    """Keys are strings so ids and names share one shape; the frontend maps them back to filters."""
    return {**row, "key": spec.empty_key if row["key"] is None else str(row["key"])}
