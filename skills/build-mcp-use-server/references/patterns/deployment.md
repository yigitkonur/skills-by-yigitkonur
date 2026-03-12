# Deployment Patterns for MCP Servers

Ship mcp-use servers to production across npm, Docker, serverless, and desktop environments.

---

## 1. npm Distribution

Package your server as an installable npm module with a `bin` entry for CLI usage.

### package.json

```json
{
  "name": "@yourorg/mcp-server-mytools",
  "version": "1.0.0",
  "description": "MCP server for MyTools integration",
  "type": "module",
  "main": "dist/server.js",
  "bin": {
    "mcp-server-mytools": "dist/server.js"
  },
  "scripts": {
    "build": "tsc",
    "start": "node dist/server.js",
    "prepublishOnly": "npm run build"
  },
  "files": ["dist/"],
  "engines": { "node": ">=20" },
  "dependencies": {
    "mcp-use": "^0.5.0",
    "zod": "^3.23.0"
  },
  "devDependencies": {
    "typescript": "^5.5.0"
  }
}
```

Add a shebang to your entrypoint:

```typescript
#!/usr/bin/env node
// dist/server.js — entrypoint
import { MCPServer } from "mcp-use";
// ...
```

### Installing and running globally

```bash
npm install -g @yourorg/mcp-server-mytools
mcp-server-mytools  # runs via stdio by default
```

### Claude Desktop config for npm-published server

```json
{
  "mcpServers": {
    "mytools": {
      "command": "npx",
      "args": ["-y", "@yourorg/mcp-server-mytools"],
      "env": {
        "API_KEY": "your-key"
      }
    }
  }
}
```

Use `npx -y` so users do not need a global install. The package downloads and caches on first run.

---

## 2. Docker Deployment

### Dockerfile

```dockerfile
FROM node:20-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY tsconfig.json ./
COPY src/ ./src/
RUN npm run build

FROM node:20-slim
WORKDIR /app
ENV NODE_ENV=production
COPY package*.json ./
RUN npm ci --omit=dev && npm cache clean --force
COPY --from=builder /app/dist/ ./dist/
EXPOSE 3000
USER node
CMD ["node", "dist/server.js"]
```

**Key points:**
- Multi-stage build keeps the final image small — no TypeScript compiler or dev dependencies.
- Run as `node` user, never root.
- Set `NODE_ENV=production` for optimized module behavior.

### docker-compose.yml with Redis sessions

```yaml
version: "3.9"
services:
  mcp-server:
    build: .
    ports:
      - "3000:3000"
    environment:
      PORT: "3000"
      TRANSPORT: "httpStream"
      REDIS_URL: "redis://redis:6379"
      API_KEY: "${API_KEY}"
      ALLOWED_ORIGINS: "https://app.example.com"
    depends_on:
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "node", "-e", "fetch('http://localhost:3000/health').then(r => process.exit(r.ok ? 0 : 1))"]
      interval: 30s
      timeout: 5s
      retries: 3

  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

volumes:
  redis-data:
```

### .dockerignore

```
node_modules
src
.git
*.md
.env
tsconfig.json
```

---

## 3. Supabase Edge Functions

Deploy an MCP server as a Supabase Edge Function using Deno-compatible mcp-use.

```typescript
// supabase/functions/mcp-server/index.ts
import { MCPServer, text, object } from "mcp-use";

const server = new MCPServer({
  name: "supabase-mcp",
  version: "1.0.0",
});

server.tool(
  {
    name: "query-db",
    description: "Query the Supabase database",
    schema: z.object({ table: z.string() }),
  },
  async ({ table }) => {
    const { data, error } = await supabase.from(table).select("*").limit(100);
    if (error) return text(`Query failed: ${error.message}`);
    return object(data);
  }
);

export default server.handler({
  transportType: "httpStream",
});
```

Deploy with the Supabase CLI:

```bash
supabase functions deploy mcp-server
```

---

## 4. Cloud Platform Deployments

### Google Cloud Run

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/mcp-server
# Deploy
gcloud run deploy mcp-server \
  --image gcr.io/PROJECT_ID/mcp-server \
  --port 3000 \
  --allow-unauthenticated \
  --set-env-vars="TRANSPORT=httpStream,API_KEY=$API_KEY"
