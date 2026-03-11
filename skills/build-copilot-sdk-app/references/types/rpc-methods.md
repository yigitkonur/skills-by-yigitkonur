# RPC Methods Reference — @github/copilot-sdk

Complete reference for every RPC method in the Copilot SDK. These are the
primary mechanism for programmatic interaction with the platform — controlling
models, sessions, agents, workspace files, plans, permissions, and more.

**Total: 24 RPC methods** — 4 server-scoped, 20 session-scoped.

---

## Access Patterns

| Scope | Access | Lifetime | Purpose |
|-------|--------|----------|---------|
| **Server** | `client.rpc.*` | Application-wide | Platform: ping, models, tools, quota |
| **Session** | `session.rpc.*` | Per-session | State: model, plans, workspace, agents |

```typescript
import { CopilotClient } from "@github/copilot-sdk";
const client = new CopilotClient({ /* config */ });
await client.start();

// Server-scoped — available after client.start()
const pong = await client.rpc.ping({ message: "hello" });

// Session-scoped — available on each session object
const session = await client.createSession();
const model = await session.rpc.model.getCurrent();
```

> `client.rpc` requires a connected client (post-`start()`).
> `session.rpc` is bound to a specific session instance.

---

## Server-Scoped RPC Methods

### `client.rpc.ping()`
Health-check and protocol version handshake.
```typescript
// Params
{ message?: string }
// Result
{ message: string; timestamp: number; protocolVersion: number }
```

### `client.rpc.models.list()`
Retrieve all models available to the authenticated user.
```typescript
// Params: none
// Result
{ models: ModelInfo[] }
// ModelInfo: { id, name, version, capabilities, maxTokens?, ... }
```
Model IDs from this list are used with `session.rpc.model.switchTo()`.

### `client.rpc.tools.list()`
List registered tools, optionally filtered by model compatibility.
```typescript
// Params
{ model?: string }
// Result
{ tools: Array<{ name: string; description: string; inputSchema: object }> }
```

### `client.rpc.account.getQuota()`
Check the user's quota usage and limits.
```typescript
// Params: none
// Result
{
  quotaSnapshots: {
    [key: string]: {
      used: number;
      limit: number;
      resetsAt: string;  // ISO 8601
    }
  }
}
```

---

## Session-Scoped RPC Methods

### Model Operations

#### `session.rpc.model.getCurrent()`
```typescript
// Params: none
// Result
{ modelId?: string }
```
Returns `undefined` for `modelId` when the platform default is in use.

#### `session.rpc.model.switchTo()`
```typescript
// Params
{ modelId: string; reasoningEffort?: "low" | "medium" | "high" | "xhigh" }
// Result
{ modelId?: string }
```
Switches the model immediately. `reasoningEffort` adjusts compute depth.
> `session.setModel(modelId)` is a convenience wrapper around this call.

### Mode Operations

#### `session.rpc.mode.get()`
```typescript
// Params: none
// Result
{ mode: "interactive" | "plan" | "autopilot" }
```

| Mode | Behavior |
|------|----------|
| `interactive` | User confirms each action (default) |
| `plan` | Agent creates a plan before executing |
| `autopilot` | Agent executes autonomously |

#### `session.rpc.mode.set()`
```typescript
// Params
{ mode: "interactive" | "plan" | "autopilot" }
// Result
{ mode: "interactive" | "plan" | "autopilot" }
```

### Plan Operations

#### `session.rpc.plan.read()`
```typescript
// Params: none
// Result
{ exists: boolean; content: string | null; path: string | null }
```
When `exists` is `false`, both `content` and `path` are `null`.

#### `session.rpc.plan.update()`
```typescript
// Params
{ content: string }
// Result: void
```
Replaces plan content entirely. Creates a new plan if none exists.

#### `session.rpc.plan.delete()`
```typescript
// Params: none
// Result: void
```

### Workspace File Operations

Operate on the session's workspace directory. Primarily used with infinite
sessions that maintain persistent workspace state.

#### `session.rpc.workspace.listFiles()`
```typescript
// Params: none
// Result
{ files: string[] }  // Relative paths
```

#### `session.rpc.workspace.readFile()`
```typescript
// Params
{ path: string }
// Result
{ content: string }  // UTF-8 encoded
```

#### `session.rpc.workspace.createFile()`
```typescript
// Params
{ path: string; content: string }
// Result: void
```
Creates the file and intermediate directories. Overwrites if file exists.

### Fleet Mode

#### `session.rpc.fleet.start()`
Launch fleet mode — executes sub-agents in parallel.
```typescript
// Params
{ prompt?: string }  // Optional prompt combined with fleet instructions
// Result
{ started: boolean }
```

### Agent Management

#### `session.rpc.agent.list()`
```typescript
// Params: none
// Result
{ agents: Array<{ name: string; displayName?: string; description?: string }> }
```

#### `session.rpc.agent.getCurrent()`
```typescript
// Params: none
// Result
{ agent: { name: string; displayName?: string; description?: string } | null }
```
Returns `null` when no agent is selected.

#### `session.rpc.agent.select()`
```typescript
// Params
{ name: string }
// Result
{ agent: { name: string; displayName?: string; description?: string } }
```
The `name` must match one from `agent.list()`.

#### `session.rpc.agent.deselect()`
```typescript
// Params: none
// Result: void
```

