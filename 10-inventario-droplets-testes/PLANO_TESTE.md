# Plano de teste · testando a ferramenta

Roteiro manual para validar o exemplo antes da gravação. Rode tudo de dentro de
`10-inventario-droplets-testes`.

## 1. Instalação e estrutura

- [ ] `uv sync --locked` conclui sem alterar `uv.lock`.
- [ ] `pyproject.toml` não tem `langchain-anthropic` e tem `pytest` no grupo `dev`.
- [ ] `.env` só com `DIGITALOCEAN_TOKEN`; nenhuma chave de modelo.
- [ ] `.env`, `.venv` e caches estão ignorados (`git status` não os lista).

## 2. Sem token

- [ ] Sem `DIGITALOCEAN_TOKEN` no ambiente nem no `.env`, a suíte passa com 8 verdes e
      9 pulados (os que chamam a API):

```bash
uv run pytest -v -rs
```

## 3. Preparação da conta DigitalOcean

- [ ] `DIGITALOCEAN_TOKEN` no `.env`: escopo customizado, só `droplet:read`.
- [ ] `DIGITALOCEAN_TOKEN_SETUP` no `.env`: `droplet:create`, `droplet:read`, `droplet:update`,
      `droplet:delete`, `tag:create` e `tag:read`.
- [ ] Laboratório criado: `web-01` (`nyc1`, 2048 MB, active), `worker-01` (`nyc1`,
      1024 MB, active) e `batch-01` (`sfo3`, 1024 MB, off); pule se já existir:

```bash
uv run setup/criar_droplets.py
```

## 4. A suíte com token

- [ ] Todos os 17 testes verdes, nenhum pulado:

```bash
uv run pytest -v
```

- [ ] Sem o laboratório, os 7 testes de `test_invocacao.py` falham com
      `Nenhum Droplet com a tag inventario-droplets. Rode o setup deste exemplo: uv run setup/criar_droplets.py`, não passam vazios.
- [ ] Droplets de fora do laboratório na conta não quebram nenhum teste.
- [ ] `test_invocacao.py`: a ferramenta imprime `Ferramenta: listar_droplets(regiao='nyc1', ...)`
      quando roda com `-s`, e cada Droplet devolvido tem só as chaves do resumo.
- [ ] `test_validacao.py::test_docstring_deixa_argumento_fora_da_regra_chegar_na_execucao` imprime
      `Ferramenta: listar_droplets(...)` com `regiao='NYC-1'` e com a mínima acima da máxima
      (`-s`) e passa com a lista vazia nos dois casos.

## 5. Fronteiras

- [ ] Não há `app.py`, agente, modelo nem chave de modelo.
- [ ] Não há cliente simulado nem resposta inventada.
- [ ] `src/droplets.py`, `src/ferramentas/` e `setup/` são idênticos aos do `09`:

```bash
diff -r src/ferramentas ../09-inventario-droplets/src/ferramentas -x __pycache__
diff src/droplets.py ../09-inventario-droplets/src/droplets.py
diff -r setup ../09-inventario-droplets/setup -x __pycache__
```

## 6. Depois da gravação

- [ ] Apagar os Droplets de teste (só os que têm a tag `inventario-droplets`):

```bash
uv run setup/destruir_droplets.py
```
