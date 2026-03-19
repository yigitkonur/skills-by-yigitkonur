# MCP Client Common Errors

Diagnose and fix the most frequent errors encountered when building MCP clients with the `mcp-use` library — connection, session, tool, resource, sampling, elicitation, React, code mode, and import issues.

---

## Connection Errors

---
### Error: Cannot connect to server

**When:** `createSession` or `createAllSessions` hangs or throws a connection error against an HTTP server.

**Cause:** Server is not running, URL is wrong (wrong host, port, or path), or a firewall/network rule blocks the request.

**Fix:**
1. Verify the server is running and listening on the expected port.
2. Confirm the URL includes the correct path (typically `/mcp`):
```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    myServer: {
      url: "http://localhost:3000/mcp", // ✅ include /mcp path
      // url: "http://localhost:3000",  // ❌ missing path
    },
  },
});
await client.createAllSessions();
```
3. Test reachability: `curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/mcp` — should return 200 or 405.

**Prevention:** Log the full URL at startup. Use environment variables for host/port so dev and prod configs don't diverge.

---
### Error: ECONNREFUSED

**When:** Creating a session for a STDIO server — `createSession` throws `ECONNREFUSED` or `spawn ENOENT`.

**Cause:** The `command` in the server config does not exist, is not on `$PATH`, or the server process crashes on startup before completing the MCP handshake.

**Fix:**
1. Verify the command runs standalone: `npx -y @modelcontextprotocol/server-everything` in a terminal.
2. Check spelling and args:
```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    everything: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-everything"],
      // ❌ wrong: command: "npxx" or missing "-y"
    },
  },
});
await client.createAllSessions();
```
3. If the server requires environment variables, pass them via `env`:
```typescript
env: { API_KEY: process.env.API_KEY! }
```

**Prevention:** Always test the server command in isolation before adding it to client config. Add `env` for any required variables.

---
### Error: Session not found (404)

**When:** A tool call or resource read returns a 404 after the server has restarted or the session expired.

**Cause:** The client is sending a stale `Mcp-Session-Id` header. The server's in-memory session store lost the session on restart.

**Fix:**
The client handles this automatically with 404 auto-recovery:
```
[StreamableHttp] Session not found (404), re-initializing per MCP spec...
[StreamableHttp] Re-initialization successful, retrying request
```
If auto-recovery is not working:
1. Ensure you are using `mcp-use` v1.21.1+ (the version that introduced stable auto-recovery; latest is v1.21.5).
2. Check that the server correctly returns 404 (not 500) for expired sessions.
3. Manually reconnect:
```typescript
await client.closeAllSessions();
await client.createAllSessions();
```

**Prevention:** Upgrade `mcp-use` to latest. For production servers, use a persistent session store (Redis) so sessions survive restarts.

---
### Error: CORS blocked

**When:** A browser-based client fails to connect with `Access to fetch has been blocked by CORS policy`.

**Cause:** The MCP server does not return `Access-Control-Allow-Origin` headers, or the browser's origin is not in the allowed list.

**Fix:**
1. **Preferred: Use auto proxy fallback** — the client detects CORS errors and retries via a proxy:
```typescript
import { MCPClient } from "mcp-use/browser";

const client = new MCPClient({
  mcpServers: {
    myServer: {
      url: "http://localhost:3000/mcp",
      autoProxyFallback: true,
    },
  },
});
```
2. Or configure CORS on the server side (see server troubleshooting guide).
3. With React, set it at the provider level:
```typescript
import { McpClientProvider } from "mcp-use/react";

<McpClientProvider defaultAutoProxyFallback={true}>
  <App />
</McpClientProvider>
```

**Prevention:** Always enable `autoProxyFallback` for browser clients during development. In production, configure CORS on the server.

---
### Error: WebSocket connection failed

**When:** Client attempts to connect via WebSocket and gets a connection failure or protocol error.

**Cause:** MCP uses HTTP Streamable transport (or legacy SSE), not WebSocket. The `url` might point to a WebSocket endpoint, or `transportType` is misconfigured.

**Fix:**
Use the correct transport type:
```typescript
import { MCPClient } from "mcp-use/browser";

const client = new MCPClient({
  mcpServers: {
    myServer: {
      url: "http://localhost:3000/mcp",
      transportType: "http",  // ✅ Use HTTP, not WebSocket
      // transportType: "sse", // Or force SSE for legacy servers
      // transportType: "auto", // Default: auto-detect
    },
  },
});
```

**Prevention:** MCP does not use WebSocket. Use `transportType: "auto"` (default) which tries HTTP Streamable first, then falls back to SSE.

---
### Error: Authentication required (401 Unauthorized)

**When:** `createSession` or tool calls return 401 against an OAuth-protected server.

**Cause:** The server requires OAuth authentication but the client has no `authProvider`, `headers`, or `callbackUrl` configured.

**Fix:**
For Node.js with bearer token:
```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    myServer: {
      url: "https://api.example.com/mcp",
      headers: {
        Authorization: `Bearer ${process.env.API_TOKEN}`,
      },
    },
  },
});
```

For browser with OAuth:
```typescript
import { MCPClient, BrowserOAuthClientProvider } from "mcp-use/browser";

const authProvider = new BrowserOAuthClientProvider({
  clientId: "your-client-id",
  authorizationUrl: "https://api.example.com/oauth/authorize",
  tokenUrl: "https://api.example.com/oauth/token",
  callbackUrl: window.location.origin + "/oauth/callback",
});

const client = new MCPClient({
  mcpServers: {
    myServer: {
      url: "https://api.example.com/mcp",
      authProvider,
    },
  },
});
```

