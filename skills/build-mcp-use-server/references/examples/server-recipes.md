# MCP Server Recipes

Complete, copy-pasteable server examples using the mcp-use TypeScript library.

## Recipe 1: File System Server

```typescript
import { MCPServer, text, object, error } from "mcp-use/server";
import z from "zod";
import fs from "fs/promises";
import path from "path";

const server = new MCPServer({
  name: "filesystem-server",
  version: "1.0.0",
  description: "Read and search files in a directory",
});

const ALLOWED_DIR = process.env.FS_ROOT || process.cwd();

server.tool(
  {
    name: "read-file",
    description: "Read contents of a file",
    schema: z.object({
      path: z.string().describe("Relative path to file"),
    }),
  },
  async ({ path: filePath }) => {
    const fullPath = path.resolve(ALLOWED_DIR, filePath);
    if (!fullPath.startsWith(ALLOWED_DIR)) {
      return error("Access denied: path outside allowed directory");
    }
    try {
      const content = await fs.readFile(fullPath, "utf-8");
      return text(content);
    } catch (e) {
      return error(`Failed to read file: ${(e as Error).message}`);
    }
  }
);

server.tool(
  {
    name: "list-files",
    description: "List files in a directory",
    schema: z.object({
      directory: z.string().default(".").describe("Relative directory path"),
      pattern: z.string().optional().describe("Filter by extension, e.g. '.ts'"),
    }),
  },
  async ({ directory, pattern }) => {
    const fullPath = path.resolve(ALLOWED_DIR, directory);
    if (!fullPath.startsWith(ALLOWED_DIR)) {
      return error("Access denied: path outside allowed directory");
    }
    const entries = await fs.readdir(fullPath, { withFileTypes: true });
    const items = entries
      .filter(e => !pattern || e.name.endsWith(pattern))
      .map(e => ({ name: e.name, type: e.isDirectory() ? "dir" : "file" }));
    return object({ directory, items, count: items.length });
  }
);

server.resource(
  {
    name: "file",
    uri: "file://{path}",
    title: "File Contents",
    description: "Read any file by path",
  },
  async ({ path: filePath }) => {
    const fullPath = path.resolve(ALLOWED_DIR, filePath);
    const content = await fs.readFile(fullPath, "utf-8");
    return text(content);
  }
);

await server.listen();
```

## Recipe 2: Database Server (with Connection Pooling)

```typescript
import { MCPServer, text, object, error } from "mcp-use/server";
import z from "zod";
import Database from "better-sqlite3";

const server = new MCPServer({
  name: "database-server", version: "1.0.0",
  description: "Query and explore a SQLite database",
});

const db = new Database(process.env.DB_PATH || "./data.db");
db.pragma("journal_mode = WAL");
db.pragma("busy_timeout = 5000");

server.tool(
  {
    name: "query",
    description: "Run a read-only SQL query",
    schema: z.object({
      sql: z.string().describe("SQL SELECT query"),
      params: z.array(z.unknown()).optional().describe("Bind parameters"),
      limit: z.number().default(100).describe("Max rows"),
    }),
  },
  async ({ sql, params, limit }) => {
    if (!/^\s*SELECT/i.test(sql)) return error("Only SELECT queries allowed");
    try {
      const limited = sql.includes("LIMIT") ? sql : `${sql} LIMIT ${limit}`;
      const rows = db.prepare(limited).all(...(params || []));
      return object({ rows, count: rows.length, truncated: rows.length >= limit });
    } catch (e) {
      return error(`Query failed: ${(e as Error).message}`);
    }
  }
);

server.tool(
  {
    name: "list-tables",
    description: "List all tables in the database",
    schema: z.object({}),
  },
  async () => {
    const tables = db.prepare(
      `SELECT name, type FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%' ORDER BY name`
    ).all();
    return object({ tables, count: tables.length });
  }
);

server.tool(
  {
    name: "describe-table",
    description: "Show columns and row count for a table",
    schema: z.object({ table: z.string().describe("Table name") }),
  },
  async ({ table }) => {
    const safe = table.replace(/[^a-zA-Z0-9_]/g, "");
    try {
      const columns = db.prepare(`PRAGMA table_info('${safe}')`).all();
      const { count } = db.prepare(`SELECT COUNT(*) as count FROM "${safe}"`).get() as { count: number };
      return object({ table: safe, columns, rowCount: count });
    } catch { return error(`Table not found: ${safe}`); }
  }
);

