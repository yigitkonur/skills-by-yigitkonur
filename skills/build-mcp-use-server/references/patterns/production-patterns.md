# Production Patterns for MCP Servers

Battle-tested patterns for building reliable, production-grade MCP servers with mcp-use.

---

## 1. Graceful Shutdown

Register shutdown handlers before calling `server.listen()`. Close resources in reverse initialization order. Guard against double-shutdown and set a hard timeout for stuck cleanup.

```typescript
import { MCPServer } from "mcp-use";

const server = new MCPServer({ name: "my-server", version: "1.0.0" });

// Register all tools, resources, prompts first...

await server.listen({ transportType: "httpStream", port: 3000 });

let isShuttingDown = false;

async function shutdown(signal: string) {
  if (isShuttingDown) return;
  isShuttingDown = true;
  console.log(`[${signal}] Shutting down gracefully...`);

  const forceExit = setTimeout(() => {
    console.error("Forced exit after 10s timeout");
    process.exit(1);
  }, 10_000);

  try {
    await server.close();
    if (dbPool) await dbPool.end();
    if (redisClient) await redisClient.quit();
    clearTimeout(forceExit);
    process.exit(0);
  } catch (err) {
    console.error("Error during shutdown:", err);
    clearTimeout(forceExit);
    process.exit(1);
  }
}

process.on("SIGTERM", () => shutdown("SIGTERM"));
process.on("SIGINT", () => shutdown("SIGINT"));
process.on("uncaughtException", (err) => {
  console.error("Uncaught exception:", err);
  shutdown("uncaughtException");
});
process.on("unhandledRejection", (reason) => {
  console.error("Unhandled rejection:", reason);
  shutdown("unhandledRejection");
});
```

---

## 2. Environment-Based Configuration

Centralize config at the top of the entrypoint. Validate required values at startup — fail fast, not at first request.

```typescript
function requireEnv(key: string): string {
  const val = process.env[key];
  if (!val) throw new Error(`Missing required env var: ${key}`);
  return val;
}

const config = {
  name: process.env.SERVER_NAME || "my-server",
  version: process.env.SERVER_VERSION || "1.0.0",
  port: parseInt(process.env.PORT || "3000", 10),
  transportType: (process.env.TRANSPORT || "httpStream") as "httpStream" | "stdio",
  redisUrl: process.env.REDIS_URL,
  databaseUrl: process.env.DATABASE_URL,
  apiKey: requireEnv("API_KEY"),
  logLevel: process.env.LOG_LEVEL || "info",
  allowedOrigins: process.env.ALLOWED_ORIGINS?.split(",").map(s => s.trim()) || [],
  maxRequestsPerMinute: parseInt(process.env.RATE_LIMIT || "60", 10),
};
```

Use `requireEnv()` for secrets and critical values. Parse numbers with `parseInt(..., 10)`. Split comma-separated lists and trim whitespace.

---

## 3. Lazy Initialization for Expensive Resources

Defer heavyweight connections (database pools, ML models) until first use.

```typescript
import { Pool } from "pg";

let dbPool: Pool | null = null;

async function getDB(): Promise<Pool> {
  if (!dbPool) {
    dbPool = new Pool({
      connectionString: config.databaseUrl,
      max: 20,
      idleTimeoutMillis: 30_000,
      connectionTimeoutMillis: 5_000,
    });
    await dbPool.query("SELECT 1"); // verify connection
  }
  return dbPool;
}

server.tool(
  {
    name: "query-users",
    description: "Query user records from the database",
    schema: z.object({ limit: z.number().int().min(1).max(100).default(10) }),
  },
  async ({ limit }) => {
    const db = await getDB();
    const result = await db.query("SELECT id, name, email FROM users LIMIT $1", [limit]);
    return object(result.rows);
  }
);
```

---

## 4. Connection Pooling for HTTP Clients

Reuse TCP connections with a pooled client. Close the pool in your shutdown handler.

