# LangChain para DevOps — exemplos

Uma série de exemplos didáticos de LangChain, cada um resolvendo um problema real de DevOps e
ensinando **uma** ideia por vez. São projetos independentes: você pode clonar o repositório
inteiro e rodar só o que interessa.

Os exemplos foram escritos para serem **lidos**, não estendidos. Cada um é o menor código que
demonstra sua ideia — o que falta num exemplo costuma ser o assunto do próximo.

## Os exemplos

| # | Pasta | O que resolve | O que ensina |
|---|---|---|---|
| 01 | [`01-chat-devops`](01-chat-devops) | Uma pergunta DevOps ao Gemini | Modelo, mensagens, `invoke()` vs `stream()` e metadados do `AIMessage` |
| 02 | [`02-chat-devops-sem-memoria`](02-chat-devops-sem-memoria) | A mesma pergunta, agora num chat que continua aberto | Que um terminal contínuo não é uma conversa: cada chamada começa do zero, e que um `ChatPromptTemplate` compõe a entrada |
| 03 | [`03-chat-devops-memoria`](03-chat-devops-memoria) | O mesmo chat, agora lembrando da conversa | Que o modelo **não** tem memória — quem lembra é o seu código, reenviando a lista por um `MessagesPlaceholder` |
| 04 | [`04-agente-runbook`](04-agente-runbook) | Responder sobre um runbook privado carregado pela aplicação | Runtime mínimo de agente, objetos `Document` e conhecimento inserido diretamente no contexto |
| 05 | [`05-agente-runbook-tool`](05-agente-runbook-tool) | Consultar diferentes runbooks pelo identificador presente na pergunta | Criação de ferramenta, registro com `create_agent` e seleção de parâmetro pelo modelo |
| 06 | [`06-assistente-plataforma`](06-assistente-plataforma) | Consultar o cluster Kubernetes em linguagem natural | Descoberta e registro do catálogo de ferramentas de um MCP server HTTP |
| 07 | [`07-assistente-plataforma-cli`](07-assistente-plataforma-cli) | Executar uma consulta operacional por processo | Contrato de CLI com argumento, contexto, canais e códigos de saída |
| 08 | [`08-assistente-plataforma-chat`](08-assistente-plataforma-chat) | Conversar com o assistente e acompanhar a resposta | Histórico de sessão e retorno progressivo em Streamlit |
| 09 | [`09-inventario-droplets`](09-inventario-droplets) | Consultar os Droplets de uma conta DigitalOcean | A mesma ferramenta declarada de duas formas (docstring e Pydantic) e o esquema que o modelo recebe de cada uma |
| 10 | [`10-pesquisa-web-devops`](10-pesquisa-web-devops) | Pesquisar tendências de DevOps e cloud na web | Ferramenta pronta de pacote de integração (Tavily): o esquema é do pacote e a consulta sai do seu ambiente |
| 11 | [`11-inventario-droplets-mcp`](11-inventario-droplets-mcp) | Consultar e ligar/desligar recursos de uma conta DigitalOcean | O agente não declara ferramenta: descobre o catálogo inteiro de um MCP server próprio, inclusive ferramentas de escrita |
| 12 | [`12-agente-memoria-persistente`](12-agente-memoria-persistente) | Comparar a conversa antes e depois de reiniciar o chat | Checkpointer por thread em memória ou PostgreSQL, escolhido por variável de ambiente |
| 13 | [`13-consultor-arquitetura-cloud`](13-consultor-arquitetura-cloud) | Retomar conversas e consultar decisões de um projeto Cloud | Checkpointer por thread e Store por usuário e projeto, ambos no PostgreSQL |
| 14 | [`14-busca-vetorial-pgvector`](14-busca-vetorial-pgvector) | Encontrar documentos operacionais por similaridade | Embeddings OpenAI, pgvector e busca com `k` e distância, sem gerar resposta |
| 15 | [`15-chunking-dados-operacionais`](15-chunking-dados-operacionais) | Dividir a documentação para a busca | Estratégia de chunk pela natureza do dado, sobreposição e tamanho medido, com os chunks indexados no pgvector e buscados por similaridade |
| 16 | [`16-reindexacao-incremental`](16-reindexacao-incremental) | Manter o índice em dia com uma base que muda | Indexação incremental por hash e ID estável numa base com versões v1 e v2, e reindexação total no lugar ou numa coleção nova, com embeddings locais pelo Ollama |
| 17 | [`17-agente-onboarding`](17-agente-onboarding) | Achar o procedimento certo do projeto certo numa base de onboarding | Retriever no agente como etapa fixa (2-Step): a aplicação busca sempre, sem filtro, antes do modelo; ingestão e chat web com sessões no PostgreSQL |
| 18 | [`18-agente-onboarding-tool`](18-agente-onboarding-tool) | Deixar o agente decidir a busca e o projeto | Retriever como ferramenta (Agentic), com filtro por metadados montado pelo agente, que pergunta o projeto quando falta |
| 19 | [`19-limite-chamadas-agente`](19-limite-chamadas-agente) | Parar um agente que consulta um deploy que nunca termina | `ModelCallLimitMiddleware` encerra a execução; `ToolCallLimitMiddleware` bloqueia a chamada excedida e o modelo responde |
| 20 | [`20-tratamento-erro-ferramenta`](20-tratamento-erro-ferramenta) | Manter o agente de pé quando a API que a ferramenta chama falha | `ToolErrorMiddleware` devolve a exceção ao modelo como mensagem; `ToolRetryMiddleware`, interno, repete só o erro transitório com recuo exponencial |

