---
name: build-mcp-use-client
description: Use skill if you are building MCP client applications with the mcp-use TypeScript SDK — MCPClient, sessions, tools, resources, React hooks, code mode, and authentication.
---

# Build MCP Use Client

Build production-grade MCP client applications with the `mcp-use` TypeScript library (v1.21+, Node 18+ supported, Node 22 LTS recommended). The library provides `MCPClient` for multi-server management, `MCPSession` for per-server protocol operations, `useMcp`/`McpClientProvider` React hooks, CLI client, code mode, and environment-specific entry points (`mcp-use`, `mcp-use/browser`, `mcp-use/react`).

> **Building an MCP server?** Use `build-mcp-use-server`. **Building an AI agent?** Use `build-mcp-use-agent`. **Building widget-based MCP Apps?** Use `build-mcp-use-apps-widgets`.

---

## Behavioral flow — what to do when this skill is invoked

This is the decision procedure you MUST follow every time.

### Step 1 — Detect what exists

Run `tree -L 3` (or `ls -R` if tree is unavailable) at the actual project root you will edit. If the user named a package, fixture, or app subdirectory, scan that path instead of the repo root. Look for signs of an existing mcp-use client:

- `package.json` with `"mcp-use"` as a dependency
- Files importing from `"mcp-use"`, `"mcp-use/browser"`, or `"mcp-use/react"`
- `MCPClient` constructor calls
- `useMcp` / `McpClientProvider` usage
- `session.callTool()`, `session.readResource()`, or similar session method calls

### Step 2A — Existing mcp-use client found

When there IS an existing client implementation, launch four parallel subagents to explore the codebase and cross-reference with the reference files:

If the runtime cannot launch subagents, do the same audits sequentially yourself and keep the same four coverage areas.
When you do use subagents, write each prompt as a bounded audit brief: why the audit matters, the desired end-state, hard constraints, and binary deliverables.

**Subagent 1 — Client configuration audit**
Explore constructor options, server entries, transport types, `loadConfigFile` / `MCPClient.fromConfigFile` / `MCPClient.fromDict` usage, environment-specific imports. Cross-reference with `references/guides/client-configuration.md` and `references/guides/environments.md`. Surface: what is correctly configured, what violates best practices, what is missing.

**Subagent 2 — Tool, resource, and prompt usage audit**
Explore how tools are listed/called, how tool results handle both `content` and `structuredContent`, how resources are read, how prompts are retrieved, completion usage, timeout/abort config. Cross-reference with `references/guides/tools.md`, `references/guides/resources.md`, `references/guides/prompts.md`, and `references/guides/completion.md`. Surface: correct patterns, missing error handling, timeout gaps, and clients that accidentally drop one result surface.

**Subagent 3 — Callbacks and lifecycle audit**
Explore sampling callbacks, elicitation callbacks, notification handlers, logging setup, session cleanup, reconnection config. Cross-reference with `references/guides/sampling.md`, `references/guides/elicitation.md`, `references/guides/notifications-and-logging.md`, and `references/guides/authentication.md`. Surface: missing callbacks, wrong precedence, cleanup gaps.

**Subagent 4 — React integration audit** (only if React hooks are used)
Explore `useMcp` options, `McpClientProvider` props, state handling, `useMcpClient`/`useMcpServer` usage, proxy config, persistence. Cross-reference with `references/guides/usemcp-and-react.md`. Surface: missing state guards, wrong prop names, reconnection gaps.

After all subagents report back:
1. Synthesize findings into a prioritized improvement plan
2. Apply improvements directly — fix anti-patterns, add missing callbacks, correct imports
3. Review final result against `references/patterns/anti-patterns.md`
4. Only ask the user if something is genuinely ambiguous (e.g., which LLM provider for sampling)

### Step 2B — No existing mcp-use client found

Check context: is there an existing app that needs MCP client integration?

**If context exists** (e.g., a React app, a Node CLI, a backend service): infer what is needed and build the client integration directly using the reference files.

Pick the server target explicitly before coding:
- If the repo already contains a real MCP server, connect to that server and discover its actual tool/resource names with `listTools()`, `listResources()`, and `listPrompts()`.
- If the task is only about client mechanics and no domain server exists yet, use `@modelcontextprotocol/server-everything` as a smoke-test server and discover the real tool names before calling them.
- If the request depends on a domain-specific tool such as `calculator`, `search-products`, or repo-specific commands and no matching server exists, stop and add/build that server first instead of inventing tool names. Route to `build-mcp-use-server` when needed.

