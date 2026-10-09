# Contexto para sessões de IA neste projeto

Leia o `README.md` para entender a demonstração. Este arquivo registra as fronteiras que
preservam a função didática do exemplo.

## Natureza do projeto

Exemplo didático `09` da série `langchain-devops-examples`. A lição é: **a mesma ferramenta
declarada de duas formas (docstring e Pydantic), e o esquema que o modelo recebe de cada uma**.
Regra em prosa × regra no esquema.

O código será lido em aula e projetado numa tela. Quando simplicidade e robustez colidirem,
vence a simplicidade.

## As duas formas são o experimento

- As duas ficam em `src/ferramentas/`, um arquivo por forma, ambas expondo `listar_droplets`
  com o mesmo nome, os mesmos argumentos (`regiao`, `status`, `memoria_minima_mb`,
  `memoria_maxima_mb`) e as mesmas regras.
- Na forma docstring todas as regras ficam em prosa no bloco `Args:`, sem `parse_docstring`.
  Na forma Pydantic (`FiltroDroplets`) elas ficam no esquema: `pattern` `^[a-z]{3}[0-9]$` em
  `regiao`, `Literal` em `status`, `ge=512` nas memórias. Mudou uma regra numa, mude na outra.
- A regra entre campos (mínima ≤ máxima) é um `model_validator`: não aparece no JSON Schema,
  só vale na validação. Esse contraste é parte da lição; não tente levá-la ao esquema.
- Não volte a ter `parse_docstring=True` nem `Annotated`: a série reduziu as formas a duas.
- A execução vive **uma vez só**, em `src/droplets.py` (`consultar_droplets`). Os arquivos de
  `src/ferramentas/` só declaram e chamam essa função.
- O arquivo da forma Pydantic se chama `modelo_pydantic.py`, não `pydantic.py`, para não
  sombrear o pacote `pydantic`.

## Fronteiras curriculares

- Não adicione validação explícita, `try/except` de `ValidationError` nem script de valores
  inválidos na ferramenta.
- Não use `bind_tools` nem abra `tool_calls`/`ToolMessage`.
- A API não filtra por região, status nem memória: `consultar_droplets` lista e filtra na
  aplicação. Argumento fora da regra devolve `[]` sem erro na forma docstring; isso é material da
  aula de retorno, não corrija aqui.
- A tag `inventario-droplets` é recorte do laboratório (setup), não filtro da ferramenta.
- O retorno é um dict por Droplet com `id`, `nome`, `status`, `regiao`, `tamanho`, `vcpus`,
  `memoria_mb`, `disco_gb`, `ip_publico`, `tags` e `criado_em` (função `resumir`). Sem
  paginação; declarar o escopo no retorno é assunto posterior.
- Não ative `strict` no provider.
- A ferramenta é só de leitura e o token do exemplo (`DIGITALOCEAN_TOKEN`) tem só
  `droplet:read`. Escrita (`shutdown`) é assunto de um exemplo posterior.
- Os scripts de `setup/` são preparação de cenário, não parte da lição. São o único código
  que cria ou apaga recursos, usam outro token (`DIGITALOCEAN_TOKEN_SETUP`) e o destruir só
  toca em Droplets com a tag `inventario-droplets`, em todas as regiões.
- O laboratório cobre os critérios de cada filtro (um Droplet entra, outro fica de fora):
  `web-01` (`nyc1`, 2 GB, `active`), `worker-01` (`nyc1`, 1 GB, `active`) e `batch-01`
  (`sfo3`, 1 GB, `off`). Um Droplet por nome: nomes únicos são premissa de exemplos
  posteriores. O criar não recria nome existente com a tag e corrige o estado; desliga com
  `shutdown` e cai para `power_off` só se o shutdown não concluir. Mudou a tabela do
  `setup/criar_droplets.py`, atualize a tabela de critérios do README.
- Não adicione retry, cache, paginação, middleware ou tratamento abrangente de erro.

## Testes: a exceção da série

Este é o único exemplo da série com testes. A pasta `tests/` nasce em aula, criada por um agente de
codificação a partir de um prompt.

- Os testes invocam a ferramenta direto, sem modelo e sem agente.
- Integração contra a conta DigitalOcean real, com o `DIGITALOCEAN_TOKEN` só de leitura; sem mock
  nem cliente simulado. O resultado esperado vem dos Droplets com a tag `inventario-droplets`; a
  conta pode ter outros.
- `pytest` fica no grupo `dev`, adicionado com `uv add --dev`. Rode com `uv run pytest`.
- Teste que falha não justifica mudar `src/` ou `setup/`: reporte a causa.

## Ambiente e pacotes

- Use somente `uv`; nunca `pip`, Poetry, Conda ou ativação manual de virtualenv.
- Dependências devem ser alteradas com `uv add` ou `uv remove` para preservar o lockfile.
- Não use `temperature`, `top_p` ou `top_k`.

## Credenciais

`ANTHROPIC_API_KEY`, `DIGITALOCEAN_TOKEN` e `DIGITALOCEAN_TOKEN_SETUP` nunca entram no
repositório. `.env.example` contém somente placeholders e `.env` permanece ignorado. Não grave
id de conta, nome de time ou id de Droplet real em nenhum arquivo versionado.
