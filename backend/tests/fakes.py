"""Named fakes for external I/O: Tiflux HTTP, Tiflux source and the sync store."""

from collections.abc import Callable, Collection, Iterator, Sequence
from datetime import datetime, timedelta
from typing import Any

import httpx
from sqlalchemy import Table

from app.sync.descriptions import PendingTicket
from app.tiflux.client import PAGE_SIZE, JsonObject, Page, TifluxApiError, TifluxNotFound


class FakeTifluxHttp:
    """Serves queued responses to httpx.MockTransport and records every request."""

    def __init__(self, responses: list[httpx.Response]) -> None:
        self._responses = responses
        self.requests: list[httpx.Request] = []

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self._responses.pop(0)

    def client(self) -> httpx.Client:
        return httpx.Client(transport=httpx.MockTransport(self.handle))


class FakeSleeper:
    def __init__(self) -> None:
        self.waits: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.waits.append(seconds)


def make_ticket(number: int, created_at: str, **overrides: Any) -> JsonObject:
    ticket: JsonObject = {
        "ticket_number": number,
        "title": f"Chamado {number}",
        "is_closed": False,
        "created_at": created_at,
        "updated_at": created_at,
        "status": {"id": 1, "name": "Opened"},
        "stage": {"id": 2, "name": "Pending"},
        "priority": {"id": 3, "name": "Alta"},
        "desk": {"id": 10, "name": "SUPORTE"},
        "client": {"id": 20, "name": "Cliente A"},
        "responsible": {"id": 30, "name": "Técnico X"},
        "requestor": {"id": None, "name": "Fulano", "email": "f@x.test"},
        "services_catalog": None,
        "sla_info": {"solve_expiration": None, "stage_expiration": None, "solved_in_time": None,
                     "attend_expiration": None, "stopped": False},
    }
    ticket.update(overrides)
    return ticket


class FakeTifluxSource:
    """In-memory Tiflux: `tickets_for(params)` decides which tickets a /tickets query returns."""

    def __init__(self, tickets_for: Callable[[dict[str, str | int]], list[JsonObject]],
                 dimensions: dict[str, list[JsonObject]] | None = None,
                 details: dict[int, JsonObject] | None = None) -> None:
        self._tickets_for = tickets_for
        self._dimensions = dimensions or {}
        self._details = details or {}  # /tickets/<n>; missing number = 404 (deleted)
        self.calls: list[tuple[str, dict[str, str | int]]] = []

    def fetch_one(self, path: str) -> JsonObject | None:
        self.calls.append((path, {}))
        return self._details.get(int(path.rsplit("/", 1)[1]))

    def _items(self, path: str, params: dict[str, str | int]) -> list[JsonObject]:
        self.calls.append((path, dict(params)))
        if path == "/tickets":
            return self._tickets_for(params)
        return self._dimensions.get(path, [])

    def fetch_page(self, path: str, params: dict[str, str | int]) -> Page:
        items = self._items(path, params)
        return Page(items=items[: int(params.get("limit", PAGE_SIZE))], total=len(items))

    def iter_pages(self, path: str, params: dict[str, str | int]) -> Iterator[list[JsonObject]]:
        items = self._items(path, params)
        for start in range(0, len(items), PAGE_SIZE):
            yield items[start : start + PAGE_SIZE]


class FakeSyncStore:
    def __init__(self) -> None:
        self.rows: dict[str, dict[Any, dict[str, Any]]] = {}
        self.state: dict[str, str] = {}

    def upsert(self, table: Table, rows: Sequence[dict[str, Any]], key: str) -> int:
        bucket = self.rows.setdefault(table.name, {})
        for row in rows:
            bucket[row[key]] = row
        return len(rows)

    def ticket_numbers(self, situation: str) -> set[int]:
        return {key for key, row in self.rows.get("tickets", {}).items() if row["situation"] == situation}

    def delete_tickets(self, numbers: Sequence[int]) -> int:
        bucket = self.rows.get("tickets", {})
        return sum(bucket.pop(number, None) is not None for number in numbers)

    def get_state(self, key: str) -> str | None:
        return self.state.get(key)

    def set_state(self, key: str, value: str) -> None:
        self.state[key] = value


