---
name: build-mcp-server-sdk-v2
description: "Use skill if you are building or maintaining MCP servers with @modelcontextprotocol/server v2 alpha — split packages, Zod v4, ServerContext, framework adapters, ESM-only."
---

# Build MCP Server (SDK v2 Alpha)

Build and maintain MCP servers using the v2 alpha split-package SDK: `@modelcontextprotocol/server`, `@modelcontextprotocol/client`, `@modelcontextprotocol/core`. Node.js 20+, ESM-only, Zod v4. Use this skill for new v2 alpha builds and v2 maintenance; use `convert-mcp-server-sdk-v1-to-v2` to port an existing v1 server.

## Current channel matrix

| Channel | Status | Use for |
|---|---|---|
| npm published alpha | `@modelcontextprotocol/server@2.0.0-alpha.2` and split packages, published 2026-04-01; stdio transports are root exports | Install commands and runnable examples that must work from npm today |
| main branch / `v2.0.0-bc` PR series | Compatibility work after alpha.2; docs now show stdio subpath exports | Forward-looking notes only, gated by fresh npm/source verification |
| v1 stable | `@modelcontextprotocol/sdk@1.x` | Default production path until a non-alpha v2 release exists |

**When to use a different skill instead:**

- `@modelcontextprotocol/sdk` (single package, v1) in `package.json` → use `build-mcp-server-sdk-v1`
- Handlers use `(args, extra)` with `extra.sendNotification` / `extra.authInfo` → that's v1, use `build-mcp-server-sdk-v1`
- Existing v1 server that needs to be ported to v2 → use `convert-mcp-server-sdk-v1-to-v2`
- Uses the `mcp-use` wrapper library → use `build-mcp-use-server`
- Imports `@hono/mcp` → community Hono middleware, not the official SDK adapter; choose whether to migrate before applying `@modelcontextprotocol/hono` examples

**How to detect v2:** Look for split package imports (`@modelcontextprotocol/server`, `@modelcontextprotocol/client`), handlers using `(args, ctx)` with `ctx.mcpReq.log()` / `ctx.mcpReq.signal`, and `"type": "module"` in `package.json`.

Core rules:

- Always use `McpServer` from `@modelcontextprotocol/server` — the `Server` class is deprecated
- Always use `registerTool` / `registerResource` / `registerPrompt` — positional overloads removed
- Always use Zod v4 full schemas (`z.object({...})`) — raw shapes are v1 style; treat any current-release compatibility shim as migration aid, not target pattern
- Always use `NodeStreamableHTTPServerTransport` from `@modelcontextprotocol/node` for HTTP
- Use `@modelcontextprotocol/hono` for the official SDK Hono adapter; do not silently substitute community `@hono/mcp`
- Server-side OAuth is removed from the SDK — wire HTTP-layer auth (external AS + `jose`, Passport, custom Bearer middleware) and forward `req.auth` into `ctx.http?.authInfo`; treat `@modelcontextprotocol/server-auth-legacy` as planned/open until npm and PR #1908 confirm publication
- SSE server transport is removed — use Streamable HTTP
- ESM-only — no CommonJS support
- Node.js 20+ required

## Workflow

### 1 — Detect what exists

Run `tree -L 3` and check `package.json`. Look for:

- `@modelcontextprotocol/server` in dependencies → existing v2 server
- `@modelcontextprotocol/sdk` (single package) → v1, redirect to `build-mcp-server-sdk-v1`
- `mcp-use` → wrong skill, redirect to `build-mcp-use-server`
- Handler patterns: `ctx.mcpReq` → v2; `extra.sendNotification` → v1

### 2A — Maintain or fix an existing v2 server

Read the implementation. Check for:

- Correct context usage: `ctx.mcpReq.signal`, `ctx.http?.authInfo`, `ctx.mcpReq.notify()`
- Proper schema usage: full `z.object()` instead of v1 raw shapes
- Framework adapter usage: `createMcpExpressApp()` from `@modelcontextprotocol/express`
- `outputSchema` validation: tools with `outputSchema` must return `structuredContent`

### 2B — Scope a new v2 server

Ask or infer:

1. **What does the server wrap?** (API, database, filesystem, CLI)
2. **Transport?** stdio for local, Streamable HTTP for remote
3. **Framework?** Express or Hono (both have dedicated adapters)
4. **Auth?** Client-side only in v2 (server-side OAuth removed)

### 3 — Choose the implementation branch

