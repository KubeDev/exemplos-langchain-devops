# 10 · Testando a ferramenta sem modelo

O exemplo pega a ferramenta `listar_droplets` do `09` e faz a pergunta que faltava: **como
testar uma ferramenta, se quem a chama é o modelo?**

O modelo não chama nada. Ele **pede** a chamada, e quem executa é a aplicação. No teste, o teste
ocupa o lugar da aplicação: invoca a ferramenta direto com argumentos, ou escreve à mão o pedido
que o modelo faria e recebe o `ToolMessage` que voltaria para ele. Não há modelo neste projeto,
nem chave de modelo.

Os testes de invocação rodam contra a conta DigitalOcean de verdade, com os Droplets criados pelo
`setup/` deste exemplo e o token só de leitura. Cada filtro tem uma resposta esperada sobre os Droplets do laboratório
(os que têm a tag `inventario-droplets`); os outros Droplets da conta são ignorados:

| Filtro | Droplets do laboratório devolvidos |
|---|---|
| `regiao="nyc1"` | `web-01`, `worker-01` |
| `status="active"` | `web-01`, `worker-01` |
| `status="off"` | `batch-01` |
| `memoria_minima_mb=2048` | `web-01` |
| `memoria_maxima_mb=1024` | `worker-01`, `batch-01` |

Sem o laboratório, esses testes falham com a mensagem que manda rodar `uv run setup/criar_droplets.py`, em vez
de passar com uma lista vazia.

## O que fica do `09`

- `src/droplets.py`: a consulta à DigitalOcean e o `resumir`, que devolve os campos principais
  de cada Droplet, idênticos.
- As duas formas de declarar a ferramenta, idênticas:

| Arquivo | Declaração | Onde moram as regras dos filtros |
|---|---|---|
| `src/ferramentas/docstring.py` | `@tool` com bloco `Args:` | em prosa, na descrição da ferramenta |
| `src/ferramentas/modelo_pydantic.py` | `args_schema` com `FiltroDroplets` | no esquema (`pattern`, `enum`, `minimum`) e num `model_validator` |

Os filtros são `regiao`, `status`, `memoria_minima_mb` e `memoria_maxima_mb`. Na forma Pydantic, a
região tem `pattern` `^[a-z]{3}[0-9]$`, o status é um `Literal` (vira `enum`), as memórias têm
`ge=512` (vira `minimum`) e a regra "mínima até a máxima" é um `model_validator`. Essa última não
aparece no JSON Schema: o modelo não fica sabendo dela, só a validação a aplica.

## Os testes

```text
tests/conftest.py         carrega o .env (DIGITALOCEAN_TOKEN)
tests/test_invocacao.py   a ferramenta invocada com argumentos e com um pedido de chamada
tests/test_esquema.py     o esquema que cada forma gera
tests/test_validacao.py   o que acontece com um argumento fora do esquema
```

O contraste do `test_validacao.py` é o ponto do exemplo. Com `regiao="NYC-1"` (formato) e com
`memoria_minima_mb=2048, memoria_maxima_mb=1024` (regra entre campos):

- a **forma Pydantic** recusa na hora, com `ValidationError`, antes de a função rodar;
- a **forma docstring** aceita, a função roda, nenhum Droplet atende ao filtro e a ferramenta
  devolve uma lista vazia, sem erro.

A regra que estava só na descrição orientou o modelo, mas não protegeu a execução. A regra que
estava no esquema faz as duas coisas. E a resposta vazia da forma docstring parece válida:
"nenhum Droplet atende" é uma conclusão errada, não um erro.

O `test_esquema.py` mostra o que cada forma põe no esquema, e que a regra entre campos fica
fora dele mesmo na forma Pydantic.

Os testes que chamam a API precisam de `DIGITALOCEAN_TOKEN`. Sem ele, são pulados, e os de
esquema e validação rodam offline: eles não saem da máquina.

## Pré-requisitos na DigitalOcean

- O token do `09`: escopo customizado, só `droplet:read`. O passo a passo está no README do
  `09`, em "O token da DigitalOcean". Só leitura é o que torna seguro rodar a suíte na conta.
- O laboratório, com a tag `inventario-droplets`: `web-01` (`nyc1`, 2048 MB, ligado),
  `worker-01` (`nyc1`, 1024 MB, ligado) e `batch-01` (`sfo3`, 1024 MB, desligado).

Os scripts de `setup/` são os mesmos do `09`, copiados para cá: a pasta roda sozinha. Eles
**escrevem** na conta, por isso usam um segundo token, `DIGITALOCEAN_TOKEN_SETUP`, com
`droplet:create`, `droplet:read`, `droplet:update`, `droplet:delete`, `tag:create` e `tag:read`.
Os testes nunca usam esse token.

```bash
uv run setup/criar_droplets.py     # antes dos testes
uv run setup/destruir_droplets.py  # depois da aula: apaga só os Droplets com a tag inventario-droplets
```

Droplet desligado continua sendo cobrado: rode o destruir ao terminar. Se o laboratório já foi
criado pelo `09`, é o mesmo: não precisa criar de novo.

## Como rodar

```bash
cp .env.example .env      # preencha DIGITALOCEAN_TOKEN e DIGITALOCEAN_TOKEN_SETUP
uv sync

uv run pytest -v
```

## O que este exemplo não faz

- Não simula a DigitalOcean: sem cliente falso, sem resposta ou erro inventado.
- Não trata a falha da ferramenta: o erro da API sai como exceção.
- Não tem agente nem modelo: a escolha da ferramenta pelo modelo não se testa com `assert`.

## Arquivos

```text
src/droplets.py                     a consulta à DigitalOcean, igual à do 09
src/ferramentas/docstring.py        forma docstring
src/ferramentas/modelo_pydantic.py  forma Pydantic
tests/                              a suíte
.env.example                        tokens da DigitalOcean (testes e setup)
PLANO_TESTE.md                      validação manual antes da gravação
setup/criar_droplets.py             cria o laboratório
setup/destruir_droplets.py          apaga o laboratório
pyproject.toml                      dependências; pytest como dependência de desenvolvimento
```