**If no context exists**: ask up to 10 questions, each with 5+ numbered options:

1. **What environment?** (1) Node.js CLI, (2) Node.js backend service, (3) Browser app, (4) React app, (5) CLI scripting with `npx mcp-use client`
2. **How many MCP servers?** (1) Single server, (2) Multiple servers
3. **Transport type?** (1) STDIO for local servers, (2) HTTP for remote servers, (3) Both STDIO and HTTP
4. **Need authentication?** (1) Bearer token, (2) OAuth 2.1, (3) Custom headers, (4) None
5. **Need React hooks?** (1) `useMcp` for single server, (2) `McpClientProvider` for multi-server, (3) No React
6. **Need sampling/elicitation callbacks?** (1) Sampling only, (2) Elicitation only, (3) Both, (4) Neither
7. **Need code mode?** (1) VM executor (local), (2) E2B executor (cloud sandbox), (3) Custom executor, (4) No
8. **Session persistence needs?** (1) In-memory only, (2) LocalStorage (React), (3) Custom StorageProvider, (4) None
9. **Need notifications/logging?** (1) Tool/resource list changes, (2) Custom notifications, (3) Server log streaming, (4) None
10. **Production hardening?** (1) Auto-reconnect + health checks, (2) Basic error handling only, (3) Full production setup

Then build the client using answers + reference files.

---

## Reference routing — read these when you need depth

Each trigger below tells you exactly when and why to open a reference file. Read them with curiosity — they contain the full type signatures, edge cases, and validated patterns that this summary intentionally compresses.

**Getting started and environment setup:**

- If you are starting from scratch and need the minimal happy-path to a working client — read `references/guides/quick-start.md`. It walks through install, first connection, first tool call, and first resource read.
- If you are choosing between Node.js, Browser, React, or CLI and need to know what works where — read `references/guides/environments.md`. It has the full feature matrix (STDIO, HTTP, OAuth, code mode, persistence) and the correct import paths for each environment.

**Client configuration and connections:**

- If you are connecting to servers, choosing between STDIO and HTTP, setting up multi-server configs, or wiring per-server callbacks — read `references/guides/client-configuration.md`. It has the full `MCPClientConfigShape`, discriminated union types for STDIO vs HTTP entries, `loadConfigFile`, `MCPClient.fromConfigFile`, `MCPClient.fromDict`, `ClientInfo` shape, and per-server callback overrides.
- If you are managing multiple servers with lazy loading, composed capabilities, or `disallowedTools` filtering — read `references/guides/server-manager.md`. It covers `useServerManager` on `MCPAgent`, environment variable substitution in config JSON, and dynamic server addition.

**Core protocol operations:**

- If you are listing or calling tools, setting timeouts, using AbortSignal, or handling `CallToolResult` — read `references/guides/tools.md`. It has `CallToolOptions`, `maxTotalTimeout`, `resetTimeoutOnProgress`, result-surface handling for `content` / `structuredContent` / `_meta`, and the `isError` handling pattern.
- If you are reading resources, working with resource templates, or handling binary vs text content — read `references/guides/resources.md`. It has `listResources()`, `readResource()`, `ResourceContent[]` shape, and MIME type handling.
- If you are retrieving prompt templates with arguments or building multi-message prompt flows — read `references/guides/prompts.md`. It has `listPrompts()`, `getPrompt()`, `PromptResult` structure, and argument passing.
- If you are implementing autocomplete for prompt arguments or resource template URIs — read `references/guides/completion.md`. It has `session.complete()`, `CompleteRequestParams`, debouncing strategy, and capability checking.

**Callbacks and server interactions:**

- If a server uses `ctx.sample()` and you need to route LLM calls — read `references/guides/sampling.md`. It has `CreateMessageRequestParams`, `CreateMessageResult`, model preferences with `hints`/`costPriority`/`speedPriority`, per-server overrides, and the full callback precedence order.
- If a server uses `ctx.elicit()` and you need to handle user input forms or URL-mode elicitation — read `references/guides/elicitation.md`. It has all eight helper utilities (`accept`, `decline`, `cancel`, `reject`, `validate`, `acceptWithDefaults`, `getDefaults`, `applyDefaults`), form vs URL mode discrimination, `ElicitResult` shape, and callback precedence.
- If you need to listen for tool/resource/prompt list changes, send roots, handle custom notifications, or stream server logs — read `references/guides/notifications-and-logging.md`. It has `session.on("notification")`, `setRoots()`, `getRoots()`, `loggingCallback`, logging levels, and custom notification patterns.
- If you need bearer tokens, OAuth 2.1 flows (popup vs redirect), `BrowserOAuthClientProvider`, or CLI `--auth` — read `references/guides/authentication.md`. It has `headers` config, `authToken`, `callbackUrl`, `preventAutoAuth`, `useRedirectFlow`, `onMcpAuthorization()`, and DCR.

