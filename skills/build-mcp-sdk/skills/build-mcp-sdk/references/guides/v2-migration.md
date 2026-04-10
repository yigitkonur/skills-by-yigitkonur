# v2 Migration Guide (Source-Verified)

Source-verified against both `v1.x` branch (v1.27.0) and `main` branch (v2.0.0-alpha.0) of `modelcontextprotocol/typescript-sdk`.

**Do not use v2 in production.** Use `@modelcontextprotocol/sdk@^1.27.0` (single package, stable).

## Package split

| v1 (stable) | v2 (alpha) |
|---|---|
| `@modelcontextprotocol/sdk` | `@modelcontextprotocol/server` |
| | `@modelcontextprotocol/client` |
| | `@modelcontextprotocol/core` |
| | `@modelcontextprotocol/node` (HTTP transport for Node.js) |
| | `@modelcontextprotocol/express` (Express adapter) |
| | `@modelcontextprotocol/hono` (Hono adapter) |

### Import path changes

```typescript
// v1 — subpath exports from single package
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { McpError, ErrorCode } from "@modelcontextprotocol/sdk/types.js";

// v2 — separate packages, no subpath exports needed
import { McpServer, StdioServerTransport } from "@modelcontextprotocol/server";
import { NodeStreamableHTTPServerTransport } from "@modelcontextprotocol/node";
import { Client } from "@modelcontextprotocol/client";
import { ProtocolError, ProtocolErrorCode } from "@modelcontextprotocol/core";
```

## Schema system: Zod dual-version → Zod v4 only

v1 supports both Zod v3 and v4 via a compatibility shim (`zod-compat.ts`) using runtime detection (`._zod` property check). v2 uses Zod v4 exclusively — no compatibility layer.

```typescript
// v1 — accepts ZodRawShape (plain object) OR full Zod schema
import { z } from "zod";
server.registerTool("greet", {
  inputSchema: { name: z.string() },  // ZodRawShape shorthand works
}, async ({ name }, extra) => { ... });

// v2 — requires full z.object() schema
import * as z from "zod/v4";
server.registerTool("greet", {
  inputSchema: z.object({ name: z.string() }),  // must be full schema
}, async ({ name }, ctx) => { ... });
```

**Type changes:**
| v1 | v2 |
|---|---|
| `ZodRawShapeCompat = Record<string, AnySchema>` | Removed entirely |
| `AnySchema = z3.ZodTypeAny \| z4.$ZodType` (union) | `AnySchema = z.core.$ZodType` (single) |
| `SchemaOutput<S>` branches v3/v4 | `z.output<T>` directly |
| JSON Schema output: Draft-7 (via `zod-to-json-schema`) | JSON Schema 2020-12 (via `z.toJSONSchema()`) |

## Handler context: `RequestHandlerExtra` → `ServerContext`

The second argument to all handlers is restructured:

```typescript
// v1 — flat RequestHandlerExtra
server.registerTool("my-tool", config, async (args, extra) => {
  extra.signal;                    // AbortSignal
  extra.authInfo;                  // AuthInfo
  extra.sessionId;                 // string
  extra.requestId;                 // RequestId
  extra.requestInfo;               // HTTP request metadata
  extra.sendNotification(notif);   // send notification
  extra.sendRequest(req, schema);  // send request (sampling, elicitation)
  extra.closeSSEStream?.();        // close SSE stream
});

// v2 — structured ServerContext
server.registerTool("my-tool", config, async (args, ctx) => {
  ctx.mcpReq.signal;              // AbortSignal (moved)
  ctx.http?.authInfo;             // AuthInfo (moved under http)
  ctx.sessionId;                  // string (stays top-level)
  ctx.mcpReq.id;                  // RequestId (renamed)
  ctx.http?.req;                  // HTTP request metadata (renamed)
  ctx.mcpReq.notify(notif);      // send notification (renamed)
  ctx.mcpReq.send(req, schema);  // send request (renamed)
  ctx.http?.closeSSE?.();         // close SSE stream (renamed)
  // New convenience methods:
  ctx.mcpReq.log("info", data);             // structured logging
  ctx.mcpReq.elicitInput(params);           // request user input
  ctx.mcpReq.requestSampling(params);       // request LLM completion
});
```

