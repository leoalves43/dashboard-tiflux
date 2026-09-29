# HANDOFF (2026-09-29)
DONE: plan 001 tasks 1–7. Stack up via `docker compose up -d`; UI http://localhost:8080. Backfill complete (164,304 tickets); incremental every 5 min. Backend 42 tests, frontend 9 tests green. Counts vs API (same minute): open 697=697, canceled 1628=1628, closed 161981 vs 161980.
NEXT: optional — link ticket numbers to Tiflux web; business-hours SLA if the API ever exposes calendars; async/background job for full XLSX export (~95 s for all 164k rows).
RISKS: `docker compose down -v` deletes the volume → full re-sync (~15 min). Full-table XLSX export is slow (~95 s, nginx timeout 300 s). Tickets deleted in Tiflux stay locally (2026-09-29: local closed = API + 1, likely one deletion).
CONTEXT: docs/ARCHITECTURE.md, docs/specs/001-dashboard.md, DESIGN.md.
