# Production Patterns for MCP Clients

Complete reference for building reliable, production-grade MCP client applications — graceful shutdown, connection management, retry logic, multi-server orchestration, and observability.

---

> **Note:** All examples use `mcp-use` for Node.js imports, `mcp-use/browser` for browser, and `mcp-use/react` for React. Use `OnNotificationCallback` (not `NotificationHandler`) for typed notification handlers. Set `clientInfo` at the top-level config object (alongside `mcpServers`) to identify your client to all servers, or per-server in the server config object to override per-connection. Latest version: **v1.21.5**.

---

## 1. Graceful Shutdown

Clean up sessions and connections on process termination. Guard against double-shutdown with a flag and set a hard timeout.

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    api: { url: "https://api.example.com/mcp" },
    search: { url: "https://search.example.com/mcp" },
  },
});
await client.createAllSessions();

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
    await client.closeAllSessions();
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

## 2. Connection Pooling

Reuse a single `MCPClient` instance across your application. Never create a new client per request.

```typescript
import { MCPClient } from "mcp-use";

let sharedClient: MCPClient | null = null;

async function getClient(): Promise<MCPClient> {
  if (!sharedClient) {
    sharedClient = new MCPClient({
      mcpServers: {
        api: {
          url: process.env.MCP_API_URL!,
          headers: { Authorization: `Bearer ${process.env.MCP_API_KEY}` },
        },
      },
    });
    await sharedClient.createAllSessions();
  }
  return sharedClient;
}

// In your request handler (Express, Fastify, etc.)
async function handleRequest(req: Request) {
  const client = await getClient();
  const session = client.getSession("api");
  const result = await session.callTool("process-data", { input: req.body });
  return result;
}
```

| Approach | When to Use |
|---|---|
| **Singleton client** | Single-process servers, CLI tools, scripts |
| **Per-worker client** | Cluster mode, worker threads |
| **Client factory** | Multi-tenant apps with different credentials |

---

## 3. Retry with Exponential Backoff

Handle transient failures with exponential backoff. Distinguish between retryable and permanent errors.

```typescript
import { MCPClient } from "mcp-use";

interface RetryOptions {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
}

const DEFAULT_RETRY: RetryOptions = {
  maxRetries: 3,
  baseDelayMs: 1000,
  maxDelayMs: 30_000,
};

function isRetryableError(err: unknown): boolean {
  if (err instanceof Error) {
    const msg = err.message.toLowerCase();
    return (
      msg.includes("econnrefused") ||
      msg.includes("econnreset") ||
      msg.includes("etimedout") ||
      msg.includes("socket hang up") ||
      msg.includes("network") ||
      msg.includes("503") ||
      msg.includes("429")
    );
  }
  return false;
}

async function callToolWithRetry(
  session: Awaited<ReturnType<MCPClient["createSession"]>>,
  toolName: string,
  args: Record<string, unknown>,
  options: RetryOptions = DEFAULT_RETRY
) {
  let lastError: unknown;

  for (let attempt = 0; attempt <= options.maxRetries; attempt++) {
    try {
      const result = await session.callTool(toolName, args);
      if (result.isError) {
        throw new Error(`Tool error: ${JSON.stringify(result.content)}`);
      }
      return result;
    } catch (err) {
      lastError = err;
      if (!isRetryableError(err) || attempt === options.maxRetries) {
        throw err;
      }
      const delay = Math.min(
        options.baseDelayMs * Math.pow(2, attempt) + Math.random() * 1000,
        options.maxDelayMs
      );
      console.warn(
        `[retry] Attempt ${attempt + 1}/${options.maxRetries} failed, retrying in ${Math.round(delay)}ms`
      );
      await new Promise((r) => setTimeout(r, delay));
    }
  }
  throw lastError;
}
```

---

## 4. Auto-Reconnection

Configure auto-reconnect for resilient long-lived connections. The client handles reconnection transparently.

### Node.js — HttpConnector with roots

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    api: {
      url: "https://api.example.com/mcp",
    },
  },
});

// The SDK's StreamableHTTPClientTransport supports reconnection natively.
// Use HttpConnector for low-level access; supply initial roots via options:
import { HttpConnector, MCPSession } from "mcp-use";

const connector = new HttpConnector("https://api.example.com/mcp", {
  roots: [{ uri: "file:///workspace", name: "Workspace" }],
});

