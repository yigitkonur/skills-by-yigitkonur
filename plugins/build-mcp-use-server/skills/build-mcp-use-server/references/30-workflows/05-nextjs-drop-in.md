# Workflow: Next.js Drop-In

*Read this for an end-to-end workflow: add an MCP server to an existing Next.js app with `withMcpUse` and `createNextHandler`.*

## Prerequisites

- Existing Next.js 14+ app (App Router)
- Node.js >= 22
- `npm` or `pnpm`

## Steps

### 1. Install `mcp-use`

```bash
npm install mcp-use@beta zod@4
```

**Verify:** `npm ls mcp-use` shows v2.

### 2. Create MCP Server Definition

Create `src/mcp-server.ts` without calling `listen()`:

```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({
  name: "my-next-mcp",
  version: "1.0.0",
  basePath: "/api/mcp",
});

export const echoTool = server.tool(
  {
    name: "echo",
    description: "Echo back a message",
    inputSchema: z.object({
      message: z.string().describe("Message to echo"),
    }),
    outputSchema: z.object({
      echoed: z.string(),
      timestamp: z.number(),
    }),
  },
  async ({ message }) => ({
    content: [{ type: "text", text: `Echo: ${message}` }],
    structuredContent: { echoed: message, timestamp: Date.now() },
  })
);

export default server;
```

**Verify:** `npm run typecheck` passes. Never call `server.listen()` here; Next.js owns the listener.

### 3. Wrap `next.config.ts`

```typescript
import type { NextConfig } from "next";
import { withMcpUse } from "mcp-use/next";

const nextConfig: NextConfig = {};

export default withMcpUse(nextConfig, {
  entry: "./src/mcp-server.ts",
  basePath: "/api/mcp",
});
```

**Verify:** Restart `next dev`; it starts without a configuration error.

### 4. Create Route Handler

Create `app/api/mcp/[[...path]]/route.ts`:

```typescript
import server from "@/mcp-server";
import { createNextHandler } from "mcp-use/next";

export const { GET, POST, DELETE, OPTIONS } = createNextHandler(server);
```

**Verify:** The route file exports all four HTTP handlers.

### 5. Test Locally

```bash
npm run dev
```

The embedded Next.js topology does not auto-mount an inspector route — there is no `/api/mcp/inspector`. Run the standalone Inspector against the running route instead:

```bash
npx @mcp-use/inspector --url http://localhost:3000/api/mcp
```

Connect and call `echo` with `{"message":"Hello Next.js!"}`.

**Verify:** The response contains `echoed: "Hello Next.js!"` and a numeric `timestamp`.

### 6. Build and Deploy

```bash
npm run build
```

**Verify:** Next.js builds the app, MCP server, and any views without errors.

Deploy through the application's normal Vercel workflow. The MCP endpoint is `https://your-domain.com/api/mcp`.

**Verify:** Point the standalone Inspector at the deployed URL and repeat the `echo` call — the deployed route has no `/inspector` sub-path either:

```bash
npx @mcp-use/inspector --url https://your-domain.com/api/mcp
```

## Common Issues

| Issue | Solution |
|-------|----------|
| Port conflict | Remove `server.listen()` from `mcp-server.ts`. |
| 404 on `/api/mcp` | Match `basePath` in the server, `next.config.ts`, and route folder. |
| `mcp-use/next` not found | Install a v2 release of `mcp-use`. |

## Next

- Read `../19-nextjs-drop-in/01-overview-withmcpuse.md` for integration details.
- Read `../19-nextjs-drop-in/04-deploying-on-vercel.md` for Vercel details.
