# MCP Server Recipes

Complete, copy-pasteable server examples using the mcp-use TypeScript server library. All examples use `mcp-use/server` imports and Zod for schema validation.

## Recipe 1: File System Server

```typescript
import { MCPServer, text, object, error } from "mcp-use/server";
import { z } from "zod";
import fs from "fs/promises";
import path from "path";

const server = new MCPServer({ name: "filesystem-server", version: "1.0.0", description: "Read and search files in a directory" });
const ALLOWED_DIR = process.env.FS_ROOT || process.cwd();

server.tool(
  { name: "read-file", description: "Read contents of a file",
    schema: z.object({ path: z.string().describe("Relative path to file") }) },
  async ({ path: filePath }) => {
    const fullPath = path.resolve(ALLOWED_DIR, filePath);
    if (!fullPath.startsWith(ALLOWED_DIR)) return error("Access denied: path outside allowed directory");
    try { return text(await fs.readFile(fullPath, "utf-8")); }
    catch (e) { return error(`Failed to read file: ${(e as Error).message}`); }
  }
);

server.tool(
  { name: "list-files", description: "List files in a directory",
    schema: z.object({ directory: z.string().default(".").describe("Relative directory path"),
      pattern: z.string().optional().describe("Filter by extension, e.g. '.ts'") }) },
  async ({ directory, pattern }) => {
    const fullPath = path.resolve(ALLOWED_DIR, directory);
    if (!fullPath.startsWith(ALLOWED_DIR)) return error("Access denied: path outside allowed directory");
    const entries = await fs.readdir(fullPath, { withFileTypes: true });
    const items = entries.filter(e => !pattern || e.name.endsWith(pattern))
      .map(e => ({ name: e.name, type: e.isDirectory() ? "dir" : "file" }));
    return object({ directory, items, count: items.length });
  }
);

server.resourceTemplate(
  { name: "file", uriTemplate: "file://{path}", title: "File Contents", description: "Read any file by path" },
  async (uri, { path: filePath }) => {
    const fullPath = path.resolve(ALLOWED_DIR, filePath);
    return text(await fs.readFile(fullPath, "utf-8"));
  }
);

await server.listen();
```

## Recipe 2: Database Server (with Connection Pooling)

```typescript
import { MCPServer, text, object, error } from "mcp-use/server";
import { z } from "zod";
import Database from "better-sqlite3";

const server = new MCPServer({ name: "database-server", version: "1.0.0", description: "Query and explore a SQLite database" });
const db = new Database(process.env.DB_PATH || "./data.db");
db.pragma("journal_mode = WAL"); db.pragma("busy_timeout = 5000");

server.tool(
  { name: "query", description: "Run a read-only SQL query",
    schema: z.object({ sql: z.string().describe("SQL SELECT query"),
      params: z.array(z.union([z.string(), z.number(), z.boolean(), z.null()])).optional().describe("Bind parameters"),
      limit: z.number().default(100).describe("Max rows") }) },
  async ({ sql, params, limit }) => {
    if (!/^\s*SELECT/i.test(sql)) return error("Only SELECT queries allowed");
    try { const rows = db.prepare(sql.includes("LIMIT") ? sql : `${sql} LIMIT ${limit}`).all(...(params || []));
      return object({ rows, count: rows.length, truncated: rows.length >= limit });
    } catch (e) { return error(`Query failed: ${(e as Error).message}`); }
  }
);
server.tool(
  { name: "list-tables", description: "List all tables in the database", schema: z.object({}) },
  async () => {
    const tables = db.prepare(`SELECT name, type FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%' ORDER BY name`).all();
    return object({ tables, count: tables.length });
  }
);
server.tool(
  { name: "describe-table", description: "Show columns and row count for a table",
    schema: z.object({ table: z.string().describe("Table name") }) },
  async ({ table }) => {
    const safe = table.replace(/[^a-zA-Z0-9_]/g, "");
    try { const columns = db.prepare(`PRAGMA table_info('${safe}')`).all();
      const { count } = db.prepare(`SELECT COUNT(*) as count FROM "${safe}"`).get() as { count: number };
      return object({ table: safe, columns, rowCount: count });
    } catch { return error(`Table not found: ${safe}`); }
  }
);
server.resource(
  { name: "schema", uri: "db://schema", title: "Full Schema", description: "Database schema as SQL" },
  async () => {
    const rows = db.prepare(`SELECT sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%'`).all() as { sql: string }[];
    return text(rows.map(r => r.sql + ";").join("\n\n"));
  }
);
process.on("SIGINT", () => { db.close(); process.exit(0); });
await server.listen();
```

## Recipe 3: API Wrapper Server (with Caching)

```typescript
import { MCPServer, object, error } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "github-api-server", version: "1.0.0",
  description: "Query GitHub repos and issues with caching",
});

