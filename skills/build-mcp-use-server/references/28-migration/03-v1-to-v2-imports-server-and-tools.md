# Imports, Server, and Tool Registration

*Read this when migrating tool registration syntax from v1 to v2.*

## Step 1: Update imports

**v1**:
```typescript
import { MCPServer, text, object, error } from "mcp-use/server";
```

**v2**:
```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";
```

`mcp-use/server` no longer exists. Import `MCPServer` from root. Response helpers (`text`, `object`) are deprecated shims; prefer raw MCP envelopes.

## Step 1b: The `Logger` root API is removed

v1's application logger is not exported from v2. `Logger`, `Logger.get(name)`, `Logger.configure(...)`, `Logger.setDebug(level)`, and the default `logger` instance **do not exist** in beta.66 — v2's only root logging exports are `requestLogger` (Fetch middleware) and the built-in `logging` constructor option.

**v1**:
```typescript
import { Logger } from "mcp-use";
const log = Logger.get("startup");
Logger.configure({ level: "debug" });
Logger.setDebug(2);
log.info("Starting");
log.warn("slow path");
log.error("failed", err);
```

**v2** — pick by *where the log must go*:

| v1 use | v2 destination |
|---|---|
| Server-side startup/diagnostic logs | Your own logger (`console`, `pino`, Winston, Sentry). mcp-use does not provide one. |
| HTTP request logging | Constructor `logging: { enabled?: boolean, level?: "info" \| "debug" \| "trace" }`, or env `MCP_USE_LOG_LEVEL`. |
| Logs the *client* should see | `ctx.sendLog(level, data, loggerName?)` inside a tool callback — an MCP `notifications/message` to the connected client, not a server sink. |
| Custom Fetch request logging | `requestLogger({...})` composed around `server.fetch` via `composeFetch` (not `server.use()`). |

```typescript
import { MCPServer } from "mcp-use";
import pino from "pino";

const log = pino({ name: "startup" }); // own logger, replaces Logger.get

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  logging: { level: "debug" }, // framework request logging
});

export const work = server.tool({ name: "work", inputSchema: ..., outputSchema: ... }, async (input, ctx) => {
  log.info("work started");                 // server-side only
  await ctx.sendLog("info", { stage: "start" }); // delivered to the connected client
  return { content: [...], structuredContent: {...} };
});
```

`ctx.sendLog()` is client-facing and fires unconditionally — never route secrets through it. See `../15-logging/02-ctx-sendlog.md`.

## Step 1c: Mechanical constructor/config renames

These v1 `ServerConfig` fields fail as **type errors** in v2 — an import scan will not catch them. Rename or remove:

| v1 field | v2 status | Action |
|---|---|---|
| `baseUrl` | **Removed** | Delete it. The public origin is runtime config (`MCP_URL` env or request origin), not a constructor field. The path comes from `basePath`. |
| `cors.allowMethods` | → `cors.methods` | Rename |
| `cors.allowHeaders` | → `cors.allowedHeaders` | Rename |
| `cors.exposeHeaders` | **Removed** | Delete — v2 `CorsOptions` has no exposure field (`cors?: { enabled?, origin?, methods?, allowedHeaders?, credentials? }`). |
| `sessionStore` / `streamManager` / `stateless: false` / `sessionIdleTimeoutMs` | **Removed** | See `07-v1-to-v2-sessions-transports-stdio-sse.md`. |

```typescript
// v1
const server = new MCPServer({
  name, version,
  baseUrl: "https://api.example.com",
  cors: { allowMethods: ["POST"], allowHeaders: ["authorization"], exposeHeaders: ["mcp-session-id"] },
});

// v2
const server = new MCPServer({
  name, version,
  basePath: "/mcp",                       // path only; origin is env/runtime
  cors: { methods: ["POST"], allowedHeaders: ["authorization"], credentials: true },
});
// MCP_URL=https://api.example.com npm start   ← public origin lives here
```