**React integration:**

- Building a React app with MCP? The `useMcp` hook has 20+ options and a full return type. Read `references/guides/usemcp-and-react.md` for connection states (`discovering`/`authenticating`/`pending_auth`/`ready`/`failed`), `McpClientProvider` props, `useMcpClient`/`useMcpServer` hooks, `McpServerOptions` table, proxy fallback, `autoReconnect` vs `reconnectionOptions`, `LocalStorageProvider`, and notification management.

**Code mode:**

- If you need programmatic code execution across MCP tools — read `references/guides/code-mode.md`. It has VM executor options (`timeoutMs`, `memoryLimitMb`), E2B cloud sandbox setup, custom executor function/class patterns, `executeCode()`, `searchTools()` / `search_tools()`, `BaseCodeExecutor`, `ExecutionResult`, and `PROMPTS.CODE_MODE`.

**CLI client:**

- If you are using the CLI for testing, scripting, or interactive sessions — read `references/guides/cli-reference.md`. It has `connect`, `disconnect`, `sessions`, `tools call`, `resources read/subscribe`, `prompts get`, `interactive` REPL, `--json` output, `--auth`, and session storage at `~/.mcp-use/cli-sessions.json`.

**Production hardening and patterns:**

- Before shipping to production, read `references/patterns/production-patterns.md`. It covers reconnection strategies, health checks, graceful shutdown, error handling, retry patterns, and cleanup.
- Before finalizing any client, review against `references/patterns/anti-patterns.md`. It catalogs common client mistakes in configuration, callbacks, lifecycle management, and error handling.

**Examples and templates:**

- Need a working example to copy from? Read `references/examples/client-recipes.md` for complete Node, Browser, React, and multi-server client recipes.
- Starting a new project and want the right folder structure? Read `references/examples/project-templates.md` for starter projects for Node CLI, React app, and Browser extension.

**Debugging:**

- Hit a specific error message? Read `references/troubleshooting/common-errors.md` for 404 auto-recovery, "Method not found", "Client not ready", timeout errors, and other known issues with cause and fix.

---

## Quick start

Minimal MCP client in 15 lines:

```typescript
import { MCPClient } from "mcp-use";  // mcp-use ^1.21.0

const client = new MCPClient({
  mcpServers: {
    myServer: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-everything"],
    },
  },
});
await client.createAllSessions();
const session = client.requireSession("myServer");

const tools = await session.listTools();
console.log("Tools:", tools.map((t) => t.name));

const result = await session.callTool("greet-user", { name: "Ada", formal: false });
console.log("Result:", result);

await client.closeAllSessions();
```

If the repo does not already have a TypeScript runner, add one first with `npm install -D tsx typescript`. Save this as `src/client.ts` or `src/mcp-client.ts`, keep the run command aligned with the filename you chose, then run `npm pkg set scripts.start="tsx src/client.ts"` and `npm start`, or `npx tsx src/client.ts` (substitute `src/mcp-client.ts` if that is the file you saved).
Smoke test the same STDIO server from the CLI: `npx mcp-use client connect --stdio "npx -y @modelcontextprotocol/server-everything" --name test`

If the first connection prints an anonymized telemetry banner from `mcp-use`, treat it as informational unless the repo explicitly disables telemetry.

---

## Core API summary

This section gives you the essential shapes. For full type definitions, options tables, and edge cases, follow the reference routing above.

### MCPClient constructor

```typescript
import { MCPClient, acceptWithDefaults, types } from "mcp-use";

const client = new MCPClient(
  {
    mcpServers: {
      // STDIO server (local):
      local: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-everything"],
        env: { NODE_ENV: "development" },
        clientInfo: { name: "my-app", version: "1.0.0" },
      },
      // HTTP server (remote):
      remote: {
        url: "https://api.example.com/mcp",
        headers: { Authorization: "Bearer ${AUTH_TOKEN}" },
        onSampling: async (params) => ({ /* ... */ }),
        onElicitation: async (params) => acceptWithDefaults(params),
        onNotification: (n) => console.log(n.method),
      },
    },
  },
  {
    onSampling: async (params) => ({ /* ... */ }),
    onElicitation: async (params) => acceptWithDefaults(params),
    onNotification: (n) => console.log(n.method),
    codeMode: true,
    loggingCallback: async (log: types.LoggingMessageNotificationParams) => {
      console.log(`[${log.level.toUpperCase()}]: ${log.message}`);
    },
  }
);
```