**Prevention:** Check the server's auth requirements before configuring the client. Use environment variables for tokens, never hardcode them.

---
### Error: Connection drops after ~60 seconds

**When:** HTTP or SSE connections are silently terminated after approximately 60 seconds of inactivity.

**Cause:** A reverse proxy (nginx, Cloudflare, AWS ALB) between the client and server has a default idle timeout of 60 seconds.

**Fix:**
1. Enable auto-reconnect on the client:
```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient(
  {
    mcpServers: {
      myServer: {
        url: "http://localhost:3000/mcp",
      },
    },
  },
);
const session = await client.createSession("myServer");
// The client's 404 auto-recovery handles reconnection automatically
```
2. Configure proxy timeouts: `proxy_read_timeout 86400s;` in nginx.
3. With React, configure reconnection:
```typescript
import { useMcp } from "mcp-use/react";

const mcp = useMcp({
  url: "http://localhost:3000/mcp",
  autoReconnect: {
    enabled: true,
    initialDelay: 3000,
    healthCheckInterval: 30000,
  },
});
```

**Prevention:** Always enable `autoReconnect` in production. Prefer HTTP Streamable transport over SSE to reduce proxy issues.

---

## Session Errors

---
### Error: Client not ready — calling methods before session creation

**When:** Calling `session.listTools()`, `session.callTool()`, or any session method throws "Client not ready" or returns undefined.

**Cause:** You are calling session methods before `createSession()` or `createAllSessions()` has completed.

**Fix:**
Always `await` session creation before using sessions:
```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    myServer: { url: "http://localhost:3000/mcp" },
  },
});

// ❌ Wrong: using session before it's ready
// const session = client.getSession("myServer");
// const tools = await session.listTools(); // throws

// ✅ Correct: await session creation first
await client.createAllSessions();
const session = client.getSession("myServer");
const tools = await session.listTools();
```

In React, check the state before accessing tools:
```typescript
import { useMcp } from "mcp-use/react";

function MyComponent() {
  const mcp = useMcp({ url: "http://localhost:3000/mcp" });

  if (mcp.state !== "ready") {
    return <div>Connecting... ({mcp.state})</div>;
  }

  // ✅ Safe to access tools only when state is "ready"
  return <div>{mcp.tools.length} tools available</div>;
}
```

**Prevention:** Always `await createAllSessions()` in Node.js. In React, gate all tool/resource access behind `state === "ready"`.

---
### Error: Session already exists

**When:** Calling `createSession("myServer")` throws an error indicating the session already exists.

**Cause:** `createSession` was called twice for the same server name, or `createAllSessions` was called after individual `createSession` calls.

**Fix:**
Use `createAllSessions()` once, or check if the session already exists:
```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    serverA: { url: "http://localhost:3000/mcp" },
    serverB: { url: "http://localhost:3001/mcp" },
  },
});

// ✅ Option 1: Create all at once
await client.createAllSessions();

// ✅ Option 2: Create individually, but only once each
// await client.createSession("serverA");
// await client.createSession("serverB");

// ❌ Don't mix or double-call
// await client.createAllSessions();
// await client.createSession("serverA"); // throws
```

**Prevention:** Always use `createAllSessions()` for simplicity.

---
### Error: No active session — getSession returns undefined

**When:** `client.getSession("myServer")` returns `undefined`, and subsequent method calls fail.

**Cause:** The server name passed to `getSession` does not match any key in `mcpServers`, or sessions have not been created yet.

**Fix:**
1. Verify the server name matches exactly (case-sensitive):
```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    "my-server": { url: "http://localhost:3000/mcp" },
    // Key is "my-server", not "myServer" or "My-Server"
  },
});
await client.createAllSessions();

const session = client.getSession("my-server"); // ✅ exact match
// const session = client.getSession("myServer"); // ❌ undefined
```
2. Check that `createAllSessions()` or `createSession()` completed without errors.

**Prevention:** Use consistent naming conventions for server keys. Log available session names for debugging.

---
### Error: Cannot create STDIO session in browser

**When:** A browser-based client throws an error when configured with `command` and `args` (STDIO config).

**Cause:** Browsers cannot spawn child processes. STDIO transport is only available in Node.js and CLI environments.

**Fix:**
Use HTTP transport for browser clients:
```typescript
// ❌ Wrong: STDIO config in browser
import { MCPClient } from "mcp-use/browser";
const client = new MCPClient({
  mcpServers: {
    myServer: {
      command: "npx",                    // ❌ Not supported in browser
      args: ["-y", "my-mcp-server"],
    },
  },
});

// ✅ Correct: HTTP config for browser
const client = new MCPClient({
  mcpServers: {
    myServer: {
      url: "http://localhost:3000/mcp",  // ✅ HTTP only
    },
  },
});
```

**Prevention:** Always use `url`-based config for browser and React clients. Run STDIO servers separately and expose them via HTTP for browser access.

---

## Tool Errors

---
### Error: Tool not found

**When:** `session.callTool("my-tool", args)` returns an error that the tool was not found.

**Cause:** The tool name does not match any tool exposed by the server. Names are case-sensitive. The server may not have registered the tool, or the tool was registered after `server.listen()`.

