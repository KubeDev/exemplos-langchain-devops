# Contexto para sessões de IA neste projeto

Leia o `README.md` antes de alterar este exemplo. Ele define o contrato público da CLI.

## Natureza do projeto

Exemplo didático `06` da série `langchain-devops-examples`. A lição é: **uma CLI operacional tem
contrato explícito de entrada, canais de saída e código de retorno**. O projeto é autocontido e o
código será projetado em aula; simplicidade vence generalidade.

## Contrato obrigatório

- Comando principal: `uv run assistente-plataforma-cli "Liste os pods com reinicializações" --namespace kube-system`.
- `pergunta` é posicional e obrigatória.
- `--namespace` é contexto opcional incorporado à solicitação; não replique a interface do `kubectl`.
- Uma solicitação por processo.
- Somente a resposta final em `stdout`.
- Eventos didáticos e erros em `stderr`.
- Códigos: `0` sucesso, `1` execução/configuração, `2` uso inválido.
- Não adicione `--debug`.

## Superfície do agente e do MCP

Preserve o MCP Kubernetes HTTP separado, a versão fixada do server, o bind local, a autenticação e
`ALLOW_ONLY_READONLY_TOOLS=true`. Mantenha a proibição de consultar `Secret` ou revelar credenciais.
O cliente descobre as ferramentas pelo adapter e as registra diretamente no agente.

Use exatamente uma chamada a `agent.ainvoke()`, sem streaming e sem loop manual de tool calling. Não
percorra `tool_calls`, não crie `ToolMessage` e não chame `kubectl` pelo Python.

## Observabilidade didática

- Todos os eventos vão para `stderr`.
- Restrinja nomes visíveis às oito ferramentas read-only esperadas.
- Restrinja valores de argumentos visíveis a `pods`, `pod` e `kube-system`.
- Redija token, autorização, API key, senha e segredo.
- Resuma resultado de tool somente por tipo, itens ou quantidade de caracteres.
- Nunca registre mensagens completas, headers, configuração MCP, estado ou chain of thought.

## Fronteiras curriculares

Não adicione chat contínuo, memória ou persistência; isso muda o contrato de uma solicitação por
processo. Não adicione streaming ou retorno parcial; esse é o conteúdo da Aula 07. Não adicione
middleware, retry, cache, RAG, interface web ou opções que transformem a CLI em clone do `kubectl`.

## Ambiente

Use somente `uv`. Dependências entram por `uv add`. Nunca grave credenciais no repositório, use
parâmetros de sampling ou faça commits como parte de alterações didáticas.
