from datetime import UTC, datetime

import pytest

from app.sync.mapper import derive_situation, map_ticket
from tests.fakes import make_ticket


def test_map_ticket_flattens_refs_and_sla_dates() -> None:
    item = make_ticket(1, "2026-09-01T10:00:00Z", services_catalog={
        "catalog_name": "Finanças", "area_name": "PEC", "item_name": "Dúvidas"})
    item["sla_info"]["solve_expiration"] = "2026-09-03T10:00:00Z"
    row = map_ticket(item)
    assert row["desk_name"] == "SUPORTE" and row["client_id"] == 20
    assert row["services_catalog"] == "Finanças / PEC / Dúvidas"
    assert row["solve_expiration"] == datetime(2026, 9, 3, 10, tzinfo=UTC)
    assert row["situation"] == "open"
    assert row["raw"] is item


def test_map_ticket_tolerates_missing_responsible() -> None:
    assert map_ticket(make_ticket(1, "2026-09-01T10:00:00Z", responsible=None))["responsible_id"] is None


@pytest.mark.parametrize(("is_closed", "status", "expected"), [
    (False, "Opened", "open"),
    (True, "Closed", "closed"),
    (True, "Canceled", "canceled"),
    (True, "Cancelado", "canceled"),
])
def test_derive_situation(is_closed: bool, status: str, expected: str) -> None:
    item = make_ticket(1, "2026-09-01T10:00:00Z", is_closed=is_closed, status={"id": 1, "name": status})
    assert derive_situation(item) == expected


def test_explicit_situation_overrides_and_is_validated() -> None:
    item = make_ticket(1, "2026-09-01T10:00:00Z", is_closed=True)
    assert map_ticket(item, "canceled")["situation"] == "canceled"
    with pytest.raises(ValueError, match="'bogus'"):
        map_ticket(item, "bogus")


def test_map_ticket_translates_tiflux_default_names() -> None:
    item = make_ticket(1, "2026-09-01T10:00:00Z", status={"id": 1, "name": "Opened"},
                       stage={"id": 2, "name": "Pending"}, priority={"id": 3, "name": "High"})
    row = map_ticket(item)
    assert (row["status_name"], row["stage_name"], row["priority_name"]) == ("Aberto", "Pendente", "Alta")
    assert row["raw"]["status"]["name"] == "Opened"


def test_map_ticket_keeps_custom_names() -> None:
    item = make_ticket(1, "2026-09-01T10:00:00Z", status={"id": 1, "name": "Em Atendimento"})
    assert map_ticket(item)["status_name"] == "Em Atendimento"
