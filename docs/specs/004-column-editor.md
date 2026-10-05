# 004 — Editor de colunas da lista de chamados

## Intent
Cada usuário escolhe quais colunas a lista de chamados mostra e em que ordem, para ver só o que importa no seu trabalho.

## User outcomes
- Toda lista de chamados (Visão geral, Clientes, Mesas, Técnicos, Atrasos (SLA), Categorias, Chamados) tem um botão "Colunas" ao lado dos botões de exportar.
- O botão abre um painel com as 22 colunas existentes, na ordem atual, cada uma com uma caixa de marcar (mostrar/ocultar). Status, Prazo estágio e Reaberturas (antes só na exportação) começam ocultas.
- No painel, a ordem muda arrastando a coluna ou pelos botões ↑/↓ (acessível por teclado).
- Um botão "Restaurar padrão" volta à ordem e às colunas originais.
- A escolha vale para todas as listas de chamados e continua após recarregar a página, no mesmo navegador.
- A exportação CSV/XLSX de chamados leva só as colunas visíveis, na ordem escolhida.

## Constraints
- Só as colunas que já existem (as 22 da exportação); nenhum campo novo no backend.
- Pelo menos 1 coluna fica sempre visível (a última não pode ser desmarcada).
- Preferência salva só no navegador (sem login no projeto). Preferência salva inválida ou de versão antiga (coluna removida/nova) não quebra a tela: colunas desconhecidas são ignoradas e colunas novas entram no fim, com a visibilidade padrão delas.
- Ordenação por clique no cabeçalho continua funcionando nas colunas visíveis.
- Visual segue DESIGN.md (tokens, tema claro/escuro).

## Acceptance criteria
1. Em cada uma das 7 visões, o botão "Colunas" abre o painel com as 22 colunas (19 marcadas no padrão).
2. Desmarcar uma coluna a remove da tabela na hora; marcar a traz de volta na posição definida no painel.
3. Arrastar ou usar ↑/↓ muda a ordem das colunas na tabela na hora.
4. Não é possível ocultar a última coluna visível.
5. "Restaurar padrão" volta exatamente à configuração original.
6. Após recarregar a página, a configuração é mantida e vale em todas as visões.
7. Preferência salva corrompida ou com colunas desconhecidas cai no padrão / ignora as desconhecidas, sem erro.
8. O painel fecha com Esc e com clique fora.
9. CSV/XLSX de chamados contém exatamente as colunas visíveis, na ordem do painel; link sem `columns` exporta todas (22).
10. Testes do backend e do frontend verdes; lint/typecheck limpos.

## Out of scope
- Configuração diferente por visão.
- Sincronizar a preferência entre navegadores/usuários (precisaria de login).
- Redimensionar largura das colunas; adicionar colunas novas (ex.: descrição).
