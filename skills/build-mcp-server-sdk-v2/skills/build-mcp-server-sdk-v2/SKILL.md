---
name: build-mcp-server-sdk-v2
description: "Use skill if you are building or maintaining MCP servers on @modelcontextprotocol/server v2 alpha — split packages, McpServer, registerTool, ctx.mcpReq handler context."
---

# Build MCP Server (SDK v2 Alpha)

Build and maintain MCP servers on the v2 alpha **split-package SDK**: `@modelcontextprotocol/server`, `@modelcontextprotocol/client`, `@modelcontextprotocol/core`, plus `/node`, `/express`, `/hono` adapters. ESM-only, Node 20+, Zod v4. Status as of 2026-05-09: latest npm tag is `2.0.0-alpha.2` — pin exact, plan rollback.

## When to use

Trigger this skill if any of these are true:

- *Building a brand-new MCP server and the user picks v2, "the alpha", or split packages.*
- *`package.json` already depends on `@modelcontextprotocol/server`, `@modelcontextprotocol/client`, or `@modelcontextprotocol/core`.*
- *Existing code uses `new McpServer(...)` from `@modelcontextprotocol/server` and `server.registerTool(...)` with the high-level API.*
- *Tool/resource/prompt handlers use `(args, ctx)` with `ctx.mcpReq.signal`, `ctx.mcpReq.log()`, `ctx.mcpReq.notify()`, or `ctx.http?.authInfo`.*
- *HTTP work uses `NodeStreamableHTTPServerTransport` from `@modelcontextprotocol/node`, or `createMcpExpressApp()` / `createMcpHonoApp()` from the official adapters.*
- *Schemas are full `z.object({...})` from `zod/v4`, not raw-shape shorthand.*

Do NOT use this skill if any of these are true:

- *`package.json` depends on the single-package `@modelcontextprotocol/sdk` (v1) — use **`build-mcp-server-sdk-v1`** instead.*
- *Handlers use `(args, extra)` with `extra.sendNotification`, `extra.authInfo`, or `extra.signal` — that is v1; use **`build-mcp-server-sdk-v1`**.*
- *The job is **porting** an existing v1 server to v2 — use **`convert-mcp-server-sdk-v1-to-v2`** (covers package split, import rewrite, `extra → ctx` mapping, OAuth replacement, staging strategy).*
- *The project uses the `mcp-use` wrapper or `@hono/mcp` community middleware — use **`build-mcp-use-server`**, or migrate before applying official adapter patterns.*
- *The user wants an agentic-quality / hardening / context-budget audit, not SDK correctness — pair this skill with the relevant `build-mcp-*` reference for protocol patterns.*

## Detect v2 vs v1

Run `tree -L 3` and read `package.json`. v2 fingerprints (any one is sufficient):

| Signal | Where | Means |
|---|---|---|
| `@modelcontextprotocol/server` (or `/client`, `/core`, `/node`, `/express`, `/hono`) | `package.json` dependencies | v2 split package |
| `import { McpServer, StdioServerTransport } from "@modelcontextprotocol/server"` | source | v2 server entrypoint |
| Handler signature `(args, ctx) => …` and `ctx.mcpReq.*` | source | v2 ServerContext |
| `import * as z from "zod/v4"` | source | v2 Zod v4 path |
| `"type": "module"` + Node 20+ | `package.json` / engines | v2 ESM-only target |

v1 anti-fingerprints (treat as **wrong skill**, redirect):

- `@modelcontextprotocol/sdk` single package → `build-mcp-server-sdk-v1`
- `extra.sendNotification`, `extra.authInfo`, `extra.signal` → `build-mcp-server-sdk-v1`
- `SSEServerTransport` → v1 only; v2 removed it

## Core rules

