"""SLA rules as SQL expressions (see docs/specs/001-dashboard.md § SLA).

`now` is a bound parameter instead of now() so results are reproducible in tests.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import ColumnElement, Numeric, and_, case, cast, extract, func, literal, or_

from app.db import tickets as t

SLA_LATE = "late"
SLA_ON_TIME = "on_time"
SLA_NONE = "no_sla"
SLA_STATES = (SLA_LATE, SLA_ON_TIME, SLA_NONE)
SECONDS_PER_DAY = 86400.0


@dataclass(frozen=True)
class QueryContext:
    """Reference instant for 'late' checks and the timezone used for calendar grouping."""

    now: datetime
    timezone: str = "America/Sao_Paulo"

    def now_param(self) -> ColumnElement[datetime]:
        return literal(self.now, type_=t.c.created_at.type)


def _round1(value: ColumnElement[float]) -> ColumnElement[float]:
    # Postgres only has round(numeric, int); epoch arithmetic may yield double precision.
    return func.round(cast(value, Numeric), 1)


def is_solve_late(ctx: QueryContext) -> ColumnElement[bool]:
    open_late = and_(t.c.situation == "open", t.c.solve_expiration < ctx.now_param())
    closed_late = and_(t.c.situation == "closed", t.c.solved_at > t.c.solve_expiration)
    return and_(t.c.solve_expiration.is_not(None), or_(open_late, closed_late))


def sla_state(ctx: QueryContext) -> ColumnElement[str]:
    """Canceled tickets and tickets without a solve deadline are 'no_sla'."""
    without_sla = or_(t.c.situation == "canceled", t.c.solve_expiration.is_(None))
    return case(
        (without_sla, SLA_NONE),
        (is_solve_late(ctx), SLA_LATE),
        else_=SLA_ON_TIME,
    )


def solve_late_days(ctx: QueryContext) -> ColumnElement[float]:
    """Calendar days past the solve deadline (NULL when not late)."""
    reference = case((t.c.situation == "open", ctx.now_param()), else_=t.c.solved_at)
    days = extract("epoch", reference - t.c.solve_expiration) / SECONDS_PER_DAY
    return case((is_solve_late(ctx), _round1(days)), else_=None)


def is_stage_late(ctx: QueryContext) -> ColumnElement[bool]:
    return and_(t.c.situation == "open", t.c.stage_expiration < ctx.now_param())


def stage_late_days(ctx: QueryContext) -> ColumnElement[float]:
    days = extract("epoch", ctx.now_param() - t.c.stage_expiration) / SECONDS_PER_DAY
    return case((is_stage_late(ctx), _round1(days)), else_=None)


def open_age_days(ctx: QueryContext) -> ColumnElement[float]:
    days = extract("epoch", ctx.now_param() - t.c.created_at) / SECONDS_PER_DAY
    return case((t.c.situation == "open", _round1(days)), else_=None)


def resolution_hours() -> ColumnElement[float]:
    hours = extract("epoch", t.c.solved_at - t.c.created_at) / 3600.0
    return case((t.c.situation == "closed", _round1(hours)), else_=None)