| Scenario | Action |
|---|---|
| New stdio server | `references/guides/quick-start.md` |
| New HTTP server (Express) | `references/guides/transports.md` + `references/guides/framework-adapters.md` |
| New HTTP server (Hono) | `references/guides/transports.md` + `references/guides/framework-adapters.md` |
| Add tools | `references/guides/tools-and-schemas.md` |
| Add resources or prompts | `references/guides/resources-and-prompts.md` |
| Build an MCP client | `references/guides/client-api.md` |
| Stage or package for production readiness | `references/patterns/deployment.md` |

### 4 — Preflight setup

- [ ] Node.js 20+ installed
- [ ] `npm install --save-exact @modelcontextprotocol/server@2.0.0-alpha.2`
- [ ] `npm install zod@^4`
- [ ] If HTTP: `npm install --save-exact @modelcontextprotocol/node@2.0.0-alpha.2`
- [ ] If Express: `npm install --save-exact @modelcontextprotocol/express@2.0.0-alpha.2` plus `npm install express`
- [ ] If Hono: `npm install --save-exact @modelcontextprotocol/hono@2.0.0-alpha.2` plus `npm install hono`
- [ ] `"type": "module"` in package.json
- [ ] TypeScript 5+ with `"module": "Node16"`, `"moduleResolution": "Node16"`

### 5 — Build or extend

1. Create `McpServer` with name, version, optional description/icons
2. Define Zod v4 schemas: `z.object({ field: z.string() })` (not raw shapes as the target pattern)
3. Register tools with `server.registerTool()` — input schema, annotations, handler with `(args, ctx)` pattern
4. Register resources with `server.registerResource()` if exposing data
5. Register prompts with `server.registerPrompt()` if providing templates
6. Create transport and connect: `await server.connect(transport)`
7. Handle graceful shutdown

### 6 — Validate

- **stdio**: `npx @anthropic-ai/mcp-inspector npx tsx src/index.ts`
- **HTTP**: Start server, test with curl or Inspector
- **Schemas**: Verify Zod validation catches bad input
- **Context**: Confirm `ctx.mcpReq` is used (not `extra`)

## Quick start — minimal v2 stdio server

```typescript
import { McpServer, StdioServerTransport } from "@modelcontextprotocol/server";
import * as z from "zod/v4";

const server = new McpServer(
  { name: "my-server", version: "1.0.0" },
  { instructions: "A helpful server" }
);

server.registerTool("greet", {
  title: "Greet User",
  description: "Greet a user by name",
  inputSchema: z.object({
    name: z.string().describe("The user's name"),
  }),
  annotations: { readOnlyHint: true, destructiveHint: false },
}, async ({ name }, ctx) => {
  await ctx.mcpReq.log("info", `Greeting ${name}`);
  return {
    content: [{ type: "text" as const, text: `Hello, ${name}!` }],
  };
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

## Core API summary

### McpServer

```typescript
import { McpServer, StdioServerTransport } from "@modelcontextprotocol/server";

new McpServer(
  { name: string, version: string, description?: string, icons?: Icon[] },
  { capabilities?: ServerCapabilities, instructions?: string }
)

server.connect(transport: Transport): Promise<void>
server.close(): Promise<void>
server.registerTool(name, config, handler): RegisteredTool
server.registerResource(name, uri | template, config, handler): RegisteredResource
server.registerPrompt(name, config, handler): RegisteredPrompt
server.sendToolListChanged(): void
server.sendResourceListChanged(): void
server.sendPromptListChanged(): void
server.sendLoggingMessage(params): Promise<void>
server.isConnected(): boolean
server.experimental.tasks  // ExperimentalMcpServerTasks
```

### registerTool config

```typescript
{
  title?: string,
  description?: string,
  inputSchema?: AnySchema,           // z.object({...}) — full Zod v4 schema
  outputSchema?: AnySchema,          // enables structuredContent validation
  annotations?: ToolAnnotations,
  _meta?: Record<string, unknown>,
}
```

### ServerContext (handler second argument)

```typescript
// Tool handler: (args, ctx) => CallToolResult
// No-args tool: (ctx) => CallToolResult

