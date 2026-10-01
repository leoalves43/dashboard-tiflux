# 002 — Detalhes do chamado (hover e modal)

## Intent
Ver o conteúdo de um chamado sem sair do dashboard: um resumo ao passar o mouse e o chamado completo, com histórico, ao clicar.

## User outcomes
- Todas as visões (Visão geral, Clientes, Mesas, Técnicos, Atrasos (SLA), Categorias, Chamados) mostram uma lista de chamados que respeita os filtros ativos. Nas visões de recorte, o clique numa barra ou linha, que já filtra o painel, também filtra essa lista.
- Passar o mouse sobre um chamado da lista mostra um cartão com: solicitante, cliente, mesa, prioridade, status, estágio, técnico responsável, data de abertura e descrição.
- Clicar num chamado abre um modal com os mesmos campos e mais:
  - anexos do chamado (nome, tipo, tamanho, link para abrir);
  - seção "Comunicações" com a pública (respostas ao cliente) e a interna separadas, como na interface do Tiflux; cada uma em ordem cronológica, com autor, data, texto e anexos.
- O modal fecha com Esc, com o botão fechar ou com um clique fora; o foco volta ao chamado de onde ele foi aberto.

## Constraints
- 8 campos do resumo vêm do nosso banco e aparecem na hora. A descrição não vem na listagem do Tiflux, então é lida ao vivo (1 requisição, com cache) quando o hover aparece ou no clique.
- Follow-ups (respostas + comunicações internas) e anexos são lidos do Tiflux pelo backend ao abrir o modal, sem guardar nada no banco. O token nunca chega ao navegador. (Projeto roda localmente; se for para um servidor, passa a guardar tudo no banco; ver LOG.)
- Limite da API: 120 req/min, compartilhado com o sincronizador. Cada abertura de modal custa 3 requisições + 1 por follow-up com anexo.
- Descrição e textos podem conter HTML do Tiflux: exibir sem executar scripts.
- Visual segue DESIGN.md (tokens, pílulas, tema claro/escuro).

## Acceptance criteria
1. Em cada uma das 7 visões existe uma lista de chamados paginada e filtrada pelos filtros ativos.
2. O cartão de hover aparece após uma breve pausa do mouse sobre a linha (sem piscar ao percorrer a lista) e mostra os 9 campos do resumo. Campo vazio aparece como "–".
3. O clique abre o modal com os 9 campos, a lista de anexos e a seção "Comunicações" com pública e interna separadas (com contagem), com rótulos em português.
4. Chamado sem anexos ou sem comunicações mostra "Nenhum anexo." / "Nenhuma comunicação pública." / "Nenhuma comunicação interna."
5. Falha ao consultar o Tiflux mostra um aviso só na parte de anexos/follow-ups; o resumo continua visível.
6. Esc, o botão fechar e o clique fora fecham o modal, e o foco volta à linha de origem.
7. Nenhuma resposta do backend expõe o token, e HTML vindo do Tiflux não executa scripts.
8. Um follow-up ou anexo novo no Tiflux aparece na próxima abertura do modal.
9. Testes do backend e do frontend verdes; lint limpo.

## Out of scope
- Editar, responder, fechar ou reabrir chamados.
- Guardar descrição, follow-ups ou anexos no banco (fase de servidor, futura; ver HANDOFF NEXT).
- Baixar anexos via backend (o link do Tiflux é usado diretamente; pode expirar).
- Hover ou modal a partir de barras dos gráficos (que continuam filtrando o painel).
