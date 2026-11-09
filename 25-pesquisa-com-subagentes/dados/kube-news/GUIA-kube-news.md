---
projeto: kube-news
tipo: guia
commit: aab9356
---

# Guia do kube-news

Portal de notícias em Node.js. Permite listar, cadastrar e visualizar notícias, e tem rotas de saúde e de simulação de falha. Este guia leva do clone do repositório até a aplicação rodando na sua máquina.

## Stack

- Node.js com Express 4
- EJS como motor de templates
- Sequelize como ORM, com PostgreSQL
- Métricas Prometheus pelo `express-prom-bundle` e um contador próprio `http_requests_total`

## Pré-requisitos

- Git
- Node.js com npm. O time usa o Node.js 24; o `package.json` não fixa versão.
- PostgreSQL rodando na sua máquina, com acesso de superusuário (`postgres`) e o cliente `psql`

O repositório não tem Dockerfile nem arquivo de Compose: o banco é instalado direto na máquina.

## 1. Obter o projeto

O repositório é público:

```bash
git clone https://github.com/KubeDev/kube-news.git
cd kube-news
git log -1 --format="%h %s"
```

Este guia descreve o commit `aab9356` ("Melhorias na documentação."). Se o `git log` mostrar outro commit, confira o código antes de seguir um passo daqui.

O código da aplicação fica todo em `src/`. Na raiz estão só o `README.md` e o `popula-dados.http`.

## 2. Preparar o banco local

A aplicação já vem com valores padrão para a conexão: base `kubedevnews`, usuário `kubedevnews`, senha `Pg#123`, em `localhost:5432`. O caminho mais curto é criar o banco com esses mesmos valores:

```bash
psql -U postgres -h localhost
```

```sql
CREATE USER kubedevnews WITH PASSWORD 'Pg#123';
CREATE DATABASE kubedevnews OWNER kubedevnews;
```

Não é preciso criar tabela: na subida, a aplicação executa `sync({ alter: true })` do Sequelize e cria a tabela `Posts` sozinha.

## 3. Instalar as dependências

```bash
cd src
npm install
```

O `npm install` termina com avisos de vulnerabilidade nas dependências. Não rode `npm audit fix --force`: ele troca versões fixadas no `package.json` e muda o comportamento da aplicação.

## 4. Configurar as variáveis de ambiente

A conexão usa variáveis separadas, lidas em `src/models/post.js`. Toda variável ausente cai no valor padrão:

| Variável | Padrão | Observação |
|---|---|---|
| `DB_DATABASE` | `kubedevnews` | nome da base |
| `DB_USERNAME` | `kubedevnews` | usuário |
| `DB_PASSWORD` | `Pg#123` | senha |
| `DB_HOST` | `localhost` | endereço do banco |
| `DB_PORT` | `5432` | porta do banco |
| `DB_SSL_REQUIRE` | `false` | só o texto exato `true` liga o SSL |

Se você criou o banco com os valores do passo 2, não precisa configurar nada. Se o seu PostgreSQL usa outra porta ou outra senha, exporte as variáveis no mesmo terminal antes de subir:

```bash
export DB_PORT=5433
export DB_PASSWORD='outra-senha'
```

Não existe arquivo `.env` no kube-news nem uma variável `DATABASE_URL`. Quem vem do encontros-tech costuma procurar os dois e não encontra.

## 5. Subir a aplicação

Ainda dentro de `src/`:

```bash
npm start
```

O terminal mostra `Aplicação rodando na porta 8080` e, em seguida, as linhas `Executing (default): ...` do Sequelize ajustando a tabela `Posts`. A porta é sempre 8080: ela está fixa em `src/server.js` (`app.listen(8080)`) e não existe variável para mudá-la.

## 6. Verificar

Em outro terminal:

```bash
curl http://localhost:8080/health
curl -o /dev/null -w "%{http_code}\n" http://localhost:8080/ready
```

O `/health` devolve `{"state":"up","machine":"<nome da sua máquina>"}` e o `/ready` devolve 200. No navegador, `http://localhost:8080` mostra a página inicial, ainda sem notícias.

## 7. Carregar notícias de exemplo

O arquivo `popula-dados.http`, na raiz, carrega notícias pela rota `POST /api/post`, mas aponta para a porta 4503. Ajuste para a 8080 antes de usar, no arquivo ou direto pelo `curl`:

```bash
curl -X POST http://localhost:8080/api/post \
  -H "Content-Type: application/json" \
  -d '{"artigos":[{"title":"Kubernetes na Nuvem","resumo":"Gerencie contêineres na nuvem.","description":"Saiba como orquestrar contêineres na nuvem."}]}'
```

A página inicial passa a listar a notícia. Para cadastrar uma de cada vez, use o formulário em `http://localhost:8080/post`.

## 8. Testes

O repositório não tem testes automatizados: o `npm test` só imprime um erro. A verificação é a do passo 6.

## Rotas

| Rota | Método | O que faz |
|---|---|---|
| `/` | GET | lista as notícias |
| `/post` | GET | formulário de nova notícia |
| `/post` | POST | cadastra pelo formulário, com validação de tamanho |
| `/post/:id` | GET | mostra uma notícia |
| `/api/post` | POST | cadastra várias notícias de uma vez, sem validação |
| `/health` | GET | devolve `state` e o nome da máquina |
| `/ready` | GET | 200 quando pronta, 500 durante a indisponibilidade simulada |
| `/metrics` | GET | métricas Prometheus |
| `/unhealth` | PUT | simula falha: a aplicação passa a devolver 500 em tudo, exceto `/metrics` |
| `/unreadyfor/:seconds` | PUT | simula indisponibilidade do `/ready` por N segundos |

As duas rotas `PUT` existem para testar resiliência. Não chame `/unhealth` na sua máquina esperando voltar sem reiniciar: o estado só volta ao normal com o reinício do processo.

## Regras de validação do formulário

O `POST /post` só aceita a notícia quando o título tem menos de 30 caracteres, o resumo menos de 50 e a descrição menos de 2000, e nenhum deles está vazio. A rota `/api/post` não aplica essas regras, e o banco recusa título ou resumo acima de 255 caracteres: um valor maior pela API derruba o processo.

## Logs

Cada requisição imprime uma linha no terminal pelo middleware `countRequests`:

```text
Request Type: GET /
```

## Em produção

Em `kube-news-prod-01`, a aplicação roda com o mesmo `npm start` dentro de `src/`, com as variáveis `DB_*` apontando para o PostgreSQL gerenciado `pg-prod.interno` e `DB_SSL_REQUIRE=true`.

## Quando algo dá errado

- Não conecta no banco: `RB-kube-news-conexao-banco.md`
- 500 em todas as rotas: `RB-kube-news-500-em-todas-as-rotas.md`
- Só o `/ready` devolve 500: `RB-kube-news-ready-500.md`
- Carga de notícias falhando: `RB-kube-news-carga-de-noticias.md`
