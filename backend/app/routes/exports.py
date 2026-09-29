"""Export endpoints: every view downloads as CSV or XLSX with the same filters as the screen."""

from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from app.config import Settings
from app.exporters import ExportColumn, ExportFormat, export_bytes
from app.queries import breakdown as breakdown_queries
from app.queries.breakdown import DIMENSIONS, Dimension
from app.queries.metrics import METRIC_COLUMNS
from app.queries.overview import aging_buckets, kpis, late_buckets, timeseries
from app.queries.ticket_list import LIST_COLUMNS, iter_all_tickets
from app.routes.deps import Conn, Ctx, Filters, TicketSortQuery, TimeseriesQuery, get_settings

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
def export_tickets(fmt: ExportFormat, conn: Conn, ctx: Ctx, settings: AppSettings,
                   query: Annotated[TicketSortQuery, Query()]) -> Response:
    try:
        rows = iter_all_tickets(conn, query, ctx, sort=query.sort, direction=query.direction)
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


SERIES_COLUMNS = [ExportColumn("period", "Período (início)"), ExportColumn("created", "Abertos"),
                  ExportColumn("solved", "Resolvidos")]
BUCKET_COLUMNS = [ExportColumn("bucket", "Faixa"), ExportColumn("count", "Chamados")]
BUCKET_QUERIES = {"late": (late_buckets, "Atraso por faixa"), "aging": (aging_buckets, "Backlog por idade")}


@router.get("/timeseries/{fmt}")
def export_timeseries(fmt: ExportFormat, conn: Conn, ctx: Ctx, settings: AppSettings,
                      query: Annotated[TimeseriesQuery, Query()]) -> Response:
    rows = timeseries(conn, query, query.granularity, ctx)
    content = export_bytes(fmt, rows, SERIES_COLUMNS, "Abertos x resolvidos", settings.tz)
    return _download(content, fmt, f"serie-{query.granularity}", settings.tz)


@router.get("/buckets/{kind}/{fmt}")
def export_buckets(kind: str, fmt: ExportFormat, conn: Conn, ctx: Ctx, filters: Filters,
                   settings: AppSettings) -> Response:
    if kind not in BUCKET_QUERIES:
        raise HTTPException(404, f"bucket kind={kind!r}; expected one of {sorted(BUCKET_QUERIES)}")
    load, title = BUCKET_QUERIES[kind]
    content = export_bytes(fmt, load(conn, filters, ctx), BUCKET_COLUMNS, title, settings.tz)
    return _download(content, fmt, f"faixas-{kind}", settings.tz)
