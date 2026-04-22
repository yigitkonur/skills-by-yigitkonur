---
name: build-mcp-server-sdk-v2
description: "Use skill if you are building or maintaining MCP servers with @modelcontextprotocol/server v2 — split packages, Zod v4, ServerContext, framework adapters, and ESM-only."
---

# Build MCP Server (SDK v2)

Build and maintain MCP servers using the v2 split-package SDK: `@modelcontextprotocol/server`, `@modelcontextprotocol/client`, `@modelcontextprotocol/core`. Node.js 20+, ESM-only, Zod v4. Released Q1 2026, community adoption still early.

**When to use a different skill instead:**

- `@modelcontextprotocol/sdk` (single package) in `package.json` → use `build-mcp-server-sdk-v1`
- Handlers use `(args, extra)` with `extra.sendNotification` / `extra.authInfo` → that's v1, use `build-mcp-server-sdk-v1`
- Uses the `mcp-use` wrapper library → use `build-mcp-use-server`

**How to detect v2:** Look for split package imports (`@modelcontextprotocol/server`, `@modelcontextprotocol/client`), handlers using `(args, ctx)` with `ctx.mcpReq.log()` / `ctx.mcpReq.signal`, and `"type": "module"` in `package.json`.

Core rules:

- Always use `McpServer` from `@modelcontextprotocol/server` — the `Server` class is deprecated
- Always use `registerTool` / `registerResource` / `registerPrompt` — positional overloads removed
- Always use Zod v4 full schemas (`z.object({...})`) — raw shapes not accepted in v2
- Always use `NodeStreamableHTTPServerTransport` from `@modelcontextprotocol/node` for HTTP
- Server-side OAuth is removed — use `better-auth` or a dedicated auth library
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
- Proper schema usage: full `z.object()` not raw shapes
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
| Deploy to production | `references/patterns/deployment.md` |

### 4 — Preflight setup

- [ ] Node.js 20+ installed
- [ ] `npm install @modelcontextprotocol/server zod` (Zod v4)
- [ ] If HTTP: `npm install @modelcontextprotocol/node` (Node.js transport)
- [ ] If Express: `npm install @modelcontextprotocol/express express`
- [ ] If Hono: `npm install @modelcontextprotocol/hono hono`
- [ ] `"type": "module"` in package.json
- [ ] TypeScript 5+ with `"module": "Node16"`, `"moduleResolution": "Node16"`

### 5 — Build or extend

1. Create `McpServer` with name, version, optional description/icons
2. Define Zod v4 schemas: `z.object({ field: z.string() })` (not raw shapes)
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

- Always use `z.object({...})` — raw shapes (`{ name: z.string() }`) are not accepted in v2
- Prefer `isError: true` for recoverable tool errors — LLMs self-correct from these
- Prefer `ctx.mcpReq.log()` over `console.error()` — sends structured logs to the client
- Prefer `ctx.mcpReq.elicitInput()` over `ctx.mcpReq.send()` for user input — cleaner API
- Use `createMcpExpressApp()` or `createMcpHonoApp()` instead of raw Express/Hono setup
- Set `annotations` on every tool

## Guardrails

- Never use raw Zod shapes — v2 requires full `z.object()` schemas
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
| `references/guides/client-api.md` | Building MCP clients, auth providers, middleware |
| `references/guides/framework-adapters.md` | Express and Hono adapters, DNS rebinding protection |
| `references/guides/context-and-lifecycle.md` | ServerContext fields, sampling, elicitation, sessions, shutdown |

### Build and ship

| Reference | When to read |
|---|---|
| `references/examples/server-recipes.md` | Complete v2 server examples |
| `references/patterns/deployment.md` | Docker, serverless, Cloudflare Workers |
| `references/patterns/anti-patterns.md` | Common mistakes — including v1 patterns to avoid |

## Community adoption note

v2 shipped Q1 2026. Most production MCP servers still run v1.x. You may encounter:
- Fewer community examples and Stack Overflow answers
- Some MCP clients not yet supporting v2-specific features
- Third-party tools still targeting v1 patterns

The SDK itself is stable and actively maintained on the `main` branch.
