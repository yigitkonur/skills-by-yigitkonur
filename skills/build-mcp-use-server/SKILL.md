---
name: build-mcp-use-server
description: Use skill if you are building MCP servers with the mcp-use TypeScript library — tool registration, Zod schemas, resources, prompts, transports, OAuth, sessions, and deployment.
---

# Build MCP Use Server

Build production-grade MCP servers with the `mcp-use` TypeScript library (v1.21+, Node 18+). The library wraps the official `@modelcontextprotocol/sdk` with a streamlined API: `MCPServer` constructor, object-first registration methods, Zod-based schemas, 15 response helpers (`text()`, `object()`, `markdown()`, `error()`, etc.), built-in OAuth, session stores, and HMR dev server.

All imports come from `mcp-use/server`. Never import from `@modelcontextprotocol/sdk` directly.

---

## When this skill is invoked — behavioral decision flow

Follow this flow every time the skill activates. Do not skip steps.

### Step 1 — Detect what exists in the user's working directory

Run `tree -L 3` (or `ls -R` if tree is unavailable) on the current working directory. Scan the output for signs of an existing mcp-use server implementation:

- `package.json` with `"mcp-use"` as a dependency or devDependency
- Files importing from `"mcp-use/server"`
- `MCPServer` constructor calls (`new MCPServer(`)
- `server.tool()` registrations
- mcp-use config files (e.g., `mcp-use.config.ts`, `.mcp-use/`)

Based on what you find, proceed to Step 2A or Step 2B.

### Step 2A — Existing mcp-use server found

When the codebase already contains an mcp-use server implementation, do NOT start from scratch. Instead, explore and improve what exists.

**Skip subagent exploration if** the codebase was already explored earlier in this conversation (e.g., from a prior task, audit, or plan phase). In that case, summarize known state and proceed directly to improvements. Only launch subagents when the codebase is genuinely unknown.

**Launch subagents to explore the codebase in parallel. Assign each subagent a focused investigation area:**

**Subagent 1 — Tool definitions audit:**
- Read every `server.tool()` registration in the codebase
- Catalog each tool's name, description, schema fields, response pattern
- Check: Does every schema field have `.describe()`? Are tool names action-verb-noun? Are schemas specific (no `z.any()`)?
- Read `references/guides/tools-and-schemas.md` for the exact ToolOptions interface, all ctx methods, and annotation patterns
- Surface: what is working well, what violates best practices, what is missing

**Subagent 2 — Server configuration and transport audit:**
- Read the MCPServer constructor call and all configuration
- Identify: transport mode, CORS setup, middleware, environment variable usage, port configuration
- Check: Is graceful shutdown handled? Is CORS configured for HTTP servers? Are secrets in env vars?
- Read `references/guides/server-configuration.md` for the full ServerConfig interface and env var precedence
- Read `references/guides/transports.md` for transport decision matrix and serverless patterns
- Surface: configuration gaps, security concerns, transport mismatches

**Subagent 3 — Resources, prompts, and notification setup:**
- Read all `server.resource()`, `server.resourceTemplate()`, `server.prompt()` registrations
- Check for notification usage, subscription patterns, elicitation, sampling
- Read `references/guides/resources-and-prompts.md` for resource/prompt registration patterns
- Read `references/guides/notifications-and-subscriptions.md` for broadcast and progress patterns
- Read `references/guides/elicitation-and-sampling.md` for ctx.elicit() and ctx.sample() usage
- Surface: missing primitives that would improve the server, incorrect patterns

**Subagent 4 — Production readiness audit:**
- Assess error handling (try/catch in handlers, error() helper usage)
- Check for logging patterns (ctx.log vs console.log)
- Look for deployment configuration (Dockerfile, deploy scripts, CI/CD)
- Evaluate session management setup
- Read `references/patterns/production-patterns.md` for hardening checklist
- Read `references/patterns/anti-patterns.md` for the 6 categories of common mistakes
- Read `references/patterns/deployment.md` for deploy verification list
- Surface: production blockers, anti-patterns found, deployment readiness

**After all subagents report back:**

1. Synthesize findings into a prioritized improvement plan — most impactful fixes first
2. Apply improvements directly — fix anti-patterns, fill gaps, align with best practices from reference files
3. Only ask the user if a decision genuinely cannot be made without their domain-specific input (e.g., "Should this tool require authentication?" when there is no clear signal either way)