**Fix:**
1. List available tools to confirm the exact name:
```typescript
const tools = await session.listTools();
console.log("Available tools:", tools.map(t => t.name));
```
2. Use the exact name from the listing:
```typescript
// If listTools shows "readFile" (not "read_file"):
const result = await session.callTool("readFile", { path: "/tmp/test.txt" });
```
3. If tools list is empty, see "Server starts but no tools appear" in the server troubleshooting guide.

**Prevention:** Always call `listTools()` first to discover exact tool names. Tool names are case-sensitive and server-defined.

---
### Error: Invalid arguments — tool call validation failure

**When:** `callTool` returns an error with validation details — wrong types, missing required fields, or extra fields.

**Cause:** The arguments passed to `callTool` do not match the tool's JSON Schema. Common issues: wrong types (string vs number), missing required fields, extra unrecognized fields.

**Fix:**
1. Inspect the tool's input schema:
```typescript
const tools = await session.listTools();
const tool = tools.find(t => t.name === "create-issue");
console.log("Schema:", JSON.stringify(tool?.inputSchema, null, 2));
```
2. Pass arguments matching the schema:
```typescript
// If schema requires { title: string, priority: number }:
const result = await session.callTool("create-issue", {
  title: "Fix login bug",  // ✅ string
  priority: 1,             // ✅ number, not "1"
});
```
3. Use `z.coerce` on the server side if the client sends strings for numbers.

**Prevention:** Always check `inputSchema` before calling unfamiliar tools. Use TypeScript types to match schema shapes.

---
### Error: Request timeout

**When:** `callTool` throws a timeout error — the tool took too long to respond.

**Cause:** The tool performs a slow operation (large file processing, external API call, heavy computation) that exceeds the default 60-second timeout.

**Fix:**
1. Increase the timeout for the specific call:
```typescript
const result = await session.callTool(
  "process-dataset",
  { datasetId: "large-dataset" },
  {
    timeout: 300000,                // 5 minutes
    maxTotalTimeout: 600000,        // 10 minutes absolute max
    resetTimeoutOnProgress: true,   // Reset on progress notifications
  }
);
```
2. Use an `AbortController` for manual cancellation:
```typescript
const controller = new AbortController();
setTimeout(() => controller.abort(), 120000); // 2 min manual timeout

const result = await session.callTool(
  "slow-tool",
  { input: "data" },
  { signal: controller.signal }
);
```

**Prevention:** Set appropriate timeouts per tool. Ask server authors to implement progress notifications for long-running operations.

---
### Error: Method not found (-32601)

**When:** Calling `session.complete()` or another protocol method returns JSON-RPC error `-32601: Method not found`.

**Cause:** The server does not support the called method. For completions, the server must explicitly declare `completions` in its capabilities.

**Fix:**
Check server capabilities before calling optional methods:
```typescript
await client.createAllSessions();
const session = client.getSession("myServer");
const capabilities = session.connector.serverCapabilities;

// Check before calling complete()
if (capabilities?.completions) {
  const result = await session.complete({
    ref: { type: "ref/prompt", name: "my-prompt" },
    argument: { name: "language", value: "py" },
  });
  console.log("Suggestions:", result.completion.values);
} else {
  console.warn("Server does not support completions");
}
```

**Prevention:** Always check `serverCapabilities` before using optional protocol features (completions, sampling, elicitation). Not all servers support all MCP features.

---

## Resource Errors

---
### Error: Resource not found

**When:** `session.readResource(uri)` returns an error that the resource does not exist.

**Cause:** The URI does not match any resource exposed by the server. The resource may have been removed, or the URI is misspelled.

**Fix:**
1. List available resources:
```typescript
const resources = await session.listResources();
console.log("Available:", resources.map(r => r.uri));
```
2. For templated resources, ensure variables are correctly substituted:
```typescript
// Template: "file:///{path}"
// ✅ Correct: pass the full resolved URI
const result = await session.readResource("file:///home/user/data.json");
for (const content of result.contents) {
  console.log(content.text);
}

// ❌ Wrong: passing the template itself
// const result = await session.readResource("file:///{path}");
```

**Prevention:** Always list resources first to discover available URIs. Use `listResources()` to discover available resources.

---
### Error: Invalid URI — malformed resource URI

**When:** `readResource` throws a URI parsing error.

**Cause:** The URI is not correctly formatted. Common issues: missing scheme, double-encoded characters, backslashes instead of forward slashes.

**Fix:**
```typescript
// ❌ Wrong URIs:
// "home/user/file.txt"         — missing scheme
// "file:///C:\\Users\\file.txt" — backslashes
// "file:///path%2Fto%2Ffile"   — double-encoded

// ✅ Correct URIs:
await session.readResource("file:///home/user/file.txt");
await session.readResource("https://api.example.com/data");
await session.readResource("custom://my-resource/id-123");
```

**Prevention:** Always use forward slashes. Include the URI scheme. Use `encodeURIComponent()` only for individual path segments, not the entire URI.

---
### Error: Resource read failed — server-side error

**When:** `readResource` throws an error originating from the server (e.g., file not found, permission denied, database error).

**Cause:** The server encountered an error while reading the resource. The resource exists in the listing but the underlying data source is unavailable.

**Fix:**
1. Check the error message for specifics:
```typescript
try {
  const result = await session.readResource("file:///sensitive/data.json");
} catch (error) {
  console.error("Resource read failed:", error.message);
  // Check if it's a permission issue, file not found, etc.
}
```
2. Verify the server has access to the underlying data source.
3. Check server logs for detailed error information.

**Prevention:** Wrap `readResource` calls in try/catch. Implement retry logic for transient failures (network, database connection).