Scan for all of them: `grep -rnE 'baseUrl|allowMethods|allowHeaders|exposeHeaders|sessionStore|streamManager|sessionIdleTimeout|stateless' src/ index.ts`.

## Step 2: Server constructor

**v1**:
```typescript
const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  oauth: oauthAuth0Provider(...), // import from "mcp-use/server"
});
```

**v2**:
```typescript
import { MCPServer } from "mcp-use";
// OAuth moved to separate imports — see 05-v1-to-v2-auth.md

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  // oauth config here if used (see section 05)
});
```

## Step 3: Tool registration — definition-first callback

**v1** — Inline schema + callback as `cb` field:
```typescript
server.tool({
  name: "weather",
  description: "Get weather",
  schema: z.object({ city: z.string() }),
  cb: async ({ city }) => text(await fetchWeather(city)),
});
```

**v2** — Separate definition (arg 1) and callback (arg 2):
```typescript
export const weather = server.tool(
  {
    name: "weather",
    description: "Get weather",
    inputSchema: z.object({ city: z.string() }),
    outputSchema: z.object({ forecast: z.string() }),
  },
  async ({ city }) => {
    const forecast = await fetchWeather(city);
    return {
      content: [{ type: "text", text: JSON.stringify({ forecast }) }],
      structuredContent: { forecast },
    };
  }
);
```

**Changes**:
- `schema` → `inputSchema` (matches MCP wire field name; `schema` still works as alias but is deprecated)
- **Add `outputSchema`** (required if tool has a View; enables client-side validation)
- **Export as const** (required for `mcp-env.d.ts` View type generation)
- Callback is **2nd argument**, not `cb` field
- Return raw `{ content, structuredContent }` instead of `text(...)` helper

**Do not chain** `server.tool(...).tool(...)`. v1's `MCPServer.tool()` returned `this` for chaining; v2's `tool()` returns a `ToolRef` (the value you export for View typing), which has no `.tool()` method. Call `server.tool(...)` once per statement instead.

## Step 4: Export every static tool

All tools declared at module level must be exported:

```typescript
// ✓ Correct
export const search = server.tool({ name: "search", ... }, async (...) => {...});
export const details = server.tool({ name: "details", ... }, async (...) => {...});

// ✗ Not exported — View typing breaks
const dynamic = server.tool({ name: "dynamic", ... }, async (...) => {...});

// ✓ Re-export from other modules
export { getTrending } from "./tools/trending.js";
```

Dynamic tools (from loops, config, OpenAPI) cannot be exported as `ToolRef`. Call them from Views with:
```typescript
import { useDynamicTool } from "mcp-use/react";
const lookup = useDynamicTool<InputType, OutputType>("tool-name");
```

## Step 5: Resources and templates

Static resources: v1's static callback received only request context (`(ctx)`) and examples often used no arguments. v2 adds the requested `URL` as the first parameter and moves context to the second: `(uri, ctx)`.

**v1**:
```typescript
server.resource(
  { name: "settings", uri: "app://settings", mimeType: "application/json" },
  async () => text(JSON.stringify({ theme: "dark" })),
);
```

**v2**:
```typescript
server.resource(
  { name: "settings", uri: "app://settings", mimeType: "application/json" },
  async (uri, ctx) => ({
    contents: [{ uri: uri.href, mimeType: "application/json", text: JSON.stringify({ theme: "dark" }) }],
  }),
);
```

Resource templates: v1.34.5 accepted both a legacy nested `resourceTemplate: { uriTemplate, callbacks }` shape and a newer flat `uriTemplate` + `callbacks` overload. v2 keeps only the flat form, moves `callbacks.complete` to top-level `complete`, and standardizes the reader as `(uri, params, ctx)`. Inferred template values are `string | string[]` (RFC 6570 expressions can expand to one or many).

**v1**:
```typescript
server.resourceTemplate(
  {
    name: "user",
    resourceTemplate: {
      uriTemplate: "users://{id}",
      callbacks: {
        complete: { id: async (value) => ["alice", "bob"].filter((id) => id.startsWith(value)) },
      },
    },
  },
  async (uri, { id }) => text(`User ${id}`),
);
```

