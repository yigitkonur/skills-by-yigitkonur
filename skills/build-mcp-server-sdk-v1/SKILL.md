---
name: build-mcp-server-sdk-v1
description: "Use skill if you are building or maintaining a TypeScript MCP server on @modelcontextprotocol/sdk v1.x — single-package, Zod schemas, RequestHandlerExtra, McpServer."
---

# Build MCP Server (SDK v1.x)

Build and maintain MCP servers using `@modelcontextprotocol/sdk` v1.x — the **single-package**, Zod-based TypeScript SDK (protocol version 2025-11-25). Covers `McpServer`, `registerTool`, `registerResource`, `registerPrompt`, transports, OAuth 2.1, sessions, and deployment.

## When to use this skill

- *Building a new MCP server on `@modelcontextprotocol/sdk` v1.x (single package)*
- *Adding tools, resources, or prompts to an existing v1 server*
- *Migrating a v1 server from deprecated APIs (`tool()`, `SSEServerTransport`, raw JSON Schema) to current ones (`registerTool`, `StreamableHTTPServerTransport`, Zod)*
- *Wiring authentication on a v1 server — bearer token, OAuth 2.1 via `mcpAuthRouter`, or custom middleware*
- *Hardening transports, sessions, or capabilities on a v1 server (Origin validation, session resumability, sampling/elicitation)*
- *Diagnosing v1-specific runtime errors — `RequestHandlerExtra` access, capability declarations, JSON Schema 2020-12 conversion*

## Do NOT use this skill when

- *Project imports from `@modelcontextprotocol/server` / `@modelcontextprotocol/client` / `@modelcontextprotocol/node` (split packages)* → use `build-mcp-server-sdk-v2`
- *Handlers receive `(args, ctx)` with `ctx.mcpReq.log()` / `ctx.http?.authInfo`* (v2 `ServerContext`) → use `build-mcp-server-sdk-v2`
- *Goal is **porting** an existing v1 server to v2 (not new build, not v1 maintenance)* → use `convert-mcp-sdk-v1-to-v2`
- *Project depends on the `mcp-use` wrapper library, not the raw SDK* → use `build-mcp-use-server`
- *Goal is an agentic-quality / hardening / context-budget audit beyond SDK correctness* → use `audit-agentic-mcp`

## Detect v1 vs v2 (do this first)

Before writing any code, confirm v1 by checking three signals. Any one v2 signal means stop and route to a different skill.

| Signal | v1 (this skill) | v2 (`build-mcp-server-sdk-v2`) |
|---|---|---|
| `package.json` dependency | `@modelcontextprotocol/sdk` (single, `^1.x`) | `@modelcontextprotocol/server`, `/client`, `/node`, `/express`, `/hono` (split, `2.0.0-alpha.x`) |
| Import path | `@modelcontextprotocol/sdk/server/mcp.js`, `/server/stdio.js`, `/server/streamableHttp.js` | `@modelcontextprotocol/server`, `@modelcontextprotocol/node` |
| Handler signature | `(args, extra) => …` with `extra.sendNotification`, `extra.authInfo`, `extra.signal` flat | `(args, ctx) => …` with `ctx.mcpReq.log()`, `ctx.mcpReq.signal`, `ctx.http?.authInfo` |
| HTTP transport class | `StreamableHTTPServerTransport` (or legacy `SSEServerTransport`) | `NodeStreamableHTTPServerTransport` |
| Module system | CJS or ESM | ESM-only, `"type": "module"` required |
| Node engine | Node 18+ | Node 20+ |
| Zod | Zod v3, `ZodRawShape` accepted (`{ name: z.string() }`) | Zod v4, full `z.object({...})` only |

Legacy low-level v1 code may also import request schemas like `ListToolsRequestSchema`, `CallToolRequestSchema` from `@modelcontextprotocol/sdk/types.js` and call `server.setRequestHandler(...)` directly. That is still v1 — but it is the deprecated low-level path; the skill recommends migrating it to `McpServer.registerTool` (see `references/patterns/anti-patterns.md`).

If `package.json` exists, run `bash scripts/check-mcp-sdk-v1-version.sh [project-dir]` (see `scripts/check-mcp-sdk-v1-version.sh.md`) — it asserts single-package v1 and refuses to run if v2 split packages are present.

## Core rules

