# MCP Client Anti-Patterns

Avoid these mistakes when building MCP client applications with **mcp-use** — connection management, tool calling, configuration, sessions, React, and security.

---

## 1. Connection Anti-Patterns

### Creating New MCPClient Per Request

```typescript
// ❌ BAD — new client + session for every request (leaks connections, slow)
async function handleRequest(query: string) {
  const client = new MCPClient({
    mcpServers: { api: { url: "https://api.example.com/mcp" } },
  });
  await client.createAllSessions();
  const result = await client.getSession("api").callTool("search", { query });
  await client.closeAllSessions();
  return result;
}

// ✅ GOOD — reuse a single client across requests
import { MCPClient } from "mcp-use";

let client: MCPClient | null = null;

async function getClient(): Promise<MCPClient> {
  if (!client) {
    client = new MCPClient({
      mcpServers: { api: { url: "https://api.example.com/mcp" } },
    });
    await client.createAllSessions();
  }
  return client;
}

async function handleRequest(query: string) {
  const c = await getClient();
  return c.getSession("api").callTool("search", { query });
}
```

### Not Calling closeAllSessions on Cleanup

```typescript
// ❌ BAD — sessions leak, server resources not freed
const client = new MCPClient({ mcpServers: { api: { url: "http://localhost:3000/mcp" } } });
await client.createAllSessions();
const result = await client.getSession("api").callTool("get-data", {});
// process exits without closing sessions

// ✅ GOOD — always close sessions with try/finally
const client = new MCPClient({ mcpServers: { api: { url: "http://localhost:3000/mcp" } } });
try {
  await client.createAllSessions();
  const result = await client.getSession("api").callTool("get-data", {});
  console.log(result);
} finally {
  await client.closeAllSessions();
}

// ✅ GOOD — register shutdown handlers for long-lived processes
process.on("SIGTERM", async () => {
  await client.closeAllSessions();
  process.exit(0);
});
process.on("SIGINT", async () => {
  await client.closeAllSessions();
  process.exit(0);
});
```

### Ignoring Connection State Before Calling Tools

```typescript
// ❌ BAD — calling tool without verifying session is initialized
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: { api: { url: "https://api.example.com/mcp" } },
});
// Forgot to call createSession or createAllSessions
const session = client.getSession("api");
const result = await session.callTool("search", { query: "test" }); // throws

// ✅ GOOD — ensure session is created before use
const client = new MCPClient({
  mcpServers: { api: { url: "https://api.example.com/mcp" } },
});
await client.createAllSessions(); // or: await client.createSession("api");
const session = client.getSession("api");
const result = await session.callTool("search", { query: "test" });
```

### Hardcoding Server URLs

```typescript
// ❌ BAD — hardcoded URLs and tokens in source code
const client = new MCPClient({
  mcpServers: {
    api: {
      url: "https://prod-api.mycompany.com/mcp",
      headers: { Authorization: "Bearer sk-abc123secret" },
    },
  },
});

// ✅ GOOD — use environment variables
const client = new MCPClient({
  mcpServers: {
    api: {
      url: process.env.MCP_API_URL!,
      headers: { Authorization: `Bearer ${process.env.MCP_API_KEY}` },
    },
  },
});

// ✅ GOOD — or use config file with env var interpolation
import { MCPClient, loadConfigFile } from "mcp-use";
const config = loadConfigFile("./mcp-config.json");
const client = new MCPClient(config);
// Config file uses ${MCP_API_KEY} syntax for secrets
```

### Not Configuring Reconnection for Long-Lived Connections

```typescript
// ❌ BAD — no reconnection config, connection drops silently
import { useMcp } from "mcp-use/react";

const mcp = useMcp({
  url: "https://api.example.com/mcp",
});

// ✅ GOOD — configure auto-reconnect with health checks
const mcp = useMcp({
  url: "https://api.example.com/mcp",
  autoReconnect: {
    enabled: true,
    initialDelay: 3000,
    healthCheckInterval: 10_000,
  },
});
```

