# Tools

Complete reference for discovering and calling MCP tools — listing, execution, timeouts, and error handling.

---

## Understanding Tools

Tools are executable functions exposed by MCP servers. Each tool has a name, a description, and a JSON Schema that defines its input parameters. The `mcp-use` client library gives you a type-safe, asynchronous interface for discovering and invoking these tools.

Key characteristics of MCP tools:

- **Schema-based validation** — Every tool declares its accepted parameters via JSON Schema. The client validates inputs before sending them to the server.
- **Type-safe execution** — TypeScript generics let you constrain parameter and return types at compile time.
- **Asynchronous operation** — All tool calls return Promises. Long-running tools support progress notifications and cancellation.
- **Structured error handling** — Results carry an `isError` flag so you can distinguish success from failure without relying on thrown exceptions.

---

## Listing Tools

Use `session.listTools()` to retrieve every tool the server exposes. Call this after the session is fully connected.

### Node.js

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    myServer: { url: "http://localhost:3000/mcp" }
  }
});

await client.createAllSessions();
const session = client.requireSession("myServer");

// listTools() always returns fresh data from the server
const tools = await session.listTools();

for (const tool of tools) {
  console.log(`${tool.name}: ${tool.description}`);
  console.log(`  Input schema: ${JSON.stringify(tool.inputSchema)}`);
}

await client.closeAllSessions();
```

### Browser

```typescript
import { MCPClient } from "mcp-use/browser";

const client = new MCPClient({
  mcpServers: {
    myServer: { url: "http://localhost:3000/mcp" }
  }
});

await client.createAllSessions();
const session = client.requireSession("myServer");

// listTools() always returns fresh data from the server
const tools = await session.listTools();
console.log(`Server exposes ${tools.length} tool(s)`);

await client.closeAllSessions();
```

### Tool Object Shape

Each element returned by `listTools()` has the following structure:

| Field | Type | Description |
|---|---|---|
| `name` | `string` | Unique identifier for the tool within this server |
| `description` | `string` | Human-readable summary of what the tool does |
| `inputSchema` | `object` | JSON Schema describing accepted parameters |

---

## Calling Tools

Pass the tool name and a parameter object to `session.callTool()`. The client serializes the arguments, sends the request, and returns a result that may include `content`, `structuredContent`, and `_meta`.

For broad interoperability, prefer `content` as the default human/model-facing answer, but preserve `structuredContent` when it exists. Some MCP clients and adapters are content-first, some are structured-first, and some drop one surface. Client code should not assume `content[0].text` is the only successful payload.

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    github: { url: "http://localhost:3000/mcp" }
  }
});

await client.createAllSessions();
const session = client.requireSession("github");

const result = await session.callTool("list_pull_requests", {
  owner: "facebook",
  repo: "react",
  state: "open"
});

if (result.isError) {
  // On error, content[0] typically holds the error message as text
  const errorMsg = result.content[0]?.type === "text" ? result.content[0].text : JSON.stringify(result.content);
  console.error("Tool call failed:", errorMsg);
} else {
  for (const item of result.content) {
    if (item.type === "text") console.log("Pull requests:", item.text);
  }
}

await client.closeAllSessions();
```

### CallToolResult Interface

Every call returns a `CallToolResult` (from `@modelcontextprotocol/sdk/types.js`):

```typescript
interface CallToolResult {
  content: Array<TextContent | ImageContent | EmbeddedResource>;
  structuredContent?: Record<string, unknown>;
  _meta?: Record<string, unknown>;
  isError?: boolean; // true when the tool reported an error (may be absent on success)
}

// Content item types:
interface TextContent  { type: "text";  text: string; }
interface ImageContent { type: "image"; data: string; mimeType: string; }
interface EmbeddedResource { type: "resource"; resource: { uri: string; mimeType?: string; text?: string; blob?: string }; }
```

| Field | Type | Description |
|---|---|---|
| `content` | `Array<TextContent \| ImageContent \| EmbeddedResource>` | Array of content items. Text responses appear as `{ type: "text", text: "..." }` entries. |
| `structuredContent` | `Record<string, unknown> \| undefined` | Typed JSON result when the server provides structured output. Treat as model-visible unless the exact host proves otherwise. |
| `_meta` | `Record<string, unknown> \| undefined` | Private/client-only metadata. Do not forward to the model by default. |
| `isError` | `boolean \| undefined` | Present and `true` when the tool executed but reported an error. Absent or `false` on success. |

Always inspect `isError` before consuming `content`. When `isError` is `true`, content items typically carry a text error message.

