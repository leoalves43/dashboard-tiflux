"""Global dashboard filters -> SQL WHERE conditions. Shared by charts, tables and exports."""

from datetime import date, datetime, time, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field
from sqlalchemy import ColumnElement, Text, cast, or_

from app.db import tickets as t
from app.sla import QueryContext, is_stage_late, sla_state

Situation = Literal["open", "closed", "canceled"]
SlaState = Literal["late", "on_time", "no_sla"]
UNASSIGNED_ID = 0  # responsible_ids=0 selects tickets without a responsible technician


class TicketFilters(BaseModel):
    """Example: TicketFilters(desk_ids=[37964], situations=["open"], sla=["late"])"""

    date_field: Literal["created", "solved"] = "created"
    date_from: date | None = None
    date_to: date | None = None
    desk_ids: list[int] = Field(default_factory=list)
    client_ids: list[int] = Field(default_factory=list)
    responsible_ids: list[int] = Field(default_factory=list)
    priority_names: list[str] = Field(default_factory=list)
    stage_names: list[str] = Field(default_factory=list)
    situations: list[Situation] = Field(default_factory=list)
    sla: list[SlaState] = Field(default_factory=list)
    stage_late: bool = False
    search: str | None = None


def filter_conditions(filters: TicketFilters, ctx: QueryContext) -> list[ColumnElement[bool]]:
    conditions = _date_conditions(filters, ctx)
    conditions += _membership_conditions(filters)
    if filters.responsible_ids:
        conditions.append(_responsible_condition(filters.responsible_ids))
    if filters.sla:
        conditions.append(sla_state(ctx).in_(filters.sla))
    if filters.stage_late:
        conditions.append(is_stage_late(ctx))
    if filters.search and filters.search.strip():
        conditions.append(_search_condition(filters.search.strip()))
    return conditions


def _date_conditions(filters: TicketFilters, ctx: QueryContext) -> list[ColumnElement[bool]]:
    column = t.c.created_at if filters.date_field == "created" else t.c.solved_at
    zone = ZoneInfo(ctx.timezone)
    conditions: list[ColumnElement[bool]] = []
    if filters.date_from:
        conditions.append(column >= datetime.combine(filters.date_from, time.min, zone))
    if filters.date_to:  # inclusive end date
        next_day = filters.date_to + timedelta(days=1)
        conditions.append(column < datetime.combine(next_day, time.min, zone))
    return conditions


def _membership_conditions(filters: TicketFilters) -> list[ColumnElement[bool]]:
    pairs = [
        (t.c.desk_id, filters.desk_ids),
        (t.c.client_id, filters.client_ids),
        (t.c.priority_name, filters.priority_names),
        (t.c.stage_name, filters.stage_names),
        (t.c.situation, filters.situations),
    ]
    return [column.in_(values) for column, values in pairs if values]


def _responsible_condition(ids: list[int]) -> ColumnElement[bool]:
    real_ids = [value for value in ids if value != UNASSIGNED_ID]
    options = [t.c.responsible_id.in_(real_ids)] if real_ids else []
    if UNASSIGNED_ID in ids:
        options.append(t.c.responsible_id.is_(None))
    return or_(*options)


def _search_condition(term: str) -> ColumnElement[bool]:
    pattern = f"%{term}%"
    columns = [t.c.title, t.c.client_name, t.c.desk_name, t.c.responsible_name, t.c.requestor_name]
    options = [column.ilike(pattern) for column in columns]
    options.append(cast(t.c.ticket_number, Text).like(pattern))
    return or_(*options)
