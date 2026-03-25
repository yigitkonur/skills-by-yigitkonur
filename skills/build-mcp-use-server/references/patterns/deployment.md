# Deployment

Ship mcp-use servers to production across npm, Docker, managed cloud, serverless, and desktop environments.

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

Fastest path to production. The CLI builds and deploys from your GitHub repo. Available via `npm run deploy` in projects scaffolded with `create-mcp-use-app`.

```bash
# Install the CLI (if you are using create-mcp-use-app this step is not needed)
npm install -g @mcp-use/cli

# Login to Manufact Cloud
npm run mcp-use login

# Deploy your server
npm run mcp-use deploy
```

If your project is a GitHub repository, `mcp-use deploy` automatically detects it and offers GitHub-based deployment:

```
GitHub repository detected:
  Repository: your-org/your-repo
  Branch:     main
  Commit:     abc1234

Deploy from GitHub repository your-org/your-repo? (y/n):
```

GitHub deployment: deploys directly from your repo, auto-detects build/start commands, uses the latest commit — no manual source upload needed.

> **CRITICAL: Commit and push first.** `mcp-use deploy` builds from the remote HEAD on GitHub. Uncommitted or unpushed local changes will NOT be deployed. Always `git add && git commit && git push` before running `mcp-use deploy`.

> **`.mcp-use/project.json`** links your local project to a cloud deployment for stable URLs across redeployments.
> - Created automatically on first deploy — do NOT pre-create it manually
> - DO NOT delete it — you'll get a new URL on next deploy
> - DO NOT commit it (`.mcp-use/` should be in `.gitignore`)
> - If the server was deleted on the cloud side (FK constraint error on deploy), delete this file and redeploy to create a fresh link

**Always use `--name`** to set a meaningful deployment name: `mcp-use deploy --name my-server`. The name controls the URL subdomain. Without it, you get random names like `empty-snowflake-cek9p`.

**After deployment** you receive:

```
✓ Deployment successful!

🌐 MCP Server URL:
   https://your-deployment/id.deploy.mcp-use.com/mcp

🔍 Inspector URL:
   https://inspector.mcp-use.com/inspect?autoConnect=https://your-deployment/id.deploy.mcp-use.com/mcp
```

Claude Desktop configuration after deploy:

```json
{
  "mcpServers": {
    "my-server": {
      "url": "https://your-deployment/id.deploy.mcp-use.com/mcp"
    }
  }
}
```

Test locally first: `mcp-use build && mcp-use start`

### Post-deploy verification

After `mcp-use deploy` succeeds, always verify:

1. `curl -s https://{url}/health | jq .status` — should return `"ok"`
2. Open the Inspector URL from the deploy output — confirm all tools appear and are callable
3. Test one tool call via Inspector or `mcp-cli call {server} {tool} '{}'`
4. Update client configs (Claude Desktop, Codex, Claude Code) with the new MCP URL

---

## 4. Google Cloud Run

Container-based, auto-scaling deployment with built-in IAM authentication. The official SDK guide uses Google Cloud Shell (includes `gcloud`, `npm`, `node`).

### Prerequisites

- Personal Google Account (work/school accounts may have restrictions)
- Google Cloud project with billing enabled (free trial available: $300 credit)

```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com
```

### Create the project

```bash
npx create-mcp-use-app mcp-on-cloudrun
cd mcp-on-cloudrun
npm install
```

### Dockerfile for Cloud Run

```dockerfile
# Use the official Node.js image
FROM node:22-slim

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (needed for build)
RUN npm ci

# Copy source code
COPY . .

# Build TypeScript and widgets (mcp-use build handles everything)
RUN npm run build

# Allow statements and log messages to immediately appear in the logs
ENV NODE_ENV=production

# Expose port (Cloud Run sets PORT env var)
EXPOSE $PORT

# Run the MCP server (mcp-use start runs the built server)
CMD ["npm", "start"]
```

Create a `.dockerignore` to exclude unnecessary files:

