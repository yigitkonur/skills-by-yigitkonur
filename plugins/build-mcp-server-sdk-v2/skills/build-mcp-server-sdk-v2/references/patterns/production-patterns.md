# Production Patterns (v2)

Patterns for shipping v2 MCP servers under realistic load. Focused on logging, error handling, rate limiting, response formatting, configuration, and cancellation.

## Logging — two channels

v2 servers should write to two channels: **stderr** for operator visibility and **`ctx.mcpReq.log()`** for client visibility (structured log notifications the LLM and host can act on).

### Stderr structured logger

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
```

Stdout is reserved for JSON-RPC traffic on stdio transport — never write logs there.

### Client-visible logging via ctx

```typescript
server.registerTool("fetch-data", schema, async ({ id }, ctx) => {
  await ctx.mcpReq.log("info", { event: "fetch.start", id, sessionId: ctx.sessionId });
  // ...
});
```

Levels: `debug`, `info`, `notice`, `warning`, `error`, `critical`, `alert`, `emergency`. The host filters by client preference; the SDK forwards the notification.

### Server-wide logging notifications

For events outside any specific request (startup, periodic state changes):

```typescript
await server.sendLoggingMessage({
  level: "info",
  data: "Indexed 1,200 records",
});
```

## Error handling

### API wrapper with classification

```typescript
async function safeApiCall<T>(
  fn: () => Promise<T>,
  context: string,
): Promise<{ data: T } | { error: string }> {
  try {
    return { data: await fn() };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    log("error", `${context} failed`, { error: message });

    if (/429|rate limit/i.test(message)) {
      return { error: "Rate limit exceeded. Wait a moment and try again." };
    }
    if (/401|403/.test(message)) {
      return { error: "Authentication failed. Check API credentials." };
    }
    if (/404/.test(message)) {
      return { error: "Resource not found. Verify the ID or path." };
    }
    return { error: `${context} failed: ${message}` };
  }
}

server.registerTool("fetch-data", schema, async ({ id }, ctx) => {
  const result = await safeApiCall(() => api.getData(id, { signal: ctx.mcpReq.signal }), "Fetch");
  if ("error" in result) {
    return { content: [{ type: "text" as const, text: result.error }], isError: true };
  }
  return {
    content: [{ type: "text" as const, text: JSON.stringify(result.data, null, 2) }],
  };
});
```

The `signal: ctx.mcpReq.signal` propagation is the v2 idiom — fetch aborts cooperatively when the client cancels.

### Soft vs hard errors

- **Soft (`isError: true` in CallToolResult):** rate limits, missing scope, recoverable API failures, validation errors. The LLM self-corrects.
- **Hard (`throw new ProtocolError(...)`):** malformed protocol input, server in an unusable state. The client treats this as protocol-level.

Default to soft. Reach for `ProtocolError` only when the request itself is invalid.

### Input sanitization

```typescript
import { isAbsolute, relative, resolve } from "node:path";

