# 11 — Duas ferramentas, uma colisão

O exemplo coloca uma segunda ferramenta ao lado da `listar_instancias` do `09`. A nova,
`verificar_status`, consulta as verificações de saúde das instâncias EC2. As duas leem a mesma
conta, recebem os mesmos argumentos e respondem sobre as mesmas instâncias. Quando as descrições
são parecidas, o modelo não tem como saber qual chamar.

O ponto da aula é este: **colisão é uma propriedade do conjunto de ferramentas, não de uma delas**.
A `listar_instancias` funcionava sozinha. Ela só fica ambígua quando entra a vizinha, e a correção
é uma descrição que diz quando usar, quando não usar e qual ferramenta usar no lugar.

## Estado × status

| Ferramenta | API | Responde |
|---|---|---|
| `listar_instancias` | `describe_instances` | **Estado**: `running`, `stopped`… e o nome de cada instância |
| `verificar_status` | `describe_instance_status` | **Status checks** de sistema e de instância, e também o estado |

Na AWS, *state* e *status* são coisas diferentes. Em português, "estado" e "status" são quase
sinônimos, e quem pergunta "qual o status da worker-01?" quase sempre quer saber se ela está
parada. A `verificar_status` ainda devolve o estado de cada instância, então os dados também se
sobrepõem.

## As duas versões do inventário

| Arquivo | Descrições |
|---|---|
| `src/ferramentas/ambiguas.py` | Parecidas: "Consulta as instâncias EC2 da conta." × "Consulta o status das instâncias EC2 da conta." |
| `src/ferramentas/contrastivas.py` | Cada uma diz quando usar, quando não usar e aponta a vizinha |

Os dois arquivos têm as mesmas ferramentas, com os mesmos nomes, argumentos e corpo. **Só as
docstrings mudam.** Confira:

```bash
diff src/ferramentas/ambiguas.py src/ferramentas/contrastivas.py
```

A execução vive em `src/ec2.py`: `consultar_instancias` (idêntica à do `09`) e
`consultar_status`.

## O agente

`src/app.py` registra as duas ferramentas com `create_agent`. A versão do inventário é escolhida
por **uma linha de import**:

```python
from src.ferramentas.ambiguas import listar_instancias, verificar_status
```

Cada ferramenta imprime o que o modelo pediu. Essa linha é o diagnóstico: a chamada pedida mostra
qual ferramenta o modelo escolheu e com quais argumentos.

```text
Ferramenta: verificar_status(estado=None, regiao=None)
Ferramenta: listar_instancias(estado=None, regiao=None)
```

Rode a mesma pergunta algumas vezes com cada versão e compare as linhas `Ferramenta:`:

```bash
uv run inventario-ec2-colisao "Qual o status da worker-01?"
```

Com `ambiguas`, a escolha varia entre as execuções. Com `contrastivas`, fica estável.

## Pré-requisitos na AWS

- Credencial com permissão para `ec2:DescribeInstances` e `ec2:DescribeInstanceStatus`.
- Região e credencial pela configuração padrão do boto3 (perfil ou variáveis de ambiente).
- As instâncias do `09`, com a mesma tag `Projeto=inventario-ec2`. Os scripts de `setup/` são os
  mesmos e servem aos dois exemplos.

```bash
uv run setup/criar_instancias.py     # us-east-1: web-01 rodando · worker-01 e batch-01 paradas
                                     # us-east-2: web-02 rodando · batch-02 parada
uv run setup/destruir_instancias.py  # encerra só as instâncias com a tag Projeto=inventario-ec2
```

Depois de criada, a `web-01` leva alguns minutos com os status checks em `initializing` até
chegar a `ok`.

## Como rodar

```bash
cp .env.example .env      # preencha ANTHROPIC_API_KEY e a configuração AWS
uv sync

uv run inventario-ec2-colisao "Qual o status da worker-01?"
```

## O que este exemplo não faz

- Não junta as duas ferramentas numa só.
- Não conta acertos nem mede a escolha do modelo em lote: isso é avaliação, outra camada.
- Não abre o ciclo de tool calling com `bind_tools`: a chamada pedida aparece no log da ferramenta.
- Não trata erro nem diferencia retorno vazio de sucesso.
- Não recorta a resposta: as ferramentas devolvem o JSON completo da API.
- Não usa `Stubber` nem testes.

## Arquivos

```text
src/app.py                        agente; o import escolhe a versão do inventário
src/ec2.py                        as consultas ao EC2, uma por ferramenta
src/ferramentas/ambiguas.py       as duas ferramentas com descrições parecidas
src/ferramentas/contrastivas.py   as mesmas, com descrições contrastivas
.env.example                      chave da API, modelo e configuração AWS
PLANO_TESTE.md                    validação manual e critérios de aceite da demo
setup/criar_instancias.py         cria as instâncias de teste
setup/destruir_instancias.py      encerra as instâncias de teste
pyproject.toml                    dependências e comando `inventario-ec2-colisao`
```
