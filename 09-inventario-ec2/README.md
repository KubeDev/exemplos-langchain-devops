# 09 — A mesma ferramenta, quatro declarações

O exemplo troca os runbooks e o cluster por uma conta AWS. A ferramenta `listar_instancias`
consulta o inventário EC2 da conta, com filtro opcional por estado e por região, e aparece
**declarada de quatro formas diferentes**. A execução é uma função só, em `src/ec2.py`; as
quatro formas apenas a declaram e a chamam. Muda só o que o modelo recebe.

O ponto da aula é este: **o modelo não lê a sua função, lê o esquema gerado a partir dela**.
A forma de declarar decide o que entra nesse esquema.

## As quatro formas

| # | Arquivo | Declaração | O que chega ao modelo |
|---|---|---|---|
| 1 | `src/ferramentas/docstring_sem_parse.py` | `@tool` com bloco `Args:` | Tipos e `enum`; o bloco `Args:` vira prosa na descrição da ferramenta |
| 2 | `src/ferramentas/docstring.py` | `@tool(parse_docstring=True)` | Cada argumento com a sua descrição |
| 3 | `src/ferramentas/anotada.py` | `Annotated[..., Field(...)]` na assinatura | Descrição e formato da região (`pattern`) |
| 4 | `src/ferramentas/modelo_pydantic.py` | `args_schema` com um `BaseModel` | O mesmo esquema da forma 3, declarado fora da função |

As formas 1 e 2 têm o mesmo código e diferem apenas em `parse_docstring=True`. As formas 3 e
4 geram o mesmo esquema; a diferença é onde ele mora.

## Inspecionando o que o modelo recebe

`src/inspecionar.py` converte cada forma no formato que o `ChatAnthropic` envia à API, com
`convert_to_anthropic_tool`, e imprime nome, descrição e `input_schema`:

```bash
uv run inspecionar        # as quatro formas
uv run inspecionar 1      # só a forma 1
```

Nenhuma chamada à AWS ou ao modelo acontece aqui.

## O agente

`src/app.py` registra a ferramenta com `create_agent`. A forma usada é escolhida por **uma
linha de import**:

```python
from src.ferramentas.docstring_sem_parse import listar_instancias
```

Troque `docstring_sem_parse` por `docstring`, `anotada` ou `modelo_pydantic` e rode de novo.
A ferramenta imprime os argumentos que recebeu:

```text
Ferramenta: listar_instancias(estado='stopped', regiao=None)
```

## Pré-requisitos na AWS

- Credencial com permissão apenas para `ec2:DescribeInstances`.
- Região e credencial pela configuração padrão do boto3 (perfil ou variáveis de ambiente).
- Instâncias em duas regiões, com estados diferentes e a tag `Name`, para o filtro por estado
  e por região terem o que mostrar. Instância parada só cobra o volume.

Os scripts de `setup/` preparam e limpam esse cenário com o boto3, na VPC padrão de `us-east-1` e `us-east-2`.
Eles criam e encerram recursos; a ferramenta do exemplo só lê.

```bash
uv run setup/criar_instancias.py     # us-east-1: web-01 rodando · worker-01 e batch-01 paradas
                                     # us-east-2: web-02 rodando · batch-02 parada
uv run setup/destruir_instancias.py  # encerra, nas duas regiões, só as instâncias com a tag Projeto=inventario-ec2
```

## Como rodar

```bash
cp .env.example .env      # preencha ANTHROPIC_API_KEY e a configuração AWS
uv sync

uv run inspecionar
uv run inventario-ec2 "Quais instâncias estão paradas?"
```

## O que este exemplo não faz

- Não valida argumentos na chamada nem mostra o que acontece com valor inválido.
- Não abre nem instrumenta manualmente o ciclo de tool calling.
- Não testa a ferramenta com a AWS simulada.
- Não recorta a resposta: a ferramenta devolve o JSON completo do `describe_instances`.
- Não tira a região da escolha do modelo nem coloca a conta no esquema.
- Não ativa `strict` no provider.

## Arquivos

```text
src/app.py                            agente; o import escolhe a forma
src/inspecionar.py                    o que o modelo recebe de cada forma
src/ec2.py                            a consulta ao EC2, comum às quatro formas
src/ferramentas/docstring_sem_parse.py  forma 1
src/ferramentas/docstring.py            forma 2
src/ferramentas/anotada.py              forma 3
src/ferramentas/modelo_pydantic.py      forma 4
.env.example                          chave da API, modelo e configuração AWS
PLANO_TESTE.md                        validação manual e preparação da conta AWS
setup/criar_instancias.py             cria as instâncias de teste
setup/destruir_instancias.py          encerra as instâncias de teste
pyproject.toml                        dependências e comandos `inventario-ec2` e `inspecionar`
```