server.resource(
  { name: "schema", uri: "db://schema", title: "Full Schema", description: "Database schema as SQL" },
  async () => {
    const rows = db.prepare(
      `SELECT sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%'`
    ).all() as { sql: string }[];
    return text(rows.map(r => r.sql + ";").join("\n\n"));
  }
);

process.on("SIGINT", () => { db.close(); process.exit(0); });
await server.listen();
```

## Recipe 3: API Wrapper Server (with Caching)

```typescript
import { MCPServer, object, error } from "mcp-use/server";
import z from "zod";

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
import z from "zod";

const server = new MCPServer({
  name: "task-manager-server", version: "1.0.0",
  description: "Task management with notifications and progress",
});

interface Task { id: string; title: string; status: "todo" | "in-progress" | "done"; priority: "low" | "medium" | "high"; tags: string[]; createdAt: string; }
const tasks = new Map<string, Task>();

server.tool(
  { name: "create-task", description: "Create a new task",
    schema: z.object({ title: z.string(), priority: z.enum(["low", "medium", "high"]).default("medium"), tags: z.array(z.string()).default([]) }) },
  async ({ title, priority, tags }, { notify }) => {
    const id = `task-${Date.now().toString(36)}`;
    const task: Task = { id, title, status: "todo", priority, tags, createdAt: new Date().toISOString() };
    tasks.set(id, task);
    await notify(`Task created: ${title}`);
    return object({ task });
  }
);

server.tool(
  { name: "update-task", description: "Update task status or details",
    schema: z.object({ id: z.string(), status: z.enum(["todo", "in-progress", "done"]).optional(), title: z.string().optional(), priority: z.enum(["low", "medium", "high"]).optional() }) },
  async ({ id, status, title, priority }, { notify }) => {
    const task = tasks.get(id);
    if (!task) return error(`Task not found: ${id}`);
    if (status) task.status = status;
    if (title) task.title = title;
    if (priority) task.priority = priority;
    await notify(`Task updated: ${task.title} → ${task.status}`);
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
  async ({ tasks: list }, { notify, progress }) => {
    const created: Task[] = [];
    for (let i = 0; i < list.length; i++) {
      const { title, priority, tags } = list[i];
      const task: Task = { id: `task-${Date.now().toString(36)}-${i}`, title, status: "todo", priority, tags, createdAt: new Date().toISOString() };
      tasks.set(task.id, task);
      created.push(task);
      await progress((i + 1) / list.length, `Imported ${i + 1}/${list.length}`);
    }
    await notify(`Bulk import complete: ${created.length} tasks`);
    return object({ imported: created.length, tasks: created });
  }
);

server.tool(
  { name: "task-summary", description: "Markdown summary of all tasks", schema: z.object({}) },
  async () => {
    const all = Array.from(tasks.values());
    const g = { todo: all.filter(t => t.status === "todo"), "in-progress": all.filter(t => t.status === "in-progress"), done: all.filter(t => t.status === "done") };
    const lines = [`# Task Summary`, ``, `**Total:** ${all.length} | **Todo:** ${g.todo.length} | **In Progress:** ${g["in-progress"].length} | **Done:** ${g.done.length}`, ``];
    for (const [s, items] of Object.entries(g)) {
      if (!items.length) continue;
      lines.push(`## ${s}`, ``);
      for (const t of items) lines.push(`- **[${t.priority.toUpperCase()}]** ${t.title} _(${t.id})_`);
      lines.push(``);
    }
    return markdown(lines.join("\n"));
  }
);

await server.listen();
```

## Key Patterns

**Error handling** — return `error()` instead of throwing:
```typescript
return error(`File not found: ${filePath}`);  // structured error to client
```

**Schema descriptions** — always use `.describe()` for tool parameter help:
```typescript
schema: z.object({
  query: z.string().min(1).describe("Search query"),
  limit: z.number().default(10).describe("Max results (1-100)"),
})
```

**Response helpers** — `text()` for raw content, `object()` for structured data, `markdown()` for rich output, `error()` for failures.
