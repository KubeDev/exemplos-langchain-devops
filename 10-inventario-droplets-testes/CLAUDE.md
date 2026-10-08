# Contexto para sessões de IA neste projeto

Leia o `README.md` para entender a demonstração. Este arquivo registra as fronteiras que
preservam a função didática do exemplo.

## Natureza do projeto

Exemplo didático `10` da série `langchain-devops-examples`. A lição é: **a ferramenta é código e
se testa sem modelo; o teste ocupa o lugar da aplicação que executa o pedido**.

O código será lido em aula e projetado numa tela. Quando simplicidade e robustez colidirem,
vence a simplicidade. A suíte é lida, não escrita, em aula: cada teste mostra uma ideia só.

## O que veio do `09`, e não muda

- `src/droplets.py` (`consultar_droplets`) e `src/ferramentas/` são idênticos aos do `09`.
  A ferramenta testada é a mesma. O código é duplicado, não compartilhado.
- As duas formas (`docstring.py` e `modelo_pydantic.py`) são o contraste do exemplo: as mesmas
  regras dos filtros, em prosa numa e no `FiltroDroplets` na outra (`pattern`, `Literal`, `ge`
  e o `model_validator` da regra entre campos). Não altere uma das duas
  para ficar igual à outra.
- `setup/` é cópia idêntica do `09`: o aluno copia esta pasta e roda. Os scripts são o único
  código que cria, desliga ou apaga recursos, usam `DIGITALOCEAN_TOKEN_SETUP` e o destruir só
  toca em Droplets com a tag `inventario-droplets`. Mudou no `09`, copie de novo.

## Fronteiras curriculares

- Não há modelo nem agente: sem `app.py`, sem `create_agent`, sem `langchain-anthropic`, sem
  chave de modelo. A ausência é a lição.
- Os testes de invocação rodam contra a conta DigitalOcean real, com o token só de leitura.
  Não use cliente simulado nem resposta inventada: simular a API e a falha dela é assunto de um
  exemplo posterior.
- Os testes de invocação afirmam cada filtro sobre os Droplets do laboratório (tag
  `inventario-droplets`) e ignoram os demais: a conta pode ter outros Droplets. Sem o
  laboratório, falham com `pytest.fail` mandando rodar `uv run setup/criar_droplets.py`; nunca pulam em silêncio.
- Sem `DIGITALOCEAN_TOKEN`, os testes que chamam a API são pulados (`skipif`); os de esquema e
  validação rodam offline. Mantenha essa divisão.
- Não trate exceção na ferramenta. O erro da API sai como exceção, e o teste mostra isso.
- O retorno é o resumo do `09` (`resumir`), sem paginação.
- A resposta vazia da forma docstring com `regiao='NYC-1'` ou com a mínima
  acima da máxima é o perigo a apontar, não a corrigir:
  falha silenciosa é assunto de um exemplo posterior.
- Não teste a escolha do modelo nem use modelo falso (`GenericFakeChatModel`): é avaliação de
  agente, outra camada.
- Não adicione fixture, plugin, cobertura ou configuração de pytest além do `conftest.py` que
  carrega o `.env`.

## Ambiente e pacotes

- Use somente `uv`; nunca `pip`, Poetry, Conda ou ativação manual de virtualenv.
- Dependências devem ser alteradas com `uv add` ou `uv remove`; `pytest` fica no grupo `dev`.
- Rode a suíte com `uv run pytest`, de dentro da pasta do exemplo.

## Credenciais

`DIGITALOCEAN_TOKEN` e `DIGITALOCEAN_TOKEN_SETUP` nunca entram no repositório. `.env.example`
contém somente placeholders e
`.env` permanece ignorado. Não grave id de conta, nome de time ou id de Droplet real em nenhum
arquivo versionado.
