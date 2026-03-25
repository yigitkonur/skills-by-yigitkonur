# Production Patterns for MCP Servers

Battle-tested patterns for building reliable, production-grade MCP servers with mcp-use.

> **Note:** All examples use `mcp-use/server` for server-side imports and `zod` for schema validation.

---

## 1. Graceful Shutdown

Register shutdown handlers before calling `server.listen()`. Close resources in reverse order. Guard against double-shutdown and set a hard timeout.

```typescript
import { MCPServer } from "mcp-use/server";

const server = new MCPServer({ name: "my-server", version: "1.0.0" });
await server.listen(3000);

let isShuttingDown = false;

async function shutdown(signal: string) {
  if (isShuttingDown) return;
  isShuttingDown = true;
  console.error(`[${signal}] Shutting down gracefully...`);

  const forceExit = setTimeout(() => {
    console.error("Forced exit after 10s timeout");
    process.exit(1);
  }, 10_000);

  try {
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
  redisUrl: process.env.REDIS_URL,
  apiKey: requireEnv("API_KEY"),
  allowedOrigins: process.env.ALLOWED_ORIGINS?.split(",").map(s => s.trim()),
};
```

The server also reads `PORT`, `HOST`, `MCP_URL`, `NODE_ENV`, `DEBUG`, and `CSP_URLS` automatically — see SDK configuration docs.

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
    await dbPool.query("SELECT 1");
  }
  return dbPool;
}
```

---

## 4. Structured Error Handling

Use `try/catch` in every tool handler. Return user-friendly errors via `error()` — never let raw exceptions reach the client.

```typescript
import { z } from "zod";
import { error, object } from "mcp-use/server";

class ToolError extends Error {
  constructor(message: string, public readonly code: string) {
    super(message);
  }
}