A ordem importa. O `02` coloca a chamada isolada do `01` num loop, passa a compor a entrada
por template e mostra que o modelo esquece; o `03` resolve isso com memória explícita, num
slot do mesmo template; o `04` entra no runtime sem tools e
torna o contexto externo explícito; o `05` registra a primeira ferramenta no agente; o `06`
conecta o agente a ferramentas Kubernetes publicadas por um MCP server e torna o fluxo
observável; o `07` transforma uma solicitação em execução single shot; o `08` adiciona
conversa, memória de sessão e retorno progressivo; o `09` sai do cluster para uma conta
DigitalOcean e olha a ferramenta por dentro: as formas de declará-la e o esquema que cada uma
envia ao modelo, e é também o projeto em que um agente de codificação cria os testes da
ferramenta, sem modelo, no lugar da aplicação que executa o pedido; e o `10` deixa de escrever
a ferramenta e usa uma pronta do ecossistema; o `11` volta à conta DigitalOcean, agora
com todas as ferramentas descobertas de um MCP server próprio; e o `12` compara o mesmo
chat com checkpoints em memória e no PostgreSQL após reiniciar a aplicação; o `13` acrescenta
um Store para dados do projeto que atravessam threads; o `14` indexa PDF e Markdown em
um banco vetorial e recupera o texto diretamente, antes de conectá-lo ao agente; o `15` troca
o arquivo inteiro por chunks escolhidos pela natureza de cada dado e busca nesses chunks; e o `16` deixa de
regerar a coleção inteira a cada execução: grava só o que mudou e reindexa tudo, no lugar ou numa coleção nova,
quando muda o que o hash não vê, como o modelo de embedding; e o `17` liga a base ao agente como etapa fixa: a aplicação busca sempre, sem filtro, numa conversa com
sessões; e o `18` entrega a busca ao agente como ferramenta: ele monta o filtro de metadado e pergunta o projeto
quando falta; e o `19` abre o capítulo de middleware: um teto de chamadas de modelo ou de ferramenta
para o agente que repete a mesma consulta sem progresso; e o `20` trata o erro da ferramenta: a
exceção vira mensagem que o modelo lê, e só o erro transitório ganha nova tentativa.

## Pré-requisitos

