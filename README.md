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
| 09 | [`09-inventario-ec2`](09-inventario-ec2) | Consultar o inventário EC2 da conta | A mesma ferramenta declarada de quatro formas e o esquema que o modelo recebe de cada uma |
| 10 | [`10-inventario-ec2-testes`](10-inventario-ec2-testes) | Garantir que a ferramenta do inventário funciona antes de entregá-la ao agente | Teste da ferramenta sem modelo: invocação direta, pedido de chamada escrito à mão e validação do esquema na execução |
| 11 | [`11-inventario-ec2-colisao`](11-inventario-ec2-colisao) | Escolher entre duas ferramentas parecidas: estado e status das instâncias | Colisão entre ferramentas, diagnóstico pela chamada pedida e correção por descrição contrastiva |
| 12 | [`12-pesquisa-web-devops`](12-pesquisa-web-devops) | Pesquisar tendências de DevOps e cloud e ler um documento na web | Ferramentas prontas de pacotes de integração (Tavily e Firecrawl), registradas com uma chave e trocadas por uma linha |

A ordem importa. O `02` coloca a chamada isolada do `01` num loop, passa a compor a entrada
por template e mostra que o modelo esquece; o `03` resolve isso com memória explícita, num
slot do mesmo template; o `04` entra no runtime sem tools e
torna o contexto externo explícito; o `05` registra a primeira ferramenta no agente; o `06`
conecta o agente a ferramentas Kubernetes publicadas por um MCP server e torna o fluxo
observável; o `07` transforma uma solicitação em execução single shot; o `08` adiciona
conversa, memória de sessão e retorno progressivo; o `09` sai do cluster para uma conta AWS e
olha a ferramenta por dentro: as formas de declará-la e o esquema que cada uma envia ao modelo;
o `10` testa essa ferramenta sem modelo, no lugar da aplicação que executa o pedido;
o `11` coloca uma segunda ferramenta ao lado dela e mostra que descrições parecidas colidem;
e o `12` deixa de escrever a ferramenta e usa ferramentas prontas do ecossistema, com camada gratuita.

## Pré-requisitos

- [uv](https://docs.astral.sh/uv/) — gerencia Python e dependências
- Python 3.12 (o `uv` instala sozinho, se faltar)
- Uma chave da Gemini Developer API para os exemplos `01` e `02`
- Uma chave da API da Anthropic para os exemplos `03` a `09`, `11` e `12` (o `10` não usa modelo)
- Node.js, `npx`, `kubectl` e um cluster de estudo para os exemplos `06` a `08`
- Uma conta AWS com credencial de leitura do EC2 para os exemplos `09` a `11`
- Chaves do Tavily e do Firecrawl para o exemplo `12` (as duas têm camada gratuita, sem cartão)

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
cd 09-inventario-ec2        && uv run inventario-ec2 "Quais instâncias estão paradas?"
cd 10-inventario-ec2-testes && uv run pytest -v
cd 11-inventario-ec2-colisao && uv run inventario-ec2-colisao "Qual o status da worker-01?"
cd 12-pesquisa-web-devops   && uv run pesquisa-web-devops "Quais as tendências recentes de DevOps e cloud?"
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
