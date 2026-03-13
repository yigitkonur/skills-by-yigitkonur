---
name: build-mcp-use-server
description: Use skill if you are building MCP servers with the mcp-use TypeScript library — tool registration, Zod schemas, resources, prompts, transports, OAuth providers, session management, middleware, deployment, elicitation, sampling, notifications, widgets, React hooks, CLI tooling, and server configuration.
---

# Build MCP Use Server

Build production-grade MCP servers with the `mcp-use` TypeScript library (v1.21+, Node 22 LTS). The library wraps the official `@modelcontextprotocol/sdk` with a streamlined API: `MCPServer` constructor, Zod-based schemas, 15 response helpers (`text()`, `object()`, `markdown()`, `error()`, `image()`, `audio()`, `binary()`, `html()`, `xml()`, `css()`, `javascript()`, `array()`, `resource()`, `widget()`, `mix()`), built-in OAuth providers, session stores, React hooks (`useMcp`, `useCallTool`, `McpClientProvider`, `useMcpClient`, `useMcpServer`, `useWidget`, `generateHelpers`), and auto-detected transports.

## Decision tree

```
What do you need?
│
├── New server from scratch
│   ├── Minimal stdio server ─────────────► Quick start (below) + references/guides/quick-start.md
│   ├── HTTP/remote server ───────────────► references/guides/quick-start.md + references/guides/transports.md
│   └── OAuth-protected server ───────────► references/guides/quick-start.md + references/guides/authentication.md
│
├── Tools (actions the LLM can invoke)
│   ├── Tool registration & Zod schemas ──► references/guides/tools-and-schemas.md — server.tool(), z.object(), .describe()
│   ├── Context object (ctx) ─────────────► references/guides/tools-and-schemas.md — ctx.auth, ctx.session, ctx.log()
│   └── Tool design best practices ───────► references/guides/tools-and-schemas.md — naming, schemas, annotations
│
├── Response helpers
│   ├── All 15 helpers deep dive ─────────► references/guides/response-helpers.md — text(), object(), mix(), widget(), etc.
│   └── Typed responses & MIME handling ──► references/guides/response-helpers.md — TypedCallToolResult<T>, _meta.mimeType
│
├── Resources & prompts
│   ├── Static & dynamic resources ───────► references/guides/resources-and-prompts.md — server.resource(), URI templates
│   ├── Prompt templates ─────────────────► references/guides/resources-and-prompts.md — server.prompt(), multi-message
│   └── When to use which primitive ──────► references/guides/resources-and-prompts.md — resources vs tools vs prompts
│
├── Transport & networking
│   ├── stdio / httpStream / SSE ─────────► references/guides/transports.md — server.listen(), decision matrix
│   ├── Serverless handlers ──────────────► references/guides/transports.md — Supabase Edge, Cloudflare, Deno Deploy
│   └── DNS rebinding protection ─────────► references/guides/transports.md — allowedOrigins config
│
├── Session management
│   ├── Session stores (memory/Redis/FS) ─► references/guides/session-management.md — pluggable stores, lifecycle
│   ├── Stream managers (distributed) ────► references/guides/session-management.md — RedisStreamManager, scaling
│   └── Session idle timeout ─────────────► references/guides/session-management.md — sessionIdleTimeoutMs config
│
├── Server configuration
│   ├── MCPServer config options ─────────► references/guides/server-configuration.md — full ServerConfig interface
│   ├── CORS / CSP / middleware ──────────► references/guides/server-configuration.md — cors, Express/Hono integration
│   └── Environment variables & logging ──► references/guides/server-configuration.md — env var precedence, ctx.log()
│
├── Authentication
│   ├── Auth0 / WorkOS / Supabase / Keycloak ► references/guides/authentication.md — zero-config OAuth via env vars
│   ├── Custom OAuth provider ────────────► references/guides/authentication.md — oauthCustomProvider()
│   └── Permission-based access ──────────► references/guides/authentication.md — ctx.auth guards
│
├── Elicitation & sampling
│   ├── User input forms (elicitation) ───► references/guides/elicitation-and-sampling.md — ctx.elicit(), Zod schemas, URL
│   └── LLM completions (sampling) ───────► references/guides/elicitation-and-sampling.md — ctx.sample(), model preferences
│
├── Notifications & subscriptions
│   ├── Broadcasting & progress ──────────► references/guides/notifications-and-subscriptions.md — sendNotification, progress
│   ├── Resource subscriptions ───────────► references/guides/notifications-and-subscriptions.md — notifyResourceUpdated
│   └── Client events (roots changed) ────► references/guides/notifications-and-subscriptions.md — onRootsChanged, listRoots
│
├── Widgets & MCP Apps
│   ├── Server-side widget() helper ──────► references/guides/widgets-and-ui.md — widget(), structuredContent, output schemas
│   └── React hooks & components ─────────► references/guides/widgets-and-ui.md — useMcp, useCallTool, McpClientProvider
│
├── CLI tooling
│   ├── Dev / build / start commands ─────► references/guides/cli-reference.md — mcp-use dev, build, start
│   ├── Deploy & generate-types ──────────► references/guides/cli-reference.md — mcp-use deploy, generate-types
│   └── Project scaffolding ──────────────► references/guides/cli-reference.md — npx create-mcp-use-app
│
├── Advanced features
│   ├── Server composition (proxy) ───────► references/guides/advanced-features.md — MCPServer proxy()
│   ├── User context extraction ──────────► references/guides/advanced-features.md — ctx.client.user()
│   ├── Autocomplete (completable) ───────► references/guides/advanced-features.md — completable()
│   └── Client capability detection ──────► references/guides/advanced-features.md — ctx.client.supportsApps()
│
├── Production & deployment
│   ├── Hardening patterns ───────────────► references/patterns/production-patterns.md — shutdown, caching, retries, modules
│   ├── npm / Docker / cloud deploy ──────► references/patterns/deployment.md — Dockerfile, Claude Desktop config
│   └── Pre-deploy checklist ─────────────► references/patterns/deployment.md — full verification list
│
├── Debugging & errors
│   ├── Known error message ──────────────► references/troubleshooting/common-errors.md — 25+ errors with cause/fix
│   ├── Testing with MCP Inspector ───────► references/guides/testing-and-debugging.md — Inspector, curl, Claude Desktop
│   └── Design review ───────────────────► references/patterns/anti-patterns.md — 6 categories of common mistakes
│
└── Complete examples
    ├── Working server recipes ────────────► references/examples/server-recipes.md — filesystem, database, API, multi-tool
    └── Project templates ────────────────► references/examples/project-templates.md — CLI, production HTTP, OAuth
```

