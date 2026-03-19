# Advanced Features

Server composition, autocomplete, client introspection, and how mcp-use compares to alternative MCP implementations.

---

## 1. Server Composition / Proxy

`server.proxy()` combines multiple upstream MCP servers into a single aggregator endpoint. Tools, resources, and prompts from each child server are namespaced to avoid collisions.

### Config-Based Proxy (Recommended)

```typescript
import { MCPServer } from "mcp-use/server";
import path from "node:path";

const server = new MCPServer({ name: "UnifiedServer", version: "1.0.0" });

await server.proxy({
  // Proxy a local TypeScript server
  database: {
    command: "tsx",
    args: [path.resolve(__dirname, "./db-server.ts")],
  },

  // Proxy a local Python server
  weather: {
    command: "uv",
    args: ["run", "weather_server.py"],
    env: { ...process.env, FASTMCP_LOG_LEVEL: "ERROR" },
  },

  // Proxy a remote server over HTTP
  manufact: {
    url: "https://manufact.com/docs/mcp",
  },
});

// Add aggregator-level tools alongside proxied ones
server.tool(
  { name: "aggregator_status", description: "Check aggregator status" },
  async () => ({ content: [{ type: "text", text: "All systems operational" }] })
);

await server.listen(3000);
```

Child tools are prefixed with their namespace key — `database_query`, `weather_get_forecast`, etc.

### Session-Based Proxy (Advanced)

For dynamic auth headers or custom connection lifecycles, inject an explicit `MCPSession`:

```typescript
import { MCPServer } from "mcp-use/server";
import { MCPClient } from "mcp-use/client";

const server = new MCPServer({ name: "UnifiedServer", version: "1.0.0" });

const client = new MCPClient({
  mcpServers: { secure_db: { url: "https://secure-db.example.com/mcp" } },
});
const dbSession = await client.createSession("secure_db");

await server.proxy(dbSession, { namespace: "secure_db" });
await server.listen(3000);
```

### How Proxying Works

1. **Introspects** the child server (`listTools`, `listResources`, `listPrompts`).
2. **Translates** raw JSON Schemas into runtime Zod schemas for validation.
3. **Namespaces** component names to prevent collisions.
4. **Relays** execution — forwards tool calls to the child server.
5. **Synchronizes** state — listens for `list_changed` notifications and forwards them to all aggregator clients.

The proxy also transparently handles sampling, elicitation, and progress tracking requests from child servers, routing them back to the correct user's client.

### Resource URI Namespacing

To prevent URI collisions across different servers, the proxy automatically prepends the namespace to the resource URI protocol. For example, if the `weather` server exposes a resource at `app://settings`, the Aggregator exposes it as `weather://app://settings`. When a client reads that resource, the Aggregator strips the prefix and requests the original URI from the child server.

---

## 2. Autocomplete (completable)

The `completable()` helper enables argument completion suggestions for prompts and resource templates. Clients request suggestions via the MCP `completion/complete` protocol method.

### List-Based Completion

Pass a static array of values — the SDK handles case-insensitive prefix filtering:

```typescript
import { MCPServer, completable } from "mcp-use/server";
import { z } from "zod";

server.prompt(
  {
    name: "code-review",
    description: "Review code with language completion",
    schema: z.object({
      language: completable(z.string(), [
        "python", "javascript", "typescript", "java", "cpp",
      ]),
      code: z.string().describe("The code to review"),
    }),
  },
  async ({ language, code }) => ({
    messages: [{ role: "system", content: `Review this ${language} code: ${code}` }],
  })
);
```

### Callback-Based Completion (Dynamic)

For context-aware suggestions, pass an async function. The callback receives the current input value and optional context containing other argument values:

```typescript
server.prompt(
  {
    name: "analyze-project",
    schema: z.object({
      projectId: completable(z.string(), async (value, context) => {
        const userId = context?.arguments?.userId;
        const projects = await fetchUserProjects(userId);
        return projects.filter((p) => p.id.startsWith(value)).map((p) => p.id);
      }),
    }),
  },
  async ({ projectId }) => ({
    messages: [{ role: "system", content: `Analyzing project ${projectId}...` }],
  })
);
```

### Resource Template Completion

