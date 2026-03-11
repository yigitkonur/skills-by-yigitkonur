---
name: build-copilot-sdk-app
description: Use skill if you are building TypeScript applications with the GitHub Copilot SDK (@github/copilot-sdk), including sessions, tools, streaming, hooks, custom agents, or BYOK.
---

# Build Copilot SDK App

Build applications powered by GitHub Copilot using the `@github/copilot-sdk` TypeScript/Node.js package (v0.1.32+, protocol v3). The SDK communicates with the Copilot CLI over JSON-RPC (stdio or TCP) and exposes a session-based API for sending prompts, receiving streamed responses, registering custom tools, handling permissions, and managing agent workflows.

## Decision tree

```
What do you need?
│
├── New app from scratch
│   ├── Install & basic example ────────────► Quick start (below)
│   ├── Client constructor options ─────────► references/client/setup-and-options.md
│   ├── Transport mode selection ───────────► references/client/transport-modes.md
│   ├── Client lifecycle & health ──────────► references/client/lifecycle-and-health.md
│   └── Authentication ────────────────────► references/auth/github-oauth.md
│
├── Sessions
│   ├── Create & configure ────────────────► references/sessions/create-and-configure.md
│   ├── Persistence & resume ──────────────► references/sessions/persistence-and-resume.md
│   ├── Infinite sessions & compaction ────► references/sessions/infinite-sessions.md
│   └── System messages & steering ────────► references/sessions/system-messages.md
│
├── Messages & streaming
│   ├── send / sendAndWait ────────────────► Quick start (below)
│   ├── Streaming subscription patterns ──► references/events/streaming-patterns.md
│   ├── Assistant message events ──────────► references/events/assistant-events.md
│   └── Delta accumulation ────────────────► references/events/streaming-patterns.md
│
├── Custom tools
│   ├── defineTool with Zod ───────────────► references/tools/define-tool-zod.md
│   ├── JSON Schema tools ────────────────► references/tools/json-schema-tools.md
│   ├── Tool results & errors ────────────► references/tools/tool-results-and-errors.md
│   └── Override built-in tools ──────────► references/tools/override-builtin-tools.md
│
├── Events (47 types)
│   ├── Session lifecycle events ──────────► references/events/session-lifecycle-events.md
│   ├── Assistant events ─────────────────► references/events/assistant-events.md
│   ├── Tool events ──────────────────────► references/events/tool-events.md
│   ├── Permission events ────────────────► references/events/permission-events.md
│   ├── User input events ────────────────► references/events/user-input-events.md
│   ├── Agent & skill events ─────────────► references/events/agent-events.md
│   ├── System events ────────────────────► references/events/system-events.md
│   └── Hook events ──────────────────────► references/events/hook-events.md
│
├── Permissions & user input
│   ├── Permission handler ───────────────► references/permissions/permission-handler.md
│   ├── Permission kinds (7 types) ───────► references/permissions/permission-kinds.md
│   └── askUser / elicitation ────────────► references/permissions/user-input-handler.md
│
├── Hooks (lifecycle interceptors)
│   ├── Pre-tool use ─────────────────────► references/hooks/pre-tool-use.md
│   ├── Post-tool use ────────────────────► references/hooks/post-tool-use.md
│   ├── User prompt submitted ────────────► references/hooks/user-prompt-submitted.md
│   ├── Session start / end ──────────────► references/hooks/session-lifecycle-hooks.md
│   └── Error handling hook ──────────────► references/hooks/error-handling-hook.md
│
├── Agents, MCP & skills
│   ├── Custom agents ────────────────────► references/agents/custom-agents.md
│   ├── MCP server config ───────────────► references/agents/mcp-servers.md
│   ├── Skills system ───────────────────► references/agents/skills-system.md
│   └── CLI extensions (.mjs) ───────────► references/agents/cli-extensions.md
│
├── Advanced patterns
│   ├── Plan / autopilot / interactive ──► references/patterns/plan-autopilot-mode.md
│   ├── Fleet mode ──────────────────────► references/patterns/fleet-mode.md
│   ├── Multi-client architecture ───────► references/patterns/multi-client.md
│   ├── Ralph loop (autonomous dev) ────► references/patterns/ralph-loop.md
│   ├── Steering & queueing ────────────► references/patterns/steering-and-queueing.md
│   ├── Backend service patterns ───────► references/patterns/backend-service.md
│   ├── Scaling & performance ──────────► references/patterns/scaling.md
│   └── Workspace file operations ──────► references/patterns/workspace-files.md
│
├── Auth & BYOK
│   ├── GitHub OAuth / tokens ──────────► references/auth/github-oauth.md
│   ├── Environment variables ──────────► references/auth/environment-variables.md
│   └── Bring Your Own Key ────────────► references/auth/byok-providers.md
│
└── Type reference
    ├── Client types ──────────────────► references/types/client-types.md
    ├── Session types ─────────────────► references/types/session-types.md
    ├── Tool types ────────────────────► references/types/tool-types.md
    ├── Event types (all 47) ──────────► references/types/event-types.md
    ├── Hook types ────────────────────► references/types/hook-types.md
    └── RPC methods ───────────────────► references/types/rpc-methods.md
```