### Step 2B — No existing mcp-use server found

Check whether there is enough context in the working directory to infer what to build:

- An existing REST API, Express/Fastify/Hono app that could be wrapped as an MCP server
- A CLI tool whose commands map naturally to MCP tools
- A database or data source that should be exposed as MCP resources
- A README or spec describing desired functionality

**If context exists:** Infer the right MCP server implementation from the existing codebase. Explain briefly what you plan to build and why, then build it. Read `references/guides/quick-start.md` and `references/examples/project-templates.md` to pick the right starting template.

**If no context exists:** Ask the user focused questions to determine what to build. Ask up to 10 questions, one at a time, each with 5+ numbered options:

1. What kind of data or service will this server expose?
   (1) Filesystem access, (2) Database queries, (3) External API wrapper, (4) Custom business logic, (5) Multi-source aggregator, (6) Other — describe it
2. Which transport do you need?
   (1) stdio — for local CLI tools and Claude Desktop, (2) HTTP — for remote/web access, (3) Both — stdio for dev + HTTP for production, (4) Serverless — Supabase Edge / Cloudflare Workers / Deno Deploy, (5) Not sure — recommend based on use case
3. Does it need authentication?
   (1) None, (2) Bearer token (simple), (3) Auth0, (4) Supabase Auth, (5) WorkOS, (6) Keycloak, (7) Custom OAuth provider, (8) Not sure
4. How many tools do you need initially?
   (1) 1-3 tools, (2) 4-8 tools, (3) 9+ tools — consider modular file organization, (4) Not sure — help me figure it out
5. Will it serve resources (data the LLM can read without calling a tool)?
   (1) Yes — static config/docs, (2) Yes — dynamic data with URI templates, (3) No, (4) Not sure what resources are
6. Will it need interactive widgets or UI?
   (1) No — server only, (2) Yes — use the `build-mcp-use-apps-widgets` skill instead, (3) Maybe later
7. Session management needs?
   (1) In-memory (default, fine for single instance), (2) Redis (production, multi-instance), (3) Filesystem (dev only), (4) Not sure
8. Deployment target?
   (1) Local development only, (2) Docker, (3) Cloud (mcp-use deploy), (4) Serverless edge, (5) npm package distribution, (6) Not sure yet
9. Will tools need to ask users for input mid-execution (elicitation)?
   (1) No, (2) Yes — form-based input, (3) Yes — URL redirects (OAuth/payments), (4) Not sure
10. Will tools need to call an LLM themselves (sampling)?
    (1) No, (2) Yes — summarization/analysis within tools, (3) Not sure

After gathering answers, build the full implementation following the build workflow below.

---

## Quick start

Minimal MCP server using the object-first registration API:

```typescript
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
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

await server.listen(3000);
```

Run: `npm run dev` (with HMR) or `npx tsx src/server.ts`

For the full scaffolding walkthrough (create-mcp-use-app, project structure, package.json setup), read `references/guides/quick-start.md`. For ready-to-copy project templates (minimal CLI, production HTTP, OAuth-protected), read `references/examples/project-templates.md`.

---

## Core API quick reference

### MCPServer constructor

Full `ServerConfig` interface — all fields except `name` and `version` are optional:

```typescript
const server = new MCPServer({
  // Required
  name: "server-name",
  version: "1.0.0",

  // Optional display metadata
  title: "Human-readable title",
  description: "What this server does",
  websiteUrl: "https://example.com",
  favicon: "favicon.ico",
  icons: [{ src: "/icon.svg", mimeType: "image/svg+xml", sizes: ["512x512"] }],

  // Optional networking
  host: "localhost",                       // Default: 'localhost'
  baseUrl: "https://api.example.com",     // Overrides host:port; also read from MCP_URL env
  cors: { origin: ["https://myapp.com"] },
  allowedOrigins: ["https://myapp.com"],  // DNS rebinding protection

  // Optional transport
  stateless: false,                        // Default: false; auto-detect on Deno/edge

  // Optional sessions
  sessionIdleTimeoutMs: 86_400_000,        // Default: 1 day
  sessionStore: new RedisSessionStore({ client: redis }),
  streamManager: new RedisStreamManager({ client: redis, pubSubClient: pubSub }),

  // Optional auth
  oauth: oauthAuth0Provider({ domain: "...", audience: "..." }),
});
```

