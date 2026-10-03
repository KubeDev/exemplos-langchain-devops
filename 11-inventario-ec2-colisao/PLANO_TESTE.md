# Plano de teste — colisão entre ferramentas

Roteiro manual para validar o exemplo antes da gravação. Rode tudo de dentro de
`11-inventario-ec2-colisao`.

## 1. Instalação e estrutura

- [ ] `uv sync --locked` conclui sem alterar `uv.lock`.
- [ ] O comando instalado se chama `inventario-ec2-colisao`.
- [ ] `.env`, `.venv` e caches estão ignorados (`git status` não os lista).
- [ ] `src/app.py` importa `ambiguas`.

## 2. Preparação da conta AWS

- [ ] `.env` com `ANTHROPIC_API_KEY`, `AWS_PROFILE` e `AWS_REGION=us-east-1`.
- [ ] A credencial tem `ec2:DescribeInstances` e `ec2:DescribeInstanceStatus`.
- [ ] Instâncias de pé (`uv run setup/criar_instancias.py`, se faltarem).
- [ ] A `web-01` rodando há pelo menos 10 minutos: os status checks saem de `initializing` e
      chegam a `ok`.

## 3. Mesmo esquema, só a descrição muda

- [ ] `diff src/ferramentas/ambiguas.py src/ferramentas/contrastivas.py` mostra só linhas de
      docstring.
- [ ] Convertidas com `convert_to_anthropic_tool`, cada ferramenta tem `name` e `input_schema`
      iguais nas duas versões e `description` diferente.

## 4. A ferramenta de status

- [ ] Invocada direto em `us-east-1`, `verificar_status` devolve as três instâncias em
      `InstanceStatuses`, cada uma com `InstanceState`.
- [ ] `worker-01` e `batch-01` aparecem com status `not-applicable`; `web-01` com `ok`.
- [ ] Com `estado="stopped"`, só as paradas.
- [ ] A resposta não traz a tag `Name`, só o `InstanceId`.

## 5. Perguntas-sonda

Leia a **primeira** linha `Ferramenta:` de cada execução como a escolha do modelo. Se uma pergunta
com uma ferramenta certa também chamar a outra, isso conta como colisão.

| # | Pergunta | Esperada |
|---|---|---|
| P1 | "Qual o status da worker-01?" | `listar_instancias` |
| P2 | "Quais instâncias estão paradas?" | `listar_instancias` |
| P3 | "Alguma instância está falhando nas verificações de status?" | `verificar_status` |

- [ ] **Ambíguas, P1, 5 execuções:** em pelo menos uma, o modelo chama `verificar_status`.
- [ ] **Contrastivas, P1 e P2, 10 execuções cada:** só `listar_instancias`.
- [ ] **P3, 5 execuções, nas duas versões:** só `verificar_status`.
- [ ] **Fecho, contrastivas:** a resposta de P3 cita os status checks das instâncias.
- [ ] Cada execução termina em até ~20 s.
- [ ] Volte o import para `ambiguas` antes da gravação.

P3 não cita instância pelo nome de propósito. Como a resposta de `describe_instance_status` não
traz a tag `Name`, uma pergunta como "a web-01 passou nas verificações?" leva o modelo a chamar
as duas ferramentas, uma para achar o id e outra para o status. Isso é composição, não colisão.

### Resultado observado (03/10/2026, `claude-sonnet-5`)

| Pergunta | Ambíguas | Contrastivas |
|---|---|---|
| P1 | 4/5 chamaram as duas, em ordem variável (2 com `verificar_status` primeiro); 1/5 só `listar_instancias` | 10/10 só `listar_instancias` |
| P2 | 5/5 só `listar_instancias(estado='stopped')` | 10/10 só `listar_instancias(estado='stopped')` |
| P3 | 5/5 só `verificar_status` | 5/5 só `verificar_status` |
| "A web-01 passou nas verificações de status?" | 5/5 as duas, ordem variável | 5/5 as duas, sempre `verificar_status` primeiro |

Tempo por execução: 5 a 9 s.

A primeira versão ambígua ("Consulta as instâncias EC2 da conta e o status de cada uma.") não
colidia: 10 de 10 execuções acertaram, porque a descrição da `listar_instancias` já cobria
"status". A colisão só apareceu quando "status" ficou só na descrição da vizinha.

## 6. Fronteiras

- [ ] Não há fusão das ferramentas, parâmetro discriminante, `bind_tools` nem loop de repetição.
- [ ] Não há `try/except`, contrato de retorno, `Stubber` nem testes.
- [ ] As ferramentas devolvem o JSON completo, sem recorte.
- [ ] Não há `temperature`.
- [ ] Nenhum recurso da conta é alterado pelo exemplo.

## 7. Depois da gravação

- [ ] Encerrar as instâncias de teste (só as que têm a tag `Projeto=inventario-ec2`):

```bash
uv run setup/destruir_instancias.py
```