const session = new MCPSession(connector);
await session.connect();
await session.initialize();

// Update roots later — sends notifications/roots/list_changed to the server:
await session.setRoots([
  { uri: "file:///workspace", name: "Workspace" },
  { uri: "file:///docs", name: "Docs" },
]);
```

### React — useMcp with autoReconnect

```typescript
import { useMcp } from "mcp-use/react";

function Dashboard() {
  const mcp = useMcp({
    url: "https://api.example.com/mcp",
    autoReconnect: {
      enabled: true,
      initialDelay: 3000,
      healthCheckInterval: 10_000,
      healthCheckTimeout: 30_000,
    },
    reconnectionOptions: {
      initialReconnectionDelay: 2000,
      maxReconnectionDelay: 60_000,
      reconnectionDelayGrowFactor: 2,
      maxRetries: 5,
    },
  });

  if (mcp.state !== "ready") {
    return <div>Connection state: {mcp.state}...</div>;
  }

  return <div>{mcp.tools.length} tools available</div>;
}
```

| Config | Layer | Purpose |
|---|---|---|
| `autoReconnect` | Application | Health checks, reconnect delay, transparent recovery |
| `reconnectionOptions` | SDK transport | Low-level transport reconnection with backoff |

---

## 5. 404 Session Recovery

The client handles expired sessions automatically — no code needed. When an HTTP server returns 404 (session expired or server restarted), the client re-initializes transparently.

```
[StreamableHttp] Session not found (404), re-initializing per MCP spec...
[StreamableHttp] Re-initialization successful, retrying request
```

### What to do: log it for observability

```typescript
import { MCPClient, type OnNotificationCallback } from "mcp-use";

const onNotification: OnNotificationCallback = (notification) => {
  // Log all notifications including recovery events
  console.log(`[mcp] ${notification.method}`, notification.params);
};

const client = new MCPClient(
  {
    mcpServers: {
      api: { url: "https://api.example.com/mcp" },
    },
  },
  { onNotification }
);
```

Built-in recovery covers:
- Server restarts
- Session expiration (idle timeout)
- Load balancer failover to a different server instance

---

## 6. Timeout Management

Configure timeouts at multiple levels: per-call, maximum total, progress-based reset, and programmatic cancellation.

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    api: { url: "https://api.example.com/mcp" },
  },
});
const session = await client.createSession("api");

// Basic timeout
const quick = await session.callTool("fast-lookup", { id: "123" }, {
  timeout: 5000,
});

// Long-running tool with progress resets
const report = await session.callTool("generate-report", { year: 2024 }, {
  timeout: 60_000,
  maxTotalTimeout: 300_000,
  resetTimeoutOnProgress: true,
});

// Programmatic cancellation with AbortSignal
const controller = new AbortController();
setTimeout(() => controller.abort(), 120_000); // hard 2-min cap

const analysis = await session.callTool("analyze-dataset", { dataset: "sales" }, {
  timeout: 60_000,
  resetTimeoutOnProgress: true,
  signal: controller.signal,
});
```

| Option | Purpose | Default |
|---|---|---|
| `timeout` | Per-request timeout in ms | `60000` |
| `maxTotalTimeout` | Hard cap even with progress resets | None |
| `resetTimeoutOnProgress` | Reset timer on progress notifications | `false` |
| `signal` | AbortSignal for programmatic cancellation | None |

### User-triggered cancellation in React

```typescript
import { useMcp } from "mcp-use/react";
import { useRef } from "react";

function AnalysisTool() {
  const mcp = useMcp({ url: "https://api.example.com/mcp" });
  const controllerRef = useRef<AbortController | null>(null);

  const runAnalysis = async () => {
    controllerRef.current = new AbortController();
    try {
      const result = await mcp.callTool("analyze", { query: "revenue" }, {
        timeout: 120_000,
        signal: controllerRef.current.signal,
      });
      console.log("Result:", result);
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") {
        console.log("Cancelled by user");
      }
    }
  };

  const cancel = () => controllerRef.current?.abort();

  return (
    <div>
      <button onClick={runAnalysis}>Run</button>
      <button onClick={cancel}>Cancel</button>
    </div>
  );
}
```

---

## 7. Multi-Server Orchestration

