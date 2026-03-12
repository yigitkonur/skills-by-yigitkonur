# MCP Server Anti-Patterns

Avoid these mistakes when building MCP servers with the TypeScript SDK.

---

## 1. Tool Design Anti-Patterns

| Anti-pattern | Example | Why It's Bad | Fix |
|---|---|---|---|
| Generic tool names | `"run"`, `"process"`, `"execute"` | LLMs cannot distinguish tools by name alone | Use specific names: `"search-issues"`, `"create-user"` |
| Missing descriptions | `server.tool("fetch", schema, handler)` | LLM has no context for when to invoke | Always pass a description string as second arg |
| Missing `.describe()` | `z.string()` without annotation | LLM guesses parameter purpose, often wrong | Add `.describe("GitHub username, e.g. octocat")` |
| God tools | One tool handling CRUD + search + export | Token-heavy schema, ambiguous invocation | Split into focused single-responsibility tools |
| Raw API passthrough | Returning full third-party API response | Wastes tokens, leaks internal structure | Filter to only the fields the LLM needs |
| Too many parameters | Tool with 8+ params | LLMs produce hallucinated or missing args | Cap at 5-7; group related params into sub-objects |
| No input validation beyond schema | Trusting Zod parsing alone | Edge cases slip through (empty strings, negative IDs) | Add runtime guards inside the handler |
| Mutable global state | Shared variable across tool calls | Race conditions, unpredictable behavior | Pass state via closures or dependency injection |
| Synchronous blocking | `fs.readFileSync` in handler | Blocks the event loop, stalls all requests | Use `fs.promises.readFile` or `await` equivalents |
| Ignoring AbortSignal | Not checking `extra.signal` | Long tools cannot be cancelled by the client | Check `signal.aborted` and wire into fetch/child procs |

### Generic Tool Names

```typescript
// ❌ BAD — name tells the LLM nothing
server.tool("run", { query: z.string() }, async ({ query }) => {
  const results = await db.execute(query);
  return { content: [{ type: "text", text: JSON.stringify(results) }] };
});

// ✅ GOOD — name clearly communicates purpose
server.tool(
  "search-database-records",
  "Search the application database by a natural-language query.",
  { query: z.string().describe("SQL-safe search term, e.g. 'active users'") },
  async ({ query }) => {
    const results = await db.search(query);
    return { content: [{ type: "text", text: JSON.stringify(results) }] };
  }
);
```

### Missing `.describe()` on Schema Fields

```typescript
// ❌ BAD — LLM must guess what each field means
server.tool("create-issue", {
  title: z.string(),
  body: z.string(),
  labels: z.array(z.string()),
  assignee: z.string().optional(),
}, handler);

// ✅ GOOD — every field carries context for the LLM
server.tool("create-issue", "Create a GitHub issue in the configured repo.", {
  title: z.string().describe("Short issue title, max 100 chars"),
  body: z.string().describe("Markdown body with reproduction steps"),
  labels: z.array(z.string()).describe("Label names, e.g. ['bug','urgent']"),
  assignee: z.string().optional().describe("GitHub username to assign"),
}, handler);
```

### God Tools

```typescript
// ❌ BAD — one tool does everything
server.tool("manage-users", {
  action: z.enum(["create", "read", "update", "delete", "list", "search"]),
  id: z.string().optional(),
  data: z.any().optional(),
  query: z.string().optional(),
}, async ({ action, id, data, query }) => {
  switch (action) {
    case "create": return createUser(data);
    case "read": return getUser(id);
    // ... 50 more lines
  }
});

// ✅ GOOD — one tool per operation
server.tool("create-user", "Register a new user account.", {
  name: z.string().describe("Full display name"),
  email: z.string().email().describe("Valid email address"),
}, createUserHandler);

server.tool("get-user", "Retrieve user profile by ID.", {
  userId: z.string().uuid().describe("User UUID"),
}, getUserHandler);

server.tool("search-users", "Search users by name or email.", {
  query: z.string().describe("Partial name or email to match"),
  limit: z.number().int().min(1).max(50).default(10).describe("Max results"),
}, searchUsersHandler);
```