---

## Sampling Errors

---
### Error: No sampling callback configured

**When:** A tool call triggers a server-side sampling request (the server calls `ctx.sample()`), but the client has no `onSampling` callback.

**Cause:** The server requested an LLM completion from the client, but the client was not configured with a sampling callback to handle it.

**Fix:**
Provide an `onSampling` callback at the client or per-server level:
```typescript
import { MCPClient, type OnSamplingCallback } from "mcp-use";

const onSampling: OnSamplingCallback = async (params) => {
  const lastMessage = params.messages[params.messages.length - 1];
  const text = typeof lastMessage?.content === "object" && "text" in lastMessage.content
    ? lastMessage.content.text
    : "";

  const response = await yourLLM.complete(text ?? "");
  return {
    role: "assistant",
    content: { type: "text", text: response },
    model: "your-model",
    stopReason: "endTurn",
  };
};

const client = new MCPClient(
  { mcpServers: { myServer: { url: "http://localhost:3000/mcp" } } },
  { onSampling }
);
```

**Prevention:** If connecting to servers that use sampling (agentic servers), always configure `onSampling`. Check server documentation for sampling requirements.

---
### Error: Sampling callback returned invalid result

**When:** The `onSampling` callback returns a result that fails validation — the server rejects it.

**Cause:** The `CreateMessageResult` is missing required fields (`role`, `content.type`, `model`) or has wrong types.

**Fix:**
Ensure all required fields are present in the return value:
```typescript
import type { OnSamplingCallback, CreateMessageResult } from "mcp-use";

const onSampling: OnSamplingCallback = async (params) => {
  const response = await yourLLM.complete(/* ... */);

  // ✅ All required fields present
  return {
    role: "assistant",                             // Required: must be "assistant"
    content: { type: "text", text: response },     // Required: type + text/data
    model: "gpt-4",                                // Required: model identifier
    stopReason: "endTurn",                          // Optional but recommended
  };

  // ❌ Missing fields will cause errors:
  // return { text: response };  // Missing role, content structure, model
};
```

**Prevention:** Use the `CreateMessageResult` type for type-checking. Always include `role`, `content` (with `type`), and `model`.

---
### Error: Sampling request not approved (React provider)

**When:** Using `McpClientProvider` with `onSamplingRequest`, the sampling request is never processed.

**Cause:** The `approve` callback was never called — the UI did not show an approval dialog, or the logic skipped it.

**Fix:**
```typescript
import { McpClientProvider } from "mcp-use/react";

<McpClientProvider
  onSamplingRequest={(request, serverId, serverName, approve, reject) => {
    // ✅ Must call approve() or reject() — don't ignore the request
    const userApproved = window.confirm(
      `${serverName} wants to use LLM sampling. Allow?`
    );
    if (userApproved) {
      approve({
        role: "assistant",
        content: { type: "text", text: "Approved response" },
        model: "gpt-4",
      });
    } else {
      reject();
    }
  }}
>
  <App />
</McpClientProvider>
```

**Prevention:** Always call either `approve()` or `reject()` in the `onSamplingRequest` callback. Unanswered requests will hang indefinitely.

---

## Elicitation Errors

---
### Error: No elicitation callback configured

**When:** A tool on the server calls `ctx.elicit()` to request user input, but the client has no `onElicitation` callback.

**Cause:** The server needs structured input from the user (a form or URL redirect), but the client was not configured to handle elicitation requests.

**Fix:**
Configure an `onElicitation` callback:
```typescript
import { MCPClient, acceptWithDefaults, type OnElicitationCallback } from "mcp-use";

const onElicitation: OnElicitationCallback = async (params) => {
  // Simplest: accept using schema defaults — no manual field filling needed
  return acceptWithDefaults(params);
};
```

For interactive applications, handle form and URL modes:
```typescript
import { accept, decline, cancel, validate } from "mcp-use";

const onElicitation: OnElicitationCallback = async (params) => {
  if (params.mode === "url") {
    console.log(`Visit: ${params.url}`);
    console.log(`Reason: ${params.message}`);
    const completed = await askUser("Did you complete the action?");

    // ✅ URL mode: action only, no content
    return { action: completed ? "accept" : "decline" };

    // ❌ Wrong: including content in URL mode
    // return { action: "accept", content: { result: "done" } };
  }

  // Form mode: collect input from user
  const data = await collectFormData(params.message, params.requestedSchema);
  return accept(data);
};
```

**Prevention:** If connecting to servers that use elicitation, always configure `onElicitation`. Use `accept(...)` with safe defaults.

---
### Error: Elicitation validation failed — form data doesn't match schema

**When:** The `onElicitation` callback returns data that does not match the server's `requestedSchema`.

**Cause:** The user-provided form data has wrong types, missing required fields, or values outside allowed ranges.

**Fix:**
Use the `validate()` helper before returning:
```typescript
import { accept, decline, validate } from "mcp-use";

const onElicitation: OnElicitationCallback = async (params) => {
  const formData = await collectFormFromUser(params.message, params.requestedSchema);

  // ✅ Validate before returning
  const { valid, errors } = validate(params, formData);
  if (!valid) {
    console.error("Validation errors:", errors);
    return decline(errors?.join("; "));
  }

  return accept(formData);
};
```

**Prevention:** Always call `validate(params, data)` before returning `accept(data)`. Derive defaults from `params.requestedSchema` when needed.

---
### Error: Elicitation callback returns wrong action for URL mode