const GITHUB_TOKEN = process.env.GITHUB_TOKEN || "";
const cache = new Map<string, { data: unknown; expires: number }>();
const CACHE_TTL = 300_000;
let lastReq = 0;

async function ghFetch(endpoint: string): Promise<unknown> {
  const c = cache.get(endpoint);
  if (c && Date.now() < c.expires) return c.data;
  const wait = 2000 - (Date.now() - lastReq);
  if (wait > 0) await new Promise(r => setTimeout(r, wait));
  lastReq = Date.now();
  const res = await fetch(`https://api.github.com${endpoint}`, {
    headers: { Accept: "application/vnd.github.v3+json",
      ...(GITHUB_TOKEN ? { Authorization: `Bearer ${GITHUB_TOKEN}` } : {}) },
  });
  if (!res.ok) throw new Error(`GitHub API ${res.status}: ${res.statusText}`);
  const data = await res.json();
  cache.set(endpoint, { data, expires: Date.now() + CACHE_TTL });
  return data;
}

server.tool(
  {
    name: "get-repo",
    description: "Get repository details",
    schema: z.object({ owner: z.string(), repo: z.string() }),
  },
  async ({ owner, repo }) => {
    try {
      const d = (await ghFetch(`/repos/${owner}/${repo}`)) as Record<string, unknown>;
      return object({ name: d.full_name, description: d.description, stars: d.stargazers_count, language: d.language });
    } catch (e) { return error((e as Error).message); }
  }
);

server.tool(
  {
    name: "list-issues",
    description: "List repository issues",
    schema: z.object({
      owner: z.string(), repo: z.string(),
      state: z.enum(["open", "closed", "all"]).default("open"),
      per_page: z.number().default(10).describe("Max 30"),
    }),
  },
  async ({ owner, repo, state, per_page }) => {
    try {
      const p = new URLSearchParams({ state, per_page: String(Math.min(per_page, 30)) });
      const data = (await ghFetch(`/repos/${owner}/${repo}/issues?${p}`)) as any[];
      return object({ issues: data.map(i => ({ number: i.number, title: i.title, state: i.state })), count: data.length });
    } catch (e) { return error((e as Error).message); }
  }
);

server.tool(
  {
    name: "search-repos",
    description: "Search GitHub repositories",
    schema: z.object({ query: z.string(), sort: z.enum(["stars", "forks", "updated"]).default("stars"), limit: z.number().default(10) }),
  },
  async ({ query, sort, limit }) => {
    try {
      const p = new URLSearchParams({ q: query, sort, per_page: String(Math.min(limit, 30)) });
      const d = (await ghFetch(`/search/repositories?${p}`)) as any;
      return object({ total: d.total_count, repos: d.items.map((r: any) => ({ name: r.full_name, stars: r.stargazers_count, language: r.language })) });
    } catch (e) { return error((e as Error).message); }
  }
);

await server.listen();
```

## Recipe 4: Multi-Tool Server (with Notifications and Progress)

```typescript
import { MCPServer, object, markdown, error } from "mcp-use/server";
import { z } from "zod";
const server = new MCPServer({ name: "task-manager-server", version: "1.0.0" });
interface Task { id: string; title: string; status: "todo" | "in-progress" | "done"; priority: "low" | "medium" | "high"; tags: string[]; createdAt: string; }
const tasks = new Map<string, Task>();

