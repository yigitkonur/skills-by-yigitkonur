# MCP Server Anti-Patterns

Avoid these mistakes when building MCP servers with **mcp-use**.

---

## 1. SDK & Framework Anti-Patterns

These are the most common mistakes — using lower-level APIs when mcp-use provides better abstractions.

### Using `@modelcontextprotocol/sdk` Directly

`mcp-use/server` wraps `@modelcontextprotocol/sdk` with Zod schema support, built-in HTTP transport, middleware, widgets, and more. Using the raw SDK directly means re-implementing all of that.

```typescript
// ❌ BAD — raw SDK, manual transport wiring, no Zod
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const server = new McpServer({ name: "my-server", version: "1.0.0" });
server.tool("greet", { name: { type: "string" } }, async ({ name }) => ({
  content: [{ type: "text", text: `Hello ${name}` }],
}));
const transport = new StdioServerTransport();
await server.connect(transport);

// ✅ GOOD — mcp-use handles transport, validation, HTTP
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({ name: "my-server", version: "1.0.0" });
server.tool(
  { name: "greet", schema: z.object({ name: z.string().describe("User name") }) },
  async ({ name }) => text(`Hello ${name}`)
);
await server.listen(3000);
```

### Building JSON Schema Manually Instead of Zod

mcp-use auto-converts Zod schemas to JSON Schema. Building JSON Schema by hand is error-prone and loses `.describe()` for LLM context.

```typescript
// ❌ BAD — manual JSON Schema, no runtime validation, no LLM hints
server.tool("search", {
  type: "object",
  properties: {
    query: { type: "string" },
    limit: { type: "number" },
  },
  required: ["query"],
}, handler);

// ✅ GOOD — Zod gives validation + description + type inference
server.tool(
  {
    name: "search",
    description: "Search records by keyword.",
    schema: z.object({
      query: z.string().describe("Search keyword"),
      limit: z.number().int().min(1).max(100).default(10).describe("Max results"),
    }),
  },
  async ({ query, limit }) => { /* limit is always a number */ }
);
```

### Creating Transport Manually Instead of `server.listen()`

`server.listen()` handles Streamable HTTP, SSE, session management, CORS, and inspector. Don't create transports yourself.

```typescript
// ❌ BAD — manual transport wiring
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
const transport = new StdioServerTransport();
await server.connect(transport);

// ✅ GOOD — listen() sets up everything
await server.listen(3000);
// Or for serverless: export default { fetch: server.getHandler() };
```

### Using Winston Instead of Built-in Logger

Winston was removed in mcp-use v1.12.0. The built-in `SimpleConsoleLogger` works in Node.js and browsers with zero dependencies.

```typescript
// ❌ BAD — external dependency, Node.js only (removed in v1.12.0)
import winston from "winston";
const logger = winston.createLogger({
  level: "info",
  transports: [new winston.transports.Console()],
});

// ✅ GOOD — built-in Logger, cross-environment
import { Logger } from "mcp-use/server";

Logger.configure({ level: "info", format: "minimal" });
const logger = Logger.get("my-component");
logger.info("Server started");
```

---

## 2. Tool Design Anti-Patterns

| Anti-pattern | Why It's Bad | Fix |
|---|---|---|
| Generic names (`"run"`, `"process"`) | LLMs can't distinguish tools | Use specific names: `"search-issues"` |
| Missing `description` | LLM has no context for invocation | Always include a `description` field |
| Missing `.describe()` on fields | LLM guesses parameter purpose | Add `.describe("GitHub username")` |
| God tools (CRUD + search in one) | Token-heavy, ambiguous invocation | Split into single-responsibility tools |
| Raw API passthrough | Wastes tokens, leaks internal structure | Filter to only needed fields |
| Too many parameters (8+) | LLMs hallucinate or miss args | Cap at 5-7 params |
| Synchronous blocking | Stalls event loop for all requests | Use `async`/`await` equivalents |

### God Tools