```typescript
server.resourceTemplate(
  {
    name: "user_data",
    uriTemplate: "user://{userId}/profile",
    callbacks: {
      complete: {
        userId: ["user-1", "user-2", "user-3"],
        // Or dynamic: userId: async (value) => fetchUserIds(value),
      },
    },
  },
  async (uri, { userId }) => text(`User: ${userId}`)
);
```

---

## 3. User Context Extraction

`ctx.client.user()` returns per-invocation caller metadata from `params._meta`. It returns `undefined` for clients that do not send this metadata (Inspector, Claude Desktop, CLI, etc.).

> **Warning:** This data is client-reported and unverified. Do not use it for access control. For verified identity, use OAuth authentication with `ctx.auth`.

```typescript
server.tool({ name: "personalise", schema: z.object({}) }, async (_p, ctx) => {
  const caller = ctx.client.user();

  if (!caller) return text("Hello! (no caller context available)");

  const city = caller.location?.city ?? "there";
  const greeting = caller.locale?.startsWith("it") ? "Ciao" : "Hello";
  return text(`${greeting} from ${city}!`);
});
```

**`UserContext` fields:**

| Field | Type | Description |
|---|---|---|
| `subject` | `string` | Stable opaque user identifier (same across conversations) |
| `conversationId` | `string` | Current chat thread ID (changes per chat) |
| `locale` | `string` | BCP-47 locale, e.g. `"it-IT"` — detected server-side at session start |
| `location` | `object` | `{ city, region, country, timezone, latitude, longitude }` |
| `userAgent` | `string` | Browser / host user-agent string |
| `timezoneOffsetMinutes` | `number` | UTC offset in minutes |

**`locale` note:** `ctx.client.user()?.locale` is detected server-side from the user's account language at session start. Inside a widget, `useWidget().locale` is preferred — it reads the same preference client-side and is therefore fresher and browser-aware.

**ChatGPT multi-tenant model:** ChatGPT establishes a **single MCP session for all users** of a deployed app. Use `ctx.client.user()?.subject` to identify individual users and `conversationId` for chat threads:

```typescript
// Session hierarchy:
// 1 MCP session  ctx.session.sessionId              — shared across ALL users
//   N subjects   ctx.client.user()?.subject         — one per ChatGPT user account
//     M threads  ctx.client.user()?.conversationId  — one per chat conversation

server.tool({ name: "identify-caller", schema: z.object({}) }, async (_p, ctx) => {
  const caller = ctx.client.user();
  return object({
    mcpSession:   ctx.session.sessionId,         // shared transport session
    user:         caller?.subject ?? null,        // ChatGPT user ID
    conversation: caller?.conversationId ?? null, // this chat thread
  });
});
```

---

## 4. Client Capability Checking

Use `ctx.client` methods to adapt behaviour based on what the connected client supports:

```typescript
server.tool({ name: "smart-tool", schema: z.object({}) }, async (_p, ctx) => {
  // Client name and version from the MCP initialize handshake
  const { name, version } = ctx.client.info();

  // Check specific capabilities
  const hasSampling    = ctx.client.can("sampling");
  const hasElicitation = ctx.client.can("elicitation");

  // Check MCP Apps / widget support (SEP-1865)
  const isAppsClient = ctx.client.supportsApps();

  // Access raw MCP extensions
  const uiExt = ctx.client.extension("io.modelcontextprotocol/ui");

  // Branch logic based on capabilities
  if (hasSampling && hasElicitation) {
    // Use both sampling and elicitation
  } else if (hasSampling) {
    // Sampling only — fall back to simpler flow
  } else {
    // Basic text response
  }

  return text(`${name} v${version}, apps: ${isAppsClient}`);
});
```

**Key methods on `ctx.client`:**

| Method | Returns | Description |
|---|---|---|
| `info()` | `{ name, version }` | Client name and version from initialize handshake |
| `can(capability)` | `boolean` | Check for `"sampling"`, `"elicitation"`, `"roots"`, etc. |
| `supportsApps()` | `boolean` | Convenience check for MCP Apps support (SEP-1865) |
| `extension(id)` | `object \| undefined` | Access raw MCP extension data by ID |
| `user()` | `UserContext \| undefined` | Per-invocation caller metadata (see §3) |