### Returning Raw API Responses

```typescript
// ❌ BAD — dumps the entire GitHub API response
server.tool("get-repo", { repo: z.string() }, async ({ repo }) => {
  const res = await fetch(`https://api.github.com/repos/${repo}`);
  const data = await res.json();
  return { content: [{ type: "text", text: JSON.stringify(data) }] };
});

// ✅ GOOD — extract only what the LLM needs
server.tool("get-repo", "Get key info about a GitHub repo.", {
  repo: z.string().describe("owner/repo format"),
}, async ({ repo }) => {
  const res = await fetch(`https://api.github.com/repos/${repo}`);
  const data = await res.json();
  const summary = {
    name: data.full_name,
    description: data.description,
    stars: data.stargazers_count,
    language: data.language,
    open_issues: data.open_issues_count,
    updated: data.updated_at,
  };
  return { content: [{ type: "text", text: JSON.stringify(summary, null, 2) }] };
});
```

### Synchronous Blocking and Ignoring AbortSignal

```typescript
// ❌ BAD — blocks event loop, ignores cancellation
server.tool("read-log", { path: z.string() }, async ({ path }) => {
  const content = fs.readFileSync(path, "utf-8"); // blocks
  return { content: [{ type: "text", text: content }] };
});

// ✅ GOOD — async I/O, respects cancellation
server.tool("read-log", "Read a log file from the allowed directory.", {
  path: z.string().describe("Relative path inside /var/log/app/"),
}, async ({ path }, extra) => {
  if (extra.signal?.aborted) throw new Error("Request cancelled");

  const safePath = resolve("/var/log/app", path);
  if (!safePath.startsWith("/var/log/app/")) {
    return { content: [{ type: "text", text: "Path outside allowed directory" }], isError: true };
  }

  const content = await fs.promises.readFile(safePath, "utf-8");
  return { content: [{ type: "text", text: content }] };
});
```

### Mutable Global State

```typescript
// ❌ BAD — shared mutable state across all requests
let requestCount = 0;
const cache: Record<string, unknown> = {};

server.tool("cached-fetch", { url: z.string() }, async ({ url }) => {
  requestCount++;
  if (cache[url]) return { content: [{ type: "text", text: JSON.stringify(cache[url]) }] };
  const data = await fetch(url).then(r => r.json());
  cache[url] = data; // unbounded growth, race conditions
  return { content: [{ type: "text", text: JSON.stringify(data) }] };
});

// ✅ GOOD — scoped cache with TTL, injected via closure
function createCachedFetchTool(server: McpServer, cacheMaxAge = 60_000) {
  const cache = new Map<string, { data: unknown; expires: number }>();

  server.tool("cached-fetch", "Fetch a URL with 60s caching.", {
    url: z.string().url().describe("URL to fetch"),
  }, async ({ url }) => {
    const now = Date.now();
    const entry = cache.get(url);
    if (entry && entry.expires > now) {
      return { content: [{ type: "text", text: JSON.stringify(entry.data) }] };
    }
    const data = await fetch(url).then(r => r.json());
    cache.set(url, { data, expires: now + cacheMaxAge });
    return { content: [{ type: "text", text: JSON.stringify(data) }] };
  });
}
```

---

## 2. Schema Anti-Patterns

### Using `z.any()` or `z.unknown()`

```typescript
// ❌ BAD — LLM has zero guidance on what to pass
server.tool("process", { data: z.any() }, handler);

// ✅ GOOD — explicit shape
server.tool("process", {
  data: z.object({
    name: z.string().describe("Record name"),
    value: z.number().describe("Numeric value to process"),
  }).strict().describe("The record to process"),
}, handler);
```

### Missing `.strict()` on Objects

```typescript
// ❌ BAD — silently accepts extra fields
server.tool("update-profile", {
  profile: z.object({ name: z.string(), age: z.number() }),
}, handler);

