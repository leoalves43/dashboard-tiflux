# 001 — Plano: Dashboard Tiflux

## Arquitetura
```
Tiflux API ──> sync (Python) ──> Postgres 18 (schema dashboard) <── api (FastAPI) <── web (React+Vite, nginx proxy /api)
```
- `db`: postgres:18.6-alpine, volume em `/var/lib/postgresql` (layout PG18).
- `api` e `sync`: mesma imagem python:3.14-slim; `sync` roda o loop de sincronização.
- `web`: build em node:26-alpine, servido por nginx:alpine; `/api` → `api:8000`.
- Tabelas: `tickets` (colunas tipadas + `raw jsonb`), `clients`, `desks`, `users`, `sync_state`.
- Um único construtor filtro → SQL alimenta KPIs, gráficos, tabelas e exportação.
- Stack: FastAPI, SQLAlchemy 2.1 Core, psycopg 3, httpx, openpyxl; React 19, TypeScript, ECharts 6, TanStack Table.

## Arquivos
`docker-compose.yml`, `.env` / `.env.example`, `backend/` (app/{config,db,tiflux,sync,filters,queries,exporters,routes}), `backend/tests/`, `frontend/` (src/{api,components,pages,filters}), `DESIGN.md`, `docs/INDEX.md`, `docs/ARCHITECTURE.md`, `docs/decisions/LOG.md`, `docs/state/HANDOFF.md`.

## Riscos
- Carga inicial ~822 requisições (~7–10 min) — roda uma vez, retomável via `sync_state`.
- Campos de SLA nulos em ~54% dos abertos → classe "sem SLA".
- `.env` passa a ter `DB_HOST=db`; `SCHEMA_NAME = dashboard` vira `SCHEMA_NAME=dashboard` (espaços quebram o compose).
- Volume do Postgres é persistente: apagar (`down -v`) perde a carga (recuperável por novo sync).

## Tarefas
- [x] 1. Infra: compose, Dockerfiles, `.env.example`, ajuste do `.env`. Done: `docker compose config` válido.
- [x] 2. Backend base: config, conexão, schema/tabelas. Done: tabelas criadas no start; testes passam.
- [x] 3. Cliente Tiflux + sync (backfill, incremental, rate limit). Done: testes com `FakeTifluxClient`; contagens batem com a API.
- [x] 4. Filtros → SQL + consultas (KPIs, séries, por cliente/mesa/técnico, atrasos, lista). Done: testes de SLA/dias de atraso.
- [ ] 5. Exportação CSV/XLSX + rotas. Done: teste gera arquivo com linhas = consulta.
- [ ] 6. DESIGN.md + frontend (filtros globais, páginas, gráficos, tabelas, botões de exportação). Done: build ok, páginas carregam.
- [ ] 7. Subir tudo, verificar critérios da spec, docs (INDEX, ARCHITECTURE, LOG, HANDOFF).
