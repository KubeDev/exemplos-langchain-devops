# Contexto para sessões de IA neste projeto

Leia o `README.md` antes de alterar este exemplo. Ele define o contrato público da CLI.

## Natureza do projeto

Exemplo didático `07` da série `langchain-devops-examples`. A lição é: **uma CLI operacional tem
contrato explícito de entrada, canais de saída e código de retorno**. O projeto é autocontido e o
código será projetado em aula; simplicidade vence generalidade.

## Contrato obrigatório

- Comando principal: `uv run assistente-plataforma-cli "Liste os pods com reinicializações" --namespace kube-system`.
- `pergunta` é posicional e obrigatória.
- `--namespace` é contexto opcional incorporado à solicitação; não replique a interface do `kubectl`.
- Uma solicitação por processo.
- Somente a resposta final em `stdout`.
- Aviso do catálogo MCP e erros em `stderr`.
- Códigos: `0` sucesso, `1` execução/configuração, `2` uso inválido.
- Não adicione `--debug`.
- A CLI é declarada com Typer: um único comando, sem subcomandos.

## Superfície do agente e do MCP

Preserve o MCP Kubernetes HTTP separado, a versão fixada do server, o bind local, a autenticação e
`ALLOW_ONLY_READONLY_TOOLS=true`. Mantenha a proibição de consultar `Secret` ou revelar credenciais.
O cliente descobre as ferramentas pelo adapter e as registra diretamente no agente.

Use exatamente uma chamada a `agent.ainvoke()`, sem streaming e sem loop manual de tool calling. Não
percorra `tool_calls`, não crie `ToolMessage` e não chame `kubectl` pelo Python.

## Sem logs de passos

Não use callbacks nem registre decisões do modelo ou chamadas de ferramenta: observabilidade não é
assunto desta aula.

## Fronteiras curriculares

Não adicione chat contínuo, memória ou persistência; isso muda o contrato de uma solicitação por
processo. Não adicione streaming ou retorno parcial; esse é o conteúdo da Aula 08. Não adicione
middleware, retry, cache, RAG, interface web ou opções que transformem a CLI em clone do `kubectl`.

## Ambiente

Use somente `uv`. Dependências entram por `uv add`. Nunca grave credenciais no repositório, use
parâmetros de sampling ou faça commits como parte de alterações didáticas.
