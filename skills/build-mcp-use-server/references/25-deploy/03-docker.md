# Docker

*Read this when containerizing your mcp-use server for self-hosted or cloud container platforms.*

## Multi-Stage Dockerfile (Production)

```dockerfile
FROM node:22-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-slim
WORKDIR /app
ENV NODE_ENV=production
COPY package*.json ./
RUN npm ci --omit=dev && npm cache clean --force
COPY --from=builder /app/.mcp-use/build/ ./.mcp-use/build/
EXPOSE 3000
USER node
CMD ["npm", "start"]
```

Key points:
- **Multi-stage:** Build layer stays out of runtime image; only `.mcp-use/build/` and prod dependencies deployed.
- **`USER node`:** Never run as root. `node:*` images include a built-in non-root user.
- **`--omit=dev`:** Runtime layer skips dev dependencies.
- **Views included:** `.mcp-use/build/` contains generated Views; server reads them from disk at runtime.

## Signal Handling

Node in PID 1 does not forward signals to child processes. Use `tini` for proper SIGTERM handling:

```dockerfile
FROM node:22-slim
RUN apt-get update && apt-get install -y tini && rm -rf /var/lib/apt/lists/*
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["npm", "start"]
```

Or when running: `docker run --init -p 3000:3000 <image>`.

## `.dockerignore`

```
node_modules
.git
dist
*.md
.env*
.mcp-use/sessions
```

## Verification

After building:
```bash
docker build -t my-mcp-server .
docker run --rm -p 3000:3000 my-mcp-server &
curl http://localhost:3000/mcp/health
```

See `platforms/04-google-cloud-run.md` for `gcloud run deploy` with Docker.
