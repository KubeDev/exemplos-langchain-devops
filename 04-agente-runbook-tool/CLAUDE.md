# Contexto para sessões de IA neste projeto

Leia o `README.md` para entender a demonstração. Este arquivo registra as fronteiras que
preservam a função didática do exemplo.

## Natureza do projeto

Exemplo didático `04` da série `langchain-devops-examples`. A lição é: **configurar uma
ferramenta no agente e observar se ele envia o identificador correto ao usá-la**.

O código será lido em aula e projetado numa tela. Quando simplicidade e robustez colidirem,
vence a simplicidade.

## Preserve o contraste com o exemplo 03

O `03-agente-runbook` insere o documento diretamente no contexto antes da primeira chamada.
Este exemplo não pode fazer isso. O `SYSTEM_PROMPT` não contém `{contexto}` e os runbooks só
são carregados dentro de `consultar_runbook()`.

## Use o agente, não reconstrua seu loop

Mantenha `create_agent()` em `src/app.py`, com `tools=[consultar_runbook]`. A aplicação deve
somente escolher uma pergunta, chamar `agent.invoke()` e imprimir a resposta final.

Não abra, reproduza ou monitore manualmente `AIMessage.tool_calls`, `ToolMessage` ou o ciclo
de execução. O único log da ferramenta é o `runbook_id` recebido, pois essa é a evidência que
a aula precisa observar.

## Separe a ferramenta do fluxo

Mantenha o catálogo e `consultar_runbook()` em `src/tools.py`. Mantenha configuração e uso do
agente em `src/app.py`.

O argumento da ferramenta é `runbook_id`. Não o troque por um caminho fornecido pelo modelo.
A aplicação controla o mapeamento entre identificador e arquivo.

## Preserve o experimento controlado

Existe uma única pergunta parametrizada. Entre os cenários, altere somente `runbook_id`:

```text
Segundo o runbook {runbook_id}, qual é o procedimento para estabilizar o serviço?
```

Não acrescente serviço, alerta, verbo ou tarefa específicos a uma das perguntas. As diferenças
de contexto devem vir do documento escolhido, não do texto que chega ao agente.

Os runbooks devem conservar a mesma estrutura de seções para que profundidade e organização
não virem variáveis acidentais na comparação.

## Fronteiras curriculares

- Não adicione splitter, embedding, vector store, retriever ou RAG.
- Não adicione retry, cache, async, middleware, persistência ou tratamento abrangente de erro.
- Não transforme o exemplo em acesso genérico ao filesystem.
- Não acrescente observabilidade do loop ou de todas as chamadas de ferramentas.

## Ambiente e pacotes

- Use somente `uv`; nunca `pip`, Poetry, Conda ou ativação manual de virtualenv.
- Dependências devem ser alteradas com `uv add` ou `uv remove` para preservar o lockfile.
- Não use `temperature`, `top_p` ou `top_k`.

## Credenciais

`ANTHROPIC_API_KEY` nunca entra no repositório. `.env.example` contém somente placeholder e
`.env` permanece ignorado.
