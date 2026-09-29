"""Overview queries: KPI totals, created/solved time series and day-range buckets."""

from typing import Literal

from sqlalchemy import ColumnElement, Connection, case, func, literal_column, select

from app.db import tickets as t
from app.filters import TicketFilters, filter_conditions
from app.queries.metrics import PlainRow, metric_expressions, to_plain
from app.sla import QueryContext, open_age_days, solve_late_days

Granularity = Literal["day", "week", "month"]
# (upper bound in days, label); anything above the last bound falls in "> 30 dias".
DAY_BUCKETS = ((2, "até 2 dias"), (7, "3–7 dias"), (15, "8–15 dias"), (30, "16–30 dias"))
LAST_BUCKET = "> 30 dias"


def kpis(conn: Connection, filters: TicketFilters, ctx: QueryContext) -> PlainRow:
    query = select(*metric_expressions(ctx)).where(*filter_conditions(filters, ctx))
    return to_plain(conn.execute(query).mappings().one())


def _period(column: ColumnElement[object], granularity: Granularity, ctx: QueryContext) -> ColumnElement[object]:
    local = func.timezone(ctx.timezone, column)
    return func.to_char(func.date_trunc(granularity, local), "YYYY-MM-DD")


def _count_by_period(conn: Connection, column: ColumnElement[object], granularity: Granularity,
                     conditions: list[ColumnElement[bool]], ctx: QueryContext) -> dict[str, int]:
    period = _period(column, granularity, ctx).label("period")
    query = select(period, func.count()).where(column.is_not(None), *conditions).group_by(period)
    return {row[0]: row[1] for row in conn.execute(query)}


def timeseries(conn: Connection, filters: TicketFilters, granularity: Granularity,
               ctx: QueryContext) -> list[PlainRow]:
    """Tickets opened and solved per period, under the same filters (sorted by period)."""
    conditions = filter_conditions(filters, ctx)
    created = _count_by_period(conn, t.c.created_at, granularity, conditions, ctx)
    solved_conditions = [*conditions, t.c.situation == "closed"]
    solved = _count_by_period(conn, t.c.solved_at, granularity, solved_conditions, ctx)
    periods = sorted(created.keys() | solved.keys())
    return [{"period": p, "created": created.get(p, 0), "solved": solved.get(p, 0)} for p in periods]


def _bucket_label(days: ColumnElement[float]) -> ColumnElement[str]:
    whens = [(days <= upper, label) for upper, label in DAY_BUCKETS]
    return case(*whens, else_=LAST_BUCKET)


def _bucket_counts(conn: Connection, days: ColumnElement[float],
                   conditions: list[ColumnElement[bool]]) -> list[PlainRow]:
    bucket = _bucket_label(days).label("bucket")
    query = select(bucket, func.count().label("count")).where(days.is_not(None), *conditions)
    counts = {row.bucket: row.count for row in conn.execute(query.group_by(literal_column("1")))}
    labels = [label for _, label in DAY_BUCKETS] + [LAST_BUCKET]
    return [{"bucket": label, "count": counts.get(label, 0)} for label in labels]


def late_buckets(conn: Connection, filters: TicketFilters, ctx: QueryContext) -> list[PlainRow]:
    """Open tickets past the solve deadline, grouped by days late."""
    conditions = [*filter_conditions(filters, ctx), t.c.situation == "open"]
    return _bucket_counts(conn, solve_late_days(ctx), conditions)


def aging_buckets(conn: Connection, filters: TicketFilters, ctx: QueryContext) -> list[PlainRow]:
    """Open backlog grouped by days since creation."""
    return _bucket_counts(conn, open_age_days(ctx), filter_conditions(filters, ctx))
