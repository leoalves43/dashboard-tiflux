"""FastAPI dependencies: DB connection, query context and parsed filters."""

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, Query, Request
from sqlalchemy import Connection, Engine

from app.config import Settings
from app.filters import TicketFilters
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
