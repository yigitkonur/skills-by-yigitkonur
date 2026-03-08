# Deployment Patterns

## Overview

mcp-use servers can be deployed to various platforms. This reference covers deployment configurations for each supported target.

## Local Development

### CLI / Script Commands

```bash
# Create a project (recommended)
npx create-mcp-use-app my-mcp-server
cd my-mcp-server

# Development server (HMR + inspector)
npm run dev
# equivalent CLI: mcp-use dev

# Production build + run
npm run build
npm run start
# equivalent CLI: mcp-use build && mcp-use start
```

### Development Server (HTTP)

```typescript
import { MCPServer } from 'mcp-use/server'

const server = new MCPServer({
    name: 'dev-server',
    version: '1.0.0',
})

await server.listen(3000)
// → http://localhost:3000/mcp
// → http://localhost:3000/inspector
```

## Manufact Cloud (mcp-use Cloud)

### Deploy via CLI

```bash
# Login
mcp-use login

# Deploy
mcp-use deploy

# With environment variables
mcp-use deploy --env API_KEY=sk-xxx --env DB_URL=postgres://...

# With an env file
mcp-use deploy --env-file .env.production

# Optional deployment name and browser open
mcp-use deploy --name my-server --open
```

### Key Build/Deploy Artifacts

- `dist/mcp-use.json` — build manifest (`entryPoint`, widgets, build metadata)
- `.mcp-use/project.json` — local project ↔ cloud deployment link (created by `deploy`)
- `.mcp-use/sessions.json` — development sessions persistence

## Supabase Edge Functions

### Setup

```bash
supabase init
supabase login
supabase link --project-ref YOUR_PROJECT_REF
```

### Edge Function Pattern

```typescript
// supabase/functions/mcp-server/index.ts
import { MCPServer, text } from 'https://esm.sh/mcp-use@latest/server'

const PROJECT_REF = Deno.env.get('SUPABASE_PROJECT_REF') || 'your-project-ref'
const BASE_URL =
    Deno.env.get('MCP_URL') ||
    `https://${PROJECT_REF}.supabase.co/functions/v1/mcp-server`

const server = new MCPServer({
    name: 'supabase-mcp-server',
    version: '1.0.0',
    baseUrl: BASE_URL,
})

server.tool({
    name: 'hello',
    description: 'Simple example tool',
}, async () => text('hello from supabase'))

await server.listen()
```

### Deploy

```bash
# Build app and copy artifacts as described in docs
npm run build
cp -r dist supabase/functions/mcp-server/

# Set env vars used for CSP/widget assets
supabase secrets set MCP_URL="https://YOUR_PROJECT_REF.supabase.co/functions/v1/mcp-server" --project-ref YOUR_PROJECT_REF
supabase secrets set CSP_URLS="https://YOUR_PROJECT_REF.supabase.co" --project-ref YOUR_PROJECT_REF

# Deploy with Docker (required for static files bundling)
supabase functions deploy mcp-server --use-docker
```

## Google Cloud Run

### Dockerfile

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

### Server Code

```typescript
import { MCPServer, text } from 'mcp-use/server'
import { z } from 'zod'

const server = new MCPServer({
    name: 'cloud-run-mcp',
    version: '1.0.0',
})

server.tool({
    name: 'hello',
    schema: z.object({ name: z.string() }),
}, async ({ name }) => text(`Hello, ${name}!`))

await server.listen(parseInt(process.env.PORT || '3000', 10))
```

### Deploy

```bash
gcloud run deploy zoo-mcp-server \
  --service-account=mcp-server-sa@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com \
  --no-allow-unauthenticated \
  --region=europe-west1 \
  --source=.
```

## Docker (Self-Hosted)

### Dockerfile

```dockerfile
FROM node:22-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-slim
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
ENV NODE_ENV=production
EXPOSE 3000
CMD ["npm", "start"]
```

## Environment Variables

mcp-use server and CLI commonly use these environment variables:

| Variable | Scope | Purpose | Default |
|---|---|---|---|
| `PORT` | Server / CLI | HTTP listen port | `3000` |
| `HOST` | Server | Host binding | `localhost` |
| `MCP_URL` | Server | Public base URL (widget/assets URL generation) | `http://{HOST}:{PORT}` |
| `NODE_ENV` | Server / CLI | Environment mode (`production` disables dev-only features) | unset |
| `DEBUG` | Server | Verbose logging control | unset |
| `CSP_URLS` | Server | Extra CSP resource domains (comma-separated) | unset |
| `MCP_SERVER_URL` | CLI build | Build-time server URL injection for static widget deployments | unset |
| `MCP_WEB_URL` | CLI cloud | Cloud frontend URL for auth/device flow | `https://manufact.com` |
| `MCP_API_URL` | CLI cloud | Cloud API base URL | `https://cloud.manufact.com/api/v1` |

## Connecting Clients to Deployed Servers

### mcp-use Python Client

```python
config = {
    "mcpServers": {
        "remote": {
            "url": "https://your-server.example.com/mcp",
            "headers": {"Authorization": "Bearer your-token"}
        }
    }
}

client = MCPClient(config=config)
agent = MCPAgent(llm=llm, client=client)
result = await agent.run("Query the remote server")
```

### Claude Desktop / Cursor

```json
{
    "mcpServers": {
        "remote-server": {
            "url": "https://your-server.example.com/mcp",
            "headers": {
                "Authorization": "Bearer your-token"
            }
        }
    }
}
```