Connect to multiple MCP servers with independent sessions. Run parallel tool calls across servers and implement fallback strategies.

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    search: { url: "https://search.example.com/mcp" },
    analytics: { url: "https://analytics.example.com/mcp" },
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/data"],
    },
  },
});
await client.createAllSessions();

// Parallel tool calls across servers
const [searchResults, analyticsData] = await Promise.all([
  client.getSession("search").callTool("find-documents", { query: "revenue" }),
  client.getSession("analytics").callTool("get-metrics", { period: "Q4" }),
]);

// Fallback pattern: try primary, fall back to secondary
async function searchWithFallback(query: string) {
  try {
    const result = await client.getSession("search").callTool("search", { query });
    if (!result.isError) return result;
  } catch {
    console.warn("[fallback] Primary search failed, trying analytics");
  }
  return client.getSession("analytics").callTool("search-records", { query });
}

await client.closeAllSessions();
```

### React multi-server with McpClientProvider

```typescript
import { McpClientProvider, useMcpClient, useMcpServer } from "mcp-use/react";

function App() {
  return (
    <McpClientProvider
      mcpServers={{
        search: { url: "https://search.example.com/mcp", name: "Search" },
        analytics: { url: "https://analytics.example.com/mcp", name: "Analytics" },
      }}
      defaultAutoProxyFallback={true}
    >
      <Dashboard />
    </McpClientProvider>
  );
}

function Dashboard() {
  const search = useMcpServer("search");
  const analytics = useMcpServer("analytics");

  if (search.state !== "ready" || analytics.state !== "ready") {
    return <div>Connecting to servers...</div>;
  }

  return (
    <div>
      <p>Search: {search.tools.length} tools</p>
      <p>Analytics: {analytics.tools.length} tools</p>
    </div>
  );
}
```

---

## 8. Error Boundary Patterns

Categorize errors as transient (retry) or permanent (fail fast). Handle `isError` in tool results.

```typescript
import { MCPClient } from "mcp-use";

type ErrorCategory = "transient" | "permanent" | "unknown";

function categorizeError(err: unknown): ErrorCategory {
  if (err instanceof Error) {
    const msg = err.message.toLowerCase();
    // Transient — retry
    if (msg.includes("timeout") || msg.includes("econnreset") ||
        msg.includes("429") || msg.includes("503") || msg.includes("network")) {
      return "transient";
    }
    // Permanent — fail fast
    if (msg.includes("401") || msg.includes("403") || msg.includes("404") ||
        msg.includes("invalid") || msg.includes("schema")) {
      return "permanent";
    }
  }
  return "unknown";
}

async function resilientToolCall(
  session: Awaited<ReturnType<MCPClient["createSession"]>>,
  toolName: string,
  args: Record<string, unknown>
) {
  const MAX_RETRIES = 3;
  let lastError: unknown;

  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    try {
      const result = await session.callTool(toolName, args, { timeout: 30_000 });

      // Always check isError in the result
      if (result.isError) {
        const errorMsg = JSON.stringify(result.content);
        console.error(`[tool-error] ${toolName}: ${errorMsg}`);
        // Tool-level errors are permanent — the tool ran but reported failure
        return { success: false, error: errorMsg, result };
      }

      return { success: true, result };
    } catch (err) {
      lastError = err;
      const category = categorizeError(err);

      if (category === "permanent") {
        console.error(`[permanent-error] ${toolName}: ${err}`);
        return { success: false, error: String(err) };
      }

      if (category === "transient" && attempt < MAX_RETRIES) {
        const delay = Math.pow(2, attempt) * 1000;
        console.warn(`[retry] ${toolName} attempt ${attempt + 1}, waiting ${delay}ms`);
        await new Promise((r) => setTimeout(r, delay));
        continue;
      }

      break;
    }
  }

  console.error(`[exhausted] ${toolName} failed after ${MAX_RETRIES + 1} attempts`);
  return { success: false, error: String(lastError) };
}
```

---

## 9. Environment-Based Configuration

Use environment variables for URLs, tokens, and secrets. Load config files for complex setups. Validate at startup.

```typescript
import { MCPClient } from "mcp-use";

// Validate required environment variables at startup
function requireEnv(key: string): string {
  const val = process.env[key];
  if (!val) throw new Error(`Missing required env var: ${key}`);
  return val;
}

