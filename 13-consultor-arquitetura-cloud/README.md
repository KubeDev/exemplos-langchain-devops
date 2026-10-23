# 13 — Consultor de arquitetura Cloud com duas memórias

Este exemplo usa o **checkpointer PostgreSQL** para retomar uma conversa por `thread_id` e o
**Store PostgreSQL** para guardar projetos e decisões entre conversas. O agente só
consulta a memória do projeto quando o usuário pede. Os resultados das ferramentas aparecem no
chat para que a origem da resposta seja visível.

## Preparação

Use Python 3.12, `uv`, Docker e uma chave da API da Anthropic. Nesta pasta:

```bash
cp .env.example .env
uv sync --locked
docker compose up -d --wait
uv run flask --app src.web run --port 8502
```

Preencha `ANTHROPIC_API_KEY` no `.env` antes de enviar mensagens. Abra
`http://127.0.0.1:8502`. O PostgreSQL usa `127.0.0.1:55433` e um volume persistente.
O `.env` e a `.venv` ficam fora do Git. Não use dados reais de clientes ou infraestrutura.
Registros de versões anteriores permanecem no banco e podem conter outro formato. O exemplo
não os migra; para a gravação, prepare um banco novo.

## Percurso da aula

1. No perfil **Ana**, comece uma conversa e peça para criar o projeto `Plataforma Aurora`.
2. Diga: `Decidimos usar AWS na região sa-east-1. Registre essa decisão.`
3. Diga: `Decidimos usar uma fila entre a API e o processamento. Registre essa decisão.`
4. Pergunte: `Quais decisões estão registradas para este projeto?` Observe as duas decisões retornadas por `consultar_projeto`.
5. Crie outra conversa de Ana. Peça para listar projetos, escolha `Plataforma Aurora` e pergunte: `O que já foi decidido?` A nova thread não contém o histórico da primeira; a ferramenta recupera a decisão.
6. Volte à primeira conversa para observar seu histórico pelo checkpointer. Reinicie apenas o Flask e recarregue a página: as conversas e os dados do projeto continuam disponíveis.
7. Troque para o perfil **Bruno** e peça para listar projetos. O catálogo dele deve estar vazio.

A resposta do modelo pode variar. A prova é o histórico da thread e o resultado da ferramenta
mostrado no chat. Os perfis são apenas uma simulação didática, **não autenticação**.

## Onde está cada dado

- `src/web.py`: página Flask, perfis de demonstração e leitura do histórico no checkpointer;
- `src/agent.py`: agente, instruções de escrita explícita e `invoke` com `thread_id` e usuário;
- `src/memory_tools.py`: ferramentas que usam `runtime.store`; projetos e decisões ficam em namespaces separados;
- `src/database.py`: conexões do checkpointer e do Store ao mesmo PostgreSQL;
- `compose.yaml`: banco e volume local.

A escolha do projeto fica nas mensagens da conversa; uma nova thread pede a escolha de novo.
O catálogo usa o namespace `("consultor-arquitetura-cloud", user_id, "projects")` e o nome
normalizado do projeto como chave. Cada decisão ocupa um item próprio no namespace
`("consultor-arquitetura-cloud", user_id, "decisions", nome_normalizado)`, com uma chave
única e o valor `{"texto": "..."}`. `consultar_projeto` reúne esses itens para responder.