```

Set `--min-instances=1` if you need warm starts. MCP HTTP sessions are stateful — configure session affinity or use an external session store (Redis).

### Fly.io

```toml
# fly.toml
app = "mcp-server-mytools"

[build]
  dockerfile = "Dockerfile"

[env]
  PORT = "3000"
  TRANSPORT = "httpStream"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = false    # keep alive for session state
  auto_start_machines = true
  min_machines_running = 1

[[vm]]
  size = "shared-cpu-1x"
  memory = "256mb"
```

```bash
fly launch
fly secrets set API_KEY=your-key
fly deploy
```

### Vercel (Serverless — Stateless Mode)

Use stateless HTTP transport for serverless platforms that do not support persistent sessions.

```typescript
// api/mcp.ts (Vercel serverless function)
import { MCPServer, text } from "mcp-use";

const server = new MCPServer({
  name: "vercel-mcp",
  version: "1.0.0",
});

// Register tools...

export default server.handler({
  transportType: "httpStream",
  stateless: true,  // No session persistence
});
```

**Warning:** Stateless mode means no session persistence between requests. Each request is independent. Do not use features that require session state (notifications, sampling, elicitation) in stateless mode.

---

## 5. Claude Desktop Configuration

### Local development server (stdio)

```json
{
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["/absolute/path/to/dist/server.js"],
      "env": {
        "API_KEY": "your-key",
        "LOG_LEVEL": "debug"
      }
    }
  }
}
```

### Local development server (HTTP)

```json
{
  "mcpServers": {
    "my-server": {
      "url": "http://localhost:3000/mcp"
    }
  }
}
```

### Production server via npx

```json
{
  "mcpServers": {
    "my-server": {
      "command": "npx",
      "args": ["-y", "@yourorg/mcp-server-mytools@latest"],
      "env": {
        "API_KEY": "your-key"
      }
    }
  }
}
```

### Remote HTTP server

```json
{
  "mcpServers": {
    "my-server": {
      "url": "https://mcp.example.com/mcp",
      "headers": {
        "Authorization": "Bearer your-token"
      }
    }
  }
}
```

**Key points:**
- Use absolute paths for local `command` + `args` — relative paths are unreliable.
- For stdio transport, Claude Desktop manages the process lifecycle (start/stop).
- For HTTP transport, start the server yourself; Claude Desktop connects to the URL.
- The `env` field passes environment variables to the spawned process (stdio only).
- The `headers` field sends custom headers on HTTP connections.

---

## 6. Deployment Checklist

Run through this checklist before every production deployment.

### Configuration
- [ ] All required environment variables documented in README
- [ ] All required environment variables set in production
- [ ] Secrets stored in secret manager (not in code or config files)
- [ ] `NODE_ENV=production` set

### Reliability
- [ ] Graceful shutdown handlers registered (`SIGTERM`, `SIGINT`)
- [ ] Hard timeout on shutdown (10s) to prevent process hangs
- [ ] Resource cleanup order verified (server → pools → connections)
- [ ] Retry logic on transient external calls

### Security
- [ ] CORS configured with explicit `allowedOrigins` (no wildcards)
- [ ] DNS rebinding protection enabled for HTTP transport
- [ ] Rate limiting enabled on expensive or sensitive tools
- [ ] Input validation via Zod schemas on every tool
- [ ] No secrets or stack traces in error responses
- [ ] OAuth configured if server is publicly accessible

### Observability
- [ ] Structured JSON logging to stdout/stderr
- [ ] Health check endpoint or resource exposed
- [ ] Log level configurable via environment variable
- [ ] Error responses tested with invalid inputs

### Scaling
- [ ] Session store configured (Redis) for multi-process HTTP deployments
- [ ] Connection pooling for databases and HTTP clients
- [ ] Memory-bounded caches (TTL + max size)

### Validation
- [ ] Server tested with MCP Inspector (`npx @anthropic/inspector`)
- [ ] All tools callable and returning expected shapes
- [ ] Error paths tested (missing params, invalid input, upstream failures)
- [ ] Claude Desktop config tested with target client
