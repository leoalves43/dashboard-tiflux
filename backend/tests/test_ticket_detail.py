from sqlalchemy import Engine

from app.queries.ticket_detail import ticket_summary


def test_ticket_summary_reads_local_columns(engine: Engine) -> None:
    with engine.connect() as conn:
        summary = ticket_summary(conn, 1)
    assert summary is not None
    assert (summary["requestor_name"], summary["client_name"], summary["desk_name"]) == ("Fulano", "Cliente A", "SUPORTE")
    assert (summary["status_name"], summary["stage_name"], summary["priority_name"]) == ("Aberto", "Pendente", "Alta")
    assert summary["responsible_name"] == "Técnico X"


def test_ticket_summary_is_none_for_unknown_ticket(engine: Engine) -> None:
    with engine.connect() as conn:
        assert ticket_summary(conn, 999_999) is None
