# Workflow: Multi-Server Proxy Gateway

**Goal:** front three upstream MCP servers (one stdio, one stdio, one HTTP) behind a single endpoint. Add a gateway-only health tool. Tools from upstreams are auto-namespaced.

> **Requires `mcp-use` ≥ v1.21.0.** `MCPServer.proxy()` is **async** — it must be `await`ed before `listen()`. Forgetting `await` is the most common gateway bug: `listen()` starts before upstream connections are ready and the first call fails.

## Layout

```
mcp-gateway/
├── package.json
├── tsconfig.json
└── index.ts
```

## `package.json`

```json
{
  "name": "mcp-gateway",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "mcp-use dev",
    "build": "mcp-use build",
    "start": "mcp-use start"
  },
  "dependencies": {
    "mcp-use": "^1.21.5",
    "zod": "^4.0.0"
  },
  "devDependencies": {
    "@mcp-use/cli": "latest",
    "typescript": "^5.5.0"
  }
}
```

## `index.ts`

```typescript
import { MCPServer, object, text } from "mcp-use/server";
import { z } from "zod";

const gateway = new MCPServer({
  name: "mcp-gateway",
  version: "1.0.0",
  description: "Gateway composing multiple upstream MCP servers",
});

// proxy() is async (v1.21.0+). MUST be awaited before listen() — otherwise the
// HTTP server starts before the upstream connections are ready and the first
// tools/list returns an empty list.
await gateway.proxy({
  github: {
    command: "npx",
    args: ["-y", "@modelcontextprotocol/server-github"],
    env: { GITHUB_PERSONAL_ACCESS_TOKEN: process.env.GITHUB_TOKEN ?? "" },
  },
  filesystem: {
    command: "npx",
    args: ["-y", "@modelcontextprotocol/server-filesystem", "./data"],
  },
  db: {
    url: "https://db-mcp.internal:3001/mcp",
  },
});

// Gateway-only tool, available alongside all proxied tools.
gateway.tool(
  {
    name: "health",
    description: "Check upstream MCP servers",
    schema: z.object({}),
  },
  async () => {
    return object({
      servers: ["github", "filesystem", "db"],
      gateway: "ok",
      timestamp: new Date().toISOString(),
    });
  }
);

// Optional: HTTP middleware (request log).
gateway.use(async (c, next) => {
  const start = Date.now();
  await next();
  console.log(`${c.req.method} ${c.req.url} ${Date.now() - start}ms`);
});

// Optional: MCP operation middleware (audit every proxied tool call).
gateway.use("mcp:tools/call", async (ctx, next) => {
  const start = Date.now();
  const result = await next();
  console.log(`tools/call ${ctx.params.name} ${Date.now() - start}ms`);
  return result;
});

await gateway.listen(parseInt(process.env.PORT || "3000", 10));
```

## How proxied tool names look

Upstream tools are namespaced by their key:

| Upstream tool | Visible at gateway as |
|---|---|
| `get_file_contents` from `github` | `github_get_file_contents` |
| `read_file` from `filesystem` | `filesystem_read_file` |
| `query` from `db` | `db_query` |

The gateway's own `health` tool is not namespaced.

## Run

```bash
GITHUB_TOKEN=ghp_... npm run dev
```

## Test

```bash
# tools/list — proxied tools and the local health tool both appear
curl -N -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" -H "Accept: text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

# call a proxied tool
curl -N -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" -H "Accept: text/event-stream" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"github_search_repositories","arguments":{"query":"language:typescript stars:>1000","perPage":5}}}'

# call the gateway-only tool
curl -N -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" -H "Accept: text/event-stream" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"health","arguments":{}}}'
```

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `tools/list` returns only `health` | `proxy()` not awaited; upstreams missing | Add `await` before `gateway.proxy(...)` |
| Proxied tool fails with `connection closed` | Upstream stdio process crashed | Set `env`, verify `command` runs standalone |
| Duplicate tool names | Two upstreams expose the same name | They are differentiated by the namespace key — use distinct keys |
| `listen()` hangs | Upstream HTTP server unreachable | Check the `url` and that the upstream MCP path is `/mcp` |

## Audit logging

The `mcp:tools/call` middleware above logs every proxied tool call. Persist the entries to a file or a database for compliance review. See `../31-canonical-examples/07-mcp-multi-server-hub.md` for the full reference.

## See also

- Hub canonical example: `../31-canonical-examples/07-mcp-multi-server-hub.md`
- Custom routes alongside `proxy()`: `../17-advanced/`
- Side-car versus gateway: `../29-templates/06-side-car-existing-app.md`
