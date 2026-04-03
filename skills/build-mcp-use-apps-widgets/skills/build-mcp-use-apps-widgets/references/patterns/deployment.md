# Deployment

Ship mcp-use servers to production across npm, Docker, managed cloud, serverless, and desktop environments.

> **Current stable version:** v1.21.5 (March 2026). Zod is now a `peerDependency` — install separately: `npm install zod`.
> **Port resolution order:** `listen(port)` argument → `--port` CLI flag → `PORT` env var → `3000` (fallback).
> **Base-URL resolution order:** `baseUrl` config → `MCP_URL` env var → `http://{host}:{port}`.

---

## 1. npm Distribution

Package your server as an installable npm module with a `bin` entry for CLI usage.

```json
{
  "name": "@yourorg/mcp-server-mytools",
  "version": "1.0.0",
  "type": "module",
  "main": "dist/server.js",
  "bin": { "mcp-server-mytools": "dist/server.js" },
  "scripts": {
    "build": "tsc",
    "start": "node dist/server.js",
    "prepublishOnly": "npm run build"
  },
  "files": ["dist/"],
  "engines": { "node": "^20.19.0 || >=22.12.0" },
  "dependencies": { "mcp-use": "^1.21.0", "zod": "^4.0.0" }
}
```

Add a shebang to your entrypoint (`#!/usr/bin/env node`). Users run via `npx -y @yourorg/mcp-server-mytools` — no global install needed.

---

## 2. Docker Deployment

### Dockerfile (multi-stage)

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

Multi-stage build excludes dev deps. Run as `node` user, never root.

### docker-compose.yml with Redis sessions

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

---

## 3. mcp-use Cloud (Manufact Cloud)

Fastest path to production. The CLI builds and deploys from your GitHub repo.

```bash
npm run mcp-use login
npm run mcp-use deploy
```

Add the deploy script to `package.json` scripts (or use `npx mcp-use deploy` directly):

```json
{
  "scripts": {
    "dev": "mcp-use dev",
    "build": "mcp-use build",
    "start": "mcp-use start",
    "mcp-use": "mcp-use"
  }
}
```

| Option              | Description                       | Default        |
|---------------------|-----------------------------------|----------------|
| `--name <name>`     | Custom deployment name            | Auto-generated |
| `--port <port>`     | Server port                       | 3000           |
| `--runtime <rt>`    | `"node"` or `"python"`            | `"node"`       |
| `--env <key=val>`   | Environment variable (repeatable) | —              |
| `--env-file <path>` | Path to .env file                 | —              |
| `--open`            | Open deployment in browser        | false          |

```bash
npm run mcp-use deploy -- --name my-server --env DATABASE_URL=postgres://... --env-file .env.production --open
```

**What happens:** Detects GitHub repo → prompts to install GitHub App → builds & deploys → returns MCP endpoint + Inspector URL → creates `.mcp-use/project.json` for stable URLs.

After a successful deploy:
```
MCP Server URL:   https://<id>.deploy.mcp-use.com/mcp
Inspector URL:    https://inspector.mcp-use.com/inspect?autoConnect=...
```

Test locally first: `npm run build && npm run start`

---

## 4. Google Cloud Run

Container-based, auto-scaling deployment with built-in IAM authentication. From the official SDK guide.

### Prerequisites

```bash
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
```

### Dockerfile for Cloud Run

```dockerfile
FROM node:22-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
ENV NODE_ENV=production
EXPOSE $PORT
CMD ["npm", "start"]
```

Cloud Run sets `PORT` automatically. Your server must read it:

```typescript
const port = parseInt(process.env.PORT || "8080", 10);
await server.listen(port);
```

### Deploy with authentication

```bash
# Create dedicated service account
gcloud iam service-accounts create mcp-server-sa \
  --display-name="MCP Server Service Account"

# Grant Cloud Build access to Artifact Registry
PROJECT_NUMBER=$(gcloud projects describe $GOOGLE_CLOUD_PROJECT --format="value(projectNumber)")
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

# Deploy (--no-allow-unauthenticated = require IAM auth)
gcloud run deploy mcp-server \
  --service-account=mcp-server-sa@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com \
  --no-allow-unauthenticated \
  --region=europe-west1 \
  --source=. \
  --labels=dev-tutorial=codelab-mcp
```

