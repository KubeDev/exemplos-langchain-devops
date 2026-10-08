# Contexto para sessões de IA neste projeto

Leia o `README.md` antes de alterar este exemplo. Ele registra a demonstração e suas fronteiras.

## Natureza do projeto

Exemplo didático `15` da série `langchain-devops-examples`. A lição é: **a escrita entra
recortada**: o server publica uma ação nomeada e estreita (`desligar_droplet`, via `shutdown`),
menor do que o token permitiria, com parâmetro restrito, efeito declarado no retorno e registro
do que ficou de fora. O limite desse recorte é a fronteira do protocolo.

O exemplo é autocontido e parte de uma cópia do `14` (código duplicado, nada compartilhado), já
na versão com escopo: a alternância `sem_escopo` × `com_escopo` saiu e `retornar` mora em
`src/servidor.py`. Quando simplicidade e robustez colidirem, vence a simplicidade.

## Server

- Todo o server fica em `src/servidor.py`. As quatro ferramentas de leitura do `14` continuam,
  com `readOnlyHint`; `desligar_droplet` tem `destructiveHint`. Anotação é dica, não controle.
- Recorte da escrita: `DROPLETS_PERMITIDOS` (`Literal`, vira `enum` no esquema) e
  `TAG_LABORATORIO = "inventario-droplets"` (conferida na função antes da action).
- `listar_droplets` é igual à do `14`: filtro opcional por `regiao`, feito na aplicação, com
  paginação local depois do filtro. A tag não é filtro do usuário; é recorte da escrita.
- A escrita não filtra por região (laboratório: `web-01`/`worker-01` em `nyc1`, `batch-01` em
  `sfo3`). Nome duplicado na tag é proteção: recusa com os IDs, sem escolher um. Não troque por
  "o primeiro".
- Única action disparada: `{"type": "shutdown"}`. Droplet já `off` não dispara nada.
- O efeito vai no **texto** do retorno: pedido, estado anterior, action, o que não foi feito e a
  compensação (`power_on`, manual). `shutdown` é **compensável**, não reversível.
- Tokens: `listar_droplets` lê `DIGITALOCEAN_TOKEN` (`droplet:read`); `desligar_droplet` lê
  `DIGITALOCEAN_TOKEN_ESCRITA` (`droplet:read` + `droplet:update`). Não unifique os dois.
- Versão do contrato `1.1.0`: ferramenta nova é mudança compatível.
- Transporte stdio: nada de `print` no stdout dentro do server.

## Clientes

- `src/agente.py` é o mesmo do `14`. Não filtre ferramentas no cliente: o filtro aparece só como
  trecho no README (escopo do agente).

## Testes

`tests/test_servidor.py` usa o cliente em memória do FastMCP, sem modelo. Os testes de escrita
trocam `servidor.Client` por um cliente falso com `monkeypatch`. O teste real
`test_desliga_o_droplet_de_teste` exige `DIGITALOCEAN_TOKEN_ESCRITA` **e** `DROPLET_TESTE`; não
relaxe essa condição, para um `uv run pytest` nunca desligar Droplet por acaso.

## Fronteiras curriculares

- Não publique `power_off`, `power_on`, `reboot`, destruir nem ação genérica.
- Não implemente autorização por ação, aprovação humana, auditoria ou validação de conteúdo: é a
  lacuna nomeada, que fica fora deste exemplo. Não antecipe a solução.
- Não suba o server por HTTP nem faça deploy.
- Não adicione autenticação, middleware, retry, cache, memória ou streaming.

## Ambiente e credenciais

- Use somente `uv`; dependências por `uv add` e `uv remove`.
- Não use `temperature`, `top_p` ou `top_k`.
- `ANTHROPIC_API_KEY`, `DIGITALOCEAN_TOKEN` e `DIGITALOCEAN_TOKEN_ESCRITA` nunca entram em arquivo
  versionado.