- Always use `McpServer` from `@modelcontextprotocol/server`. The low-level `Server` class is deprecated for direct use.
- Always use `registerTool` / `registerResource` / `registerPrompt`. Positional overloads were removed in v2.
- Always pass full Zod v4 schemas (`z.object({...})`). Raw shapes are a v1 pattern; if a current alpha still accepts them, treat that as a migration shim, not the target.
- Always import HTTP transport from `@modelcontextprotocol/node` (e.g. `NodeStreamableHTTPServerTransport`). `SSEServerTransport` is removed.
- For Express, use `@modelcontextprotocol/express` (`createMcpExpressApp()`). For Hono, use `@modelcontextprotocol/hono`. Do not silently substitute the community `@hono/mcp` package.
- Server-side OAuth is removed from the SDK. Wire authentication at the HTTP layer (Passport, custom Bearer middleware, `jose`) and forward auth into `ctx.http?.authInfo`. Treat any `@modelcontextprotocol/server-auth-legacy` as planned/open until npm publish is confirmed.
- ESM-only. No CommonJS dual-publish. Node.js 20+ required.
- Pin alpha versions exactly (`--save-exact`); never use `^` ranges across alphas.

## Workflow

### 1 — Detect what exists

Inspect `package.json` and `src/`. Decide: **existing v2 server** (go to 2A), **new v2 server** (go to 2B), or **wrong skill** (redirect per *When to use* and stop).

### 2A — Maintain or fix an existing v2 server

Read the implementation. Verify:

- Context usage: `ctx.mcpReq.signal`, `ctx.mcpReq.log()`, `ctx.mcpReq.notify()`, `ctx.http?.authInfo`. Flag any `extra.*` access — that is v1 leakage.
- Schemas: full `z.object()` (not raw shapes) for new code. `outputSchema` present whenever the tool returns `structuredContent`.
- Transport: `NodeStreamableHTTPServerTransport` from `@modelcontextprotocol/node` for HTTP; `StdioServerTransport` from `@modelcontextprotocol/server` for stdio.
- Framework: `createMcpExpressApp()` or `createMcpHonoApp()` for HTTP framework wiring (DNS rebinding protection lives in the adapter).
- Annotations: `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint` set deliberately for tools with side effects.

Then make the requested change (add tool, fix bug, add auth middleware, etc.).

### 2B — Scope a new v2 server

Decide:

1. **Wraps what?** API, database, filesystem, CLI, or in-process logic.
2. **Transport?** `stdio` for local; `Streamable HTTP` for remote/multi-client.
3. **Framework?** Express or Hono if HTTP — both have first-party adapters.
4. **Auth?** External AS + middleware; SDK no longer hosts an authorization server.

### 3 — Choose the implementation branch

| Scenario | Read |
|---|---|
| New stdio server | `references/guides/quick-start.md` |
| New HTTP server (Express) | `references/guides/transports.md` + `references/guides/framework-adapters.md` |
| New HTTP server (Hono) | `references/guides/transports.md` + `references/guides/framework-adapters.md` |
| Add tools | `references/guides/tools-and-schemas.md` |
| Add resources or prompts | `references/guides/resources-and-prompts.md` |
| Add auth middleware | `references/guides/authentication.md` |
| Build an MCP client | `references/guides/client-api.md` |
| Sampling, elicitation, sessions, shutdown | `references/guides/context-and-lifecycle.md` |
| Working server examples | `references/examples/server-recipes.md` |
| Production hardening | `references/patterns/production-patterns.md` |
| Deploy (Docker, serverless, Workers) | `references/patterns/deployment.md` |
| Avoid common mistakes / v1 leakage | `references/patterns/anti-patterns.md` |

### 4 — Preflight setup

- [ ] Node.js 20+ installed
- [ ] If existing: run `bash scripts/check-mcp-server-v2-version.sh` from the project root (see `scripts/check-mcp-server-v2-version.sh.md`); unsafe alpha ranges must fail
- [ ] `npm install --save-exact @modelcontextprotocol/server@2.0.0-alpha.2`
- [ ] `npm install zod@^4`
- [ ] HTTP also: `npm install --save-exact @modelcontextprotocol/node@2.0.0-alpha.2`
- [ ] Express also: `npm install --save-exact @modelcontextprotocol/express@2.0.0-alpha.2 express`
- [ ] Hono also: `npm install --save-exact @modelcontextprotocol/hono@2.0.0-alpha.2 hono`
- [ ] `"type": "module"` in `package.json`
- [ ] TypeScript 5+, `"module": "Node16"`, `"moduleResolution": "Node16"`

### 5 — Build

Default sequence:

