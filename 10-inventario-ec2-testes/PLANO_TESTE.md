# Plano de teste — testando a ferramenta

Roteiro manual para validar o exemplo antes da gravação. Rode tudo de dentro de
`10-inventario-ec2-testes`.

## 1. Instalação e estrutura

- [ ] `uv sync --locked` conclui sem alterar `uv.lock`.
- [ ] `pyproject.toml` não tem `langchain-anthropic` e tem `pytest` no grupo `dev`.
- [ ] `.env` só com a configuração AWS; nenhuma chave de modelo.
- [ ] `.env`, `.venv` e caches estão ignorados (`git status` não os lista).

## 2. Preparação da conta AWS

- [ ] Perfil ou variáveis AWS configurados no `.env` (`AWS_PROFILE`, `AWS_REGION=us-east-1`).
- [ ] A credencial dos testes tem `ec2:DescribeInstances`; a do setup tem também
      `ec2:RunInstances`, `ec2:CreateTags`, `ec2:StopInstances`, `ec2:TerminateInstances` e
      `ssm:GetParameter`.
- [ ] Instâncias criadas (as mesmas do `09`; pule se já existirem):

```bash
uv run setup/criar_instancias.py
```

## 3. A suíte

- [ ] Todos os testes verdes:

```bash
uv run pytest -v
```

- [ ] `test_invocacao.py`: a ferramenta imprime `Ferramenta: listar_instancias(estado='stopped', regiao=None)`
      quando roda com `-s`.
- [ ] `test_validacao.py::test_forma2_deixa_regiao_fora_do_formato_chegar_na_aws` leva alguns
      segundos (novas tentativas do boto3); os demais são imediatos.

## 4. Fronteiras

- [ ] Não há `app.py`, agente, modelo nem chave de API.
- [ ] Não há `Stubber`, `moto` nem resposta simulada.
- [ ] `src/ec2.py` é idêntico ao do `09`.

## 5. Depois da gravação

- [ ] Encerrar as instâncias de teste (só as que têm a tag `Projeto=inventario-ec2`):

```bash
uv run setup/destruir_instancias.py
```
