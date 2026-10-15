# Contexto deste exemplo

Leia o `README.md` e o `CLAUDE.md` da raiz do repositório antes de alterar o projeto.

Este é o exemplo da Aula 07 de Memória e RAG: estratégias de chunking e sobreposição para dados
operacionais.

- O público tem pouco Python. Cada arquivo é lido em aula de cima a baixo e não importa nada de
  outro arquivo do projeto: `runbook.py` (por tamanho e por seção, demo no RB-381), `log.py`
  (janela de tempo, demo no payments-worker), `indexar.py` e `buscar.py`. As funções de divisão e
  as constantes de configuração são repetidas de propósito; o autor aceitou a duplicação em troca
  de não navegar entre arquivos. Não crie módulo compartilhado (`config.py`, `dividir.py`). Ao
  mudar uma estratégia, mude em `indexar.py` e na demo.
- Uma função por estratégia, sem classe, registry ou configuração genérica; parâmetros da demo
  como constantes no topo. Cada execução da aula muda uma variável só.
- A seção não tem limite de tamanho; o comentário em `dividir_por_secao()` explica quando teria.
  A medição é o maior chunk por tipo, impresso por `indexar`.
- Um arquivo de log por serviço; a janela só inclui WARN e ERROR e o `if` do filtro fica visível.
  A primeira janela é alinhada ao relógio: sem isso, a janela de 15 s junta a recusa do broker e
  a falha ao publicar, e a demo de sobreposição perde o sentido.
- No log, o evento vira uma linha legível no conteúdo; serviço e horário da janela vão para o
  metadado.
- `dividir_base()`, em `indexar.py`, aplica a estratégia de cada tipo de dado; `indexar` grava uma coleção só
  (`chunks`). Comparar dois índices com um teste de busca pertence à Aula 08.
- `runbook` e `log` rodam sem chave e sem banco; `indexar` e `buscar` precisam do `.env` e do Compose.
- Use `uv`; mantenha a chave da API somente no `.env`, fora do Git.