// ✅ GOOD — rejects unexpected fields
server.tool("update-profile", "Update user profile fields.", {
  profile: z.object({
    name: z.string().describe("Display name"),
    age: z.number().int().min(0).describe("Age in years"),
  }).strict().describe("Profile fields to update"),
}, handler);
```

### `.optional()` vs `.default()` Confusion

```typescript
// ❌ BAD — handler must null-check every optional field
server.tool("search", {
  query: z.string(),
  limit: z.number().optional(),   // could be undefined
  offset: z.number().optional(),  // could be undefined
}, async ({ query, limit, offset }) => {
  const l = limit ?? 10;  // defensive defaults scattered everywhere
  const o = offset ?? 0;
  return search(query, l, o);
});

// ✅ GOOD — defaults baked into the schema
server.tool("search", "Search records with pagination.", {
  query: z.string().describe("Search term"),
  limit: z.number().int().min(1).max(100).default(10).describe("Results per page"),
  offset: z.number().int().min(0).default(0).describe("Pagination offset"),
}, async ({ query, limit, offset }) => {
  return search(query, limit, offset); // always numbers, never undefined
});
```

### Overly Nested Schemas

```typescript
// ❌ BAD — LLMs struggle with deep nesting
server.tool("create-order", {
  order: z.object({
    customer: z.object({
      address: z.object({
        geo: z.object({
          lat: z.number(),
          lng: z.number(),
        }),
      }),
    }),
  }),
}, handler);

// ✅ GOOD — flatten to max 2 levels
server.tool("create-order", "Place a new order.", {
  customerName: z.string().describe("Customer full name"),
  streetAddress: z.string().describe("Delivery street address"),
  city: z.string().describe("Delivery city"),
  latitude: z.number().optional().describe("Delivery GPS latitude"),
  longitude: z.number().optional().describe("Delivery GPS longitude"),
}, handler);
```

---

## 3. Response Anti-Patterns

### Enormous Payloads

```typescript
// ❌ BAD — returns entire database table as JSON
server.tool("list-all-users", {}, async () => {
  const users = await db.query("SELECT * FROM users"); // could be 100k rows
  return { content: [{ type: "text", text: JSON.stringify(users) }] };
});

// ✅ GOOD — paginate and summarize
server.tool("list-users", "List users with pagination.", {
  page: z.number().int().min(1).default(1).describe("Page number"),
  pageSize: z.number().int().min(1).max(50).default(20).describe("Results per page"),
}, async ({ page, pageSize }) => {
  const offset = (page - 1) * pageSize;
  const users = await db.query("SELECT id, name, email FROM users LIMIT ? OFFSET ?", [pageSize, offset]);
  const total = await db.query("SELECT COUNT(*) as count FROM users");
  return {
    content: [{
      type: "text",
      text: JSON.stringify({ users, page, pageSize, total: total[0].count }),
    }],
  };
});
```

### Returning Errors as `text` Instead of `isError`

```typescript
// ❌ BAD — LLM cannot distinguish error from normal text
server.tool("get-user", { id: z.string() }, async ({ id }) => {
  const user = await db.findUser(id);
  if (!user) {
    return { content: [{ type: "text", text: "Error: user not found" }] };
  }
  return { content: [{ type: "text", text: JSON.stringify(user) }] };
});

// ✅ GOOD — use isError flag so clients handle it correctly
server.tool("get-user", "Retrieve a user by ID.", {
  id: z.string().uuid().describe("User UUID"),
}, async ({ id }) => {
  const user = await db.findUser(id);
  if (!user) {
    return {
      content: [{ type: "text", text: `User ${id} not found.` }],
      isError: true,
    };
  }
  return { content: [{ type: "text", text: JSON.stringify(user, null, 2) }] };
});
```

### Including Sensitive Data in Responses

```typescript
// ❌ BAD — leaks credentials to the LLM context
server.tool("get-config", {}, async () => {
  const config = {
    dbHost: process.env.DB_HOST,
    dbPassword: process.env.DB_PASSWORD, // leaked!
    apiKey: process.env.API_KEY,          // leaked!
  };
  return { content: [{ type: "text", text: JSON.stringify(config) }] };
});