function handleToolError(err: unknown) {
  if (err instanceof ToolError) return error(`Error (${err.code}): ${err.message}`);
  console.error("[unexpected-error]", err);
  return error("An unexpected error occurred. Check server logs.");
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

## 5. Health Check Endpoints

Expose health via both an HTTP endpoint (for load balancers) and an MCP resource (for clients).

```typescript
import { MCPServer, object } from "mcp-use/server";

const server = new MCPServer({ name: "my-server", version: "1.0.0" });

// HTTP health check — load balancers, k8s probes
server.get("/health", (c) =>
  c.json({
    status: "healthy",
    service: config.name,
    version: config.version,
    uptime: Math.floor(process.uptime()),
    timestamp: new Date().toISOString(),
  })
);

// MCP resource — richer health data for MCP clients
server.resource(
  {
    uri: "health://status",
    name: "Server Health",
    description: "Current server health and uptime",
    mimeType: "application/json",
  },
  async () => {
    const mem = process.memoryUsage();
    return object({
      status: "ok",
      uptime: `${Math.floor(process.uptime() / 60)}m`,
      memory: { heapUsedMB: Math.round(mem.heapUsed / 1024 / 1024) },
      timestamp: new Date().toISOString(),
    });
  }
);
```

Register custom routes before calling `listen()`.

---

## 6. Logging with Built-in Logger

Use the built-in `Logger` (replaced Winston in v1.12.0). Works in Node.js and browser environments with zero dependencies. Since v1.21.5, `zod` is a peer dependency — declare it in your own `package.json`.

```typescript
import { Logger } from "mcp-use";  // Logger is from root package, NOT mcp-use/server

// Configure at startup
Logger.configure({
  level: "info",       // error | warn | info | http | verbose | debug | silly
  format: "minimal",   // "minimal" (default) or "detailed"
});

// Or use numeric debug levels
Logger.setDebug(0); // production (info)
Logger.setDebug(1); // debug mode
Logger.setDebug(2); // verbose (full JSON-RPC logging)

// Get a named logger instance for custom components
const logger = Logger.get("my-component");
logger.info("Component initialized");
logger.debug("Processing request", { userId: 123 });
logger.error("Operation failed", new Error("timeout"));
```

For tool-level logging visible to clients, use `ctx.log()`:

```typescript
server.tool(
  { name: "process-data", schema: z.object({ items: z.array(z.string()) }) },
  async ({ items }, ctx) => {
    await ctx.log("info", "Starting processing");
    for (const item of items) {
      await ctx.log("debug", `Processing: ${item}`, "processor");
    }
    await ctx.log("info", "Processing complete");
    return text("Done");
  }
);
```

---

## 7. Distributed Session & Stream Management

For multi-instance deployments behind a load balancer, use Redis for both session storage and SSE notification fan-out.

> **Note:** `RedisStreamManager` requires **two** separate Redis clients — one for commands and one dedicated to Pub/Sub (Redis Pub/Sub blocks the connection).

```typescript
import { MCPServer, RedisSessionStore, RedisStreamManager } from "mcp-use/server";
import { createClient } from "redis";

const redis = createClient({ url: process.env.REDIS_URL });
const pubSubRedis = redis.duplicate();

await redis.connect();
await pubSubRedis.connect();

const server = new MCPServer({
  name: "resilient-server",
  version: "1.0.0",
  sessionStore: new RedisSessionStore({
    client: redis,
    prefix: "mcp:session:",
    defaultTTL: 3600,              // seconds
  }),
  streamManager: new RedisStreamManager({
    client: redis,                 // session availability checks
    pubSubClient: pubSubRedis,     // dedicated Pub/Sub client (required)
    prefix: "mcp:stream:",
    heartbeatInterval: 10,         // seconds
  }),
});
```

**How notification fan-out works:**
1. Client connects to Server A → SSE stream created, Server A subscribes to `mcp:stream:{sessionId}`
2. Client's next request hits Server B (load balancer)
3. Server B publishes notification → Redis channel → Server A pushes to SSE → client receives it

For development, use `FileSystemSessionStore` (survives HMR reloads):

```typescript
import { FileSystemSessionStore } from "mcp-use/server";
const server = new MCPServer({
  name: "dev-server", version: "1.0.0",
  sessionStore: new FileSystemSessionStore({ path: ".mcp-use/sessions.json" }),
});
```

---

## 8. Stateless Mode for Serverless/Edge

For edge functions, serverless, or simple request/response flows, use the `stateless: true` constructor option or let the runtime be auto-detected.

```typescript
// Force stateless mode (no sessions, no SSE)
const server = new MCPServer({
  name: "edge-server",
  version: "1.0.0",
  stateless: true,
});

// Force stateful mode (always use sessions)
const server = new MCPServer({
  name: "stateful-server",
  version: "1.0.0",
  stateless: false,
});
```

| Mode | Sessions | SSE | Best for |
|---|---|---|---|
| **Stateful** (default) | Yes | Yes | Long-lived clients, notifications, sampling |
| **Stateless** | No | No | Edge functions, serverless, request/response |

**Auto-detection (when `stateless` is not set):**
- Deno / edge runtimes → always stateless
- Node.js → per-request from `Accept` header:
  - `Accept: application/json, text/event-stream` → stateful
  - `Accept: application/json` → stateless

For Supabase Edge Functions, call `server.listen()` — it auto-detects the Deno runtime and runs stateless. For Cloudflare Workers or Deno Deploy, export the handler directly:

```typescript
// register tools...
export default { fetch: server.getHandler() };
```

---

## 9. Security: allowedOrigins & Content Security Policy

### DNS Rebinding Protection

Always set `allowedOrigins` in production HTTP deployments. Without it, all `Host` header values are accepted.

```typescript
const server = new MCPServer({
  name: "prod-server",
  version: "1.0.0",
  allowedOrigins: [
    "https://myapp.com",
    "https://app.myapp.com",
  ],
  // Or from environment:
  // allowedOrigins: process.env.ALLOWED_ORIGINS?.split(","),
});
```

### Content Security Policy for Widgets

Use the `CSP_URLS` env var to whitelist domains for widget resources:

```bash
CSP_URLS=https://cdn.example.com,https://fonts.googleapis.com node server.js
```

### CORS for Production

Override the default permissive CORS (`origin: "*"`) in production:

```typescript
const server = new MCPServer({
  name: "prod-server",
  version: "1.0.0",
  cors: {
    origin: ["https://app.example.com"],
    allowMethods: ["GET", "POST", "DELETE", "OPTIONS"],
    allowHeaders: ["Content-Type", "Authorization", "mcp-protocol-version", "mcp-session-id"],
    exposeHeaders: ["mcp-session-id"],
  },
});
```

> **Warning:** The `cors` config **replaces** the default entirely — include `mcp-session-id` in both `allowHeaders` and `exposeHeaders`.

---

## 10. Modular Tool Organization

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
    └── cache.ts        # TTLCache
```

```typescript
// tools/users.ts
import { MCPServer } from "mcp-use/server";
import { z } from "zod";

export function registerUserTools(server: MCPServer) {
  server.tool(
    { name: "list-users", schema: z.object({ limit: z.number().default(10) }) },
    async ({ limit }) => { /* ... */ }
  );
}

// server.ts
import { registerUserTools } from "./tools/users.js";
registerUserTools(server);
```

---

## 11. Response Caching with TTL

Cache expensive responses. Use a bounded LRU cache in production to prevent unbounded memory growth.

```typescript
import { object } from "mcp-use/server";

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
}

const cache = new TTLCache<unknown>();

