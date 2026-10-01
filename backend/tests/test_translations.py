from sqlalchemy import Engine, select, update

from app.db import tickets
from app.sync.store import SyncStore
from app.sync.translations import translate_name


def test_translate_name_maps_known_and_passes_unknown() -> None:
    assert translate_name("Canceled") == "Cancelado"
    assert translate_name("BLOCKs") == "BLOCKs"
    assert translate_name(None) is None


def test_translate_stored_names_rewrites_legacy_rows(engine: Engine) -> None:
    """Rows synced before the de-para still hold English names until the sync worker starts."""
    with engine.begin() as conn:
        conn.execute(update(tickets).where(tickets.c.ticket_number == 1)
                     .values(status_name="Opened", priority_name="High"))
    assert SyncStore(engine).translate_stored_names() == 2
    with engine.connect() as conn:
        row = conn.execute(select(tickets.c.status_name, tickets.c.priority_name)
                           .where(tickets.c.ticket_number == 1)).one()
    assert tuple(row) == ("Aberto", "Alta")
    assert SyncStore(engine).translate_stored_names() == 0
