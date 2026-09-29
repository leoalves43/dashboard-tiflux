"""Read endpoints consumed by the dashboard UI."""

from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query

from app.queries import breakdown as breakdown_queries
from app.queries import options, overview, ticket_list
from app.queries.breakdown import Dimension
from app.queries.metrics import PlainRow
from app.routes.deps import Conn, Ctx, Filters, TicketPageQuery, TimeseriesQuery

router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/options")
def get_options(conn: Conn) -> PlainRow:
    return options.filter_options(conn)


@router.get("/sync-status")
def get_sync_status(conn: Conn) -> PlainRow:
    return options.sync_status(conn)


@router.get("/kpis")
def get_kpis(conn: Conn, ctx: Ctx, filters: Filters) -> PlainRow:
    return overview.kpis(conn, filters, ctx)


@router.get("/timeseries")
def get_timeseries(conn: Conn, ctx: Ctx, query: Annotated[TimeseriesQuery, Query()]) -> list[PlainRow]:
    return overview.timeseries(conn, query, query.granularity, ctx)


@router.get("/buckets/{kind}")
def get_buckets(kind: str, conn: Conn, ctx: Ctx, filters: Filters) -> list[PlainRow]:
    if kind == "late":
        return overview.late_buckets(conn, filters, ctx)
    if kind == "aging":
        return overview.aging_buckets(conn, filters, ctx)
    raise HTTPException(404, f"bucket kind={kind!r}; expected 'late' or 'aging'")


@router.get("/breakdown/{dimension}")
def get_breakdown(dimension: Dimension, conn: Conn, ctx: Ctx, filters: Filters) -> list[PlainRow]:
    return breakdown_queries.breakdown(conn, dimension, filters, ctx)


@router.get("/tickets")
def get_tickets(conn: Conn, ctx: Ctx, query: Annotated[TicketPageQuery, Query()]) -> dict[str, Any]:
    try:
        return ticket_list.list_tickets(conn, query, ctx, sort=query.sort, direction=query.direction,
                                        page=query.page, page_size=query.page_size)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
