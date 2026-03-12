---
name: build-mcp-use-server
description: Use skill if you are building MCP servers with the mcp-use TypeScript library — tool registration, Zod schemas, resources, prompts, transports, OAuth providers, session management, middleware, and deployment.
---

# Build MCP Use Server

Build production-grade MCP servers with the `mcp-use` TypeScript library. The library wraps the official `@modelcontextprotocol/sdk` with a streamlined API: `MCPServer` constructor, Zod-based schemas, response helpers (`text()`, `object()`, `error()`), built-in OAuth providers, session stores, and auto-detected transports.

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
│   ├── Response helpers ─────────────────► references/guides/tools-and-schemas.md — text(), object(), markdown(), error(), mix()
│   ├── Context object (ctx) ─────────────► references/guides/tools-and-schemas.md — ctx.auth, ctx.session, ctx.log(), ctx.elicit()
│   └── Tool design best practices ───────► references/guides/tools-and-schemas.md — naming, schemas, annotations
│
├── Resources & prompts
│   ├── Static & dynamic resources ───────► references/guides/resources-and-prompts.md — server.resource(), URI templates
│   ├── Prompt templates ─────────────────► references/guides/resources-and-prompts.md — server.prompt(), multi-message
│   └── When to use which primitive ──────► references/guides/resources-and-prompts.md — resources vs tools vs prompts
│
├── Transport & sessions
│   ├── stdio / httpStream / SSE ─────────► references/guides/transports.md — server.listen() options, decision matrix
│   ├── Session stores (memory/Redis) ────► references/guides/transports.md — InMemorySessionStore, RedisSessionStore
│   └── DNS rebinding protection ─────────► references/guides/transports.md — allowedOrigins config
│
├── Authentication
│   ├── Auth0 / WorkOS / Supabase ────────► references/guides/authentication.md — zero-config OAuth via env vars
│   ├── Custom OAuth provider ────────────► references/guides/authentication.md — oauthCustomProvider()
│   └── Permission-based access ──────────► references/guides/authentication.md — ctx.auth guards
│
├── Advanced features
│   ├── Elicitation (user input forms) ───► references/guides/advanced-features.md — ctx.elicit()
│   ├── Sampling (LLM completions) ───────► references/guides/advanced-features.md — ctx.sample()
│   ├── Notifications & progress ─────────► references/guides/advanced-features.md — ctx.sendNotification()
│   ├── Middleware (Express/Hono) ─────────► references/guides/advanced-features.md — server.use(), server.get()
│   └── Widgets (MCP Apps) ───────────────► references/guides/advanced-features.md — widget(), ctx.client.supportsApps()
│
├── Production & deployment
│   ├── Hardening patterns ───────────────► references/patterns/production-patterns.md — shutdown, caching, retries, modules
│   ├── npm / Docker / cloud deploy ──────► references/patterns/deployment.md — Dockerfile, Claude Desktop config
│   └── Pre-deploy checklist ─────────────► references/patterns/deployment.md — full verification list
│
├── Debugging & errors
│   ├── Known error message ──────────────► references/troubleshooting/common-errors.md — 18 errors with cause/fix
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
import { MCPServer, text } from "mcp-use/server";
import z from "zod";

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
  oauth: oauthAuth0Provider(),           // optional
  sessionStore: new RedisSessionStore(), // optional
  allowedOrigins: ["https://myapp.com"], // optional
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
  async (args, ctx) => text("result") // or object(), markdown(), error(), mix()
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
| `mix(...)` | Multiple content types combined |

### Resources and prompts

```typescript
server.resource(
  { name: "config", uri: "config://app", title: "App Config" },
  async () => object({ env: "production" })
);

server.prompt(
  { name: "review", description: "Code review", schema: z.object({ code: z.string() }) },
  async ({ code }) => text(`Review this code:\n${code}`)
);
```

### Transport

```typescript
await server.listen();                                             // stdio (default)
await server.listen({ transportType: "httpStream", port: 3000 }); // HTTP
await server.listen({ transportType: "sse", port: 3000 });        // SSE (legacy)
```

## Rules

1. Every schema field must have `.describe()` — LLMs use descriptions to choose correct arguments.
2. Use response helpers (`text()`, `object()`, `error()`), not raw `{ content: [...] }` objects.
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
| No CORS config on HTTP servers | Set `cors: true` or `allowedOrigins` |
| Using SSE for new servers | Use `httpStream` — SSE is legacy |

## Do this, not that

| Do this | Not that |
|---------|---------|
| Import from `mcp-use/server` | Import from `@modelcontextprotocol/sdk` directly |
| `server.tool()` with Zod schema | Build JSON Schema objects manually |
| Return `text()`, `object()`, `error()` | Return `{ content: [{ type: "text", text: "..." }] }` |
| `server.listen()` for transport | Create `StdioServerTransport` manually |
| `oauthAuth0Provider()` for auth | Build custom OAuth middleware |
| `ctx.log()` for tool logging | `console.log()` (breaks stdio) |
| `ctx.elicit()` for user input | Build custom input collection |
| Split tools into separate files | Put everything in one 1000-line file |

## Build workflow

New server:

1. **Scaffold** — project setup with package.json, tsconfig.json, src/server.ts → `references/guides/quick-start.md`
2. **Define tools** — register actions with Zod schemas → `references/guides/tools-and-schemas.md`
3. **Add resources/prompts** — data sources and templates → `references/guides/resources-and-prompts.md`
4. **Choose transport** — stdio for local, httpStream for remote → `references/guides/transports.md`
5. **Add auth** — OAuth if needed → `references/guides/authentication.md`
6. **Test** — MCP Inspector, curl, Claude Desktop → `references/guides/testing-and-debugging.md`
7. **Harden** — error handling, shutdown, caching → `references/patterns/production-patterns.md`
8. **Deploy** — npm, Docker, or cloud → `references/patterns/deployment.md`

Extending an existing server:

1. Read existing tool/resource registrations for the pattern in use
2. Add new capability matching the same style
3. Test with MCP Inspector
4. Review against `references/patterns/anti-patterns.md`

## Reference routing

| File | Read when |
|------|-----------|
| `references/guides/quick-start.md` | Starting a new MCP server project from scratch |
| `references/guides/tools-and-schemas.md` | Registering tools, writing Zod schemas, using response helpers, or understanding ctx |
| `references/guides/resources-and-prompts.md` | Adding resources or prompts, choosing between primitives |
| `references/guides/transports.md` | Choosing transport, configuring sessions, setting up middleware |
| `references/guides/authentication.md` | Setting up OAuth with Auth0, WorkOS, Supabase, or custom providers |
| `references/guides/advanced-features.md` | Elicitation, sampling, notifications, widgets, or client capability detection |
| `references/guides/testing-and-debugging.md` | Testing with MCP Inspector, curl, Claude Desktop, or debugging |
| `references/patterns/production-patterns.md` | Hardening for production: shutdown, caching, retries, connection pooling, modular organization |
| `references/patterns/deployment.md` | Deploying via npm, Docker, Supabase Edge, or cloud platforms |
| `references/patterns/anti-patterns.md` | Reviewing design for common mistakes in tools, schemas, responses, security, or architecture |
| `references/examples/server-recipes.md` | Need a complete working server example (filesystem, database, API wrapper, multi-tool) |
| `references/examples/project-templates.md` | Need a project template structure (minimal CLI, production HTTP, OAuth-protected) |
| `references/troubleshooting/common-errors.md` | Encountering a specific error message or unexpected behavior |

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
