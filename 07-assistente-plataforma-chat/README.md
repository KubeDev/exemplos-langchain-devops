# 07 — Assistente de plataforma em interface conversacional

Este exemplo independente expõe o assistente Kubernetes da Aula 05 em uma interface de chat.
A conversa fica em `st.session_state`, é reenviada integralmente ao agente em cada turno e desaparece
quando a sessão do navegador termina. A resposta final chega progressivamente à mensagem do
assistente; chamadas de ferramentas e marcos da execução aparecem somente no terminal do Streamlit.

## O que muda

O agente, o catálogo MCP e os limites de acesso continuam os mesmos. A nova camada é a porta de
entrada:

```text
navegador                         processo Streamlit                 MCP Kubernetes
mensagens + campo de chat  ───►  histórico de sessão + agente  ───►  consultas read-only
resposta progressiva       ◄───  somente texto do modelo       ◄───  resultado da ferramenta
                                  logs seguros no terminal
```

`st.session_state.messages` contém dicionários `role`/`content`. Quando chega uma pergunta, ela é
adicionada à lista antes da execução; o agente recebe a lista completa e a resposta agregada por
`st.write_stream` volta à mesma lista. Isso permite perguntas de continuidade como “e quais deles
reiniciaram?” sem banco de dados ou checkpointer.

O streaming usa a interface pública do agente:

```python
async for part in agent.astream(
    {"messages": messages},
    stream_mode="messages",
    version="v2",
    config={"callbacks": [observability]},
):
    text = text_from_stream_part(part)
    if text:
        yield text
```

`text_from_stream_part()` aceita somente texto produzido pelo nó `model`. Partes de tool call,
resultados de ferramenta e demais eventos não são renderizados. O código não percorre `tool_calls`,
não cria `ToolMessage` e não reproduz o ciclo interno do agente.

## Pré-requisitos

- Python 3.12 e `uv`;
- Node.js e `npx`;
- `kubectl` configurado para um cluster de estudo;
- chave da API da Anthropic.

Prepare o ambiente:

```bash
cp .env.example .env
uv sync
kubectl config current-context
kubectl get pods -n kube-system
```

## Executar

No primeiro terminal, inicie o server MCP:

```bash
./scripts/subir-mcp-kubernetes
```

No segundo terminal, inicie a interface:

```bash
uv run streamlit run src/app.py
```

Abra o endereço exibido pelo Streamlit e faça duas perguntas:

```text
Liste os pods do namespace kube-system e responda somente com nome, status e reinicializações.
```

```text
Agora mostre somente os que tiveram reinicializações.
```

O segundo pedido depende do histórico. No navegador devem aparecer apenas mensagens. No terminal do
Streamlit devem aparecer inventário MCP, decisões do modelo, ferramenta e argumentos sanitizados,
resumo estrutural do resultado e duração. Compare os dados com:

```bash
kubectl get pods -n kube-system
```

## Segurança e limites

- O server fixa `mcp-server-kubernetes@4.1.6`, usa bind local, token e
  `ALLOW_ONLY_READONLY_TOOLS=true`.
- O prompt proíbe alterações, consultas a `Secret` e revelação de credenciais.
- Logs permitem somente nomes esperados e os valores didáticos `pods`, `pod` e `kube-system`; o
  restante é omitido ou resumido.
- A memória dura somente a sessão do Streamlit. Não há banco, autenticação de usuário, aprovação,
  auditoria, retry, cache, RAG ou tracing de produção.
- A interface não é apropriada para produção. Autenticação, gate e trilha são lacunas curriculares
  deliberadas.

## Arquivos

```text
src/app.py                   interface e construção do agente
src/chat.py                  filtro e streaming de texto para a UI
src/observability.py         eventos sanitizados no stderr
src/tools.py                 configuração do endpoint MCP
scripts/subir-mcp-kubernetes server HTTP read-only separado
tests/                       testes com agentes e eventos simulados
PLANO_TESTE.md               validação técnica e roteiro manual
```
