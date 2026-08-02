# Add to existing app

*Read this to embed an MCP server inside an existing web application.*

Use this pattern when you own an existing app (Node, Next.js, Express, Hono, etc.) and want to expose its capabilities via MCP without creating a separate server.

## Side-car server pattern

Run a separate MCP server process alongside your app. Each listens on a different port.

```typescript
// mcp-server.ts
import { MCPServer } from "mcp-use";

const server = new MCPServer({
  name: "my-app-mcp",
  version: "1.0.0",
});

// Use your app's client as a library
import { myApiClient } from "./api-client";

server.tool(
  {
    name: "get-user",
    description: "Fetch user profile",
    inputSchema: z.object({ userId: z.string() }),
  },
  async ({ userId }, ctx) => {
    const user = await myApiClient.users.get(userId);
    return {
      content: [{ type: "text", text: JSON.stringify(user) }],
      structuredContent: user,
    };
  }
);

await server.listen(3001); // Your app on 3000, MCP on 3001
```

Pros: Independent lifecycle, easy to debug. Cons: Extra process, two HTTP servers.

## Embed in Next.js

Use `mcp-use/next` integration to mount MCP as a route handler:

```typescript
// app/api/mcp/[[...path]]/route.ts
import { MCPServer } from "mcp-use";
import { createNextHandler } from "mcp-use/next";
import { z } from "zod";

const server = new MCPServer({
  name: "my-nextjs-app",
  version: "1.0.0",
});

export const POST = createNextHandler(server);
export const GET = createNextHandler(server);

// Register tools, resources, prompts...
server.tool(
  {
    name: "get-user",
    description: "Fetch user",
    inputSchema: z.object({ id: z.string() }),
  },
  async ({ id }, ctx) => ({ /* ... */ })
);
```

Inspector auto-mounts at `/api/mcp/inspector` in dev. Prod: `/api/mcp/inspector` with `--with-inspector` flag.

## Embed in Express / Hono

Use `mcp-use/node` for raw HTTP:

```typescript
// server.ts
import { MCPServer } from "mcp-use";
import { toNodeHandler } from "mcp-use/node";
import express from "express";

const app = express();
const server = new MCPServer({ name: "my-express-app", version: "1.0.0" });

// Mount MCP at /mcp
const handler = toNodeHandler(server);
app.use("/mcp", (req, res) => {
  handler(new Request(`http://localhost:3000${req.url}`, {
    method: req.method,
    headers: req.headers as Record<string, string>,
    body: req.body ? JSON.stringify(req.body) : undefined,
  }))
    .then(r => res.send(r))
    .catch(e => res.status(500).send(e));
});

app.listen(3000);
```

## Compose fetch handlers

If you have multiple fetch-based servers, use `composeFetch`:

```typescript
import { composeFetch } from "mcp-use";

const mcpServer = new MCPServer({ name: "mcp", version: "1.0.0" });
const apiServer = new Hono(); // or other fetch handler

export default composeFetch([
  ["/mcp", mcpServer.fetch],
  ["/api", apiServer.fetch],
  ["/", fallbackHandler],
]);
```

Each path routes to its handler.

## When NOT to embed

- **Many independent clients** connecting to the same server — use side-car
- **Separate deployment** — side-car is simpler
- **Distinct auth zones** — side-car avoids mixing concerns

Embed when:
- Shared session/auth context
- Single deployment unit
- Convenient to couple lifecycle