`baseUrl` resolution: `baseUrl` config > `MCP_URL` env > `http://{host}:{port}`.
`listen(port)` priority: explicit param > `--port` CLI arg > `PORT` env > `3000`.

For the complete ServerConfig interface with all CORS fields, CSP, middleware integration, and env var precedence, read `references/guides/server-configuration.md`.

### MCPServer public methods

| Method | Signature | Purpose |
|--------|-----------|---------|
| `listen` | `listen(port?: number): Promise<void>` | Start server (port = HTTP, no port = stdio) |
| `close` | `close(): Promise<void>` | Stop HTTP listener (graceful, waits for keep-alive drain) |
| `forceClose` | `forceClose(): Promise<void>` | Force-close all connections immediately |
| `terminate` | `terminate(sessionId: string): Promise<void>` | Kill a specific session |
| `getHandler` | `getHandler(options?): RequestHandler` | Serverless handler (Supabase/CF/Deno) |
| `use` | `use(pathOrMiddleware, ...middleware): void` | Add Hono middleware |
| `get` / `post` / `route` | Standard Hono routing | Custom HTTP endpoints alongside MCP |
| `tool` | `tool(options, handler): this` | Register a tool (chainable) |
| `resource` | `resource(options, callback): this` | Register a static resource |
| `resourceTemplate` | `resourceTemplate(options, callback): this` | Register a dynamic resource with URI template |
| `uiResource` | `uiResource(options): this` | Register a UI resource |
| `prompt` | `prompt(options, handler): this` | Register a prompt template |
| `proxy` | `proxy(config): Promise<void>` | Compose upstream MCP servers |
| `sendNotification` | `sendNotification(method, params): Promise<void>` | Broadcast to all clients |
| `sendNotificationToSession` | `sendNotificationToSession(sessionId, method, params): Promise<boolean>` | Notify one session |
| `getActiveSessions` | `getActiveSessions(): string[]` | List live session IDs |
| `sendToolsListChanged` | `sendToolsListChanged(): Promise<void>` | Notify clients tools changed |
| `sendResourcesListChanged` | `sendResourcesListChanged(): Promise<void>` | Notify clients resources changed |
| `sendPromptsListChanged` | `sendPromptsListChanged(): Promise<void>` | Notify clients prompts changed |
| `onRootsChanged` | `onRootsChanged(cb): void` | React to client root changes |
| `listRoots` | `listRoots(sessionId): Promise<Root[] \| undefined>` | Query client roots |

### Tool registration

```typescript
server
  .tool(
    {
      name: "action-verb-noun",
      description: "Agent-facing description of what this tool does",
      schema: z.object({
        param: z.string().describe("What this parameter means"),
      }),
      annotations: { requiresAuth: true, rateLimit: "10/minute" },
    },
    async (args, ctx) => text("result")
  )
  .tool({ name: "tool-two", description: "...", schema: z.object({}) }, async () => text("ok"));
```

`ToolContext` (`ctx`) fields:

```typescript
interface ToolContext {
  log(level: ToolLogLevel, message: string, loggerName?: string): Promise<void>;
  sendNotification(method: string, params: any): Promise<void>;
  reportProgress(current: number, total?: number, message?: string): Promise<void>;
  elicit(message: string, schemaOrUrl: ZodSchema | string, options?: ElicitOptions): Promise<ElicitResult>;
  sample(promptOrParams: string | CreateMessageRequestParams, options?: SampleOptions): Promise<CreateMessageResult>;
  auth?: AuthUser;
  session: { sessionId: string };
  client: {
    info(): { name: string; version: string };
    can(capability: string): boolean;
    capabilities(): Record<string, any>;
    supportsApps(): boolean;
    extension(key: string): any;
    user(): UserContext | undefined;
  };
}
```

For the full ToolOptions interface (including widget field, _meta, all annotation keys), all ctx method signatures, UserContext fields, and tool design best practices, read `references/guides/tools-and-schemas.md`.

### Response helpers

Import all from `mcp-use/server`:

```typescript
import {
  text, markdown, html, xml, css, javascript,
  object, array,
  image, audio, binary,
  resource, error,
  mix, widget
} from "mcp-use/server";
```