When normalizing a result for an LLM or UI, keep both compatible surfaces available:

```typescript
const result = await session.callTool("search_web", { query: "MCP protocol" });

const textContent = result.content
  .filter((item) => item.type === "text")
  .map((item) => item.text)
  .join("\n");

const normalized = {
  text: textContent || JSON.stringify(result.structuredContent ?? result.content),
  structuredContent: result.structuredContent,
};
```

```typescript
const result = await session.callTool("search_web", { query: "MCP protocol" });

// content is always an array — iterate and check type
for (const item of result.content) {
  if (item.type === "text") {
    console.log(`Text: ${item.text}`);
  } else if (item.type === "image") {
    console.log(`Image (${item.mimeType}): ${item.data.slice(0, 20)}...`);
  }
}
```

---

## Timeout Configuration

The default timeout for tool calls is **60 seconds**. For long-running operations like data processing or external API calls, configure appropriate timeout values explicitly.

Pass an options object as the third argument to `callTool()`.

```typescript
const abortController = new AbortController();

const result = await session.callTool(
  "generate_report",
  { format: "pdf", datasetId: "ds-42" },
  {
    timeout: 60000,                    // Request timeout in ms (default: 60000)
    maxTotalTimeout: 300000,           // Maximum total time in ms
    resetTimeoutOnProgress: true,      // Reset timeout on progress notification
    signal: abortController.signal     // AbortSignal to cancel mid-flight
  }
);
```

### Timeout Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `timeout` | `number` | `60000` | Per-request timeout in milliseconds. The timer starts when the request is sent. |
| `maxTotalTimeout` | `number` | `undefined` | Absolute ceiling in milliseconds. Even if progress resets keep extending the window, the call aborts after this duration. |
| `resetTimeoutOnProgress` | `boolean` | `false` | When `true`, every progress notification from the server resets the `timeout` counter back to zero. Useful for tools that stream incremental updates. |
| `signal` | `AbortSignal` | `undefined` | An `AbortSignal` that lets you cancel the call programmatically from outside. |

### How Timeouts Interact

```
┌──────────────────────────────────────────────────────────────┐
│ maxTotalTimeout (300 000 ms)                                 │
│ ┌──────────┐ progress ┌──────────┐ progress ┌──────────┐    │
│ │ timeout  │ ──────►  │ timeout  │ ──────►  │ timeout  │    │
│ │ 60 000ms │  reset   │ 60 000ms │  reset   │ 60 000ms │    │
│ └──────────┘          └──────────┘          └──────────┘    │
└──────────────────────────────────────────────────────────────┘
```

When `resetTimeoutOnProgress` is `true`, the `timeout` window restarts each time the server sends a progress notification. The `maxTotalTimeout` acts as a hard cap — once hit, the call aborts regardless of progress resets.

---

## Progress Notifications

Some tools emit progress notifications while they work. These notifications carry a progress token and optional descriptive text. When combined with `resetTimeoutOnProgress: true`, they keep the call alive as long as the server is making forward progress.

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    processor: { url: "http://localhost:4000/mcp" }
  }
});

await client.createAllSessions();
const session = client.requireSession("processor");

// The tool sends progress notifications every 10 seconds while indexing.
// resetTimeoutOnProgress keeps the call alive as long as notifications arrive.
const result = await session.callTool(
  "index_repository",
  { repoUrl: "https://github.com/org/large-repo" },
  {
    timeout: 30000,
    maxTotalTimeout: 600000,
    resetTimeoutOnProgress: true
  }
);

if (result.isError) {
  const errText = result.content[0]?.type === "text" ? result.content[0].text : JSON.stringify(result.content);
  console.error("Indexing failed:", errText);
} else {
  for (const item of result.content) {
    if (item.type === "text") console.log("Index complete:", item.text);
  }
}
```

---

## Cancelling a Tool Call

Use an `AbortController` to cancel a tool call from outside — for example, when a user clicks "Cancel" or a parent operation times out.

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    analytics: { url: "http://localhost:5000/mcp" }
  }
});

await client.createAllSessions();
const session = client.requireSession("analytics");

const abortController = new AbortController();

// Cancel after 10 seconds if the user loses patience
const cancelTimer = setTimeout(() => abortController.abort(), 10000);

try {
  const result = await session.callTool(
    "run_query",
    { sql: "SELECT * FROM events WHERE ts > now() - interval '1 hour'" },
    { signal: abortController.signal }
  );
  clearTimeout(cancelTimer);
  for (const item of result.content) {
    if (item.type === "text") console.log("Query result:", item.text);
  }
} catch (err) {
  if (err instanceof Error && err.name === "AbortError") {
    console.log("Tool call was cancelled by the user.");
  } else {
    throw err;
  }
}
```