server.tool(
  { name: "cached-lookup", schema: z.object({ key: z.string() }) },
  async ({ key }) => {
    const cached = cache.get(key);
    if (cached) return object(cached);
    const fresh = await fetchExpensiveData(key);
    cache.set(key, fresh, 5 * 60 * 1000);
    return object(fresh);
  }
);
```

---

## 12. Rate Limiting

Protect expensive tools with a sliding-window counter. For multi-instance deployments, use Redis-backed rate limiting.

```typescript
import { error } from "mcp-use/server";

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

const limiter = new RateLimiter(60, 60_000);

server.tool(
  { name: "expensive-call", schema: z.object({ query: z.string() }) },
  async ({ query }, ctx) => {
    if (!limiter.check(ctx.client.info().name || "anon")) {
      return error("Rate limit exceeded. Try again in a minute.");
    }
    // proceed...
  }
);
```

---

## 13. Multi-Server Proxy (Gateway)

Aggregate multiple downstream MCP servers behind a single gateway using `MCPServer.proxy()` (added in v1.21.0). Tools from each upstream server are namespaced by key (e.g. `search_find-docs`).

```typescript
import { MCPServer, object } from "mcp-use/server";

const gateway = new MCPServer({ name: "gateway", version: "1.0.0" });

// Proxy HTTP-based servers
await gateway.proxy({
  search: { url: "https://search-mcp.internal/mcp" },
  analytics: { url: "https://analytics-mcp.internal/mcp" },
});

// Or proxy stdio-based servers alongside HTTP
await gateway.proxy({
  github:     { command: "npx", args: ["-y", "@modelcontextprotocol/server-github"] },
  filesystem: { command: "npx", args: ["-y", "@modelcontextprotocol/server-filesystem", "./data"] },
  db:         { url: "https://db-mcp.internal:3001/mcp" },
});

// Add gateway-level tools
gateway.tool(
  { name: "health", description: "Check all upstream servers" },
  async () => object({ servers: ["search", "analytics"], status: "healthy" })
);

await gateway.listen(4000);
```

---

## 14. Input Validation Patterns

Go beyond basic types with Zod refinements and transformations. Validate data *structure* and *business rules* before your handler runs.

### Semantic Validation
Use `.refine()` to enforce logical constraints that types cannot capture.

```typescript
import { z } from "zod";

const dateSchema = z.string().refine((val) => !isNaN(Date.parse(val)), {
  message: "Invalid date format",
});

server.tool(
  {
    name: "schedule-meeting",
    schema: z.object({
      start: dateSchema,
      end: dateSchema,
      attendees: z.array(z.string().email()).min(1),
    }).refine((data) => new Date(data.start) < new Date(data.end), {
      message: "End time must be after start time",
      path: ["end"], // Error attaches to 'end' field
    }),
  },
  async ({ start, end, attendees }) => {
    // Handler is guaranteed to have valid logical dates
    return text(`Scheduled for ${attendees.length} people`);
  }
);
```

### Transformations
Normalize input data automatically using `.transform()`.

```typescript
server.tool(
  {
    name: "search-products",
    schema: z.object({
      query: z.string().trim().toLowerCase(), // Auto-clean input
      tags: z.string().transform((val) => val.split(",").map((t) => t.trim())), // "a,b" -> ["a", "b"]
    }),
  },
  async ({ query, tags }) => {
    // query is already trimmed/lowercased
    // tags is already an array
    return text(`Searching for ${query} with tags: ${tags.join(", ")}`);
  }
);
```

---

## 15. Tool Timeouts & Cancellation

Prevent hung processes from blocking your server. Enforce strict execution time limits.

```typescript
import { error } from "mcp-use/server";

const TIMEOUT_MS = 5000;

server.tool(
  { name: "heavy-computation", schema: z.object({ input: z.string() }) },
  async ({ input }, ctx) => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS);

    try {
      // Pass signal to async operations
      const result = await longRunningTask(input, { signal: controller.signal });
      return text(result);
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        return error("Tool execution timed out");
      }
      throw err;
    } finally {
      clearTimeout(timeout);
    }
  }
);

// Helper wrapper for timeouts
function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  return Promise.race([
    promise,
    new Promise<T>((_, reject) =>
      setTimeout(() => reject(new Error("Operation timed out")), ms)
    ),
  ]);
}
```

---

## 16. Circuit Breakers

Fail fast when external dependencies (APIs, Databases) are struggling. Prevent cascading failures.

```typescript
import { error } from "mcp-use/server";

enum CircuitState { CLOSED, OPEN, HALF_OPEN }

class CircuitBreaker {
  private state = CircuitState.CLOSED;
  private failures = 0;
  private lastFailure = 0;