### Compaction

#### `session.rpc.compaction.compact()`
Compact conversation history to reduce token usage.
```typescript
// Params: none
// Result
{ success: boolean; tokensRemoved: number; messagesRemoved: number }
```
Summarizes older messages, replacing them with a condensed version.

### Pending Tool Call Handling

#### `session.rpc.tools.handlePendingToolCall()`
Resolve a deferred tool call with a result or error.
```typescript
// Params
{
  requestId: string;
  result?: string | { content: string; metadata?: Record<string, unknown> };
  error?: string;
}
// Result
{ success: boolean }
```
For **external/deferred** tool handling only — not normal tool flow.
Provide either `result` or `error`, not both. The `requestId` comes from
the pending tool call event in the session stream.

### Pending Permission Handling

#### `session.rpc.permissions.handlePendingPermissionRequest()`
Resolve a deferred permission request.
```typescript
// Params
{ requestId: string; result: PermissionRequestResult }
// Result
{ success: boolean }
```

### `PermissionRequestResult` — Discriminated Union (5 variants)

```typescript
type PermissionRequestResult =
  | { kind: "approved" }
  | { kind: "denied-by-rules"; rules: unknown[] }
  | { kind: "denied-no-approval-rule-and-could-not-request-from-user" }
  | { kind: "denied-interactively-by-user"; feedback?: string }
  | { kind: "denied-by-content-exclusion-policy"; path: string; message: string };
```

| Variant | When to use |
|---------|------------|
| `approved` | User or policy grants the permission |
| `denied-by-rules` | Automated rules rejected; attach rule objects |
| `denied-no-approval-rule-and-could-not-request-from-user` | No rule and user unavailable |
| `denied-interactively-by-user` | User denied; optional feedback |
| `denied-by-content-exclusion-policy` | File excluded by policy |

### Session Logging

#### `session.rpc.log()`
```typescript
// Params
{ message: string; level?: "info" | "warning" | "error"; ephemeral?: boolean }
// Result
{ eventId: string }
```
When `ephemeral` is `true`, the message is transient and may not persist.
> `session.log(message)` is a convenience wrapper around this call.

---

## Usage Examples

### 1. Health Check with Ping
```typescript
const client = new CopilotClient({ apiKey: process.env.COPILOT_API_KEY });
await client.start();
const health = await client.rpc.ping({ message: "health-check" });
console.log(`Protocol v${health.protocolVersion}`);
```

### 2. Model Switching Mid-Session
```typescript
const session = await client.createSession();
const { models } = await client.rpc.models.list();
const premium = models.find(m => m.id.includes("gpt-4"));
if (premium) {
  await session.rpc.model.switchTo({
    modelId: premium.id,
    reasoningEffort: "high",
  });
}
```

### 3. Plan Mode Management
```typescript
const session = await client.createSession();
await session.rpc.mode.set({ mode: "plan" });
await session.rpc.plan.update({
  content: "## Plan\n1. Create schema\n2. Build API\n3. Add auth",
});
const plan = await session.rpc.plan.read();
console.log("Plan exists:", plan.exists);
await session.rpc.mode.set({ mode: "autopilot" });
// Clean up later
await session.rpc.plan.delete();
```

### 4. Workspace File Operations
```typescript
const session = await client.createSession();
await session.rpc.workspace.createFile({
  path: "src/config.json",
  content: JSON.stringify({ port: 3000, debug: true }, null, 2),
});
const { files } = await session.rpc.workspace.listFiles();
const { content } = await session.rpc.workspace.readFile({ path: "src/config.json" });
console.log("Config:", JSON.parse(content));
```

### 5. Agent Selection and Deselection
```typescript
const session = await client.createSession();
const { agents } = await session.rpc.agent.list();
const reviewer = agents.find(a => a.name === "code-review");
if (reviewer) {
  await session.rpc.agent.select({ name: reviewer.name });
  const current = await session.rpc.agent.getCurrent();
  console.log("Active:", current.agent?.displayName);
}
await session.rpc.agent.deselect();
```

---

## Important Caveats

1. **`client.rpc` requires connected state.** Calling any server-scoped RPC
   before `client.start()` resolves throws a connection error.

2. **`session.rpc` is session-scoped.** Each session has its own RPC proxy.
   Methods on one session do not affect another.

3. **Convenience wrappers exist.** `session.setModel()` wraps
   `session.rpc.model.switchTo()` and `session.log()` wraps
   `session.rpc.log()`. RPC methods are the underlying primitives.

4. **`tools.handlePendingToolCall` is for deferred tool handling only.** In
   normal flow the SDK handles tool calls automatically.

5. **`permissions.handlePendingPermissionRequest` is for deferred permissions.**
   Use when intercepting permission requests for custom approval flows.

6. **Fleet mode runs sub-agents in parallel.** `fleet.start()` launches
   concurrent agents with optional combined prompt.

7. **`compaction.compact()` reduces token usage.** Summarizes older messages,
   freeing context window space for long-running sessions.

8. **Workspace operations are workspace-scoped.** Paths are relative to the
   session's workspace directory (infinite sessions).

9. **All RPC methods return Promises.** They can throw on connection failure,
   invalid params, or server errors. Always handle errors in production.

10. **JSON-RPC 2.0 protocol internally.** The SDK handles serialization,
    request IDs, and error mapping transparently.