---

## 2. Tool Calling Anti-Patterns

### Not Handling isError in CallToolResult

```typescript
// ❌ BAD — assumes every tool call succeeds
const result = await session.callTool("process-data", { input: "test" });
console.log("Data:", result.content); // might be an error message!

// ✅ GOOD — always check isError
const result = await session.callTool("process-data", { input: "test" });
if (result.isError) {
  console.error("Tool failed:", result.content);
  // Handle error: retry, fallback, or report
} else {
  console.log("Data:", result.content);
}
```

### No Timeout Configuration for Long-Running Tools

```typescript
// ❌ BAD — uses default 60s timeout for a tool that may take 5+ minutes
const result = await session.callTool("generate-report", {
  dataset: "all-transactions",
  year: 2024,
});

// ✅ GOOD — set appropriate timeout with progress reset
const result = await session.callTool("generate-report", {
  dataset: "all-transactions",
  year: 2024,
}, {
  timeout: 60_000,
  maxTotalTimeout: 600_000,
  resetTimeoutOnProgress: true,
});
```

### Ignoring AbortSignal for Cancellation

```typescript
// ❌ BAD — no way to cancel a long-running tool call
async function runAnalysis() {
  const result = await session.callTool("analyze", { query: "revenue" });
  return result;
}
// User clicks "cancel" → nothing happens, tool keeps running

// ✅ GOOD — use AbortController for cancellation
const controller = new AbortController();

async function runAnalysis() {
  try {
    const result = await session.callTool("analyze", { query: "revenue" }, {
      timeout: 120_000,
      signal: controller.signal,
    });
    return result;
  } catch (err) {
    if (err instanceof Error && err.name === "AbortError") {
      console.log("Analysis cancelled by user");
      return null;
    }
    throw err;
  }
}

function cancelAnalysis() {
  controller.abort();
}
```

### Fire-and-Forget Tool Calls Without Error Handling

```typescript
// ❌ BAD — no error handling, no await
session.callTool("send-notification", { message: "Hello" });
// Errors are silently swallowed

// ❌ BAD — catches error but does nothing useful
try {
  await session.callTool("send-notification", { message: "Hello" });
} catch {
  // silently ignored
}

// ✅ GOOD — handle errors explicitly
try {
  const result = await session.callTool("send-notification", { message: "Hello" });
  if (result.isError) {
    console.error("Notification failed:", result.content);
    await retryOrQueue("send-notification", { message: "Hello" });
  }
} catch (err) {
  console.error("Tool call failed:", err);
  // Retry, queue for later, or alert
}
```

### Calling Non-Existent Tools Without Discovery

```typescript
// ❌ BAD — calling a tool by guessed name
const result = await session.callTool("searchDocuments", { query: "test" });
// Tool name is actually "search-documents" → server returns error

// ✅ GOOD — discover tools first, then call by exact name
const tools = await session.listTools();
const searchTool = tools.find((t) => t.name.includes("search"));
if (searchTool) {
  const result = await session.callTool(searchTool.name, { query: "test" });
}
```

---

## 3. Configuration Anti-Patterns

### Hardcoding Secrets in Source Code

```typescript
// ❌ BAD — secrets committed to git
const client = new MCPClient({
  mcpServers: {
    github: {
      command: "mcp-server-github",
      env: { GITHUB_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxx" },
    },
  },
});

// ✅ GOOD — reference environment variables
const client = new MCPClient({
  mcpServers: {
    github: {
      command: "mcp-server-github",
      env: { GITHUB_TOKEN: "${GITHUB_TOKEN}" },
    },
  },
});
```

### Not Using Per-Server Callbacks When Servers Need Different LLMs

