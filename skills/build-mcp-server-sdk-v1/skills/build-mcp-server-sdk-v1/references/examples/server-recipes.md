# Server Recipes

Copy-paste working server examples for common patterns.

## Recipe 1 — API wrapper server (stdio)

Wraps a REST API as MCP tools. The most common server pattern.

```typescript
#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const API_BASE = process.env.API_BASE_URL;
const API_KEY = process.env.API_KEY;

if (!API_BASE || !API_KEY) {
  console.error("API_BASE_URL and API_KEY environment variables are required");
  process.exit(1);
}

async function apiRequest(path: string, options?: RequestInit) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Authorization": `Bearer ${API_KEY}`,
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`API ${response.status}: ${body}`);
  }

  return response.json();
}

const server = new McpServer(
  { name: "api-wrapper", version: "1.0.0" },
  { instructions: "Wraps the Example API for search and CRUD operations" },
);

server.registerTool("search", {
  description: "Search for items by query. Returns name, ID, and description for each match.",
  inputSchema: {
    query: z.string().min(1).describe("Search query"),
    limit: z.number().min(1).max(100).default(20).describe("Max results"),
  },
  annotations: {
    readOnlyHint: true,
    destructiveHint: false,
    idempotentHint: true,
    openWorldHint: true,
  },
}, async ({ query, limit }) => {
  try {
    const data = await apiRequest(`/search?q=${encodeURIComponent(query)}&limit=${limit}`);
    return {
      content: [{
        type: "text",
        text: JSON.stringify(data.results, null, 2),
      }],
    };
  } catch (error) {
    return {
      content: [{ type: "text", text: `Search failed: ${(error as Error).message}` }],
      isError: true,
    };
  }
});

server.registerTool("get-item", {
  description: "Get full details of an item by ID",
  inputSchema: {
    id: z.string().describe("Item ID"),
  },
  annotations: {
    readOnlyHint: true,
    destructiveHint: false,
    idempotentHint: true,
    openWorldHint: true,
  },
}, async ({ id }) => {
  try {
    const item = await apiRequest(`/items/${encodeURIComponent(id)}`);
    return {
      content: [{ type: "text", text: JSON.stringify(item, null, 2) }],
    };
  } catch (error) {
    return {
      content: [{ type: "text", text: `Get failed: ${(error as Error).message}` }],
      isError: true,
    };
  }
});

server.registerTool("create-item", {
  description: "Create a new item with a name and optional description",
  inputSchema: {
    name: z.string().min(1).max(200).describe("Item name"),
    description: z.string().optional().describe("Item description"),
  },
  annotations: {
    readOnlyHint: false,
    destructiveHint: false,
    idempotentHint: false,
    openWorldHint: true,
  },
}, async ({ name, description }) => {
  try {
    const item = await apiRequest("/items", {
      method: "POST",
      body: JSON.stringify({ name, description }),
    });
    return {
      content: [{ type: "text", text: `Created item: ${JSON.stringify(item, null, 2)}` }],
    };
  } catch (error) {
    return {
      content: [{ type: "text", text: `Create failed: ${(error as Error).message}` }],
      isError: true,
    };
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

## Recipe 2 — File system server (stdio)

Provides read access to a project directory.

```typescript
#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { ResourceTemplate } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { readFile, readdir, stat } from "node:fs/promises";
import { join, resolve, relative } from "node:path";

const ROOT_DIR = resolve(process.argv[2] || ".");

const server = new McpServer(
  { name: "filesystem", version: "1.0.0" },
  { instructions: `File system access for ${ROOT_DIR}` },
);

// Tool: search files by glob
server.registerTool("find-files", {
  description: "Find files matching a pattern in the project directory",
  inputSchema: {
    pattern: z.string().describe("Glob pattern (e.g., '**/*.ts')"),
  },
  annotations: { readOnlyHint: true },
}, async ({ pattern }) => {
  const { glob } = await import("node:fs");
  const { promisify } = await import("node:util");
  // Use recursive readdir as a simpler alternative
  const files = await findFiles(ROOT_DIR, pattern);
  return {
    content: [{ type: "text", text: files.join("\n") }],
  };
});

