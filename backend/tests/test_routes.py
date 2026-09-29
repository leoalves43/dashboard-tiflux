"""HTTP-level checks: filters must parse alongside endpoint-specific query params (regression)."""

import io
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from openpyxl import load_workbook
from sqlalchemy import Engine

from app.config import Settings
from app.main import create_app
from tests.conftest import TEST_SCHEMA


@pytest.fixture(scope="module")
def client(engine: Engine) -> Iterator[TestClient]:
    app = create_app(Settings(schema_name=TEST_SCHEMA))  # type: ignore[call-arg]
    with TestClient(app) as test_client:
        yield test_client


def test_timeseries_accepts_filters_and_granularity(client: TestClient) -> None:
    response = client.get("/api/timeseries", params={"granularity": "day", "desk_ids": [11]})
    assert response.status_code == 200, response.text
    assert response.json() == [{"period": "2026-09-25", "created": 1, "solved": 0}]


def test_tickets_accepts_filters_sort_and_paging(client: TestClient) -> None:
    params = {"situations": ["closed"], "sort": "ticket_number", "direction": "asc", "page_size": 1}
    body = client.get("/api/tickets", params=params).json()
    assert body["total"] == 2
    assert [row["ticket_number"] for row in body["rows"]] == [3]


def test_invalid_sort_is_422_with_value(client: TestClient) -> None:
    response = client.get("/api/tickets", params={"sort": "drop table"})
    assert response.status_code == 422 and "drop table" in response.text


def test_ticket_export_matches_filtered_rows(client: TestClient) -> None:
    response = client.get("/api/export/tickets/xlsx", params={"situations": ["open"], "sort": "late_days"})
    assert response.status_code == 200
    rows = list(load_workbook(io.BytesIO(response.content)).active.iter_rows(values_only=True))
    assert len(rows) == 1 + 3  # header + open tickets A, B, F


def test_breakdown_export_csv(client: TestClient) -> None:
    response = client.get("/api/export/breakdown/desk/csv", params={"sla": ["late"]})
    lines = response.content.decode("utf-8-sig").splitlines()
    assert lines[0].startswith("Mesa;Total;")
    assert lines[1].startswith("SUPORTE;2;")