1. Construct `McpServer` with `{ name, version }` and optional `{ instructions, capabilities }`.
2. Define Zod v4 schemas: `z.object({ field: z.string() })` (full schemas, not raw shapes).
3. Register tools with `server.registerTool(name, config, handler)` — `inputSchema`, `annotations`, handler `(args, ctx) => CallToolResult`.
4. Register resources with `server.registerResource()` if exposing data.
5. Register prompts with `server.registerPrompt()` if providing templates.
6. Construct transport, then `await server.connect(transport)`.
7. Handle graceful shutdown (`SIGINT`/`SIGTERM` → `await server.close()`).

### 6 — Validate

- Local checks first: `npm run build`, focused tests if present.
- **stdio:** `npx @anthropic-ai/mcp-inspector npx tsx src/index.ts`.
- **HTTP:** start server; probe with `curl` or Inspector.
- **Live CLI smoke:** if `mcpc` is installed, hand off to `test-by-mcpc-cli`. Minimum sequence: initialize → `tools/list` → one successful call → one invalid-arg call returning `isError: true`.
- **Schemas:** invalid input → tool error (`isError: true`), not a thrown protocol error.
- **Context:** confirm `ctx.mcpReq` is the access path, never `extra`.

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
  inputSchema: z.object({ name: z.string().describe("The user's name") }),
  annotations: { readOnlyHint: true, destructiveHint: false },
}, async ({ name }, ctx) => {
  await ctx.mcpReq.log("info", `Greeting ${name}`);
  return { content: [{ type: "text" as const, text: `Hello, ${name}!` }] };
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

## Core API summary

### McpServer

```typescript
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
// No-arg tool:  (ctx)       => CallToolResult

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

- Use full `z.object({...})` for every new tool schema. Raw shapes are v1 style; even if accepted, do not target them.
- Prefer `isError: true` for recoverable failures — the LLM self-corrects from soft errors.
- Prefer `ctx.mcpReq.log()` over `console.error()` so logs reach the client.
- Prefer `ctx.mcpReq.elicitInput()` over hand-rolled `ctx.mcpReq.send()` for user input requests.
- Use `createMcpExpressApp()` / `createMcpHonoApp()` instead of raw Express/Hono setup — DNS rebinding is handled inside.
- Set every relevant `annotations` field deliberately; fill all four when safety or side-effects matter.

## Guardrails

- Never write new v2-native code with raw Zod shapes — always full `z.object()`.
- Never use `extra.sendNotification` / `extra.authInfo` / `extra.signal` — those are v1; the v2 access path is `ctx.mcpReq.*` and `ctx.http?.authInfo`.
- Never import from `@modelcontextprotocol/sdk` — that is the v1 single package; in v2 you import from `/server`, `/client`, `/core`, `/node`, `/express`, `/hono`.
- Never use `SSEServerTransport` — removed in v2; use Streamable HTTP.
- Never implement server-side OAuth in the SDK — removed in v2; integrate at the HTTP layer.
- Never use CommonJS — v2 is ESM-only.
- Never run on Node < 20.
- Never use `^` ranges for alpha packages — pin exact and plan rollback.

## Compatibility and adoption note

v2 is pre-release alpha as of 2026-05-09. The latest npm split packages are at `2.0.0-alpha.2`; main-branch PRs labeled `v2.0.0-bc` may not yet be published. Most production servers should remain on v1.x until v2 cuts a non-alpha stable release.

In practice:

- **Pin alpha versions exactly** (no `^`); alphas can break between patches.
- **Plan rollback** before deploying — keep the v1 branch deployable.
- **The `@modelcontextprotocol/sdk` meta-package** remains v1 on npm unless fresh `npm view` proves otherwise.
- **`@modelcontextprotocol/server-auth-legacy`** is planned/open; treat it as unpublished until `npm view` succeeds.
- **Verify each MCP host** (Claude Desktop, Cursor, Cline, custom) end-to-end on v2 features before depending on them.

## Output contract

Report v2 server work with:

1. Target path and detected channel/version.
2. Transport (stdio, Streamable HTTP) and framework (none, Express, Hono).
3. Tools, resources, and prompts added or changed.
4. Auth shape (none, Bearer middleware, Passport, jose, external AS).
5. Validation rung reached and exact commands run.
6. Alpha-risk caveats and rollback status.
