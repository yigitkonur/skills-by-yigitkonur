# mcp-use v2 vs @modelcontextprotocol/server

*Read this when deciding whether to use mcp-use or build directly on the official MCP SDK, or migrating from SDK to mcp-use.*

## Which official SDK mcp-use wraps

mcp-use v2 wraps `@modelcontextprotocol/server` — the **v2 split-package** official SDK (`McpServer`, `registerTool`, `createMcpHandler`, published separately from `@modelcontextprotocol/client` and `@modelcontextprotocol/core`). It does **not** wrap the classic single-package `@modelcontextprotocol/sdk` (v1, `Server` + `setRequestHandler(CallToolRequestSchema, ...)`). `mcp-use`'s own `package.json` lists `@modelcontextprotocol/server` as a direct dependency; internally `MCPServer` constructs an `SdkMcpServer` (the split-package `McpServer`) and drives it through `createMcpHandler`.

If your comparison baseline is the classic `@modelcontextprotocol/sdk` v1 (still the npm `latest` tag), treat this file's "SDK" column as the v2 split package, not v1 — v1's API (`new Server(...)`, `setRequestHandler("tools/call", ...)`, `StdioServerTransport`) is a different, older surface. See sister skill `convert-mcp-sdk-v1-to-v2` for the v1→v2 SDK migration itself.

## What mcp-use adds

mcp-use wraps `@modelcontextprotocol/server` (v2) and provides:

| Feature | Official SDK (`@modelcontextprotocol/server`) | mcp-use | Benefit |
|---|---|---|---|
| **HTTP transport** | `createMcpHandler()` + framework adapter (Express/Hono via `@modelcontextprotocol/node`) | Streamable HTTP built in + runtime adapters | Less wiring; works serverless |
| **Stateless model** | Per-request factory (`McpServerFactory` passed to `createMcpHandler`) | Per-request MCP instance | Same core model; mcp-use adds the HTTP/runtime layer on top |
| **Definition-first tools** | `registerTool(name, config, callback)` | `server.tool(definition, callback)` | Similar shape; mcp-use unifies schema + view + CSP in one definition |
| **Runtime adapters** | Node/Express/Hono adapters (official) | Node, Next.js, edge/fetch, Hono | mcp-use adds Next.js and generic Fetch adapters |
| **OAuth sugar** | Not in the SDK — wire your own bearer verification | Provider shortcuts (Clerk, Supabase, Auth0, ...) | No boilerplate |
| **React hooks** | N/A | `useToolContext`, `useCallTool`, `useViewState`, ... (from `mcp-use/react`) | Interactive views without glue |
| **MCP Apps** | Not in SDK | Full React view support + CSP | Rich UIs with form/URL elicitation |
| **Proxy composition** | Not in SDK | `server.proxy()` | Gateway patterns; namespace management |
| **OpenAPI generation** | Not in SDK | `MCPServer.fromOpenAPI()` | Bootstrap from existing APIs |
| **CLI tooling** | None | create-mcp-use-app, dev, build, deploy | Scaffold + dev + production pipeline |

## When to use mcp-use

✅ **Use mcp-use if:**
- Building production servers for cloud (Vercel, Cloudflare, etc.)
- Need HTTP or edge runtimes (no Node stdio)
- Want interactive views or forms (MCP Apps)
- Deploying to shared infrastructure (stateless model)
- Using OAuth with known providers
- Building gateways or proxying servers

## When to use the SDK directly