- [uv](https://docs.astral.sh/uv/) — gerencia Python e dependências
- Python 3.12 (o `uv` instala sozinho, se faltar)
- Uma chave da Gemini Developer API para os exemplos `01` e `02`
- Uma chave da API da Anthropic para os exemplos `03` a `13` e `17` a `20`
- Uma chave da API da OpenAI para os embeddings dos exemplos `14` e `15`
- O [Ollama](https://ollama.com) instalado para os embeddings locais dos exemplos `16` a `18`
- Docker com Compose para o PostgreSQL dos exemplos `12` a `18`
- Node.js, `npx`, `kubectl` e um cluster de estudo para os exemplos `06` a `08`
- Uma conta DigitalOcean para o exemplo `09`, com tokens de escopo
  customizado:
  - um token de leitura (`droplet:read`) para o exemplo e os testes;
  - um token de setup, usado só pelos scripts de `setup/` do `09` para criar e destruir os
    Droplets de teste.
- Uma chave do Tavily para o exemplo `10`
- O MCP server DigitalOcean rodando em `http://localhost:8000/mcp` para o exemplo `11`

> **Droplets de teste geram custo** enquanto existirem, mesmo desligados. Crie-os com o
> `setup/` do `09` quando for estudar e destrua-os com o mesmo `setup/` ao terminar.

## Como rodar qualquer exemplo

Todo exemplo segue o mesmo ritual, sempre **de dentro da pasta dele**:

```bash
cd 01-chat-devops
cp .env.example .env      # preencha GOOGLE_API_KEY
uv sync
```

O comando de execução muda por exemplo:

```bash
cd 01-chat-devops          && uv run src/app.py
cd 02-chat-devops-sem-memoria && uv run chat-devops-sem-memoria
cd 03-chat-devops-memoria  && uv run chat-devops-memoria
cd 04-agente-runbook        && uv run agente-runbook
cd 05-agente-runbook-tool   && uv run agente-runbook-tool
cd 06-assistente-plataforma && uv run assistente-plataforma
cd 07-assistente-plataforma-cli && uv run assistente-plataforma-cli "Liste os pods com reinicializações" --namespace kube-system
cd 08-assistente-plataforma-chat && uv run streamlit run src/app.py
cd 09-inventario-droplets   && uv run inventario-droplets "Quais Droplets estão em nyc1?"
cd 10-pesquisa-web-devops   && uv run pesquisa-web-devops "Quais as tendências recentes de DevOps e cloud?"
cd 11-inventario-droplets-mcp && uv run inventario-droplets-mcp "Quais Droplets estão ativos?"
cd 12-agente-memoria-persistente && uv run flask --app src.web run --port 8501
cd 13-consultor-arquitetura-cloud && uv run flask --app src.web run --port 8502
cd 14-busca-vetorial-pgvector && uv run indexar
cd 14-busca-vetorial-pgvector && uv run buscar "fila parada após rotação de credencial" --k 3
cd 15-chunking-dados-operacionais && uv run gerar-chunks
cd 15-chunking-dados-operacionais && uv run indexar
cd 19-limite-chamadas-agente && uv run limite-modelo dpl-4821
cd 19-limite-chamadas-agente && uv run limite-ferramenta dpl-4821
cd 20-tratamento-erro-ferramenta && uv run erro-ferramenta 498123456
cd 20-tratamento-erro-ferramenta && uv run retry-ferramenta 498123456
```

Cada pasta tem um `README.md` próprio, com a explicação completa daquele exemplo. Comece por
ele.

## Como o repositório é organizado

Pastas seguem `nn-slug`: número sequencial da aula + nome do projeto. Cada exemplo é
**autocontido** — tem seu próprio `pyproject.toml`, `uv.lock`, `.venv` e `.env`. Não há
workspace, pacote compartilhado nem utilitário comum, de propósito: você pode copiar uma pasta
sozinha para outro lugar e ela roda.

Isso significa dependência duplicada entre os exemplos. É intencional, e o preço é barato
perto de poder tratar cada aula como um projeto independente.

## Sua chave nunca entra no repositório

Cada exemplo tem `.env.example` com placeholder; o `.env` de verdade está no `.gitignore`.
Nenhum arquivo versionado aqui contém credencial.
