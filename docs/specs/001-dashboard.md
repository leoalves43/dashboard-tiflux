# 001 — Dashboard Tiflux

## Intent
Dar visão completa e detalhada da operação de chamados do Tiflux: volume, backlog, SLA e atrasos, recortada por cliente, mesa e técnico, com tudo exportável.

## User outcomes
- Visão geral: KPIs (abertos, fechados, cancelados, em atraso, % no SLA, tempo médio de resolução) e tendência no tempo.
- Por cliente / por mesa / por técnico: ranking, abertos x fechados, atrasados, % SLA, dias médios de atraso; clicar num item filtra o painel todo.
- Atrasos: lista de chamados em atraso com dias de atraso (SLA de solução) e faixa (1–2, 3–7, 8–15, 16–30, >30 dias); atrasos de estágio à parte.
- Chamados: tabela detalhada paginada e ordenável com todos os campos.
- Filtros globais: período (abertura ou resolução), mesa, cliente, técnico, status (aberto/fechado/cancelado), prioridade, estágio, busca textual.
- Exportar para XLSX e CSV qualquer visão (tabela e agregados), respeitando os filtros, com o conjunto completo e não só a página visível.
- Dados atualizados automaticamente a partir da API do Tiflux.

## Constraints
- API Tiflux: 120 req/min, 200 itens/página; ~164 mil chamados (691 abertos, 1.628 cancelados em 2026-09-29).
- Token do Tiflux nunca chega ao navegador.
- Tudo sobe com Docker Compose, imagens/pacotes nas versões estáveis mais recentes; config em `.env`.
- Banco Postgres criado do zero no Docker, com usuário/senha/banco/schema do `.env`.

## SLA — definição (medida em 2026-09-29 nos 691 abertos)
- `solve_expiration` preenchido em 319; `stage_expiration` em 508; `attend_expiration` em 319.
- Em atraso (solução): aberto com `agora > solve_expiration`, ou fechado com `solved_in_time > solve_expiration`.
- Dias de atraso = diferença em dias corridos (a API não expõe calendário de expediente).
- Atraso de estágio: aberto com `agora > stage_expiration` — indicador separado.
- Chamado sem `solve_expiration` = "sem SLA" (não conta como atrasado nem como no prazo).

## Acceptance criteria
1. `docker compose up -d` sobe banco, API, sincronizador e web sem passos manuais.
2. Carga inicial traz todos os chamados (inclusive cancelados), clientes, mesas e técnicos; depois sincroniza incrementalmente (padrão a cada 5 min).
3. Os totais de abertos/fechados/cancelados no painel batem com `X-Total-Items` da API (tolerância: o intervalo de sync).
4. Cada filtro altera KPIs, gráficos e tabelas de forma consistente.
5. Exportar XLSX/CSV em qualquer visão gera arquivo com as mesmas linhas que a visão filtrada.
6. Dias de atraso seguem a definição acima; cobertos por testes.
7. Sync respeita rate limit (lê `RateLimit-Remaining`, recua em 429) sem falhar.

## Out of scope
- Escrita no Tiflux (só leitura).
- Autenticação de usuários do painel (acesso local).
- SLA em horas úteis/calendário de expediente.
- Chats, contratos, equipamentos, apontamentos de horas.