```typescript
// ❌ BAD — single sampling callback for all servers (uses same model for everything)
import { MCPClient, type OnSamplingCallback } from "mcp-use";

const onSampling: OnSamplingCallback = async (params) => {
  return callClaude(params); // code server gets Claude, but so does the cheap utility server
};

const client = new MCPClient(
  {
    mcpServers: {
      codeServer: { url: "https://code.example.com/mcp" },
      utilityServer: { url: "https://util.example.com/mcp" },
    },
  },
  { onSampling }
);

// ✅ GOOD — per-server callbacks with appropriate models
const client = new MCPClient(
  {
    mcpServers: {
      codeServer: {
        url: "https://code.example.com/mcp",
        onSampling: async (params) => callClaude(params),  // expensive, high quality
      },
      utilityServer: {
        url: "https://util.example.com/mcp",
        onSampling: async (params) => callGPT35(params),   // cheap, fast
      },
    },
  },
  {
    onSampling: async (params) => callDefaultModel(params), // fallback for any without override
  }
);
```

### Ignoring Callback Precedence Order

```typescript
// ❌ BAD — confused about which callback runs
const client = new MCPClient(
  {
    mcpServers: {
      api: {
        url: "https://api.example.com/mcp",
        onSampling: serverSpecificSampling,    // ← THIS wins (priority 1)
      },
    },
  },
  {
    onSampling: globalSampling,                // ← This is the fallback (priority 3)
  }
);
// If you expected globalSampling to run for "api", it won't!

// ✅ GOOD — understand the precedence
// Priority order (first match wins):
// 1. Per-server onSampling / onElicitation / onNotification
// 2. Per-server samplingCallback / elicitationCallback (deprecated — use onSampling / onElicitation)
// 3. Global onSampling / onElicitation / onNotification
// 4. Global samplingCallback / elicitationCallback (deprecated)
```

### Not Forwarding Server Logs via loggingCallback

```typescript
// ❌ BAD — server log messages are silently discarded
const client = new MCPClient(
  { mcpServers: { api: { url: "https://api.example.com/mcp" } } },
  { onSampling }
);
// Server-emitted logs (debug/info/warning/error) are never seen

// ✅ GOOD — register loggingCallback to surface server logs
import { MCPClient, types, type OnNotificationCallback } from "mcp-use";

const onNotification: OnNotificationCallback = (notification) => {
  console.log(`[mcp:${notification.method}]`, notification.params ?? "");
};

const client = new MCPClient(
  { mcpServers: { api: { url: "https://api.example.com/mcp" } } },
  {
    onSampling,
    onNotification,
    loggingCallback: (logParams: types.LoggingMessageNotificationParams) => {
      // logParams.level: "debug" | "info" | "warning" | "error"
      // logParams.message: string
      console.log(`[server:${logParams.level}] ${logParams.message}`);
    },
  }
);
```

### Missing clientInfo Configuration

```typescript
// ❌ BAD — using default clientInfo ("mcp-use" with package version)
const client = new MCPClient({
  mcpServers: { api: { url: "https://api.example.com/mcp" } },
});
// Server sees: { name: "mcp-use", version: "1.x.x" } — not helpful for server-side analytics

// ✅ GOOD — set meaningful clientInfo at the top-level config (applies to all servers)
const client = new MCPClient({
  clientInfo: {
    name: "my-dashboard",
    version: "2.1.0",
    description: "Internal analytics dashboard",
  },
  mcpServers: {
    api: { url: "https://api.example.com/mcp" },
  },
});

// ✅ ALSO GOOD — set clientInfo per-server (overrides top-level for that server)
const client2 = new MCPClient({
  mcpServers: {
    api: {
      url: "https://api.example.com/mcp",
      clientInfo: {
        name: "my-dashboard",
        version: "2.1.0",
      },
    },
  },
});
```

### Confusing decline vs cancel in Elicitation Results