**When:** URL-mode elicitation fails because the callback returned `content` (which is only valid for form mode).

**Cause:** URL-mode elicitation expects only `action: "accept" | "decline" | "cancel"` — no `content` field.

**Fix:**
```typescript
import { accept, decline, cancel, type OnElicitationCallback } from "mcp-use";

const onElicitation: OnElicitationCallback = async (params) => {
  if (params.mode === "url") {
    // Open URL for the user
    console.log(`Please visit: ${params.url}`);
    console.log(`Reason: ${params.message}`);
    const completed = await askUser("Did you complete the action?");

    // ✅ URL mode: action only, no content
    return { action: completed ? "accept" : "decline" };

    // ❌ Wrong: including content in URL mode
    // return { action: "accept", content: { result: "done" } };
  }

  // Form mode: content is required for accept
  return { action: "accept", content: formData };
};
```

**Action semantics:**
- `accept(data)` — user provided input; include `content` for form mode.
- `decline(reason?)` — user explicitly refused; the server should not retry.
- `cancel()` — user dismissed the dialog; the server may retry.
- `reject(reason?)` — alias of `decline`.

**Prevention:** Check `params.mode` and handle `"url"` vs `"form"` differently. URL mode never has `content`. Use `cancel()` for user dismissals rather than `decline()` so the server can distinguish the two.

---

## React Errors

---
### Error: useMcpClient must be used within McpClientProvider

**When:** Calling `useMcpClient()` or `useMcpServer()` throws a context error.

**Cause:** The component using the hook is not wrapped in a `McpClientProvider`.

**Fix:**
Wrap your app (or the relevant subtree) with the provider:
```typescript
import { McpClientProvider, useMcpClient, useMcpServer } from "mcp-use/react";

// ✅ Provider wraps components that use the hooks
function App() {
  return (
    <McpClientProvider defaultAutoProxyFallback={true}>
      <Dashboard />
    </McpClientProvider>
  );
}

function Dashboard() {
  const { addServer, servers } = useMcpClient(); // ✅ Works inside provider
  return <div>{servers.length} servers</div>;
}

// ❌ Wrong: hook outside provider
// function BrokenApp() {
//   const { servers } = useMcpClient(); // Throws!
//   return <McpClientProvider><div /></McpClientProvider>;
// }
```

**Prevention:** Place `McpClientProvider` at the top level of your component tree, typically in `App.tsx` or `layout.tsx`.

> **Breaking change (v1.20.1):** `McpUseProvider` (the older name) no longer includes `BrowserRouter`. If your app uses React Router, wrap it manually: `<BrowserRouter><McpClientProvider>...</McpClientProvider></BrowserRouter>`. Use `McpClientProvider` (the current name) instead of the deprecated `McpUseProvider`.

---
### Error: Server not found — useMcpServer with wrong ID

**When:** `useMcpServer("my-server")` returns undefined or throws because no server with that ID exists.

**Cause:** The server ID passed to `useMcpServer` does not match any ID used in `addServer()`.

**Fix:**
```typescript
import { McpClientProvider, useMcpClient, useMcpServer } from "mcp-use/react";

function MyComponent() {
  const { addServer } = useMcpClient();

  useEffect(() => {
    addServer("linear-server", {          // ← ID is "linear-server"
      url: "https://mcp.linear.app/mcp",
      name: "Linear",
    });
  }, [addServer]);

  return <ServerView />;
}

function ServerView() {
  const server = useMcpServer("linear-server"); // ✅ exact match
  // const server = useMcpServer("linear");     // ❌ wrong ID
  // const server = useMcpServer("Linear");     // ❌ case mismatch

  if (!server) return <div>Server not found</div>;
  return <div>{server.state}</div>;
}
```

**Prevention:** Use consistent server IDs. Define IDs as constants to avoid typos across components.

---
### State stuck on "discovering"

**When:** `mcp.state` remains `"discovering"` indefinitely — the connection never completes.

**Cause:** The server URL is unreachable, CORS is blocking the request, or the server is not returning a valid MCP response.

**Fix:**
1. Verify the server URL is correct and reachable:
```bash
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","id":1,"params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
```
2. Enable proxy fallback for CORS issues:
```typescript
import { useMcp } from "mcp-use/react";

const mcp = useMcp({
  url: "http://localhost:3000/mcp",
  autoProxyFallback: true,  // Falls back to proxy if CORS blocks
  autoRetry: 3,             // Retry up to 3 times
});
```
3. Check for network errors in browser DevTools (Console and Network tabs).

**Prevention:** Always enable `autoProxyFallback` during development. Add `autoRetry` for resilience.

`autoRetry` is a `useMcp` option (also available as a `McpServerOptions` field in `McpClientProvider`). It accepts `true`, `false`, or a number for the retry count.

---
### State stuck on "pending_auth"

**When:** `mcp.state` is `"pending_auth"` but the OAuth flow never starts.

**Cause:** The server requires OAuth, but `preventAutoAuth` is `true` (the default) and `authenticate()` was never called.

**Fix:**
Show an auth button and call `authenticate()`:
```typescript
import { useMcp } from "mcp-use/react";

function MyComponent() {
  const mcp = useMcp({
    url: "http://localhost:3000/mcp",
    callbackUrl: window.location.origin + "/oauth/callback",
    // preventAutoAuth: true is the default
  });

  if (mcp.state === "pending_auth") {
    return (
      <button onClick={mcp.authenticate}>
        Sign in with OAuth
      </button>
    );
  }

  if (mcp.state === "ready") {
    return <div>{mcp.tools.length} tools available</div>;
  }

  return <div>State: {mcp.state}</div>;
}
```