function sanitizePath(input: string, rootDir: string): string | null {
  const root = resolve(rootDir);
  const target = resolve(root, input);
  const rel = relative(root, target);
  if (rel === "" || (!rel.startsWith("..") && !isAbsolute(rel))) return target;
  return null;
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

Zod validates structure; sanitization checks semantics. Use both.

## Rate limiting

### Per-session in-memory limiter

```typescript
const rateLimits = new Map<string, { count: number; resetAt: number }>();

function checkRateLimit(sessionId: string | undefined, limit = 60, windowMs = 60_000): boolean {
  if (!sessionId) return true; // stdio: single client, no limit needed
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

server.registerTool("api-call", schema, async (args, ctx) => {
  if (!checkRateLimit(ctx.sessionId)) {
    return {
      content: [{ type: "text" as const, text: "Rate limit exceeded. Try again in a minute." }],
      isError: true,
    };
  }
  // ...
});
```

For multi-process deployments, swap the in-memory map for Redis. The shape of the check stays identical.

### Per-user (auth-aware) limiter

When `ctx.http?.authInfo` is populated, key by user not session — multiple sessions per user shouldn't multiply the budget.

```typescript
const key = ctx.http?.authInfo?.subject ?? ctx.sessionId ?? "anon";
if (!checkRateLimit(key)) { /* ... */ }
```

## Response formatting

### Markdown structure

LLMs parse structure efficiently. Use lists, bold, code blocks deliberately.

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

### Truncation

Tool responses larger than ~50K characters bloat the LLM context. Truncate and signal pagination:

```typescript
const MAX_RESPONSE_LENGTH = 50_000;

function truncateResponse(text: string): string {
  if (text.length <= MAX_RESPONSE_LENGTH) return text;
  return text.slice(0, MAX_RESPONSE_LENGTH) +
    `\n\n[Truncated — ${text.length - MAX_RESPONSE_LENGTH} characters omitted. Use pagination to see more.]`;
}
```

If the tool has an `outputSchema`, prefer `structuredContent` for the data and a short `text` for the human-readable summary — the host can render the structured payload directly.

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

In v2 ESM-only contexts, prefer `import process from "node:process"` over the implicit global when stricter lint rules are enabled.

## Dynamic tool registration

`server.registerTool()` returns a `RegisteredTool` handle with `enable()`, `disable()`, `remove()`, and `update()`. v2 keeps the handle shape unchanged from v1 — same patterns work.

```typescript
const tools = new Map<string, ReturnType<typeof server.registerTool>>();

async function refreshToolsFromApi(server: McpServer) {
  const endpoints = await fetchApiEndpoints();

  for (const [name, handle] of tools) {
    if (!endpoints.find((e) => e.name === name)) {
      handle.remove();
      tools.delete(name);
    }
  }

  for (const endpoint of endpoints) {
    const existing = tools.get(endpoint.name);
    if (existing) {
      existing.update({ description: endpoint.description });
    } else {
      tools.set(endpoint.name, server.registerTool(endpoint.name, {
        description: endpoint.description,
        inputSchema: buildSchemaFromEndpoint(endpoint),
        annotations: { readOnlyHint: endpoint.method === "GET" },
      }, createHandler(endpoint)));
    }
  }
}
```

After a refresh, call `server.sendToolListChanged()` so connected clients re-fetch the tool list.

## Timeout handling

```typescript
async function withTimeout<T>(
  operation: (signal: AbortSignal) => Promise<T>,
  timeoutMs: number,
  context: string,
  parentSignal: AbortSignal,
): Promise<T> {
  const timeoutSignal = AbortSignal.timeout(timeoutMs);
  const signal = AbortSignal.any([parentSignal, timeoutSignal]);
  try {
    return await operation(signal);
  } catch (error) {
    if (timeoutSignal.aborted) {
      throw new Error(`${context} timed out after ${timeoutMs}ms`);
    }
    throw error;
  }
}

server.registerTool("slow-op", schema, async (args, ctx) => {
  try {
    const result = await withTimeout(
      (signal) => performSlowOperation(args, { signal }),
      30_000,
      "slow-op",
      ctx.mcpReq.signal
    );
    return { content: [{ type: "text" as const, text: JSON.stringify(result) }] };
  } catch (error) {
    return {
      content: [{ type: "text" as const, text: (error as Error).message }],
      isError: true,
    };
  }
});
```

`AbortSignal.timeout()` and `AbortSignal.any()` require Node 20-compatible runtimes. If a project pins an older runtime despite v2's Node 20+ requirement, use a controller-based fallback and still propagate `ctx.mcpReq.signal`.

## Cancellation via AbortSignal

Every handler receives an `AbortSignal` via `ctx.mcpReq.signal`. Forward it to every async I/O call.

```typescript
server.registerTool("long-task", schema, async (args, ctx) => {
  for (const chunk of dataChunks) {
    if (ctx.mcpReq.signal.aborted) {
      return {
        content: [{ type: "text" as const, text: "Operation cancelled" }],
        isError: true,
      };
    }
    await processChunk(chunk);
  }
  return { content: [{ type: "text" as const, text: "Done" }] };
});

// fetch automatically aborts when signal fires
const response = await fetch(url, { signal: ctx.mcpReq.signal });
```

Cooperative cancellation is critical under HTTP transport — clients disconnect, networks blip, sessions reset. Without `signal` propagation, server work continues invisibly to the host.

## Graceful shutdown

```typescript
process.on("SIGINT", async () => {
  await server.close();
  process.exit(0);
});
process.on("SIGTERM", async () => {
  await server.close();
  process.exit(0);
});
```

For HTTP transport, also drain in-flight sessions:

```typescript
async function shutdown() {
  for (const transport of transports.values()) {
    transport.close();
  }
  await server.close();
  httpServer.close(() => process.exit(0));
}
```

Skipping shutdown handling leaks transports during deploys, which surfaces as orphaned sessions on the host.

## ESM and Node 20+ reminders

- `"type": "module"` in `package.json`. v2 has no CommonJS dual-publish.
- `"engines": { "node": ">=20" }`. v2 uses Node 20 features (`AbortSignal.any`, etc.) at the SDK level.
- Avoid `require()` in production code. If CommonJS-only interop is unavoidable, use `createRequire(import.meta.url)` from `node:module`.

## Production checklist

- [ ] All logs go to stderr (operator) or `ctx.mcpReq.log()` (client) — never stdout under stdio.
- [ ] Every async I/O call receives `ctx.mcpReq.signal`.
- [ ] Soft errors use `isError: true`; hard errors throw `ProtocolError`.
- [ ] Rate limits keyed by user when authenticated, by session otherwise.
- [ ] Large responses truncated; structured data sent via `outputSchema` + `structuredContent`.
- [ ] Config loaded from env at startup; missing required vars exit non-zero.
- [ ] `SIGINT` and `SIGTERM` handlers close the server cleanly.
- [ ] HTTP transport drains in-flight sessions on shutdown.
- [ ] Input sanitization for paths, URLs, IDs — Zod validates shape, sanitizers check semantics.