```typescript
// ❌ BAD — using decline when the user explicitly cancelled (confused semantics)
const onElicitation: OnElicitationCallback = async (params) => {
  const data = await showForm(params);
  if (!data) {
    return decline(); // Wrong — "decline" means the server should not proceed;
                      // "cancel" means the user dismissed the dialog
  }
  return accept(data);
};

// ✅ GOOD — use cancel for user dismissal, decline for explicit refusal
import { accept, decline, cancel, validate, type OnElicitationCallback } from "mcp-use";

const onElicitation: OnElicitationCallback = async (params) => {
  const data = await showForm(params); // returns null if user closed dialog

  if (data === null) {
    return cancel();   // user explicitly dismissed — server can retry
  }
  if (data === false) {
    return decline();  // user explicitly refused — server should not retry
  }

  const { valid, errors } = validate(params, data);
  if (!valid) return decline(errors?.join("; "));
  return accept(data);
};
```

---

## 4. Session Anti-Patterns

### Calling Methods Before Session Initialization

```typescript
// ❌ BAD — getSession before createSession
const client = new MCPClient({
  mcpServers: { api: { url: "http://localhost:3000/mcp" } },
});
const session = client.getSession("api"); // returns null until a session is created
const tools = await session.listTools();  // crashes

// ✅ GOOD — create session first
const client = new MCPClient({
  mcpServers: { api: { url: "http://localhost:3000/mcp" } },
});
await client.createAllSessions();
const session = client.requireSession("api");
const tools = await session.listTools();
```

### Not Logging Session Recovery Events

```typescript
// ❌ BAD — 404 recovery happens silently, you never know about it
const client = new MCPClient({
  mcpServers: { api: { url: "https://api.example.com/mcp" } },
});

// ✅ GOOD — log notifications to track recovery events
const client = new MCPClient(
  {
    mcpServers: { api: { url: "https://api.example.com/mcp" } },
  },
  {
    onNotification: (notification) => {
      console.log(`[mcp:${notification.method}]`, notification.params ?? "");
    },
  }
);
// Now you'll see when sessions are re-initialized after 404
```

### Using STDIO Config in Browser Environment

```typescript
// ❌ BAD — STDIO requires child processes, not available in browser
import { MCPClient } from "mcp-use/browser";

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",  // This cannot work in a browser!
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/data"],
    },
  },
});

// ✅ GOOD — use HTTP connections in browser
import { MCPClient } from "mcp-use/browser";

const client = new MCPClient({
  mcpServers: {
    api: {
      url: "https://api.example.com/mcp",
      headers: { Authorization: "Bearer token" },
    },
  },
});
```

### Creating Redundant Sessions

```typescript
// ❌ BAD — creating the same session multiple times
await client.createSession("api");
await client.createSession("api"); // redundant, may cause issues
await client.createSession("api");

// ✅ GOOD — create once, reuse
await client.createAllSessions(); // or: await client.createSession("api");
const session = client.getSession("api");
// Use session for all subsequent calls
```

---

## 5. React Anti-Patterns

### Not Checking State Before Rendering Tool Results

```typescript
// ❌ BAD — accessing tools before connection is ready
import { useMcp } from "mcp-use/react";

function ToolList() {
  const mcp = useMcp({ url: "https://api.example.com/mcp" });

  return (
    <ul>
      {mcp.tools.map((tool) => (  // tools may be empty or undefined during connection
        <li key={tool.name}>{tool.name}</li>
      ))}
    </ul>
  );
}

// ✅ GOOD — handle all connection states
function ToolList() {
  const mcp = useMcp({ url: "https://api.example.com/mcp" });

  if (mcp.state === "discovering") return <div>Connecting...</div>;
  if (mcp.state === "authenticating") return <div>Authenticating...</div>;
  if (mcp.state === "pending_auth") {
    return <button onClick={mcp.authenticate}>Authorize</button>;
  }
  if (mcp.state === "failed") return <div>Error: {mcp.error}</div>;
  if (mcp.state !== "ready") return null;

  return (
    <ul>
      {mcp.tools.map((tool) => (
        <li key={tool.name}>{tool.name}: {tool.description}</li>
      ))}
    </ul>
  );
}
```