server.tool(
  { name: "create-task", description: "Create a new task",
    schema: z.object({ title: z.string(), priority: z.enum(["low", "medium", "high"]).default("medium"), tags: z.array(z.string()).default([]) }) },
  async ({ title, priority, tags }, ctx) => {
    const id = `task-${Date.now().toString(36)}`;
    const task: Task = { id, title, status: "todo", priority, tags, createdAt: new Date().toISOString() };
    tasks.set(id, task);
    await ctx.sendNotification("custom/task-created", { taskId: id, title, createdAt: task.createdAt });
    return object({ task });
  }
);
server.tool(
  { name: "update-task", description: "Update task status or details",
    schema: z.object({ id: z.string(), status: z.enum(["todo", "in-progress", "done"]).optional(), title: z.string().optional(), priority: z.enum(["low", "medium", "high"]).optional() }) },
  async ({ id, status, title, priority }, ctx) => {
    const task = tasks.get(id);
    if (!task) return error(`Task not found: ${id}`);
    if (status) task.status = status;
    if (title) task.title = title;
    if (priority) task.priority = priority;
    await ctx.sendNotification("custom/task-updated", { taskId: id, title: task.title, status: task.status });
    return object({ task });
  }
);
server.tool(
  { name: "list-tasks", description: "List and filter tasks",
    schema: z.object({ status: z.enum(["todo", "in-progress", "done", "all"]).default("all"), tag: z.string().optional() }) },
  async ({ status, tag }) => {
    let filtered = Array.from(tasks.values());
    if (status !== "all") filtered = filtered.filter(t => t.status === status);
    if (tag) filtered = filtered.filter(t => t.tags.includes(tag));
    return object({ tasks: filtered, count: filtered.length });
  }
);
server.tool(
  { name: "bulk-import", description: "Import multiple tasks with progress reporting",
    schema: z.object({ tasks: z.array(z.object({ title: z.string(), priority: z.enum(["low", "medium", "high"]).default("medium"), tags: z.array(z.string()).default([]) })) }) },
  async ({ tasks: list }, ctx) => {
    const created: Task[] = [];
    for (let i = 0; i < list.length; i++) {
      const { title, priority, tags } = list[i];
      const task: Task = { id: `task-${Date.now().toString(36)}-${i}`, title, status: "todo", priority, tags, createdAt: new Date().toISOString() };
      tasks.set(task.id, task);
      created.push(task);
      await ctx.reportProgress?.(i + 1, list.length, `Imported ${i + 1}/${list.length}`);
    }
    return object({ imported: created.length, tasks: created });
  }
);
server.tool(
  { name: "task-summary", description: "Markdown summary of all tasks", schema: z.object({}) },
  async () => {
    const all = Array.from(tasks.values());
    const byStatus = (s: string) => all.filter(t => t.status === s);
    const lines = [`# Task Summary`, `**Total:** ${all.length} | **Todo:** ${byStatus("todo").length} | **In Progress:** ${byStatus("in-progress").length} | **Done:** ${byStatus("done").length}`];
    for (const s of ["todo", "in-progress", "done"]) {
      const items = byStatus(s);
      if (items.length) { lines.push(`## ${s}`); items.forEach(t => lines.push(`- **[${t.priority.toUpperCase()}]** ${t.title} _(${t.id})_`)); }
    }
    return markdown(lines.join("\n"));
  }
);
await server.listen();
```

## Recipe 5: Proxy/Aggregator Server

```typescript
import { MCPServer, object } from "mcp-use/server";
const gateway = new MCPServer({ name: "api-gateway", version: "1.0.0" });
await gateway.proxy({
  github: { command: "npx", args: ["-y", "@modelcontextprotocol/server-github"] },
  filesystem: { command: "npx", args: ["-y", "@modelcontextprotocol/server-filesystem", "./data"] },
  db: { url: "https://db-mcp.internal:3001/mcp" },
});
gateway.tool(
  { name: "health", description: "Check all upstream server health" },
  async () => object({ servers: ["github", "filesystem", "db"], status: "healthy" })
);
await gateway.listen(3000);
```

## Recipe 6: Weather Service Server (Resources, Prompts, Widgets)

```typescript
import { MCPServer, text, object, error } from "mcp-use/server";
import { z } from "zod";
const server = new MCPServer({ name: "weather-server", version: "1.0.0" });
const cache = new Map<string, { data: any; expires: number }>();
async function getWeather(city: string) {
  const c = cache.get(city);
  if (c && Date.now() < c.expires) return c.data;
  const res = await fetch(`https://api.weather.example.com/current?city=${encodeURIComponent(city)}`);
  if (!res.ok) throw new Error(`Weather API ${res.status}`);
  const data = await res.json();
  cache.set(city, { data, expires: Date.now() + 600_000 });
  return data;
}
server.tool(
  { name: "get-weather", description: "Get current weather",
    schema: z.object({ city: z.string(), units: z.string().optional().default("fahrenheit") }) },
  async ({ city }) => { try { return object(await getWeather(city)); } catch (e) { return error((e as Error).message); } }
);
server.resource({ name: "monitored-cities", uri: "weather://monitored", title: "Monitored Cities",
  annotations: { audience: ["user", "assistant"], priority: 0.8 } },
  async () => object({ cities: ["New York", "London", "Tokyo"] }));
