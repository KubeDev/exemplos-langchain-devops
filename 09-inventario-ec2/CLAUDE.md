# Contexto para sessões de IA neste projeto

Leia o `README.md` para entender a demonstração. Este arquivo registra as fronteiras que
preservam a função didática do exemplo.

## Natureza do projeto

Exemplo didático `09` da série `langchain-devops-examples`. A lição é: **a mesma ferramenta
declarada de quatro formas, e o esquema que o modelo recebe de cada uma**.

O código será lido em aula e projetado numa tela. Quando simplicidade e robustez colidirem,
vence a simplicidade.

## As quatro formas são o experimento

- As quatro ficam em `src/ferramentas/`, um arquivo por forma, todas expondo
  `listar_instancias` com o mesmo nome e os mesmos argumentos.
- As formas 1 e 2 só podem diferir em `parse_docstring=True`. Não altere uma sem a outra.
- As formas 3 e 4 devem gerar o mesmo `input_schema`. Confira com `uv run inspecionar`.
- A execução vive **uma vez só**, em `src/ec2.py` (`consultar_instancias`). Os arquivos de
  `src/ferramentas/` só declaram e chamam essa função. Não devolva o corpo para dentro das
  formas: uma função, quatro declarações, é a própria lição.
- A regra de duplicar código do `CLAUDE.md` da raiz vale **entre exemplos**, não dentro deste.
- O arquivo da forma 4 se chama `modelo_pydantic.py`, não `pydantic.py`, para não sombrear
  o pacote `pydantic`.

## Fronteiras curriculares

- Não adicione validação explícita, `try/except` de `ValidationError` nem script de valores
  inválidos. Validação na chamada é assunto do exemplo de testes.
- Não use `bind_tools` nem abra `tool_calls`/`ToolMessage`: o ciclo manual é o exemplo seguinte.
- Não use `Stubber` nem testes: a AWS simulada é assunto posterior.
- A região **entra** no esquema, de propósito: aqui ela é filtro escolhido pelo modelo. Torná-la
  parâmetro determinístico da aplicação é assunto posterior. Sem região, vale a padrão do boto3.
- A conta não entra no esquema; vem da credencial.
- O retorno é o JSON completo do `describe_instances`, sem recorte de campos nem de
  instâncias. Recortar a resposta para o que o modelo precisa é assunto posterior.
- Não ative `strict` no provider.
- Os scripts de `setup/` são preparação de cenário, não parte da lição. Eles são o único
  código que cria ou encerra recursos, e o destruir só toca em instâncias com a tag
  `Projeto=inventario-ec2`. A ferramenta continua só de leitura.
- Não adicione retry, cache, paginação, middleware ou tratamento abrangente de erro.

## Ambiente e pacotes

- Use somente `uv`; nunca `pip`, Poetry, Conda ou ativação manual de virtualenv.
- Dependências devem ser alteradas com `uv add` ou `uv remove` para preservar o lockfile.
- Não use `temperature`, `top_p` ou `top_k`.

## Credenciais

`ANTHROPIC_API_KEY` e credenciais AWS nunca entram no repositório. `.env.example` contém
somente placeholders e `.env` permanece ignorado. Não grave account id nem nome de perfil
real em nenhum arquivo versionado.