const client = new MCPClient({
  clientInfo: {
    name: process.env.SERVICE_NAME || "my-service",
    version: process.env.SERVICE_VERSION || "1.0.0",
  },
  mcpServers: {
    api: {
      url: requireEnv("MCP_API_URL"),
      headers: {
        Authorization: `Bearer ${requireEnv("MCP_API_KEY")}`,
      },
    },
    search: {
      url: process.env.MCP_SEARCH_URL || "http://localhost:3001/mcp",
    },
  },
});
```

### Config file with environment variable interpolation

```json
{
  "mcpServers": {
    "github": {
      "command": "mcp-server-github",
      "env": { "GITHUB_TOKEN": "${GITHUB_TOKEN}" }
    },
    "api": {
      "url": "${MCP_API_URL}",
      "headers": { "Authorization": "Bearer ${MCP_API_KEY}" }
    }
  }
}
```

```typescript
// Load from config file — env vars are interpolated automatically
import { MCPClient, loadConfigFile } from "mcp-use";

const config = await loadConfigFile("./mcp-config.json");
const client = new MCPClient(config);
```

### Multiple environments

```typescript
const ENV = process.env.NODE_ENV || "development";

const configs: Record<string, Record<string, { url: string }>> = {
  development: {
    api: { url: "http://localhost:3000/mcp" },
  },
  staging: {
    api: { url: "https://staging-api.example.com/mcp" },
  },
  production: {
    api: { url: "https://api.example.com/mcp" },
  },
};

const client = new MCPClient({ mcpServers: configs[ENV] });
```

---

## 10. Logging and Observability

Monitor notifications, forward server logs, track errors, and measure tool call performance.

### Server log forwarding via loggingCallback

```typescript
import { MCPClient, types } from "mcp-use";

const client = new MCPClient(
  { mcpServers: { api: { url: "https://api.example.com/mcp" } } },
  {
    loggingCallback: (logParams: types.LoggingMessageNotificationParams) => {
      // level: "debug" | "info" | "warning" | "error"
      // message: string
      console.log(`[server:${logParams.level}] ${logParams.message}`);
    },
  }
);
```

### Notification handler for protocol events

```typescript
import { MCPClient, type OnNotificationCallback, type Notification } from "mcp-use";

// Structured notification handler
const onNotification: OnNotificationCallback = (notification: Notification) => {
  const timestamp = new Date().toISOString();

  switch (notification.method) {
    case "notifications/tools/list_changed":
      console.log(`[${timestamp}] [tools-changed] Tools list updated`);
      break;
    case "notifications/resources/list_changed":
      console.log(`[${timestamp}] [resources-changed] Resources list updated`);
      break;
    case "notifications/prompts/list_changed":
      console.log(`[${timestamp}] [prompts-changed] Prompts list updated`);
      break;
    default:
      console.log(`[${timestamp}] [notification] ${notification.method}`, notification.params);
  }
};

const client = new MCPClient(
  {
    mcpServers: {
      api: { url: "https://api.example.com/mcp" },
    },
  },
  { onNotification }
);
```

### Tool call metrics wrapper

```typescript
async function trackedCallTool(
  session: Awaited<ReturnType<MCPClient["createSession"]>>,
  toolName: string,
  args: Record<string, unknown>
) {
  const start = performance.now();
  try {
    const result = await session.callTool(toolName, args);
    const durationMs = Math.round(performance.now() - start);
    console.log(
      JSON.stringify({
        event: "tool_call",
        tool: toolName,
        success: !result.isError,
        durationMs,
      })
    );
    return result;
  } catch (err) {
    const durationMs = Math.round(performance.now() - start);
    console.error(
      JSON.stringify({
        event: "tool_call_error",
        tool: toolName,
        durationMs,
        error: err instanceof Error ? err.message : String(err),
      })
    );
    throw err;
  }
}
```

### Session-level notification listener

```typescript
const session = await client.createSession("api");

