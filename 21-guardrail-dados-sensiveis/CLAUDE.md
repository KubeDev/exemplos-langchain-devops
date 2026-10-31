# Contexto deste exemplo

Leia o `README.md` e o `CLAUDE.md` da raiz do repositório antes de alterar o projeto.

Exemplo `21` da série. A lição é: **guardrail de dados sensíveis com o `PIIMiddleware`**, um
por dado, cada um com tipo, detector, estratégia e ponto de verificação (entrada, retorno de
ferramenta, resposta).

- **Quatro arquivos, um papel cada.** `ferramentas.py` (dados simulados + ferramenta),
  `guardrails.py` (a lista `GUARDRAILS`, o arquivo lido em aula), `agente.py` (composição) e
  `app.py` (encanamento). Não junte nem crie módulo utilitário.
- **A ferramenta é simulada e devolve segredos de propósito**, no meio de uma informação de
  sistema. Só `kube-news` e `encontros-tech`; outro nome devolve "Não tenho informações". Não
  troque por API real nem por MCP.
- **Todos os segredos são fictícios.** Nunca grave um token `dop_v1_` no repositório: o token
  entra pela pergunta, na hora. A chave SSH tem corpo obviamente falso.
- **Os dois jeitos de escrever detector aparecem de propósito:** regex como string (token, senha)
  e função que devolve `PIIMatch` (`detectar_chave_ssh`, com a regex dentro). Não troque a função
  por string.
- **O host do banco não tem ponto** (`db-kube-news`). Com ponto, `senha@host.dominio` casa com o
  detector pronto de e-mail e o `mask` de e-mail deixa a senha visível.
- **A cobertura dos pontos é deliberada:** token na entrada (`mask`), chave e e-mail no retorno
  da ferramenta (`redact`, `mask`), senha só na resposta (`hash`). A senha fica crua no retorno
  da ferramenta de propósito: é o que mostra que filtrar a saída não protege o provedor.
- **A linha "copie os valores exatamente" do system prompt é necessária.** Sem ela, o modelo às
  vezes omite a senha sozinho, e a demo da saída deixa de ser repetível.
- **O `app.py` lê o estado (`stream_mode="values"`), não as atualizações dos nós.** A
  atualização do nó do modelo traz a resposta antes do filtro de saída, com a senha crua. A linha
  `Pergunta:` imprime o token cru de propósito.
- **Variações trocadas na tela pelo instrutor:** comentar `middleware=GUARDRAILS`; `mask` =>
  `block` no token. Não crie flag nem modo.
- **Fora daqui:** tratamento de erro de ferramenta, checkpointer, middleware próprio, autorização
  por usuário, human-in-the-loop.
- **Provider:** chat Anthropic (`MODELO`, padrão `claude-haiku-5-5`). Sem `temperature`.
- Use `uv`.