Other construction patterns:
```typescript
// From JSON file (Node.js only):
import { MCPClient, loadConfigFile } from "mcp-use";
const config = loadConfigFile("path/to/config.json");
const client = new MCPClient(config);

// Convenience factory:
const fromFile = MCPClient.fromConfigFile("path/to/config.json");

// From in-memory object:
const client = MCPClient.fromDict({
  mcpServers: { "my-server": { url: "https://api.example.com/mcp", authToken: "sk-key" } },
});
```

Full config shape, `ClientInfo` interface, and per-server callback overrides are in `references/guides/client-configuration.md`.

### Session management

```typescript
await client.createAllSessions();              // connect to all configured servers
const session = await client.createSession("myServer"); // connect to one server
const session = client.getSession("myServer"); // get existing session or null
await client.closeAllSessions();               // disconnect all
await client.close();                          // alias — also cleans up E2B sandboxes
```

### callTool

```typescript
const result = await session.callTool("tool_name", { param: "value" });
// result.content — the result data
// result.isError — boolean indicating success/failure

// With timeout and abort:
const controller = new AbortController();
const result = await session.callTool("slow_tool", { data: "value" }, {
  timeout: 60000,
  maxTotalTimeout: 300000,
  resetTimeoutOnProgress: true,
  signal: controller.signal,
});
```

Full `CallToolOptions`, `CallToolResult`, and `Tool` types are in `references/guides/tools.md`.

### listResources / listAllResources / readResource

```typescript
const resources = await session.listResources();      // paginated
const allResources = await session.listAllResources(); // full catalog
const result = await session.readResource("file:///data/config.json");
for (const content of result.contents) {
  console.log(content.text ?? content.blob);
}
```

Full `Resource`, `ResourceResult`, and template patterns are in `references/guides/resources.md`.

### getPrompt / complete

```typescript
const prompts = await session.listPrompts();
const result = await session.getPrompt("plan_vacation", { destination: "Japan" });

const completions = await session.complete({
  ref: { type: "ref/prompt", name: "my-prompt" },
  argument: { name: "language", value: "py" },
});
```

Full types in `references/guides/prompts.md` and `references/guides/completion.md`.

### Notifications and roots

```typescript
session.on("notification", async (notification) => {
  if (notification.method === "notifications/tools/list_changed") {
    const tools = await session.listTools();
  }
});

await session.setRoots([
  { uri: "file:///home/user/project", name: "My Project" },
]);
```

Full notification types, custom events, and logging in `references/guides/notifications-and-logging.md`.

### Sampling callback

```typescript
import { MCPClient, type OnSamplingCallback } from "mcp-use";

const onSampling: OnSamplingCallback = async (params) => {
  const lastMsg = params.messages[params.messages.length - 1];
  const text = typeof lastMsg?.content === "object" && "text" in lastMsg.content
    ? lastMsg.content.text ?? "" : "";
  return {
    role: "assistant",
    content: { type: "text", text: await yourLLM.complete(text) },
    model: "your-model",
    stopReason: "endTurn",
  };
};
```

Callback precedence: per-server `onSampling` > global `onSampling`. Full `CreateMessageRequestParams`, `CreateMessageResult`, and model preferences in `references/guides/sampling.md`.

### Elicitation callback

```typescript
import { accept, decline, cancel, validate, acceptWithDefaults, MCPClient } from "mcp-use";
import type { OnElicitationCallback } from "mcp-use";

const onElicitation: OnElicitationCallback = async (params) => {
  if (params.mode === "url") {
    console.log(`Visit: ${params.url}`);
    return { action: "accept" };
  }
  return acceptWithDefaults(params);
};
```

Eight helper utilities (`accept`, `decline`, `cancel`, `reject`, `validate`, `acceptWithDefaults`, `getDefaults`, `applyDefaults`), form vs URL modes, and validation patterns are in `references/guides/elicitation.md`.

### React hooks