## Quick start

Minimal MCP server in 15 lines:

```typescript
import { MCPServer, text } from "mcp-use/server";  // mcp-use ^1.21.0
import { z } from "zod";                               // zod ^4.0.0

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  description: "A simple MCP server",
});

server.tool(
  {
    name: "greet",
    description: "Greet someone by name",
    schema: z.object({
      name: z.string().describe("Name of the person to greet"),
    }),
  },
  async ({ name }) => text(`Hello, ${name}!`)
);

await server.listen();
```

Run: `npx tsx src/server.ts`
Test: `npx @modelcontextprotocol/inspector node dist/server.js`

## Core API

### MCPServer constructor

```typescript
const server = new MCPServer({
  name: "server-name",
  version: "1.0.0",
  description: "What it does",
  title: "My Server",                    // optional — display name for clients
  websiteUrl: "https://example.com",     // optional — project homepage
  icons: [{ src: "icon.svg", mimeType: "image/svg+xml", sizes: ["512x512"] }],
  favicon: "favicon.ico",               // optional — favicon path (relative to public/)
  oauth: oauthAuth0Provider(),           // optional
  sessionStore: new RedisSessionStore(), // optional — see session-management.md
  streamManager: new RedisStreamManager(), // optional — for distributed notifications
  allowedOrigins: ["https://myapp.com"], // optional — DNS rebinding protection
  cors: { origin: ["https://myapp.com"] }, // optional — see server-configuration.md
  stateless: false,                      // optional — auto-detected (Deno=true, Node=false)
  sessionIdleTimeoutMs: 86400000,        // optional — 1 day default
});
```