Or enable auto-auth (not recommended for most UIs):
```typescript
const mcp = useMcp({
  url: "http://localhost:3000/mcp",
  callbackUrl: window.location.origin + "/oauth/callback",
  preventAutoAuth: false,  // Auto-trigger OAuth popup
});
```

**Prevention:** Always handle the `"pending_auth"` state in your UI. Provide a clear authentication button.

---
### Error: State is "failed" with no clear error

**When:** `mcp.state` becomes `"failed"` but `mcp.error` is empty or generic.

**Cause:** The connection failed for a non-obvious reason — network issue, malformed server response, or proxy failure.

**Fix:**
Check the error property and enable RPC logging:
```typescript
import { McpClientProvider, useMcpClient } from "mcp-use/react";

// Enable RPC logging for debugging
<McpClientProvider enableRpcLogging={true}>
  <App />
</McpClientProvider>

// In your component:
function ServerStatus() {
  const { servers } = useMcpClient();

  return servers.map(s => (
    <div key={s.id}>
      {s.name}: {s.state}
      {s.error && <span className="error">{s.error}</span>}
      {s.state === "failed" && (
        <button onClick={s.retry}>Retry</button>
      )}
    </div>
  ));
}
```

**Prevention:** Always render the `error` property when state is `"failed"`. Enable `enableRpcLogging` during development.

---

## Logging Errors

---
### Server log messages not appearing

**When:** The server emits log messages (e.g., `ctx.log("info", "processing")`) but nothing shows in the client.

**Cause:** No `loggingCallback` was provided in `MCPClientOptions`.

**Fix:**
```typescript
import { MCPClient, types } from "mcp-use";

const client = new MCPClient(
  { mcpServers: { myServer: { url: "http://localhost:3000/mcp" } } },
  {
    loggingCallback: (logParams: types.LoggingMessageNotificationParams) => {
      // level: "debug" | "info" | "warning" | "error"
      console.log(`[${logParams.level.toUpperCase()}] ${logParams.message}`);
    },
  }
);
```

**Prevention:** Always configure `loggingCallback` in development to see server-side logs. Route to your structured logger (Winston, Pino, etc.) in production.

---

## Code Mode Errors

---
### Error: Code mode not enabled

**When:** `client.executeCode()` throws an error that code mode is not enabled.

**Cause:** The `codeMode` option was not set in `MCPClientOptions`.

**Fix:**
Enable code mode when creating the client:
```typescript
import { MCPClient } from "mcp-use";

// ✅ Simple: enable with default VM executor
const client = new MCPClient(
  { mcpServers: { myServer: { command: "npx", args: ["-y", "my-server"] } } },
  { codeMode: true }
);

// ✅ With configuration
const client2 = new MCPClient(
  { mcpServers: { myServer: { command: "npx", args: ["-y", "my-server"] } } },
  {
    codeMode: {
      enabled: true,
      executor: "vm",
      executorOptions: { timeoutMs: 60000 },
    },
  }
);

await client.createAllSessions();
const result = await client.executeCode("return 1 + 1");
```

**Prevention:** Set `codeMode: true` (or a `CodeModeConfig` object) when you need code execution. Code mode is only available in Node.js.

---
### Error: E2B API key required

**When:** Using the E2B executor throws an error about a missing API key.

**Cause:** `executor: "e2b"` requires an `apiKey` in `executorOptions`, but it was not provided.

**Fix:**
```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient(
  { mcpServers: { myServer: { url: "http://localhost:3000/mcp" } } },
  {
    codeMode: {
      enabled: true,
      executor: "e2b",
      executorOptions: {
        apiKey: process.env.E2B_API_KEY!, // ✅ Required for E2B
        timeoutMs: 300000,
      },
    },
  }
);
```

Also install the E2B dependency:
```bash
npm install @e2b/code-interpreter
# or
yarn add @e2b/code-interpreter
```

**Prevention:** Set `E2B_API_KEY` in your environment. Use the VM executor for local development (no API key needed).

---
### Error: Execution timeout — code exceeded timeoutMs

**When:** `executeCode()` throws a timeout error.

**Cause:** The executed code took longer than the configured `timeoutMs` (default: 30s for VM, 300s for E2B).

**Fix:**
1. Increase the timeout:
```typescript
const client = new MCPClient(config, {
  codeMode: {
    enabled: true,
    executor: "vm",
    executorOptions: {
      timeoutMs: 120000, // 2 minutes
    },
  },
});
```
2. Or pass a per-call timeout:
```typescript
const result = await client.executeCode(code, 120000); // 2 min for this call
```
3. Optimize the code to avoid unnecessary loops or blocking operations.

**Prevention:** Set `timeoutMs` appropriate for your workload. Break large operations into smaller code blocks.

---
### Error: Code mode not available in browser

**When:** Attempting to use `codeMode` from a `mcp-use/browser` import throws an error.

**Cause:** Code mode (VM and E2B executors) requires Node.js — it is not available in browser environments.

**Fix:**
Code execution must happen on the server side. Use a Node.js backend:
```typescript
// ❌ Browser: code mode not supported
import { MCPClient } from "mcp-use/browser";
const client = new MCPClient(config, { codeMode: true }); // Fails

// ✅ Node.js: code mode works
import { MCPClient } from "mcp-use";
const client = new MCPClient(config, { codeMode: true }); // Works
```