## Quick start

```bash
npm install @github/copilot-sdk tsx
```

Requires Node.js >= 20 and Copilot CLI installed (`copilot --version`).

### Minimal example

```typescript
import { CopilotClient, approveAll } from "@github/copilot-sdk";

const client = new CopilotClient();

const session = await client.createSession({
  model: "gpt-4.1",
  onPermissionRequest: approveAll,
});

const response = await session.sendAndWait({ prompt: "What is 2 + 2?" });
console.log(response?.data.content);

await session.disconnect();
await client.stop();
```

### With streaming

```typescript
const session = await client.createSession({
  model: "gpt-4.1",
  streaming: true,
  onPermissionRequest: approveAll,
});

session.on("assistant.message_delta", (event) => {
  process.stdout.write(event.data.deltaContent);
});

session.on("session.idle", () => console.log("\n--- done ---"));

await session.send({ prompt: "Explain TypeScript generics" });
```

### With a custom tool

```typescript
import { CopilotClient, defineTool, approveAll } from "@github/copilot-sdk";
import { z } from "zod";

const getWeather = defineTool("get_weather", {
  description: "Get current weather for a city",
  parameters: z.object({
    city: z.string().describe("City name"),
  }),
  handler: async ({ city }) => ({
    city,
    temperature: "62F",
    condition: "cloudy",
  }),
});

const client = new CopilotClient();
const session = await client.createSession({
  model: "gpt-4.1",
  tools: [getWeather],
  onPermissionRequest: approveAll,
});

const response = await session.sendAndWait({
  prompt: "What's the weather in San Francisco?",
});
console.log(response?.data.content);

await session.disconnect();
await client.stop();
```

## Key patterns

### Send-and-wait vs fire-and-forget

```typescript
// Blocking — waits for session.idle, returns last assistant.message
const response = await session.sendAndWait(
  { prompt: "Hello" },
  30_000, // optional timeout in ms
);

// Non-blocking — returns immediately, events arrive via session.on()
await session.send({ prompt: "Start a long task..." });
```

### Event subscription (typed + wildcard)

```typescript
// Typed — only fires for the specific event type
const unsub = session.on("tool.execution_complete", (event) => {
  console.log(`${event.data.toolName}: ${event.data.success}`);
});

// Wildcard — fires for every event
session.on((event) => {
  if (event.type === "session.error") {
    console.error(event.data.message);
  }
});

unsub(); // unsubscribe
```

### Session persistence

```typescript
// Create with a stable ID
const session = await client.createSession({
  sessionId: "user-123-conversation",
  model: "gpt-4.1",
  onPermissionRequest: approveAll,
});
await session.sendAndWait({ prompt: "Let's discuss TypeScript" });
await session.disconnect(); // preserves state on disk

// Resume later (same or different client)
const resumed = await client.resumeSession("user-123-conversation", {
  onPermissionRequest: approveAll,
});
```

### Handling askUser programmatically