### Complete field mapping

| v1 `extra` | v2 `ctx` | Notes |
|---|---|---|
| `extra.signal` | `ctx.mcpReq.signal` | |
| `extra.authInfo` | `ctx.http?.authInfo` | Moved under `http` |
| `extra.sessionId` | `ctx.sessionId` | Same |
| `extra.requestId` | `ctx.mcpReq.id` | Renamed |
| `extra._meta` | `ctx.mcpReq._meta` | Same |
| `extra.requestInfo` | `ctx.http?.req` | Renamed |
| `extra.sendNotification(n)` | `ctx.mcpReq.notify(n)` | Renamed |
| `extra.sendRequest(r, s)` | `ctx.mcpReq.send(r, s)` | Renamed |
| `extra.closeSSEStream?.()` | `ctx.http?.closeSSE?.()` | Renamed |
| `extra.closeStandaloneSSEStream?.()` | `ctx.http?.closeStandaloneSSE?.()` | Renamed |
| `extra.taskId` | `ctx.task?.id` | Moved under `task` |
| `extra.taskStore` | `ctx.task?.store` | Moved under `task` |
| N/A | `ctx.mcpReq.log(level, data, logger?)` | New |
| N/A | `ctx.mcpReq.elicitInput(params)` | New |
| N/A | `ctx.mcpReq.requestSampling(params)` | New |

### No-args tool handlers

```typescript
// v1 — no inputSchema: handler gets only extra
server.registerTool("status", {}, async (extra) => { ... });

// v2 — no inputSchema: handler gets only ctx (same pattern, renamed)
server.registerTool("status", {}, async (ctx) => { ... });
```

## Error handling changes

| v1 | v2 |
|---|---|
| `McpError(code, message, data?)` | `ProtocolError(code, message, data?)` (wire errors) |
| `ErrorCode` enum | `ProtocolErrorCode` enum |
| N/A | `SdkError` / `SdkErrorCode` (local SDK errors) |

## Request handler registration

```typescript
// v1 — pass Zod schema object
import { CallToolRequestSchema } from "@modelcontextprotocol/sdk/types.js";
server.server.setRequestHandler(CallToolRequestSchema, async (req, extra) => { ... });

// v2 — pass method string
server.server.setRequestHandler("tools/call", async (req, ctx) => { ... });
```

| v1 Schema | v2 Method string |
|---|---|
| `CallToolRequestSchema` | `"tools/call"` |
| `ListToolsRequestSchema` | `"tools/list"` |
| `CreateMessageRequestSchema` | `"sampling/createMessage"` |
| `ElicitRequestSchema` | `"elicitation/create"` |
| `SubscribeRequestSchema` | `"resources/subscribe"` |

## Transport changes

| v1 | v2 |
|---|---|
| `StreamableHTTPServerTransport` (Node.js built-in) | `NodeStreamableHTTPServerTransport` from `@modelcontextprotocol/node` |
| `WebStandardStreamableHTTPServerTransport` (web-standard) | Same name, now in `@modelcontextprotocol/server` |
| `SSEServerTransport` (deprecated) | Removed entirely |
| `createMcpExpressApp()` from SDK | `createMcpExpressApp()` from `@modelcontextprotocol/express` |
| N/A | `createMcpHonoApp()` from `@modelcontextprotocol/hono` |

### Framework adapters

v2 provides dedicated adapter packages:

```typescript
// Express
import { createMcpExpressApp } from "@modelcontextprotocol/express";
const app = createMcpExpressApp({ host: "127.0.0.1" });

// Hono (new in v2)
import { createMcpHonoApp } from "@modelcontextprotocol/hono";
const app = createMcpHonoApp({ host: "127.0.0.1" });
```

