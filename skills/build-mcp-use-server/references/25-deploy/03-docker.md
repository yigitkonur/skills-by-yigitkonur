# Docker

Production Dockerfile patterns for self-hosted and platform-agnostic container deploys.

---

## 1. Multi-stage Dockerfile

```dockerfile
FROM node:22-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY tsconfig.json ./
COPY src/ ./src/
COPY resources/ ./resources/
RUN npm run build

FROM node:22-slim
WORKDIR /app
ENV NODE_ENV=production
COPY package*.json ./
RUN npm ci --omit=dev && npm cache clean --force
COPY --from=builder /app/dist/ ./dist/
EXPOSE 3000
USER node
CMD ["node", "dist/server.js"]
```

What this gives you:
- **Multi-stage** — build artifacts stay in the builder; runtime image carries only `dist/` and prod deps.
- **`USER node`** — never run as root. `node` is a built-in non-root user in `node:*` images.
- **`npm cache clean --force`** — drops cache directory in the runtime layer.
- **`--omit=dev`** — runtime layer skips dev dependencies.

---

## 2. `docker-compose.yml` with Redis sessions

```yaml
services:
  mcp-server:
    build: .
    ports: ["3000:3000"]
    environment:
      PORT: "3000"
      REDIS_URL: "redis://redis:6379"
      API_KEY: "${API_KEY}"
    depends_on:
      redis: { condition: service_healthy }
    healthcheck:
      test: ["CMD", "node", "-e", "fetch('http://localhost:3000/health').then(r=>process.exit(r.ok?0:1))"]
      interval: 30s
  redis:
    image: redis:7-alpine
    volumes: [redis-data:/data]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
volumes:
  redis-data:
```

The healthcheck depends on an explicit `/health` route — register it before `server.listen()` (see `02-pre-deploy-checklist.md` §3).

---

## 3. Init for signal handling

PID 1 in a container is your Node process. It does not reap zombies and does not forward signals to children by default. If your server spawns subprocesses or uses a wrapper, use `tini`:

```dockerfile
FROM node:22-slim
RUN apt-get update && apt-get install -y tini && rm -rf /var/lib/apt/lists/*
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["node", "dist/server.js"]
```

Or pass `--init` to `docker run`:

```bash
docker run --init -p 3000:3000 my-mcp-server
```

Without an init, `SIGTERM` from `docker stop` may not reach Node, and the container only dies after the 10-second kill timeout.

---

## 4. `.dockerignore`

Ship only what you need. Bloated images slow deploys and broaden attack surface:

```
node_modules
.git
.gitignore
*.md
.env
.env.local
.mcp-use/sessions/
dist/
```

(`dist/` is in `.dockerignore` because the multi-stage build regenerates it inside the builder stage. If your CI pre-builds, drop the `dist/` line and copy it directly.)

---

## 5. Anti-patterns

- **`:latest` tag in production.** Pin to an immutable tag (digest or version): `image: ghcr.io/myorg/mcp-server:1.4.2`. `:latest` floats — a redeploy can silently change the image. See `26-anti-patterns/`.
- **Running as root.** Always `USER node` (or another non-root user).
- **Single-stage build with `npm install` in the runtime image.** Ships dev deps and source.
- **No healthcheck.** Containers can be alive but dead. The orchestrator needs a probe.
- **Forgetting `EXPOSE`.** Some platforms (Cloud Run, Fly) require it; documentation, network policy, and tooling key off it.

---

## 6. Sizing

- `node:22-slim` is ~50 MB base, well under `node:22` (~150 MB).
- Distroless (`gcr.io/distroless/nodejs22-debian12`) trades shell access for a smaller, less-attackable image.
- Alpine (`node:22-alpine`) has musl libc — beware of native modules that expect glibc.

---

See `25-deploy/platforms/05-fly.md` and `platforms/03-google-cloud-run.md` for platform-specific Docker workflows.