// Tool: read file contents
server.registerTool("read-file", {
  description: "Read the contents of a file by path (relative to project root)",
  inputSchema: {
    path: z.string().describe("File path relative to project root"),
  },
  annotations: { readOnlyHint: true },
}, async ({ path: filePath }) => {
  const fullPath = resolve(ROOT_DIR, filePath);

  // Security: prevent path traversal
  if (!fullPath.startsWith(ROOT_DIR)) {
    return {
      content: [{ type: "text", text: "Error: path traversal not allowed" }],
      isError: true,
    };
  }

  try {
    const content = await readFile(fullPath, "utf-8");
    return {
      content: [{ type: "text", text: content }],
    };
  } catch {
    return {
      content: [{ type: "text", text: `Error: file not found: ${filePath}` }],
      isError: true,
    };
  }
});

// Resource: file by path template
const fileTemplate = new ResourceTemplate("file://{path}", {
  list: async () => {
    const files = await listAllFiles(ROOT_DIR);
    return {
      resources: files.map((f) => ({
        uri: `file://${relative(ROOT_DIR, f)}`,
        name: relative(ROOT_DIR, f),
        mimeType: "text/plain",
      })),
    };
  },
});

server.registerResource("project-file", fileTemplate, {
  description: "Read a project file by path",
  mimeType: "text/plain",
}, async (uri, variables) => ({
  contents: [{
    uri: uri.href,
    text: await readFile(resolve(ROOT_DIR, variables.path), "utf-8"),
  }],
}));

async function listAllFiles(dir: string): Promise<string[]> {
  const entries = await readdir(dir, { withFileTypes: true });
  const files: string[] = [];
  for (const entry of entries) {
    const full = join(dir, entry.name);
    if (entry.isDirectory() && !entry.name.startsWith(".")) {
      files.push(...(await listAllFiles(full)));
    } else if (entry.isFile()) {
      files.push(full);
    }
  }
  return files;
}

async function findFiles(dir: string, pattern: string): Promise<string[]> {
  const all = await listAllFiles(dir);
  const regex = new RegExp(pattern.replace(/\*/g, ".*"));
  return all.map((f) => relative(dir, f)).filter((f) => regex.test(f));
}

const transport = new StdioServerTransport();
await server.connect(transport);
```

## Recipe 3 — Database query server (HTTP, stateful)

Exposes read-only database queries over HTTP with session management.

```typescript
#!/usr/bin/env node
import express from "express";
import { randomUUID } from "node:crypto";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { createMcpExpressApp } from "@modelcontextprotocol/sdk/server/express.js";
import { isInitializeRequest } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";

const app = createMcpExpressApp();
const transports: Record<string, StreamableHTTPServerTransport> = {};

function createServer(): McpServer {
  const server = new McpServer(
    { name: "db-query", version: "1.0.0" },
    { instructions: "Read-only database query server" },
  );

  server.registerTool("query", {
    description: "Execute a read-only SQL query. Only SELECT statements are allowed.",
    inputSchema: {
      sql: z.string().min(1).describe("SQL SELECT query"),
      params: z.array(z.union([z.string(), z.number(), z.boolean(), z.null()]))
        .optional()
        .describe("Query parameters for prepared statement"),
    },
    annotations: {
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: false,
    },
  }, async ({ sql, params }) => {
    // Validate read-only
    const normalized = sql.trim().toUpperCase();
    if (!normalized.startsWith("SELECT")) {
      return {
        content: [{ type: "text", text: "Error: only SELECT queries are allowed" }],
        isError: true,
      };
    }

    try {
      const rows = await executeQuery(sql, params);
      return {
        content: [{
          type: "text",
          text: JSON.stringify({ rows, count: rows.length }, null, 2),
        }],
      };
    } catch (error) {
      return {
        content: [{ type: "text", text: `Query error: ${(error as Error).message}` }],
        isError: true,
      };
    }
  });

  server.registerTool("list-tables", {
    description: "List all tables in the database",
    annotations: { readOnlyHint: true },
  }, async () => {
    const tables = await executeQuery(
      "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
    );
    return {
      content: [{
        type: "text",
        text: tables.map((t: { table_name: string }) => t.table_name).join("\n"),
      }],
    };
  });

  server.registerTool("describe-table", {
    description: "Show columns and types for a table",
    inputSchema: {
      table: z.string().describe("Table name"),
    },
    annotations: { readOnlyHint: true },
  }, async ({ table }) => {
    const columns = await executeQuery(
      "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = $1",
      [table]
    );
    return {
      content: [{ type: "text", text: JSON.stringify(columns, null, 2) }],
    };
  });

  return server;
}