```bash
cat > .dockerignore << 'EOF'
node_modules
.git
.gitignore
*.md
.env
.env.local
EOF
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

# Grant Artifact Registry access
PROJECT_NUMBER=$(gcloud projects describe $GOOGLE_CLOUD_PROJECT --format="value(projectNumber)")
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

# Deploy (--no-allow-unauthenticated = require auth)
gcloud run deploy zoo-mcp-server \
  --service-account=mcp-server-sa@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com \
  --no-allow-unauthenticated \
  --region=europe-west1 \
  --source=. \
  --labels=dev-tutorial=codelab-mcp
```

Use `--no-allow-unauthenticated` to require authentication. Without it, anyone can call your MCP server.

### Client authentication (Gemini CLI example)

```bash
# Grant invoker role to your user
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
  --member=user:$(gcloud config get-value account) \
  --role='roles/run.invoker'

# Save credentials for client config
export PROJECT_NUMBER=$(gcloud projects describe $GOOGLE_CLOUD_PROJECT --format="value(projectNumber)")
export ID_TOKEN=$(gcloud auth print-identity-token)
```

Gemini CLI `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "zoo-remote": {
      "httpUrl": "https://zoo-mcp-server-$PROJECT_NUMBER.europe-west1.run.app/mcp",
      "headers": {
        "Authorization": "Bearer $ID_TOKEN"
      }
    }
  }
}
```

> Note: Gemini CLI uses the `httpUrl` key (not `url`). Standard MCP clients use `url`.

### Verify deployment

```bash
gcloud run services logs read zoo-mcp-server --region europe-west1 --limit=5
```

---

## 5. Supabase Edge Functions

Deploy as a Deno-based edge function. `MCPServer` wraps a Hono app internally; on Supabase, call `server.listen()` — it auto-detects the Deno runtime and runs in stateless mode. The recommended approach uses `npm:` specifiers in `deno.json` (avoids Zod v3/v4 conflicts from `esm.sh`).

### Prerequisites

- Supabase CLI, Supabase account, Docker (required for static file bundling), Node.js/Bun

### Setup

```bash
# Install Supabase CLI
npm install supabase --save-dev

# Create project
npx create-mcp-use-app@latest your-project-name
cd your-project-name
npm install

# Initialize Supabase
supabase init
supabase login
supabase link --project-ref YOUR_PROJECT_REF

# Start Docker before deploying (required)
open -a Docker   # macOS
docker info      # verify Docker is running

# Create edge function
supabase functions new mcp-server
```

### Quick deploy (automated)

```bash
# Interactive mode
curl -fsSL https://url.mcp-use.com/supabase | bash

# Or download and run with your project ID
curl -fsSL https://url.mcp-use.com/supabase -o deploy.sh
chmod +x deploy.sh
./deploy.sh YOUR_PROJECT_ID
# Optional: specify custom function name and bucket name
./deploy.sh YOUR_PROJECT_ID my-function-name my-bucket-name
```

The script automatically: validates CLI install, checks project init/link, patches `config.toml`, builds with correct `MCP_URL`/`MCP_SERVER_URL`, copies artifacts, sets env vars, deploys the function, uploads widgets to storage.

### Manual deploy

#### Edge function code

The recommended pattern uses `npm:` specifiers (from `deno.json`) rather than `esm.sh` URLs — this avoids Zod v3/v4 conflicts:

```typescript
// supabase/functions/mcp-server/index.ts
import { MCPServer, text } from "npm:mcp-use/server";

const server = new MCPServer({
  name: "test-app",
  version: "1.0.0",
  description: "MCP server deployed on Supabase Edge Functions",
});

server.tool(
  {
    name: "get-my-city",
    description: "Get my city",
  },
  async () => text("My city is San Francisco")
);

// server.listen() auto-detects the Deno runtime and runs in stateless mode
server.listen().catch(console.error);
```

If you need to set a custom `baseUrl` for widgets (manual deploy):