server.resourceTemplate({ name: "city-weather", uriTemplate: "weather://city/{cityName}", title: "City Weather", description: "Weather data for a specific city" },
  async (uri, { cityName }) => object(await getWeather(cityName as string)));
server.prompt({ name: "weather-report", description: "Generate a weather report",
  schema: z.object({ city: z.string().describe("City name") }) },
  async ({ city }) => ({ messages: [{ role: "user" as const, content: `Weather report for ${city} using current data.` }] }));
// Register an MCP Apps widget (must have a matching widget.tsx in resources/)
// server.uiResource({ name: "weather-dashboard", title: "Weather Dashboard", type: "mcpApps" });
server.get("/api/weather/:city", async (c) => c.json(await getWeather(c.req.param("city"))));
await server.listen();
```

## Recipe 7: Database Management Server (PostgreSQL)

```typescript
import { MCPServer, text, object, error } from "mcp-use/server";
import { z } from "zod";
import pg from "pg";
const pool = new pg.Pool({ connectionString: process.env.DATABASE_URL });
const server = new MCPServer({ name: "db-manager", version: "1.0.0" });
server.tool(
  { name: "execute_query", description: "Run a read-only SQL query (SELECT only)",
    schema: z.object({ sql: z.string().describe("SQL SELECT query"), params: z.array(z.string()).optional() }) },
  async ({ sql, params }) => {
    if (!/^\s*SELECT/i.test(sql)) return error("Only SELECT queries are allowed");
    try { const { rows } = await pool.query(sql.includes("LIMIT") ? sql : `${sql} LIMIT 100`, params); return object({ rows, count: rows.length }); }
    catch (e) { return error(`Query failed: ${(e as Error).message}`); }
  }
);
server.tool(
  { name: "get_schema", description: "Get column info for a table",
    schema: z.object({ table: z.string(), schema: z.string().default("public") }) },
  async ({ table, schema: s }) => {
    const { rows } = await pool.query(`SELECT column_name, data_type, is_nullable, column_default FROM information_schema.columns WHERE table_schema = $1 AND table_name = $2 ORDER BY ordinal_position`, [s, table]);
    return object({ table, schema: s, columns: rows });
  }
);
server.resource({ name: "db-statistics", uri: "db://statistics", title: "Database Statistics" },
  async () => { const { rows } = await pool.query(`SELECT relname AS table, n_live_tup AS rows FROM pg_stat_user_tables ORDER BY n_live_tup DESC LIMIT 20`); return object({ tables: rows }); });
server.prompt({ name: "generate_query", description: "Generate SQL from natural language",
  schema: z.object({ description: z.string().describe("What data you want") }) },
  async ({ description }) => ({ messages: [{ role: "user" as const, content: `Generate a PostgreSQL SELECT query for: ${description}. Use get_schema tool first.` }] }));
process.on("SIGINT", async () => { await pool.end(); process.exit(0); });
await server.listen();
```

## Recipe 8: File System Manager (Path Validation, Binary Support)

```typescript
import { MCPServer, text, object, error, binary } from "mcp-use/server";
import { z } from "zod";
import fs from "fs/promises";
import path from "path";
import { lookup } from "mime-types";
const BASE = path.resolve(process.env.FS_ROOT || "./files"), MAX = 10 * 1024 * 1024;
const server = new MCPServer({ name: "fs-manager", version: "1.0.0" });
function safe(p: string) { const r = path.resolve(BASE, p); if (!r.startsWith(BASE)) throw new Error("Path traversal denied"); return r; }
server.tool(
  { name: "list_directory", description: "List directory contents",
    schema: z.object({ path: z.string().default("."), showHidden: z.boolean().default(false) }) },
  async ({ path: p, showHidden }) => {
    try { const entries = await fs.readdir(safe(p), { withFileTypes: true });
      return object({ items: entries.filter(e => showHidden || !e.name.startsWith(".")).map(e => ({ name: e.name, type: e.isDirectory() ? "dir" : "file" })) });
    } catch (e) { return error((e as Error).message); }
  }
);
server.tool(
  { name: "read_file", description: "Read a file's contents",
    schema: z.object({ path: z.string(), encoding: z.string().default("utf-8") }) },
  async ({ path: p, encoding }) => {
    try { const fp = safe(p), stat = await fs.stat(fp);
      if (stat.size > MAX) return error("File exceeds 10MB limit");
      return text(await fs.readFile(fp, encoding as BufferEncoding));
    } catch (e) { return error((e as Error).message); }
  }
);
server.resourceTemplate({ name: "file-resource", uriTemplate: "file://{path}", title: "File Contents", description: "Access file contents" },
  async (uri, { path: p }) => {
    const fp = safe(p as string), mime = lookup(fp) || "application/octet-stream";
    if (mime.startsWith("text/") || mime === "application/json") return text(await fs.readFile(fp, "utf-8"));
    return binary((await fs.readFile(fp)).toString("base64"), mime);
  });