**Prevention:** Only use code mode in Node.js environments. If you need code execution from a browser, proxy through a Node.js backend.

---

## Import Errors

---
### Error: Cannot find module 'mcp-use/browser'

**When:** TypeScript compilation or runtime throws a module resolution error for `mcp-use/browser` (or `mcp-use/react`, `mcp-use/auth`).

**Cause:** TypeScript's `moduleResolution` is set to `"node"` (legacy) which doesn't support subpath exports. You need `"node16"` or `"bundler"`.

**Fix:**
Update `tsconfig.json`:
```json
{
  "compilerOptions": {
    "module": "node16",
    "moduleResolution": "node16",
    "target": "ES2022"
  }
}
```
Or for bundler-based projects (Next.js, Vite):
```json
{
  "compilerOptions": {
    "module": "esnext",
    "moduleResolution": "bundler"
  }
}
```

Then verify imports:
```typescript
// Node.js
import { MCPClient } from "mcp-use";

// Browser
import { MCPClient } from "mcp-use/browser";

// React
import { useMcp, McpClientProvider, useMcpClient, useMcpServer } from "mcp-use/react";

// Auth helpers
import { onMcpAuthorization } from "mcp-use/auth";

// Agent
import { MCPAgent } from "mcp-use/agent";
```

**Prevention:** Always set `"moduleResolution": "node16"` or `"bundler"` in new projects. Never use legacy `"node"` resolution with `mcp-use`.

---
### Error: MCPClient is not a constructor — CommonJS vs ESM

**When:** `new MCPClient(...)` throws `TypeError: MCPClient is not a constructor` or `MCPClient is not defined`.

**Cause:** Mismatch between CommonJS `require()` and ESM `import`. The `mcp-use` package uses ESM with subpath exports.

**Fix:**
1. **ESM (recommended):** Set `"type": "module"` in `package.json` and use `import`:
```typescript
// package.json: { "type": "module" }
import { MCPClient } from "mcp-use";
const client = new MCPClient(config);
```

2. **CommonJS:** Use dynamic `import()`:
```javascript
// package.json: no "type" field or "type": "commonjs"
async function main() {
  const { MCPClient } = await import("mcp-use");
  const client = new MCPClient(config);
}
main();
```

3. **Wrong:**
```javascript
// ❌ This won't work with ESM packages
const { MCPClient } = require("mcp-use");
```

**Prevention:** Use ESM (`import`/`export`) consistently. Set `"type": "module"` in `package.json`.

---
### Error: Wrong import path for environment

**When:** Using `import { MCPClient } from "mcp-use"` in a browser, or `import { MCPClient } from "mcp-use/browser"` in Node.js, causes missing features or runtime errors.

**Cause:** Each environment has its own entry point with different capabilities.

**Fix:**
Use the correct import for your environment:
```typescript
// Node.js (full features: STDIO, HTTP, code mode)
import { MCPClient } from "mcp-use";

// Browser (HTTP only, OAuth, no STDIO/code mode)
import { MCPClient } from "mcp-use/browser";

// React (hooks, provider, HTTP only)
import { useMcp, McpClientProvider, useMcpClient, useMcpServer } from "mcp-use/react";
import { LocalStorageProvider } from "mcp-use/react";

// Browser OAuth
import { BrowserOAuthClientProvider } from "mcp-use/browser";

// Auth callback (browser/React)
import { onMcpAuthorization } from "mcp-use/auth";

// Agent (Node.js only)
import { MCPAgent } from "mcp-use/agent";
```

**Prevention:** Refer to the environment matrix in the docs. Node.js = `mcp-use`, Browser = `mcp-use/browser`, React = `mcp-use/react`.

---

## TypeScript Configuration Errors

---
### Error: TypeScript compilation errors with mcp-use types

**When:** `tsc` reports type errors on `mcp-use` imports — `Cannot find type definition`, `has no exported member`, etc.

**Cause:** Wrong `tsconfig.json` settings, mismatched `@types/node`, or importing types from the wrong subpath.

**Fix:**
1. Set correct `tsconfig.json`:
```json
{
  "compilerOptions": {
    "module": "node16",
    "moduleResolution": "node16",
    "target": "ES2022",
    "strict": true,
    "esModuleInterop": true
  }
}
```
2. Import types correctly:
```typescript
import type {
  OnSamplingCallback,
  CreateMessageRequestParams,
  CreateMessageResult,
  OnElicitationCallback,
  OnNotificationCallback,
  Notification,
  Root,
} from "mcp-use";

// For elicitation types from the SDK:
import type {
  ElicitRequestFormParams,
  ElicitRequestURLParams,
  ElicitResult,
} from "@modelcontextprotocol/sdk/types.js";
```
3. Ensure `@types/node` matches your Node.js version:
```bash
npm install -D @types/node@22  # for Node 22.x
```

**Prevention:** Always set `"moduleResolution": "node16"` or `"bundler"` in new projects. Use `import type` for type-only imports.

---

## Miscellaneous Errors

---
### Error: Config file not found — loadConfigFile

**When:** `loadConfigFile("path/to/config.json")` throws a file-not-found error.

**Cause:** The config file path is wrong, the file doesn't exist, or the file is not valid JSON.

**Fix:**
```typescript
import { MCPClient, loadConfigFile } from "mcp-use";
import { existsSync } from "fs";

const configPath = "./mcp-config.json";
if (!existsSync(configPath)) {
  console.error(`Config file not found: ${configPath}`);
  process.exit(1);
}

const config = await loadConfigFile(configPath);
const client = new MCPClient(config);
```

