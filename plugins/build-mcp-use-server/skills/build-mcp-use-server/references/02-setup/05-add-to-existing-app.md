# Add to existing app

*Read this to embed an MCP server inside an existing web application.*

Use this pattern when you own an existing app (Node, Next.js, Express, Hono, etc.) and want to expose its capabilities via MCP without creating a separate server.

## Side-car server pattern

Run a separate MCP server process alongside your app. Each listens on a different port.

```typescript
// mcp-server.ts
import { MCPServer } from "mcp-use";
import { z } from "zod";
// Use your app's client as a library
import { myApiClient } from "./api-client";

const server = new MCPServer({
  name: "my-app-mcp",
  version: "1.0.0",
});

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

Two pieces wire an `MCPServer` into the Next.js App Router: `withMcpUse` (in `next.config.ts`, handles build/CORS/tracing integration) and `createNextHandler` (in the route file, exposes the server over HTTP). Both come from `mcp-use/next`.

```typescript
// mcp-server.ts
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({
  name: "my-nextjs-app",
  version: "1.0.0",
  basePath: "/api/mcp", // default is "/mcp" — override to match the route below
});

server.tool(
  {
    name: "get-user",
    description: "Fetch user",
    inputSchema: z.object({ id: z.string() }),
  },
  async ({ id }, ctx) => ({ /* ... */ })
);

export default server; // do not call listen() — Next.js owns the HTTP listener
```

```typescript
// next.config.ts
import type { NextConfig } from "next";
import { withMcpUse } from "mcp-use/next";

const nextConfig: NextConfig = {};

export default withMcpUse(nextConfig, {
  entry: "./mcp-server.ts",
  basePath: "/api/mcp",
});
```

```typescript
// app/api/mcp/[[...path]]/route.ts
import server from "@/mcp-server";
import { createNextHandler } from "mcp-use/next";

export const { GET, POST, DELETE, OPTIONS } = createNextHandler(server);
```

`createNextHandler(server)` returns one object with all four method handlers — call it **once** and destructure; do not call it separately per HTTP verb. Use an optional catch-all (`[[...path]]`) because mcp-use serves the MCP endpoint and nested view assets from the same subtree. `withMcpUse` defaults: `entry: "mcp/server.ts"`, `mcpDir: "mcp"`, `basePath: "/api/mcp"` — pass matching `basePath` to both `withMcpUse` and the `MCPServer` constructor.

There is no Inspector mount for the embedded Next.js route. Inspector mounting (`${basePath}/inspector`) only exists on `mcp-use dev` and `mcp-use start --with-inspector` — the CLI-owned standalone listener. Test an embedded server with the standalone Inspector against its URL instead: `npx @mcp-use/inspector --url http://localhost:3000/api/mcp`.

mcp-use also supports a **standalone-beside-Next.js** topology: keep the MCP source under `src/mcp/` in the same Next.js project, run it with `mcp-use dev --mcp-dir src/mcp --port 3001` (a separate script alongside `next dev`), and get Inspector mounting for free. Choose embedded when the website and MCP endpoint should deploy as one application; choose standalone-beside when MCP needs its own process, port, deployment, or scaling policy. Full Next.js coverage (both topologies, Vercel deploy, views): `../19-nextjs-drop-in/01-overview-withmcpuse.md`.

## Embed in Express / Hono

Use `mcp-use/node`'s `toNodeHandler` — it produces a **Node-style** `(req, res, parsedBody?) => Promise<void>` handler that writes directly to `res`; it does not accept or return a Web `Request`/`Response`. Because Express's own `(req, res)` handler signature already duck-types the `NodeIncomingMessageLike`/`NodeServerResponseLike` shape `toNodeHandler` expects, pass it straight through with no adapter code:

```typescript
// server.ts
import { MCPServer } from "mcp-use";
import { toNodeHandler } from "mcp-use/node";
import express from "express";

const app = express();
const server = new MCPServer({ name: "my-express-app", version: "1.0.0" });

// Mount MCP at /mcp — do not run express.json() (or any body-parser) in front
// of this route; toNodeHandler reads and parses the raw body itself.
app.all("/mcp*", toNodeHandler(server));

app.listen(3000);
```

For a raw `node:http` server (no framework), the same handler works directly:

```typescript
import { createServer } from "node:http";
import { toNodeHandler } from "mcp-use/node";

createServer(toNodeHandler(server)).listen(3000);
```

## Compose fetch handlers

`composeFetch` is an onion-style **middleware chain around one terminal handler** — it is not a path router. Signature: `composeFetch(terminal: FetchHandler, ...middlewares: FetchMiddleware[]): FetchHandler`, where each middleware is `(request, next) => Promise<Response>`.

```typescript
import { composeFetch, jsonBodyMiddleware, hostValidationMiddleware } from "mcp-use";

const server = new MCPServer({ name: "mcp", version: "1.0.0" });

export default composeFetch(
  server.fetch, // terminal handler — runs when no middleware short-circuits
  jsonBodyMiddleware(),
  hostValidationMiddleware(["example.com"])
);
```

To dispatch by path to more than one fetch handler, route inside a middleware (or write a terminal handler that branches) using the `matchesPath`/`matchesPathPrefix` helpers from `mcp-use`:

```typescript
import { composeFetch, matchesPath } from "mcp-use";

const terminal = async (request: Request): Promise<Response> => {
  if (matchesPath(request, "/mcp")) return server.fetch(request);
  if (matchesPath(request, "/api")) return apiHandler(request);
  return fallbackHandler(request);
};

export default composeFetch(terminal, jsonBodyMiddleware());
```

For routes on the same Hono app instance `MCPServer` already owns, it is simpler to add them directly on `server.app` (or the bound helpers `server.get`/`server.post`/`server.delete`) instead of composing a second fetch handler — see `../08-server-config/05-middleware.md` and `../08-server-config/06-custom-routes.md`.

## When NOT to embed

- **Many independent clients** connecting to the same server — use side-car
- **Separate deployment** — side-car is simpler
- **Distinct auth zones** — side-car avoids mixing concerns

Embed when:
- Shared session/auth context
- Single deployment unit
- Convenient to couple lifecycle