// Replace with your actual database client
async function executeQuery(sql: string, params?: unknown[]): Promise<unknown[]> {
  // Example: const { rows } = await pool.query(sql, params);
  // return rows;
  throw new Error("Implement with your database client");
}

app.post("/mcp", async (req, res) => {
  const sessionId = req.headers["mcp-session-id"] as string | undefined;

  if (sessionId && transports[sessionId]) {
    await transports[sessionId].handleRequest(req, res, req.body);
    return;
  }

  if (!sessionId && isInitializeRequest(req.body)) {
    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: () => randomUUID(),
      onsessioninitialized: (sid) => { transports[sid] = transport; },
    });
    transport.onclose = () => {
      const sid = transport.sessionId;
      if (sid) delete transports[sid];
    };

    const server = createServer();
    await server.connect(transport);
    await transport.handleRequest(req, res, req.body);
    return;
  }

  res.status(400).json({
    jsonrpc: "2.0",
    error: { code: -32000, message: "Bad Request" },
    id: null,
  });
});

app.get("/mcp", async (req, res) => {
  const sid = req.headers["mcp-session-id"] as string;
  if (!sid || !transports[sid]) return res.status(400).send("Invalid session");
  await transports[sid].handleRequest(req, res);
});

app.delete("/mcp", async (req, res) => {
  const sid = req.headers["mcp-session-id"] as string;
  if (sid && transports[sid]) await transports[sid].handleRequest(req, res);
  res.status(200).end();
});

app.listen(3000, () => console.error("DB query MCP server on :3000"));
```

## Recipe 4 — Multi-capability server with prompts

A server that combines tools, resources, and prompts.

```typescript
#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { ResourceTemplate } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

const server = new McpServer(
  { name: "docs-assistant", version: "1.0.0" },
  { instructions: "Documentation assistant with search, templates, and analysis" },
);

// --- Tools ---

server.registerTool("search-docs", {
  description: "Search documentation by keyword",
  inputSchema: {
    query: z.string().describe("Search query"),
    section: z.enum(["api", "guides", "faq"]).optional().describe("Limit to section"),
  },
  annotations: { readOnlyHint: true, openWorldHint: false },
}, async ({ query, section }) => {
  const results = await searchDocumentation(query, section);
  return {
    content: [{ type: "text", text: JSON.stringify(results, null, 2) }],
  };
});

server.registerTool("update-doc", {
  description: "Update a documentation page",
  inputSchema: {
    path: z.string().describe("Doc path (e.g., 'api/authentication.md')"),
    content: z.string().describe("New markdown content"),
    message: z.string().describe("Change description"),
  },
  annotations: {
    readOnlyHint: false,
    destructiveHint: false,
    idempotentHint: true,
    openWorldHint: false,
  },
}, async ({ path, content, message }) => {
  await writeDoc(path, content, message);
  return {
    content: [{ type: "text", text: `Updated ${path}: ${message}` }],
  };
});

// --- Resources ---

const docTemplate = new ResourceTemplate("docs://{section}/{page}", {
  list: async () => ({
    resources: [
      { uri: "docs://api/overview", name: "API Overview" },
      { uri: "docs://guides/quickstart", name: "Quick Start Guide" },
    ],
  }),
});

server.registerResource("doc-page", docTemplate, {
  description: "Documentation page",
  mimeType: "text/markdown",
}, async (uri, { section, page }) => ({
  contents: [{
    uri: uri.href,
    text: await readDoc(`${section}/${page}.md`),
    mimeType: "text/markdown",
  }],
}));

// --- Prompts ---

server.registerPrompt("write-api-doc", {
  description: "Generate API documentation for an endpoint",
  argsSchema: {
    method: z.enum(["GET", "POST", "PUT", "DELETE"]).describe("HTTP method"),
    path: z.string().describe("Endpoint path"),
    description: z.string().describe("What the endpoint does"),
  },
}, async ({ method, path, description }) => ({
  messages: [{
    role: "user",
    content: {
      type: "text",
      text: [
        `Write API documentation for this endpoint:`,
        `- Method: ${method}`,
        `- Path: ${path}`,
        `- Description: ${description}`,
        ``,
        `Include: description, parameters, request/response examples, error codes.`,
        `Format as markdown.`,
      ].join("\n"),
    },
  }],
}));

// Placeholder implementations
async function searchDocumentation(query: string, section?: string) { return []; }
async function readDoc(path: string) { return ""; }
async function writeDoc(path: string, content: string, message: string) {}

const transport = new StdioServerTransport();
await server.connect(transport);
```
