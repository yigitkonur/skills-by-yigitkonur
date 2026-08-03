# Vercel

*Read this when deploying a non-Next mcp-use server as a Vercel Function.*

For Next.js, use `withMcpUse()` and `createNextHandler()` as described in `references/19-nextjs-drop-in/01-overview-withmcpuse.md`.

## Setup

Vercel Functions are stateless. `MCPServer` builds a fresh SDK server per HTTP request from its module-scope registry, so reuse one configured server across warm invocations.

Create `mcp-server.ts`:

```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";

export const server = new MCPServer({
  name: "vercel-mcp",
  version: "1.0.0",
  basePath: "/api/mcp",
});

server.tool(
  {
    name: "convert-temperature",
    description: "Convert a temperature value",
    inputSchema: z.object({
      value: z.number(),
      from: z.enum(["celsius", "fahrenheit"]),
    }),
  },
  async ({ value, from }) => {
    const result = from === "celsius"
      ? (value * 9) / 5 + 32
      : ((value - 32) * 5) / 9;

    return {
      content: [{ type: "text", text: `Result: ${result}` }],
    };
  }
);
```

Create `api/mcp.ts`:

```typescript
import { server } from "../mcp-server.ts";

export default server;
```

Vercel accepts the server directly because `MCPServer` exposes a Web-standard Fetch handler.

## Match the Function Path

Vercel serves `api/mcp.ts` at `/api/mcp`. Set `basePath: "/api/mcp"` to the same path. If the function path and `basePath` drift, Hono has no matching route and requests return 404.

## Deploy

```bash
npx vercel deploy
```

Connect clients to:

```text
https://<deployment>.vercel.app/api/mcp
```

For Views, build with the public origin and follow the example's `includeFiles` and catch-all rewrite configuration so nested asset requests reach the function:

```bash
MCP_URL=https://<project>.vercel.app npm run build
npx vercel deploy --prod
```

## Verify

```bash
npx --yes mcp-use@beta screenshot \
  --mcp https://<project>.vercel.app/api/mcp \
  --tool <tool-name> \
  --output vercel-live-view.png
```

`server.fetch` applies no Host validation by default. Vercel's edge only routes assigned deployment hostnames to the function. Set `allowedHosts` only when you intentionally want stricter application-level validation.
