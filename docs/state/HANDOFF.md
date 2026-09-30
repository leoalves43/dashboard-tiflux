# HANDOFF (2026-09-30)
DONE: plan 001 tasks 1–7. Compose no longer ships Postgres: api/sync use the shared `Postgres` container (db `projetos`, schema `dashboard`) via `host.docker.internal`. Stack recreated; backfill re-running into the shared DB. UI http://localhost:8080.
NEXT: optional — link ticket numbers to Tiflux web; business-hours SLA if the API ever exposes calendars; async job for full XLSX export (~95 s). Old volume `dashboard-tiflux_pgdata` is orphaned — delete when sure.
RISKS: dashboard depends on the external `Postgres` container being up on host port `DB_PORT`. Full-table XLSX export is slow. Deleted tickets only detected while locally open (reconcile_open).
CONTEXT: docs/ARCHITECTURE.md, docs/specs/001-dashboard.md, DESIGN.md.
