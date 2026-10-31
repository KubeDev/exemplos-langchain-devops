# 20 · Tratamento de erro e retry de ferramenta

Um agente desliga Droplets da DigitalOcean com a ferramenta `desligar_droplet`. A ferramenta é
simulada e falha de propósito, como a API real falharia: recusando a credencial
(`PermissionError`) ou sem responder a tempo (`TimeoutError`).

Sem tratamento, a exceção da ferramenta derruba o agente e o usuário fica sem resposta. O
ponto da aula é tratar o erro no agente com dois middlewares prontos do LangChain, cada um com
uma responsabilidade:

| Middleware | Decide | Onde fica na lista |
|---|---|---|
| `ToolErrorMiddleware(tratar_erro)` | o que o modelo lê quando a ferramenta falha | primeiro (externo) |
| `ToolRetryMiddleware(..., on_failure="error")` | o que vale repetir, e quantas vezes | depois (interno) |

| Arquivo | Ferramenta simulada | Middleware |
|---|---|---|
| `src/erro_ferramenta.py` | sempre `PermissionError` | só o `ToolErrorMiddleware` |
| `src/retry_ferramenta.py` | `TimeoutError` nas primeiras `FALHAS_SIMULADAS` chamadas | os dois, compostos |

Os valores de tentativas e recuo servem à demonstração, não são recomendação.

## Erro devolvido ao modelo

```bash
uv run erro-ferramenta 498123456
```

```text
Pergunta: Desligue o droplet 498123456.

[model] chama desligar_droplet({'droplet_id': '498123456'})
[tools] devolve (error): Falha de autenticação na DigitalOcean (PermissionError). Não tente de novo: peça ao usuário para verificar o token.
[model] responde: Não consegui desligar o Droplet 498123456. A DigitalOcean recusou a requisição por falha de autenticação...
```

O `tratar_erro` recebe a exceção e devolve o texto do `ToolMessage(status="error")`. Para o que
ele não reconhece, devolve `None`, e a exceção segue e derruba a execução: só vira mensagem o
erro que você escolheu mostrar.

Com a linha do `ToolErrorMiddleware` comentada, a execução termina num traceback:

```text
PermissionError: DigitalOcean API 401 Unauthorized: Unable to authenticate you
During task with name 'tools' and id '...'
```

## Nova tentativa só para o erro transitório

```bash
uv run retry-ferramenta 498123456
```

```text
Pergunta: Desligue o droplet 498123456.

[model] chama desligar_droplet({'droplet_id': '498123456'})
[api 21:26:28.104] chamada 1 à DigitalOcean
[api 21:26:29.092] chamada 2 à DigitalOcean
[tools] devolve (success): droplet 498123456: desligado
[model] responde: O Droplet 498123456 foi desligado com sucesso.
```

O modelo pediu uma chamada; a API recebeu duas. A nova tentativa acontece dentro do nó `tools`,
por isso só aparece no `print` da ferramenta. A espera entre as tentativas é
`initial_delay * backoff_factor ** n` (1s, 2s, ...), com variação de ±25% (`jitter`, ligado por
padrão).

| Troca na tela | O que acontece |
|---|---|
| `FALHAS_SIMULADAS = 5` | três chamadas (1 + `max_retries=2`), depois o `ToolErrorMiddleware` entrega a mensagem de indisponibilidade |
| `raise PermissionError(...)` no lugar do `TimeoutError` | uma chamada só: o erro está fora do `retry_on`, sobe na hora e o `ToolErrorMiddleware` o converte |
| Sem o `ToolErrorMiddleware`, com o `PermissionError` | traceback: a exceção fora do `retry_on` não passa pelo `on_failure` |
| `ToolRetryMiddleware()` com os padrões, com o `PermissionError` | três chamadas: o `retry_on` padrão repete toda exceção, e a mensagem final traz o erro cru e `Please try again.` |

## Por que repetir o shutdown é seguro

Um timeout numa escrita não diz se a escrita aconteceu. Repetir só é seguro quando a operação é
idempotente: desligar um Droplet já desligado não faz nada (está na docstring da ferramenta).
Repetir uma criação depois de um timeout pode criar o recurso duas vezes. Quem decide isso é o
desenho da ferramenta, não o modelo nem o middleware.

## Como rodar

```bash
cp .env.example .env      # preencha ANTHROPIC_API_KEY
uv sync

uv run erro-ferramenta 498123456
uv run retry-ferramenta 498123456
```

## O que este exemplo não faz

- Não chama a API da DigitalOcean: a ferramenta é local e simulada, para o erro acontecer sempre.
- Não usa o retry do SDK nem o filtro `tools=` do `ToolRetryMiddleware`.
- Não pega falha silenciosa: um retorno que parece sucesso não chega ao middleware.

## Arquivos

```text
src/erro_ferramenta.py       agente com o erro da ferramenta devolvido ao modelo
src/retry_ferramenta.py      o mesmo agente com nova tentativa interna e erro externo
.env.example                 chave da API e modelo
pyproject.toml               dependências e comandos `erro-ferramenta` e `retry-ferramenta`
```
