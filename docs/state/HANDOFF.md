# HANDOFF (2026-09-29)
DONE: plan 001 tasks 1–7. Stack up via `docker compose up -d`; UI http://localhost:8080. Backfill complete (164,304 tickets); incremental every 5 min. Backend 40 tests, frontend 8 tests green.
NEXT: optional — link ticket numbers to Tiflux web; business-hours SLA if the API ever exposes calendars; async/background job for full XLSX export (~95 s for all 164k rows).
RISKS: `docker compose down -v` deletes the volume → full re-sync (~15 min). Full-table XLSX export is slow (nginx timeout 300 s). Tickets deleted in Tiflux are never removed locally.
CONTEXT: docs/ARCHITECTURE.md, docs/specs/001-dashboard.md, DESIGN.md.