```typescript
// Single-server:
import { useMcp } from "mcp-use/react";
const mcp = useMcp({
  url: "http://localhost:3000/mcp",
  autoReconnect: true,
  callbackUrl: "http://localhost:3000/callback",
  onElicitation: async (params) => acceptWithDefaults(params),
});
// mcp.state: "discovering" | "authenticating" | "pending_auth" | "ready" | "failed"
// mcp.tools, mcp.resources, mcp.prompts
// mcp.callTool("name", args), mcp.readResource(uri), mcp.authenticate(), mcp.retry()

// Multi-server:
import { McpClientProvider, useMcpClient, useMcpServer } from "mcp-use/react";

<McpClientProvider storageProvider={new LocalStorageProvider("my-app")}>
  <App />
</McpClientProvider>

const { servers, addServer, removeServer } = useMcpClient();
const server = useMcpServer("linear");
```

Full `useMcp` options (20+), `McpClientProvider` props, `McpServerOptions` table, proxy fallback, `autoReconnect` vs `reconnectionOptions`, and notification management in `references/guides/usemcp-and-react.md`.

### Code mode

```typescript
const client = new MCPClient(config, { codeMode: true }); // VM executor (default)
const result = await client.executeCode(`
  const tools = await search_tools("github");
  return tools;
`);
// result.result, result.logs, result.error, result.execution_time
await client.close(); // required — cleans up E2B sandboxes if used
```

VM options, E2B setup, custom executors, `BaseCodeExecutor`, and `PROMPTS.CODE_MODE` in `references/guides/code-mode.md`.

---

## Environment feature matrix

| Feature | Node.js | Browser | React (hook) | CLI |
|---------|---------|---------|--------------|-----|
| STDIO connections | Yes | No | No | Yes |
| HTTP connections | Yes | Yes | Yes | Yes |
| File system access | Yes | No | No | Yes |
| Code mode | Yes | No | No | No |
| OAuth flow | Yes | Yes | Yes | Yes |
| Automatic state management | No | No | Yes | No |
| Session persistence | No | No | No | Yes |

**Import paths:**

| Environment | Import |
|-------------|--------|
| Node.js | `import { MCPClient, loadConfigFile } from "mcp-use"` |
| Browser | `import { MCPClient } from "mcp-use/browser"` |
| React | `import { useMcp } from "mcp-use/react"` |
| Browser OAuth | `import { BrowserOAuthClientProvider } from "mcp-use/browser"` |
| OAuth callback | `import { onMcpAuthorization } from "mcp-use/auth"` |

---

## Rules

1. Always call `client.closeAllSessions()` or `client.close()` in cleanup — leaked sessions hold server processes open. Use `client.close()` when using E2B code mode.
2. Check `session.connector.serverCapabilities` before calling `complete()` — not all servers support completions.
3. Use `acceptWithDefaults(params)` as the default elicitation callback — never leave `onElicitation` undefined if the server uses elicitation.
4. Import from the correct entry point: `mcp-use` (Node), `mcp-use/browser` (Browser), `mcp-use/react` (React) — wrong imports cause runtime errors.
5. Set `timeout` and `maxTotalTimeout` on long-running tool calls — the default 60s timeout will abort slow operations.
6. Handle `isError: true` in `CallToolResult` — tool errors are returned, not thrown.
7. Use per-server callbacks when connecting to servers with different LLM providers.
8. Debounce `complete()` calls in autocomplete UIs — servers may rate-limit completion requests.
9. Listen for `notifications/tools/list_changed` and re-fetch tools — servers can add/remove tools dynamically.
10. Use `autoReconnect` in production React apps — connections drop; the client handles re-initialization transparently.

---

## Common pitfalls

| Mistake | Fix |
|---------|-----|
| Not calling `createAllSessions()` before using sessions | Call `await client.createAllSessions()` after construction |
| Calling `complete()` without capability check | Check `session.connector.serverCapabilities?.completions` first |
| Missing `onElicitation` when server uses `ctx.elicit()` | Set `onElicitation: (params) => acceptWithDefaults(params)` |
| Missing `onSampling` when server uses `ctx.sample()` | Provide `onSampling` callback routing to your LLM |
| Using `mcp-use` import in browser | Use `mcp-use/browser` — main entry point requires Node APIs |
| Hardcoded secrets in client config | Use environment variables: `` headers: { Authorization: `Bearer ${process.env.TOKEN}` } `` |
| Not handling `isError` in tool results | Check `result.isError` before processing `result.content` |
| Forgetting cleanup on process exit | Register `process.on("SIGINT", () => client.closeAllSessions())` |
| Using legacy SSE for new HTTP connections | Prefer streamable HTTP: use `transport: "http"` in client config or `transportType: "http"` in React |
| No reconnection config in React | Set `autoReconnect: true` on `useMcp` or per-server options |
| Checking `mcp.status` instead of `mcp.state` | The hook exposes `state`, not `status` |
| Assuming one `listResources()` call returns the full catalog | Use `session.listAllResources()` for the full set, or follow `nextCursor` with `listResources(cursor)` |
| Treating `readResource()` as plain value | It returns `{ contents: ResourceContent[] }` — iterate `result.contents` |
| Using `persistenceProvider` on McpClientProvider | Correct prop is `storageProvider` |
| Confusing `autoReconnect` with `reconnectionOptions` | `autoReconnect` = app-level health checks; `reconnectionOptions` = SDK transport back-off |
| Not calling `client.close()` after E2B code mode | E2B sandboxes stay alive until `client.close()` is called |