```typescript
const PROJECT_REF = Deno.env.get("SUPABASE_PROJECT_REF") || "your-project-ref";
const BASE_URL =
  Deno.env.get("MCP_URL") ||
  `https://${PROJECT_REF}.supabase.co/functions/v1/mcp-server`;

const server = new MCPServer({
  name: "test-app",
  version: "1.0.0",
  baseUrl: BASE_URL,
});
```

> `MCPServer` wraps a Hono app internally. On Supabase Edge, `server.listen()` auto-detects the Deno runtime and runs in stateless mode. For Cloudflare Workers or Deno Deploy, export the handler: `export default { fetch: server.getHandler() }`.

#### Deno configuration — handle Zod v3/v4 conflicts

Preferred (`npm:` specifiers — Deno handles peer deps better than esm.sh):

```json
{
  "imports": {
    "mcp-use/": "npm:mcp-use@latest/",
    "zod": "npm:zod@^4.2.0"
  }
}
```

If you must use `esm.sh`, pin conflicting Zod versions explicitly:

```json
{
  "imports": {
    "mcp-use/server": "https://esm.sh/mcp-use@latest/server?external=zod",
    "mcp-use/client": "https://esm.sh/mcp-use@latest/client?external=zod",
    "zod": "https://esm.sh/[email protected]",
    "zod/v3": "https://esm.sh/[email protected]",
    "zod/v4": "https://esm.sh/[email protected]",
    "zod/v4-mini": "https://esm.sh/[email protected]"
  }
}
```

#### Widget assets (for static file deployments)

```bash
# Upload widget assets to Supabase Storage
supabase storage cp -r dist/resources/widgets ss://widgets/ --experimental
```

Set these environment variables before building — they are baked in at build time:

```bash
# MCP_URL: Where widget assets (JS/CSS) are stored (Supabase Storage bucket URL)
export MCP_URL="https://YOUR_PROJECT_REF.supabase.co/storage/v1/object/public/widgets"

# MCP_SERVER_URL: Where the MCP server runs (for API calls in widgets)
export MCP_SERVER_URL="https://YOUR_PROJECT_REF.supabase.co/functions/v1/YOUR_FUNCTION_NAME"

# CSP_URLS: Supabase project base URL (for Content Security Policy — no path needed)
export CSP_URLS="https://YOUR_PROJECT_REF.supabase.co"
```

Then build, copy dist, and configure `supabase/config.toml`:

```bash
npm run build
cp -r dist supabase/functions/mcp-server/
```

```toml
# supabase/config.toml
[functions.mcp-server]
static_files = [ "./functions/mcp-server/dist/**/*.html", "./functions/mcp-server/dist/mcp-use.json" ]
```

#### Set runtime environment variables

Set **before deploying** (if set after, you must redeploy):

```bash
# MCP_URL: Whitelists the edge function domain for API calls from widgets
supabase secrets set MCP_URL="https://YOUR_PROJECT_REF.supabase.co/functions/v1/mcp-server" --project-ref YOUR_PROJECT_REF

# CSP_URLS: Whitelists the Supabase project base URL for widget assets and storage
supabase secrets set CSP_URLS="https://YOUR_PROJECT_REF.supabase.co" --project-ref YOUR_PROJECT_REF
```

#### Deploy

Docker must be running. `--use-docker` is required for static file bundling:

```bash
docker info  # verify Docker is running
supabase functions deploy mcp-server --use-docker
```

### Client connection

MCP server URL pattern: `https://YOUR_PROJECT_ID.supabase.co/functions/v1/mcp-server/mcp`

**Browser client:**

```typescript
import { BrowserMCPClient } from "mcp-use";

const client = new BrowserMCPClient({
  mcpServers: {
    supabase: {
      url: `https://YOUR_PROJECT_ID.supabase.co/functions/v1/mcp-server/mcp`,
      transport: "http",
      headers: {
        Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
        "Content-Type": "application/json",
        Accept: "application/json, text/event-stream",
      },
    },
  },
});

