"""Aggregate columns shared by KPIs and breakdowns, plus result-row conversion."""

from decimal import Decimal
from typing import Any

from sqlalchemy import ColumnElement, Numeric, RowMapping, cast, func

from app.db import tickets as t
from app.exporters import ExportColumn
from app.sla import (
    SLA_LATE,
    SLA_NONE,
    SLA_ON_TIME,
    QueryContext,
    is_stage_late,
    open_age_days,
    resolution_hours,
    sla_state,
    solve_late_days,
)

PlainRow = dict[str, Any]


METRIC_COLUMNS = (
    ExportColumn("total", "Total"),
    ExportColumn("open", "Abertos"),
    ExportColumn("closed", "Fechados"),
    ExportColumn("canceled", "Cancelados"),
    ExportColumn("late", "Atrasados (SLA solução)"),
    ExportColumn("on_time", "No prazo"),
    ExportColumn("no_sla", "Sem SLA"),
    ExportColumn("pct_sla", "% no SLA"),
    ExportColumn("open_late", "Abertos em atraso"),
    ExportColumn("stage_late", "Estágio vencido"),
    ExportColumn("avg_late_days", "Média dias de atraso"),
    ExportColumn("max_late_days", "Máx. dias de atraso"),
    ExportColumn("avg_resolution_hours", "Tempo médio resolução (h)"),
    ExportColumn("max_open_age_days", "Aberto mais antigo (dias)"),
)


def _count_where(condition: ColumnElement[bool]) -> ColumnElement[int]:
    return func.count().filter(condition)


def _pct(part: ColumnElement[int], whole: ColumnElement[int]) -> ColumnElement[float]:
    return func.round(100 * cast(part, Numeric) / func.nullif(whole, 0), 1)


def metric_expressions(ctx: QueryContext) -> list[ColumnElement[Any]]:
    """Example: select(*metric_expressions(ctx)).where(*conditions)"""
    state = sla_state(ctx)
    late = _count_where(state == SLA_LATE)
    on_time = _count_where(state == SLA_ON_TIME)
    return [
        func.count().label("total"),
        _count_where(t.c.situation == "open").label("open"),
        _count_where(t.c.situation == "closed").label("closed"),
        _count_where(t.c.situation == "canceled").label("canceled"),
        late.label("late"),
        on_time.label("on_time"),
        _count_where(state == SLA_NONE).label("no_sla"),
        _pct(on_time, on_time + late).label("pct_sla"),
        _count_where((state == SLA_LATE) & (t.c.situation == "open")).label("open_late"),
        _count_where(is_stage_late(ctx)).label("stage_late"),
        func.round(func.avg(solve_late_days(ctx)), 1).label("avg_late_days"),
        func.max(solve_late_days(ctx)).label("max_late_days"),
        func.round(func.avg(resolution_hours()), 1).label("avg_resolution_hours"),
        func.max(open_age_days(ctx)).label("max_open_age_days"),
    ]


def to_plain(row: RowMapping) -> PlainRow:
    """Decimals -> float so JSON and spreadsheet cells get numbers, not strings."""
    return {key: float(value) if isinstance(value, Decimal) else value for key, value in row.items()}