### Tool registration

```typescript
server.tool(
  {
    name: "action-verb-noun",
    description: "Agent-facing description",
    schema: z.object({
      param: z.string().describe("What this parameter means"),
    }),
    annotations: { readOnlyHint: true, destructiveHint: false },
  },
  async (args, ctx) => text("result") // or any of the 15 response helpers
);
```

### Response helpers

| Helper | Use for |
|--------|---------|
| `text(str)` | Plain text responses |
| `object(obj)` | Structured JSON data |
| `markdown(str)` | Rich formatted text |
| `error(str)` | Expected failures (sets `isError: true`) |
| `image(b64, mime)` | Base64 images |
| `audio(b64, mime)` | Audio content |
| `binary(b64, mime)` | Arbitrary binary data |
| `html(str)` | HTML content |
| `xml(str)` | XML content |
| `css(str)` | CSS stylesheets |
| `javascript(str)` | JavaScript code |
| `array(items)` | Array of items |
| `resource(uri, mimeOrContent, text?)` | Resource references (3-arg or 2-arg with helper) |
| `widget(config)` | MCP App widgets (config: `{ props, output, metadata?, message? }`) |
| `mix(...)` | Multiple content types combined |

Deep dive on all 15 helpers: `references/guides/response-helpers.md`

### Resources and prompts

```typescript
server.resource(
  { name: "config", uri: "config://app", title: "App Config" },
  async () => object({ env: "production" })
);

server.resourceTemplate(
  { name: "users", uriTemplate: "db://users/{id}", mimeType: "application/json" },
  async (uri, params) => text(JSON.stringify(await db.users.get(params.id)))
);

server.prompt(
  { name: "review", description: "Code review", schema: z.object({ code: z.string() }) },
  async ({ code }) => text(`Review this code:\n${code}`)
);
```

### Server composition

```typescript
const server = new MCPServer({ name: "gateway", version: "1.0.0" });

server.proxy({
  github: { command: "npx", args: ["-y", "@modelcontextprotocol/server-github"] },
  db: { url: "https://db-server.example.com/mcp" },
});
// Upstream tools namespaced: github_create_issue, db_query, ...

await server.listen();
```

### User context & autocomplete

```typescript
// Extract connected user info (advisory — unverified, self-reported by client)
server.tool({ name: "whoami", schema: z.object({}) }, async (_args, ctx) => {
  const user = ctx.client.user();
  return text(`Hello, user ${user?.subject}`);
});

// Autocomplete for prompt/resource arguments
import { completable } from "mcp-use/server";

server.prompt(
  { name: "query", schema: z.object({ table: completable(z.string(), async (input) => {
    return ["users", "orders", "products"].filter(t => t.startsWith(input));
  }) }) },
  async ({ table }) => text(`SELECT * FROM ${table}`)
);
```

### React hooks

```typescript
import { useMcp, useCallTool, McpClientProvider, useMcpClient, useMcpServer } from "mcp-use/react";

const mcp = useMcp({ url: "http://localhost:3000/mcp" });
// mcp.state: 'discovering' | 'pending_auth' | 'authenticating' | 'ready' | 'failed'

const { callTool, callToolAsync, data, status, isPending, isError } = useCallTool("greet");
callTool({ name: "World" }, { onSuccess: (result) => console.log(result) });

<McpClientProvider mcpServers={{ main: { url: "..." } }}><App /></McpClientProvider>
const { servers, addServer, removeServer } = useMcpClient();
const server = useMcpServer("main");
```

### Transport

```typescript
await server.listen();        // HTTP on port 3000 (default)
await server.listen(8080);    // HTTP on port 8080
// Port priority: param > --port CLI arg > PORT env var > 3000

// For serverless (Supabase Edge, Cloudflare Workers, Deno Deploy):
const handler = await server.getHandler({ provider: "supabase" });
Deno.serve(handler);
```

### Notifications

