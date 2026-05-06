# Server Proxy and Gateway Composition

`server.proxy()` aggregates multiple upstream MCP servers behind one endpoint. Use it to build a single gateway that fronts local stdio processes, remote HTTP servers, and pre-authenticated `MCPSession` instances — all namespaced to prevent collisions.

> **Version requirement (mcp-use ≥ v1.21.0):** `MCPServer.proxy()` was introduced in v1.21.0 and is **async** in the v1.26.0 package declarations (`proxy(...): Promise<void>`). Always `await` it before `server.listen()` because `proxy()` mounts child sessions and introspects tools/resources/prompts before the gateway should accept traffic.

---

## 1. Config-Based Proxy (Default)

Pass a record of `namespace → target` and let the SDK manage child connections.

```typescript
import { MCPServer, object } from "mcp-use/server";
import path from "node:path";

const gateway = new MCPServer({
  name: "mcp-gateway",
  version: "1.0.0",
  description: "Gateway composing multiple MCP servers",
});

// proxy() is async — await it before listen()
await gateway.proxy({
  // Local stdio child (TypeScript)
  database: {
    command: "tsx",
    args: [path.resolve(__dirname, "./db-server.ts")],
  },

  // Local stdio child (Python via uv)
  weather: {
    command: "uv",
    args: ["run", "weather_server.py"],
  },

  // Remote HTTP child
  inventory: {
    url: "https://inventory.example.com/mcp",
  },
});

// Gateway-level tools coexist with proxied tools
gateway.tool(
  { name: "health", description: "Check upstream servers" },
  async () => object({
    servers: ["database", "weather", "inventory"],
    status: "healthy",
  })
);

await gateway.listen(3000);
```

Child tools are auto-prefixed: `database_query`, `weather_get_forecast`, `inventory_list`.

---

## 2. Parameter Reference

`server.proxy(config)` — config form:

| Field | Type | Required | Description |
|---|---|---|---|
| `config` | `Record<string, any>` | yes | Map of namespace → target. |
| `config[ns].command` | `string` | no | Local executable. |
| `config[ns].args` | `string[]` | no | Args for `command`. |
| `config[ns].env` | `Record<string, string>` | no | Env vars for child process. |
| `config[ns].url` | `string` | no | Remote MCP HTTP URL (mutually exclusive with `command`). |
| `config[ns].headers` | `Record<string, string>` | no | Extra HTTP headers for remote targets. |
| `config[ns].authToken` | `string` | no | Bearer token shortcut for remote HTTP targets. |
| `config[ns].fetch` | `typeof fetch` | no | Custom fetch implementation for remote HTTP targets. |
| `config[ns].authProvider` | `unknown` | no | OAuth/auth provider passed to the HTTP connector. |
| `config[ns].transport` | `"http" \| "sse"` | no | Force Streamable HTTP or SSE transport. |
| `config[ns].preferSse` | `boolean` | no | Prefer SSE when both transports are possible. |
| `config[ns].disableSseFallback` | `boolean` | no | Disable HTTP-to-SSE fallback. |
| `config[ns].clientInfo` | `ClientInfo` | no | Override client metadata sent to the upstream. |
| `config[ns].onSampling` | callback | no | Per-server sampling callback. |
| `config[ns].onElicitation` | callback | no | Per-server elicitation callback. |
| `config[ns].onNotification` | callback | no | Per-server notification callback. |

`server.proxy(session, options)` — session form (covered in `02-session-based-proxy.md`):

| Field | Type | Required | Description |
|---|---|---|---|
| `session` | `MCPSession` | yes | Pre-authenticated client session. |
| `options.namespace` | `string` | yes | Prefix for all proxied components. |

---

## 3. How Proxying Works

1. **Introspection** — proxy calls `listTools`, `listResources`, `listPrompts` on each child during the `await server.proxy(...)` step.
2. **Schema translation** — raw JSON Schemas from children are converted to runtime Zod for validation on the gateway.
3. **Namespacing** — every component name is prefixed with the namespace key (e.g. `database_query`).
4. **Relay** — incoming tool calls forward to the matching child; responses bubble back.
5. **State sync** — the gateway listens for `notifications/tools/list_changed`, `notifications/resources/list_changed`, and `notifications/prompts/list_changed` from children and forwards list-changed notifications to connected aggregator clients.
6. **Reverse-channel passthrough** — sampling, elicitation, and progress events from children are routed back to the originating user's client transparently.

---

## 4. Resource URI Namespacing

To prevent URI collisions, the v1.26.0 package prepends the namespace and URL-encodes the original URI:

| Child URI | Gateway-exposed URI |
|---|---|
| `app://settings` (in `weather` ns) | `weather://app%3A%2F%2Fsettings` |
| `db://schema` (in `database` ns) | `database://db%3A%2F%2Fschema` |

When a client reads the namespaced URI, the gateway reads the original child URI captured during startup introspection.

> **Docs/package disagreement:** the canonical proxy doc shows unencoded examples such as `weather://app://settings`; `mcp-use@1.26.0` runtime uses `${namespace}://${encodeURIComponent(res.uri)}`. Package behavior wins. Sources: https://manufact.com/docs/typescript/server/proxy and `dist/chunk-CQTMUGLH.js`.

---

## 5. Multi-Server Hub Pattern (Production)

```typescript
import { MCPServer } from "mcp-use/server";

const hub = new MCPServer({ name: "hub", version: "1.0.0" });

const PROXY_CONFIG = {
  weather: { url: "https://weather-mcp.example.com/mcp" },
  local: { command: "node", args: ["./local-server.js"] },
};

await hub.proxy(PROXY_CONFIG);

// Hono middleware applies to gateway-level routes only — proxied calls
// are routed through the MCP transport, not custom HTTP routes.
hub.use("/api/*", async (c, next) => { /* auth, audit */ await next(); });
hub.get("/api/health", (c) => c.json({ ok: true }));

await hub.listen(3000);
```

See `canonical-anchor.md` for the reference repo layout.

---

## 6. Gotchas

| Issue | Cause | Fix |
|---|---|---|
| Gateway tools missing on first request | `proxy()` not awaited | Always `await server.proxy(...)` before `listen()`. |
| Tool name collision across children | Two children expose same tool | Use distinct namespace keys; collisions resolved by prefix. |
| Child sampling/elicitation lost | Gateway version < v1.21.0 | Upgrade to ≥ v1.21.0. |
| Remote child auth fails | No headers/token on HTTP target | Add `headers` or `authToken`; use the session form when you need manual lifecycle. |
| Child list changes not forwarded | Stale gateway client connections | Reconnect; gateway only forwards to live clients. |

---

## 7. Cross-References

- **Session-based proxy with custom auth headers** → `02-session-based-proxy.md`
- **mcp-use vs official SDK proxy support** → `03-mcp-use-vs-official-sdk.md`
- **Reference implementation** → `canonical-anchor.md`
- **Per-call client capability checks** → `../16-client-introspection/01-overview.md`
- **Autocomplete on prompts (`completable()`)** → `../07-prompts/04-completable-arguments.md`

---

**Canonical doc:** https://manufact.com/docs/typescript/server/proxy
