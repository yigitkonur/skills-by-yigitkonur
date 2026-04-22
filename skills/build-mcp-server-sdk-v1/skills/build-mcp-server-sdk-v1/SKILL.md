---
name: build-mcp-server-sdk-v1
description: "Use skill if you are building or maintaining MCP servers with @modelcontextprotocol/sdk v1.x — single-package TypeScript SDK with Zod, RequestHandlerExtra, and built-in OAuth."
---

# Build MCP Server (SDK v1)

Build and maintain MCP servers using `@modelcontextprotocol/sdk` v1.x (single package, Zod-based, protocol version 2025-11-25). Covers `McpServer`, `registerTool`, `registerResource`, `registerPrompt`, transports, OAuth 2.1, sessions, and deployment.

**When to use a different skill instead:**

- Imports from `@modelcontextprotocol/server` (split packages) → use `build-mcp-server-sdk-v2`
- Handlers use `ctx.mcpReq` instead of flat `extra` → use `build-mcp-server-sdk-v2`
- Uses the `mcp-use` wrapper library → use `build-mcp-use-server`
- Auditing/optimizing an existing server → use `optimize-agentic-mcp`

**How to detect v1:** `@modelcontextprotocol/sdk` (single package) in `package.json`. Handlers use `(args, extra)` with `extra.sendNotification`, `extra.authInfo`, `extra.signal` at the top level.

Core rules:

- Always use `McpServer` — the `Server` class is deprecated for direct use
- Always use `registerTool` / `registerResource` / `registerPrompt` — positional `tool()` / `resource()` / `prompt()` overloads are deprecated
- Always use `zod` for input/output schemas — the SDK converts them to JSON Schema 2020-12 automatically
- Always use `StreamableHTTPServerTransport` for HTTP — `SSEServerTransport` is deprecated
- Access `server.server` only for sampling, elicitation, resource subscriptions, or custom protocol extensions
- Tool names SHOULD be 1-128 chars using letters, digits, underscore, hyphen, dot
- Input validation errors SHOULD be returned as tool execution errors (`isError: true`) not protocol errors — enables LLM self-correction

## Workflow

### 1 — Detect what exists

Run `tree -L 3` and `ls package.json tsconfig.json` in the project directory. Look for:

- `@modelcontextprotocol/sdk` in `package.json` dependencies → existing MCP server
- `mcp-use` in dependencies → wrong skill, redirect to `build-mcp-use-server`
- `.mcp.json` or `mcp` key in `package.json` → MCP client config, not server code
- `src/` with tool/resource handler files → existing implementation to extend

Summarize: existing server (go to Step 2A) or new server (go to Step 2B).

### 2A — Audit an existing SDK server

When an MCP server already exists, do not rebuild. Read the implementation and assess:

- Which API style is used? If deprecated `tool()` / `resource()`, migrate to `registerTool` / `registerResource`
- Are Zod schemas defined for all tool inputs? If raw JSON Schema objects, convert to Zod
- Is the transport current? If `SSEServerTransport`, migrate to `StreamableHTTPServerTransport`
- Are tool annotations set? Add `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint` where missing
- Does the server validate `Origin` header for HTTP transport? Add `createMcpExpressApp()` or `hostHeaderValidation`
- Does the server declare capabilities correctly during initialization? Check `tools`, `resources`, `prompts`, `logging`

Then proceed to the user's requested changes (add tools, fix bugs, add auth, etc.).

### 2B — Scope a new server

Ask or infer from context:

1. **What does the server wrap?** (API, database, file system, CLI tool, etc.)
2. **Transport?** stdio for local CLI integration, Streamable HTTP for remote/multi-client
3. **Auth needed?** Bearer token, OAuth 2.1, or none (local stdio)
4. **Tools, resources, or prompts?** Most servers need tools; resources for data access; prompts for reusable templates
5. **Client features needed?** Sampling (LLM completions), elicitation (user input), roots (filesystem access)

### 3 — Choose the implementation branch

| Scenario | Action |
|---|---|
| New stdio server | Scaffold from quick-start template → `references/guides/quick-start.md` |
| New HTTP server (stateful) | Scaffold with session management → `references/guides/transports.md` |
| New HTTP server (stateless) | Scaffold without sessions → `references/guides/transports.md` |
| Add tools to existing server | Read `references/guides/tools-and-schemas.md`, register new tools |
| Add resources | Read `references/guides/resources-and-prompts.md` |
| Add authentication | Read `references/guides/authentication.md` |
| Add sampling or elicitation | Read `references/guides/sessions-and-lifecycle.md` |
| Deploy to production | Read `references/patterns/deployment.md` |
| Understand the MCP protocol | Read `references/guides/protocol-spec.md` |