```typescript
// ❌ BAD — one tool does everything
server.tool({
  name: "manage-users",
  schema: z.object({
    action: z.enum(["create", "read", "update", "delete", "list"]),
    id: z.string().optional(),
    data: z.any().optional(),
  }),
}, handler);

// ✅ GOOD — one tool per operation
server.tool({
  name: "create-user",
  description: "Register a new user account.",
  schema: z.object({
    name: z.string().describe("Full display name"),
    email: z.string().email().describe("Valid email address"),
  }),
}, createUserHandler);

server.tool({
  name: "get-user",
  description: "Retrieve user profile by ID.",
  schema: z.object({ userId: z.string().uuid().describe("User UUID") }),
}, getUserHandler);
```

### Returning Raw API Responses

```typescript
// ❌ BAD — dumps entire GitHub API response (100+ fields)
server.tool({ name: "get-repo", schema: z.object({ repo: z.string() }) },
  async ({ repo }) => {
    const data = await fetch(`https://api.github.com/repos/${repo}`).then(r => r.json());
    return text(JSON.stringify(data));
  }
);

// ✅ GOOD — extract only what the LLM needs
server.tool({
  name: "get-repo",
  description: "Get key info about a GitHub repo.",
  schema: z.object({ repo: z.string().describe("owner/repo format") }),
}, async ({ repo }) => {
  const data = await fetch(`https://api.github.com/repos/${repo}`).then(r => r.json());
  return object({ name: data.full_name, stars: data.stargazers_count, language: data.language });
});
```

---

## 3. Schema Anti-Patterns

### Using `z.any()` or `z.unknown()`

```typescript
// ❌ BAD — LLM has zero guidance
server.tool({ name: "process", schema: z.object({ data: z.any() }) }, handler);

// ✅ GOOD — explicit shape with descriptions
server.tool({
  name: "process",
  schema: z.object({
    data: z.object({
      name: z.string().describe("Record name"),
      value: z.number().describe("Numeric value"),
    }).strict(),
  }),
}, handler);
```

### `.optional()` vs `.default()` Confusion

```typescript
// ❌ BAD — handler must null-check every optional
server.tool({
  name: "search",
  schema: z.object({
    query: z.string(),
    limit: z.number().optional(),   // could be undefined
  }),
}, async ({ query, limit }) => {
  const l = limit ?? 10;  // defensive defaults everywhere
  return search(query, l);
});

// ✅ GOOD — defaults in the schema
server.tool({
  name: "search",
  schema: z.object({
    query: z.string().describe("Search term"),
    limit: z.number().int().min(1).max(100).default(10).describe("Results per page"),
  }),
}, async ({ query, limit }) => search(query, limit)); // limit is always a number
```

### Overly Nested Schemas

```typescript
// ❌ BAD — LLMs struggle with deep nesting
z.object({ order: z.object({ customer: z.object({ address: z.object({ geo: z.object({ lat: z.number(), lng: z.number() }) }) }) }) })

// ✅ GOOD — flatten to max 2 levels
z.object({
  customerName: z.string().describe("Customer full name"),
  streetAddress: z.string().describe("Delivery street address"),
  latitude: z.number().optional().describe("GPS latitude"),
  longitude: z.number().optional().describe("GPS longitude"),
})
```

---

## 4. Response Anti-Patterns

### Returning Errors as `text()` Instead of `error()`

```typescript
// ❌ BAD — LLM cannot distinguish error from normal text
if (!user) return text("Error: user not found");

// ✅ GOOD — use error() so clients handle it correctly
if (!user) return error(`User ${id} not found.`);
```

### Enormous Payloads

```typescript
// ❌ BAD — returns entire table
const users = await db.query("SELECT * FROM users"); // 100k rows
return text(JSON.stringify(users));