const session = await client.createSession("supabase");
await session.initialize();
const response = await session.connector.callTool("greet", { name: "World" });
```

**Node.js client:**

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    supabase: {
      url: `https://YOUR_PROJECT_ID.supabase.co/functions/v1/mcp-server/mcp`,
      transport: "http",
      headers: {
        Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
        "Content-Type": "application/json",
        Accept: "application/json, text/event-stream",
      },
    },
  },
});

const session = await client.createSession("supabase");
await session.initialize();
const response = await session.connector.callTool("greet", { name: "World" });
```

### Troubleshooting

**`TypeError: e.custom is not a function`** — Zod v3/v4 conflict from esm.sh bundling. Fix: use `npm:` specifiers in `deno.json` (see Deno config above).

**"Initialising login role..." appears multiple times** — Normal. The Supabase CLI authenticates separately for project linking, widget file upload, and public file upload.

**Deployment stuck on "Initialising login role..."** — Supabase may have temporarily banned your IP after multiple failed attempts. Check and unban at: `https://supabase.com/dashboard/project/{PROJECT_ID}/database/settings#banned-ips`.

**"Docker is required for widgets data"** — Start Docker Desktop and retry deployment.

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

Use request/response handlers for serverless deployments — no session persistence, each request independent:

```typescript
// api/mcp.ts
import { MCPServer } from "mcp-use/server";

const server = new MCPServer({
  name: "serverless-mcp",
  version: "1.0.0",
});

// Register tools...
const handler = await server.getHandler();
export default { fetch: handler };
```

**Warning:** Features requiring session state (notifications, sampling, elicitation) will not work in stateless mode.

---

## 8. Claude Desktop Configuration

```json
// stdio — local dev (absolute paths required)
{ "mcpServers": { "my-server": {
  "command": "node",
  "args": ["/absolute/path/to/dist/server.js"],
  "env": { "API_KEY": "your-key" }
}}}

// stdio — via npx (published package, no global install)
{ "mcpServers": { "my-server": {
  "command": "npx",
  "args": ["-y", "@yourorg/mcp-server-mytools@latest"],
  "env": { "API_KEY": "your-key" }
}}}

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

- **stdio:** Claude Desktop manages process lifecycle. `env` passes environment variables. **HTTP:** Start server yourself; `headers` sends custom headers.

---

## 9. Deployment Decision Matrix

| Criteria               | mcp-use Cloud | Cloud Run     | Supabase Edge | Fly.io        | Vercel/Netlify  | npm + stdio   |
|------------------------|---------------|---------------|---------------|---------------|-----------------|---------------|
| **Setup effort**       | Minimal       | Moderate      | Moderate      | Low           | Low             | Minimal       |
| **Sessions**           | ✅ Full       | ✅ With Redis | ✅ Full       | ✅ Full       | ❌ Stateless    | ✅ In-process |
| **Auto-scaling**       | ✅            | ✅            | ✅            | ✅            | ✅              | ❌            |
| **Cold starts**        | Managed       | Configurable  | ~50ms         | Configurable  | Yes             | None          |
| **Auth built-in**      | ✅            | ✅ IAM        | ✅ Anon key   | Manual        | Manual          | OS-level      |
| **Widget support**     | ✅ Native     | ✅ Manual     | ✅ With CDN   | ✅ Manual     | ❌              | ❌            |
| **Best for**           | Quick deploy  | GCP ecosystem | Deno/Supabase | Containers    | Simple stateless| Desktop only  |

**Choose:** mcp-use Cloud for fastest path • Cloud Run for GCP/IAM • Supabase Edge for Deno/edge • Fly.io for persistent containers • Vercel/Netlify for stateless • npm+stdio for desktop.

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

---

## 11. Cloudflare Workers

Deploy globally on the edge with zero cold starts.

### Worker Code

```typescript
// src/worker.ts
import { MCPServer } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "cf-worker",
  version: "1.0.0",
});