### 4 — Preflight setup

Before writing server code, confirm:

- [ ] Node.js 18+ installed (required for `globalThis.crypto`)
- [ ] `npm install @modelcontextprotocol/sdk zod` — both are required
- [ ] TypeScript 5+ with `"moduleResolution": "node16"` or `"nodenext"` in tsconfig
- [ ] If HTTP transport: `npm install express` (Express 5 recommended)

### 5 — Build or extend the server

Default implementation sequence:

1. Create `McpServer` instance with name, version, and optional description/icons
2. Define Zod schemas for each tool's input (and output if `structuredContent` is needed)
3. Register tools with `server.registerTool()` — input schema, annotations, async handler
4. Register resources with `server.registerResource()` if the server exposes data
5. Register prompts with `server.registerPrompt()` if the server provides templates
6. Create transport and connect: `await server.connect(transport)`
7. Handle graceful shutdown with `process.on('SIGINT', ...)`

Refer to `references/examples/server-recipes.md` for complete working examples.

### 6 — Validate

- **stdio**: Test with `npx @anthropic-ai/mcp-inspector` or pipe JSON-RPC messages directly
- **HTTP**: Start the server, then test with `curl` or the MCP Inspector
- **Tool schemas**: Verify Zod validation catches bad input (pass invalid args, confirm error response)
- **Annotations**: Check that `readOnlyHint` / `destructiveHint` are accurate for each tool
- **Capabilities**: Verify the server declares the correct capabilities during initialization

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
```

### registerTool config

```typescript
{
  title?: string,              // Human-readable display name
  description?: string,        // LLM reads this to decide when to call the tool
  inputSchema?: ZodRawShape | ZodSchema,
  outputSchema?: ZodRawShape | ZodSchema,   // Enables structuredContent validation
  annotations?: {
    readOnlyHint?: boolean,    // Does not modify state
    destructiveHint?: boolean, // May delete/modify data
    idempotentHint?: boolean,  // Repeated calls safe
    openWorldHint?: boolean,   // Interacts with external services
  },
  icons?: Icon[],              // Visual identifier (2025-11-25)
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

### RequestHandlerExtra (v1.x)

Every handler receives `extra` as the last argument:

```typescript
{
  signal: AbortSignal,         // For cooperative cancellation
  authInfo?: AuthInfo,         // From OAuth middleware
  sessionId?: string,          // Current session ID
  requestId: RequestId,        // JSON-RPC request ID
  requestInfo?: RequestInfo,   // Original HTTP request metadata
  _meta?: RequestMeta,         // Protocol-level metadata
  sendNotification: (notification) => Promise<void>,
  sendRequest: (request, schema, options?) => Promise<Result>,
}
```

Note: In v2 alpha, this becomes `ServerContext` with a restructured API. See `references/guides/v2-migration.md`.

### Error handling

```typescript
import { McpError, ErrorCode } from "@modelcontextprotocol/sdk/types.js";

// Hard protocol errors (tool not found, bad params):
throw new McpError(ErrorCode.InvalidParams, "Missing required field: query");

// Soft tool errors (API failures the LLM can handle):
return { content: [{ type: "text", text: "Error: rate limit exceeded" }], isError: true };
```

Per spec: input validation errors SHOULD use `isError: true` (tool execution errors) rather than protocol errors — this enables model self-correction.

## Decision rules

- Prefer `ZodRawShape` (`{ name: z.string() }`) for simple inputs — use full `z.object()` only for transforms, refinements, or discriminated unions
- Prefer `isError: true` soft errors over thrown `McpError` for recoverable failures — LLMs handle soft errors better
- Prefer stdio for local-only servers — zero infrastructure, single client
- Prefer Streamable HTTP for remote or multi-client servers
- Prefer stateful HTTP (with `sessionIdGenerator`) when the server needs progress notifications, resumability, or multi-turn context
- Prefer stateless HTTP (`sessionIdGenerator: undefined`) for simple request-response tools
- Set `annotations` on every tool — LLMs use them to decide execution safety; treat annotations as untrusted unless from a trusted server
- Use `server.server` (the underlying `Server`) only when `McpServer` lacks the method you need
- Use `outputSchema` when the tool must return validated structured data alongside text content
- Tool names: use `service_action_resource` format (e.g. `github_search_repos`), 1-128 characters

## Guardrails

- Never use the deprecated `tool()`, `resource()`, or `prompt()` positional-argument methods
- Never use the deprecated `SSEServerTransport` in new servers
- Never use the deprecated `Server` class directly — always go through `McpServer`
- Never expose internal error details to clients — return user-friendly error messages
- Never skip `zod` schemas for tool inputs — unvalidated input is a security risk
- Never hardcode secrets — use environment variables for API keys and tokens
- Never omit graceful shutdown handling for HTTP servers
- Never run HTTP servers on localhost without DNS rebinding protection (`createMcpExpressApp()` or `hostHeaderValidation` middleware)
- Never use `inputSchema: null` — for parameterless tools, omit `inputSchema` entirely
- Servers MUST validate `Origin` header on HTTP transport to prevent DNS rebinding; respond with 403 for invalid origins

## Reference routing

Use the smallest relevant set for the branch of work.

### Start here

| Reference | When to read |
|---|---|
| `references/guides/quick-start.md` | Scaffolding a new server from scratch |
| `references/guides/tools-and-schemas.md` | Registering tools, defining Zod schemas, handling tool results |
| `references/guides/transports.md` | Choosing and configuring stdio, Streamable HTTP, or SSE (legacy) |

### Server capabilities

| Reference | When to read |
|---|---|
| `references/guides/resources-and-prompts.md` | Adding resources (static/template URI) or prompts |
| `references/guides/authentication.md` | Adding OAuth 2.1, bearer tokens, or custom auth |
| `references/guides/client-api.md` | Building MCP clients — connecting, calling tools, reading resources, auth, sampling |
| `references/guides/sessions-and-lifecycle.md` | Managing sessions, sampling, elicitation, resumability, graceful shutdown |
| `references/guides/experimental-tasks.md` | Durable long-running tool operations — registerToolTask, InMemoryTaskStore, callToolStream |
| `references/guides/protocol-spec.md` | Understanding protocol lifecycle, capabilities, message format, security requirements |
| `references/guides/v2-migration.md` | Planning for v2 alpha migration — package split, Standard Schema, ServerContext, framework adapters |

### Build and ship

| Reference | When to read |
|---|---|
| `references/examples/server-recipes.md` | Copy-paste working server examples for common patterns |
| `references/patterns/deployment.md` | Deploying to production (Docker, serverless, cloud) |
| `references/patterns/production-patterns.md` | Logging, error handling, rate limiting, monitoring |
| `references/patterns/anti-patterns.md` | Common mistakes and how to fix them |

### Specification Enhancement Proposals (SEPs)

| Reference | When to read |
|---|---|
| `references/seps/overview.md` | Understanding what SEPs exist and their developer impact |
| `references/seps/auth-security.md` | Implementing OAuth flows, enterprise auth, URL elicitation, client security |
| `references/seps/tools-metadata.md` | Tool naming rules, icons, validation errors, sampling with tools, tasks, tracing |
| `references/seps/protocol-transport.md` | JSON Schema dialect, SSE polling, extensions framework, elicitation improvements, MCP Apps |
| `references/seps/upcoming.md` | Accepted SEPs not yet Final — upcoming breaking changes to prepare for |

## Why migrate to v2?

v2 (`@modelcontextprotocol/server` + `@modelcontextprotocol/client`) shipped in early 2026. Key benefits over v1:

- **Structured handler context** — `ctx.mcpReq.log()`, `ctx.mcpReq.elicitInput()`, `ctx.mcpReq.requestSampling()` replace manual `extra.sendRequest()` calls
- **Framework adapters** — `createMcpExpressApp()` and `createMcpHonoApp()` from dedicated packages instead of manual wiring
- **Standard Schema support** — use Zod v4, Valibot, or ArkType for tool schemas (not locked to Zod)
- **JSON Schema 2020-12 by default** — v1 defaults to Draft-7 via `zod-to-json-schema`; v2 uses native `z.toJSONSchema()`
- **Better auth** — client middleware system (`withOAuth`, `withLogging`, `applyMiddlewares`), grant-agnostic `prepareTokenRequest()`, discovery caching
- **Smaller bundles** — split packages mean you only install what you use
- **ESM-only** — cleaner module resolution, no CJS baggage

Community adoption is still early (Q1 2026 release). Most production servers remain on v1.x. See `references/guides/v2-migration.md` for the full source-verified migration guide, or use `build-mcp-server-sdk-v2` for new v2 projects.

## Compatibility note

This skill targets `@modelcontextprotocol/sdk` v1.x (stable, `v1.x` branch). Source-verified against the TypeScript SDK repository.

Key 2025-11-25 spec additions: icons for tools/resources/prompts, tool name guidance (SEP-986), URL-mode elicitation (SEP-1036), tool calling in sampling (SEP-1577), experimental tasks (SEP-1686), JSON Schema 2020-12 as default dialect (SEP-1613), extensions framework (SEP-2133).
