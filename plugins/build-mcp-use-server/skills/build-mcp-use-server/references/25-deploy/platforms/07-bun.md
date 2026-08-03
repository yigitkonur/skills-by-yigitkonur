# Bun

*Read this when deploying an MCP server using Bun as the runtime.*

## When to choose Bun

- Bun runtime with Web-standard `Request`/`Response`
- A deployed filesystem that includes `.mcp-use/build`
- You will own Bun-specific process binding and deployment configuration; mcp-use ships no dedicated `mcp-use/bun` adapter or first-party Bun deployment guide

## Handler wiring

Bun is Node-compatible. Bun's file-run auto-serve convention detects a default-exported **object** with a `fetch` property (the same convention Cloudflare Workers and Hono use) — a bare function default export is not the documented shape, so export the `server` instance itself, not `server.fetch` detached from it:

```ts
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({ name: "my-server", version: "1.0.0" });
server.tool(
  { name: "example", description: "...", inputSchema: z.object({}) },
  () => ({ content: [{ type: "text", text: "ok" }] }),
);

export default server;
```

`bun run server.ts` detects `server.fetch` on the exported object and starts the HTTP server automatically — no explicit `Bun.serve()` call needed.

Or with explicit Bun server binding (e.g. to control `port`/`hostname` directly):

```ts
const port = Number(process.env.PORT ?? 3000);
const hostname = process.env.HOST ?? "0.0.0.0";

Bun.serve({
  port,
  hostname,
  fetch(request) {
    return server.fetch(request);
  },
});
```

## Build & run commands

```bash
# Build the mcp-use server and generated Views for the public endpoint
MCP_URL=https://api.example.com npm run build

# Run the Bun entrypoint shown above (or the explicit Bun.serve variant)
bun run src/server.ts
```

Choose the final container/platform packaging through your Bun host. If you bundle the entry, still deploy `.mcp-use/build/` beside the process working directory — the mcp-use runtime reads generated View files from that path.

## Env & assets

- **MCP_URL (build-time):** Public origin used for View/server origin metadata (no path)
- **PORT / HOST (runtime):** Read these yourself in the explicit `Bun.serve` wrapper when the deployment platform injects them; this path does not use `mcp-use start`
- **.mcp-use/build/:** Must be co-deployed with the server in its working directory

## Gotchas

- **No dedicated adapter:** Import from `mcp-use`; the package has no `mcp-use/bun` subpath, so keep the integration at the portable `server.fetch` boundary
- **Filesystem requirement:** The runtime reads `.mcp-use/build/views/` from disk; ensure build output is part of deployment
- **Verify after build:** Call `mcp-use@beta screenshot` against deployed endpoint; HTTP 200 alone does not validate streamable MCP or rendered views
- **Session state:** Bun follows the framework's stateless-per-request pattern (fresh SDK server built per HTTP request); maintain external state (DB, cache) if running multiple instances. `RequestContext.requestState` is unrelated — it echoes opaque client state across an `input_required` round, not general session storage
