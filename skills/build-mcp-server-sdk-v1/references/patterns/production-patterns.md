# Production Patterns

Patterns for building robust, production-grade MCP servers.

## Structured logging

All MCP server logging must go to stderr. Use a structured logger:

```typescript
function log(level: string, message: string, data?: Record<string, unknown>) {
  const entry = {
    timestamp: new Date().toISOString(),
    level,
    message,
    ...data,
  };
  console.error(JSON.stringify(entry));
}

// In tool handlers:
server.registerTool("my-tool", config, async (args, extra) => {
  log("info", "Tool called", { tool: "my-tool", sessionId: extra.sessionId });
  // ...
});
```

### MCP logging notifications

Send log messages to connected clients via the SDK:

```typescript
await server.sendLoggingMessage({
  level: "info",
  data: "Processing completed",
});
```

Available levels: `debug`, `info`, `notice`, `warning`, `error`, `critical`, `alert`, `emergency`.

## Error handling patterns

### API wrapper error handling

```typescript
async function safeApiCall<T>(
  fn: () => Promise<T>,
  context: string,
): Promise<{ data: T } | { error: string }> {
  try {
    const data = await fn();
    return { data };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    log("error", `${context} failed`, { error: message });

    if (message.includes("429") || message.includes("rate limit")) {
      return { error: `Rate limit exceeded. Wait a moment and try again.` };
    }
    if (message.includes("401") || message.includes("403")) {
      return { error: `Authentication failed. Check your API credentials.` };
    }
    if (message.includes("404")) {
      return { error: `Resource not found. Verify the ID or path is correct.` };
    }
    return { error: `${context} failed: ${message}` };
  }
}

// Usage in tool handler:
server.registerTool("fetch-data", config, async ({ id }) => {
  const result = await safeApiCall(() => api.getData(id), "Fetch data");

  if ("error" in result) {
    return { content: [{ type: "text", text: result.error }], isError: true };
  }
  return { content: [{ type: "text", text: JSON.stringify(result.data, null, 2) }] };
});
```

### Input sanitization

```typescript
function sanitizePath(input: string, rootDir: string): string | null {
  const resolved = resolve(rootDir, input);
  if (!resolved.startsWith(rootDir)) return null; // path traversal
  return resolved;
}

function sanitizeUrl(input: string): string | null {
  try {
    const url = new URL(input);
    if (!["http:", "https:"].includes(url.protocol)) return null;
    return url.href;
  } catch {
    return null;
  }
}
```

## Rate limiting

### Per-session rate limiting

```typescript
const rateLimits = new Map<string, { count: number; resetAt: number }>();

function checkRateLimit(sessionId: string, limit = 60, windowMs = 60_000): boolean {
  const now = Date.now();
  const entry = rateLimits.get(sessionId);

  if (!entry || now > entry.resetAt) {
    rateLimits.set(sessionId, { count: 1, resetAt: now + windowMs });
    return true;
  }

  if (entry.count >= limit) return false;
  entry.count++;
  return true;
}

// In tool handler:
server.registerTool("api-call", config, async (args, extra) => {
  if (extra.sessionId && !checkRateLimit(extra.sessionId)) {
    return {
      content: [{ type: "text", text: "Rate limit exceeded. Try again in a minute." }],
      isError: true,
    };
  }
  // ... proceed
});
```

## Response formatting

### Markdown for LLM consumption

Format tool responses as structured text that LLMs can parse efficiently:

```typescript
function formatResults(items: Array<{ name: string; id: string; status: string }>): string {
  if (items.length === 0) return "No results found.";

  const header = `Found ${items.length} item(s):\n\n`;
  const rows = items.map((item, i) =>
    `${i + 1}. **${item.name}** (ID: ${item.id}) — ${item.status}`
  ).join("\n");

  return header + rows;
}
```

### Truncation for large responses

```typescript
const MAX_RESPONSE_LENGTH = 50_000; // characters

function truncateResponse(text: string): string {
  if (text.length <= MAX_RESPONSE_LENGTH) return text;
  return text.slice(0, MAX_RESPONSE_LENGTH) +
    `\n\n[Truncated — ${text.length - MAX_RESPONSE_LENGTH} characters omitted. Use pagination to see more.]`;
}
```

## Configuration management

```typescript
interface ServerConfig {
  name: string;
  version: string;
  apiBaseUrl: string;
  apiKey: string;
  maxResultsPerPage: number;
  logLevel: string;
}

function loadConfig(): ServerConfig {
  const required = (name: string): string => {
    const value = process.env[name];
    if (!value) {
      console.error(`Required environment variable ${name} is not set`);
      process.exit(1);
    }
    return value;
  };

  return {
    name: process.env.SERVER_NAME || "my-mcp-server",
    version: process.env.SERVER_VERSION || "1.0.0",
    apiBaseUrl: required("API_BASE_URL"),
    apiKey: required("API_KEY"),
    maxResultsPerPage: parseInt(process.env.MAX_RESULTS || "50", 10),
    logLevel: process.env.LOG_LEVEL || "info",
  };
}
```

## Dynamic tool registration

Register or update tools at runtime based on server state:

```typescript
const tools = new Map<string, ReturnType<McpServer["registerTool"]>>();

async function refreshToolsFromApi(server: McpServer) {
  const endpoints = await fetchApiEndpoints();

  // Remove tools for deleted endpoints
  for (const [name, handle] of tools) {
    if (!endpoints.find((e) => e.name === name)) {
      handle.remove();
      tools.delete(name);
    }
  }

  // Add or update tools for current endpoints
  for (const endpoint of endpoints) {
    if (tools.has(endpoint.name)) {
      tools.get(endpoint.name)!.update({
        description: endpoint.description,
      });
    } else {
      const handle = server.registerTool(endpoint.name, {
        description: endpoint.description,
        inputSchema: buildSchemaFromEndpoint(endpoint),
        annotations: { readOnlyHint: endpoint.method === "GET" },
      }, createHandler(endpoint));
      tools.set(endpoint.name, handle);
    }
  }
}
```

## Timeout handling

```typescript
async function withTimeout<T>(
  promise: Promise<T>,
  timeoutMs: number,
  context: string,
): Promise<T> {
  const timeout = new Promise<never>((_, reject) =>
    setTimeout(() => reject(new Error(`${context} timed out after ${timeoutMs}ms`)), timeoutMs)
  );
  return Promise.race([promise, timeout]);
}

// In tool handler:
server.registerTool("slow-op", config, async (args, extra) => {
  try {
    const result = await withTimeout(
      performSlowOperation(args),
      30_000,
      "slow-op",
    );
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  } catch (error) {
    return {
      content: [{ type: "text", text: (error as Error).message }],
      isError: true,
    };
  }
});
```

## Cancellation via AbortSignal

Every handler receives an `AbortSignal` via `extra.signal`. Use it for cooperative cancellation:

```typescript
server.registerTool("long-task", config, async (args, extra) => {
  for (const chunk of dataChunks) {
    if (extra.signal.aborted) {
      return {
        content: [{ type: "text", text: "Operation cancelled" }],
        isError: true,
      };
    }
    await processChunk(chunk);
  }
  return { content: [{ type: "text", text: "Done" }] };
});

// Pass signal to fetch calls:
const response = await fetch(url, { signal: extra.signal });
```