- Always use `McpServer` from `@modelcontextprotocol/sdk/server/mcp.js` — the low-level `Server` class is deprecated for direct use
- Always use `registerTool` / `registerResource` / `registerPrompt` — positional `tool()` / `resource()` / `prompt()` overloads are deprecated
- Always use `zod` for input/output schemas — the SDK auto-converts to JSON Schema 2020-12
- Always use `StreamableHTTPServerTransport` for HTTP — `SSEServerTransport` is deprecated
- Always set `annotations` on tools (`readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`) — LLMs rely on them for safe execution
- Tool names per SEP-986: 1–64 chars from `A–Z a–z 0–9 _ - . /`; format `service_action_resource` (e.g. `github_search_repos`)
- Input validation failures SHOULD return `{ isError: true }` (tool execution error, LLM-recoverable) — not thrown `McpError` (protocol error)
- Access `server.server` (the underlying low-level `Server`) only for sampling, elicitation, resource subscriptions, or custom protocol extensions

## Workflow

### 1 — Detect what exists

Run `tree -L 3` and inspect `package.json` and `tsconfig.json`. Look for:

- `@modelcontextprotocol/sdk` in dependencies → existing v1 server (go to Step 2A)
- `@modelcontextprotocol/server` (split) → wrong skill, redirect to `build-mcp-server-sdk-v2`
- `mcp-use` in dependencies → wrong skill, redirect to `build-mcp-use-server`
- `.mcp.json` or top-level `mcp` key in `package.json` → MCP **client** config, not server code
- `src/` with tool handler files → existing implementation to extend
- Empty/greenfield → go to Step 2B

For existing projects, run `bash scripts/check-mcp-sdk-v1-version.sh [project-dir]` to confirm v1 single-package and `zod` are present.

### 2A — Audit an existing v1 server

When an MCP server already exists, do not rebuild. Read the implementation and assess each axis:

- **API style:** deprecated `tool()` / `resource()` / `setRequestHandler` low-level → migrate to `registerTool` / `registerResource`
- **Schemas:** raw JSON Schema objects → convert to Zod (preserves type inference and JSON Schema generation)
- **Transport:** `SSEServerTransport` → migrate to `StreamableHTTPServerTransport`
- **Annotations:** missing on any tool → add `readOnlyHint` / `destructiveHint` / `idempotentHint` / `openWorldHint`
- **Origin validation:** HTTP transport without DNS-rebinding protection → add `createMcpExpressApp()` or `hostHeaderValidation` middleware
- **Capabilities:** verify `tools`, `resources`, `prompts`, `logging` declared correctly during initialization

Then proceed to the user's requested change (add tools, fix bugs, add auth, etc.).

### 2B — Scope a new v1 server

Ask or infer:

1. **What does the server wrap?** API, database, file system, CLI tool
2. **Transport?** stdio (local CLI), Streamable HTTP stateful (sessions, resumability), Streamable HTTP stateless (simple req/resp)
3. **Auth?** None (local stdio), static bearer, OAuth 2.1, custom middleware
4. **Surfaces?** Tools (most common), resources (data access), prompts (reusable templates)
5. **Client features?** Sampling (LLM completions), elicitation (user input), roots (filesystem access)

For empty greenfield, scaffold with `bash scripts/scaffold-v1-server.sh <target-dir> <server-name> [stdio|http-stateful|http-stateless]` (see `scripts/scaffold-v1-server.sh.md`).

### 3 — Branch by scenario

| Scenario | First read |
|---|---|
| New stdio server | `references/guides/quick-start.md` |
| New HTTP server (stateful or stateless) | `references/guides/transports.md` |
| Add tools to existing server | `references/guides/tools-and-schemas.md` |
| Add resources or prompts | `references/guides/resources-and-prompts.md` |
| Add authentication | `references/guides/authentication.md` |
| Build a v1 client | `references/guides/client-api.md` |
| Add sampling, elicitation, or session resumability | `references/guides/sessions-and-lifecycle.md` |
| Long-running tools / durable tasks | `references/guides/experimental-tasks.md` |
| Understand the MCP protocol contract | `references/guides/protocol-spec.md` |
| Deploy to production | `references/patterns/deployment.md` |
| Wire logging, error handling, rate limits, monitoring | `references/patterns/production-patterns.md` |
| Avoid common v1 mistakes | `references/patterns/anti-patterns.md` |
| Copy-paste working server example | `references/examples/server-recipes.md` |

### 4 — Preflight

- [ ] Node.js 18+ (required for `globalThis.crypto`)
- [ ] `npm install @modelcontextprotocol/sdk zod` — both required
- [ ] TypeScript 5+ with `"moduleResolution": "node16"` or `"nodenext"`
- [ ] HTTP transport: also `npm install express` (Express 5 recommended)
- [ ] Existing project passed `scripts/check-mcp-sdk-v1-version.sh`

### 5 — Build sequence