  constructor(
    private threshold = 5,
    private resetTimeout = 30000
  ) {}

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === CircuitState.OPEN) {
      if (Date.now() - this.lastFailure > this.resetTimeout) {
        this.state = CircuitState.HALF_OPEN;
      } else {
        throw new Error("Circuit is OPEN");
      }
    }

    try {
      const result = await fn();
      if (this.state === CircuitState.HALF_OPEN) {
        this.reset();
      }
      return result;
    } catch (err) {
      this.recordFailure();
      throw err;
    }
  }

  private recordFailure() {
    this.failures++;
    this.lastFailure = Date.now();
    if (this.failures >= this.threshold) {
      this.state = CircuitState.OPEN;
      console.error("[CircuitBreaker] Circuit opened due to failures");
    }
  }

  private reset() {
    this.state = CircuitState.CLOSED;
    this.failures = 0;
    console.info("[CircuitBreaker] Circuit closed (recovered)");
  }
}

const apiBreaker = new CircuitBreaker();

server.tool(
  { name: "external-api-call", schema: z.object({}) },
  async () => {
    try {
      const data = await apiBreaker.execute(() => fetch("https://unreliable-api.com"));
      return text(await data.text());
    } catch (err) {
      return error("Service temporarily unavailable");
    }
  }
);
```

---

## 17. Memory Management & Streaming

Handle large datasets without blowing up the heap. Use Node.js Streams or async generators.

```typescript
import { Readable } from "stream";
import { pipeline } from "stream/promises";
import { createWriteStream } from "fs";

server.tool(
  { name: "process-large-file", schema: z.object({ url: z.string().url() }) },
  async ({ url }, ctx) => {
    // 1. Stream download instead of buffering
    const response = await fetch(url);
    if (!response.body) return error("No body");

    const tempFile = `/tmp/${Date.now()}.dat`;
    
    // 2. Pipe to disk to keep memory low
    await pipeline(
      Readable.fromWeb(response.body as any),
      createWriteStream(tempFile)
    );

    // 3. Process line-by-line using readline (not shown for brevity)
    
    return text(`Processed file to ${tempFile}`);
  }
);
```

For returning large data to the client, prefer pagination over massive payloads. MCP tool responses are JSON-RPC and must fit in memory.

---

## 18. Request Tracing & Correlation IDs

Track requests across distributed systems. Attach a request ID to logs and downstream calls.

```typescript
import { AsyncLocalStorage } from "async_hooks";

const traceContext = new AsyncLocalStorage<{ requestId: string }>();

// Middleware to set context (conceptual, depends on transport)
function wrapWithContext(fn: Function) {
  return (...args: any[]) => {
    const requestId = `req_${crypto.randomUUID().slice(0, 8)}`;
    return traceContext.run({ requestId }, () => fn(...args));
  };
}

function getLogger() {
  const store = traceContext.getStore();
  return {
    info: (msg: string) => console.log(`[${store?.requestId || "sys"}] ${msg}`),
    error: (msg: string) => console.error(`[${store?.requestId || "sys"}] ${msg}`),
  };
}

server.tool(
  { name: "trace-demo", schema: z.object({}) },
  async () => {
    const logger = getLogger();
    logger.info("Handling request");
    
    // Pass ID to downstream API
    const headers = { "X-Request-ID": traceContext.getStore()?.requestId || "" };
    // await fetch(..., { headers })
    
    return text("Check logs for Request ID");
  }
);
```

---

## 19. Background Jobs

Offload long-running tasks to a background queue. Tools should return "Accepted" immediately.

```typescript
import { text } from "mcp-use/server";

const queue: Array<{ id: string; data: any }> = [];

server.tool(
  { name: "generate-report", schema: z.object({ type: z.string() }) },
  async ({ type }) => {
    const jobId = `job_${Date.now()}`;
    
    // Push to queue (or Redis/BullMQ in production)
    queue.push({ id: jobId, data: type });
    
    // Start processing asynchronously (fire and forget)
    processQueue().catch(console.error);

    return text(`Report generation started. Job ID: ${jobId}`);
  }
);

async function processQueue() {
  const job = queue.shift();
  if (!job) return;
  
  console.log(`Processing ${job.id}...`);
  await new Promise(r => setTimeout(r, 2000)); // Simulate work
  console.log(`Job ${job.id} complete`);
}
```

---

## 20. Feature Flags

Dynamically enable/disable tools without redeploying.

```typescript
const flags = {
  EXPERIMENTAL_TOOLS: process.env.ENABLE_EXPERIMENTAL === "true",
  BETA_Search: false,
};

// Conditional registration
if (flags.EXPERIMENTAL_TOOLS) {
  server.tool(
    { name: "experimental-feature", schema: z.object({}) },
    async () => text("This is experimental!")
  );
}

// Runtime check
server.tool(
  { name: "search", schema: z.object({ q: z.string() }) },
  async ({ q }) => {
    if (flags.BETA_Search) {
      return text("Using new beta search engine...");
    }
    return text("Using standard search...");
  }
);
```