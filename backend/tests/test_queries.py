from datetime import date

import pytest
from sqlalchemy import Engine

from app.filters import TicketFilters
from app.queries.breakdown import breakdown
from app.queries.overview import aging_buckets, kpis, late_buckets, timeseries
from app.queries.ticket_list import iter_all_tickets, list_tickets
from app.sla import QueryContext


def _kpis(engine: Engine, ctx: QueryContext, **filters: object) -> dict[str, object]:
    with engine.connect() as conn:
        return kpis(conn, TicketFilters(**filters), ctx)


def test_kpis_follow_sla_definition(engine: Engine, ctx: QueryContext) -> None:
    result = _kpis(engine, ctx)
    assert (result["total"], result["open"], result["closed"], result["canceled"]) == (6, 3, 2, 1)
    assert (result["late"], result["on_time"], result["no_sla"]) == (2, 2, 2)
    assert result["pct_sla"] == 50.0
    assert (result["open_late"], result["stage_late"]) == (1, 1)
    assert (result["avg_late_days"], result["max_late_days"]) == (6.0, 10.0)
    assert result["avg_resolution_hours"] == 144.0


@pytest.mark.parametrize(("filters", "expected_total"), [
    ({"sla": ["late"]}, 2),
    ({"situations": ["open"], "sla": ["late"]}, 1),
    ({"responsible_ids": [0]}, 1),
    ({"responsible_ids": [0, 30]}, 6),
    ({"desk_ids": [11]}, 1),
    ({"search": "infra"}, 1),
    ({"stage_late": True}, 1),
    ({"date_from": date(2026, 9, 1), "date_to": date(2026, 9, 10)}, 3),
    ({"date_field": "solved", "date_from": date(2026, 9, 12)}, 1),
])
def test_filters_narrow_the_set(engine: Engine, ctx: QueryContext, filters: dict[str, object],
                                expected_total: int) -> None:
    assert _kpis(engine, ctx, **filters)["total"] == expected_total


def test_breakdown_by_responsible_names_unassigned(engine: Engine, ctx: QueryContext) -> None:
    with engine.connect() as conn:
        rows = {row["key"]: row for row in breakdown(conn, "responsible", TicketFilters(), ctx)}
    assert rows["0"]["name"] == "Sem responsável" and rows["0"]["total"] == 1
    assert rows["30"]["total"] == 5 and rows["30"]["late"] == 2


def test_list_sorts_by_late_days_and_pages(engine: Engine, ctx: QueryContext) -> None:
    with engine.connect() as conn:
        result = list_tickets(conn, TicketFilters(), ctx, sort="late_days", direction="desc", page=1, page_size=2)
    assert result["total"] == 6
    assert [row["ticket_number"] for row in result["rows"]] == [1, 3]
    assert result["rows"][0]["late_days"] == 10.0 and result["rows"][0]["sla_state"] == "late"


def test_list_rejects_unknown_sort(engine: Engine, ctx: QueryContext) -> None:
    with engine.connect() as conn, pytest.raises(ValueError, match="'nope'"):
        list_tickets(conn, TicketFilters(), ctx, sort="nope", direction="asc", page=1, page_size=10)


def test_export_iterator_returns_every_filtered_row(engine: Engine, ctx: QueryContext) -> None:
    with engine.connect() as conn:
        rows = list(iter_all_tickets(conn, TicketFilters(situations=["closed"]), ctx,
                                     sort="created_at", direction="asc"))
    assert [row["ticket_number"] for row in rows] == [3, 4]


def test_buckets_and_timeseries(engine: Engine, ctx: QueryContext) -> None:
    with engine.connect() as conn:
        late = {row["bucket"]: row["count"] for row in late_buckets(conn, TicketFilters(), ctx)}
        aging = {row["bucket"]: row["count"] for row in aging_buckets(conn, TicketFilters(), ctx)}
        series = timeseries(conn, TicketFilters(), "month", ctx)
    assert late["8–15 dias"] == 1 and sum(late.values()) == 1
    assert aging["> 30 dias"] == 1 and sum(aging.values()) == 3
    assert series == [
        {"period": "2026-08-01", "created": 1, "solved": 0},
        {"period": "2026-09-01", "created": 5, "solved": 2},
    ]
