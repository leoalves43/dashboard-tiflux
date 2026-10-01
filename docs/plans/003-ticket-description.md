# 003 — Plano: Descrição do chamado no banco + coluna na exportação

Spec: docs/specs/003-ticket-description.md.

## Arquitetura (delta)
```
sync ciclo: dimensões → backfill/incremental/reconcile (como hoje)
            → descrições até o prazo do ciclo (início + SYNC_INTERVAL_MINUTES):
              fila = tickets LEFT JOIN ticket_descriptions
                     WHERE d IS NULL OR t.updated_at > d.ticket_updated_at
                     ORDER BY t.updated_at DESC LIMIT lote
              por chamado: GET /tickets/{n} → upsert (description, ticket_updated_at, synced_at)
runner: dorme só o que falta até o próximo ciclo
export tickets: LEFT JOIN ticket_descriptions → html_to_text → coluna "Descrição"
GET /api/tickets/{n}/description: banco; se ausente → Tiflux ao vivo (como hoje)
```
- Tabela nova `ticket_descriptions` (PK ticket_number; description text; ticket_updated_at; synced_at), criada por `ensure_schema` (`create_all`). É tabela separada, sem ALTER em `tickets`, para o upsert dos chamados nunca apagar a descrição.
- Retomada: o estado é a própria tabela. Cada chamado é gravado assim que buscado, então uma interrupção perde no máximo um.
- 404 → grava `description = NULL` com `ticket_updated_at` atual (sai da fila). Outras falhas → log e segue; o chamado continua pendente.
- `app/rich_text.py` (novo): `html_to_text` em Python com `html.parser` da stdlib, mesmas regras do `richText.ts` (blocos → quebra de linha, descarta script/style, decodifica entidades).
- Exportação: `iter_all_tickets` ganha um parâmetro para incluir a descrição (só a exportação usa; a listagem paginada da UI não carrega esse texto). Corte em 32.767 caracteres no XLSX.

## Arquivos
- backend: `app/db.py`, `app/rich_text.py` (novo), `app/sync/descriptions.py` (novo), `app/sync/description_store.py` (novo; o `SyncStore` não muda), `app/sync/runner.py`, `app/queries/ticket_list.py`, `app/routes/exports.py`, `app/routes/dashboard.py`, `app/exporters.py`; testes `tests/test_rich_text.py`, `tests/test_description_sync.py` (novos), `tests/fakes.py`, `tests/test_queries.py`, `tests/test_exporters.py`, `tests/test_routes.py`.
- frontend: nenhum (o endpoint `/description` mantém o contrato).
- docs: `docs/ARCHITECTURE.md`, `docs/decisions/LOG.md`, `docs/state/HANDOFF.md`.

## Riscos
- ~23 h de cota quase cheia: outras integrações com o mesmo token disputam a cota nesse período.
- Notebook dormindo pausa a carga (esperado). Para render fora do horário, o notebook precisa ficar ligado, sem suspensão, com o Docker Desktop iniciando com o Windows.
- Se o Tiflux não mudar o `updated_at` ao editar só a descrição, a edição não é rebuscada. Raro (descrição é a abertura do chamado); aceito.
- Banco cresce ~190 MB (estimativa por amostra).
- Reversível: `DROP TABLE ticket_descriptions` desfaz tudo; nada existente é alterado.

## Tarefas
- [x] 1. Schema `ticket_descriptions` + `html_to_text` em Python. Done: tabela criada no Postgres de teste; testes do conversor (blocos, script, entidades, vazio).
- [x] 2. `DescriptionSync` + `DescriptionStore` (`pending_descriptions`, `save_description`, `description_progress`) + ciclo com prazo no runner. Done: testes com fakes (ordem, retomada sem refazer, rebusca após alteração, 404, falha isolada, para no prazo) e teste do store contra o Postgres.
- [ ] 3. Exportação: coluna "Descrição" (texto limpo, corte no XLSX) na lista de chamados. Done: testes de query/exportação/rota; arquivo real aberto com a coluna.
- [ ] 4. `/description` lê do banco com fallback ao vivo. Done: teste de rota (banco, ausente → Tiflux).
- [ ] 5. Subir e acompanhar: rebuild do `sync`/`api`, log de progresso, reinício no meio para provar a retomada. Done: contagem continua após o restart; chamado novo aparece normalmente.
- [ ] 6. Docs + verificação: ARCHITECTURE, LOG, HANDOFF; pytest + ruff + build; os 10 critérios. Done: tudo verde.