ctx.sessionId?: string
ctx.mcpReq.id: RequestId
ctx.mcpReq.method: string
ctx.mcpReq.signal: AbortSignal
ctx.mcpReq._meta?: RequestMeta
ctx.mcpReq.send(request, schema, options?): Promise<Result>
ctx.mcpReq.notify(notification): Promise<void>
ctx.mcpReq.log(level, data, logger?): Promise<void>
ctx.mcpReq.elicitInput(params): Promise<ElicitResult>
ctx.mcpReq.requestSampling(params): Promise<CreateMessageResult>
ctx.http?.authInfo?: AuthInfo
ctx.http?.req?: RequestInfo
ctx.http?.closeSSE?(): void
ctx.http?.closeStandaloneSSE?(): void
ctx.task?.id?: string
ctx.task?.store?: RequestTaskStore
```

### Error handling

```typescript
import { ProtocolError, ProtocolErrorCode } from "@modelcontextprotocol/core";

// Hard protocol errors:
throw new ProtocolError(ProtocolErrorCode.InvalidParams, "Bad input");

// Soft tool errors (LLM can self-correct):
return { content: [{ type: "text", text: "Error: not found" }], isError: true };
```

## Decision rules

- Always use `z.object({...})` — raw shapes (`{ name: z.string() }`) are v1 style; if the current release accepts them, treat that as migration compatibility only
- Prefer `isError: true` for recoverable tool errors — LLMs self-correct from these
- Prefer `ctx.mcpReq.log()` over `console.error()` — sends structured logs to the client
- Prefer `ctx.mcpReq.elicitInput()` over `ctx.mcpReq.send()` for user input — cleaner API
- Use `createMcpExpressApp()` or `createMcpHonoApp()` instead of raw Express/Hono setup
- Set every relevant annotation deliberately; fill all four when safety or side effects matter

## Guardrails

- Never write new v2-native code with raw Zod shapes — use full `z.object()` schemas
- Never use `extra.sendNotification` / `extra.authInfo` — those are v1 patterns; use `ctx.mcpReq`
- Never import from `@modelcontextprotocol/sdk` — that's v1; import from `/server`, `/client`, `/core`
- Never use `SSEServerTransport` — removed in v2
- Never implement server-side OAuth with the SDK — removed; use external auth library
- Never use CommonJS — v2 is ESM-only
- Never use Node.js < 20

## Reference routing

### Start here

| Reference | When to read |
|---|---|
| `references/guides/quick-start.md` | Scaffolding a new v2 server from scratch |
| `references/guides/tools-and-schemas.md` | Registering tools with Zod v4, ServerContext, annotations |
| `references/guides/transports.md` | stdio, Streamable HTTP, web-standard transport |

### Server capabilities

| Reference | When to read |
|---|---|
| `references/guides/resources-and-prompts.md` | Resources (static/template URI) and prompts |
| `references/guides/authentication.md` | Server-side auth: JWT/Passport middleware, planned server-auth-legacy caveat, scope checks, DNS rebinding |
| `references/guides/client-api.md` | Building MCP clients, auth providers, middleware |
| `references/guides/framework-adapters.md` | Express and Hono adapters, DNS rebinding protection |
| `references/guides/context-and-lifecycle.md` | ServerContext fields, sampling, elicitation, sessions, shutdown |

### Build and ship

| Reference | When to read |
|---|---|
| `references/examples/server-recipes.md` | Complete v2 server examples |
| `references/patterns/deployment.md` | Docker, serverless, Cloudflare Workers |
| `references/patterns/production-patterns.md` | Logging, error handling, rate limits, timeouts, AbortSignal, graceful shutdown |
| `references/patterns/anti-patterns.md` | Common mistakes — including v1 patterns to avoid |

## Compatibility and adoption note

v2 is in pre-release alpha as of 2026-05-08. The latest npm-published split packages are `2.0.0-alpha.2`; the `v2.0.0-bc` label tracks main-branch compatibility PRs that may not be published yet. Most production MCP servers should stay on v1.x until v2 publishes a non-alpha stable release.

What this means in practice:

- **Pin alpha versions exactly** (no `^` ranges) — alphas can break between patches.
- **Plan rollback** before deploying — keep the v1 branch deployable.
- **The `@modelcontextprotocol/sdk` meta-package** remains v1 on npm unless fresh npm verification proves otherwise; main-branch meta-package PRs are migration signals, not an install target.
- **`@modelcontextprotocol/server-auth-legacy`** is a planned/open transitional package until `npm view` succeeds and PR #1908 or release notes confirm publication.
- Some MCP clients and third-party tooling still target v1 patterns; verify your host (Claude Desktop, Cursor, Cline, custom) handles v2-specific features end-to-end before relying on them.

The SDK is actively maintained on the `main` branch (which is now the v2 branch). Subscribe to release notes for the duration of any v2 work.