1. Create `McpServer` instance with `name`, `version`, optional `description` and `icons`
2. Define Zod schemas for each tool's input (and `outputSchema` if returning `structuredContent`)
3. Register tools with `server.registerTool(name, config, handler)` — config carries schema, annotations, description
4. Register resources with `server.registerResource()` if exposing data
5. Register prompts with `server.registerPrompt()` if exposing templates
6. Create transport and connect: `await server.connect(transport)`
7. Handle graceful shutdown: `process.on('SIGINT', async () => { await server.close(); process.exit(0); })`

See `references/examples/server-recipes.md` for complete working examples by transport.

### 6 — Validate

1. Local checks first: `npm run build`, focused unit tests
2. **Live smoke test** with the bundled `test-by-mcpc-cli` skill, `npx @anthropic-ai/mcp-inspector`, or raw JSON-RPC. Minimum sequence: initialize/connect → `tools/list` → one successful tool call → one invalid-argument call returning `isError: true`
3. Verify Zod catches bad input — pass invalid args, confirm `isError: true`
4. Verify annotations are accurate per tool
5. Verify capabilities are declared (initialize response)
6. For deeper hardening or agentic-quality audits, route to `audit-agentic-mcp` — do not duplicate that here

## Quick start — minimal stdio server

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer(
  { name: "my-server", version: "1.0.0" },
  { instructions: "A helpful server" }
);

server.registerTool("greet", {
  description: "Greet a user by name",
  inputSchema: { name: z.string().describe("The user's name") },
  annotations: { readOnlyHint: true, destructiveHint: false },
}, async ({ name }) => ({
  content: [{ type: "text", text: `Hello, ${name}!` }],
}));

await server.connect(new StdioServerTransport());
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
```

### registerTool config

```typescript
{
  title?: string,              // Human-readable display name
  description?: string,        // LLM reads this to decide when to call
  inputSchema?: ZodRawShape | ZodSchema,
  outputSchema?: ZodRawShape | ZodSchema,   // Enables structuredContent validation
  annotations?: {
    readOnlyHint?: boolean,
    destructiveHint?: boolean,
    idempotentHint?: boolean,
    openWorldHint?: boolean,
  },
  icons?: Icon[],              // 2025-11-25
}
```

### CallToolResult

```typescript
{
  content: Array<
    | { type: "text", text: string }
    | { type: "image", data: string, mimeType: string }
    | { type: "audio", data: string, mimeType: string }
    | { type: "resource", resource: { uri: string, text?: string, blob?: string } }
    | { type: "resource_link", uri: string, name?: string, description?: string }
  >,
  structuredContent?: Record<string, unknown>,
  isError?: boolean,
}
```

### RequestHandlerExtra (v1-specific — flat shape)

Every handler receives `extra` as the last argument:

```typescript
{
  signal: AbortSignal,         // Cooperative cancellation
  authInfo?: AuthInfo,         // From OAuth middleware
  sessionId?: string,
  requestId: RequestId,
  requestInfo?: RequestInfo,   // Original HTTP request metadata
  _meta?: RequestMeta,
  sendNotification: (notification) => Promise<void>,
  sendRequest: (request, schema, options?) => Promise<Result>,
}
```

This flat shape is the **single biggest v1-vs-v2 tell**. v2 nests these fields under `ctx.mcpReq` / `ctx.http`. To port an existing v1 server to v2, use `convert-mcp-sdk-v1-to-v2`.

### Error handling

```typescript
import { McpError, ErrorCode } from "@modelcontextprotocol/sdk/types.js";

// Hard protocol errors (tool not found, bad params at the protocol layer):
throw new McpError(ErrorCode.InvalidParams, "Missing required field: query");