// ✅ GOOD — redact sensitive values
server.tool("get-config", "Show non-sensitive server configuration.", {}, async () => {
  const config = {
    dbHost: process.env.DB_HOST,
    dbPasswordSet: !!process.env.DB_PASSWORD,
    apiKeySet: !!process.env.API_KEY,
  };
  return { content: [{ type: "text", text: JSON.stringify(config, null, 2) }] };
});
```

---

## 4. Architecture Anti-Patterns

### One Massive Server File

```typescript
// ❌ BAD — 800-line index.ts with everything inlined
// index.ts
const server = new McpServer({ name: "my-app", version: "1.0.0" });
server.tool("tool-1", ...); // 50 lines
server.tool("tool-2", ...); // 80 lines
// ... 15 more tools, helpers, DB setup, all in one file

// ✅ GOOD — modular structure
// src/index.ts
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { registerUserTools } from "./tools/users.js";
import { registerSearchTools } from "./tools/search.js";

const server = new McpServer({ name: "my-app", version: "1.0.0" });
registerUserTools(server);
registerSearchTools(server);

// src/tools/users.ts
export function registerUserTools(server: McpServer) {
  server.tool("create-user", ...);
  server.tool("get-user", ...);
}
```

### Import-Time Side Effects

```typescript
// ❌ BAD — connects to DB when file is imported
// db.ts
import { createPool } from "mysql2/promise";
export const pool = createPool({ host: "localhost", database: "app" }); // runs immediately

// ✅ GOOD — lazy initialization
// db.ts
import { createPool, Pool } from "mysql2/promise";
let pool: Pool | null = null;

export function getPool(): Pool {
  if (!pool) {
    pool = createPool({
      host: process.env.DB_HOST ?? "localhost",
      database: process.env.DB_NAME ?? "app",
    });
  }
  return pool;
}
```

### No Graceful Shutdown

```typescript
// ❌ BAD — server just crashes on SIGTERM, leaking connections
const server = new McpServer({ name: "my-app", version: "1.0.0" });
// ... register tools
const transport = new StdioServerTransport();
await server.connect(transport);

// ✅ GOOD — clean shutdown
const server = new McpServer({ name: "my-app", version: "1.0.0" });
const transport = new StdioServerTransport();
await server.connect(transport);

async function shutdown() {
  console.error("Shutting down gracefully...");
  await server.close();
  await pool?.end();
  process.exit(0);
}
process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
```

### Hardcoded Configuration

```typescript
// ❌ BAD — values baked in
const server = new McpServer({ name: "my-app", version: "1.0.0" });
const API_URL = "https://api.production.example.com";
const PORT = 3000;

// ✅ GOOD — environment-driven
const server = new McpServer({
  name: process.env.MCP_SERVER_NAME ?? "my-app",
  version: process.env.npm_package_version ?? "1.0.0",
});
const API_URL = process.env.API_URL ?? "http://localhost:8080";
const PORT = parseInt(process.env.PORT ?? "3000", 10);
```

---

## 5. Security Anti-Patterns

### Path Traversal

```typescript
// ❌ BAD — user controls the full path
server.tool("read-file", { path: z.string() }, async ({ path }) => {
  const content = await fs.promises.readFile(path, "utf-8"); // reads /etc/passwd
  return { content: [{ type: "text", text: content }] };
});

// ✅ GOOD — resolve and confine to allowed directory
import { resolve, normalize } from "path";

const ALLOWED_DIR = resolve(process.env.FILES_DIR ?? "./data");

server.tool("read-file", "Read a file from the data directory.", {
  path: z.string().describe("Relative path within the data directory"),
}, async ({ path: relPath }) => {
  const absolute = resolve(ALLOWED_DIR, normalize(relPath));
  if (!absolute.startsWith(ALLOWED_DIR + "/")) {
    return { content: [{ type: "text", text: "Access denied: path outside allowed directory" }], isError: true };
  }
  const content = await fs.promises.readFile(absolute, "utf-8");
  return { content: [{ type: "text", text: content }] };
});
```

### SQL Injection

```typescript
// ❌ BAD — string interpolation in SQL
server.tool("find-user", { name: z.string() }, async ({ name }) => {
  const rows = await db.query(`SELECT * FROM users WHERE name = '${name}'`);
  return { content: [{ type: "text", text: JSON.stringify(rows) }] };
});