| Helper | Returns | Notes |
|--------|---------|-------|
| `text(content)` | `CallToolResult` | Plain text, `text/plain` |
| `markdown(content)` | `CallToolResult` | Markdown, `text/markdown` |
| `html(content)` | `CallToolResult` | HTML, `text/html` |
| `xml(content)` | `CallToolResult` | XML, `text/xml` |
| `css(content)` | `CallToolResult` | CSS, `text/css` |
| `javascript(content)` | `CallToolResult` | JS, `text/javascript` |
| `object(payload)` | `TypedCallToolResult<T>` | JSON with structuredContent, `application/json` |
| `array(items)` | `TypedCallToolResult<{ data: T[] }>` | Wraps in `{ data: items }` |
| `image(base64, mimeType?)` | `CallToolResult` | Base64 string (NOT Buffer). Default: `image/png` |
| `audio(dataOrPath, mimeType?)` | `CallToolResult \| Promise` | Base64 string or file path. File path returns Promise |
| `binary(base64, mimeType)` | `CallToolResult` | Any binary data |
| `resource(uri, mimeType, text)` | `CallToolResult` | Embed a resource reference |
| `error(message)` | `CallToolResult` | `isError: true` — for expected failures |
| `mix(...parts)` | `CallToolResult` | Combine multiple helper results |
| `widget(params)` | `CallToolResult` | Interactive UI (structuredContent hidden from LLM) |

For all overloads, WidgetParams interface, TypedCallToolResult details, and MIME type handling, read `references/guides/response-helpers.md`.

### Resources and prompts (pattern overview)

```typescript
server
  .resource(
    { name: "config", uri: "config://app", description: "App settings" },
    async () => object({ env: "production" })
  )
  .resourceTemplate(
    {
      name: "users",
      uriTemplate: "db://users/{id}",
      callbacks: {
        complete: {
          id: async (value) => (await db.getIds()).filter(id => id.startsWith(value)),
        },
      },
    },
    async (uri, { id }) => text(JSON.stringify(await db.users.get(id)))
  )
  .prompt(
    { name: "review", description: "Code review", schema: z.object({ code: z.string() }) },
    async ({ code }) => text(`Review this code:\n${code}`)
  );
```

For all resource callback overloads, annotation fields (audience, priority, lastModified), prompt message formats, and when-to-use-which-primitive guidance, read `references/guides/resources-and-prompts.md`.

### Hono proxy methods

`MCPServer` exposes Hono routing for custom HTTP endpoints alongside the MCP transport:

```typescript
server.get("/health", (c) => c.json({ status: "ok" }));
server.post("/webhook", async (c) => c.json({ received: true }));
server.use(async (c, next) => { console.error(`${c.req.method} ${c.req.url}`); await next(); });
server.use("/api/admin/*", async (c, next) => {
  if (c.req.header("x-api-key") !== process.env.API_KEY) return c.json({ error: "Unauthorized" }, 401);
  await next();
});
```

---

## Reference routing — read these when you need depth

Each reference file below contains the full, fact-checked API documentation for its topic. The SKILL.md gives you enough to start; the references give you everything.

### Guides

- **`references/guides/quick-start.md`** — Starting a brand-new MCP server project? This has the full scaffolding walkthrough: `npx create-mcp-use-app`, project structure, package.json scripts, first tool registration, and running with HMR. Start here for any greenfield build.

- **`references/guides/server-configuration.md`** — Need to configure CORS origins, CSP headers, custom middleware, or understand how `baseUrl`, `MCP_URL`, `PORT`, and `--port` interact? This file has the complete ServerConfig interface and environment variable precedence rules.

- **`references/guides/cli-reference.md`** — Using the `@mcp-use/cli` for `mcp-use dev`, `mcp-use build`, `mcp-use start`, `mcp-use deploy`, or `mcp-use generate-types`? This file documents every command, flag, and behavior.

- **`references/guides/tools-and-schemas.md`** — Registering tools, defining Zod schemas, or wondering what fields `ctx` exposes? This has the exact ToolOptions interface, all ctx methods (log, elicit, sample, reportProgress, sendNotification), UserContext fields, and annotation patterns. Read it any time you write a `server.tool()` call.

- **`references/guides/resources-and-prompts.md`** — Adding resources or prompts to a server? This covers static resources, dynamic URI templates with autocomplete callbacks, prompt registration with multi-message returns, and the decision framework for when to use resources vs tools vs prompts.

