# ARQ - catalog-api: arquitetura e dependências

Revisão 1 do documento de arquitetura. Responsável: time de catálogo.

## Papel no sistema

A catalog-api expõe produtos, preços e ofertas para o site e o aplicativo. Ela só lê dados: o cadastro de produtos é feito por outro sistema e chega por carga noturna.

## Dependências

- PostgreSQL `catalogo-db`: produtos e ofertas, só leitura.
- Redis `catalogo-cache`: cache das ofertas, com expiração de 5 minutos.

Se o Redis cair, a API continua respondendo direto do banco, mais lenta. Se o banco cair, a API responde só o que estiver no cache.

## Capacidade

Roda com 4 réplicas fixas no namespace `catalogo`, sem autoscaling. Cada réplica atende cerca de 300 requisições por segundo na rota de ofertas.
