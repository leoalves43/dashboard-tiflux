"""FastAPI dependencies: DB connection, query context and parsed filters."""

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, Query, Request
from sqlalchemy import Connection, Engine

from app.config import Settings
from app.filters import TicketFilters
from app.queries.overview import Granularity
from app.queries.ticket_list import SortDirection
from app.sla import QueryContext


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_connection(request: Request) -> Iterator[Connection]:
    engine: Engine = request.app.state.engine
    with engine.connect() as conn:
        yield conn


def get_context(settings: Annotated[Settings, Depends(get_settings)]) -> QueryContext:
    return QueryContext(now=datetime.now(UTC), timezone=settings.tz)


Conn = Annotated[Connection, Depends(get_connection)]
Ctx = Annotated[QueryContext, Depends(get_context)]
Filters = Annotated[TicketFilters, Query()]


# FastAPI only expands a Pydantic query model when it is the sole query parameter,
# so endpoints needing extra params get a subclass instead of a second argument.
class TimeseriesQuery(TicketFilters):
    granularity: Granularity = "month"


class TicketSortQuery(TicketFilters):
    sort: str = "created_at"
    direction: SortDirection = "desc"


class TicketPageQuery(TicketSortQuery):
    page: int = 1
    page_size: int = 50