✅ **Use `@modelcontextprotocol/server` directly if:**
- Targeting only Node.js + stdio transport
- Building internal CLIs or desktop apps (not cloud)
- Need direct protocol control unavailable in mcp-use (e.g., `Server`-level access, or the `tasks/*` task-primitive and `server/discover` methods, neither of which mcp-use's `ctx` exposes)
- Prefer minimal dependencies

For SDK-direct work, see sister skill `build-mcp-server-sdk-v2`.

## Key API differences

The comparison blocks below are focused fragments, not standalone projects. Each fragment names its assumed surrounding value (such as an existing `server` or framework-provided `request`); file-specific adapter examples are labeled with their destination path.

### Server instantiation

```typescript
// Official SDK (v2 split package)
import { McpServer } from "@modelcontextprotocol/server";
const server = new McpServer({ name: "my-server", version: "1.0.0" });

// mcp-use
import { MCPServer } from "mcp-use";
const server = new MCPServer({ name: "my-server", version: "1.0.0" });
```

### Tool registration

```typescript
// Official SDK
server.registerTool(
  "greet",
  {
    title: "Greet",
    description: "Say hello",
    inputSchema: z.object({ name: z.string() }),
  },
  async ({ name }) => ({
    content: [{ type: "text", text: `Hello, ${name}` }],
  })
);

// mcp-use (definition-first)
server.tool(
  {
    name: "greet",
    inputSchema: z.object({ name: z.string() }),
  },
  async ({ name }) => ({
    content: [{ type: "text", text: `Hello, ${name}` }],
  })
);
```

Both are definition-first and callback-based — the SDK already moved to `registerTool` in v2. mcp-use's `server.tool()` folds view/CSP config into the same definition object. mcp-use ships `text()`/`object()`/`widget()`/... response-shape helpers, but all of them are `@deprecated` in the current dist typings — prefer returning a plain `CallToolResult` object (`{ content, structuredContent?, isError? }`) directly, as shown above.

### Transport

```typescript
// Official SDK fragment — `createOfficialServer()` builds a fresh McpServer
import { createMcpHandler } from "@modelcontextprotocol/server";
const handler = createMcpHandler(() => createOfficialServer()); // Web-standard Fetch handler
// Node/Express/Hono wiring uses @modelcontextprotocol/node adapters.
// Stdio uses StdioServerTransport + server.connect(transport).

// mcp-use runtime fragments — `server` is an existing MCPServer
await server.listen(3000);              // Bind a Node HTTP listener
const response = await server.fetch(request); // Handle a Web Fetch Request

import { toNodeHandler } from "mcp-use/node";
const nodeHandler = toNodeHandler(server);
```

For Next.js, configuration wrapping and route handling belong in different files:

```typescript
// next.config.ts
import { withMcpUse } from "mcp-use/next";

export default withMcpUse();
```

```typescript
// app/api/mcp/route.ts
import { server } from "@/mcp/server";
import { createNextHandler } from "mcp-use/next";

export const { GET, POST, DELETE, OPTIONS } = createNextHandler(server);
```

Both center on a Fetch-standard HTTP handler (`createMcpHandler` in the SDK, `server.fetch` in mcp-use); mcp-use adds the Node listener, Next.js adapters, and stdio removal — v2 mcp-use serves Streamable HTTP only, no stdio.

### Context

```typescript
// Official SDK — second callback argument is a ServerContext
server.registerTool("greet", { inputSchema: z.object({ name: z.string() }) }, async (args, ctx) => {
  ctx.mcpReq.log(...)               // Send a log notification (deprecated SEP-2577; still functional)
  ctx.requestState                  // Multi-round state accessor
  ctx.signal                        // AbortSignal for cancellation
  ctx.send({ method: ..., params }) // Send a request related to this one
  ctx.notify(...)                   // Send a notification related to this one
  ctx.http?.authInfo                // Validated access token, HTTP transport only
});

// mcp-use
server.tool({...}, async (args, ctx) => {
  ctx.client.capabilities()        // Query client features
  ctx.auth.user.id                 // OAuth user (if enabled)
  await ctx.reportProgress(...)    // Send progress
  ctx.signal                       // AbortSignal for cancellation
  await ctx.sendNotification(...)  // Custom notifications
  ctx.requestState<MyState>()      // Read decoded multi-round state (codec)
});
```

Both SDKs pass a structured context as the second callback argument — the "SDK has no context" framing is v1-only. The SDK's `ctx.http?.authInfo` carries a validated token but no decoded user; mcp-use's `ctx.auth.user` builds on top of it via the OAuth provider shortcuts. mcp-use also exposes `ctx.client` (capability introspection) and `ctx.reportProgress`, which the bare SDK does not provide directly.

### OAuth

```typescript
// Official SDK
// No server-side OAuth in the SDK. Verify bearer tokens yourself and place the
// result on ctx.http.authInfo (HTTP transport only) — see build-mcp-server-sdk-v2.

// mcp-use
import { MCPServer } from "mcp-use";
import { oauthSupabaseProvider } from "mcp-use/oauth/supabase";
import { z } from "zod";

const authServer = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  oauth: oauthSupabaseProvider({ projectId: "example-project" }), // or Clerk, Auth0, etc.
});

authServer.tool(
  { name: "who-am-i", inputSchema: z.object({}) },
  async (_args, ctx) => ({
    content: [{ type: "text", text: `User: ${ctx.auth.user.id}` }],
  })
);
```

mcp-use includes auth provider shortcuts; the SDK requires custom bearer-token verification wired into the HTTP layer.

### Views (MCP Apps)

```typescript
// Official SDK
// No built-in view support; you manage React + CSP separately.

// mcp-use server fragment — assumes an existing `server`
import { z } from "zod";

const chartOutput = z.object({ data: z.array(z.number()) });

// Export the ToolRef so generated mcp-env.d.ts can type the view hook.
export const createChart = server.tool(
  {
    name: "create-chart",
    outputSchema: chartOutput,
    view: {
      name: "chart-viewer",
      description: "Interactive chart",
      csp: { connectDomains: ["https://api.example.com"] },
    },
  },
  async () => ({
    content: [{ type: "text", text: "Chart generated" }],
    structuredContent: { data: [12, 19, 7] },
  })
);
```

```tsx
// views/chart-viewer/view.tsx
import { useToolContext } from "mcp-use/react";

export default function ChartViewer() {
  const ctx = useToolContext<"create-chart">();

  if (ctx.status === "error") return <p>{ctx.error.message}</p>;
  if (ctx.status !== "ready") return <p>Generating chart…</p>;

  return <pre>{JSON.stringify(ctx.toolOutput.data, null, 2)}</pre>;
}
```

mcp-use integrates view scaffolding, CSP config, and React hooks; the SDK offers no view layer.

## Migration path: SDK → mcp-use

If moving existing SDK servers to mcp-use:

1. **Check transport:** SDK servers using stdio? Rewrite to HTTP (mcp-use default; v2 mcp-use has no stdio transport).
2. **Rewrite tools:** Replace `registerTool()` calls with `server.tool()` definitions (`inputSchema` becomes a `z.object({...})`, not a raw shape, for mcp-use's non-legacy overload).
3. **Update context:** Replace `ctx.mcpReq.*`/`ctx.http.authInfo` reads with mcp-use's `ctx.client`/`ctx.auth`/`ctx.requestState` equivalents.
4. **Add OAuth:** If you hand-rolled bearer verification, simplify via mcp-use's `oauth` config and a provider shortcut.
5. **Choose deployment:** Deploy to Vercel, Cloudflare, etc., using mcp-use adapters.

See `build-mcp-server-sdk-v2` and `convert-mcp-sdk-v1-to-v2` for detailed SDK guidance.

## Performance considerations

- **mcp-use:** Builds directly on the official SDK's `McpServer`/`createMcpHandler`; the added layer is request routing, context translation, and view/OAuth wiring — not a second protocol implementation. No published benchmark numbers exist for either package as of beta.66; do not cite a specific per-request overhead figure without a measured source.
- **SDK direct:** Same core dispatch path, without mcp-use's HTTP-adapter and context-translation layer. Appropriate when you need to shave that layer off, or need SDK surface mcp-use doesn't expose (e.g., raw `Server`/`Protocol` access, the `tasks/*` task-primitive and `server/discover` methods).
- **Stateless scaling:** Both are per-request-factory models under HTTP (`McpServerFactory` in the SDK, `MCPServer` instance construction in mcp-use) — horizontal scaling comes from that shared design, not from mcp-use alone.

## Summary

**mcp-use is the recommended path for cloud MCP servers.** It trades minor protocol abstraction for major developer experience gains (views, OAuth, deploy tooling, HTTP transport) on top of the same official `@modelcontextprotocol/server` core. The SDK directly is appropriate for stdio-only, maximum-control, or minimal-dependency scenarios.
