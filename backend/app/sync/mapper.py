"""Converts Tiflux API payloads into rows for the local tables."""

from datetime import datetime
from typing import Any

from app.sync.translations import translate_name
from app.tiflux.client import JsonObject

Row = dict[str, Any]
SITUATIONS = ("open", "closed", "canceled")


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def _nested(item: JsonObject, key: str, field: str) -> Any:
    child = item.get(key)
    return child.get(field) if isinstance(child, dict) else None


def derive_situation(item: JsonObject) -> str:
    """Detail payloads flag canceled statuses; list payloads don't, so fall back to the name."""
    if not item.get("is_closed"):
        return "open"
    if _nested(item, "status", "default_canceled"):
        return "canceled"
    status_name = (_nested(item, "status", "name") or "").lower()
    return "canceled" if status_name.startswith("cancel") else "closed"


def _catalog_label(item: JsonObject) -> str | None:
    catalog = item.get("services_catalog")
    if not isinstance(catalog, dict):
        return None
    parts = [catalog.get("catalog_name"), catalog.get("area_name"), catalog.get("item_name")]
    return " / ".join(part for part in parts if part) or None


def map_ticket(item: JsonObject, situation: str | None = None) -> Row:
    """Example: map_ticket(api_item, situation="canceled") when it came from filter_by=canceled."""
    if situation is not None and situation not in SITUATIONS:
        raise ValueError(f"situation={situation!r}; expected one of {SITUATIONS}")
    sla = item.get("sla_info") or {}
    return {
        "ticket_number": item["ticket_number"],
        "title": item.get("title"),
        "situation": situation or derive_situation(item),
        **_ticket_refs(item),
        "created_by_way_of": item.get("created_by_way_of"),
        "reopen_count": item.get("reopen_count"),
        "created_at": parse_datetime(item.get("created_at")),
        "updated_at": parse_datetime(item.get("updated_at")),
        "solved_at": parse_datetime(sla.get("solved_in_time")),
        "attend_expiration": parse_datetime(sla.get("attend_expiration")),
        "solve_expiration": parse_datetime(sla.get("solve_expiration")),
        "stage_expiration": parse_datetime(sla.get("stage_expiration")),
        "sla_stopped": sla.get("stopped"),
        "raw": item,
    }


def _ticket_refs(item: JsonObject) -> Row:
    return {
        "status_id": _nested(item, "status", "id"),
        "status_name": translate_name(_nested(item, "status", "name")),
        "stage_id": _nested(item, "stage", "id"),
        "stage_name": translate_name(_nested(item, "stage", "name")),
        "priority_id": _nested(item, "priority", "id"),
        "priority_name": translate_name(_nested(item, "priority", "name")),
        "desk_id": _nested(item, "desk", "id"),
        "desk_name": _nested(item, "desk", "name"),
        "client_id": _nested(item, "client", "id"),
        "client_name": _nested(item, "client", "name"),
        "responsible_id": _nested(item, "responsible", "id"),
        "responsible_name": _nested(item, "responsible", "name"),
        "requestor_name": _nested(item, "requestor", "name"),
        "requestor_email": _nested(item, "requestor", "email"),
        "services_catalog": _catalog_label(item),
    }


def map_client(item: JsonObject) -> Row:
    return {"id": item["id"], "name": item.get("name"), "social": item.get("social"),
            "active": item.get("status"), "raw": item}


def map_desk(item: JsonObject) -> Row:
    return {"id": item["id"], "name": item.get("name"), "display_name": item.get("display_name"),
            "active": item.get("active"), "raw": item}


def map_technician(item: JsonObject) -> Row:
    return {"id": item["id"], "name": item.get("name"), "email": item.get("email"), "raw": item}
