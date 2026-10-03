# Contexto para sessões de IA neste projeto

Leia o `README.md` para entender a demonstração. Este arquivo registra as fronteiras que
preservam a função didática do exemplo.

## Natureza do projeto

Exemplo didático `10` da série `langchain-devops-examples`. A lição é: **a ferramenta é código e
se testa sem modelo — o teste ocupa o lugar da aplicação que executa o pedido**.

O código será lido em aula e projetado numa tela. Quando simplicidade e robustez colidirem,
vence a simplicidade. A suíte é lida, não escrita, em aula: cada teste mostra uma ideia só.

## O que veio do `09`, e não muda

- `src/ec2.py` (`consultar_instancias`) é idêntico ao do `09`. A ferramenta testada é a mesma.
- Só as formas 2 (`docstring.py`) e 4 (`modelo_pydantic.py`) ficaram. Elas são o contraste do
  exemplo: a mesma regra de região, em texto numa e como `pattern` na outra. Não adicione as
  formas 1 e 3 nem altere uma das duas para ficar igual à outra.
- Os scripts de `setup/` usam a mesma tag `Projeto=inventario-ec2` do `09`, de propósito: as
  instâncias criadas para uma aula servem à outra.

## Fronteiras curriculares

- Não há modelo nem agente: sem `app.py`, sem `create_agent`, sem `langchain-anthropic`, sem
  chave de API. A ausência é a lição.
- Os testes rodam contra a conta AWS real. Não use `Stubber`, `moto` nem resposta simulada:
  simular a AWS e a falha dela é assunto de um exemplo posterior.
- Não trate exceção na ferramenta. O erro da AWS sai como exceção, e o teste mostra isso.
- O retorno continua sendo o JSON completo do `describe_instances`, sem recorte.
- Não teste a escolha do modelo nem use modelo falso (`GenericFakeChatModel`): é avaliação de
  agente, outra camada.
- Não adicione fixture, plugin, cobertura ou configuração de pytest além do `conftest.py` que
  carrega o `.env`.

## Ambiente e pacotes

- Use somente `uv`; nunca `pip`, Poetry, Conda ou ativação manual de virtualenv.
- Dependências devem ser alteradas com `uv add` ou `uv remove`; `pytest` fica no grupo `dev`.
- Rode a suíte com `uv run pytest`, de dentro da pasta do exemplo.

## Credenciais

Credenciais AWS nunca entram no repositório. `.env.example` contém somente placeholders e `.env`
permanece ignorado. Não grave account id nem nome de perfil real em nenhum arquivo versionado.
