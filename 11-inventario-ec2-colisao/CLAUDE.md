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
  docstrings**. Nomes, assinaturas, `Estado`, descrições dos argumentos e corpo são idênticos.
  O `diff` entre os dois arquivos é a própria lição: não altere um sem conferir o outro.
- As duas ferramentas têm o mesmo `input_schema`. Só a `description` muda entre as versões.
- A versão ambígua foi calibrada para colidir: "status" aparece só na `verificar_status`, e a
  `listar_instancias` não cita o que devolve. Se mexer nas descrições, rode de novo o
  PLANO_TESTE.md para confirmar que a colisão continua acontecendo.
- O `app.py` sai importando `ambiguas`, o ponto de partida da demo.
- O system prompt é neutro: não cita nenhuma ferramenta. A escolha tem que depender só das
  descrições.
- A execução vive em `src/ec2.py`. `consultar_instancias` é idêntica à do `09`;
  `consultar_status` segue o mesmo padrão, com `IncludeAllInstances=True` para incluir as paradas.

## Fronteiras curriculares

- Não junte as duas ferramentas numa só nem adicione parâmetro discriminante.
- Não adicione script de avaliação, contagem de acertos ou loop de repetição: a instabilidade se
  mostra rodando o mesmo comando algumas vezes. Avaliação da escolha é assunto posterior.
- Não use `bind_tools` nem abra `tool_calls`: o diagnóstico é o log `Ferramenta: ...`.
- Não adicione contrato de retorno (`ok`/`vazio`/`erro`), `try/except`, `Stubber` nem testes:
  tratamento de erro e AWS simulada são assunto posterior.
- O retorno é o JSON completo da API, sem recorte de campos nem de instâncias.
- A resposta de `describe_instance_status` não traz a tag `Name`. Não a enriqueça: para perguntas
  que citam a instância pelo nome, o modelo combina as duas ferramentas, e isso é composição, não
  colisão.
- Os scripts de `setup/` são preparação de cenário, com a mesma tag `Projeto=inventario-ec2` do
  `09`. As ferramentas continuam só de leitura.
- Não adicione retry, cache, paginação, middleware nem `strict`.

## Ambiente e pacotes

- Use somente `uv`; nunca `pip`, Poetry, Conda ou ativação manual de virtualenv.
- Dependências devem ser alteradas com `uv add` ou `uv remove` para preservar o lockfile.
- Não use `temperature`, `top_p` ou `top_k`.

## Credenciais

`ANTHROPIC_API_KEY` e credenciais AWS nunca entram no repositório. `.env.example` contém
somente placeholders e `.env` permanece ignorado. Não grave account id nem nome de perfil
real em nenhum arquivo versionado.
