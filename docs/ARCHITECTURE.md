# ARCHITECTURE

Tiflux API → `sync` → Postgres 18 (schema `$SCHEMA_NAME`) ← `api` (FastAPI) ← `web` (nginx + React, proxies `/api`).
Compose: `docker-compose.yml`; host ports `DB_PORT` (Postgres) and `WEB_PORT` (UI). Token stays in api/sync only.

## Backend (`backend/app`)
- `config.py` settings from `.env`; `db.py` tables + `ensure_schema` (advisory lock, api and sync both call it).
- `tiflux/client.py` pagination (`offset` = page number, 200/page), waits on `RateLimit-Remaining<=1` and 429.
- `sync/service.py` `TicketSync.run_cycle`: dimensions → one-time backfill (31-day created_at windows walking back until none older; resumable via `sync_state.backfill_cursor`) → incremental (`update_start_datetime` − 10 min overlap, `filter_by=all` then `canceled`). `sync/runner.py` loops every `SYNC_INTERVAL_MINUTES`.
- `sla.py` SLA rules as SQL expressions with `now` bound (see spec § SLA). `filters.py` `TicketFilters` → WHERE; the only filter path for charts, tables and exports.
- `queries/` metrics (shared aggregates), overview (KPIs, series, buckets), breakdown (per dimension), ticket_list (paged + streaming), options.
- `routes/` REST under `/api`, exports under `/api/export/{tickets|breakdown/<dim>|kpis}/{csv|xlsx}`. Query models: see `routes/deps.py` (FastAPI expands a Pydantic query model only when it is the sole query param).

## Frontend (`frontend/src`)
- State lives in the URL hash `#/<page>?<filters>` (`filters/route.ts`), same param names as the API.
- `api/client.ts` typed fetch + `exportUrl`; `charts/` ECharts core wrapper reading CSS tokens; `pages/` one component per tab.

## Tests
`docker compose run --rm --no-deps -v ./backend:/srv api python -m pytest` (query tests use schema `dashboard_test` in the real db); frontend `npm test` runs in the web image build.
