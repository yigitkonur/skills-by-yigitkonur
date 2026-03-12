# MCP Server Project Templates

Starter project structures for building MCP servers with mcp-use.

## Template 1: Minimal CLI Server
```
my-mcp-server/
├── package.json
├── tsconfig.json
└── src/server.ts
```

### `package.json`
```json
{
  "name": "my-mcp-server",
  "version": "1.0.0",
  "type": "module",
  "bin": { "my-mcp-server": "./dist/server.js" },
  "scripts": { "build": "tsc", "start": "node dist/server.js", "dev": "tsx src/server.ts" },
  "dependencies": { "mcp-use": "^1.0.0", "zod": "^3.23.0" },
  "devDependencies": { "tsx": "^4.0.0", "typescript": "^5.5.0" }
}
```

### `tsconfig.json`
```json
{
  "compilerOptions": {
    "target": "ES2022", "module": "Node16", "moduleResolution": "Node16",
    "outDir": "dist", "rootDir": "src", "strict": true,
    "esModuleInterop": true, "skipLibCheck": true, "declaration": true
  },
  "include": ["src"]
}
```

### `src/server.ts`
```typescript
import { MCPServer, text } from "mcp-use/server";
import z from "zod";

const server = new MCPServer({
  name: "my-mcp-server", version: "1.0.0", description: "A minimal MCP server",
});

server.tool(
  { name: "greet", description: "Generate a greeting",
    schema: z.object({ name: z.string().describe("Name to greet") }) },
  async ({ name }) => text(`Hello, ${name}! Welcome to MCP.`)
);

await server.listen();
```

**Run:** `npm install && npm run build && echo '{}' | npx my-mcp-server`

---

## Template 2: Production HTTP Server

```
production-mcp-server/
├── package.json
├── tsconfig.json
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── src/
    ├── server.ts
    ├── config.ts
    └── tools/
        ├── index.ts
        └── search.ts
```

### `src/config.ts`
```typescript
import "dotenv/config";
export const config = {
  name: "production-server",
  version: process.env.npm_package_version || "1.0.0",
  port: parseInt(process.env.PORT || "3000", 10),
  redisUrl: process.env.REDIS_URL || "redis://localhost:6379",
};
```

### `src/tools/search.ts` — modular tool registration pattern
```typescript
import { object } from "mcp-use/server";
import type { MCPServer } from "mcp-use/server";
import z from "zod";

export function registerSearchTools(server: MCPServer) {
  server.tool(
    { name: "search", description: "Search indexed documents",
      schema: z.object({ query: z.string().min(1), limit: z.number().default(10) }) },
    async ({ query, limit }) => object({ query, results: [], count: 0 }) // replace with real search
  );
}
```

### `src/tools/index.ts` — barrel file registers all tool modules
```typescript
import type { MCPServer } from "mcp-use/server";
import { registerSearchTools } from "./search.js";
export function registerAllTools(server: MCPServer) { registerSearchTools(server); }
```

### `src/server.ts`
```typescript
import { MCPServer } from "mcp-use/server";
import { config } from "./config.js";
import { registerAllTools } from "./tools/index.js";

const server = new MCPServer({ name: config.name, version: config.version, description: "Production MCP server" });
registerAllTools(server);
await server.listen({ port: config.port });
```

### `.env.example`
```env
PORT=3000
REDIS_URL=redis://localhost:6379
API_KEY=your-api-key-here
```

### `Dockerfile` (also reuse for Template 3)
```dockerfile
FROM node:22-slim AS build
WORKDIR /app
COPY package*.json tsconfig.json ./
COPY src ./src
RUN npm ci && npm run build

FROM node:22-slim
WORKDIR /app
COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules ./node_modules
COPY package*.json ./
ENV NODE_ENV=production
EXPOSE 3000
CMD ["node", "dist/server.js"]
```

### `docker-compose.yml`
```yaml
services:
  mcp-server:
    build: .
    ports: ["3000:3000"]
    environment: [PORT=3000, "REDIS_URL=redis://redis:6379", "API_KEY=${API_KEY}"]
    depends_on: [redis]
    restart: unless-stopped
  redis:
    image: redis:7-alpine
    volumes: [redis-data:/data]
volumes:
  redis-data:
```

---

## Template 3: OAuth-Protected Server
```
oauth-mcp-server/
├── package.json          ← add jose, dotenv
├── tsconfig.json
├── .env.example
├── Dockerfile            ← reuse from Template 2
└── src/
    ├── server.ts, config.ts
    ├── auth/verify.ts
    └── tools/protected.ts
```

### `src/config.ts`
```typescript
import "dotenv/config";
export const config = {
  name: "oauth-mcp-server", version: "1.0.0",
  port: parseInt(process.env.PORT || "3000", 10),
  auth: {
    issuer: process.env.AUTH_ISSUER!, audience: process.env.AUTH_AUDIENCE!,
    jwksUri: process.env.AUTH_JWKS_URI!,
  },
};
```

### `src/auth/verify.ts`
```typescript
import { createRemoteJWKSet, jwtVerify } from "jose";
import { config } from "../config.js";

const jwks = createRemoteJWKSet(new URL(config.auth.jwksUri));
export interface TokenClaims { sub: string; scope: string; permissions?: string[]; }

export async function verifyToken(token: string): Promise<TokenClaims> {
  const { payload } = await jwtVerify(token, jwks, { issuer: config.auth.issuer, audience: config.auth.audience });
  return payload as unknown as TokenClaims;
}
```

### `src/tools/protected.ts`
```typescript
import { object, error } from "mcp-use/server";
import type { MCPServer } from "mcp-use/server";
import z from "zod";

export function registerProtectedTools(server: MCPServer) {
  server.tool(
    { name: "list-users", description: "List org users (requires read:users)",
      schema: z.object({ page: z.number().default(1), limit: z.number().default(20) }) },
    async ({ page, limit }, { auth }) => {
      if (!auth?.permissions?.includes("read:users")) return error("Forbidden: requires read:users");
      return object({ users: [], total: 0 }); // replace with real user store
    }
  );

  server.tool(
    { name: "get-tenant-config", description: "Get config for authenticated tenant", schema: z.object({}) },
    async (_params, { auth }) => {
      if (!auth) return error("Authentication required");
      return object({ tenant: auth.sub, features: ["search", "analytics"], plan: "pro" });
    }
  );
}
```

### `src/server.ts`
```typescript
import { MCPServer } from "mcp-use/server";
import { config } from "./config.js";
import { registerProtectedTools } from "./tools/protected.js";

const server = new MCPServer({ name: config.name, version: config.version, description: "OAuth-protected MCP server" });
registerProtectedTools(server);
await server.listen({
  port: config.port,
  auth: { issuer: config.auth.issuer, audience: config.auth.audience, jwksUri: config.auth.jwksUri },
});
```

### `.env.example`
```env
PORT=3000
AUTH_ISSUER=https://your-tenant.auth0.com/
AUTH_AUDIENCE=https://api.your-app.com
AUTH_JWKS_URI=https://your-tenant.auth0.com/.well-known/jwks.json
```