session.on("notification", async (notification) => {
  switch (notification.method) {
    case "notifications/tools/list_changed": {
      const tools = await session.listTools();
      console.log(`[auto-refresh] ${tools.length} tools now available`);
      break;
    }
    case "notifications/resources/list_changed": {
      // listResources() and listAllResources() are both documented;
      // listResources() is the primary public API
      const resources = await session.listResources();
      console.log(`[auto-refresh] ${resources.length} resources now available`);
      break;
    }
    case "notifications/prompts/list_changed": {
      const prompts = await session.listPrompts();
      console.log(`[auto-refresh] ${prompts.length} prompts now available`);
      break;
    }
  }
});
```

---

## 11. Resource Caching

Cache `readResource` results locally. Invalidate on `notifications/resources/list_changed`.

```typescript
import { MCPClient } from "mcp-use";

class ResourceCache {
  private cache = new Map<string, { data: unknown; fetchedAt: number }>();
  private ttlMs: number;

  constructor(ttlMs = 60_000) {
    this.ttlMs = ttlMs;
  }

  get(uri: string): unknown | undefined {
    const entry = this.cache.get(uri);
    if (!entry) return undefined;
    if (Date.now() - entry.fetchedAt > this.ttlMs) {
      this.cache.delete(uri);
      return undefined;
    }
    return entry.data;
  }

  set(uri: string, data: unknown): void {
    this.cache.set(uri, { data, fetchedAt: Date.now() });
  }

  invalidateAll(): void {
    this.cache.clear();
  }

  invalidate(uri: string): void {
    this.cache.delete(uri);
  }
}

const resourceCache = new ResourceCache(5 * 60_000);

const client = new MCPClient({
  mcpServers: {
    api: { url: "https://api.example.com/mcp" },
  },
});

const session = await client.createSession("api");

// Invalidate cache on server notification
session.on("notification", async (notification) => {
  if (notification.method === "notifications/resources/list_changed") {
    resourceCache.invalidateAll();
    console.log("[cache] Resource cache invalidated");
  }
});

// Cached resource reader
async function readResourceCached(uri: string): Promise<unknown> {
  const cached = resourceCache.get(uri);
  if (cached) return cached;

  const result = await session.readResource(uri);
  resourceCache.set(uri, result);
  return result;
}
```

---

## 12. Session Lifecycle Management

Choose between eager `createAllSessions()` and lazy `createSession()`. Always clean up.

### Eager — all sessions at startup

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    api: { url: "https://api.example.com/mcp" },
    search: { url: "https://search.example.com/mcp" },
    fs: { command: "npx", args: ["-y", "@modelcontextprotocol/server-filesystem", "/data"] },
  },
});

// Create all sessions upfront — fails fast if any server is unreachable
await client.createAllSessions();

// Use sessions immediately
const tools = await client.getSession("api").listTools();
```

### Lazy — on-demand session creation

```typescript
const client = new MCPClient({
  mcpServers: {
    api: { url: "https://api.example.com/mcp" },
    search: { url: "https://search.example.com/mcp" },
  },
});

// Only create when needed
async function searchDocuments(query: string) {
  const session = await client.createSession("search");
  return session.callTool("search", { query });
}
```

### Cleanup patterns

```typescript
// Application shutdown — close everything
await client.closeAllSessions();

// Using try/finally for scripts
const client = new MCPClient({ mcpServers: { api: { url: "http://localhost:3000/mcp" } } });
try {
  await client.createAllSessions();
  const session = client.getSession("api");
  const result = await session.callTool("process", { data: "hello" });
  console.log(result);
} finally {
  await client.closeAllSessions();
}
```

| Pattern | When to Use |
|---|---|
| `createAllSessions()` | Known servers, fail-fast at startup, short-lived scripts |
| `createSession(name)` | On-demand, optional servers, long-lived apps |
| `closeAllSessions()` | Always call on shutdown |

---

## 13. React Production Patterns

### Persistence with StorageProvider

```typescript
import { McpClientProvider, LocalStorageProvider } from "mcp-use/react";

function App() {
  return (
    <McpClientProvider
      storageProvider={new LocalStorageProvider("my-app-mcp-servers")}
      defaultAutoProxyFallback={true}
    >
      <MainApp />
    </McpClientProvider>
  );
}
```

### Handle all connection states