---

## 5. Comparison with Other MCP Implementations

| Feature | mcp-use | Official SDK | FastMCP | tmcp | xmcp |
|---------|---------|-------------|---------|------|------|
| Language | TypeScript | TypeScript | Python | JavaScript | TypeScript |
| Stateful + Stateless | ✅ | ✅ | ✅ | Stateful only | Stateless only |
| Registration Replay | ✅ | ❌ | ❌ | ❌ | ❌ |
| Auto Runtime Detection | ✅ | ❌ | ❌ | ❌ | ❌ |
| Redis Sessions | ✅ | ❌ | ✅ | ✅ | N/A |
| Distributed Notifications | ✅ | ❌ | ✅ | ✅ | N/A |
| Server Composition (Proxy) | ✅ | ❌ | ❌ | ❌ | ❌ |

### Key mcp-use Advantages

- **Registration replay** — register tools/prompts/resources once; they are automatically replayed for each new session. The official SDK requires re-registration per session.
- **Auto runtime detection** — Deno → stateless, Node.js → stateful (configurable). Same `MCPServer` class in all modes.
- **Server composition** — `server.proxy()` merges multiple upstream servers into one gateway. No equivalent in other libraries.
- **Split architecture** — `SessionStore` (metadata) + `StreamManager` (connections) with pluggable Redis backends for horizontal scaling.

### Migration from Official SDK

```typescript
// Before (@modelcontextprotocol/sdk)
const server = new MCPServer({ name: "my-server", version: "1.0.0" });
server.registerTool("greet", { name: "string" }, async ({ name }) => {
  return { content: [{ type: "text", text: `Hello!` }] };
});

// After (mcp-use)
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({ name: "my-server", version: "1.0.0" });
server.tool(
  {
    name: "greet",
    schema: z.object({ name: z.string().describe("Name to greet") }),
  },
  async ({ name }) => {
    return text(`Hello, ${name}!`);
  }
);
// Registration replay: tool registered once, auto-replayed per session
```

---

## See Also

Topics previously covered here have moved to dedicated guides:

- **Elicitation & Sampling** → `elicitation-and-sampling.md`
- **Notifications & Subscriptions** → `notifications-and-subscriptions.md`
- **Widgets, MCP Apps & React Hooks** → `widgets-and-ui.md`
- **Middleware & Server Configuration** → `server-configuration.md`

---

## Advanced Server Composition with `proxy()`

`proxy()` can aggregate local processes, remote HTTP servers, or pre-authenticated client sessions. It namespaces every tool/resource/prompt to prevent collisions.

### Parameter Table: `server.proxy()` (Config Form)

| Parameter | Type | Required | Description |
|---|---|---|---|
| `config` | `Record<string, ProxyTarget>` | Yes | Map of namespace → target config. |
| `config[ns].command` | `string` | No | Command to run local server. |
| `config[ns].args` | `string[]` | No | Args for local command. |
| `config[ns].url` | `string` | No | Remote MCP server URL. |
| `config[ns].env` | `Record<string, string>` | No | Environment vars for local process. |

### Aggregating Multiple Servers

```typescript
import { MCPServer, text, object } from 'mcp-use/server';
import path from 'node:path';

const server = new MCPServer({ name: 'gateway', version: '1.0.0' });

await server.proxy({
  billing: {
    command: 'tsx',
    args: [path.resolve(__dirname, './billing.ts')],
  },
  inventory: {
    url: 'https://inventory.example.com/mcp',
  },
});
// Results: billing_*, inventory_* (auto-namespaced from config keys)
```

---

## Session-Based Proxy (Custom Auth)

Use a pre-authenticated MCP client session when the upstream server requires per-user credentials.

```typescript
import { MCPServer } from 'mcp-use/server';
import { MCPClient } from 'mcp-use/client';

const server = new MCPServer({ name: 'gateway', version: '1.0.0' });

const client = new MCPClient({
  mcpServers: {
    secure: { url: 'https://secure.example.com/mcp', headers: { Authorization: 'Bearer token' } },
  },
});

const session = await client.createSession('secure');
await server.proxy(session, { namespace: 'secure' });
```

### Parameter Table: `server.proxy(session, options)`