- **`references/guides/response-helpers.md`** — Using any of the 15 response helpers, combining them with `mix()`, returning typed structured data with `object()`, or building widget responses? This has every overload, every MIME type, and the TypedCallToolResult generic.

- **`references/guides/session-management.md`** — Dealing with Redis sessions, distributed SSE, session idle timeouts, or scaling across multiple instances? This has the full store comparison (InMemory vs Redis vs FileSystem), constructor options for each store, RedisStreamManager setup, and session lifecycle methods.

- **`references/guides/authentication.md`** — Setting up OAuth with Auth0, WorkOS, Supabase, Keycloak, or a custom provider? This documents every built-in provider function, the OAuthMode enum (Proxy vs Direct), ctx.auth shape, permission guards, and the OAuth endpoints the server auto-exposes.

- **`references/guides/elicitation-and-sampling.md`** — Need a tool to pause and ask the user for structured input (ctx.elicit) or invoke an LLM completion within a tool (ctx.sample)? This covers Form mode, URL mode, enum schema helpers (SEP-1330), SampleOptions, model preferences, capability guards, and the full CreateMessageResult shape.

- **`references/guides/notifications-and-subscriptions.md`** — Broadcasting to all clients, sending targeted notifications to a session, reporting progress from tools, or reacting to client root changes? This has sendNotification, sendNotificationToSession, ctx.reportProgress, onRootsChanged, listRoots, and all built-in notification method strings.

- **`references/guides/widgets-and-ui.md`** — Building server-side widget responses with `widget()`, defining output schemas, or wiring up React hooks (`useMcp`, `useCallTool`, `McpClientProvider`)? This is the full widgets reference. If the user wants a full MCP App with client-side UI, suggest the `build-mcp-use-apps-widgets` skill instead.

- **`references/guides/transports.md`** — Choosing between stdio, httpStream, and SSE? Deploying to serverless platforms (Supabase Edge, Cloudflare Workers, Deno Deploy)? Configuring DNS rebinding protection with `allowedOrigins`? This file has the transport decision matrix and all handler patterns.

- **`references/guides/advanced-features.md`** — Composing multiple MCP servers with `server.proxy()`, extracting user context with `ctx.client.user()`, adding autocomplete with `completable()` (for prompts) or `callbacks.complete` (for resource templates), or detecting client capabilities? This covers all advanced API surface.

- **`references/guides/testing-and-debugging.md`** — Testing with MCP Inspector, debugging with curl against the HTTP transport, configuring Claude Desktop for local testing, or diagnosing transport-level issues? This has the full testing toolkit and debugging strategies.

### Patterns

- **`references/patterns/production-patterns.md`** — Hardening a server for production? This covers graceful shutdown (SIGTERM/SIGINT handlers), response caching, retry strategies, connection pooling, modular file organization for large servers, and the full production readiness checklist.

- **`references/patterns/deployment.md`** — Ready to deploy? This has npm package distribution, Docker multi-stage builds, `mcp-use deploy` to Manufact Cloud, Claude Desktop configuration, Supabase Edge functions, and a pre-deploy verification checklist.

- **`references/patterns/anti-patterns.md`** — Reviewing a server design or doing a code audit? This catalogs the 6 categories of common mistakes: tool design, schema definition, response formatting, security, architecture, and error handling. Each anti-pattern includes the bad code, why it is wrong, and the fix.

### Examples

- **`references/examples/server-recipes.md`** — Need a complete working server example? This has filesystem server, database server, API wrapper, and multi-tool server recipes — each production-ready and safe to copy.

- **`references/examples/project-templates.md`** — Need a full project template with directory structure, package.json, tsconfig, and all the scaffolding? This has minimal CLI template, production HTTP template, and OAuth-protected template.

### Troubleshooting

- **`references/troubleshooting/common-errors.md`** — Hit a specific error message or unexpected behavior? This catalogs 25+ errors with their exact message, root cause, and fix. Check here before debugging from scratch.

---

## Build workflow

### New server (Step 2B path)

