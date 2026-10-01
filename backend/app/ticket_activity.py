"""Live description, follow-ups (answers + internal communications) and attachments of one ticket, read from Tiflux.

Not stored locally on purpose: the project runs on a local PC (see docs/decisions/LOG.md 2026-10-01).
"""

from typing import Any, Literal

from app.tiflux.client import JsonObject, TifluxNotFound, TifluxSource

FollowupKind = Literal["answer", "internal"]
ActivityItem = dict[str, Any]

# Tiflux paths per follow-up kind and the field holding the text (answers keep it in `name`).
_FOLLOWUP_PATHS: dict[FollowupKind, str] = {"answer": "answers", "internal": "internal_communications"}
_TEXT_FIELD: dict[FollowupKind, str] = {"answer": "name", "internal": "text"}


def map_file(item: JsonObject) -> ActivityItem:
    """Example: map_file({"id": 1, "file_name": "a.png", "size": "10", ...}) -> {"id": 1, "size": 10, ...}"""
    size = item.get("size")
    return {
        "id": int(item["id"]),
        "file_name": item.get("file_name"),
        "content_type": item.get("content_type"),
        "size": int(size) if size not in (None, "") else None,
        "url": item.get("url"),
    }


def _author(kind: FollowupKind, item: JsonObject) -> str | None:
    if kind == "answer":
        return item.get("author")
    user = item.get("user")
    name = user.get("name") if isinstance(user, dict) else None
    # Comments synced from GitHub/Jira come with an empty user (seen on ticket 364000, 2026-10-01).
    return name or item.get("github_username") or item.get("jira_username")


def map_followup(kind: FollowupKind, item: JsonObject, files: list[JsonObject]) -> ActivityItem:
    """Answers and internal communications share one timeline shape."""
    return {
        "kind": kind,
        "id": int(item["id"]),
        "author": _author(kind, item),
        "created_at": item.get("answer_time") if kind == "answer" else item.get("created_at"),
        "text": item.get(_TEXT_FIELD[kind]),
        "files": [map_file(file) for file in files],
    }


def _all_items(source: TifluxSource, path: str) -> list[JsonObject]:
    return [item for page in source.iter_pages(path, {}) for item in page]


def _followup_files(source: TifluxSource, path: str, item: JsonObject) -> list[JsonObject]:
    """List payloads only carry files_count; the detail call (one request) is made only when needed."""
    if int(item.get("files_count") or 0) == 0:
        return []
    detail = source.fetch_one(f"{path}/{item['id']}")
    return list(detail.get("files") or []) if detail else []


def _followups(source: TifluxSource, ticket_number: int, kind: FollowupKind) -> list[ActivityItem]:
    path = f"/tickets/{ticket_number}/{_FOLLOWUP_PATHS[kind]}"
    return [map_followup(kind, item, _followup_files(source, path, item)) for item in _all_items(source, path)]


def load_activity(source: TifluxSource, ticket_number: int) -> ActivityItem:
    """Example: load_activity(client, 363981) -> {"files": [...], "followups": [...oldest first]}.

    Raises TifluxNotFound when the ticket no longer exists in Tiflux.
    """
    files = [map_file(item) for item in _all_items(source, f"/tickets/{ticket_number}/files")]
    followups = _followups(source, ticket_number, "answer") + _followups(source, ticket_number, "internal")
    followups.sort(key=lambda followup: followup["created_at"] or "")
    return {"files": files, "followups": followups}


def load_description(source: TifluxSource, ticket_number: int) -> str | None:
    """Example: load_description(client, 363981) -> "<div>...</div>"; list payloads omit it, so one detail call.

    Raises TifluxNotFound when the ticket no longer exists in Tiflux.
    """
    detail = source.fetch_one(f"/tickets/{ticket_number}")
    if detail is None:
        raise TifluxNotFound(f"GET /tickets/{ticket_number} -> 404")
    return detail.get("description")
