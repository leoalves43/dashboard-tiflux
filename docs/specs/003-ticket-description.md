# 003 — Descrição do chamado no banco + coluna na exportação

## Intent
Ter a descrição de todos os chamados no nosso banco, para exportá-la em XLSX/CSV junto com a lista de chamados e para o hover não depender do Tiflux.

## User outcomes
- A exportação XLSX/CSV da lista de chamados (botões da tabela "Chamados", em qualquer visão) traz a coluna "Descrição" em texto limpo (sem HTML, com quebras de linha).
- O sincronizador carrega a descrição de todos os chamados em segundo plano, dos mais recentes para os mais antigos, e depois mantém atualizada a dos chamados alterados.
- A carga pode ser interrompida a qualquer momento (notebook dormindo ou desligado, sem internet, Docker reiniciado) e continua sozinha de onde parou quando o sync volta, sem refazer o que já foi gravado.
- O log mostra o progresso (ex.: "descrições: 48.210 de 164.623").
- Hover e modal leem a descrição do banco. Se o chamado ainda não foi carregado, buscam ao vivo, como hoje.

## Constraints
- Detalhe do chamado = 1 requisição por chamado (`GET /tickets/{n}`); cota de 120 req/min dividida com o sync. Carga completa ≈ 23 h de tempo rodando; interrupções só esticam o prazo.
- A sincronização normal (chamados novos e alterados, reconciliação) roda primeiro em cada ciclo; a carga das descrições usa o tempo que sobra até o próximo ciclo.
- Armazenamento: só a descrição (+ marca de quando foi buscada), não o JSON do detalhe. Estimativa medida: ~190 MB (amostra de 40 chamados, média 1,1 KB). Espaço livre no PC: ~20 GB.
- Excel limita a célula a 32.767 caracteres; descrição maior é cortada com aviso "…(cortado)".

## Acceptance criteria
1. XLSX e CSV da lista de chamados têm a coluna "Descrição" (texto limpo), respeitando filtros e ordenação.
2. Chamado cuja descrição ainda não foi carregada sai com a célula vazia; a exportação nunca chama o Tiflux.
3. Reiniciar o `sync` no meio da carga continua do próximo chamado pendente; nenhum chamado já gravado é buscado de novo, a não ser que tenha sido alterado no Tiflux depois.
4. Chamado alterado no Tiflux (novo `updated_at`) tem a descrição rebuscada num ciclo seguinte.
5. Chamado apagado no Tiflux (404) é marcado como carregado com descrição vazia, sem travar a fila.
6. Falha de rede/Tiflux num chamado não derruba o ciclo; ele fica pendente para o próximo.
7. Durante a carga, chamados novos continuam aparecendo no dashboard no ritmo normal do sync.
8. Log com progresso a cada lote.
9. Hover/modal usam a descrição do banco quando existe; senão, a busca ao vivo atual.
10. Testes do backend e do frontend verdes; lint limpo.

## Out of scope
- Guardar comunicações (públicas/internas) ou anexos no banco.
- Busca textual dentro da descrição (filtro "Buscar").
- Exportar a descrição em outras exportações além da lista de chamados.
