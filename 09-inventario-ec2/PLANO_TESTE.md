# Plano de teste — inventário EC2

Roteiro manual para validar o exemplo antes da gravação. Rode tudo de dentro de
`09-inventario-ec2`.

## 1. Instalação e estrutura

- [ ] `uv sync --locked` conclui sem alterar `uv.lock`.
- [ ] `uv run python -c "import src.inspecionar"` conclui (o `src.app` exige a chave no `.env`).
- [ ] Os comandos instalados se chamam `inventario-ec2` e `inspecionar`.
- [ ] `.env`, `.venv` e caches estão ignorados (`git status` não os lista).

## 2. Preparação da conta AWS

O exemplo só lê. Criar, parar e encerrar instâncias é preparação, feita pelos scripts de
`setup/` com o boto3.

- [ ] Perfil ou variáveis AWS configurados no `.env` (`AWS_PROFILE`, `AWS_REGION`).
- [ ] A credencial do exemplo tem `ec2:DescribeInstances`.
- [ ] A credencial usada no setup também tem `ec2:RunInstances`, `ec2:CreateTags`,
      `ec2:StopInstances`, `ec2:TerminateInstances` e `ssm:GetParameter`.
- [ ] `us-east-1` e `us-east-2` têm VPC padrão (o script cria as instâncias nelas).
- [ ] `AWS_REGION=us-east-1` no `.env`: é a região usada quando o modelo não informa uma.
- [ ] O script cria, em `us-east-1`, `web-01` rodando e `worker-01` e `batch-01` paradas, e, em
      `us-east-2`, `web-02` rodando e `batch-02` parada. Todas com a tag
      `Projeto=inventario-ec2`, e termina listando id, estado e nome:

```bash
uv run setup/criar_instancias.py
```

## 3. O que o modelo recebe

- [ ] `uv run inspecionar` mostra as quatro formas, e `uv run inspecionar N` mostra uma só.
- [ ] Forma 1: o bloco `Args:` aparece dentro de `description`; nenhum argumento tem
      `description` no `input_schema`.
- [ ] Forma 2: `description` só com a frase da ferramenta; cada argumento com a sua `description`;
      sem `pattern`.
- [ ] Forma 3: `regiao` com `pattern`.
- [ ] Forma 4: `input_schema` idêntico ao da forma 3.
- [ ] Nas quatro, `estado` aparece como `enum` com os seis estados.

## 4. O agente

- [ ] `.env` com `ANTHROPIC_API_KEY` válida.
- [ ] Com o import padrão (`docstring_sem_parse`):

```bash
uv run inventario-ec2 "Quais instâncias estão paradas?"
```

- [ ] O log mostra `estado='stopped'` e a resposta lista `worker-01` e `batch-01`.
- [ ] Troque o import em `src/app.py` por `modelo_pydantic` e rode a mesma pergunta: mesma resposta.
- [ ] Repita com `docstring` e `anotada`; o agente responde igual nas quatro formas.
- [ ] Com região na pergunta, o log mostra `regiao='us-east-2'` e a resposta lista só `batch-02`:

```bash
uv run inventario-ec2 "Quais instâncias estão paradas na us-east-2?"
```

- [ ] Volte o import para `docstring_sem_parse` antes da gravação.

## 5. Fronteiras

- [ ] Não há validação explícita, `try/except` de `ValidationError` nem script de valor inválido.
- [ ] Não há `bind_tools`, loop sobre `tool_calls` nem `ToolMessage`.
- [ ] Não há `Stubber` nem testes.
- [ ] A conta não aparece no esquema; a região aparece como argumento opcional.
- [ ] A ferramenta devolve o JSON completo, sem recorte.
- [ ] Nenhum recurso da conta é alterado pelo exemplo.

## 6. Depois da gravação

- [ ] Encerrar as instâncias de teste (só as que têm a tag `Projeto=inventario-ec2`):

```bash
uv run setup/destruir_instancias.py
```
