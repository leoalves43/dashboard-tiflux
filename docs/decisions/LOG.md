2026-09-29 | Docker Compose stack (postgres:18.6-alpine, python:3.14-slim, node:26-alpine→nginx:alpine) | user asked for Docker + latest versions | memory "no-docker" (applied to old PHP project only)
2026-09-29 | Late = solve_expiration passed (calendar days); stage deadline is a separate indicator; no deadline or canceled = "sem SLA" | user choice; API has no business-hours calendar | -
2026-09-29 | Full history backfill in 31-day created_at windows, then incremental by updated_at | offset paging over 164k rows drifts as tickets arrive; windows are stable and resumable | -
2026-09-29 | Canceled detected by filter_by=canceled pass (list payload has no canceled flag), status name 'Cancel*' as fallback | canceled tickets come back as is_closed=true | -
2026-09-29 | Query tests run against real Postgres in schema dashboard_test instead of fakes | SQL is the unit under test; Tiflux I/O still uses named fakes | -
2026-09-29 | CSV uses ';' + UTF-8 BOM + decimal comma | Excel pt-BR opens it correctly | -
2026-09-29 | Python row/JSON types use Any (JsonObject, Row, PlainRow) | raw Tiflux JSON and SQL rows are heterogeneous; typed at the column level in db.py | CLAUDE.md 'no any' (deliberate exception)