```typescript
import { Pool as UndiciPool } from "undici";

const httpClient = new UndiciPool("https://api.example.com", {
  connections: 10,
  pipelining: 1,
  keepAliveTimeout: 30_000,
});

server.tool(
  {
    name: "fetch-data",
    description: "Fetch data from external API",
    schema: z.object({ endpoint: z.string() }),
  },
  async ({ endpoint }) => {
    const { statusCode, body } = await httpClient.request({
      path: endpoint,
      method: "GET",
      headers: { authorization: `Bearer ${config.apiKey}` },
    });
    if (statusCode !== 200) return text(`API error: ${statusCode}`);
    return object(await body.json());
  }
);
```

---

## 5. Retry with Exponential Backoff

Wrap transient-failure-prone calls with retry logic. Add jitter to prevent thundering herd.

```typescript
async function withRetry<T>(
  fn: () => Promise<T>,
  options: { maxRetries?: number; baseDelayMs?: number; label?: string } = {}
): Promise<T> {
  const { maxRetries = 3, baseDelayMs = 1000, label = "operation" } = options;
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err) {
      if (attempt === maxRetries) throw err;
      const delay = baseDelayMs * Math.pow(2, attempt) + Math.random() * 500;
      console.warn(`[retry] ${label} attempt ${attempt + 1} failed, retrying in ${Math.round(delay)}ms`);
      await new Promise((r) => setTimeout(r, delay));
    }
  }
  throw new Error("Unreachable");
}
```

Only retry transient failures — do not retry 4xx client errors.

---

## 6. Response Caching with TTL

Cache expensive or rate-limited responses in memory. Evict stale entries on read.

```typescript
class TTLCache<T> {
  private cache = new Map<string, { value: T; expiresAt: number }>();

  get(key: string): T | undefined {
    const entry = this.cache.get(key);
    if (!entry) return undefined;
    if (Date.now() > entry.expiresAt) { this.cache.delete(key); return undefined; }
    return entry.value;
  }

  set(key: string, value: T, ttlMs: number): void {
    this.cache.set(key, { value, expiresAt: Date.now() + ttlMs });
  }

  clear(): void { this.cache.clear(); }
}

const responseCache = new TTLCache<unknown>();

server.tool(
  {
    name: "cached-lookup",
    description: "Looks up data with 5-minute cache",
    schema: z.object({ key: z.string() }),
  },
  async ({ key }) => {
    const cached = responseCache.get(key);
    if (cached) return object(cached);
    const fresh = await fetchExpensiveData(key);
    responseCache.set(key, fresh, 5 * 60 * 1000);
    return object(fresh);
  }
);
```

Use a bounded LRU cache in production to prevent unbounded memory growth.

---

## 7. Structured Error Handling

Use `try/catch` in every tool handler. Return user-friendly errors via `text()` — never let raw exceptions reach the client.

```typescript
class ToolError extends Error {
  constructor(message: string, public readonly code: string) {
    super(message);
    this.name = "ToolError";
  }
}

function handleToolError(err: unknown): ReturnType<typeof text> {
  if (err instanceof ToolError) {
    console.warn(`[tool-error] ${err.code}: ${err.message}`);
    return text(`Error (${err.code}): ${err.message}`);
  }
  console.error("[unexpected-error]", err);
  return text("An unexpected error occurred. Check server logs for details.");
}

server.tool(
  { name: "get-user", schema: z.object({ id: z.string() }) },
  async ({ id }) => {
    try {
      const user = await db.findUser(id);
      if (!user) throw new ToolError("User not found", "NOT_FOUND");
      return object(user);
    } catch (err) {
      return handleToolError(err);
    }
  }
);
```

Never include stack traces, internal paths, or secrets in error responses.

---

## 8. Health Check Resource

Expose server health as an MCP resource for monitoring and load balancer probes.