await server.listen();
```

## Key Patterns

**Error handling** — return `error()` instead of throwing:
```typescript
return error(`File not found: ${filePath}`);  // structured error to client
```

**Schema descriptions** — always use `.describe()` for tool parameter help:
```typescript
schema: z.object({ query: z.string().min(1).describe("Search query"), limit: z.number().default(10).describe("Max results (1-100)") })
```

**Response helpers** — `text()` for raw content, `object()` for structured data, `markdown()` for rich output, `error()` for failures, `binary()` for non-text files.

**DNS Rebinding Protection** — restrict allowed origins via `allowedOrigins` config. Spoofed `Host` → 403. Test: `curl -H "Host: evil.com" http://localhost:3000/mcp`. See `examples/server/features/dns-rebinding`.

**Streaming Tool Props** — `useWidget` hook exposes `partialToolInput` and `isStreaming` for live previews as the LLM streams tool arguments. See `examples/server/features/streaming-props`.

---

## Recipe 9: Webhook Handler Server

Receive external webhooks (e.g., from Stripe or GitHub) and forward them to connected MCP clients via SSE notifications.

```typescript
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "webhook-server",
  version: "1.0.0",
});

// 1. Define a tool to inspect received webhooks
const recentWebhooks: any[] = [];

server.tool(
  { name: "list-webhooks", schema: z.object({ limit: z.number().default(10) }) },
  async ({ limit }) => {
    return text(JSON.stringify(recentWebhooks.slice(0, limit), null, 2));
  }
);

// 2. Add a custom Hono route to receive POST requests
server.post("/webhooks/:source", async (c) => {
  const source = c.req.param("source");
  const payload = await c.req.json();
  
  const event = {
    id: crypto.randomUUID(),
    source,
    timestamp: new Date().toISOString(),
    payload
  };
  
  // Store for tool access
  recentWebhooks.unshift(event);
  if (recentWebhooks.length > 50) recentWebhooks.pop();
  
  // 3. Notify all connected MCP clients via custom namespaced notification
  server.sendNotification("webhook/received", {
    message: `New webhook from ${source}`,
    data: event
  });
  
  return c.json({ status: "received", id: event.id });
});

await server.listen(3000);
```

**Testing:**
```bash
curl -X POST http://localhost:3000/webhooks/stripe -d '{"event": "charge.succeeded"}'
```
Connected MCP clients will receive the notification immediately.

---

## Recipe 10: Sampling Server (LLM-in-the-Loop)

Use `ctx.sample()` to ask the *client's* LLM to generate content. This allows the server to leverage the client's intelligence (e.g., summarizing data).

```typescript
import { MCPServer, text, error } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({ name: "sampling-server", version: "1.0.0" });

server.tool(
  {
    name: "summarize-file",
    description: "Read a file and ask the LLM to summarize it",
    schema: z.object({
      content: z.string().describe("Text content to summarize"),
      style: z.enum(["brief", "detailed"]).default("brief"),
    }),
  },
  async ({ content, style }, ctx) => {
    // 1. Check if client supports sampling
    if (!ctx.client.can("sampling")) {
      return error("Client does not support sampling capabilities");
    }

    // 2. Request completion from the client's LLM
    try {
      const result = await ctx.sample({
        messages: [
          {
            role: "user",
            content: {
              type: "text",
              text: `Please summarize the following text in a ${style} style:\n\n${content}`,
            },
          },
        ],
        maxTokens: 500,
        temperature: 0.7,
      });

      // 3. Return the generated summary
      const summary = result.content?.type === 'text' ? (result.content.text ?? "No text returned") : "No text returned";
      return text(summary);
    } catch (err) {
      return error(`Sampling failed: ${(err as Error).message}`);
    }
  }
);

await server.listen(3000);
```

