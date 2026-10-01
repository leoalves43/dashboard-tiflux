2026-09-29 | Docker Compose stack (postgres:18.6-alpine, python:3.14-slim, node:26-alpine→nginx:alpine) | user asked for Docker + latest versions | memory "no-docker" (applied to old PHP project only)
2026-09-29 | Late = solve_expiration passed (calendar days); stage deadline is a separate indicator; no deadline or canceled = "sem SLA" | user choice; API has no business-hours calendar | -
2026-09-29 | Full history backfill in 31-day created_at windows, then incremental by updated_at | offset paging over 164k rows drifts as tickets arrive; windows are stable and resumable | -
2026-09-29 | Canceled detected by filter_by=canceled pass (list payload has no canceled flag), status name 'Cancel*' as fallback | canceled tickets come back as is_closed=true | -
2026-09-29 | Query tests run against real Postgres in schema dashboard_test instead of fakes | SQL is the unit under test; Tiflux I/O still uses named fakes | -
2026-09-29 | CSV uses ';' + UTF-8 BOM + decimal comma | Excel pt-BR opens it correctly | -
2026-09-29 | Python row/JSON types use Any (JsonObject, Row, PlainRow) | raw Tiflux JSON and SQL rows are heterogeneous; typed at the column level in db.py | CLAUDE.md 'no any' (deliberate exception)
2026-09-29 | Each sync cycle reconciles open tickets against filter_by=open and refetches/deletes the stale ones | closing/merging/deleting may not bump updated_at, so incremental alone can leave ghosts open | -
2026-09-30 | Drop compose `db` service; use shared "Postgres" container via host.docker.internal | one Postgres for all projects | Postgres 18 db service in compose
2026-10-01 | De-para EN->pt-BR of Tiflux default status/stage/priority names at ingestion (app/sync/translations.py); sync start rewrites legacy rows | dashboard all in Portuguese; raw keeps original | -
2026-10-01 | Visual refresh: cool-tinted surfaces, brand gradient, KPI tones, table pills (DESIGN.md "Color accents") | user asked for a more colorful UI; data colors unchanged and re-validated | neutral gray surfaces; dark ordinal ramp 300→600 (failed adjacent ΔL)
2026-10-01 | Ticket modal reads follow-ups/attachments live from Tiflux (via api), not stored | project runs on a local PC; storing all history costs a ~3-day backfill. Revisit (store everything) if moved to a server | -
2026-10-01 | Ticket description also read live (GET /tickets/{n}) for hover/modal | Tiflux list payload omits description (0 of 164,623 rows have it); storing needs ~164k detail calls (~23 h) | spec 002 'hover never calls Tiflux'
2026-10-01 | nginx: index.html no-cache, /assets/ immutable 1y | browsers kept the old bundle after rebuilds; Vite fingerprints assets | -
2026-10-01 | nginx re-resolves `api` via Docker DNS (resolver 127.0.0.11 + variable proxy_pass) | recreating the api container changed its IP and every /api call returned 502 until web restarted | literal proxy_pass http://api:8000
