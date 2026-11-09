---
projeto: encontros-tech
tipo: guia
commit: 0f5bbad
---

# Guia do encontros-tech

Agenda de eventos de tecnologia em Python. Qualquer pessoa cadastra um evento e recebe um token de edição; sem esse token o evento não pode ser alterado. Este guia leva do clone do repositório até a aplicação rodando e os testes passando na sua máquina.

## Stack

- Python com Flask 3
- SQLAlchemy 2 com PostgreSQL (driver `psycopg2`)
- Pydantic e `pydantic-settings` para os dados e a configuração
- Templates Jinja2
- Métricas Prometheus pelo `prometheus-flask-exporter`
- Gunicorn listado nas dependências para rodar em produção
- Testes com `pytest`

## Pré-requisitos

- Git
- Python 3.12 ou 3.13. No Python 3.14 a instalação falha: as versões fixadas no `requirements.txt` não têm pacote para ele (o primeiro erro aparece no `MarkupSafe==3.0.2`).
- PostgreSQL rodando na sua máquina, com acesso de superusuário (`postgres`) e o cliente `psql`

O repositório não tem Dockerfile nem arquivo de Compose: o último commit removeu a configuração de Docker, e o banco é instalado direto na máquina.

## 1. Obter o projeto

O repositório é público:

```bash
git clone https://github.com/KubeDev/encontros-tech.git
cd encontros-tech
git log -1 --format="%h %s"
```

Este guia descreve o commit `0f5bbad` ("Removendo Docker"). Se o `git log` mostrar outro commit, confira o código antes de seguir um passo daqui.

O código da aplicação fica em `src/`. Na raiz estão o `pytest.ini`, o `.env.exemple` e o `api-requests.http`.

## 2. Preparar o banco local

O valor padrão da conexão é `postgresql://encontros_tech:encontros_tech@localhost:5432/encontros_tech`. O caminho mais curto é criar o banco com esses mesmos valores:

```bash
psql -U postgres -h localhost
```

```sql
CREATE USER encontros_tech WITH PASSWORD 'encontros_tech';
CREATE DATABASE encontros_tech OWNER encontros_tech;
```

Não é preciso criar tabela: na subida, `main.py` executa `Base.metadata.create_all` e cria a tabela `events`.

## 3. Criar o ambiente virtual e instalar as dependências

Na raiz do repositório:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r src/requirements.txt
```

O `requirements.txt` já inclui o `pytest`, então o mesmo ambiente serve para rodar os testes.

## 4. Configurar as variáveis de ambiente

As variáveis são lidas em `src/core/settings.py`. O `load_dotenv()` procura um arquivo `.env` a partir de `src/core/` subindo as pastas, então `src/.env` é encontrado. Crie o seu a partir do modelo:

```bash
cp src/.env.example src/.env
```

Ajuste a `DATABASE_URL` se o seu banco não usa os valores do passo 2. As linhas `POSTGRES_USER`, `POSTGRES_PASSWORD` e `POSTGRES_DB` do modelo eram usadas pelo Compose, que saiu do repositório: a aplicação não lê essas três.

| Variável | Padrão | Observação |
|---|---|---|
| `DATABASE_URL` | `postgresql://encontros_tech:encontros_tech@localhost:5432/encontros_tech` | conexão completa numa variável só |
| `HOST` | `0.0.0.0` | usado por `python main.py` |
| `PORT` | `8000` | usado por `python main.py` |
| `DEBUG` | `False` | também define o `LOG_LEVEL` padrão |
| `LOG_LEVEL` | `INFO` | `DEBUG` quando `DEBUG=true` |
| `LOG_FORMAT` | `colored` | `colored` ou `simple` |
| `SERVICE_NAME` | `encontros-tech` | nome no log e nas métricas |
| `SERVICE_VERSION` | `1.0.0` | exposto na métrica `app_info` |
| `PROMETHEUS_MULTIPROC_DIR` | `/tmp/prometheus_multiproc` | diretório criado na subida |

O `.env` é ignorado pelo git: ele nunca vai junto com o código. Diferente do kube-news, o encontros-tech não tem variáveis `DB_HOST` ou `DB_PASSWORD`: tudo vai na `DATABASE_URL`.

## 5. Subir a aplicação

Os imports partem de `src/` (`from core.settings import settings`), então a aplicação roda de dentro dessa pasta:

```bash
cd src
python main.py
```

O log mostra a criação das tabelas e a aplicação pronta:

```text
2026-05-14 09:12:01,725 | INFO | encontros-tech | <module>:20 | Criando tabelas no banco de dados
2026-05-14 09:12:01,881 | INFO | encontros-tech | <module>:59 | Aplicação Flask inicializada - Versão: 1.0.0
```

Rodar `python src/main.py` a partir da raiz falha nos imports.

## 6. Verificar

Abra `http://localhost:8000` no navegador: a página inicial lista os eventos, ainda vazia. As métricas ficam em `http://localhost:8000/metrics`. Não existe rota de health check no encontros-tech.

## 7. Cadastrar eventos

Use o formulário em `http://localhost:8000/events/new`. Depois do cadastro, a aplicação redireciona para `/?created=<id>&token=<token>` e a página inicial mostra o link de edição. Guarde esse link: ele aparece uma vez só, e sem o token o evento não pode ser editado.

Problema conhecido no commit `0f5bbad`: a API `/api/events/` responde 500 no `POST` e no `GET`, e as rotas `/api/events/by-token/<token>` também. As rotas chamam `model_dump()` direto no objeto do banco, e o log mostra `'Event' object has no attribute 'model_dump'`. No `POST`, o evento é gravado antes do erro: repetir a chamada achando que falhou cria um evento duplicado. Por isso o `api-requests.http` da raiz não serve para popular a base hoje.

## 8. Rodar os testes

Os testes ficam em `src/tests/` e usam um banco simulado (`MagicMock`), então não dependem do PostgreSQL. Eles importam os módulos a partir de `src/`:

```bash
cd src
python -m pytest tests
```

O resultado esperado é `7 passed`.

## Rotas

| Rota | Método | O que faz |
|---|---|---|
| `/` | GET | lista os eventos |
| `/events/new` | GET | formulário de novo evento |
| `/events/` | POST | cadastra pelo formulário e redireciona para `/?created=<id>&token=<token>` |
| `/events/<id>` | GET | detalhe do evento |
| `/events/edit/<token>` | GET e POST | edição pelo token |
| `/api/events/` | GET e POST | lista e cadastra pela API (hoje responde 500) |
| `/api/events/by-token/<token>` | GET e PUT | busca e atualiza pelo token (hoje responde 500) |
| `/metrics` | GET | métricas Prometheus |

## Logs

O formato é `data | nível | logger | função:linha | mensagem`, por exemplo:

```text
2026-05-14 09:12:03,118 | INFO | encontros-tech | log_request:107 | HTTP GET / - Status: 200
```

## Em produção

Em `encontros-prod-01`, a aplicação roda com Gunicorn dentro de `src/`, com a `DATABASE_URL` do PostgreSQL gerenciado `pg-prod.interno` num `src/.env` criado no próprio servidor:

```bash
gunicorn -w 4 -b 0.0.0.0:8000 main:app
```

## Quando algo dá errado

- Não conecta no banco: `RB-encontros-tech-conexao-banco.md`
- Organizador sem o link de edição: `RB-encontros-tech-edicao-de-evento.md`
- Métricas inconsistentes com Gunicorn: `RB-encontros-tech-metricas-gunicorn.md`