server.tool(
  { name: "geo", schema: z.object({}) },
  async (args, ctx) => {
    // Access Cloudflare properties
    const cf = (ctx.request as any).cf;
    return {
      content: [{ type: "text", text: `Hello from ${cf?.city || "Unknown"}` }]
    };
  }
);

export default {
  fetch: server.getHandler()
};
```

### wrangler.toml

```toml
name = "mcp-worker"
main = "src/worker.ts"
compatibility_date = "2024-09-23"

[vars]
API_KEY = "secret"
```

### Deploy

```bash
npm install -D wrangler
npx wrangler deploy
```

---

## 12. Deno Deploy

Native TypeScript support with no build step.

```typescript
// main.ts
import { MCPServer, text } from "npm:mcp-use/server";
import { z } from "npm:zod";

const server = new MCPServer({
  name: "deno-mcp",
  version: "1.0.0",
});

server.tool(
  { name: "greet", schema: z.object({ name: z.string() }) },
  async ({ name }) => text(`Hello, ${name}!`)
);

Deno.serve(server.getHandler());
```

### Deploy

```bash
deployctl deploy --project=my-mcp-project main.ts
```

---

## 13. CI/CD Pipelines

Automate testing and deployment with GitHub Actions.

### Release to npm

```yaml
# .github/workflows/publish.yml
name: Publish Package
on:
  release:
    types: [created]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          registry-url: 'https://registry.npmjs.org'
      - run: npm ci
      - run: npm run build
      - run: npm publish
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

### Build & Push Docker Image

```yaml
# .github/workflows/docker.yml
name: Docker Build
on:
  push:
    branches: [main]

jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository }}:latest
```

---

## 14. Advanced Secret Management

Move beyond `.env` files for production security.

### AWS Secrets Manager

Fetch secrets at runtime to avoid hardcoding.

```typescript
import {
  SecretsManagerClient,
  GetSecretValueCommand,
} from "@aws-sdk/client-secrets-manager";

async function loadSecrets() {
  const client = new SecretsManagerClient({ region: "us-east-1" });
  const response = await client.send(
    new GetSecretValueCommand({ SecretId: "prod/mcp-server" })
  );
  
  if (response.SecretString) {
    const secrets = JSON.parse(response.SecretString);
    process.env.API_KEY = secrets.API_KEY;
    process.env.DB_URL = secrets.DB_URL;
  }
}

// Call before server start
await loadSecrets();
const server = new MCPServer({ ... });
```

### Doppler / Infisical

Inject secrets via CLI wrapper.

```bash
# Dockerfile
CMD ["doppler", "run", "--", "node", "dist/server.js"]
```

---

## 15. Self-Hosted Nginx Proxy

Run standard Node.js servers behind a secure reverse proxy.

### nginx.conf

```nginx
server {
    listen 443 ssl http2;
    server_name mcp.example.com;

    ssl_certificate /etc/letsencrypt/live/mcp.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mcp.example.com/privkey.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        
        # SSE Support
        proxy_set_header Connection '';
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 24h;
        
        # Headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Critical:** `proxy_buffering off` is required for Server-Sent Events (SSE) to work correctly.

---

## 16. Monitoring & Alerts

Keep your server healthy.

### Uptime Kuma

Add a "HTTP Keyword" monitor:
- **URL:** `https://your-mcp.com/health`
- **Keyword:** `"status":"healthy"`
- **Interval:** 60s

### Prometheus Metrics

Expose a `/metrics` endpoint for scraping.

```typescript
import client from "prom-client";

const collectDefaultMetrics = client.collectDefaultMetrics;
collectDefaultMetrics();

const httpRequestDuration = new client.Histogram({
  name: "http_request_duration_seconds",
  help: "Duration of HTTP requests in seconds",
  labelNames: ["method", "route", "status_code"],
});

// Hono Middleware
server.use(async (c, next) => {
  const end = httpRequestDuration.startTimer();
  await next();
  end({ method: c.req.method, route: c.req.path, status_code: c.res.status });
});

server.get("/metrics", async (c) => {
  return c.text(await client.register.metrics());
});
```