// ✅ GOOD — paginate and select only needed columns
server.tool({
  name: "list-users",
  schema: z.object({
    page: z.number().int().min(1).default(1),
    pageSize: z.number().int().min(1).max(50).default(20),
  }),
}, async ({ page, pageSize }) => {
  const offset = (page - 1) * pageSize;
  const users = await db.query("SELECT id, name FROM users LIMIT $1 OFFSET $2", [pageSize, offset]);
  return object(users);
});
```

### Including Sensitive Data

```typescript
// ❌ BAD — leaks credentials to LLM context
return object({ dbPassword: process.env.DB_PASSWORD, apiKey: process.env.API_KEY });

// ✅ GOOD — redact sensitive values
return object({ dbPasswordSet: !!process.env.DB_PASSWORD, apiKeySet: !!process.env.API_KEY });
```

---

## 5. Security Anti-Patterns

### Missing `allowedOrigins` on HTTP Servers

Without `allowedOrigins`, any `Host` header value is accepted — making your server vulnerable to DNS rebinding attacks.

```typescript
// ❌ BAD — no host validation (default)
const server = new MCPServer({ name: "api", version: "1.0.0" });

// ✅ GOOD — explicit origin allowlist
const server = new MCPServer({
  name: "api",
  version: "1.0.0",
  allowedOrigins: [
    "https://myapp.com",
    "https://app.myapp.com",
  ],
});
```

### Not Checking Client Capabilities Before Elicitation/Sampling

Calling `ctx.elicit()` or `ctx.sample()` without verifying the client supports them causes runtime errors.

```typescript
// ❌ BAD — assumes client supports elicitation
server.tool({ name: "confirm", schema: z.object({}) }, async (_, ctx) => {
  const result = await ctx.elicit(
    "Do you want to continue?",
    z.object({ confirm: z.boolean().default(false) })
  ); // may throw if client doesn't support elicitation
  return text(result.data.confirm ? "Confirmed" : "Declined");
});

// ✅ GOOD — check capabilities first
server.tool({ name: "confirm", schema: z.object({}) }, async (_, ctx) => {
  if (!ctx.client.can('elicitation')) {
    return text("Client does not support interactive confirmation.");
  }
  const result = await ctx.elicit(
    "Do you want to continue?",
    z.object({ confirm: z.boolean().default(false) })
  );
  return text(result.action === "accept" && result.data.confirm ? "Confirmed" : "Declined");
});
```

### Path Traversal

```typescript
// ❌ BAD — user controls the full path
const content = await fs.promises.readFile(path, "utf-8"); // reads /etc/passwd

// ✅ GOOD — resolve and confine to allowed directory
import { resolve, normalize } from "path";
const ALLOWED_DIR = resolve("./data");

const absolute = resolve(ALLOWED_DIR, normalize(relPath));
if (!absolute.startsWith(ALLOWED_DIR + "/")) {
  return error("Access denied: path outside allowed directory");
}
```

### SQL Injection

```typescript
// ❌ BAD — string interpolation
const rows = await db.query(`SELECT * FROM users WHERE name = '${name}'`);

// ✅ GOOD — parameterized queries
const rows = await db.query("SELECT id, name FROM users WHERE name LIKE $1", [`%${name}%`]);
```

---

## 6. Architecture Anti-Patterns

### One Massive Server File

```typescript
// ❌ BAD — 800-line index.ts with everything
const server = new MCPServer({ name: "my-app", version: "1.0.0" });
server.tool({ name: "tool-1", /* ... */ }); // 50 lines
// ... 15 more tools, helpers, DB setup in one file

// ✅ GOOD — modular structure
import { registerUserTools } from "./tools/users.js";
import { registerSearchTools } from "./tools/search.js";
registerUserTools(server);
registerSearchTools(server);
```

### Import-Time Side Effects

```typescript
// ❌ BAD — connects to DB on import
export const pool = createPool({ host: "localhost" }); // runs immediately

// ✅ GOOD — lazy initialization
let pool: Pool | null = null;
export function getPool(): Pool {
  if (!pool) pool = createPool({ host: process.env.DB_HOST ?? "localhost" });
  return pool;
}
```

### No Graceful Shutdown

```typescript
// ❌ BAD — crashes on SIGTERM, leaks connections
server.listen();

