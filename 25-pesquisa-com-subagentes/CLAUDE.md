# Contexto deste exemplo

Leia o `README.md` e o `CLAUDE.md` da raiz do repositório antes de alterar o projeto.

Este é o exemplo da Aula 03 do capítulo de multi-agente: subagente como ferramenta, com contrato de entrada nos
argumentos e de saída tipada no `response_format`. O foco é **como se estrutura um subagente**.

- **Um arquivo por subagente, com o agente e a ferramenta que o embrulha juntos.** `ferramenta_subagente_web.py` e
  `ferramenta_subagente_docs.py` têm a mesma forma, de cima a baixo: o schema, o agente de dentro e a `@tool`. É a
  exceção à regra do arquivo autocontido da série, decidida pelo instrutor: a separação entre os agentes é o assunto
  da aula, e o import mostra a fronteira. Não junte os subagentes num arquivo nem separe agente e ferramenta.
- **O orquestrador importa só as duas ferramentas.** `agente_orquestrador.py` não importa Tavily, PGVector nem nada
  que os subagentes usam.
- **Modelos fixos no código**, não no `.env`: `claude-sonnet-5-5` no orquestrador e `claude-haiku-5-5` nos
  subagentes. A escolha aparece na aula sem justificativa; o critério é de outro módulo.
- **Subagente sem memória e sem gravar nada:** `checkpointer=False`. Sem ele, o subagente herda o checkpointer do
  orquestrador e grava a própria execução (com o material bruto) no PostgreSQL, num namespace próprio por chamada.
- **O retorno sobe como `structured_response.model_dump_json()`.** É texto numa `ToolMessage`: a garantia de formato
  vale na saída do subagente.
- **O Haiku usa a estratégia de ferramenta** para o `response_format` (o perfil dele não declara saída estruturada
  nativa; conferido em langchain 1.4.9). O schema chega ao modelo como uma ferramenta que encerra o loop. A docstring
  do schema diz para preenchê-lo uma vez só, depois de ler: sem isso, o Haiku o chamava junto com as buscas.
- **O contrato de entrada é a lição.** `subagente_docs` exige `projeto: Literal`. A regra do `18` "pergunte o projeto
  ao usuário" saiu do subagente e foi para o orquestrador, o único que fala com o usuário.
- **O bastidor fica fora do estado do orquestrador.** `bastidor.py` é um registro em memória que as ferramentas
  alimentam e o `web.py` lê. Não use o `artifact` da ferramenta: ele grava na `ToolMessage`, dentro do histórico do
  orquestrador, e derruba a prova de que o bruto não sobe.
- **Fora da aula:** O-R-D-E-M e o vocabulário de briefing do agente de codificação, middleware, retry, tratamento de
  erro do subagente (a falha volta como erro de ferramenta; só citado), entrada não confiável vinda do subagente.
- **Cópias do `18`:** `dados/`, `ingestao.py`, `templates/base.html`, `templates/ingestao.html`, `static/style.css` e
  a busca `buscar_documentos` dentro de `ferramenta_subagente_docs.py`. Ao mudar um, avalie o outro.
- **Portas próprias** para rodar ao lado do `18`: PostgreSQL `55439`, pgweb `58439`, web `8004`.
- **Pergunta da demo:** precisa nomear a tecnologia (PostgreSQL) para as duas pesquisas serem independentes. Sem o
  nome, o orquestrador consulta a documentação interna primeiro e só depois a web.
- Use `uv`. Sem `temperature`.
