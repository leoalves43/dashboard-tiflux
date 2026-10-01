"""Detailed ticket rows (paged for the UI, unpaged for exports)."""

from collections.abc import Iterator
from typing import Any, Literal

from sqlalchemy import ColumnElement, Connection, Select, func, select

from app.db import ticket_descriptions as d
from app.db import tickets as t
from app.exporters import ExportColumn
from app.filters import TicketFilters, filter_conditions
from app.queries.metrics import PlainRow, to_plain
from app.sla import (
    QueryContext,
    open_age_days,
    resolution_hours,
    sla_state,
    solve_late_days,
    stage_late_days,
)

SortDirection = Literal["asc", "desc"]
MAX_PAGE_SIZE = 500
EXPORT_BATCH_SIZE = 2000


LIST_COLUMNS = (
    ExportColumn("ticket_number", "Nº"),
    ExportColumn("title", "Título"),
    ExportColumn("situation", "Situação"),
    ExportColumn("status_name", "Status"),
    ExportColumn("stage_name", "Estágio"),
    ExportColumn("priority_name", "Prioridade"),
    ExportColumn("desk_name", "Mesa"),
    ExportColumn("client_name", "Cliente"),
    ExportColumn("responsible_name", "Técnico"),
    ExportColumn("requestor_name", "Solicitante"),
    ExportColumn("services_catalog", "Catálogo de serviço"),
    ExportColumn("created_by_way_of", "Canal"),
    ExportColumn("created_at", "Aberto em"),
    ExportColumn("solved_at", "Resolvido em"),
    ExportColumn("solve_expiration", "Prazo solução (SLA)"),
    ExportColumn("stage_expiration", "Prazo estágio"),
    ExportColumn("sla_state", "SLA"),
    ExportColumn("late_days", "Dias de atraso"),
    ExportColumn("stage_late_days", "Dias estágio vencido"),
    ExportColumn("open_age_days", "Idade (dias)"),
    ExportColumn("resolution_hours", "Tempo resolução (h)"),
    ExportColumn("reopen_count", "Reaberturas"),
)
# Exports only: the description is long text the paged UI list never needs (spec 003).
EXPORT_COLUMNS = (*LIST_COLUMNS, ExportColumn("description", "Descrição"))


def _selectable_columns(ctx: QueryContext) -> dict[str, ColumnElement[Any]]:
    computed: dict[str, ColumnElement[Any]] = {
        "sla_state": sla_state(ctx),
        "late_days": solve_late_days(ctx),
        "stage_late_days": stage_late_days(ctx),
        "open_age_days": open_age_days(ctx),
        "resolution_hours": resolution_hours(),
    }
    return {col.key: computed.get(col.key, t.c.get(col.key)) for col in LIST_COLUMNS}


def _base_query(filters: TicketFilters, ctx: QueryContext) -> tuple[Select[Any], dict[str, ColumnElement[Any]]]:
    columns = _selectable_columns(ctx)
    labeled = [expr.label(key) for key, expr in columns.items()]
    return select(*labeled).where(*filter_conditions(filters, ctx)), columns


def _order(columns: dict[str, ColumnElement[Any]], sort: str, direction: SortDirection) -> list[Any]:
    if sort not in columns:
        raise ValueError(f"sort={sort!r}; expected one of {sorted(columns)}")
    primary = columns[sort].asc() if direction == "asc" else columns[sort].desc()
    return [primary.nulls_last(), t.c.ticket_number.desc()]


def list_tickets(conn: Connection, filters: TicketFilters, ctx: QueryContext, *, sort: str,
                 direction: SortDirection, page: int, page_size: int) -> PlainRow:
    """Example: list_tickets(conn, filters, ctx, sort="late_days", direction="desc", page=1, page_size=50)"""
    page_size = max(1, min(page_size, MAX_PAGE_SIZE))
    query, columns = _base_query(filters, ctx)
    count_query = select(func.count()).select_from(t).where(*filter_conditions(filters, ctx))
    total = conn.execute(count_query).scalar_one()
    paged = query.order_by(*_order(columns, sort, direction)).limit(page_size).offset((max(page, 1) - 1) * page_size)
    rows = [to_plain(row) for row in conn.execute(paged).mappings()]
    return {"total": total, "page": page, "page_size": page_size, "rows": rows}


def iter_all_tickets(conn: Connection, filters: TicketFilters, ctx: QueryContext, *, sort: str,
                     direction: SortDirection) -> Iterator[PlainRow]:
    """Streams every filtered row (server-side cursor) for exports, with the stored description (HTML)."""
    query, columns = _base_query(filters, ctx)
    # LEFT JOIN: tickets whose description was not copied yet still export, with an empty cell.
    query = query.add_columns(d.c.description).select_from(t.outerjoin(d, d.c.ticket_number == t.c.ticket_number))
    result = conn.execution_options(yield_per=EXPORT_BATCH_SIZE).execute(
        query.order_by(*_order(columns, sort, direction))
    )
    for row in result.mappings():
        yield to_plain(row)
