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

This is the real generated file, verbatim:

```typescript
import { MCPServer } from "mcp-use";

const server = new MCPServer({
  name: "{{PROJECT_NAME}}",
  title: "{{PROJECT_NAME}}",
  version: "1.0.0",
  description: "A blank MCP server built with mcp-use",
});

export default server;
```

No `server.listen()` call here either — like `mcp-server` and `mcp-apps`, the CLI (`mcp-use dev`/`mcp-use build`/`mcp-use start`) imports the default export and owns the HTTP socket. Add tools, prompts, and resources above the `export default`.

## When to Skip Scaffolding: Manual HTTP Server

If you have an existing Node/Express/Hono app and want to add MCP without generating a new project, hand-code the server and call `.listen()` yourself — this is the one legitimate place `server.listen()` belongs, since there is no CLI-managed entry file.

### Minimal HTTP Server by Hand

```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({
  name: "embedded-mcp",
  version: "1.0.0",
  // basePath defaults to "/mcp"; host defaults to 127.0.0.1; port defaults to
  // process.env.PORT or 3000. There is no `baseUrl` config field.
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

// Listen on a port; resolves once bound
const { port, url } = await server.listen(3000);
console.log(`MCP server listening at ${url}`);
```

Run with:
```bash
npx tsx index.ts
```

### Key Points

1. **No `baseUrl` config field** — `ServerConfig` has `basePath` (route path, default `"/mcp"`), `host` (bind hostname, default `127.0.0.1`), and `port` (bind port, default `3000` or `process.env.PORT`). There is no `baseUrl`.
2. **`server.listen(port?, options?)`** — Starts HTTP; returns a Promise resolving to `{ port, url }`. Port precedence: argument → `PORT` env → `config.port` → `3000`. Host precedence: `options.host` → `HOST` env → `config.host` → `127.0.0.1`.
3. **Endpoint** — Served at `config.basePath` (default `/mcp`), not derived from a `baseUrl`.
4. **Localhost binds get DNS-rebinding protection automatically** — set `host: "0.0.0.0"` to serve publicly (e.g. behind a platform edge).
5. **ESM only** — Run `.ts` directly with `tsx`/`ts-node`, or transpile to `.js` first; there is no CommonJS build path.

## Adding MCP to an Express App

If you have existing Express routes and want MCP as a side-car, do not pass `server.fetch` straight to Express — `server.fetch` is a Web `(Request) => Promise<Response>` handler (from the underlying Hono app), not an Express-style `(req, res)` middleware. Use `toNodeHandler` from `mcp-use/node` to bridge it:

```typescript
import express from "express";
import { MCPServer } from "mcp-use";
import { toNodeHandler } from "mcp-use/node";

const app = express();
const mcp = new MCPServer({ name: "my-api", version: "1.0.0" });

mcp.tool(/* ... */);

// Express routes (keep existing)
app.get("/api/health", (req, res) => res.json({ ok: true }));

// Mount MCP at /mcp — do not run a body-parser in front of this route;
// toNodeHandler reads and parses the raw body itself.
app.all("/mcp*", toNodeHandler(mcp));

app.listen(3000);
```

Or run MCP on a dedicated port instead of sharing Express's:

```typescript
// Express on 3000
app.listen(3000, () => console.log("API on :3000"));

// MCP on 3001 — server.listen() binds its own HTTP server
await mcp.listen(3001);
console.log("MCP on :3001/mcp");
```

Full embedding patterns (side-car, Next.js, Express/Hono, `composeFetch`): `references/02-setup/05-add-to-existing-app.md`.

## When to Use Each Approach

| Situation | Recommendation |
|-----------|---|
| New project, full MCP focus | `npx create-mcp-use-app --template mcp-server` (or `mcp-apps`) |
| Quick test / one-off tool | `npx create-mcp-use-app --template blank` or hand-code `listen()` |
| MCP added to existing API | Existing app's stack + `mcp.listen()` on a different port, or `toNodeHandler`/`composeFetch` on the same port |
| MCP embedded in Next.js/other web framework | Read `references/19-nextjs-drop-in/01-overview-withmcpuse.md` |

## Next Steps

- Read `references/08-server-config/01-mcp-server-constructor.md` for all `ServerConfig` options.
- Read `references/02-setup/04-manual-http-server.md` for more hand-coding examples.
- Read `references/02-setup/05-add-to-existing-app.md` for integration patterns.
