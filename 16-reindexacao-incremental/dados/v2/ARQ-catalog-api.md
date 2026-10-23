# ARQ - catalog-api: arquitetura e dependências

Revisão 2 do documento de arquitetura. Responsável: time de catálogo.

## Papel no sistema

A catalog-api expõe produtos, preços e ofertas para o site e o aplicativo. Ela só lê dados: o cadastro de produtos é feito por outro sistema e chega por carga noturna.

## Dependências

- PostgreSQL `catalogo-db`: produtos e ofertas, só leitura.
- Valkey `catalogo-cache`: cache das ofertas, com expiração de 5 minutos. Substituiu o Redis na migração do trimestre.
- pricing-api: preço promocional em tempo real, consultado a cada requisição de oferta.

Se o Valkey cair, a API continua respondendo direto do banco, mais lenta. Se a pricing-api cair, a API devolve o preço de tabela e marca a oferta como sem promoção.

## Capacidade

Roda no namespace `catalogo` com HPA entre 4 e 12 réplicas, escalando pela CPU. Cada réplica atende cerca de 300 requisições por segundo na rota de ofertas.
