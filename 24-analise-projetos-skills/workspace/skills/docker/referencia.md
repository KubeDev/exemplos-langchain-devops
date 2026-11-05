# Referência: modelos do padrão Docker

## Dockerfile multi-stage para Node.js

```dockerfile
FROM node:22-alpine AS dependencias
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev

FROM node:22-alpine
WORKDIR /app
COPY --from=dependencias /app/node_modules ./node_modules
COPY . .
USER node
EXPOSE 3000
HEALTHCHECK CMD wget -qO- http://localhost:3000/health || exit 1
CMD ["node", "app.js"]
```

## .dockerignore

```
node_modules
npm-debug.log
.git
.gitignore
.env
Dockerfile
.dockerignore
k8s
README.md
```