| Parameter | Type | Required | Description |
|---|---|---|---|
| `session` | `MCPSession` | Yes | Pre-authenticated session. |
| `options.namespace` | `string` | Yes | Prefix for proxied tools/resources/prompts. |

---

## User Context with `ctx.client.user()`

`ctx.client.user()` exposes per-invocation caller metadata sent by supporting clients (e.g. ChatGPT). Use it to personalise outputs. It returns `undefined` for clients that do not send this metadata.

> **Security warning:** This data is client-reported and unverified. Do not use it for access control. For verified identity, use OAuth authentication and `ctx.auth`.

### Personalizing Tool Responses

```typescript
server.tool(
  { name: 'greet-user', description: 'Personalized greeting.' },
  async (_params, ctx) => {
    const caller = ctx.client.user();
    if (!caller) return text('Hello!');
    const city = caller.location?.city ?? 'there';
    const greeting = caller.locale?.startsWith('fr') ? 'Bonjour' : 'Hello';
    return text(`${greeting} from ${city}!`);
  }
);
```

### ❌ BAD: Assuming User Always Exists

```typescript
const caller = ctx.client.user();
return text(`Hello from ${caller.location.city}!`); // throws if caller is undefined
```

### ✅ GOOD: Graceful Fallback

```typescript
const caller = ctx.client.user();
return text(`Hello from ${caller?.location?.city ?? 'there'}!`);
```

---

## Client Capability Checks with `ctx.client.supportsApps()`

Use `supportsApps()` to verify the client can render MCP Apps (widgets) before returning `widget()` responses.

```typescript
server.tool(
  { name: 'show-dashboard', widget: { name: 'dashboard' } },
  async (_params, ctx) => {
    if (!ctx.client.supportsApps()) {
      return text('This client cannot render widgets.');
    }
    return widget({ props: { ready: true }, output: text('Dashboard loaded.') });
  }
);
```

---

## Autocomplete with `completable()`

`completable()` defines auto-complete suggestions for prompt arguments or resource template variables. Clients can surface these as typeahead results. It is used with `server.prompt()` and `server.resourceTemplate()`.

```typescript
import { completable } from 'mcp-use/server';
import { z } from 'zod';

server.prompt(
  {
    name: 'search-repo',
    description: 'Search a repository by name.',
    schema: z.object({
      repo: completable(z.string(), async (query) => {
        return ['mcp-use', 'mcp-use-examples', 'mcp-use-server'].filter((name) =>
          name.includes(query)
        );
      }),
    }),
  },
  async ({ repo }) => ({
    messages: [{ role: "system", content: `Searching ${repo}` }],
  })
);
```

### Parameter Table: `completable()`

| Parameter | Type | Required | Description |
|---|---|---|---|
| `schema` | `z.ZodTypeAny` | Yes | Base schema for the input. |
| `resolver` | `string[] \| (value: string, context?: { arguments?: Record<string, string> }) => Promise<string[]>` | Yes | Static list or async suggestion provider. |

---

## Hono Proxy Methods on `MCPServer`

`MCPServer` exposes Hono routing methods so you can build custom HTTP endpoints alongside the MCP transport.

### Parameter Table: Hono Methods

| Method | Purpose | Example |
|---|---|---|
| `server.get()` | Read-only endpoints | `/health`, `/public/*` |
| `server.post()` | Mutating endpoints | `/api/action` |
| `server.use()` | Middleware | Auth, CORS, logging |
| `server.route()` | Mount router | `/api` with nested routes |

### Middleware Example

```typescript
import { MCPServer } from 'mcp-use/server';
import { cors } from 'hono/cors';

const server = new MCPServer({ name: 'api-proxy', version: '1.0.0' });

server.use('/api/*', cors());
server.get('/api/health', (c) => c.json({ ok: true }));
```

### ❌ BAD: Leaving Routes Unprotected

```typescript
server.post('/api/admin/delete', async (c) => c.json({ ok: true }));
```

### ✅ GOOD: Add Auth Middleware

```typescript
server.use('/api/admin/*', async (c, next) => {
  if (!c.req.header('authorization')) return c.text('Unauthorized', 401);
  return next();
});
```

---

## Multi-Tenant Routing

