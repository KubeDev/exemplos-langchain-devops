# Contexto deste exemplo

Leia o `README.md` e o `CLAUDE.md` da raiz do repositório antes de alterar o projeto.

Este é o exemplo da Aula 07 de Memória e RAG: estratégias de chunking para dados operacionais.

- `dividir.py` é lido em aula de cima a baixo. Uma função por estratégia, sem classe, registry
  ou configuração genérica. `configuracao_a()` e `configuracao_b()` ficam escritas por extenso.
- A janela de log é calculada por serviço e só indexa WARN e ERROR; o `if` do filtro fica visível.
- No log e no ticket, campo estruturado vai para o metadado; só o texto renderizado vai para o
  embedding. Não volte a indexar o JSON cru na configuração B.
- Os parâmetros da B (3500 nos documentos) saíram da medição das seções. Se a base mudar,
  meça de novo com `uv run chunks` antes de alterar.
- `perguntas.json` é cópia exata da tabela do roteiro da aula; mudar um exige mudar o outro.
- As perguntas de log não completam no top-k nem na B: é proposital. A busca por similaridade
  não resolve pergunta temporal; filtro por metadado é o assunto da Aula 09. Não altere dados
  nem perguntas para "fazer passar".
- Não há agente nem modelo de geração. Atualização incremental pertence à Aula 08.
- Use `uv`; mantenha a chave da API somente no `.env`, fora do Git.
