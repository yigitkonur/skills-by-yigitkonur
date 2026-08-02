# Manual HTTP server

*Read this to build an MCPServer by hand without scaffolding.*

This is the minimal working server, suitable as a template when scaffolding is not an option (or for learning).

## Minimal server

File: `index.ts` (ESM)

```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
});

// Register one tool
export const add = server.tool(
  {
    name: "add",
    description: "Add two numbers",
    inputSchema: z.object({
      a: z.number().describe("First number"),
      b: z.number().describe("Second number"),
    }),
    outputSchema: z.object({ result: z.number() }),
  },
  async ({ a, b }, ctx) => ({
    content: [{ type: "text", text: `${a} + ${b} = ${a + b}` }],
    structuredContent: { result: a + b },
  })
);

// Start listening
const { port, url } = await server.listen(3000);
console.log(`MCP server listening at ${url}`);
```

## Export as fetch handler

For serverless/edge runtimes, export `server.fetch`:

```typescript
// Production (Vercel, Cloudflare, Deno)
export default server.fetch;
// or named export
export const fetch = server.fetch;
```

## Wrap for Node.js HTTP

To run on a Node.js `http.Server`:

```typescript
import { createServer } from "http";
import { toNodeHandler } from "mcp-use/node";

const handler = toNodeHandler(server);
const httpServer = createServer(handler);
httpServer.listen(3000, "127.0.0.1", () => {
  console.log("HTTP server running on http://127.0.0.1:3000");
});
```

## Test locally

With `mcp-use dev` (scaffolded projects):

```bash
npm run dev
```

Without scaffolding (manual):

```bash
npx @mcp-use/cli@4.0.0-beta.15 dev --entry index.ts
```

Or start the server directly and test via Inspector:

```bash
tsx index.ts
# Then browse http://localhost:3000/mcp/inspector
```

## Package scripts

Create `package.json`:

```json
{
  "name": "my-server",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "mcp-use dev --entry index.ts",
    "build": "mcp-use build --entry index.ts",
    "typecheck": "mcp-use typecheck --entry index.ts",
    "start": "mcp-use start"
  }
}
```

Then run:

```bash
npm run dev       # Dev with HMR, Inspector
npm run build     # Build to .mcp-use/build/
npm run start     # Run production build
```

## No stdio in v2

Stdio transport does not exist in v2. All servers are HTTP-only:
- Local dev: `http://127.0.0.1:3000/mcp` (Inspector at `/mcp/inspector`)
- Production: `https://<domain>/mcp`

For cloud deployment, see `references/25-deploy/`.
