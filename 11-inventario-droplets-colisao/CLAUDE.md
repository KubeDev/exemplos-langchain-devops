# Contexto para sessões de IA neste projeto

Leia o `README.md` para entender a demonstração. Este arquivo registra as fronteiras que
preservam a função didática do exemplo.

## Natureza do projeto

Exemplo didático `11` da série `langchain-devops-examples`. A lição é: **duas ferramentas com
descrições parecidas colidem, e a correção é uma descrição contrastiva**.

O código será lido em aula e projetado numa tela. Quando simplicidade e robustez colidirem,
vence a simplicidade.

## As duas versões do inventário são o experimento

- `src/ferramentas/ambiguas.py` e `src/ferramentas/contrastivas.py` diferem **só nas
  docstrings**. Nomes, assinaturas, bloco `Args:` e corpo são idênticos. O `diff` entre os dois
  arquivos é a própria lição: não altere um sem conferir o outro.
- As duas ferramentas têm o mesmo `input_schema` (`regiao`). Só a `description` muda entre as versões.
- A declaração segue a forma docstring do `09` (`@tool` sem `parse_docstring`).
- A versão ambígua foi calibrada para colidir: "situação" aparece só na `verificar_saude`, e a
  `listar_droplets` não cita o que devolve. Com descrições idênticas o modelo chamava as duas
  sempre, sem oscilar.
  Se mexer nelas, rode de novo o PLANO_TESTE.md para confirmar que a colisão continua acontecendo.
- O `app.py` sai importando `ambiguas`, o ponto de partida da demo.
- O system prompt é neutro: não cita nenhuma ferramenta. A escolha tem que depender só das
  descrições.
- `src/droplets.py` é idêntico ao do `09` (`consultar_droplets` + `resumir`). As ferramentas daqui
  recebem só `regiao` e passam `None` nos outros filtros: a lição é colisão, não esquema.
- `src/saude.py` tem `consultar_saude`: lista os Droplets do mesmo jeito, filtra pela região e busca o `load_1` de cada um no Monitoring,
  indexando a resposta pelo nome. Assim cada ferramenta responde sozinha a uma pergunta que cita
  o Droplet pelo nome, e a demo mede colisão, não composição.
- A métrica é `get_droplet_load1_metrics`: uma série por Droplet. Não troque pela de CPU (várias
  séries por modo) nem some outras métricas sem pedido.

## Fronteiras curriculares

- Não junte as duas ferramentas numa só nem adicione parâmetro discriminante.
- Não adicione script de avaliação, contagem de acertos ou loop de repetição: a instabilidade se
  mostra rodando o mesmo comando algumas vezes. Avaliação da escolha é assunto posterior.
- Não use `bind_tools` nem abra `tool_calls`: o diagnóstico é o log `Ferramenta: ...`.
- Não adicione contrato de retorno (`ok`/`vazio`/`erro`), `try/except`, cliente simulado nem
  testes: tratamento de erro e teste sem a DigitalOcean são assunto de outros exemplos.
- `listar_droplets` devolve o resumo do `09` (`resumir`); `verificar_saude` devolve a resposta
  completa do Monitoring por Droplet. Sem paginação.
- Seleção dinâmica de ferramentas (garantia por código) é assunto posterior: aqui a correção é
  só a descrição.
- O token do exemplo (`DIGITALOCEAN_TOKEN`) tem `droplet:read` e `monitoring:read`. Nada de escrita.
- Os scripts de `setup/` são idênticos aos do `09` (mesma tag `inventario-droplets`; `web-01` e
  `worker-01` ativos em `nyc1`, `batch-01` desligado em `sfo3`, sem métrica no Monitoring). São o único
  código que cria ou apaga recursos e usam `DIGITALOCEAN_TOKEN_SETUP`.
- Não adicione retry, cache, paginação, middleware nem `strict`.

## Ambiente e pacotes

- Use somente `uv`; nunca `pip`, Poetry, Conda ou ativação manual de virtualenv.
- Dependências devem ser alteradas com `uv add` ou `uv remove` para preservar o lockfile.
- Não use `temperature`, `top_p` ou `top_k`.

## Credenciais

`ANTHROPIC_API_KEY`, `DIGITALOCEAN_TOKEN` e `DIGITALOCEAN_TOKEN_SETUP` nunca entram no
repositório. `.env.example` contém somente placeholders e `.env` permanece ignorado. Não grave
id de conta, nome de time ou id de Droplet real em nenhum arquivo versionado.
