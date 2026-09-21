# 06 — Assistente de plataforma na linha de comando

Este exemplo autocontido transforma o assistente Kubernetes da Aula 05 em um comando de terminal.
A pessoa informa uma solicitação em linguagem natural como argumento; a aplicação executa uma única
invocação do agente e encerra com resposta e código de retorno próprios para automação.

```bash
uv run assistente-plataforma-cli "Liste os pods com reinicializações" --namespace kube-system
```

O contrato operacional é simples:

- a pergunta é um argumento posicional obrigatório;
- `--namespace` acrescenta contexto à solicitação, sem reproduzir opções do `kubectl`;
- a resposta final é o único conteúdo escrito em `stdout`;
- eventos didáticos e erros são escritos em `stderr`;
- o código `0` indica sucesso, `1` falha de configuração ou execução e `2` uso inválido.

Cada processo atende exatamente uma solicitação. Não há prompt interativo, sessão, memória,
streaming ou loop manual de tool calling.

## O que permanece da Aula 05

A CLI continua sendo cliente de um `mcp-server-kubernetes@4.1.6` separado, por Streamable HTTP. O
server é iniciado em modo read-only, ligado a `127.0.0.1` e protegido por token. A aplicação descobre
o catálogo MCP, entrega as tools ao `create_agent()` e usa uma única chamada a `agent.ainvoke()`.

```text
linha de comando                         mcp-server-kubernetes
pergunta + contexto           HTTP       catálogo read-only
agent.ainvoke()             ─────────►   kubeconfig + Kubernetes
```

Os callbacks continuam registrando em `stderr` somente marcos seguros: tamanho da solicitação,
início da decisão, nome permitido da ferramenta, argumentos sanitizados, resumo limitado do retorno,
confirmação da resposta e duração. Tokens, autorização, chaves, senhas e segredos são redigidos; o
conteúdo integral da pergunta, das mensagens e do resultado da ferramenta não é registrado.
Falhas de bibliotecas externas exibem somente o tipo da exceção, nunca sua mensagem potencialmente
sensível; mensagens detalhadas ficam restritas às validações de configuração definidas no projeto.

## Pré-requisitos

- Python 3.12 e `uv`;
- Node.js e `npx`;
- `kubectl` configurado para um cluster de estudo;
- chave da API da Anthropic.

Prepare o projeto:

```bash
cp .env.example .env
uv sync
```

Inicie o MCP server em outro terminal:

```bash
./scripts/subir-mcp-kubernetes
```

O script mantém `ALLOW_ONLY_READONLY_TOOLS=true`, autenticação por token e bind local. O token vem do
`.env` e não é impresso.

## Uso

Consulte a ajuda sem precisar de credenciais ou conexão com o server:

```bash
uv run assistente-plataforma-cli --help
```

Execute a solicitação preparada para a aula:

```bash
uv run assistente-plataforma-cli "Liste os pods com reinicializações" --namespace kube-system
```

`--namespace` não escolhe uma operação nem chama `kubectl`; ele apenas compõe a intenção entregue ao
agente. A escolha da ferramenta e o preenchimento de seu schema permanecem sob responsabilidade do
agente.

Para provar a separação dos canais:

```bash
uv run assistente-plataforma-cli "Liste os pods com reinicializações" \
  --namespace kube-system >resposta.txt 2>eventos.txt
```

`resposta.txt` deve conter somente a resposta destinada ao usuário. `eventos.txt` deve conter os
eventos didáticos. Confira os dados do cenário com `kubectl get pods -n kube-system`, fora da
aplicação.

## Códigos de retorno

| Código | Significado | Exemplo |
|---|---|---|
| `0` | execução concluída | resposta final emitida em `stdout` |
| `1` | falha de configuração ou execução | credencial ausente, server indisponível ou erro do agente |
| `2` | uso inválido | pergunta ausente ou opção desconhecida |

## O que este exemplo não faz

- Não implementa nem inicia o MCP server no processo cliente.
- Não chama `kubectl` pelo código Python.
- Não publica ferramentas de escrita nem consulta `Secret`.
- Não oferece opções para recurso, verbo, seletor ou formato de saída do Kubernetes.
- Não mantém chat, histórico ou memória entre processos.
- Não usa streaming nem imprime progresso em `stdout`.
- Não percorre `tool_calls` nem cria `ToolMessage` manualmente.
- Não oferece `--debug` nem despeja configuração, mensagens ou estado interno.

## Arquivos

```text
src/app.py                   contrato da CLI e execução única do agente
src/observability.py         eventos didáticos, sanitização e resumos
src/tools.py                 configuração do endpoint MCP
scripts/subir-mcp-kubernetes inicialização do server HTTP separado
PLANO_TESTE.md               verificações automatizadas e manuais
```