// ✅ GOOD — clean shutdown
async function shutdown() {
  await pool?.end();
  process.exit(0);
}
process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
```

---

## 7. Testing Anti-Patterns

### No Testing at All

At minimum, verify with curl and MCP Inspector:

```bash
# List tools
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

# Call a tool
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get-user","arguments":{"id":"test"}}}'

# Run MCP Inspector
npx @modelcontextprotocol/inspector node dist/index.js
```

Test error cases too: missing params (validation error), non-existent IDs (isError), malformed input (rejection).

---

## Quick Reference: Severity Guide

| Severity | Anti-patterns |
|---|---|
| 🔴 Critical | SQL injection, path traversal, eval(), logging secrets, missing `allowedOrigins` |
| 🟠 High | Using raw SDK, `z.any()`, no `error()`, god tools, no shutdown, unchecked capabilities |
| 🟡 Medium | Manual JSON Schema, Winston logger, missing `.describe()`, raw API passthrough |
| 🟢 Low | Single-file architecture, hardcoded config, no `.strict()`, manual transport |

---

## 8. Widget Anti-Patterns

Common mistakes when building MCP Apps widgets.

### Not Handling `isPending`

```tsx
// ❌ BAD — accesses props before they exist, crashes on undefined
const Widget: React.FC = () => {
  const { props } = useWidget<{ items: Item[] }>();
  return <div>{props.items.map(/* ... */)}</div>; // TypeError: Cannot read property 'map' of undefined
};

// ✅ GOOD — always check isPending before accessing props
const Widget: React.FC = () => {
  const { props, isPending } = useWidget<{ items: Item[] }>();

  if (isPending) {
    return (
      <div className="animate-pulse p-4 space-y-2">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-12 bg-gray-200 dark:bg-gray-700 rounded" />
        ))}
      </div>
    );
  }

  return <div>{props.items?.map(/* ... */)}</div>;
};
```

### Hardcoded Theme Colors

```tsx
// ❌ BAD — always white background, invisible in dark mode
const Widget: React.FC = () => {
  return (
    <div style={{ backgroundColor: "#ffffff", color: "#333333" }}>
      <p>This is invisible in dark mode!</p>
    </div>
  );
};

// ✅ GOOD — use theme from useWidget()
const Widget: React.FC = () => {
  const { theme } = useWidget();
  return (
    <div className={theme === "dark" ? "bg-gray-900 text-white" : "bg-white text-gray-900"}>
      <p>Readable in both modes!</p>
    </div>
  );
};

// ✅ ALSO GOOD — use Tailwind dark: variant (ThemeProvider sets the class)
const Widget: React.FC = () => (
  <div className="bg-white dark:bg-gray-900 text-gray-900 dark:text-white">
    <p>Readable in both modes!</p>
  </div>
);
```

### Using `fetch()` Instead of `useCallTool`

```tsx
// ❌ BAD — bypasses MCP protocol, no auth, breaks in sandboxed widgets
const Widget: React.FC = () => {
  const handleClick = async () => {
    const res = await fetch("http://localhost:3000/api/search", {
      method: "POST",
      body: JSON.stringify({ query: "test" }),
    });
    const data = await res.json();
  };
  return <button onClick={handleClick}>Search</button>;
};

// ✅ GOOD — uses MCP protocol, works in all hosts, handles auth automatically
import { useCallTool } from "mcp-use/react";

const Widget: React.FC = () => {
  const { callTool, data, isPending } = useCallTool("search");

  return (
    <button onClick={() => callTool({ query: "test" })} disabled={isPending}>
      {isPending ? "Searching..." : "Search"}
    </button>
  );
};
```

### Missing CSP Domains

```tsx
// ❌ BAD — widget tries to fetch from external API but CSP blocks it
export const widgetMetadata: WidgetMetadata = {
  description: "Weather widget",
  props: z.object({ city: z.string() }),
  // No CSP domains declared!
};

