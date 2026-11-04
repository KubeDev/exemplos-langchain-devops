---
name: docker
description: Revisa e corrige Dockerfile e .dockerignore pelo padrão de imagem do time. Use quando a pergunta for sobre Dockerfile, imagem, build ou .dockerignore. Não use para manifestos do Kubernetes.
---

# Padrão de imagem Docker do time

Revise o Dockerfile do projeto contra cada item abaixo. Para cada item, diga se passa ou falha,
cite a linha do Dockerfile e proponha a correção.

## Checklist

1. **Tag fixa na imagem base.** Nada de `latest`. Use versão e variante explícitas, como
   `node:22-alpine`.
2. **Multi-stage.** Um estágio instala dependências e constrói; o estágio final leva só o que
   roda. Dependência de desenvolvimento não entra na imagem final.
3. **Usuário não-root.** O estágio final declara `USER` com um usuário sem privilégio. Na imagem
   `node`, o usuário `node` já existe.
4. **Instalação reproduzível.** `npm ci --omit=dev` no lugar de `npm install`, copiando
   `package*.json` antes do código para aproveitar o cache de camada.
5. **`.dockerignore` presente.** Sem ele, `COPY . .` leva `node_modules`, `.git` e `.env` para
   dentro da imagem.
6. **HEALTHCHECK.** Se a aplicação tem rota de saúde, a imagem declara `HEALTHCHECK` apontando
   para ela.

## Referência

Os modelos de Dockerfile multi-stage e de `.dockerignore` estão em `/skills/docker/referencia.md`.
Leia esse arquivo antes de escrever qualquer um dos dois.

## Ao corrigir

Escreva o arquivo inteiro em `/projeto-analisado/`, nunca um trecho. Depois diga o que
mudou, item por item do checklist.
