# Contexto para sessões de IA neste projeto

Leia o `README.md` antes de alterar este exemplo. Ele registra a demonstração e suas fronteiras.

## Natureza do projeto

Exemplo didático `05` da série `langchain-devops-examples`. A lição é: **um assistente de
plataforma pode descobrir capacidades Kubernetes publicadas por um MCP server e usá-las em
linguagem natural**.

O exemplo é autocontido e deve fazer sentido sem comparação com outros projetos da série. O código
será lido em aula e projetado numa tela. Quando simplicidade e robustez colidirem, vence a
simplicidade.

## Superfície MCP

Concentre a integração em `MCP_CONFIG`, `MCPAdapter`, `list_tools()` e no registro direto do catálogo
retornado pelo server. O `async` existe porque a API MCP o exige; não introduza concorrência,
tarefas em background ou abstrações assíncronas auxiliares.

Mantenha o adapter aberto durante descoberta e execução. O cliente fala somente com a URL
Streamable HTTP e envia `X-MCP-AUTH`; iniciar o server e acessar o kubeconfig são responsabilidades
externas. Preserve no comando documentado a versão fixada do server,
`ALLOW_ONLY_READONLY_TOOLS=true`, o bind local e a autenticação por token.

O script `scripts/subir-mcp-kubernetes` inicia o processo separado e lê o segredo do `.env`.
Mantenha o valor do token fora do script, dos comandos exibidos e do histórico do terminal.

## Cenário da demonstração

A aplicação imprime o inventário e aguarda uma pergunta digitada pelo usuário. Na demonstração, a
pergunta deve solicitar os pods de `kube-system` com nome, status e reinicializações. O inventário
deve conter exatamente as oito ferramentas MCP read-only publicadas pelo server e nenhuma
capacidade definida no cliente.

A resposta deve ser conferida contra `kubectl get pods -n kube-system`. Os callbacks em
`src/observability.py` tornam o recebimento da pergunta, decisões do modelo, ferramenta, argumentos
sanitizados, resumo estrutural do resultado, conclusão da resposta final e duração visíveis em
`stderr`; trate esses eventos como evidência didática da execução. Não crie estado artificial nem
dependa da existência de pod defeituoso.

## Observabilidade didática

- Preserve `input()`, uma única interação e `agent.ainvoke()` sem streaming.
- Passe callbacks pela configuração pública da invocação; não percorra `tool_calls` nem crie
  `ToolMessage` manualmente.
- Mantenha a resposta normal em `stdout` e todos os eventos de observabilidade em `stderr`.
- Restrinja valores visíveis dos argumentos a `pods`, `pod` e `kube-system`; omita os demais.
- Restrinja nomes visíveis de ferramenta às oito ferramentas esperadas do catálogo read-only.
- Resuma pergunta, resultado da ferramenta e resposta final somente por tipo, itens ou caracteres.
- Sanitização deve cobrir pelo menos token, authorization, API key, password e secret.
- Preserve no system prompt a proibição de consultar `Secret` ou revelar credenciais.
- Nunca registre configuração MCP, headers, estado completo, prompts internos, mensagens completas,
  debug bruto ou chain of thought.
- Esta instrumentação existe para a aula; não a transforme em stack de tracing de produção.

## Fronteiras curriculares

- Não implemente um MCP server.
- Não inicie o server como subprocesso do cliente nem volte ao transport stdio.
- Não chame `kubectl` pelo código Python.
- Não adicione capacidades locais ou de escrita, middleware, retry, cache, memória ou RAG.
- Não abra nem reproduza manualmente o ciclo interno de tool calling.
- Preserve uma pergunta interativa por execução; argumentos de CLI e chat contínuo pertencem às aulas seguintes.
- Não adicione streaming; a saída incremental pertence à Aula 07.

## Ambiente e credenciais

- Use somente `uv`; nunca `pip`, Poetry, Conda ou ativação manual de virtualenv.
- Altere dependências com `uv add` ou `uv remove` para manter o lockfile coerente.
- Não use `temperature`, `top_p` ou `top_k`.
- `ANTHROPIC_API_KEY` nunca entra no repositório.
- `KUBERNETES_MCP_TOKEN` nunca entra no código nem em arquivo versionado.
- Execute apenas contra um contexto Kubernetes de estudo.