Ensure the config file is valid:
```json
{
  "mcpServers": {
    "my-server": {
      "url": "http://localhost:3000/mcp"
    }
  }
}
```

**Prevention:** Validate config file existence at startup. Use `new MCPClient(config)` with an inline config object when not loading from a file.

---
### Error: closeAllSessions not called — resource leak

**When:** Node.js process hangs on exit, or you see STDIO child processes still running after your script ends.

**Cause:** `closeAllSessions()` was never called — STDIO child processes and HTTP connections remain open.

**Fix:**
Always clean up sessions:
```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient(config);
try {
  await client.createAllSessions();
  const session = client.getSession("myServer");
  const result = await session.callTool("my-tool", {});
  console.log(result);
} finally {
  await client.closeAllSessions(); // ✅ Always clean up
}
```

For code mode clients, use `close()`:
```typescript
const client = new MCPClient(config, { codeMode: true });
try {
  await client.createAllSessions();
  await client.executeCode("return 42");
} finally {
  await client.close(); // Cleans up sessions + executor
}
```

**Prevention:** Always call `closeAllSessions()` (or `close()` for code mode) in a `finally` block or process exit handler.

---

## Quick Diagnostic Checklist

```
Client not working?
├── Connection failed?
│   ├── Check URL is correct (include /mcp path)
│   ├── Check server is running: curl http://localhost:3000/mcp
│   ├── Check CORS: enable autoProxyFallback for browser
│   ├── Check transport: MCP uses HTTP/SSE, not WebSocket
│   └── Check auth: provide headers, authProvider, or callbackUrl
│
├── Tools not listing?
│   ├── Check createSession/createAllSessions was awaited
│   ├── Check session state is "ready" (React: mcp.state)
│   ├── Check server name matches exactly (case-sensitive)
│   └── Check server exposes tools (test with CLI: npx mcp-use client tools list)
│
├── Tool not found?
│   ├── Check tool name matches exactly (call listTools first)
│   ├── Check arguments match inputSchema (inspect with tools describe)
│   ├── Check timeout is sufficient for slow tools
│   └── Check server capabilities for optional methods (completions)
│
├── Sampling not working?
│   ├── Check onSampling callback is configured
│   ├── Check callback returns valid CreateMessageResult
│   ├── Check role is "assistant", content has type, model is set
│   └── Use accept(...) for quick testing
│
├── Elicitation not working?
│   ├── Check onElicitation callback is configured
│   ├── Check form data matches requestedSchema (use validate())
│   ├── Check URL mode returns action only (no content)
│   └── Use accept(...) for quick testing
│
├── Auth not working?
│   ├── Check callbackUrl matches OAuth redirect URI
│   ├── Check authProvider config (clientId, URLs)
│   ├── Check preventAutoAuth — call authenticate() manually
│   └── For bearer tokens: check headers.Authorization format
│
├── React not rendering?
│   ├── Check McpClientProvider wraps component tree
│   ├── Check state before accessing tools (gate on "ready")
│   ├── Check server ID matches addServer() call exactly
│   ├── Handle "pending_auth" state with authenticate() button
│   └── Enable enableRpcLogging for debugging
│
├── Server logs not visible?
│   ├── Check loggingCallback is configured in MCPClientOptions
│   └── Callback receives types.LoggingMessageNotificationParams (level + message)
│
├── Code mode failing?
│   ├── Check codeMode is enabled in MCPClientOptions
│   ├── Check E2B API key if using e2b executor
│   ├── Check timeoutMs is sufficient
│   └── Code mode is Node.js only (not browser/React)
│
└── Import errors?
    ├── Check moduleResolution: "node16" or "bundler"
    ├── Check import path matches environment (mcp-use vs mcp-use/browser)
    ├── Check package.json "type": "module" for ESM
    └── Use import (not require) for mcp-use packages
```

| Symptom | First Check |
|---|---|
| Import errors | `"moduleResolution": "node16"` in tsconfig? Correct subpath import? |
| Connection refused | Server running? URL correct with `/mcp` path? |
| CORS blocked | `autoProxyFallback` enabled? Server CORS configured? |
| Tools empty | `createAllSessions()` awaited? Server name matches? |
| Tool not found | Exact name match? Call `listTools()` first |
| Invalid arguments | Check `inputSchema` — types and required fields |
| Timeout | Increase `timeout` in callTool options |
| Method not found (-32601) | Check `serverCapabilities` — server may not support feature |
| No sampling handler | `onSampling` callback configured? |
| No elicitation handler | `onElicitation` callback configured? |
| Validation failed | Use `validate(params, data)` before `accept()` |
| React context error | `McpClientProvider` wrapping component tree? |
| Server not found (React) | `useMcpServer` ID matches `addServer` ID? |
| Stuck on discovering | URL reachable? CORS? Check DevTools Network tab |
| Stuck on pending_auth | Call `mcp.authenticate()` — it's manual by default |
| Code mode not enabled | `codeMode: true` in MCPClientOptions? |
| Server logs missing | `loggingCallback` configured in MCPClientOptions? |
| E2B API key missing | `E2B_API_KEY` in env? `executorOptions.apiKey` set? |
| Process hangs on exit | `closeAllSessions()` called in finally block? Code mode: use `close()` instead |
| 404 after server restart | Client auto-recovers; check mcp-use version ≥1.21.1 (latest: v1.21.5) |
| Auth 401 | Token expired? Headers correct? OAuth config complete? |
