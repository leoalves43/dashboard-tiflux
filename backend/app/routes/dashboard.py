"""Read endpoints consumed by the dashboard UI."""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.queries import breakdown as breakdown_queries
from app.queries import options, overview, ticket_list
from app.queries.breakdown import Dimension
from app.queries.metrics import PlainRow
from app.queries.overview import Granularity
from app.queries.ticket_list import SortDirection
from app.routes.deps import Conn, Ctx, Filters

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
def get_timeseries(conn: Conn, ctx: Ctx, filters: Filters, granularity: Granularity = "month") -> list[PlainRow]:
    return overview.timeseries(conn, filters, granularity, ctx)


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
def get_tickets(conn: Conn, ctx: Ctx, filters: Filters, sort: str = "created_at",
                direction: SortDirection = "desc", page: int = 1, page_size: int = 50) -> dict[str, Any]:
    try:
        return ticket_list.list_tickets(conn, filters, ctx, sort=sort, direction=direction,
                                        page=page, page_size=page_size)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