### Client authentication

```bash
# Grant invoker role to your user
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
  --member=user:$(gcloud config get-value account) \
  --role='roles/run.invoker'

# Get identity token for client config
export ID_TOKEN=$(gcloud auth print-identity-token)
```

```json
{
  "mcpServers": {
    "cloud-run": {
      "httpUrl": "https://mcp-server-PROJECT_NUMBER.REGION.run.app/mcp",
      "headers": { "Authorization": "Bearer $ID_TOKEN" }
    }
  }
}
```

### Session management

Cloud Run scales to multiple replicas. Use `RedisSessionStore` for session persistence:

```typescript
import { MCPServer, RedisSessionStore } from "mcp-use/server";
import { createClient } from "redis";

const redis = createClient({ url: process.env.REDIS_URL });
await redis.connect();

const server = new MCPServer({
  name: "cloud-run-mcp",
  version: "1.0.0",
  sessionStore: new RedisSessionStore({ client: redis }),
});
```

Set `--min-instances=1` for warm starts. Verify: `gcloud run services logs read mcp-server --region us-central1 --limit=5`

---

## 5. Supabase Edge Functions

Deploy as a Deno-based edge function. The `MCPServer` wraps a Hono app internally; on Supabase, call `server.listen()` which auto-detects the edge runtime.

### Setup

```bash
npm install -D supabase        # or brew install supabase/tap/supabase
supabase init && supabase login
supabase link --project-ref YOUR_PROJECT_REF
supabase functions new mcp-server
```

### Edge function code

```typescript
// supabase/functions/mcp-server/index.ts
import { MCPServer, text } from "https://esm.sh/mcp-use@latest/server";

const PROJECT_REF = Deno.env.get("SUPABASE_PROJECT_REF") || "your-project-ref";
const BASE_URL = Deno.env.get("MCP_URL") ||
  `https://${PROJECT_REF}.supabase.co/functions/v1/mcp-server`;

const server = new MCPServer({
  name: "supabase-mcp",
  version: "1.0.0",
  baseUrl: BASE_URL,
});

server.tool({
  name: "hello",
  description: "Say hello",
  cb: async () => text("Hello from Supabase Edge!"),
});

await server.listen();
```

> `MCPServer` wraps a Hono app internally. On Supabase Edge, `server.listen()` auto-detects the Deno runtime and runs in stateless mode. For other edge platforms (Cloudflare/Deno Deploy), use `getHandler()` to get the underlying fetch handler.

### Deno configuration — handle Zod v3/v4 conflicts

```json
{
  "imports": {
    "mcp-use/": "npm:mcp-use@latest/",
    "zod": "npm:zod@^4.2.0"
  }
}
```

### Environment variables and deploy

```bash
# MCP_URL: where widget assets (JS/CSS) are stored — Supabase Storage URL
supabase secrets set MCP_URL="https://YOUR_REF.supabase.co/storage/v1/object/public/widgets" --project-ref YOUR_REF
# MCP_SERVER_URL: the MCP Edge Function URL (used for API calls from widgets)
supabase secrets set MCP_SERVER_URL="https://YOUR_REF.supabase.co/functions/v1/mcp-server" --project-ref YOUR_REF
# CSP_URLS: comma-separated origins whitelisted in Content-Security-Policy
supabase secrets set CSP_URLS="https://YOUR_REF.supabase.co" --project-ref YOUR_REF

# Upload built widget assets to Supabase Storage (required for widget JS/CSS)
supabase storage cp -r dist/resources/widgets ss://widgets/ --experimental

# Quick deploy (automated — interactive script)
curl -fsSL https://url.mcp-use.com/supabase | bash

# Or manual deploy (Docker required for static file bundling)
npm run build
cp -r dist supabase/functions/mcp-server/
supabase functions deploy mcp-server --use-docker
```

> **Tip:** Re-deploy the function after changing any secret. If the deploy hangs on "Initialising login role…", check Supabase Dashboard → Database Settings → Banned IPs.

### Client connection

```typescript
const client = new BrowserMCPClient({
  mcpServers: {
    supabase: {
      url: `https://YOUR_REF.supabase.co/functions/v1/mcp-server/mcp`,
      transport: "http",
      headers: {
        Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
        "Content-Type": "application/json",
        Accept: "application/json, text/event-stream",
      },
    },
  },
});
```

---

## 6. Fly.io

```toml
# fly.toml
app = "mcp-server-mytools"
[build]
  dockerfile = "Dockerfile"