// Widget at runtime:
const { callTool } = useWidget();
// This fetch FAILS with CSP error because the domain isn't whitelisted
await fetch("https://api.weather.com/v2/current?city=Paris");

// ✅ GOOD — declare all external domains in metadata
export const widgetMetadata: WidgetMetadata = {
  description: "Weather widget",
  props: z.object({ city: z.string() }),
  metadata: {
    csp: {
      connectDomains: ["https://api.weather.com"],
      resourceDomains: ["https://cdn.weather-icons.com"],
    },
  },
};
```

### Not Wrapping in `McpUseProvider`

```tsx
// ❌ BAD — missing provider, useWidget() will not have theme, error boundary, or auto-sizing
export default function Widget() {
  return <MyWidgetContent />; // No McpUseProvider wrapper!
}

// ✅ GOOD — always wrap in McpUseProvider
import { McpUseProvider } from "mcp-use/react";

export default function Widget() {
  return (
    <McpUseProvider autoSize>
      <MyWidgetContent />
    </McpUseProvider>
  );
}
```

> **Breaking change (v1.20.1):** `McpUseProvider` no longer wraps `BrowserRouter`. If your widget uses React Router, add `BrowserRouter` manually:
>
> ```tsx
> import { BrowserRouter } from "react-router-dom";
> import { McpUseProvider } from "mcp-use/react";
>
> export default function Widget() {
>   return (
>     <McpUseProvider autoSize>
>       <BrowserRouter>
>         <MyRoutedWidget />
>       </BrowserRouter>
>     </McpUseProvider>
>   );
> }
> ```
```

### Directly Accessing `window.openai`

```tsx
// ❌ BAD — only works in ChatGPT, crashes in Claude and other MCP clients
const Widget: React.FC = () => {
  const handleClick = () => {
    window.openai.callTool("search", { query: "test" }); // ← undefined in non-ChatGPT clients
  };
  return <button onClick={handleClick}>Search</button>;
};

// ✅ GOOD — useWidget/useCallTool works in ALL host environments
import { useCallTool } from "mcp-use/react";

const Widget: React.FC = () => {
  const { callTool } = useCallTool("search");
  return <button onClick={() => callTool({ query: "test" })}>Search</button>;
};
```

### Missing Widget Metadata Export

```tsx
// ❌ BAD — no widgetMetadata export, host cannot determine CSP or description
export default function Widget() {
  return <div>My widget</div>;
}

// ✅ GOOD — always export widgetMetadata alongside default component
import { type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

export const widgetMetadata: WidgetMetadata = {
  description: "Describes what this widget does for the LLM",
  props: z.object({ data: z.string() }),
  metadata: { prefersBorder: true },
};

export default function Widget() {
  return <div>My widget</div>;
}
```

### Ignoring Streaming State

```tsx
// ❌ BAD — shows nothing during streaming, then suddenly appears
const Widget: React.FC = () => {
  const { props, isPending } = useWidget<{ code: string }>();
  if (isPending) return <div>Loading...</div>;
  return <pre>{props.code}</pre>;
};

// ✅ GOOD — show progressive content during streaming
const Widget: React.FC = () => {
  const { props, isPending, isStreaming, partialToolInput } = useWidget<{ code: string }>();

  if (isPending && !partialToolInput) return <div className="animate-pulse">Loading...</div>;

  const displayCode = isStreaming ? (partialToolInput?.code ?? "") : (props.code ?? "");
  return (
    <pre>
      {displayCode}
      {isStreaming && <span className="animate-pulse text-blue-400">▌</span>}
    </pre>
  );
};
```

### Widget Anti-Pattern Severity

| Severity | Anti-pattern |
|----------|-------------|
| 🔴 Critical | Directly accessing `window.openai`, using `fetch()` instead of `useCallTool` |
| 🟠 High | Not handling `isPending`, missing CSP domains, not wrapping in `McpUseProvider` |
| 🟡 Medium | Hardcoded theme colors, missing `widgetMetadata` export, ignoring streaming state |
| 🟢 Low | Not using `autoSize`, missing loading skeletons |
