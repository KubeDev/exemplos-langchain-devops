---
projeto: kube-news
tipo: post-mortem
commit: aab9356
---

# PM kube-news: banco recusou a conexão depois da migração para SSL obrigatório

## Resumo

Em 28/04/2026 o PostgreSQL gerenciado `pg-prod.interno` passou a exigir conexão com SSL. O kube-news foi reiniciado na janela de manutenção e não voltou: o servidor tinha `DB_SSL_REQUIRE=1`, e o código só liga o SSL quando o valor é exatamente `true`.

## Impacto

- Duração: 1 hora e 12 minutos fora do ar (02:10 às 03:22)
- Ocorreu na janela de manutenção, com tráfego baixo
- O encontros-tech, no mesmo banco, não foi afetado: ele já conectava com `sslmode=require` na `DATABASE_URL`

## Linha do tempo

| Horário | Evento |
|---|---|
| 02:00 | Início da janela: SSL passa a ser obrigatório em `pg-prod.interno` |
| 02:10 | kube-news reiniciado em `kube-news-prod-01` |
| 02:10 | Terminal: `SequelizeConnectionError: no pg_hba.conf entry for host "10.20.1.15", user "kubedevnews", database "kubedevnews", no encryption` |
| 02:10 | O processo encerra logo depois da subida |
| 02:35 | Time confirma que `env | grep DB_` mostra `DB_SSL_REQUIRE=1` |
| 03:05 | Leitura de `src/models/post.js`: a função `strToBool` só aceita o texto `true` |
| 03:20 | Variável trocada para `DB_SSL_REQUIRE=true` e processo reiniciado |
| 03:22 | Página inicial volta a listar as notícias |

## Causa raiz

A configuração do servidor usava `DB_SSL_REQUIRE=1`, convenção comum em outros sistemas. Em `src/models/post.js`, a função `strToBool` compara o texto com `'true'`, então qualquer outro valor desliga o SSL sem aviso. Enquanto o banco aceitava conexão sem criptografia, o erro ficou escondido.

## Por que demorou

A mensagem `no encryption` foi lida no começo como problema de regra de acesso do banco. A investigação só foi para o código depois de descartar a configuração do PostgreSQL.

## O que mudou depois

- O inventário de variáveis do servidor passou a registrar o formato esperado de cada uma
- O runbook `RB-kube-news-conexao-banco.md` ganhou o passo sobre o valor exato de `DB_SSL_REQUIRE`
- Mudanças de exigência no banco gerenciado passaram a incluir um teste de conexão de cada aplicação antes da janela