---

## Recipe 11: Elicitation Server (Human-in-the-Loop)

Pause execution to ask the *user* for input or confirmation via the client UI.

```typescript
import { MCPServer, text, error } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({ name: "approval-server", version: "1.0.0" });

server.tool(
  {
    name: "deploy-production",
    description: "Deploy artifacts to production (requires approval)",
    schema: z.object({ version: z.string() }),
  },
  async ({ version }, ctx) => {
    // 1. Check capability
    if (!ctx.client.can("elicitation")) {
      return error("Client does not support user interaction (elicitation).");
    }

    // 2. Ask user for confirmation
    const response = await ctx.elicit(
      `⚠️ **Production Deployment**\n\nYou are about to deploy version **${version}**.\nAre you sure?`,
      z.object({
        confirmed: z.boolean().describe("Check to confirm deployment"),
        reason: z.string().optional().describe("Reason for deployment"),
      })
    );

    // 3. Handle user choice (action: "accept" | "cancel")
    if (response.action === "cancel" || !response.data?.confirmed) {
      return text("Deployment cancelled by user.");
    }

    // 4. Proceed if confirmed
    await performDeploy(version);
    return text(`Deployment of ${version} started. Reason: ${response.data.reason || "N/A"}`);
  }
);

async function performDeploy(v: string) { /* ... */ }

await server.listen(3000);
```

---

## Recipe 12: Chainable API & Hono Routes

Access the underlying Hono application for advanced routing, middleware, and authentication.

```typescript
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";
import { cors } from "hono/cors";
import { logger } from "hono/logger";

const server = new MCPServer({ name: "hybrid-server", version: "1.0.0" });

// 1. Use Hono middleware directly
server.use(logger());
server.use("/api/*", cors());

// 2. Add custom authentication middleware for specific routes
server.use("/secure/*", async (c, next) => {
  const token = c.req.header("Authorization");
  if (token !== "Bearer secret") return c.text("Unauthorized", 401);
  await next();
});

// 3. Define standard REST endpoints alongside MCP
server.get("/api/status", (c) => c.json({ status: "ok", mcp: true }));

server.post("/secure/trigger", async (c) => {
  const body = await c.req.json();
  return c.json({ triggered: true, data: body });
});

// 4. Define MCP Tools as usual
server.tool(
  { name: "echo", schema: z.object({ msg: z.string() }) },
  async ({ msg }) => text(msg)
);

// 5. Mount a sub-app
const adminApp = new MCPServer({ name: "admin", version: "1.0" });
adminApp.get("/", (c) => c.text("Admin Area"));
server.route("/admin", adminApp); // Mounts at /admin

await server.listen(3000);
```

---

## Recipe 13: Real-time Stock Ticker (SSE Push)

Push live data updates to clients using `ctx.session` and timers.

```typescript
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({ name: "ticker-server", version: "1.0.0" });

// Store active subscriptions: symbol -> Set<sessionId>
const subs = new Map<string, Set<string>>();

// Simulate price updates
setInterval(() => {
  subs.forEach((sessions, symbol) => {
    const price = (Math.random() * 1000).toFixed(2);
    const payload = { symbol, price, ts: Date.now() };
    
    // Notify all subscribers
    for (const sessionId of sessions) {
      server.sendNotificationToSession(sessionId, "price/update", payload);
    }
  });
}, 1000);

server.tool(
  { name: "subscribe", schema: z.object({ symbol: z.string() }) },
  async ({ symbol }, ctx) => {
    if (!subs.has(symbol)) subs.set(symbol, new Set());
    
    // Track session ID
    if (ctx.session?.sessionId) {
      subs.get(symbol)!.add(ctx.session.sessionId);
    }
    
    return text(`Subscribed to ${symbol}. Updates will arrive via 'price/update'.`);
  }
);

server.tool(
  { name: "unsubscribe", schema: z.object({ symbol: z.string() }) },
  async ({ symbol }, ctx) => {
    if (ctx.session?.sessionId && subs.has(symbol)) {
      subs.get(symbol)!.delete(ctx.session.sessionId);
    }
    return text(`Unsubscribed from ${symbol}`);
  }
);

await server.listen(3000);
```
