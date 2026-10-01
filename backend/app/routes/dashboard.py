"""Read endpoints consumed by the dashboard UI."""

from collections.abc import Callable
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query

from app.queries import breakdown as breakdown_queries
from app.queries import options, overview, ticket_detail, ticket_list
from app.queries.breakdown import Dimension
from app.queries.metrics import PlainRow
from app.routes.deps import Conn, Ctx, Filters, TicketPageQuery, Tiflux, TimeseriesQuery
from app.ticket_activity import ActivityItem, load_activity, load_description
from app.tiflux.client import TifluxApiError, TifluxNotFound

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


@router.get("/tickets/{ticket_number}")
def get_ticket_summary(conn: Conn, ticket_number: int) -> PlainRow:
    summary = ticket_detail.ticket_summary(conn, ticket_number)
    if summary is None:
        raise HTTPException(404, f"ticket_number={ticket_number} not found in the local database")
    return summary


def _live_from_tiflux(ticket_number: int, load: Callable[[], ActivityItem]) -> ActivityItem:
    """Maps Tiflux failures to HTTP: 404 when the ticket is gone, 502 when Tiflux is unavailable."""
    try:
        return load()
    except TifluxNotFound as error:
        raise HTTPException(404, f"ticket_number={ticket_number} not found in Tiflux") from error
    except TifluxApiError as error:
        raise HTTPException(502, f"Tiflux unavailable for ticket_number={ticket_number}: {error}") from error


@router.get("/tickets/{ticket_number}/description")
def get_ticket_description(conn: Conn, source: Tiflux, ticket_number: int) -> ActivityItem:
    """From our DB once the sync copied it (spec 003); live from Tiflux until then."""
    copied, description = ticket_detail.stored_description(conn, ticket_number)
    if copied:
        return {"description": description}
    return _live_from_tiflux(ticket_number, lambda: {"description": load_description(source, ticket_number)})


@router.get("/tickets/{ticket_number}/activity")
def get_ticket_activity(source: Tiflux, ticket_number: int) -> ActivityItem:
    """Live from Tiflux (not stored): attachments + answers/internal communications timeline."""
    return _live_from_tiflux(ticket_number, lambda: load_activity(source, ticket_number))