---

## Batch Tool Calling

When you need results from multiple independent tools, fire them in parallel with `Promise.all`. Each call runs on its own request; the server processes them concurrently.

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    github: { url: "http://localhost:3000/mcp" }
  }
});

await client.createAllSessions();
const session = client.requireSession("github");

const [prs, issues, branches] = await Promise.all([
  session.callTool("list_pull_requests", { owner: "org", repo: "app", state: "open" }),
  session.callTool("list_issues", { owner: "org", repo: "app", state: "open" }),
  session.callTool("list_branches", { owner: "org", repo: "app" })
]);

// Check each result individually — content is always an array
for (const [label, result] of [["PRs", prs], ["Issues", issues], ["Branches", branches]] as const) {
  if (result.isError) {
    const errText = result.content[0]?.type === "text" ? result.content[0].text : JSON.stringify(result.content);
    console.error(`${label} fetch failed:`, errText);
  } else {
    for (const item of result.content) {
      if (item.type === "text") console.log(`${label}:`, item.text);
    }
  }
}
```

### Batch with Per-Call Timeouts

```typescript
const results = await Promise.all([
  session.callTool("fast_tool", { id: 1 }, { timeout: 5000 }),
  session.callTool("slow_tool", { id: 2 }, { timeout: 120000, resetTimeoutOnProgress: true }),
  session.callTool("medium_tool", { id: 3 }, { timeout: 30000 })
]);
```

---

## Tool Discovery with Code Mode

When code mode is enabled, tools are exposed as callable functions namespaced by server name. This gives you a direct, ergonomic API without manual `callTool` invocations.

### Direct Tool Calls

```typescript
// Call tools directly as serverName.toolName(args)
const prs = await github.list_pull_requests({ owner: "facebook", repo: "react" });
const files = await filesystem.list_directory({ path: "/data" });
const weather = await weather_api.get_forecast({ city: "Istanbul", days: 7 });
```

### Searching Available Tools

The `search_tools` function lets you discover what tools are available across all connected servers. It accepts two optional parameters: a query string and a detail level.

```typescript
// List all tools across all servers (names only)
const allResult = await search_tools();

// Filter by keyword
const githubResult = await search_tools("github");

// Control detail level
const namesResult = await search_tools("", "names");
const descsResult = await search_tools("", "descriptions");
const fullResult = await search_tools("github", "full");
```

### search_tools Detail Levels

| Detail Level | Output | Use When |
|---|---|---|
| `"names"` | Tool names only | You need a quick inventory of available tools |
| `"descriptions"` | Names + short descriptions | You need to understand what each tool does |
| `"full"` | Names + descriptions + full input schemas | You need to know exact parameter shapes before calling |

### Code Mode vs. Session Mode

| Aspect | Code Mode | Session Mode |
|---|---|---|
| Syntax | `server.tool(args)` | `session.callTool("tool", args, opts)` |
| Timeout control | Default only | Full options object |
| Discovery | `search_tools()` | `session.listTools()` |
| Best for | Quick scripting, AI agents | Production apps needing fine-grained control |

---

## Error Handling Patterns

### Basic Error Check

```typescript
const result = await session.callTool("create_file", {
  path: "/tmp/output.txt",
  content: "Hello, world!"
});

if (result.isError) {
  // content[0] typically holds the error as a TextContent item
  const errText = result.content[0]?.type === "text" ? result.content[0].text : JSON.stringify(result.content);
  console.error("Tool reported an error:", errText);
  // Handle gracefully — retry, fallback, or report to user
} else {
  for (const item of result.content) {
    if (item.type === "text") console.log("File created:", item.text);
  }
}
```

### Catching Transport and Protocol Errors

Tool calls can fail at two layers: the **transport** (network errors, timeouts) and the **tool** (the tool ran but returned `isError: true`). Handle both.

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    myServer: { url: "http://localhost:3000/mcp" }
  }
});

await client.createAllSessions();
const session = client.requireSession("myServer"); // throws if not found

try {
  const result = await session.callTool("risky_operation", { id: 42 });

  if (result.isError) {
    // Tool-level error — the server processed the request but the tool failed
    const errText = result.content[0]?.type === "text" ? result.content[0].text : JSON.stringify(result.content);
    console.error("Tool error:", errText);
  } else {
    for (const item of result.content) {
      if (item.type === "text") console.log("Success:", item.text);
    }
  }
} catch (err) {
  // Transport-level error — network failure, timeout, abort, protocol violation
  if (err instanceof Error) {
    if (err.name === "AbortError") {
      console.error("Call was cancelled.");
    } else {
      console.error("Transport error:", err.message);
    }
  }
}
```

