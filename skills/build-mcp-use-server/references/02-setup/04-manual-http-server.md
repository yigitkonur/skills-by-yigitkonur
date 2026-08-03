# Manual HTTP server

*Read this to build an MCPServer by hand without scaffolding.*

This is the minimal working CLI-managed server, suitable as a template when scaffolding is not an option (or for learning).

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

// The CLI imports this instance and owns the HTTP listener.
export default server;
```

Run this entry with `mcp-use dev`, `mcp-use build`, and `mcp-use start`; do not call `listen()` in it.

## Direct-listener alternative

If you need to run without the CLI, keep listener ownership in a separate entry so `index.ts` remains importable by the CLI.

File: `direct.ts`

```typescript
import server from "./index.js";

const { url } = await server.listen(3000);
console.log(`MCP server listening at ${url}`);
```

```bash
npx --yes tsx direct.ts
```

## Export as fetch handler

For serverless/edge runtimes, create a separate adapter entry that exports `server.fetch`.

File: `serverless.ts`

```typescript
import server from "./index.js";

export default server.fetch;
export const fetch = server.fetch;
```

## Wrap for Node.js HTTP

To run on a Node.js `http.Server`, use another adapter entry.

File: `node-http.ts`

```typescript
import { createServer } from "node:http";
import { toNodeHandler } from "mcp-use/node";
import server from "./index.js";

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
npx mcp-use@2.0.0-beta.66 dev --entry index.ts
```

`mcp-use` is the canonical CLI implementation; `@mcp-use/cli@4.0.0-beta.15` is a compatibility-only bin shim for the historical install command with no command logic of its own — either invocation works, but prefer `mcp-use` directly in new docs/scripts.

Only `mcp-use dev` (or, in production, `mcp-use start --with-inspector`) mounts the Inspector. Running the entry file directly does **not**:

```bash
npx --yes tsx direct.ts
# server.listen(3000) starts the MCP endpoint at http://127.0.0.1:3000/mcp —
# but NOT the Inspector. server.fetch, listen(), and `mcp-use build` never
# mount an Inspector shell or proxy; plain `mcp-use start` also 404s on
# GET /mcp/inspector. To inspect this server, either run it through
# `mcp-use dev`/`mcp-use start --with-inspector`, or point the standalone
# inspector at the running endpoint:
npx @mcp-use/inspector --url http://127.0.0.1:3000/mcp
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
