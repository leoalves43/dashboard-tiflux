"""Values for the filter dropdowns and the sync status badge."""

from sqlalchemy import ColumnElement, Connection, distinct, func, select

from app.db import clients, desks, sync_state, technicians
from app.db import tickets as t
from app.queries.metrics import PlainRow


def _id_options(conn: Connection, id_col: ColumnElement[int], name_col: ColumnElement[str]) -> list[PlainRow]:
    """Names from tickets win over the dimension tables because they include inactive entities."""
    query = (
        select(id_col.label("id"), func.max(name_col).label("name"))
        .where(id_col.is_not(None))
        .group_by(id_col)
        .order_by(func.max(name_col))
    )
    return [dict(row) for row in conn.execute(query).mappings()]


def _merge_dimension(from_tickets: list[PlainRow], conn: Connection, table_id: ColumnElement[int],
                     table_name: ColumnElement[str]) -> list[PlainRow]:
    known = {row["id"] for row in from_tickets}
    extra = [dict(row) for row in conn.execute(select(table_id.label("id"), table_name.label("name"))).mappings()
             if row["id"] not in known]
    return sorted(from_tickets + extra, key=lambda row: (row["name"] or "").lower())


def _text_options(conn: Connection, column: ColumnElement[str]) -> list[str]:
    query = select(distinct(column)).where(column.is_not(None)).order_by(column)
    return list(conn.execute(query).scalars())


def filter_options(conn: Connection) -> PlainRow:
    return {
        "desks": _merge_dimension(_id_options(conn, t.c.desk_id, t.c.desk_name), conn, desks.c.id, desks.c.name),
        "clients": _merge_dimension(_id_options(conn, t.c.client_id, t.c.client_name), conn,
                                    clients.c.id, clients.c.name),
        "technicians": _merge_dimension(_id_options(conn, t.c.responsible_id, t.c.responsible_name), conn,
                                        technicians.c.id, technicians.c.name),
        "priorities": _text_options(conn, t.c.priority_name),
        "stages": _text_options(conn, t.c.stage_name),
        "statuses": _text_options(conn, t.c.status_name),
    }


def sync_status(conn: Connection) -> PlainRow:
    state = {row.key: row.value for row in conn.execute(select(sync_state.c.key, sync_state.c.value))}
    totals = conn.execute(select(func.count(), func.max(t.c.synced_at))).one()
    return {
        "backfill_done": state.get("backfill_done") == "1",
        "last_incremental": state.get("last_incremental"),
        "tickets": totals[0],
        "last_write": totals[1].isoformat() if totals[1] else None,
    }