**v2**:
```typescript
server.resourceTemplate(
  {
    name: "user",
    uriTemplate: "users://{id}",              // Flattened — no nested `resourceTemplate` field
    complete: {                                 // Flattened — no nested `callbacks` field
      id: async (value) => ["alice", "bob"].filter((id) => id.startsWith(value)),
    },
  },
  async (uri, { id }, ctx) => ({                // Canonical v2 signature
    contents: [{ uri: uri.href, text: `User ${String(id)}` }],
  }),
);
```

## Step 6: Prompts

v1 already deprecated the array-style `args: [{ name, type, required? }]` in favor of a single `schema` field (both existed side by side in v1). v2 drops `args` entirely — `schema` is the only option — and moves the callback to the second argument like tools:

**v1**:
```typescript
server.prompt({
  name: "review",
  schema: z.object({ code: z.string() }),
  cb: async ({ code }) => text(`Review this code:\n${code}`),
});
```

**v2**:
```typescript
server.prompt(
  { name: "review", schema: z.object({ code: z.string() }) },
  async ({ code }, ctx) => ({
    messages: [{ role: "user", content: { type: "text", text: `Review this code:\n${code}` } }],
  }),
);
```

`completable()` still works the same way, with one ordering rule: apply Zod field refinements (`.min()`, `.regex()`, etc.) **before** wrapping with `completable()`, not after — `completable()` supplies autocomplete suggestions but does not itself constrain valid values.

## Step 7: Response shape — raw MCP envelopes

**v1** — Helpers:
```typescript
return text("Result");
return object({ count: 5, items: [] });
return error("Something failed");
return widget({ props: {...}, output: text("...") });
```

**v2** — Raw envelopes:
```typescript
// Text result
return {
  content: [{ type: "text", text: "Result" }],
  structuredContent: { /* structured data matching outputSchema */ },
};

// Error
return {
  content: [{ type: "text", text: "Something failed" }],
  isError: true,
};

// Multiple content blocks (markdown + object)
return {
  content: [
    { type: "text", text: "## Summary\n..." },
    { type: "text", text: JSON.stringify({ data: [...] }) },
  ],
  structuredContent: { data: [...] },
};
```

**Why**: Raw envelopes are type-safe and align with MCP spec. Helpers (`text()`, `object()`, etc.) remain as **deprecated upgrade shims only**; beta.66 does not specify a removal release.

## Step 8: Deprecated helpers — if you must use them

Helpers are exported for backward compatibility only:

```typescript
import { text, object, array, error, markdown, mix, image, audio, binary } from "mcp-use";

// These work but are deprecated:
return text("Hello");  // Alias for { content: [{ type: "text", text: "Hello" }] }
return error("Failed"); // Alias for { content: [...], isError: true }
```

Migrate away from them and prefer raw envelopes; beta.66 does not specify when the shims will be removed.

## Step 9: Tool annotations (unchanged)

Annotations remain, no syntax change:

```typescript
export const destructive = server.tool(
  {
    name: "delete-item",
    inputSchema: z.object({ id: z.string() }),
    outputSchema: z.object({}),
    annotations: {
      destructiveHint: true,
      readOnlyHint: false,
      openWorldHint: false,
      idempotentHint: true,
    },
  },
  async ({ id }) => ({ content: [...], structuredContent: {} })
);
```

## Step 10: What about `visibility`?

**New in v2**: Tool `visibility` field (for MCP Apps):

```typescript
export const hidden = server.tool(
  {
    name: "internal",
    visibility: "app", // model-hidden, View-callable only
    inputSchema: z.object({}),
    outputSchema: z.object({}),
  },
  async () => ({ content: [...], structuredContent: {} })
);
```

Values: omit the field for the host default (normally model-callable and app-visible); set `"model"` to declare model visibility explicitly; set `"app"` for an app-private helper callable from a View while the host hides it from the model.

---

**Next**: See `04-v1-to-v2-responses-and-helpers.md` for detailed response envelope patterns.
