# Plano de teste manual

Roteiro para validar o exemplo do zero. São ~10 minutos e aproximadamente US$ 0,50 em
chamadas de API.

Marque cada `[ ]` conforme executa. Onde um critério pode falhar, o item **Se falhar** logo
abaixo diz o que investigar.

> O modelo não é determinístico: a quantidade de chamadas de ferramenta, a ordem delas e o
> texto do relatório **variam** entre execuções. O que **não** pode variar é o modo escolhido
> (analisar vs gerar), o framework identificado e a porta descoberta.

---

## Parte 0 · Preparação

- [ ] **0.1** — `uv --version` responde (se não: https://docs.astral.sh/uv/)
- [ ] **0.2** — `uv sync` conclui sem erro
- [ ] **0.3** — `cp .env.example .env` e preencher `ANTHROPIC_API_KEY`
- [ ] **0.4** — Clonar os três projetos-alvo num diretório de trabalho:

```bash
mkdir -p ~/demo-live02 && cd ~/demo-live02
git clone https://github.com/KubeDev/encontros-tech.git
git clone https://github.com/KubeDev/kube-news.git
git clone https://github.com/KubeDev/fake-shop.git
```

- [ ] **0.5** — Nenhum dos três tem Dockerfile:
      `ls ~/demo-live02/*/Dockerfile` → "No such file or directory" nos três

> **Deixe o terminal em tela cheia.** O log de chamadas é a parte da demonstração que ensina
> tool calling — se ele rolar rápido demais para ser lido, a aula perde o ponto.

---

## Parte 1 · Cenário 1 — Python/Flask, dependências fora da raiz

```bash
uv run smart-docker ~/demo-live02/encontros-tech
```

- [ ] **1.1** — Nenhum warning aparece antes do banner
- [ ] **1.2** — O log mostra chamadas numeradas, com caminhos **relativos** (`dir_path='src'`,
      não o caminho absoluto)
- [ ] **1.3** — Cada retorno traz o número da sua chamada (`[3] -> ...`), mesmo chegando fora
      de ordem
- [ ] **1.4** — A busca por `Dockerfile*` volta "No files found" e o agente **continua**
- [ ] **1.5** — O agente navega até `src/` e lê `src/requirements.txt`
- [ ] **1.6** — O relatório começa com **"# Dockerfile para ..."** (modo geração)
- [ ] **1.7** — Identifica **Flask** (não FastAPI) e menciona `gunicorn`
- [ ] **1.8** — Porta **8000**, encontrada em `src/core/settings.py`
- [ ] **1.9** — A versão do Python aparece como **"não declarada"**, com a suposição explicitada
- [ ] **1.10** — O Dockerfile gerado tem `USER`, `EXPOSE 8000` e multi-stage
- [ ] **1.11** — `relatorio.md` foi criado na raiz do projeto

> **Se falhar 1.5** (o agente conclui que não há dependências): a instrução do `prompt.py` que
> manda navegar nos subdiretórios foi enfraquecida. É o passo 2 do prompt — nos três projetos
> da demo o arquivo de dependências está em `src/`, nunca na raiz.

> **Se falhar 1.6** (veio "Relatorio de Analise Docker"): o agente alucinou um Dockerfile que
> não existe. Confira o passo 4 do `prompt.py` — a bifurcação precisa ser explícita.

**O ponto do cenário:** ninguém disse ao agente que o projeto é Flask, onde está o
`requirements.txt` ou qual é a porta. Tudo saiu de ferramentas que ele escolheu chamar.

---

## Parte 2 · Cenário 2 — Node.js, outra stack, mesmo agente

```bash
uv run smart-docker ~/demo-live02/kube-news
```

- [ ] **2.1** — Relatório em modo geração (**"# Dockerfile para kube-news"**)
- [ ] **2.2** — Identifica **Node.js/Express** e lê `src/package.json`
- [ ] **2.3** — Comando de start `node server.js`, vindo de `"scripts"` do `package.json`
- [ ] **2.4** — Porta **8080**, encontrada no `app.listen()` do `src/server.js`
- [ ] **2.5** — O Dockerfile gerado é **multi-stage** com imagem `node:*-alpine`
- [ ] **2.6** — Versão do Node aparece como não declarada (não há `engines` nem `.nvmrc`)

**O ponto do cenário:** o código do agente, o prompt e as ferramentas são **exatamente os
mesmos** do cenário 1. Mudou o projeto, mudou a stack, mudou o Dockerfile. É a diferença entre
um agente e um script.

---

## Parte 3 · Cenário 3 — o projeto com entrypoint

```bash
uv run smart-docker ~/demo-live02/fake-shop
```

- [ ] **3.1** — Relatório em modo geração
- [ ] **3.2** — Identifica **Flask** e as migrations **Alembic**
- [ ] **3.3** — **Encontra o `src/entrypoint.sh`** e o usa como `ENTRYPOINT` do Dockerfile
- [ ] **3.4** — Porta **5000**, tirada do bind do gunicorn no `entrypoint.sh`
- [ ] **3.5** — O Dockerfile inclui `chmod +x` no entrypoint

> **Se falhar 3.3** (ignora o entrypoint e usa `CMD` direto): o modo B do `prompt.py` perdeu a
> instrução de procurar `entrypoint.sh`/`start.sh`. Sem ela, o Dockerfile gerado sobe a
> aplicação sem rodar as migrations.

**O ponto do cenário:** dois projetos Flask (este e o cenário 1) geram Dockerfiles
**diferentes**, porque este tem um script de inicialização e o outro não. O agente não aplicou
um template — ele leu o projeto.

---

## Parte 4 · Cenário 4 — o outro ramo do modo duplo

Os três cenários anteriores exercitam apenas **metade** do agente. Este testa a outra.

```bash
cp -R ~/demo-live02/encontros-tech ~/demo-live02/com-dockerfile
rm -rf ~/demo-live02/com-dockerfile/.git
cat > ~/demo-live02/com-dockerfile/Dockerfile <<'EOF'
FROM python:latest

WORKDIR /app

COPY . .

RUN pip install -r src/requirements.txt

ENV DB_PASSWORD=postgres123

EXPOSE 5000

CMD ["python", "src/main.py"]
EOF

uv run smart-docker ~/demo-live02/com-dockerfile
```

São seis defeitos plantados de propósito: `latest`, `COPY . .` antes das dependências, root,
secret hardcoded, `EXPOSE 5000` numa aplicação que escuta 8000, e ausência de `.dockerignore`.

- [ ] **4.1** — O relatório começa com **"# Relatorio de Analise Docker"** (modo análise)
- [ ] **4.2** — Aponta a imagem `latest` sem versão fixada
- [ ] **4.3** — Aponta o **secret hardcoded** (`DB_PASSWORD`) com severidade crítica
- [ ] **4.4** — Aponta a falta de cache de layers
- [ ] **4.5** — Aponta a ausência de usuário não-root
- [ ] **4.6** — Aponta que **`EXPOSE 5000` não corresponde à porta real, 8000**
- [ ] **4.7** — Aponta a ausência de `.dockerignore`
- [ ] **4.8** — Traz a seção **Dockerfile Sugerido** completa
- [ ] **4.9** — Nota geral: **"precisa de ajustes"**

> **Se falhar 4.1** (veio "Dockerfile para ..."): o agente ignorou o Dockerfile existente e
> gerou um novo. A busca do passo 3 do `prompt.py` não está encontrando o arquivo na raiz.

> **Se falhar 4.6**: é o critério mais difícil da lista — exige cruzar o `EXPOSE` do Dockerfile
> com a porta lida em `src/core/settings.py`. Se os outros passarem e só este falhar,
> provavelmente o agente não leu o `settings.py`; verifique se o passo 2 do prompt continua
> mandando identificar a configuração da aplicação.

**O ponto do cenário:** mesmo comando, mesmo agente, relatório de estrutura completamente
diferente. Quem escolheu o caminho foi o modelo, olhando o resultado de uma busca — não um
`if` no Python.

---

## Parte 5 · Limpeza

- [ ] **5.1** — `rm -f relatorio.md`
- [ ] **5.2** — `rm -rf ~/demo-live02/com-dockerfile`
- [ ] **5.3** — Se usou uma chave temporária para o teste, **revogue-a** no console da Anthropic
