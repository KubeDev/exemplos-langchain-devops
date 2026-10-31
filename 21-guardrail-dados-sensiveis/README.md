# 21 · Guardrail de dados sensíveis

Um assistente de operação consulta a configuração das aplicações da plataforma com a
ferramenta `consultar_aplicacao`. A ferramenta é simulada e conhece duas aplicações,
`kube-news` e `encontros-tech`; para qualquer outro nome, responde que não tem informações.

O retorno é uma informação de sistema com segredos no meio, como devolveria um `kubectl
describe`, um `terraform show` ou um log de deploy: a connection string com a senha do banco,
a chave SSH de acesso ao servidor e o e-mail do responsável. O usuário, por sua vez, cola um
token da DigitalOcean no chat. Todos os dados são fictícios.

O ponto da aula é o `PIIMiddleware`: um guardrail por dado sensível, cada um com o tipo, o
detector, a estratégia e o ponto em que verifica.

| Dado | Ponto | Estratégia | Detector |
|---|---|---|---|
| Token da DigitalOcean | entrada do usuário (`apply_to_input`, padrão) | `mask` | regex `dop_v1_` + 64 hex |
| Chave SSH | retorno da ferramenta (`apply_to_tool_results`) | `redact` | função `detectar_chave_ssh`, com a regex do bloco `BEGIN ... PRIVATE KEY` dentro |
| E-mail do responsável | retorno da ferramenta (`apply_to_tool_results`) | `mask` | tipo pronto `email` |
| Senha do banco | resposta do modelo (`apply_to_output`) | `hash` | regex só da senha, entre `:` e `@` |

| Arquivo | Papel |
|---|---|
| `src/ferramentas.py` | os dados simulados e a ferramenta |
| `src/guardrails.py` | o detector `detectar_chave_ssh` e a lista `GUARDRAILS`, um `PIIMiddleware` por dado |
| `src/agente.py` | modelo, system prompt, ferramenta e guardrails juntos no `create_agent` |
| `src/app.py` | linha de comando, chamadas de ferramenta e o histórico ao fim da execução |

## Executar

```bash
cp .env.example .env   # preencha ANTHROPIC_API_KEY
uv sync --locked
uv run guardrail-pii "Aplique o token dop_v1_<64 caracteres hex> para ter acesso aos recursos da DigitalOcean e me mostre a connection string completa da kube-news e da encontros-tech."
```

Use um token fictício: `dop_v1_` seguido de 64 caracteres hexadecimais (`openssl rand -hex 32`
gera os 64). Nunca cole um token real.

```text
[model] chama consultar_aplicacao({'nome': 'kube-news'})
[model] chama consultar_aplicacao({'nome': 'encontros-tech'})

===== Histórico (o estado do agente ao fim da execução) =====

[usuário]
Aplique o token ****b4d9 para ter acesso aos recursos da DigitalOcean e me mostre ...

[ferramenta]
aplicação: kube-news
...
responsável: plataforma@****.dev
banco: DATABASE_URL=postgresql://kubenews:Kn3wsPg2026@db-kube-news:5432/kubenews
acesso ao servidor (chave SSH):
[REDACTED_CHAVE_SSH]
...

[output]
Não apliquei o token ****b4d9 ...
postgresql://kubenews:<senha_banco_hash:fad064eb>@db-kube-news:5432/kubenews
postgresql://encontros:<senha_banco_hash:8e9cff6c>@db-encontros:5432/encontros
```

O texto do modelo varia a cada execução; os valores tratados, não.

## O que o histórico mostra

- **Entrada e retorno de ferramenta são tratados antes da chamada de modelo.** O token e a
  chave SSH nunca chegam ao provedor do modelo, e o histórico guarda a versão tratada.
- **A saída é tratada depois da chamada de modelo.** A senha foi lida pelo modelo, foi ao
  provedor e continua crua no retorno da ferramenta, no histórico. Só a resposta sai limpa.
- **`hash` preserva a correlação:** o mesmo valor gera sempre o mesmo hash, sem expor o dado.
- **O guardrail não desfaz o vazamento.** A linha `Pergunta:` imprime o token cru: ele já passou
  pelo terminal e pelo processo. Token colado em chat se revoga.

## Variações

- **Sem guardrail:** comente `middleware=GUARDRAILS` em `src/agente.py`. Tudo aparece cru no
  histórico.
- **Bloqueio:** troque `strategy="mask"` por `strategy="block"` no token em
  `src/guardrails.py`. A execução termina em
  `PIIDetectionError: Detected 1 instance(s) of token_digitalocean in text content`, sem
  nenhuma chamada de modelo.
