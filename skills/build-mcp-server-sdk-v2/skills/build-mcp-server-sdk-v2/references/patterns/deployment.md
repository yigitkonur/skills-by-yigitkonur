# Deployment (v2)

## npm package (stdio)

```json
{
  "name": "@myorg/mcp-server",
  "version": "1.0.0",
  "type": "module",
  "bin": { "mcp-server": "./dist/index.js" },
  "files": ["dist"],
  "dependencies": {
    "@modelcontextprotocol/server": "^2.0.0",
    "zod": "^4.0.0"
  }
}
```

Add shebang: `#!/usr/bin/env node` at top of `src/index.ts`.

Client config:
```json
{ "command": "npx", "args": ["-y", "@myorg/mcp-server"] }
```

## Docker

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

Note: Node.js 20+ required. Use `node:22-slim` for v2.

## Cloudflare Workers / Deno

Use `WebStandardStreamableHTTPServerTransport` directly:

```typescript
import { McpServer } from "@modelcontextprotocol/server";
import { WebStandardStreamableHTTPServerTransport } from "@modelcontextprotocol/server";

const transport = new WebStandardStreamableHTTPServerTransport({
  sessionIdGenerator: undefined,
});
const server = new McpServer({ name: "edge", version: "1.0.0" });
await server.connect(transport);

export default {
  async fetch(request: Request): Promise<Response> {
    if (request.method === "POST" && new URL(request.url).pathname === "/mcp") {
      return transport.handleRequest(request, { parsedBody: await request.json() });
    }
    return new Response("Not Found", { status: 404 });
  },
};
```

No `@modelcontextprotocol/node` needed — the web-standard transport runs natively.

## Production checklist

- [ ] Node.js 20+ (v2 requirement)
- [ ] `"type": "module"` in package.json
- [ ] All secrets in environment variables
- [ ] HTTPS for HTTP transport
- [ ] DNS rebinding protection via `createMcpExpressApp()` or `createMcpHonoApp()`
- [ ] Graceful shutdown (SIGTERM + SIGINT)
- [ ] Health check endpoint
- [ ] Logging to stderr (not stdout)
