# Next.js drop-in: withMcpUse + createNextHandler

*Read this when integrating an MCP server into a Next.js App Router.*

v2 provides two runtime topologies for Next.js: **Embedded** (MCP runs in a Next.js Route Handler) or **Standalone** (MCP runs in a separate process). Both use the same v2 MCPServer and tool APIs.

## Embedded in Next.js

The Route Handler pattern is simplest for single-deployment scenarios. `withMcpUse()` wraps your Next.js config; `createNextHandler()` exports the four HTTP verbs.

### Setup steps

1. **Install mcp-use and zod:**
```bash
npm install mcp-use zod
```

2. **Export the MCP server** in `mcp-server.ts` (do NOT call `listen()`):
```ts
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({
  name: "my-next-app",
  version: "1.0.0",
  basePath: "/api/mcp",
});

server.tool(
  {
    name: "greet",
    description: "Greet a person",
    inputSchema: z.object({ name: z.string() }),
  },
  async ({ name }) => ({
    content: [{ type: "text", text: `Hello, ${name}!` }],
  }),
);

export default server;
```

3. **Enable the Next.js integration** in `next.config.ts`:
```ts
import { withMcpUse } from "mcp-use/next";

const nextConfig = {};

export default withMcpUse(nextConfig, {
  entry: "./mcp-server.ts",
  basePath: "/api/mcp",
});
```

4. **Add the optional catch-all route handler** in `app/api/mcp/[[...path]]/route.ts`:
```ts
import server from "@/mcp-server";
import { createNextHandler } from "mcp-use/next";

export const { GET, POST, DELETE, OPTIONS } = createNextHandler(server);
```

**Scripts:** Use standard Next.js scripts (`next dev`, `next build`, `next start`). Restart `next dev` after changing the server or any view.

**Testing:** Open `http://localhost:3000/api/mcp` in an MCP client.

## Standalone beside Next.js

Run the MCP server in a separate `mcp-use` process. This topology works in monorepos and allows independent scaling, restart, or deployment.

```bash
npm install mcp-use zod
```

Create `src/mcp/server.ts` (do NOT call `listen()`). Optionally import browser-safe components and shared services from the Next.js project:

```ts
import { MCPServer } from "mcp-use";
import { getStatus } from "@/lib/status-service";

const server = new MCPServer({
  name: "my-next-app",
  version: "1.0.0",
});

export default server;
```

Add separate scripts to `package.json`:
```json
{
  "scripts": {
    "next:dev": "next dev --port 3000",
    "mcp:dev": "mcp-use dev --mcp-dir src/mcp --port 3001"
  }
}
```

Run both in separate terminals:
```bash
npm run next:dev      # http://localhost:3000
npm run mcp:dev       # http://localhost:3001/mcp
```

For monorepos, use `--path` to select the host project:
```bash
mcp-use dev --path apps/web --entry ../mcp/src/server.ts --views-dir ../mcp/src/views --port 3001
```

Imports from `src/mcp/` automatically resolve via the Next.js `tsconfig.json` and project aliases.

## Shared code safety

Both topologies load the Next.js environment. Views run in browser iframes and must not import Server Components or server-only modules (e.g., `next/headers`, `next/cache`, database clients). Shared services that import `server-only` will load but the shims do not invent a request context.

For the standalone topology, v2 CLI provides compatibility shims so shared services load without error. Pass identity through MCP authentication (see references/11-auth) and request data through tool input or `RequestContext`.

## Verification

For either topology:

1. Build in production mode.
2. Initialize an MCP session.
3. List tools and confirm expected names + schemas.
4. Call every tool and assert text + `structuredContent`.
5. Read view URIs from tool metadata and assert HTML loads.
6. Verify every referenced JavaScript, stylesheet, and public asset.
7. (Embedded only:) Request the Next.js landing page and verify browser CORS preflight at the `/api/mcp` endpoint.

See `references/22-validate` for detailed CLI walkthroughs and `references/25-deploy/platforms/02-vercel.md` for production deployment patterns.