[env]
  PORT = "3000"
[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = false   # keep alive for session state
  auto_start_machines = true
  min_machines_running = 1
[[vm]]
  size = "shared-cpu-1x"
  memory = "256mb"
```

```bash
fly launch && fly secrets set API_KEY=your-key && fly deploy
```

---

## 7. Vercel / Netlify (Serverless)

Use stateless mode — no session persistence, each request independent:

```typescript
// api/mcp.ts
import { MCPServer } from "mcp-use/server";

const server = new MCPServer({
  name: "serverless-mcp",
  version: "1.0.0",
  stateless: true,  // required for serverless — no sessions
});

// Register tools...
const handler = await server.getHandler();
export default { fetch: handler };
```

**Warning:** Features requiring session state (notifications, sampling, elicitation) will not work in stateless mode.

---

## 8. Claude Desktop Configuration

```json
// HTTP — local, remote, or mcp-use cloud
{ "mcpServers": { "my-server": {
  "url": "http://localhost:3000/mcp"
}}}

// HTTP — authenticated remote
{ "mcpServers": { "my-server": {
  "url": "https://mcp.example.com/mcp",
  "headers": { "Authorization": "Bearer your-token" }
}}}
```

- Start the HTTP server yourself (`npm run dev`, `mcp-use start`, or your deploy target), then point Claude Desktop at the `/mcp` URL. Use `headers` only when the remote endpoint requires them.

---

## 9. Deployment Decision Matrix

| Criteria               | mcp-use Cloud | Cloud Run     | Supabase Edge | Fly.io        | Vercel/Netlify  | Localhost HTTP |
|------------------------|---------------|---------------|---------------|---------------|-----------------|----------------|
| **Setup effort**       | Minimal       | Moderate      | Moderate      | Low           | Low             | Minimal        |
| **Sessions**           | ✅ Full       | ✅ With Redis | ✅ Full       | ✅ Full       | ❌ Stateless    | ✅ In-process  |
| **Auto-scaling**       | ✅            | ✅            | ✅            | ✅            | ✅              | ❌             |
| **Cold starts**        | Managed       | Configurable  | ~50ms         | Configurable  | Yes             | None           |
| **Auth built-in**      | ✅            | ✅ IAM        | ✅ Anon key   | Manual        | Manual          | Manual/local   |
| **Widget support**     | ✅ Native     | ✅ Manual     | ✅ With CDN   | ✅ Manual     | ❌              | ✅             |
| **Best for**           | Quick deploy  | GCP ecosystem | Deno/Supabase | Containers    | Simple stateless| Desktop and local testing |

**Choose:** mcp-use Cloud for fastest path • Cloud Run for GCP/IAM • Supabase Edge for Deno/edge • Fly.io for persistent containers • Vercel/Netlify for stateless • localhost HTTP for desktop and local development.

---

## 10. Pre-deploy Checklist

### Configuration
- [ ] Environment variables documented and set in production
- [ ] Secrets in secret manager (not in code)
- [ ] `NODE_ENV=production` set

### Reliability
- [ ] Graceful shutdown handlers (`SIGTERM`, `SIGINT`) with hard timeout (10s)
- [ ] Resource cleanup order: server → pools → connections

### Security
- [ ] CORS with explicit `allowedOrigins` (no wildcards)
- [ ] Rate limiting on expensive tools
- [ ] Zod validation on every tool input
- [ ] No secrets/stack traces in error responses
- [ ] Auth configured for public servers

### Observability
- [ ] Structured JSON logging to stdout
- [ ] Health check endpoint and configurable log level

### Scaling
- [ ] `RedisSessionStore` for multi-instance deployments
- [ ] `RedisStreamManager` for distributed SSE
- [ ] Connection pooling and memory-bounded caches

### Compatibility
- [ ] Zod 4 (`zod@^4.0.0`) — imports use `"mcp-use/server"`
- [ ] Deno import maps if deploying to Supabase Edge

### Validation
- [ ] Tested with MCP Inspector — all tools callable
- [ ] Error paths tested (missing params, invalid input)
- [ ] Claude Desktop config verified