1. **Scaffold** — `npx create-mcp-use-app` or manual setup. Read `references/guides/quick-start.md` and `references/examples/project-templates.md`.
2. **Configure** — Set MCPServer options, CORS, env vars. Read `references/guides/server-configuration.md`.
3. **Define tools** — Register actions with Zod schemas. Read `references/guides/tools-and-schemas.md`.
4. **Add resources/prompts** — Expose data sources and templates. Read `references/guides/resources-and-prompts.md`.
5. **Choose transport** — stdio for local, httpStream for remote. Read `references/guides/transports.md`.
6. **Add auth** — OAuth if needed. Read `references/guides/authentication.md`.
7. **Configure sessions** — Store + stream manager. Read `references/guides/session-management.md`.
8. **Test** — MCP Inspector, curl, Claude Desktop. Read `references/guides/testing-and-debugging.md`.
9. **Harden** — Error handling, shutdown, caching. Read `references/patterns/production-patterns.md`.
10. **Deploy** — `mcp-use deploy` or Docker. Read `references/patterns/deployment.md`.

### Extending an existing server (Step 2A path)

1. Run the subagent exploration described in Step 2A
2. Synthesize findings into a prioritized improvement plan
3. Apply improvements — fix anti-patterns, add missing capabilities, align with best practices
4. Validate against `references/patterns/anti-patterns.md`
5. Test with MCP Inspector — read `references/guides/testing-and-debugging.md`

---

## Rules

1. Every Zod schema field must have `.describe()` — LLMs use descriptions to choose correct arguments.
2. Use response helpers (`text()`, `object()`, `error()`, etc.), not raw `{ content: [...] }` objects.
3. Use `error()` for expected failures, `throw` for unexpected — `error()` returns gracefully to the client.
4. Name tools with action verbs — `search-users`, `create-file`, not `users`, `file`.
5. Keep tools focused — one tool = one action. Split god-tools into multiple specific tools.
6. Use `console.error()` for debug logs — `console.log()` corrupts the stdio protocol stream.
7. Validate file paths against a root directory — prevent path traversal attacks.
8. Return agent-optimized data — curated summaries, not raw 100KB API dumps.
9. Handle graceful shutdown — register SIGTERM/SIGINT for HTTP servers.
10. Never use `z.any()` or `z.unknown()` — always use specific Zod types with constraints.
11. Always check `ctx.client.can("elicitation")` before calling `ctx.elicit()`.
12. Always check `ctx.client.can("sampling")` before calling `ctx.sample()`.
13. Always test with MCP Inspector before deploying.

---

## Common pitfalls

| Mistake | Fix |
|---------|-----|
| Missing `.describe()` on schema fields | Add `.describe()` to every field — LLMs need it to pick correct arguments |
| `console.log()` in stdio servers | Use `console.error()` or `ctx.log()` — stdout is the protocol stream |
| Returning 100KB+ JSON responses | Paginate, summarize, return only relevant fields |
| No error handling in tool handlers | Wrap in try/catch, return `error()` for expected failures |
| `z.any()` or `z.unknown()` schemas | Use specific Zod types with constraints |
| Hardcoded secrets in source | Use environment variables, never commit secrets |
| Path traversal in file tools | Validate with `path.resolve()` + prefix check against allowed root |
| `fs.readFileSync()` in handlers | Use `fs.promises` async API — sync I/O blocks the event loop |
| No CORS config on HTTP servers | Set `cors: { origin: [...] }` or `allowedOrigins` in constructor |
| Using SSE for new servers | Use httpStream (`server.listen(port)`) — SSE is legacy |
| Notifications in stateless mode | Notifications require persistent sessions (SSE/StreamableHTTP) |
| Elicit without capability check | Guard with `ctx.client.can("elicitation")` before `ctx.elicit()` |
| Using `ctx.log("warn", ...)` | Use `ctx.log("warning", ...)` — the correct level name is "warning" |
| `completable()` on tool() schema | `completable()` only works with `prompt()` — use `callbacks.complete` for `resourceTemplate()` |
| Passing Buffer to `image()` | `image()` takes a base64 **string**, not a Buffer — convert with `.toString("base64")` first |
| `audio()` used sync with file path | `audio(filePath)` returns a Promise when given a path — must be awaited |
| Missing `description` on prompt | `description` is required in PromptOptions, not optional |

---

## Do this, not that

