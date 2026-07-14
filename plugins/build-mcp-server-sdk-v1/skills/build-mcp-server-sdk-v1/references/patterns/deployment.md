# Deployment

How to deploy MCP servers to production environments.

## stdio deployment (npm package)

The simplest distribution — publish to npm so clients can invoke via `npx`:

### package.json

```json
{
  "name": "@myorg/mcp-server-example",
  "version": "1.0.0",
  "type": "module",
  "bin": {
    "mcp-server-example": "./dist/index.js"
  },
  "files": ["dist"],
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.29.0",
    "zod": "^3.25.0"
  }
}
```

### Entry point

Add shebang to `src/index.ts`:
```typescript
#!/usr/bin/env node
```

### Build and publish

```bash
npm run build
npm publish
```

### Client configuration (Claude Desktop)

```json
{
  "mcpServers": {
    "example": {
      "command": "npx",
      "args": ["-y", "@myorg/mcp-server-example"],
      "env": {
        "API_KEY": "${API_KEY}"
      }
    }
  }
}
```

## Docker deployment

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
COPY --from=builder /app/package.json .

EXPOSE 3000
ENV NODE_ENV=production

CMD ["node", "dist/index.js"]
```

### docker-compose.yml

```yaml
services:
  mcp-server:
    build: .
    ports:
      - "3000:3000"
    environment:
      - API_KEY=${API_KEY}
      - DATABASE_URL=${DATABASE_URL}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Health check endpoint

Add a health endpoint alongside the MCP endpoint:

```typescript
app.get("/health", (req, res) => {
  res.json({ status: "ok", name: "my-server", version: "1.0.0" });
});
```

## Serverless deployment (AWS Lambda)

### Lambda handler

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { APIGatewayProxyEventV2, APIGatewayProxyResultV2 } from "aws-lambda";

export async function handler(event: APIGatewayProxyEventV2): Promise<APIGatewayProxyResultV2> {
  // Stateless mode for serverless
  const transport = new StreamableHTTPServerTransport({
    sessionIdGenerator: undefined,
  });

  const server = new McpServer({ name: "lambda-server", version: "1.0.0" });
  // register tools...
  await server.connect(transport);

  // Convert Lambda event to Node.js request/response
  // (use a framework adapter like serverless-express)
}
```

Stateless mode is strongly recommended for serverless — session state across invocations requires external storage.

## Cloudflare Workers / Deno Deploy

Use the web-standard transport:

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { WebStandardStreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/webStandardStreamableHttp.js";

const transport = new WebStandardStreamableHTTPServerTransport({
  sessionIdGenerator: undefined,
});

const server = new McpServer({ name: "edge-server", version: "1.0.0" });
// register tools...
await server.connect(transport);

export default {
  async fetch(request: Request): Promise<Response> {
    if (request.method === "POST" && new URL(request.url).pathname === "/mcp") {
      return transport.handleRequest(request, {
        parsedBody: await request.json(),
      });
    }
    return new Response("Not Found", { status: 404 });
  },
};
```

## Production checklist

- [ ] All secrets in environment variables (never in code)
- [ ] HTTPS enabled (required for HTTP transport in production)
- [ ] DNS rebinding protection enabled (`createMcpExpressApp()` or `hostHeaderValidation`)
- [ ] Graceful shutdown handles SIGTERM and SIGINT
- [ ] Health check endpoint available for load balancers
- [ ] Logging goes to stderr (not stdout, which is reserved for stdio transport)
- [ ] Error messages are user-friendly (no stack traces leaked to clients)
- [ ] Rate limiting configured (at application or infrastructure level)
- [ ] Monitoring/alerting for error rates and latency
- [ ] Build step produces clean `dist/` output

## Client connection reference

For connecting clients to deployed servers:

### Stdio (npm package)

```json
{ "command": "npx", "args": ["-y", "@myorg/mcp-server"] }
```

### HTTP (remote)

```json
{ "type": "http", "url": "https://mcp.example.com/mcp" }
```

### HTTP with auth

```json
{
  "type": "http",
  "url": "https://mcp.example.com/mcp",
  "headers": { "Authorization": "Bearer ${MCP_TOKEN}" }
}
```
