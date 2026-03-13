# Advanced Features

Server composition, autocomplete, client introspection, and how mcp-use compares to alternative MCP implementations.

---

## 1. Server Composition / Proxy

`server.proxy()` combines multiple upstream MCP servers into a single aggregator endpoint. Tools, resources, and prompts from each child server are namespaced to avoid collisions.

### Config-Based Proxy (Recommended)

```typescript
import { MCPServer } from "mcp-use/server";
import path from "node:path";

const server = new MCPServer({ name: "Gateway", version: "1.0.0" });

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

const server = new MCPServer({ name: "Gateway", version: "1.0.0" });

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

For context-aware suggestions, pass an async function:

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
| `locale` | `string` | BCP-47 locale, e.g. `"it-IT"` |
| `location` | `object` | `{ city, region, country, timezone, latitude, longitude }` |
| `userAgent` | `string` | Browser / host user-agent string |
| `timezoneOffsetMinutes` | `number` | UTC offset in minutes |

**ChatGPT multi-tenant model:** ChatGPT shares a single MCP session across all users. Use `ctx.client.user()?.subject` to identify individual users and `conversationId` for chat threads.

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
| `capabilities()` | `Record<string, any>` | Full raw capabilities object |

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
const server = new McpServer({ name: "my-server", version: "1.0.0" });
server.registerTool("greet", { name: "string" }, async ({ name }) => {
  return { content: [{ type: "text", text: `Hello!` }] };
});

// After (mcp-use)
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({ name: "my-server", version: "1.0.0" });
server.tool("greet", { name: z.string() }, async ({ name }) => {
  return text(`Hello, ${name}!`);
});
// Registration replay: tool registered once, auto-replayed per session
```

---

## See Also

Topics previously covered here have moved to dedicated guides:

- **Elicitation & Sampling** → `elicitation-and-sampling.md`
- **Notifications & Subscriptions** → `notifications-and-subscriptions.md`
- **Widgets, MCP Apps & React Hooks** → `widgets-and-ui.md`
- **Middleware & Server Configuration** → `server-configuration.md`