```typescript
server.resource(
  {
    uri: "health://status",
    name: "Server Health",
    description: "Current server health and uptime",
    mimeType: "application/json",
  },
  async () => {
    const uptime = process.uptime();
    const mem = process.memoryUsage();
    return object({
      status: "ok",
      uptime: `${Math.floor(uptime / 60)}m ${Math.floor(uptime % 60)}s`,
      memory: {
        heapUsedMB: Math.round(mem.heapUsed / 1024 / 1024),
        rssMB: Math.round(mem.rss / 1024 / 1024),
      },
      timestamp: new Date().toISOString(),
    });
  }
);
```

---

## 9. Modular Tool Organization

Split tools into domain-specific modules. Keep the entrypoint lean.

```
src/
├── server.ts          # Config, server init, shutdown
├── tools/
│   ├── index.ts       # registerAllTools(server)
│   ├── users.ts       # registerUserTools(server)
│   └── analytics.ts   # registerAnalyticsTools(server)
├── resources/
│   └── health.ts      # registerHealthResource(server)
└── lib/
    ├── db.ts           # Lazy DB pool
    ├── cache.ts        # TTLCache
    └── retry.ts        # withRetry
```

```typescript
// tools/users.ts
export function registerUserTools(server: MCPServer) {
  server.tool(
    { name: "list-users", schema: z.object({ limit: z.number().default(10) }) },
    async ({ limit }) => { /* ... */ }
  );
}

// server.ts
import { registerUserTools } from "./tools/users.js";
import { registerAnalyticsTools } from "./tools/analytics.js";

registerUserTools(server);
registerAnalyticsTools(server);
```

Each module exports a single `register*` function that receives the server instance. Group tools by domain, not by technical concern.

---

## 10. Rate Limiting

Protect expensive or sensitive tools with a sliding-window counter.

```typescript
class RateLimiter {
  private windows = new Map<string, { count: number; resetAt: number }>();

  constructor(private maxRequests: number, private windowMs: number) {}

  check(key: string): boolean {
    const now = Date.now();
    const window = this.windows.get(key);
    if (!window || now > window.resetAt) {
      this.windows.set(key, { count: 1, resetAt: now + this.windowMs });
      return true;
    }
    if (window.count >= this.maxRequests) return false;
    window.count++;
    return true;
  }
}

const limiter = new RateLimiter(config.maxRequestsPerMinute, 60_000);

server.tool(
  { name: "expensive-call", schema: z.object({ query: z.string() }) },
  async ({ query }, { ctx }) => {
    const clientId = ctx?.clientInfo?.name || "anonymous";
    if (!limiter.check(clientId)) {
      return text("Rate limit exceeded. Try again in a minute.");
    }
    // proceed with expensive operation...
  }
);
```

For multi-process deployments, use Redis-backed rate limiting instead of in-memory.

---

## 11. Logging Best Practices

Use structured JSON logging. Include request context for traceability.

```typescript
type LogLevel = "debug" | "info" | "warn" | "error";
const LOG_LEVELS: Record<LogLevel, number> = { debug: 0, info: 1, warn: 2, error: 3 };

function log(level: LogLevel, message: string, meta?: Record<string, unknown>) {
  if (LOG_LEVELS[level] < LOG_LEVELS[config.logLevel as LogLevel]) return;
  const entry = JSON.stringify({
    timestamp: new Date().toISOString(),
    level,
    message,
    server: config.name,
    ...meta,
  });
  if (level === "error") console.error(entry);
  else console.log(entry);
}

// Usage
server.tool(
  { name: "process-data", schema: z.object({ input: z.string() }) },
  async ({ input }) => {
    log("info", "Processing data", { tool: "process-data", inputLength: input.length });
    try {
      const result = await processData(input);
      log("info", "Data processed", { tool: "process-data", resultSize: result.length });
      return object(result);
    } catch (err) {
      log("error", "Processing failed", { tool: "process-data", error: String(err) });
      return text("Processing failed. Check server logs.");
    }
  }
);
```

Emit JSON to stdout/stderr — let the log aggregator parse it. Include `server`, `tool`, and relevant metadata. Never log secrets, tokens, or full request payloads.
