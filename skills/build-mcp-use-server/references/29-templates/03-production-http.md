# Template: Production HTTP Server

HTTP-first scaffold with env-driven config, modular tool registration, Dockerfile, and a Redis-ready compose file. Use this when graduating beyond a single-file demo.

## Layout

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

## `src/config.ts`

```typescript
import "dotenv/config";

export const config = {
  name: "production-server",
  version: process.env.npm_package_version || "1.0.0",
  port: parseInt(process.env.PORT || "3000", 10),
  redisUrl: process.env.REDIS_URL || "redis://localhost:6379",
};
```

## `src/tools/search.ts`

Modular tool file. Each domain gets its own module, then a barrel registers them all.

```typescript
import { object } from "mcp-use/server";
import type { MCPServer } from "mcp-use/server";
import { z } from "zod";

export function registerSearchTools(server: MCPServer) {
  server.tool(
    {
      name: "search",
      description: "Search indexed documents",
      schema: z.object({
        query: z.string().min(1),
        limit: z.number().default(10),
      }),
    },
    async ({ query, limit }) => object({ query, results: [], count: 0 })
  );
}
```

## `src/tools/index.ts`

```typescript
import type { MCPServer } from "mcp-use/server";
import { registerSearchTools } from "./search.js";

export function registerAllTools(server: MCPServer) {
  registerSearchTools(server);
}
```

## `src/server.ts`

```typescript
import { MCPServer } from "mcp-use/server";
import { config } from "./config.js";
import { registerAllTools } from "./tools/index.js";

const server = new MCPServer({
  name: config.name,
  version: config.version,
  description: "Production MCP server",
});

registerAllTools(server);

await server.listen(config.port);
```

## `.env.example`

```env
PORT=3000
REDIS_URL=redis://localhost:6379
API_KEY=your-api-key-here
```

## `Dockerfile`

Multi-stage build. Reuse this same Dockerfile for an OAuth-protected variant.

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

## `docker-compose.yml`

```yaml
services:
  mcp-server:
    build: .
    ports:
      - "3000:3000"
    environment:
      - PORT=3000
      - REDIS_URL=redis://redis:6379
      - API_KEY=${API_KEY}
    depends_on:
      - redis
    restart: unless-stopped
  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data
volumes:
  redis-data:
```

## Run locally

```bash
cp .env.example .env
npm install
npm run dev
```

## Run in Docker

```bash
docker compose up --build
```

## Adding more tool modules

1. Create `src/tools/<domain>.ts` exporting `register<Domain>Tools(server)`.
2. Import and call it from `src/tools/index.ts`.
3. Restart `npm run dev`.

## Next steps

- Persist sessions across restarts: `../10-sessions/` and `../30-workflows/02-stateful-redis-streaming-server.md`.
- Add OAuth: see `../11-auth/` and swap `MCPServer` config to include an `oauth:` provider.
- Production hardening: `../24-production/`.
