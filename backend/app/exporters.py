"""CSV/XLSX writers for any tabular view (rows as dicts + ordered columns)."""

import csv
import io
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal
from zoneinfo import ZoneInfo

from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.styles import Font
from openpyxl.worksheet.worksheet import Worksheet

ExportFormat = Literal["csv", "xlsx"]
# Excel limits sheet titles to 31 characters.
_SHEET_TITLE_MAX = 31
SITUATION_LABELS = {"open": "Aberto", "closed": "Fechado", "canceled": "Cancelado"}
SLA_LABELS = {"late": "Atrasado", "on_time": "No prazo", "no_sla": "Sem SLA"}


@dataclass(frozen=True)
class ExportColumn:
    key: str
    label: str


def _translate(key: str, value: Any) -> Any:
    if key == "situation":
        return SITUATION_LABELS.get(value, value)
    if key == "sla_state":
        return SLA_LABELS.get(value, value)
    return value


def _excel_value(key: str, value: Any, timezone_name: str) -> Any:
    """openpyxl rejects tz-aware datetimes; show them in local time instead."""
    value = _translate(key, value)
    if isinstance(value, datetime) and value.tzinfo is not None:
        return value.astimezone(ZoneInfo(timezone_name)).replace(tzinfo=None)
    return value


def write_csv(rows: Iterable[dict[str, Any]], columns: Sequence[ExportColumn], timezone_name: str) -> bytes:
    """';' separator and UTF-8 BOM so Excel pt-BR opens it with accents and columns intact."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow([col.label for col in columns])
    for row in rows:
        values = [_excel_value(col.key, row.get(col.key), timezone_name) for col in columns]
        writer.writerow([_csv_text(value) for value in values])
    return ("﻿" + buffer.getvalue()).encode("utf-8")


def _csv_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y %H:%M")
    if isinstance(value, float):
        return f"{value:.1f}".replace(".", ",")
    return str(value)


def write_xlsx(rows: Iterable[dict[str, Any]], columns: Sequence[ExportColumn], title: str,
               timezone_name: str) -> bytes:
    workbook = Workbook(write_only=True)
    sheet = workbook.create_sheet(title=title[:_SHEET_TITLE_MAX])
    _write_header(sheet, columns)
    for row in rows:
        sheet.append([_excel_value(col.key, row.get(col.key), timezone_name) for col in columns])
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def _write_header(sheet: Worksheet, columns: Sequence[ExportColumn]) -> None:
    sheet.freeze_panes = "A2"
    cells = []
    for col in columns:
        cell = WriteOnlyCell(sheet, value=col.label)
        cell.font = Font(bold=True)
        cells.append(cell)
    sheet.append(cells)


def export_bytes(fmt: ExportFormat, rows: Iterable[dict[str, Any]], columns: Sequence[ExportColumn],
                 title: str, timezone_name: str) -> bytes:
    """Example: export_bytes("xlsx", rows, [ExportColumn("name", "Mesa")], "Por mesa", "America/Sao_Paulo")"""
    if fmt == "csv":
        return write_csv(rows, columns, timezone_name)
    return write_xlsx(rows, columns, title, timezone_name)