### Retry Pattern

```typescript
async function callWithRetry(
  session: any,
  toolName: string,
  args: Record<string, unknown>,
  maxRetries = 3,
  delayMs = 1000
): Promise<any> {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const result = await session.callTool(toolName, args, { timeout: 30000 });

      if (!result.isError) {
        return result;
      }

      const errMsg = result.content[0]?.type === "text" ? result.content[0].text : JSON.stringify(result.content);
      console.warn(`Attempt ${attempt}/${maxRetries} — tool error: ${errMsg}`);
    } catch (err) {
      console.warn(`Attempt ${attempt}/${maxRetries} — transport error: ${err}`);
    }

    if (attempt < maxRetries) {
      await new Promise((resolve) => setTimeout(resolve, delayMs * attempt));
    }
  }

  throw new Error(`Tool "${toolName}" failed after ${maxRetries} attempts`);
}

// Usage
const result = await callWithRetry(session, "flaky_api_call", { query: "data" });
for (const item of result.content) {
  if (item.type === "text") console.log(item.text);
}
```

---

## React Hook Usage

The `useMcp` hook manages connection lifecycle and exposes tool calling directly in React components.

```typescript
import { useMcp } from "mcp-use/react";

function ToolExplorer() {
  const mcp = useMcp({ url: "http://localhost:3000/mcp" });

  if (mcp.state === "discovering") return <div>Connecting to server...</div>;
  if (mcp.state !== "ready") return <div>Not ready: {mcp.state}</div>;

  const handleListTools = () => {
    for (const tool of mcp.tools) {
      console.log(`${tool.name}: ${tool.description}`);
    }
  };

  const handleCallTool = async () => {
    const result = await mcp.callTool("get_weather", { city: "Istanbul" });
    if (result.isError) {
      const errText = result.content[0]?.type === "text" ? result.content[0].text : JSON.stringify(result.content);
      console.error("Error:", errText);
    } else {
      for (const item of result.content) {
        if (item.type === "text") console.log("Weather:", item.text);
      }
    }
  };

  return (
    <div>
      <p>{mcp.tools.length} tools available</p>
      <button onClick={handleListTools}>List Tools</button>
      <button onClick={handleCallTool}>Get Weather</button>
    </div>
  );
}
```

### useMcpServer with Timeout Options

When using `useMcpServer` for per-server connections, pass timeout options to `callTool`:

```typescript
import { useMcpServer } from "mcp-use/react";

function EmailSender() {
  const server = useMcpServer({ url: "http://localhost:6000/mcp" });

  const handleSend = async () => {
    if (server.state !== "ready") return;

    const result = await server.callTool(
      "send-email",
      {
        to: "user@example.com",
        subject: "Report Ready",
        body: "Your report has been generated."
      },
      {
        timeout: 300000,
        resetTimeoutOnProgress: true,
        maxTotalTimeout: 600000
      }
    );

    if (result.isError) {
      const errText = result.content[0]?.type === "text" ? result.content[0].text : JSON.stringify(result.content);
      alert("Failed to send email: " + errText);
    } else {
      alert("Email sent successfully!");
    }
  };

  return (
    <button onClick={handleSend} disabled={server.state !== "ready"}>
      Send Report Email
    </button>
  );
}
```

---

## Common Mistakes

### ❌ BAD: Not checking `isError` on results

```typescript
const result = await session.callTool("fetch_data", { id: 1 });
// Directly using content without checking — will process error payloads as data
processData(result.content); // content is an array of content items, not raw data
```

### ✅ GOOD: Always check `isError` and iterate `content` array

```typescript
const result = await session.callTool("fetch_data", { id: 1 });
if (result.isError) {
  const errText = result.content[0]?.type === "text" ? result.content[0].text : JSON.stringify(result.content);
  console.error("Fetch failed:", errText);
  return;
}
// content is always an array of TextContent | ImageContent | EmbeddedResource
for (const item of result.content) {
  if (item.type === "text") processData(item.text);
}
```

---

### ❌ BAD: No timeout on long-running tools

```typescript
// This call could hang indefinitely if the server stalls
const result = await session.callTool("export_database", { format: "csv" });
```

