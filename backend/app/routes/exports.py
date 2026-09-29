"""Export endpoints: every view downloads as CSV or XLSX with the same filters as the screen."""

from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Response

from app.config import Settings
from app.exporters import ExportColumn, ExportFormat, export_bytes
from app.queries import breakdown as breakdown_queries
from app.queries.breakdown import DIMENSIONS, Dimension
from app.queries.metrics import METRIC_COLUMNS
from app.queries.overview import kpis
from app.queries.ticket_list import LIST_COLUMNS, SortDirection, iter_all_tickets
from app.routes.deps import Conn, Ctx, Filters, get_settings

router = APIRouter(prefix="/api/export")
MEDIA_TYPES = {
    "csv": "text/csv; charset=utf-8",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
AppSettings = Annotated[Settings, Depends(get_settings)]


def _download(content: bytes, fmt: ExportFormat, basename: str, tz: str) -> Response:
    stamp = datetime.now(ZoneInfo(tz)).strftime("%Y%m%d-%H%M")
    headers = {"Content-Disposition": f'attachment; filename="{basename}-{stamp}.{fmt}"'}
    return Response(content, media_type=MEDIA_TYPES[fmt], headers=headers)


@router.get("/tickets/{fmt}")
def export_tickets(fmt: ExportFormat, conn: Conn, ctx: Ctx, filters: Filters, settings: AppSettings,
                   sort: str = "created_at", direction: SortDirection = "desc") -> Response:
    try:
        rows = iter_all_tickets(conn, filters, ctx, sort=sort, direction=direction)
        content = export_bytes(fmt, rows, LIST_COLUMNS, "Chamados", settings.tz)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    return _download(content, fmt, "chamados", settings.tz)


@router.get("/breakdown/{dimension}/{fmt}")
def export_breakdown(dimension: Dimension, fmt: ExportFormat, conn: Conn, ctx: Ctx, filters: Filters,
                     settings: AppSettings) -> Response:
    spec = DIMENSIONS[dimension]
    rows = breakdown_queries.breakdown(conn, dimension, filters, ctx)
    columns = [ExportColumn("name", spec.label), *METRIC_COLUMNS]
    content = export_bytes(fmt, rows, columns, f"Por {spec.label}", settings.tz)
    return _download(content, fmt, f"por-{dimension}", settings.tz)


@router.get("/kpis/{fmt}")
def export_kpis(fmt: ExportFormat, conn: Conn, ctx: Ctx, filters: Filters, settings: AppSettings) -> Response:
    content = export_bytes(fmt, [kpis(conn, filters, ctx)], METRIC_COLUMNS, "Indicadores", settings.tz)
    return _download(content, fmt, "indicadores", settings.tz)