### Creating MCPClient in Render Function

```typescript
// ❌ BAD — new client on every render (infinite re-renders, connection thrashing)
import { MCPClient } from "mcp-use/browser";

function Dashboard() {
  const client = new MCPClient({  // re-created on EVERY render
    mcpServers: { api: { url: "https://api.example.com/mcp" } },
  });

  // ...
}

// ✅ GOOD — use the useMcp hook (manages client lifecycle automatically)
import { useMcp } from "mcp-use/react";

function Dashboard() {
  const mcp = useMcp({ url: "https://api.example.com/mcp" });
  // ...
}

// ✅ GOOD — or use McpClientProvider for multi-server
import { McpClientProvider, useMcpServer } from "mcp-use/react";

function App() {
  return (
    <McpClientProvider
      mcpServers={{
        api: { url: "https://api.example.com/mcp", name: "API" },
      }}
    >
      <Dashboard />
    </McpClientProvider>
  );
}

function Dashboard() {
  const api = useMcpServer("api");
  // ...
}
```

### Not Using McpClientProvider for Multi-Server

> **Breaking change (v1.20.1):** `McpClientProvider` no longer includes `BrowserRouter`. If you use React Router, add `<BrowserRouter>` outside `<McpClientProvider>` manually.

```typescript
// ❌ BAD — multiple independent useMcp hooks (no shared state, no coordination)
function Dashboard() {
  const search = useMcp({ url: "https://search.example.com/mcp" });
  const analytics = useMcp({ url: "https://analytics.example.com/mcp" });
  const files = useMcp({ url: "https://files.example.com/mcp" });
  // Each manages its own connection independently, no shared state
}

// ✅ GOOD — McpClientProvider manages all servers together
import { McpClientProvider, useMcpClient, useMcpServer } from "mcp-use/react";

function App() {
  return (
    <McpClientProvider
      mcpServers={{
        search: { url: "https://search.example.com/mcp", name: "Search" },
        analytics: { url: "https://analytics.example.com/mcp", name: "Analytics" },
        files: { url: "https://files.example.com/mcp", name: "Files" },
      }}
    >
      <Dashboard />
    </McpClientProvider>
  );
}

function Dashboard() {
  const { servers } = useMcpClient();
  const search = useMcpServer("search");
  const analytics = useMcpServer("analytics");
  // Shared state, coordinated lifecycle, centralized config
}
```

### Missing Cleanup on Unmount

```typescript
// ❌ BAD — manual MCPClient in useEffect without cleanup
import { MCPClient } from "mcp-use/browser";
import { useEffect, useState } from "react";

function ToolPanel() {
  const [tools, setTools] = useState([]);

  useEffect(() => {
    const client = new MCPClient({
      mcpServers: { api: { url: "https://api.example.com/mcp" } },
    });
    client.createAllSessions().then(() => {
      client.getSession("api").listTools().then(setTools);
    });
    // No cleanup! Sessions and connections leak on unmount
  }, []);

  return <div>{tools.length} tools</div>;
}

// ✅ GOOD — use useMcp (handles lifecycle automatically)
import { useMcp } from "mcp-use/react";

function ToolPanel() {
  const mcp = useMcp({ url: "https://api.example.com/mcp" });

  if (mcp.state !== "ready") return <div>Loading...</div>;
  return <div>{mcp.tools.length} tools</div>;
  // Cleanup is automatic on unmount
}
```

### Not Handling pending_auth State for OAuth Servers