class FixedClock:
    def __init__(self, moment: datetime) -> None:
        self.moment = moment

    def __call__(self) -> datetime:
        return self.moment


class FakeActivitySource:
    """Tiflux for one ticket's activity: list payloads by path, detail payloads by path, optional failure."""

    def __init__(self, lists: dict[str, list[JsonObject]], details: dict[str, JsonObject] | None = None,
                 missing: bool = False, failing: bool = False) -> None:
        self._lists = lists
        self._details = details or {}
        self._missing = missing
        self._failing = failing
        self.calls: list[str] = []

    def _guard(self, path: str) -> None:
        self.calls.append(path)
        if self._missing:
            raise TifluxNotFound(f"GET {path} -> 404")
        if self._failing:
            raise TifluxApiError(f"GET {path} -> 503")

    def fetch_page(self, path: str, params: dict[str, str | int]) -> Page:
        self._guard(path)
        items = self._lists.get(path, [])
        return Page(items=items, total=len(items))

    def iter_pages(self, path: str, params: dict[str, str | int]) -> Iterator[list[JsonObject]]:
        self._guard(path)
        yield self._lists.get(path, [])

    def fetch_one(self, path: str) -> JsonObject | None:
        self._guard(path)
        return self._details.get(path)


class TickingClock:
    """Each call advances `step`, so deadline loops end after a predictable number of checks."""

    def __init__(self, start: datetime, step: timedelta) -> None:
        self.now = start
        self._step = step

    def __call__(self) -> datetime:
        current = self.now
        self.now += self._step
        return current


class FakeTicketDetailSource:
    """GET /tickets/<n>: description per number; `missing` answers 404 (None), `failing` raises."""

    def __init__(self, descriptions: dict[int, str], missing: set[int] | None = None,
                 failing: set[int] | None = None) -> None:
        self._descriptions = descriptions
        self._missing = missing or set()
        self._failing = failing or set()
        self.fetched: list[int] = []

    def fetch_one(self, path: str) -> JsonObject | None:
        number = int(path.rsplit("/", 1)[1])
        self.fetched.append(number)
        if number in self._failing:
            raise TifluxApiError(f"GET {path} -> 503")
        if number in self._missing:
            return None
        return {"ticket_number": number, "description": self._descriptions.get(number)}

    def fetch_page(self, path: str, params: dict[str, str | int]) -> Page:
        raise AssertionError(f"description sync must not list {path}")

    def iter_pages(self, path: str, params: dict[str, str | int]) -> Iterator[list[JsonObject]]:
        raise AssertionError(f"description sync must not list {path}")


class FakeDescriptionStore:
    """Mirrors DescriptionStore: pending = never saved, or ticket updated after the saved copy."""

    def __init__(self, tickets_updated_at: dict[int, datetime]) -> None:
        self.tickets_updated_at = tickets_updated_at
        self.saved: dict[int, tuple[str | None, datetime | None]] = {}

    def _is_pending(self, number: int, updated_at: datetime) -> bool:
        if number not in self.saved:
            return True
        copied_at = self.saved[number][1]
        return copied_at is not None and updated_at > copied_at

    def pending_descriptions(self, limit: int, skip: Collection[int]) -> list[PendingTicket]:
        pending = [PendingTicket(n, at) for n, at in self.tickets_updated_at.items()
                   if n not in skip and self._is_pending(n, at)]
        return sorted(pending, key=lambda p: (p.updated_at, p.ticket_number), reverse=True)[:limit]

    def save_description(self, ticket_number: int, description: str | None,
                         ticket_updated_at: datetime | None) -> None:
        self.saved[ticket_number] = (description, ticket_updated_at)

    def description_progress(self) -> tuple[int, int]:
        return len(self.saved), len(self.tickets_updated_at)