```typescript
import { useMcp } from "mcp-use/react";

function McpToolPanel() {
  const mcp = useMcp({
    url: "https://api.example.com/mcp",
    callbackUrl: window.location.origin + "/oauth/callback",
    autoReconnect: true,
  });

  switch (mcp.state) {
    case "discovering":
      return <div className="spinner">Connecting...</div>;
    case "authenticating":
      return <div className="spinner">Authenticating...</div>;
    case "pending_auth":
      return (
        <div>
          <p>Authorization required</p>
          <button onClick={mcp.authenticate}>Authorize</button>
        </div>
      );
    case "failed":
      return (
        <div>
          <p>Connection failed: {mcp.error}</p>
          <button onClick={mcp.retry}>Retry</button>
        </div>
      );
    case "ready":
      return <ToolList tools={mcp.tools} callTool={mcp.callTool} />;
    default:
      return null;
  }
}
```

### Proxy fallback for CORS issues

```typescript
import { McpClientProvider, useMcpClient } from "mcp-use/react";

function App() {
  return (
    <McpClientProvider
      defaultAutoProxyFallback={{
        enabled: true,
        proxyAddress: "https://inspector.mcp-use.com/inspector/api/proxy",
      }}
    >
      <ServerManager />
    </McpClientProvider>
  );
}

function ServerManager() {
  const { addServer } = useMcpClient();

  useEffect(() => {
    addServer("api", {
      url: "https://api.example.com/mcp",
      name: "API Server",
      autoProxyFallback: true,
    });
  }, [addServer]);

  return <div>...</div>;
}
```

### Dynamic server management

```typescript
import { useMcpClient, useMcpServer } from "mcp-use/react";

function ServerDashboard() {
  const { servers, addServer, removeServer } = useMcpClient();

  const handleAddServer = (url: string, name: string) => {
    addServer(name, {
      url,
      name,
      autoReconnect: true,
      autoProxyFallback: true,
    });
  };

  return (
    <div>
      <h2>MCP Servers ({servers.length})</h2>
      {servers.map((server) => (
        <div key={server.id}>
          <span>{server.name}: {server.state}</span>
          {server.state === "ready" && <span> — {server.tools.length} tools</span>}
          <button onClick={() => removeServer(server.id)}>Remove</button>
        </div>
      ))}
    </div>
  );
}
```

---

## 14. Code Mode Security

Choose the right executor based on trust level. Set timeout and memory limits.

### VM executor — trusted code only

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient(
  {
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", "./data"],
      },
    },
  },
  {
    codeMode: {
      enabled: true,
      executor: "vm",
      executorOptions: {
        timeoutMs: 30_000,
        memoryLimitMb: 256,
      },
    },
  }
);
```

### E2B executor — untrusted code, full isolation

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient(
  {
    mcpServers: {
      api: { url: "https://api.example.com/mcp" },
    },
  },
  {
    codeMode: {
      enabled: true,
      executor: "e2b",
      executorOptions: {
        apiKey: process.env.E2B_API_KEY!,
        timeoutMs: 300_000,
      },
    },
  }
);
```

| Executor | Isolation | Latency | Cost | Use Case |
|---|---|---|---|---|
| **VM** | Process-level (Node.js `vm`) | Zero | Free | Trusted code, internal tools, development |
| **E2B** | Full Linux sandbox | Network RTT | Per-execution | Untrusted code, user-submitted scripts |
| **Custom** | You control | Depends | Depends | Docker, Firecracker, WASM |

### Custom executor

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient(
  { mcpServers: { api: { url: "https://api.example.com/mcp" } } },
  {
    codeMode: {
      enabled: true,
      executor: async (code: string, timeout?: number) => {
        const result = await myDockerSandbox.run(code, { timeout });
        return {
          result: result.output,
          logs: result.stdout,
          error: result.error ?? null,
          execution_time: result.durationSec,
        };
      },
    },
  }
);
```

---

## Quick Reference: Pattern Selection Guide

| Scenario | Patterns to Apply |
|---|---|
| **CLI script** | Session lifecycle (eager), try/finally cleanup, retry |
| **API server** | Connection pooling, graceful shutdown, error boundaries, metrics |
| **React SPA** | McpClientProvider, state handling, proxy fallback, persistence |
| **Multi-server agent** | Multi-server orchestration, parallel calls, fallback |
| **Long-running tools** | Timeout management, progress reset, AbortSignal |
| **Untrusted code exec** | E2B executor, timeout limits, memory limits |
| **High availability** | Auto-reconnect, 404 recovery, retry with backoff |
