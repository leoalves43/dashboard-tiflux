# 004 — Plano: Editor de colunas

Spec: docs/specs/004-column-editor.md. Aprovada em 2026-10-05 com um acréscimo: a exportação de chamados (CSV/XLSX) leva só as colunas visíveis, na ordem escolhida.

## Arquitetura (delta)
```
localStorage "ticketColumns.v1" <-> useColumnLayout <-> TicketTable (cabeçalho/células)
                                                    └> ColumnEditor (painel: marcar, arrastar, ↑/↓, restaurar)
export: /api/export/tickets/{fmt}?...&columns=title&columns=ticket_number  (sem columns = todas, como hoje)
```
- Layout = lista ordenada `{key, visible}`. Funções puras (`columns/columnLayout.ts`): padrão, reconciliar o salvo com as colunas atuais (desconhecidas saem, novas entram no fim visíveis, JSON inválido = padrão), mover, alternar (nunca a última visível).
- `Storage` injetado no load/save (teste com `FakeStorage`).
- Backend: `TicketExportQuery(TicketSortQuery)` com `columns: list[str]`; `ticket_list.export_columns(keys)` devolve os `ExportColumn` na ordem pedida; chave desconhecida = 422 com o valor. Rótulos da planilha continuam os do backend.

## Arquivos
- backend: `app/queries/ticket_list.py`, `app/routes/deps.py`, `app/routes/exports.py`; testes `tests/test_routes.py`, `tests/test_queries.py`.
- frontend: `src/columns/columnLayout.ts` + `.test.ts`, `src/columns/useColumnLayout.ts` (novos), `src/components/ticketColumns.tsx` (novo, COLUMNS saem da TicketTable), `src/components/ColumnEditor.tsx` (novo), `src/components/TicketTable.tsx`, `src/api/client.ts`, `src/api/query.test.ts`, `src/styles/app.css`.
- docs: `DESIGN.md` (Column editor), `docs/ARCHITECTURE.md`, `docs/decisions/LOG.md`, `docs/state/HANDOFF.md`, `docs/INDEX.md`.

## Riscos
- Status, Prazo estágio e Reaberturas entram no editor ocultas (decisão do usuário, 2026-10-05): a exportação padrão deixa de trazê-las até serem marcadas. Sem `columns` (links antigos) a exportação continua completa.
- Ordenar por coluna oculta continua válido: `columns` filtra só a saída, nunca a query.
- Nada irreversível: sem migração, só preferência no navegador.

## Tarefas
- [x] 1. Backend — `columns` na exportação de chamados. Done: testes (ordem, subconjunto, sort por coluna oculta = 200, desconhecida = 422) verdes; ruff limpo.
- [x] 2. Frontend — `columnLayout` + armazenamento. Done: testes Vitest verdes.
- [ ] 3. Frontend — DESIGN.md (Column editor) primeiro; depois `ticketColumns`, `useColumnLayout`, `ColumnEditor`, TicketTable usa o layout, export envia `columns`. Done: build (tsc) verde; verificado no navegador.
- [ ] 4. Docs + verificação dos 10 critérios + exportação. Done: tudo verde.