```typescript
await server.sendNotification("custom/event", { data: "value" });
await server.sendNotificationToSession(sessionId, "custom/event", data);
await server.notifyResourceUpdated("data://reports/latest");
await server.sendToolsListChanged();
server.onRootsChanged(async (roots) => console.error("Roots changed:", roots));
const roots = await server.listRoots();
const sessions = server.getActiveSessions();
```

### Elicitation & sampling

```typescript
// Elicitation — pause tool and ask user for structured input
const result = await ctx.elicit("Pick a color", z.object({
  color: z.enum(["red", "green", "blue"]).describe("Preferred color"),
}));
if (result.action === "accept") console.log(result.data.color);

// Sampling — request LLM completion from the client
const response = await ctx.sample("Summarize this text: ...");
```

## Rules

1. Every schema field must have `.describe()` — LLMs use descriptions to choose correct arguments.
2. Use response helpers (`text()`, `object()`, `error()`, etc.), not raw `{ content: [...] }` objects.
3. Use `error()` for expected failures, `throw` for unexpected — `error()` returns gracefully.
4. Name tools with action verbs — `search-users`, `create-file`, not `users`, `file`.
5. Keep tools focused — one tool = one action. Split god-tools.
6. Use `console.error()` for debug logs — `console.log()` corrupts the stdio protocol stream.
7. Validate file paths against a root directory — prevent path traversal.
8. Return agent-optimized data — curated summaries, not raw API dumps.
9. Handle graceful shutdown — register SIGTERM/SIGINT for HTTP servers.
10. Never use `z.any()` or `z.unknown()` — always use specific Zod types.

## Common pitfalls

| Mistake | Fix |
|---------|-----|
| Missing `.describe()` on schema fields | Add `.describe()` to every field — LLMs need it |
| `console.log()` in stdio servers | Use `console.error()` or `ctx.log()` |
| Returning 100KB+ JSON responses | Paginate, summarize, return only relevant fields |
| No error handling in tool handlers | Wrap in try/catch, return `error()` |
| `z.any()` or `z.unknown()` schemas | Use specific Zod types with constraints |
| Hardcoded secrets in source | Use environment variables |
| Path traversal in file tools | Validate with `path.resolve()` + prefix check |
| `fs.readFileSync()` in handlers | Use `fs.promises` async API |
| No CORS config on HTTP servers | Set `cors: { origin: [...] }` or `allowedOrigins` — see server-configuration.md |
| Using SSE for new servers | Use `httpStream` — SSE is legacy |
| Notifications in stateless mode | Notifications require persistent sessions (SSE/StreamableHTTP) |
| Elicit without capability check | Guard with `ctx.client.supportsElicitation()` |

## Do this, not that

| Do this | Not that |
|---------|---------|
| Import from `mcp-use/server` | Import from `@modelcontextprotocol/sdk` directly |
| `server.tool()` with Zod schema | Build JSON Schema objects manually |
| Return `text()`, `object()`, `error()` | Return `{ content: [{ type: "text", text: "..." }] }` |
| `server.listen()` for transport | Create `StdioServerTransport` manually |
| `oauthAuth0Provider()` / `oauthKeycloakProvider()` for auth | Build custom OAuth middleware |
| `ctx.log()` for tool logging | `console.log()` (breaks stdio) |
| `ctx.elicit()` for user input | Build custom input collection |
| `widget()` for interactive UI | Return raw HTML strings |
| Split tools into separate files | Put everything in one 1000-line file |

## Build workflow

New server:

1. **Scaffold** — `npx create-mcp-use-app` or manual setup → `references/guides/quick-start.md`
2. **Configure** — MCPServer options, CORS, env vars → `references/guides/server-configuration.md`
3. **Define tools** — register actions with Zod schemas → `references/guides/tools-and-schemas.md`
4. **Add resources/prompts** — data sources and templates → `references/guides/resources-and-prompts.md`
5. **Choose transport** — stdio for local, httpStream for remote → `references/guides/transports.md`
6. **Add auth** — OAuth if needed → `references/guides/authentication.md`
7. **Configure sessions** — store + stream manager → `references/guides/session-management.md`
8. **Test** — MCP Inspector, curl, Claude Desktop → `references/guides/testing-and-debugging.md`
9. **Harden** — error handling, shutdown, caching → `references/patterns/production-patterns.md`
10. **Deploy** — npm, Docker, or cloud → `references/patterns/deployment.md`