---

## Do this, not that

| Do this | Not that |
|---------|---------|
| `import { MCPClient } from "mcp-use"` | `import { Client } from "@modelcontextprotocol/sdk/client"` |
| `session.callTool("name", args)` | Build JSON-RPC requests manually |
| `acceptWithDefaults(params)` for elicitation | Return `{ action: "accept" }` without content |
| `session.on("notification", handler)` | Poll `session.listTools()` on an interval |
| `client.closeAllSessions()` in cleanup | Let sessions leak on process exit |
| `loadConfigFile("config.json")` then `new MCPClient(config)` | Parse JSON and construct transports manually |
| `useMcp({ url, autoReconnect: true })` in React | Build custom WebSocket reconnection logic |
| `validate(params, data)` before accepting elicitation | Skip validation and accept any input |
| Per-server `onSampling` for multi-LLM setups | One global callback with server-name switch |
| `session.listAllResources()` for the full catalog, or `session.listResources(cursor)` for pagination | Assume one `listResources()` page is exhaustive |
| `mcp.state` in React | `mcp.status` (does not exist) |
| `transport: "http"` in client config or `transportType: "http"` in React | `transport: "sse"` or `transportType: "sse"` for new integrations |
| `storageProvider={...}` on McpClientProvider | `persistenceProvider={...}` (wrong prop name) |
| `client.close()` after E2B code mode | `closeAllSessions()` alone (misses sandbox cleanup) |

---

## Guardrails

- Never import from `@modelcontextprotocol/sdk` directly — use `mcp-use`, `mcp-use/browser`, or `mcp-use/react`.
- Never call `session.callTool()` before `createAllSessions()` or `session.initialize()` completes.
- Never leave `onSampling` undefined if a server uses `ctx.sample()` — the request fails silently.
- Never leave `onElicitation` undefined if a server uses `ctx.elicit()` — use `acceptWithDefaults(params)` as minimum.
- Never hardcode secrets in client config — use environment variables or OAuth providers.
- Never skip `client.closeAllSessions()` on shutdown — leaked STDIO sessions leave orphan child processes.
- Never use `mcp-use` (Node entry point) in a browser — it requires Node APIs; use `mcp-use/browser`.
- Never assume all servers support completions — check `serverCapabilities?.completions` first.
- Always handle `isError: true` in `CallToolResult` — tool errors are returned as results, not thrown.
- Always set `autoReconnect: true` in production React apps.
- Always debounce `complete()` calls in autocomplete UIs.
- Always clean up sessions on process exit — register `SIGINT`/`SIGTERM` handlers.
- Prefer streamable HTTP for new connections: use `transport: "http"` in server config, or `transportType: "http"` / `"auto"` in React.
- Never treat `readResource()` return as a plain value — it returns `{ contents: ResourceContent[] }`.
- Do not `await loadConfigFile()` — it reads and parses JSON synchronously in Node. Use `new MCPClient("config.json")`, `MCPClient.fromConfigFile("config.json")`, or `new MCPClient(loadConfigFile("config.json"))`.
- Never use `mcp.status` in React — correct property is `mcp.state`.
- Always check all connection states: `"discovering"`, `"authenticating"`, `"pending_auth"`, `"ready"`, `"failed"`.
- Never use `persistenceProvider` on McpClientProvider — correct prop is `storageProvider`.
- Do not confuse `autoReconnect` (app-level health checks) with `reconnectionOptions` (SDK transport back-off).
- Always call `client.close()` when using E2B code mode — sandboxes persist until explicitly closed.
- Prefer `onElicitation` over the deprecated `elicitationCallback` alias.