Use `ctx.client.user()` to route requests per individual user. In ChatGPT's model, a single MCP session serves all users — use `subject` (not the session ID) to identify the caller.

```typescript
server.tool(
  { name: 'tenant-report', description: 'Fetch user-specific report.' },
  async (_params, ctx) => {
    const caller = ctx.client.user();
    const userId = caller?.subject ?? 'anonymous';
    return text(`Fetching report for user ${userId}`);
  }
);
```

### ❌ BAD: Using Session ID as User Identity

```typescript
const userId = ctx.session.sessionId; // shared across ALL ChatGPT users
```

### ✅ GOOD: Use subject per Invocation

```typescript
const userId = ctx.client.user()?.subject ?? 'anonymous';
```

---

## Autocomplete Performance Tips

| Tip | Why it Matters |
|---|---|
| Debounce queries | Avoid hammering upstream APIs |
| Cache recent suggestions | Improves latency for repeated inputs |
| Limit result size | Keeps UI responsive |

```typescript
const cached = new Map<string, string[]>();
const repoCompleter = completable(z.string(), async (query) => {
  if (cached.has(query)) return cached.get(query)!;
  const results = await fetchRepos(query);
  cached.set(query, results.slice(0, 8));
  return results.slice(0, 8);
});
```

---

## Capability Matrix

| Feature | API | Notes |
|---|---|---|
| User context | `ctx.client.user()` | Client-reported; undefined for non-supporting clients |
| Widgets support | `ctx.client.supportsApps()` | Gate `widget()` responses |
| Autocomplete | `completable()` | For prompts and resource templates |
| Proxy composition | `server.proxy()` | Namespaced tools/resources/prompts |

---

## Advanced Hono Router Mounts

Mount a full Hono router for non-MCP endpoints without breaking the MCP transport.

```typescript
import { Hono } from 'hono';

const router = new Hono();
router.get('/status', (c) => c.json({ ok: true }));

server.route('/api', router);
```

---

## Content Security Policy for Widgets

Widget CSP is declared in `WidgetMetadata` exported from your widget's `widget.tsx`. The `MCPServer` constructor accepts a `baseUrl` option (required in production) that is automatically included in widget CSP.

### Environment Variables

```bash
MCP_URL=https://myserver.com        # Base URL — auto-included in widget CSP
CSP_URLS=https://api.example.com,https://cdn.example.com  # Additional comma-separated domains
```

### Widget CSP Configuration

```typescript
import { WidgetMetadata } from "mcp-use";

export const widgetMetadata: WidgetMetadata = {
  description: "Display weather data",
  props: propSchema,
  metadata: {
    csp: {
      connectDomains: ["https://api.weather.com"],   // fetch, XHR, WebSocket
      resourceDomains: ["https://cdn.weather.com"],  // scripts, styles, images
      baseUriDomains: ["https://myserver.com"],       // base URI
      frameDomains: ["https://trusted-embed.com"],   // iframe embeds
      redirectDomains: ["https://oauth.provider.com"], // redirects (ChatGPT)
    },
  },
};
```

| Field | Purpose |
|---|---|
| `connectDomains` | Domains allowed for fetch, XHR, WebSocket |
| `resourceDomains` | Domains for scripts, styles, images |
| `baseUriDomains` | Domains for base URI |
| `frameDomains` | Domains for iframe embeds |
| `redirectDomains` | Domains for redirects (ChatGPT OAuth flows) |

### MCPServer with baseUrl

```typescript
const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  baseUrl: process.env.MCP_URL, // Required in production for correct CSP
});
```

The Inspector has two CSP modes: **Permissive** (relaxed, for debugging) and **Widget-Declared** (enforces declared CSP, production-like). Switch modes in the Inspector settings panel.

---

## Advanced Patterns Checklist

1. Namespace proxied servers for predictable tool names.
2. Guard widget responses with `supportsApps()`.
3. Prefer `completable()` for high-volume enum-like inputs on prompts.
4. Use `server.use()` for auth, CORS, and request IDs.
5. Use `ctx.client.user()?.subject` (not session ID) for per-user identity in multi-tenant deployments.
6. Set `baseUrl` in `MCPServer` constructor for correct widget CSP in production.
7. Use `MCP_URL` and `CSP_URLS` environment variables to control widget CSP domains.