```typescript
const session = await client.createSession({
  onPermissionRequest: approveAll,
  onUserInputRequest: async (request) => {
    if (request.choices?.length) {
      return { answer: request.choices[0], wasFreeform: false };
    }
    return { answer: "Yes, proceed", wasFreeform: true };
  },
});
```

### Plan / autopilot mode

```typescript
await session.rpc.mode.set({ mode: "plan" });

session.on("exit_plan_mode.requested", (event) => {
  console.log("Plan ready:", event.data.summary);
  session.rpc.mode.set({ mode: "autopilot" });
});
```

### Fleet mode

```typescript
const result = await session.rpc.fleet.start({ prompt: "Refactor auth module" });
console.log("Fleet started:", result.started);
```

### Abort in-flight work

```typescript
await session.send({ prompt: "Run sleep 100" });
await session.abort(); // cancels current work; session remains usable
```

### Workspace file operations

```typescript
const files = await session.rpc.workspace.listFiles();
const content = await session.rpc.workspace.readFile({ path: "src/index.ts" });
await session.rpc.workspace.createFile({ path: "output.md", content: "# Report" });
```

## Common pitfalls

| Pitfall | Fix |
|---------|-----|
| `onPermissionRequest` missing | Required on every `createSession`/`resumeSession`. Use `approveAll` for unattended operation. |
| `sendAndWait` timeout | Default is 60s. Pass explicit timeout: `sendAndWait(opts, 300_000)`. Timeout does NOT abort in-flight work. |
| Streaming events not arriving | Set `streaming: true` in SessionConfig. |
| `cliUrl` + `useStdio` | Mutually exclusive. `cliUrl` connects to external server; `useStdio` spawns child process. |
| `console.log` in extensions | stdout is reserved for JSON-RPC. Use `session.log()` instead. |
| Tool name collision in extensions | Tool names must be globally unique across all extensions. |
| BYOK without `model` | `model` is required when using `provider` config. |
| Race condition on event registration | Register `session.on()` before calling `session.send()`. |
| Fleet mode without session | Fleet requires an active session. Create session first, then call `session.rpc.fleet.start()`. |
| Plan mode stuck | Listen for `exit_plan_mode.requested` event and switch mode to proceed. |

## Minimal reading sets

### "I need a basic app with custom tools"

- `references/client/setup-and-options.md`
- `references/tools/define-tool-zod.md`
- `references/permissions/permission-handler.md`
- `references/events/streaming-patterns.md`

### "I need to build an autonomous agent"

- `references/patterns/plan-autopilot-mode.md`
- `references/patterns/ralph-loop.md`
- `references/hooks/pre-tool-use.md`
- `references/hooks/post-tool-use.md`
- `references/permissions/user-input-handler.md`

### "I need a backend service with multiple clients"

- `references/patterns/backend-service.md`
- `references/patterns/multi-client.md`
- `references/patterns/scaling.md`
- `references/client/transport-modes.md`
- `references/auth/github-oauth.md`

### "I need to integrate MCP servers and skills"

- `references/agents/mcp-servers.md`
- `references/agents/skills-system.md`
- `references/agents/custom-agents.md`
- `references/agents/cli-extensions.md`

### "I need to handle all events and hooks"

- `references/events/streaming-patterns.md`
- `references/events/session-lifecycle-events.md`
- `references/events/tool-events.md`
- `references/hooks/pre-tool-use.md`
- `references/hooks/post-tool-use.md`
- `references/hooks/error-handling-hook.md`

### "I need BYOK with a custom provider"

- `references/auth/byok-providers.md`
- `references/auth/environment-variables.md`
- `references/types/client-types.md`

### "I need the complete type reference"

- `references/types/client-types.md`
- `references/types/session-types.md`
- `references/types/tool-types.md`
- `references/types/event-types.md`
- `references/types/hook-types.md`
- `references/types/rpc-methods.md`

## Final reminder

This skill is split into many small, atomic reference files organized by domain. Do not load everything at once. Start with the smallest relevant reading set above, then expand into neighboring references only when the task actually requires them. Every reference file in `references/` is explicitly routed from the decision tree above.
