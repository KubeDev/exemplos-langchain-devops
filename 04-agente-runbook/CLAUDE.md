# Contexto para sessões de IA neste projeto

Leia o `README.md` para entender a demonstração. Este arquivo registra as fronteiras que
preservam a função didática do exemplo.

## Natureza do projeto

Exemplo didático `04` da série `langchain-devops-examples`. A lição é: **um arquivo privado
só vira conhecimento disponível quando a aplicação carrega seu conteúdo e o inclui na
entrada do modelo**.

O código será lido em aula e projetado numa tela. Quando simplicidade e robustez colidirem,
vence a simplicidade.

## Fluxo linear, sem abstrações prematuras

Mantenha um único fluxo dentro de `main()`: contexto, composição das mensagens e chamada ao
agente. A comparação é feita executando o mesmo código duas vezes; descomentar
`contexto = carregar_documento()` é a única mudança entre elas.

`carregar_documento()` é a única função auxiliar justificada: isola a mecânica do loader e
devolve o texto que entra no fluxo. Não extraia funções para compor mensagens, invocar o
agente ou imprimir a resposta.

## O runtime ainda não possui um ciclo de ação

`create_agent(model=model, tools=[])` é deliberado. Sem ferramentas, o runtime faz somente a
chamada ao modelo. Não descreva esse estado como um loop de decisão completo e não adicione uma
tool para “corrigir” a ausência: tool call, execução da função e `ToolMessage` são a próxima
aula.

O nome “primeiro agente” marca a entrada na abstração `create_agent`; a capacidade agentiva
ainda está incompleta e essa lacuna precisa ser nomeada em voz alta.

## O documento entra diretamente no prompt

Mantenha `TextLoader.load()`, os objetos `Document` e a composição de `page_content`
explícitos em `src/app.py`. Não introduza splitter, embedding, índice, vector store,
retriever ou RAG. O documento inteiro na janela é a limitação que a aula precisa revelar.

## A comparação precisa permanecer causal

- Use a mesma pergunta nas duas execuções.
- Reinicie o processo entre elas para que a primeira resposta não contamine a segunda.
- Mostre deterministicamente se `RB-274` está na mensagem de sistema.
- Trate o texto gerado pelo modelo como ilustração probabilística, não como prova.
- O runbook deve conter fatos fictícios e específicos que não possam ser recuperados de
  conhecimento público.

## Preserve a continuidade com o exemplo 03

O `ChatPromptTemplate` continua visível e mantém instruções, histórico e pergunta. A única
nova variável é `contexto`. Não converta a composição em LCEL nem esconda os objetos
intermediários.

## Ambiente e pacotes

- Use somente `uv`; nunca `pip`, Poetry, Conda ou ativação manual de virtualenv.
- Dependências devem ser alteradas com `uv add` ou `uv remove` para preservar o lockfile.
- Não use `temperature`, `top_p` ou `top_k`.
- Não adicione retry, cache, async, testes arquiteturais ou camadas de serviço.

## Credenciais

`ANTHROPIC_API_KEY` nunca entra no repositório. `.env.example` contém somente placeholder e
`.env` permanece ignorado.
