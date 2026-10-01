# 002 — Plano: Detalhes do chamado (hover e modal)

Spec: docs/specs/002-ticket-details.md. Hover e modal carregam os dados do chamado específico, sob o mouse ou clicado.

## Arquitetura (delta)
```
hover ─> GET /api/tickets/{n}             ─> Postgres (8 campos, na hora)
      └> GET /api/tickets/{n}/description ─> api ─> Tiflux /tickets/{n} (a listagem não traz a descrição)
click ─> GET /api/tickets/{n}           (resumo na hora)
      └> GET /api/tickets/{n}/activity  ─> api ─> Tiflux: /files, /answers, /internal_communications
                                                   (+ /answers/{id} ou /internal_communications/{id} quando files_count > 0)
```
- O container `api` ganha um `TifluxClient` em `app.state` (o token já está no `.env` do serviço e nunca vai ao navegador).
- `app/ticket_activity.py` (novo): recebe um `TifluxSource` injetado e monta `{files, followups}`. Os follow-ups formam uma linha do tempo única (resposta | interna), em ordem cronológica, com anexos normalizados. Testes com `FakeTifluxSource`.
- Rota de atividade: 404 se o chamado não existe no Tiflux; 502 com mensagem se o Tiflux falhar.
- Frontend: `TicketTable` ganha hover (atraso de 400 ms, cache por número, sem piscar) e clique (modal). Uma tabela de chamados entra no fim de `BreakdownPage`, o que cobre Visão geral, Clientes, Mesas, Técnicos e Categorias. HTML do Tiflux vira texto via `DOMParser` e é exibido com `white-space: pre-wrap` (não executa scripts; sem dependência nova).

## Arquivos
- backend: `app/queries/ticket_detail.py` (novo), `app/ticket_activity.py` (novo), `app/routes/dashboard.py`, `app/routes/deps.py`, `app/main.py`; testes `tests/test_ticket_detail.py`, `tests/test_ticket_activity.py` (novos), `tests/test_routes.py`, `tests/fakes.py`.
- frontend: `src/api/types.ts`, `src/api/client.ts`, `src/richText.ts` + `src/richText.test.ts` (novos), `src/components/TicketFields.tsx`, `TicketHoverCard.tsx`, `TicketModal.tsx` (novos), `src/components/TicketTable.tsx`, `src/pages/BreakdownPage.tsx`, `src/styles/app.css`.
- docs: `DESIGN.md` (Modal, Hover card), `docs/ARCHITECTURE.md`, `docs/decisions/LOG.md`, `docs/state/HANDOFF.md`.

## Riscos
- Cada clique custa 3 requisições + 1 por follow-up com anexo, e a cota (120/min) é dividida com o sync. Uso manual fica bem abaixo do limite.
- O texto das respostas na listagem do Tiflux é `name`, segundo a spec da API. A confirmar com dados reais na tarefa 2.
- O link de anexo do Tiflux pode expirar ou exigir login. É usado como vem.
- Nada irreversível: sem tabela nova nem migração.

## Tarefas
- [x] 1. Backend — resumo: `ticket_detail.ticket_summary(conn, n)` + `GET /api/tickets/{n}` (404 se não existir). Done: testes contra o Postgres de teste verdes.
- [x] 2. Backend — atividade e descrição ao vivo: `ticket_activity.load_activity` / `load_description` + `GET /api/tickets/{n}/activity` e `/description` + `TifluxClient` no app. Done: testes com fakes (ordem, tipos, anexos, vazio, 404, erro) verdes; campos conferidos com um chamado real.
- [x] 3. Frontend — tipos, cliente da API e `richText`. Done: teste do Vitest verde.
- [x] 4. Frontend — `TicketFields` + `TicketHoverCard` + hover na `TicketTable`. Done: hover com os 9 campos verificado no navegador.
- [x] 5. Frontend — `TicketModal` (campos, anexos, linha do tempo, carregando/vazio/erro, Esc/fora/botão, foco volta) + clique. Done: verificado no navegador.
- [ ] 6. Frontend — tabela de chamados no fim de `BreakdownPage`. Done: as 7 visões têm lista com hover e clique.
- [ ] 7. Docs + verificação: DESIGN.md, ARCHITECTURE.md, HANDOFF; pytest + ruff + build do web; os 9 critérios da spec conferidos. Done: tudo verde.
