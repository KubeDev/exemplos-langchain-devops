# 12 — Chat com checkpointer em memória e PostgreSQL

Este chat de uso geral usa `CHECKPOINTER_BACKEND=memory|postgres` para escolher onde guardar o
histórico de cada `thread_id`. Cada sessão recebe um UUID. O seletor lista threads que já têm
checkpoint; a página lê as mensagens salvas, sem guardar outra cópia no navegador.

## Preparação e execução

Use Python 3.12, `uv` e uma chave da API da Anthropic. Copie `.env.example` para `.env`,
preencha `ANTHROPIC_API_KEY` e execute nesta pasta:

```bash
uv sync --locked
uv run flask --app src.web run --port 8501
```

Abra `http://127.0.0.1:8501`. O `.env` é ignorado pelo Git. O padrão é `memory`, que guarda
as threads somente durante a vida do processo Flask.

Para usar PostgreSQL, inicie o banco, altere `CHECKPOINTER_BACKEND=postgres` no `.env` e
reinicie o Flask:

```bash
docker compose up -d --wait
uv run flask --app src.web run --port 8501
```

Para alternar durante a gravação sem editar o arquivo, use
`CHECKPOINTER_BACKEND=postgres uv run flask --app src.web run --port 8501`. O Compose expõe o
banco somente em `127.0.0.1:55432` e mantém os dados no volume `postgres_data`.

## Percurso da aula

1. Clique em **Nova sessão** e envie: `Estou planejando uma viagem para Recife em novembro. Quero visitar museus.`
2. Pergunte: `Para qual cidade estou viajando e que passeio mencionei?`
3. Crie outra sessão e envie: `Quero preparar um jantar vegetariano para quatro pessoas.` Use o seletor para alternar entre os dois históricos.
4. Pare o Flask e inicie-o novamente com `memory`. As sessões anteriores desaparecem: o saver vivia somente no processo encerrado.
5. Inicie o PostgreSQL e o Flask com `CHECKPOINTER_BACKEND=postgres`. Repita os mesmos prompts em duas threads.
6. Reinicie só o Flask. Carregue a conversa da viagem no seletor e pergunte: `Retomando a viagem: qual cidade e que tipo de passeio eu mencionei?` O histórico volta do banco.

As respostas do modelo podem variar; a prova é o histórico exibido para cada thread.

## Arquivos

- `src/checkpointer.py`: `InMemorySaver` no processo ou `PostgresSaver.from_conn_string()`;
- `src/agent.py`: `create_agent` e `invoke` com a mensagem nova e o `thread_id`;
- `src/web.py`: escolhe o caminho do backend, recebe formulários e renderiza o histórico com Jinja;
- `compose.yaml`: PostgreSQL e volume persistente;
- `src/templates/index.html` e `src/static/style.css`: página e aparência.
