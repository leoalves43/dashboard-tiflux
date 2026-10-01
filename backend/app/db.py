"""Database engine and table definitions (schema comes from SCHEMA_NAME via search_path)."""

import re

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Engine,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    create_engine,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.config import Settings

metadata = MetaData()

tickets = Table(
    "tickets",
    metadata,
    Column("ticket_number", BigInteger, primary_key=True),
    Column("title", Text),
    Column("situation", Text, nullable=False),  # open | closed | canceled
    Column("status_id", BigInteger),
    Column("status_name", Text),
    Column("stage_id", BigInteger),
    Column("stage_name", Text),
    Column("priority_id", BigInteger),
    Column("priority_name", Text),
    Column("desk_id", BigInteger),
    Column("desk_name", Text),
    Column("client_id", BigInteger),
    Column("client_name", Text),
    Column("responsible_id", BigInteger),
    Column("responsible_name", Text),
    Column("requestor_name", Text),
    Column("requestor_email", Text),
    Column("services_catalog", Text),
    Column("created_by_way_of", Text),
    Column("reopen_count", Integer),
    Column("created_at", DateTime(timezone=True)),
    Column("updated_at", DateTime(timezone=True)),
    Column("solved_at", DateTime(timezone=True)),
    Column("attend_expiration", DateTime(timezone=True)),
    Column("solve_expiration", DateTime(timezone=True)),
    Column("stage_expiration", DateTime(timezone=True)),
    Column("sla_stopped", Boolean),
    Column("raw", JSONB, nullable=False),
    Column("synced_at", DateTime(timezone=True), server_default=text("now()")),
    Index("ix_tickets_created_at", "created_at"),
    Index("ix_tickets_solved_at", "solved_at"),
    Index("ix_tickets_desk", "desk_id"),
    Index("ix_tickets_client", "client_id"),
    Index("ix_tickets_responsible", "responsible_id"),
    Index("ix_tickets_situation", "situation"),
)

clients = Table(
    "clients",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("name", Text),
    Column("social", Text),
    Column("active", Boolean),
    Column("raw", JSONB, nullable=False),
)

desks = Table(
    "desks",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("name", Text),
    Column("display_name", Text),
    Column("active", Boolean),
    Column("raw", JSONB, nullable=False),
)

technicians = Table(
    "technicians",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("name", Text),
    Column("email", Text),
    Column("raw", JSONB, nullable=False),
)

sync_state = Table(
    "sync_state",
    metadata,
    Column("key", Text, primary_key=True),
    Column("value", Text, nullable=False),
    Column("updated_at", DateTime(timezone=True), server_default=text("now()")),
)

_SCHEMA_PATTERN = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")
# Arbitrary constant so api and sync never race on CREATE TABLE.
_SCHEMA_LOCK_ID = 7_331_001


def validate_schema_name(schema: str) -> str:
    """Schema goes into DDL/search_path unquoted, so only plain identifiers are allowed."""
    if not _SCHEMA_PATTERN.match(schema):
        raise ValueError(f"SCHEMA_NAME={schema!r} invalid; expected lowercase identifier [a-z_][a-z0-9_]*")
    return schema


def build_engine(settings: Settings) -> Engine:
    """Engine whose connections resolve unqualified tables inside SCHEMA_NAME.

    Example: engine = build_engine(Settings())
    """
    schema = validate_schema_name(settings.schema_name)
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        connect_args={"options": f"-csearch_path={schema}"},
    )


def ensure_schema(engine: Engine, schema: str) -> None:
    """Create schema and tables if missing; safe to call concurrently from several services."""
    schema = validate_schema_name(schema)
    with engine.begin() as conn:
        conn.execute(text("SELECT pg_advisory_xact_lock(:id)"), {"id": _SCHEMA_LOCK_ID})
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        metadata.create_all(conn)