Both provide `hostHeaderValidation()` and `localhostHostValidation()` middleware.

## Auth changes

### Server-side auth removed

v2 **removes** all server-side OAuth exports: `mcpAuthRouter`, `OAuthServerProvider`, `requireBearerAuth`, auth handlers, error classes. Use `better-auth` or a dedicated authorization server.

### Client-side auth enhanced

v2 `OAuthClientProvider` gains new methods:

| New method | Purpose |
|---|---|
| `addClientAuthentication?` | Custom token-request auth (bypasses standard methods) |
| `validateResourceURL?` | Override RFC 8707 resource indicator |
| `invalidateCredentials?(scope)` | Granular credential invalidation |
| `prepareTokenRequest?(scope?)` | Grant-type agnostic token params |
| `saveDiscoveryState?` / `discoveryState?` | Cache RFC 9728 discovery |
| `clientMetadataUrl?` | SEP-991 URL-based client IDs |

### Client middleware system (new in v2)

```typescript
import { applyMiddlewares, withOAuth, withLogging, createMiddleware } from "@modelcontextprotocol/client";

const middleware = applyMiddlewares(
  withOAuth(oauthProvider),
  withLogging({ logger: console.error }),
  createMiddleware(async (next, url, init) => {
    // Custom middleware logic
    return next(url, init);
  }),
);
```

### Built-in auth providers

```typescript
import {
  ClientCredentialsProvider,
  PrivateKeyJwtProvider,
  StaticPrivateKeyJwtProvider,  // new in v2
} from "@modelcontextprotocol/client";
```

## Other breaking changes

| Area | v1 | v2 |
|---|---|---|
| Node.js | 18+ | 20+ |
| Module system | CJS + ESM | ESM only |
| Headers | `Record<string, string>` | Web Standard `Headers` |
| `callTool` result validation | Manual | Auto-validates `structuredContent` against `outputSchema` |
| `listTools` capability missing | Throws | Returns empty array (unless `enforceStrictCapabilities`) |
| Connect with existing session | N/A | Checks `transport.sessionId` to skip re-initialization |

## What stays the same

- `new McpServer(serverInfo, options)` constructor shape
- `server.registerTool(name, config, handler)` method name and 3-arg pattern
- `server.registerResource(name, uri|template, config, handler)` pattern
- `server.registerPrompt(name, config, handler)` pattern
- `server.connect(transport)` / `server.close()`
- `server.sendToolListChanged()` / `sendResourceListChanged()` / `sendPromptListChanged()`
- `RegisteredTool` handle: `enable()`, `disable()`, `remove()`, `update()`
- `StdioServerTransport(stdin?, stdout?)` constructor
- `CallToolResult` shape: `{ content, structuredContent?, isError? }`

## Migration checklist

- [ ] Replace `@modelcontextprotocol/sdk` → `@modelcontextprotocol/server` + `/client` + `/core`
- [ ] Add `@modelcontextprotocol/node` if using HTTP transport
- [ ] Add `@modelcontextprotocol/express` or `/hono` if using framework adapters
- [ ] Update all import paths — no more subpath exports
- [ ] Replace `ZodRawShape` shorthand with full `z.object()` (Zod v4)
- [ ] Replace `extra.*` → `ctx.*` in all handlers (see field mapping above)
- [ ] Replace `McpError`/`ErrorCode` → `ProtocolError`/`ProtocolErrorCode`
- [ ] Replace `setRequestHandler(Schema, fn)` → `setRequestHandler("method", fn)`
- [ ] Remove server-side OAuth code — use external auth library
- [ ] Update Node.js to 20+
- [ ] Set `"type": "module"` in package.json (ESM only)
- [ ] Test with `@modelcontextprotocol/server@latest` when v2 reaches stable