Extending an existing server:

1. Read existing tool/resource registrations for the pattern in use
2. Add new capability matching the same style
3. Test with MCP Inspector
4. Review against `references/patterns/anti-patterns.md`

## Companion packages

| Package | Purpose |
|---------|---------|
| `@mcp-use/cli` | Dev server with HMR, `generate-types`, `deploy` — see `references/guides/cli-reference.md` |
| `@mcp-use/inspector` | Built-in web debugger served at `/inspector` on HTTP servers |
| `create-mcp-use-app` | Project scaffolder — `npx create-mcp-use-app my-server` |

## Reference routing

| File | Read when |
|------|-----------|
| `references/guides/quick-start.md` | Starting a new MCP server project from scratch |
| `references/guides/tools-and-schemas.md` | Registering tools, writing Zod schemas, using ctx, or understanding annotations |
| `references/guides/response-helpers.md` | Using any of the 15 response helpers, typed responses, or MIME handling |
| `references/guides/resources-and-prompts.md` | Adding resources or prompts, choosing between primitives, autocomplete |
| `references/guides/transports.md` | Choosing transport (stdio/httpStream/SSE), serverless handlers, DNS rebinding |
| `references/guides/session-management.md` | Configuring session stores (memory/Redis/filesystem), stream managers, idle timeouts |
| `references/guides/server-configuration.md` | MCPServer config options, CORS, CSP, middleware integration, env vars, logging |
| `references/guides/authentication.md` | Setting up OAuth with Auth0, WorkOS, Supabase, Keycloak, or custom providers |
| `references/guides/elicitation-and-sampling.md` | Requesting user input mid-tool (ctx.elicit) or LLM completions (ctx.sample) |
| `references/guides/notifications-and-subscriptions.md` | Broadcasting notifications, progress tracking, resource subscriptions, roots |
| `references/guides/widgets-and-ui.md` | Building MCP App widgets, React hooks (useMcp, useCallTool), client components |
| `references/guides/cli-reference.md` | Using @mcp-use/cli commands: dev, build, start, deploy, generate-types |
| `references/guides/advanced-features.md` | Server composition (proxy), user context, autocomplete (completable), capability detection |
| `references/guides/testing-and-debugging.md` | Testing with MCP Inspector, curl, Claude Desktop, or debugging transport issues |
| `references/patterns/production-patterns.md` | Hardening for production: shutdown, caching, retries, connection pooling, modular organization |
| `references/patterns/deployment.md` | Deploying via npm, Docker, Supabase Edge, or cloud platforms |
| `references/patterns/anti-patterns.md` | Reviewing design for common mistakes in tools, schemas, responses, security, or architecture |
| `references/examples/server-recipes.md` | Need a complete working server example (filesystem, database, API wrapper, multi-tool) |
| `references/examples/project-templates.md` | Need a project template structure (minimal CLI, production HTTP, OAuth-protected) |
| `references/troubleshooting/common-errors.md` | Encountering a specific error message or unexpected behavior (25+ errors cataloged) |

## Guardrails

- Never import from `@modelcontextprotocol/sdk` directly — use `mcp-use/server` exports.
- Never use `console.log()` in stdio servers — it corrupts the protocol stream.
- Never return raw API responses — always curate for agent consumption.
- Never skip `.describe()` on Zod schema fields — it is not optional for MCP tools.
- Never use `z.any()` or `z.unknown()` — always use specific types.
- Never hardcode secrets — use environment variables.
- Never use synchronous I/O (`readFileSync`) in tool handlers — always use async.
- Never skip graceful shutdown for HTTP servers — register signal handlers.
- Always validate file paths against a root directory — prevent path traversal.
- Always test with MCP Inspector before deploying.
