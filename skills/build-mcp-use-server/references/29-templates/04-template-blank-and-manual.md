# Template: blank and Manual HTTP Server

*Read this for the minimal `blank` template and when to hand-code an HTTP server instead of scaffolding.*

## Template: blank

The `blank` template is the smallest starting point.

```bash
npx create-mcp-use-app@2.0.0-beta.14 my-project --template blank
```

### Generated File Tree

```
my-project/
├── index.ts                     # Empty MCPServer, you add everything
├── mcp-env.d.ts
├── package.json                 # Only mcp-use (no React)
├── tsconfig.json
├── gitignore
├── README.md
└── public/
    └── icon.svg
```

### What `index.ts` Looks Like

```typescript
import { MCPServer } from "mcp-use";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
});

// Add tools, prompts, resources here

export default server;
server.listen();
```

## When to Skip Scaffolding: Manual HTTP Server

If you have an existing Node/Express/Hono app and want to add MCP without generating a new project:

### Minimal HTTP Server by Hand

```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({
  name: "embedded-mcp",
  version: "1.0.0",
  baseUrl: "http://localhost:3000",  // Your public URL
});

server.tool(
  {
    name: "say-hello",
    description: "Say hello",
    inputSchema: z.object({ name: z.string() }),
  },
  async ({ name }) => ({
    content: [{ type: "text", text: `Hello, ${name}!` }],
  })
);

// Listen on a port
await server.listen(3000);
console.log("MCP server listening on http://localhost:3000/mcp");
```

Run with:
```bash
npx ts-node index.ts
```

### Key Points

1. **`baseUrl` is optional** — Defaults to `http://localhost:PORT/mcp`.
2. **`server.listen(port)`** — Starts HTTP; returns a Promise.
3. **Endpoint** — Always `/mcp` relative to baseUrl; no config.
4. **ESM only** — Use `.ts` with `ts-node`, or transpile to `.js`.

## Adding MCP to an Express App

If you have existing Express routes and want MCP as a side-car:

```typescript
import express from "express";
import { MCPServer } from "mcp-use";

const app = express();
const mcp = new MCPServer({ name: "my-api", version: "1.0.0" });

// MCP tools
mcp.tool(/* ... */);

// Express routes (keep existing)
app.get("/api/health", (req, res) => res.json({ ok: true }));

// Mount MCP on a sub-path
app.use("/mcp", mcp.fetch);  // MCP endpoint at /mcp

app.listen(3000);
```

Or use a dedicated port for MCP (cleaner):

```typescript
// Express on 3000
app.listen(3000, () => console.log("API on :3000"));

// MCP on 3001
await mcp.listen(3001);
console.log("MCP on :3001/mcp");
```

## When to Use Each Approach

| Situation | Recommendation |
|-----------|---|
| New project, full MCP focus | `npx create-mcp-use-app --template mcp-server` (or `mcp-apps`) |
| Quick test / one-off tool | `npx create-mcp-use-app --template blank` or hand-code `listen()` |
| MCP added to existing API | Existing app's stack + `server.listen()` on a different port |
| MCP embedded in Next.js/other web framework | Read `../19-nextjs-drop-in/01-overview-withmcpuse.md` |

## Next Steps

- Read `../08-server-config/01-mcp-server-constructor.md` for all ServerConfig options.
- Read `../02-setup/04-manual-http-server.md` for more hand-coding examples.
- Read `../02-setup/05-add-to-existing-app.md` for integration patterns.
