# Contexto deste exemplo

Leia o `README.md` e o `CLAUDE.md` da raiz do repositório antes de alterar o projeto.

Este é o exemplo da Aula 07 de Memória e RAG: estratégias de chunking e sobreposição para documentos
operacionais, seguindo as famílias da página de text splitters do LangChain.

- O público tem pouco Python. Cada arquivo é lido em aula de cima a baixo e não importa nada de
  outro arquivo do projeto: `gerar_chunks.py` (recursivo e seção, demo no RB-381), `indexar.py`
  e `buscar.py`. O recursivo, a seção e as constantes de configuração são repetidos de propósito; o
  autor aceitou a duplicação em troca de não navegar entre arquivos. Não crie módulo compartilhado
  (`config.py`, `dividir.py`). Ao mudar uma estratégia, mude em `indexar.py` e em `gerar_chunks.py`.
- Uma função por estratégia, sem classe, registry ou configuração genérica; parâmetros da demo
  como constantes no topo. O `main` de `gerar_chunks.py` chama, na ordem da aula, o recursivo
  em 1000/200, o recursivo em 2000/400 e a seção. O tamanho fixo (`CharacterTextSplitter`) saiu de
  propósito: na prática se usa o recursivo; não o traga de volta. Não acrescente argumento de
  linha de comando.
- O recursivo tem dois pontos de partida pelo tamanho da resposta, ambos com 20% de sobreposição:
  1000/200 para resposta curta, 2000/400 para resposta longa. O PDF usa 2000/400 no `indexar`.
- A sobreposição fica ligada numa execução só. A saída é uma linha de resumo por estratégia
  (chunks, menor, maior, total, repetidos), sem filtro por termo nem texto de chunk: o autor escolheu
  os números, e o corte de sentido é mostrado no arquivo e provado pela busca. Não volte à demo
  "com e sem".
- A seção não tem limite de tamanho; o comentário em `dividir_por_secao()` explica quando teria.
  A medição é o maior chunk por tipo, impresso por `indexar`.
- Log não entra na base: na aula ele é consulta a sistema por ferramenta, não chunk.
- `dividir_base()`, em `indexar.py`, aplica a estratégia de cada tipo de dado; `indexar` grava uma
  coleção só (`chunks`). Comparar dois índices com um teste de busca pertence à Aula 08.
- `gerar-chunks` roda sem chave e sem banco; `indexar` e `buscar` precisam do `.env` e do Compose.
- Use `uv`; mantenha a chave da API somente no `.env`, fora do Git.