// Soft tool errors (recoverable; LLM can retry or self-correct):
return { content: [{ type: "text", text: "Error: rate limit exceeded" }], isError: true };
```

Per spec: input validation errors SHOULD use `isError: true`, not thrown `McpError` — soft errors enable model self-correction.

## Decision rules

- Prefer `ZodRawShape` (`{ name: z.string() }`) for simple inputs; use full `z.object()` only for transforms, refinements, discriminated unions
- Prefer `isError: true` soft errors over thrown `McpError` for recoverable failures
- Prefer stdio for local-only servers (zero infra, single client)
- Prefer Streamable HTTP for remote or multi-client servers
- Prefer **stateful** HTTP (with `sessionIdGenerator`) when the server needs progress notifications, resumability, or multi-turn context
- Prefer **stateless** HTTP (`sessionIdGenerator: undefined`) for simple request-response tools
- Use `outputSchema` when the tool returns validated structured data alongside text
- Tool names: `service_action_resource`, 1–64 chars (SEP-986)

## Guardrails

- Never use deprecated `tool()`, `resource()`, `prompt()` positional methods
- Never use deprecated `SSEServerTransport` in new servers
- Never use the `Server` class directly — go through `McpServer`
- Never expose internal error details to clients — return user-friendly messages
- Never skip `zod` schemas for tool inputs — unvalidated input is a security risk
- Never hardcode secrets — use environment variables
- Never omit graceful shutdown for HTTP servers
- Never run HTTP servers without DNS-rebinding protection — `Origin` header MUST be validated (use `createMcpExpressApp()` or `hostHeaderValidation`); respond 403 for invalid origins
- Never set `inputSchema: null` — for parameterless tools, omit `inputSchema` entirely

## Output contract

When work completes, report:

- Target path; new build vs existing-server maintenance
- SDK package and version range from `package.json`
- Transport(s): stdio, stateful Streamable HTTP, stateless Streamable HTTP
- Tool / resource / prompt counts and names
- Auth mode: none, static bearer, OAuth 2.1, custom middleware
- Validation actually run and verification rung reached
- Publish/deploy path: npm `bin`/`npx` command for stdio; HTTP endpoint path for remote; Docker/serverless note when applicable
- `server-info`:

```json
{
  "name": "example-server",
  "sdk": "@modelcontextprotocol/sdk@^1.x",
  "transports": ["stdio"],
  "tools": 3,
  "resources": 0,
  "prompts": 0,
  "auth": "none",
  "validatedWith": ["build", "test-by-mcpc-cli"]
}
```

## Reference routing

Read only what the current branch needs. The full set:

### Bundled scripts

| Script | When to run |
|---|---|
| `scripts/check-mcp-sdk-v1-version.sh` | Existing-project preflight; asserts single-package v1 SDK and `zod` present, refuses if v2 split packages found. See `scripts/check-mcp-sdk-v1-version.sh.md`. |
| `scripts/scaffold-v1-server.sh` | Empty greenfield target after picking `stdio`, `http-stateful`, or `http-stateless`. See `scripts/scaffold-v1-server.sh.md`. |

### Start-here guides

| Reference | When to read |
|---|---|
| `references/guides/quick-start.md` | Scaffolding a new server from scratch |
| `references/guides/tools-and-schemas.md` | Registering tools, defining Zod schemas, handling tool results |
| `references/guides/transports.md` | Choosing and configuring stdio, Streamable HTTP, or SSE (legacy) |

### Server capabilities

| Reference | When to read |
|---|---|
| `references/guides/resources-and-prompts.md` | Adding resources (static or template URI) or prompts |
| `references/guides/authentication.md` | OAuth 2.1, bearer tokens, custom middleware |
| `references/guides/client-api.md` | Building MCP clients — connecting, calling tools, reading resources, auth, sampling |
| `references/guides/sessions-and-lifecycle.md` | Sessions, sampling, elicitation, resumability, graceful shutdown |
| `references/guides/experimental-tasks.md` | Durable long-running operations — `registerToolTask`, `InMemoryTaskStore`, `callToolStream` |
| `references/guides/protocol-spec.md` | Protocol lifecycle, capabilities, message format, security requirements |

### Build and ship

| Reference | When to read |
|---|---|
| `references/examples/server-recipes.md` | Copy-paste working server examples by transport |
| `references/patterns/deployment.md` | Docker, serverless, cloud deployment |
| `references/patterns/production-patterns.md` | Logging, error handling, rate limiting, monitoring |
| `references/patterns/anti-patterns.md` | Common v1 mistakes and fixes |

### Specification Enhancement Proposals (SEPs)

| Reference | When to read |
|---|---|
| `references/seps/overview.md` | What SEPs exist and their developer impact |
| `references/seps/auth-security.md` | OAuth flows, enterprise auth, URL elicitation, client security |
| `references/seps/tools-metadata.md` | Tool naming (SEP-986), icons, validation errors, sampling-with-tools, tasks, tracing |
| `references/seps/protocol-transport.md` | JSON Schema 2020-12 dialect, SSE polling, extensions, MCP Apps, elicitation improvements |
| `references/seps/upcoming.md` | Accepted SEPs not yet Final — upcoming breaking changes to prepare for |

## Compatibility note

This skill targets `@modelcontextprotocol/sdk` v1.x (stable, `v1.x` branch). Source-verified against the TypeScript SDK repository.

Key 2025-11-25 spec additions: icons for tools/resources/prompts, tool-name guidance (SEP-986), URL-mode elicitation (SEP-1036), tool calling in sampling (SEP-1577), experimental tasks (SEP-1686), JSON Schema 2020-12 default dialect (SEP-1613), extensions framework (SEP-2133).

v2 (`@modelcontextprotocol/server` + `/client`) remains pre-release alpha. Do not silently mix v1 and v2 packages. To port v1 → v2, route to `convert-mcp-sdk-v1-to-v2`. To start fresh on v2 alpha, route to `build-mcp-server-sdk-v2`.