| Do this | Not that |
|---------|---------|
| Import from `mcp-use/server` | Import from `@modelcontextprotocol/sdk` directly |
| `server.tool()` with object-first form and Zod schema | Build JSON Schema objects manually |
| Return `text()`, `object()`, `error()` | Return `{ content: [{ type: "text", text: "..." }] }` |
| `server.listen(port)` for HTTP, `server.listen()` for stdio | Create `StdioServerTransport` manually |
| `oauthAuth0Provider()` / `oauthKeycloakProvider()` for auth | Build custom OAuth middleware from scratch |
| `ctx.log("warning", ...)` for tool logging | `ctx.log("warn", ...)` — wrong level name |
| `ctx.elicit()` for user input | Build custom input collection mechanisms |
| `widget()` for interactive UI | Return raw HTML strings |
| Split tools into separate files for large servers | Put everything in one 1000-line file |
| `npm run dev` (calls `mcp-use dev` with HMR) | `node src/server.ts` directly (no HMR) |
| `image(base64String, "image/png")` | `image(buffer, ...)` — wrong type |
| `error("Not found")` for expected failures | `throw new Error("Not found")` in tool handlers |
| `ctx.client.can("sampling")` then `ctx.sample()` | Call `ctx.sample()` without checking capability |

---

## Guardrails

These are hard rules. Violating any of them produces broken or insecure servers:

- Never import from `@modelcontextprotocol/sdk` directly — use `mcp-use/server` exports.
- Never use `console.log()` in stdio servers — it corrupts the protocol stream. Use `console.error()`.
- Never return raw API responses to the LLM — always curate for agent consumption.
- Never skip `.describe()` on Zod schema fields — it is not optional for MCP tools.
- Never use `z.any()` or `z.unknown()` — always use specific types.
- Never hardcode secrets — use environment variables.
- Never use synchronous I/O (`readFileSync`) in tool handlers — always use async.
- Never skip graceful shutdown for HTTP servers — register SIGTERM/SIGINT signal handlers.
- Always validate file paths against a root directory — prevent path traversal.
- Always test with MCP Inspector before deploying.
- Always check `ctx.client.can("elicitation")` before calling `ctx.elicit()`.
- Always check `ctx.client.can("sampling")` before calling `ctx.sample()`.

---

## Deployment quick reference

**Before deploying:**
1. Commit and push all changes to GitHub — `mcp-use deploy` builds from the remote HEAD, NOT your working directory
2. Verify `pnpm typecheck` (or `npm run typecheck`) passes — broken code will fail the cloud build
3. Always use `--name` to set a meaningful deployment name — it controls the URL subdomain

```bash
# Scaffold
npx create-mcp-use-app my-server

# Develop with HMR
npm run dev

# Build and test locally
mcp-use build
mcp-use start

# Deploy to Manufact Cloud
mcp-use login
mcp-use deploy --name my-server   # ← always set --name; auto-generated names are random words
```

**Naming:** `--name` sets a human-readable label for the deployment (stored in `.mcp-use/project.json` as `deploymentName`). The URL subdomain is auto-generated by Manufact Cloud (e.g., `black-silence-ot8sz.run.mcp-use.com`) and does NOT match the `--name`. The URL is stable across redeployments as long as `.mcp-use/project.json` is preserved.

**Post-deploy verification:**
1. `curl -s https://{url}/health | jq .status` — should return `"ok"`
2. Open the Inspector URL from the deploy output — confirm all tools appear
3. Update client configs (Claude Desktop, Codex, etc.) with the new URL

After deploy:
- **MCP Server URL**: `https://<auto-subdomain>.run.mcp-use.com/mcp`
- **Inspector URL**: `https://inspector.manufact.com/inspector?autoConnect=https://<auto-subdomain>.run.mcp-use.com/mcp`
- **Dashboard**: `https://manufact.com/cloud/servers/<auto-subdomain>`

Claude Desktop config:
```json
{
  "mcpServers": {
    "my-server": {
      "url": "https://<id>.deploy.mcp-use.com/mcp"
    }
  }
}
```

For Docker builds, Supabase Edge, Cloudflare Workers, npm distribution, and the full pre-deploy checklist, read `references/patterns/deployment.md`. For CLI command details, read `references/guides/cli-reference.md`.

---

## Companion packages

| Package | Purpose |
|---------|---------|
| `@mcp-use/cli` | Dev server with HMR, `generate-types`, `deploy` — see `references/guides/cli-reference.md` |
| `@mcp-use/inspector` | Built-in web debugger served at `/inspector` on HTTP servers |
| `create-mcp-use-app` | Project scaffolder — `npx create-mcp-use-app my-server` |
