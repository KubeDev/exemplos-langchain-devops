# 10 — Testando a ferramenta sem modelo

O exemplo pega a ferramenta `listar_instancias` do `09` e faz a pergunta que faltava: **como
testar uma ferramenta, se quem a chama é o modelo?**

O modelo não chama nada. Ele **pede** a chamada, e quem executa é a aplicação. No teste, o teste
ocupa o lugar da aplicação: invoca a ferramenta direto com argumentos, ou escreve à mão o pedido
que o modelo faria e recebe o `ToolMessage` que voltaria para ele. Não há modelo neste projeto,
nem chave de API.

Os testes rodam contra a conta AWS de verdade, com as instâncias criadas pelo `setup/`.

## O que fica do `09`

- `src/ec2.py` — a consulta ao EC2, idêntica.
- Duas das quatro formas de declarar a ferramenta:

| # | Arquivo | Declaração | O que importa aqui |
|---|---|---|---|
| 2 | `src/ferramentas/docstring.py` | `@tool(parse_docstring=True)` | formato da região só como texto |
| 4 | `src/ferramentas/modelo_pydantic.py` | `args_schema` com um `BaseModel` | formato da região como `pattern` |

As formas 1 e 3 ficaram no `09`: a 1 se comporta como a 2, e a 3 gera o mesmo esquema da 4.

## Os testes

```text
tests/conftest.py         carrega o .env (credencial e região da AWS)
tests/test_invocacao.py   a ferramenta invocada com argumentos e com um pedido de chamada
tests/test_esquema.py     o esquema que cada forma gera
tests/test_validacao.py   o que acontece com um argumento fora do esquema
```

O contraste do `test_validacao.py` é o ponto do exemplo. Com `regiao="Virginia"`:

- a **forma 4** recusa na hora, com `ValidationError`, antes de a função rodar;
- a **forma 2** aceita, monta `https://ec2.Virginia.amazonaws.com/` e só falha na rede, com
  `EndpointConnectionError`, depois das novas tentativas do boto3.

A regra que estava só na descrição orientou o modelo, mas não protegeu a execução. A regra que
estava no esquema faz as duas coisas.

## Pré-requisitos na AWS

- Credencial com `ec2:DescribeInstances` para os testes.
- Região e credencial pela configuração padrão do boto3 (perfil ou variáveis de ambiente).
- As instâncias de teste, as mesmas do `09` (mesma tag `Projeto=inventario-ec2`):

```bash
uv run setup/criar_instancias.py     # us-east-1: web-01 rodando · worker-01 e batch-01 paradas
                                     # us-east-2: web-02 rodando · batch-02 parada
uv run setup/destruir_instancias.py  # encerra, nas duas regiões, só as instâncias com a tag Projeto=inventario-ec2
```

## Como rodar

```bash
cp .env.example .env      # preencha a configuração AWS
uv sync

uv run pytest -v
```

## O que este exemplo não faz

- Não simula a AWS: sem `Stubber`, sem resposta ou erro inventado.
- Não trata a falha da ferramenta: o erro da AWS sai como exceção.
- Não tem agente nem modelo: a escolha da ferramenta pelo modelo não se testa com `assert`.
- Não recorta a resposta: a ferramenta devolve o JSON completo do `describe_instances`.

## Arquivos

```text
src/ec2.py                         a consulta ao EC2, igual à do 09
src/ferramentas/docstring.py       forma 2
src/ferramentas/modelo_pydantic.py forma 4
tests/                             a suíte
.env.example                       configuração AWS
PLANO_TESTE.md                     validação manual e preparação da conta AWS
setup/criar_instancias.py          cria as instâncias de teste
setup/destruir_instancias.py       encerra as instâncias de teste
pyproject.toml                     dependências; pytest como dependência de desenvolvimento
```
