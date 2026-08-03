# Railway

*Read this when deploying an MCP server to Railway.*

## When to choose Railway

Use this as a generic Node/filesystem deployment pattern when the Railway service can:

- run the project's `npm run build` and `npm start` scripts;
- include `.mcp-use/build/` in the deployed filesystem;
- inject a listen port and route an assigned public domain to it.

mcp-use has no first-party Railway deployment guide or dedicated runtime adapter; import from `mcp-use` and verify Railway-specific configuration against the current platform controls.

## Handler wiring

Railway runs `npm start` (`mcp-use start`), which imports the built entry's default export and calls `.listen()` on it — export the `MCPServer` instance itself, not a detached `server.fetch` reference:

```ts
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({ name: "my-server", version: "1.0.0", host: "0.0.0.0" });
server.tool(
  { name: "example", description: "...", inputSchema: z.object({}) },
  () => ({ content: [{ type: "text", text: "ok" }] }),
);

export default server;
```

`mcp-use start` reads Railway's injected `PORT` and calls `server.listen(port, { host })` for you — no explicit `listen()` call needed in your own code as long as `npm start` runs `mcp-use start`. The resulting handler serves both MCP endpoints (`/mcp`) and view assets (`/mcp/_mcp-use/*`) from the same origin.

## Build and start configuration

Configure Railway's build command to run both checks and the mcp-use build, and its start command to run the generated server:

```text
Build: npm run typecheck && npm run build
Start: npm start
```

The generated template's `npm start` script is `mcp-use start`. Use the exact public domain assigned to the service when setting `MCP_URL` for View builds; do not infer a Railway hostname pattern:

```bash
MCP_URL=https://<assigned-service-domain> npm run build
```

Deploy through the current Railway dashboard or CLI workflow after configuring those commands.

## Env & assets

- **MCP_URL (build/runtime):** Exact assigned public origin only (scheme + host, no `/mcp` path)
- **PORT (runtime):** Railway-injected listen port; `mcp-use start` reads it automatically (explicit flag > `PORT` env > configured `port` > `3000` fallback)
- **HOST (runtime):** Set `host: "0.0.0.0"` in the `MCPServer` config so the platform proxy can reach the process
- **.mcp-use/build/:** Must exist in the deployed working directory; build it during the platform build phase

## Gotchas

- **No hostname guessing:** Use the domain shown by Railway for that environment; preview/review deployments may have distinct domains
- **Build during deploy:** Ensure `npm run typecheck && npm run build` runs in Railway's build phase, not just locally
- **View assets:** `mcp-use start` serves `.mcp-use/build/views/` through the same server handler; no separate static service is needed for this filesystem pattern
- **Verify after deploy:** Run `mcp-use@beta screenshot --mcp https://<assigned-service-domain>/mcp --tool <tool-name>` against the live endpoint
- **Application state:** Railway processes can restart or scale; keep durable state in an external data store. `RequestContext.requestState` is not persistence — it echoes opaque client state across an `input_required` round
