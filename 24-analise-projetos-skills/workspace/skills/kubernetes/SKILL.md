---
name: kubernetes
description: Revisa e corrige manifestos do Kubernetes (Deployment, Service) pelo padrão de publicação do time. Use quando a pergunta for sobre manifestos, deployment, pods, probes ou recursos no cluster. Não use para Dockerfile.
---

# Padrão de publicação no Kubernetes do time

Revise os manifestos em `/projeto-analisado/k8s/` contra cada item abaixo. Para cada item, diga se passa ou falha,
cite o campo do manifesto e proponha a correção.

## Checklist

1. **Tag fixa na imagem.** O `image` do container não usa `latest`.
2. **Probes.** O container declara `readinessProbe` e `livenessProbe`. Se a aplicação tem rota
   de saúde, as duas usam `httpGet` nela.
3. **Recursos.** O container declara `resources.requests` e `resources.limits` de CPU e memória.
4. **Contexto de segurança.** `securityContext` com `runAsNonRoot: true` e
   `allowPrivilegeEscalation: false`.
5. **Réplicas.** Serviço exposto para usuário roda com pelo menos 2 réplicas.
6. **Coerência com o Service.** O `targetPort` do Service bate com o `containerPort`.

## Ao corrigir

Escreva o manifesto inteiro em `/projeto-analisado/k8s/`, nunca um trecho. Depois diga o
que mudou, item por item do checklist.
