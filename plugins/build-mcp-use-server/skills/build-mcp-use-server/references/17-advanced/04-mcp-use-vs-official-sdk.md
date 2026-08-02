# mcp-use v2 vs @modelcontextprotocol/sdk

*Read this when deciding whether to use mcp-use or build directly on the official MCP SDK, or migrating from SDK to mcp-use.*

## What mcp-use adds

mcp-use wraps `@modelcontextprotocol/sdk` and provides:

| Feature | SDK | mcp-use | Benefit |
|---|---|---|---|
| **HTTP transport** | Stdio only | Streamable HTTP + runtime adapters | Cloud-friendly; works serverless |
| **Stateless model** | Session-based | Per-request MCP instance | Scales horizontally; no session storage needed |
| **Definition-first tools** | Callback + schema pair | Unified definition + callback | Single registration call; cleaner code |
| **Runtime adapters** | N/A | Node, Next.js, edge/fetch, Hono | Write once, deploy anywhere |
| **OAuth sugar** | Middleware pattern | Provider shortcuts (Clerk, Supabase, Auth0, ...) | No boilerplate |
| **React hooks** | N/A | `useWidget`, `useCallTool`, `useViewState`, ... | Interactive views without glue |
| **MCP Apps** | Not in SDK | Full React view support + CSP | Rich UIs with form/URL elicitation |
| **Proxy composition** | Not in SDK | `server.proxy()` + optional `@mcp-use/client` | Gateway patterns; namespace management |
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

✅ **Use `@modelcontextprotocol/sdk` directly if:**
- Targeting only Node.js + stdio transport
- Building internal CLIs or desktop apps (not cloud)
- Need direct protocol control unavailable in mcp-use
- Prefer minimal dependencies

For SDK-direct work, see sister skill `build-mcp-server-sdk-v2`.

## Key API differences

### Server instantiation

```typescript
// SDK
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
const server = new Server({ name: "my-server" });

// mcp-use
import { MCPServer } from "mcp-use";
const server = new MCPServer({ name: "my-server" });
```

### Tool registration

```typescript
// SDK
server.setRequestHandler(
  "tools/call",
  async ({ name, arguments: args }) => ({
    content: [{ type: "text", text: "result" }],
  })
);

// mcp-use (definition-first)
server.tool(
  {
    name: "greet",
    inputSchema: z.object({ name: z.string() }),
  },
  async ({ name }) => text(`Hello, ${name}`)
);
```

mcp-use registers tools as definitions with callbacks; SDK requires manual handler dispatch.

### Transport

```typescript
// SDK (stdio only)
const transport = new StdioServerTransport({ ... });
const mcp = new Server({ ..., transport });

// mcp-use (HTTP + adapters)
await server.listen(3000);        // Node
server.fetch(request);             // Fetch API (Cloudflare, Deno, edge)
toNodeHandler(server)              // Convert to Node handler
withMcpUse(server)                 // Next.js app router
createNextHandler(server)          // Next.js API routes
```

mcp-use handles transport setup; SDK requires explicit transport class.

### Context

```typescript
// SDK
// No structured context; pass through handler closure

// mcp-use
server.tool({...}, async (args, ctx) => {
  ctx.client.capabilities()        // Query client features
  ctx.auth.user.id                 // OAuth user (if enabled)
  await ctx.reportProgress(...)    // Send progress
  ctx.signal                       // AbortSignal for cancellation
  await ctx.sendNotification(...)  // Custom notifications
  ctx.requestState                 // Multi-round state (codec)
});
```

mcp-use provides a rich context object; SDK leaves context wiring to you.

### OAuth

```typescript
// SDK
// Middleware + token verification — write from scratch

// mcp-use
new MCPServer({
  oauth: oauthSupabaseProvider(),  // or Clerk, Auth0, etc.
})

// In handler:
async (args, ctx) => {
  const user = ctx.auth.user.id;  // Immediate access
}
```

mcp-use includes auth provider shortcuts; SDK requires custom middleware.

### Views (MCP Apps)

```typescript
// SDK
// No built-in view support; you manage React + CSP separately

// mcp-use
server.tool({
  name: "create-chart",
  view: {
    name: "chart-viewer",
    description: "Interactive chart",
    csp: { connectDomains: ["api.example.com"] },
  },
}, async (args) => widget({...}));

// resources/chart-viewer/view.tsx
import { useWidget } from "mcp-use/react";
export default () => {
  const { props } = useWidget();
  return <Chart data={props} />;
};
```

mcp-use integrates view scaffolding, CSP config, and React hooks; SDK offers no view layer.

## Migration path: SDK → mcp-use

If moving existing SDK servers to mcp-use:

1. **Check transport:** SDK servers using stdio? Rewrite to HTTP (mcp-use default).
2. **Rewrite tools:** Replace handler dispatch with `server.tool()` definitions.
3. **Update context:** If handlers accessed request context, wire it via mcp-use context parameter.
4. **Add OAuth:** If middleware-based auth, simplify via `oauth` config.
5. **Choose deployment:** Deploy to Vercel, Cloudflare, etc., using mcp-use adapters.

See `build-mcp-server-sdk-v2` and `convert-mcp-sdk-v1-to-v2` for detailed SDK guidance.

## Performance considerations

- **mcp-use:** Lean abstraction (~20ms per request for registration + dispatch). Stateless scaling is horizontal.
- **SDK direct:** Raw protocol handling; no overhead. Suitable for high-throughput stdio servers.

Both are fast enough for LLM-powered applications.

## Summary

**mcp-use is the recommended path for cloud MCP servers.** It trades minor protocol abstraction for major developer experience gains (views, OAuth, deploy tooling, HTTP transport). SDK is appropriate for stdio-only or maximum-control scenarios.