```typescript
// ❌ BAD — shows "loading" forever when server requires OAuth
function ServerPanel() {
  const mcp = useMcp({
    url: "https://oauth-server.example.com/mcp",
    callbackUrl: window.location.origin + "/callback",
  });

  if (mcp.state !== "ready") {
    return <div>Loading...</div>; // stuck here when state === "pending_auth"
  }
  return <div>{mcp.tools.length} tools</div>;
}

// ✅ GOOD — handle pending_auth explicitly
function ServerPanel() {
  const mcp = useMcp({
    url: "https://oauth-server.example.com/mcp",
    callbackUrl: window.location.origin + "/callback",
  });

  if (mcp.state === "pending_auth") {
    return (
      <div>
        <p>This server requires authorization.</p>
        <button onClick={mcp.authenticate}>Connect with OAuth</button>
      </div>
    );
  }
  if (mcp.state === "failed") {
    return <div>Connection failed. <button onClick={mcp.retry}>Retry</button></div>;
  }
  if (mcp.state !== "ready") {
    return <div>Connecting: {mcp.state}...</div>;
  }
  return <div>{mcp.tools.length} tools</div>;
}
```

### Not Using autoProxyFallback for Cross-Origin Servers

```typescript
// ❌ BAD — browser CORS blocks the connection, no fallback
const mcp = useMcp({ url: "https://third-party-mcp.example.com/mcp" });
// Connection fails silently due to CORS

// ✅ GOOD — enable proxy fallback
const mcp = useMcp({
  url: "https://third-party-mcp.example.com/mcp",
  autoProxyFallback: true,
});
// Tries direct → detects CORS → automatically retries through proxy
```

---

## 6. Security Anti-Patterns

### Exposing Tokens in Browser Code

```typescript
// ❌ BAD — API key visible in browser source/network tab
import { MCPClient } from "mcp-use/browser";

const client = new MCPClient({
  mcpServers: {
    api: {
      url: "https://api.example.com/mcp",
      headers: { Authorization: "Bearer sk-secret-key-12345" },
    },
  },
});

// ✅ GOOD — use OAuth for browser authentication
import { MCPClient, BrowserOAuthClientProvider } from "mcp-use/browser";

const authProvider = new BrowserOAuthClientProvider({
  clientId: "your-client-id",
  authorizationUrl: "https://api.example.com/oauth/authorize",
  tokenUrl: "https://api.example.com/oauth/token",
  callbackUrl: window.location.origin + "/oauth/callback",
});

const client = new MCPClient({
  mcpServers: {
    api: {
      url: "https://api.example.com/mcp",
      authProvider,
    },
  },
});

// ✅ GOOD — or use useMcp with built-in OAuth
import { useMcp } from "mcp-use/react";

const mcp = useMcp({
  url: "https://api.example.com/mcp",
  callbackUrl: window.location.origin + "/callback",
});
```

### Using VM Executor for Untrusted Code

```typescript
// ❌ BAD — VM executor has basic isolation, can escape sandbox
import { MCPClient } from "mcp-use";

const client = new MCPClient(
  { mcpServers: { api: { url: "https://api.example.com/mcp" } } },
  {
    codeMode: {
      enabled: true,
      executor: "vm",  // Node.js vm module — NOT safe for untrusted code
    },
  }
);
// User-submitted code can access process, require(), filesystem

// ✅ GOOD — use E2B for untrusted code execution
const client = new MCPClient(
  { mcpServers: { api: { url: "https://api.example.com/mcp" } } },
  {
    codeMode: {
      enabled: true,
      executor: "e2b",
      executorOptions: {
        apiKey: process.env.E2B_API_KEY!,
        timeoutMs: 60_000,
      },
    },
  }
);
```

### Not Validating Tool Results Before Use