// ✅ GOOD — parameterized queries
server.tool("find-user", "Find users by name.", {
  name: z.string().min(1).max(100).describe("Exact or partial user name"),
}, async ({ name }) => {
  const rows = await db.query("SELECT id, name, email FROM users WHERE name LIKE ?", [`%${name}%`]);
  return { content: [{ type: "text", text: JSON.stringify(rows, null, 2) }] };
});
```

### Executing User Input as Code

```typescript
// ❌ BAD — remote code execution
server.tool("evaluate", { expression: z.string() }, async ({ expression }) => {
  const result = eval(expression); // catastrophic
  return { content: [{ type: "text", text: String(result) }] };
});

// ✅ GOOD — use a safe math parser or refuse entirely
import { evaluate } from "mathjs";

server.tool("calculate", "Evaluate a safe math expression.", {
  expression: z.string().describe("Math expression, e.g. '2 + 3 * sin(pi/4)'"),
}, async ({ expression }) => {
  try {
    const result = evaluate(expression);
    return { content: [{ type: "text", text: `Result: ${result}` }] };
  } catch {
    return { content: [{ type: "text", text: "Invalid math expression" }], isError: true };
  }
});
```

### Logging Sensitive Data

```typescript
// ❌ BAD — tokens end up in log files
server.tool("auth-request", { token: z.string() }, async ({ token }) => {
  console.log(`Authenticating with token: ${token}`); // PII in logs
  const user = await verifyToken(token);
  return { content: [{ type: "text", text: JSON.stringify(user) }] };
});

// ✅ GOOD — redact sensitive values
server.tool("auth-request", "Verify an authentication token.", {
  token: z.string().describe("Bearer token"),
}, async ({ token }) => {
  console.error(`Authenticating token: ${token.slice(0, 4)}...redacted`);
  const user = await verifyToken(token);
  return { content: [{ type: "text", text: JSON.stringify({ id: user.id, name: user.name }) }] };
});
```

---

## 6. Testing Anti-Patterns

### No Testing at All

```typescript
// ❌ BAD — ship and pray
// "It works on my machine" → push to production

// ✅ GOOD — at minimum, test tool registration and basic responses
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";

const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
await server.connect(serverTransport);

const client = new Client({ name: "test", version: "1.0.0" });
await client.connect(clientTransport);

const tools = await client.listTools();
assert(tools.tools.length > 0, "Server should expose at least one tool");

const result = await client.callTool({ name: "get-user", arguments: { id: "test-uuid" } });
assert(!result.isError, "get-user should succeed for valid ID");
```

### Only Testing Happy Paths

```typescript
// ❌ BAD — only tests success case
const result = await client.callTool({ name: "get-user", arguments: { id: "valid-id" } });
assert(result.content[0].text.includes("name"));

// ✅ GOOD — also test error cases and edge cases
// Missing required param
await assert.rejects(
  () => client.callTool({ name: "get-user", arguments: {} }),
  /invalid/i
);

// Non-existent ID
const notFound = await client.callTool({ name: "get-user", arguments: { id: "nonexistent" } });
assert(notFound.isError === true, "Should return isError for missing user");

// Malformed input
const bad = await client.callTool({ name: "get-user", arguments: { id: "'; DROP TABLE users;--" } });
assert(bad.isError === true, "Should reject SQL injection attempts");
```

### Not Testing with MCP Inspector

```text
❌ BAD — never validate against a real MCP client

✅ GOOD — run MCP Inspector during development:
   npx @modelcontextprotocol/inspector node dist/index.js
   
   Then manually verify:
   - All tools appear in the tool list
   - Tool descriptions render clearly
   - Calling each tool returns expected shapes
   - Error responses show isError: true
```

---

## Quick Reference: Severity Guide

| Severity | Anti-patterns |
|---|---|
| 🔴 Critical | SQL injection, path traversal, eval(), logging secrets |
| 🟠 High | No `isError`, god tools, `z.any()`, no shutdown handler |
| 🟡 Medium | Missing `.describe()`, raw API passthrough, sync I/O |
| 🟢 Low | Single-file architecture, hardcoded config, no `.strict()` |
