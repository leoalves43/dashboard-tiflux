# ARCHITECTURE

Tiflux API → `sync` → shared external Postgres (container `Postgres`, not in compose; schema `$SCHEMA_NAME`) ← `api` (FastAPI) ← `web` (nginx + React, proxies `/api`).
Compose: `docker-compose.yml`; api/sync reach the remote DB at `DB_HOST:DB_PORT` (186.250.92.136:5432, LOG 2026-10-02); host port `WEB_PORT` (UI). Token stays in api/sync only. `api` also calls Tiflux live, only for the ticket modal/hover (description, follow-ups, attachments; not stored — LOG 2026-10-01).

## Backend (`backend/app`)
- `config.py` settings from `.env`; `db.py` tables + `ensure_schema` (advisory lock, api and sync both call it).
- `tiflux/client.py` pagination (`offset` = page number, 200/page), waits on `RateLimit-Remaining<=1` and 429.
- `sync/service.py` `TicketSync.run_cycle`: dimensions → one-time backfill (31-day created_at windows walking back until none older; resumable via `sync_state.backfill_cursor`) → incremental (`update_start_datetime` − 10 min overlap, `filter_by=all` then `canceled`) → `reconcile_open` (local open ∖ API open refetched via `/tickets/{n}`; 404 = deleted locally). `sync/runner.py` loops every `SYNC_INTERVAL_MINUTES`.
- `sla.py` SLA rules as SQL expressions with `now` bound (see spec § SLA). `filters.py` `TicketFilters` → WHERE; the only filter path for charts, tables and exports.
- `queries/` metrics (shared aggregates), overview (KPIs, series, buckets), breakdown (per dimension), ticket_list (paged + streaming), options.
- `queries/ticket_detail.py` one ticket's local summary; `ticket_activity.py` live description + follow-ups (answers ∪ internal communications, chronological) + attachments, `TifluxSource` injected via `routes/deps.get_tiflux_source`; Tiflux 404 → HTTP 404, other failures → 502.
- `routes/` REST under `/api`, exports under `/api/export/{tickets|breakdown/<dim>|kpis}/{csv|xlsx}`. Query models: see `routes/deps.py` (FastAPI expands a Pydantic query model only when it is the sole query param).

## Frontend (`frontend/src`)
- State lives in the URL hash `#/<page>?<filters>` (`filters/route.ts`), same param names as the API.
- `api/client.ts` typed fetch + `exportUrl`; per-ticket summary/description cached for the session (activity never cached).
- `components/TicketTable` (used on every tab) → `TicketHoverCard` (400 ms rest) and `TicketModal` (native `<dialog>`); Tiflux HTML shown as text via `richText.htmlToText`.
- `charts/` ECharts core wrapper reading CSS tokens; `pages/` one component per tab.

## Tests
`docker compose run --rm --no-deps -v ./backend:/srv api python -m pytest` (query tests use schema `dashboard_test` in the real db); frontend `npm test` runs in the web image build.