### ✅ GOOD: Setting appropriate timeouts

```typescript
const result = await session.callTool(
  "export_database",
  { format: "csv" },
  {
    timeout: 120000,
    maxTotalTimeout: 600000,
    resetTimeoutOnProgress: true
  }
);
```

---

### ❌ BAD: Calling tools before session is ready

```typescript
const client = new MCPClient({
  mcpServers: { myServer: { url: "http://localhost:3000/mcp" } }
});
// Session not created yet — getSession returns null, calling callTool on null throws
const session = client.getSession("myServer"); // null
const result = await session!.callTool("my_tool", {}); // TypeError
```

### ✅ GOOD: Create sessions before accessing them

```typescript
const client = new MCPClient({
  mcpServers: { myServer: { url: "http://localhost:3000/mcp" } }
});
await client.createAllSessions();

// requireSession throws a descriptive error if the session is missing
const session = client.requireSession("myServer");

// Now the session is connected and ready
const result = await session.callTool("my_tool", {});
```

---

### ❌ BAD: Ignoring abort cleanup

```typescript
const controller = new AbortController();
setTimeout(() => controller.abort(), 5000);

// No try/catch — unhandled AbortError crashes the process
const result = await session.callTool("slow_tool", {}, { signal: controller.signal });
```

### ✅ GOOD: Handling abort errors gracefully

```typescript
const controller = new AbortController();
setTimeout(() => controller.abort(), 5000);

try {
  const result = await session.callTool("slow_tool", {}, { signal: controller.signal });
  if (result.isError) {
    const errText = result.content[0]?.type === "text" ? result.content[0].text : JSON.stringify(result.content);
    console.error("Tool error:", errText);
  } else {
    for (const item of result.content) {
      if (item.type === "text") console.log("Result:", item.text);
    }
  }
} catch (err) {
  if (err instanceof Error && err.name === "AbortError") {
    console.log("Call cancelled — cleaning up.");
  } else {
    throw err;
  }
}
```

---

### ❌ BAD: Sequential calls when tools are independent

```typescript
const prs = await session.callTool("list_prs", { repo: "app" });
const issues = await session.callTool("list_issues", { repo: "app" });
const commits = await session.callTool("list_commits", { repo: "app" });
// Total time = sum of all three calls
```

### ✅ GOOD: Parallel calls for independent tools

```typescript
const [prs, issues, commits] = await Promise.all([
  session.callTool("list_prs", { repo: "app" }),
  session.callTool("list_issues", { repo: "app" }),
  session.callTool("list_commits", { repo: "app" })
]);
// Total time = max of the three calls
```

---

## Quick Reference

### Minimal Tool Call (5 lines)

```typescript
import { MCPClient } from "mcp-use";
const client = new MCPClient({ mcpServers: { s: { url: "http://localhost:3000/mcp" } } });
await client.createAllSessions();
const result = await client.requireSession("s").callTool("ping", {});
console.log(result.content[0]?.type === "text" ? result.content[0].text : result.content);
```

### Full Tool Call with All Options

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    myServer: { url: "http://localhost:3000/mcp" }
  }
});

await client.createAllSessions();
const session = client.requireSession("myServer");

const controller = new AbortController();

try {
  const result = await session.callTool(
    "complex_operation",
    { input: "data", options: { verbose: true } },
    {
      timeout: 60000,
      maxTotalTimeout: 300000,
      resetTimeoutOnProgress: true,
      signal: controller.signal
    }
  );

  if (result.isError) {
    const errText = result.content[0]?.type === "text" ? result.content[0].text : JSON.stringify(result.content);
    console.error("Tool error:", errText);
  } else {
    for (const item of result.content) {
      if (item.type === "text") console.log("Success:", item.text);
    }
  }
} catch (err) {
  if (err instanceof Error && err.name === "AbortError") {
    console.log("Cancelled.");
  } else {
    console.error("Transport error:", err);
  }
}
```

---

## Checklist

Before calling any tool, verify:

1. **Session exists** — `createAllSessions()` or `createSession()` has completed.
2. **Tool exists** — Use `listTools()` or `search_tools()` to confirm the tool name.
3. **Parameters match schema** — Check `inputSchema` from `listTools()` for required fields.
4. **Timeout is set** — Never rely on defaults for tools that may take more than a few seconds.
5. **`isError` is checked** — Every `callTool` result must be inspected before the content is used.
6. **Abort is handled** — If you pass a `signal`, wrap the call in try/catch for `AbortError`.