```typescript
// ❌ BAD — blindly trusting tool output
const result = await session.callTool("get-config", { key: "db_url" });
const dbUrl = result.content[0].text;
await connectToDatabase(dbUrl); // could be malicious URL from compromised server

// ✅ GOOD — validate tool results before using them
const result = await session.callTool("get-config", { key: "db_url" });
if (result.isError) {
  throw new Error("Failed to get config");
}

const dbUrl = result.content?.[0]?.text;
if (!dbUrl || typeof dbUrl !== "string") {
  throw new Error("Invalid config response");
}

// Validate URL format and allowed hosts
const parsed = new URL(dbUrl);
const allowedHosts = ["db.example.com", "db-staging.example.com"];
if (!allowedHosts.includes(parsed.hostname)) {
  throw new Error(`Untrusted database host: ${parsed.hostname}`);
}

await connectToDatabase(dbUrl);
```

### Trusting Server-Sent Data Without Validation

```typescript
// ❌ BAD — rendering server HTML directly (XSS risk)
const result = await session.callTool("render-widget", { id: "dashboard" });
document.innerHTML = result.content[0].text; // XSS vulnerability

// ✅ GOOD — sanitize server-provided content
import DOMPurify from "dompurify";

const result = await session.callTool("render-widget", { id: "dashboard" });
if (!result.isError && result.content?.[0]?.text) {
  const clean = DOMPurify.sanitize(result.content[0].text);
  container.innerHTML = clean;
}
```

### Not Setting Timeout Limits on Code Execution

```typescript
// ❌ BAD — no timeout, code can run forever
const client = new MCPClient(
  { mcpServers: { api: { url: "https://api.example.com/mcp" } } },
  {
    codeMode: {
      enabled: true,
      executor: "vm",
      // No timeoutMs set — defaults to 30s but should be explicit
    },
  }
);

// ✅ GOOD — explicit timeout and memory limits
const client = new MCPClient(
  { mcpServers: { api: { url: "https://api.example.com/mcp" } } },
  {
    codeMode: {
      enabled: true,
      executor: "vm",
      executorOptions: {
        timeoutMs: 15_000,
        memoryLimitMb: 128,
      },
    },
  }
);
```

### Logging Sensitive Callback Data

```typescript
// ❌ BAD — logs full sampling params which may include user data/secrets
const client = new MCPClient(
  { mcpServers: { api: { url: "https://api.example.com/mcp" } } },
  {
    onSampling: async (params) => {
      console.log("Sampling request:", JSON.stringify(params)); // leaks message content
      return callLLM(params);
    },
  }
);

// ✅ GOOD — log metadata only
const client = new MCPClient(
  { mcpServers: { api: { url: "https://api.example.com/mcp" } } },
  {
    onSampling: async (params) => {
      console.log("Sampling request:", {
        messageCount: params.messages?.length,
        maxTokens: params.maxTokens,
        hasSystemPrompt: !!params.systemPrompt,
      });
      return callLLM(params);
    },
  }
);
```

---

## Quick Reference: Severity Guide

| Severity | Anti-patterns |
|---|---|
| Critical | Exposing tokens in browser, VM for untrusted code, no tool result validation, hardcoded secrets |
| High | No `isError` check, no `closeAllSessions`, new client per request, no state check in React |
| Medium | Missing reconnection config, no timeout config, ignoring callback precedence, STDIO in browser, missing `loggingCallback`, confusing `decline`/`cancel` |
| Low | Default clientInfo, no proxy fallback, not logging recovery events, redundant sessions |

---

## Quick Reference: Environment Constraints

| Feature | Node.js | Browser | React |
|---|---|---|---|
| STDIO connections | ✅ | ❌ Never | ❌ Never |
| HTTP connections | ✅ | ✅ | ✅ |
| OAuth (built-in) | ✅ | ✅ | ✅ (with `pending_auth` handling) |
| Code Mode | ✅ | ❌ Never | ❌ Never |
| Config file loading | ✅ | ❌ | ❌ |
| `closeAllSessions` | ✅ Manual | ✅ Manual | ✅ Automatic via hooks |
| Auto-reconnect | Via HttpConnector | Via HttpConnector | Via `autoReconnect` prop |
