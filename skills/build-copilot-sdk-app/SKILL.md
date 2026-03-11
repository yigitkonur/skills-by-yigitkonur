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
│   ├── Install & basic example ──────────► Quick start (below)
│   ├── Client options & transport ───────► references/client-and-transport.md
│   └── Authentication ──────────────────► references/auth-and-byok.md
│
├── Sessions
│   ├── Create / resume / disconnect ────► references/sessions.md
│   ├── Infinite sessions & compaction ──► references/sessions.md
│   └── Persistence & resumption ────────► references/sessions.md
│
├── Messages & streaming
│   ├── send / sendAndWait ──────────────► Quick start (below)
│   ├── Streaming deltas ────────────────► references/events-and-streaming.md
│   └── All 47 event types ─────────────► references/events-and-streaming.md
│
├── Custom tools
│   ├── defineTool with Zod ─────────────► references/tools-and-schemas.md
│   ├── JSON Schema tools ──────────────► references/tools-and-schemas.md
│   └── Override built-in tools ────────► references/tools-and-schemas.md
│
├── Permissions & user input
│   ├── Permission handler ─────────────► references/permissions-and-user-input.md
│   ├── askUser / onUserInputRequest ───► references/permissions-and-user-input.md
│   └── Elicitation (MCP forms) ────────► references/permissions-and-user-input.md
│
├── Hooks (lifecycle interceptors)
│   ├── Pre/post tool use ──────────────► references/hooks.md
│   ├── Prompt modification ────────────► references/hooks.md
│   └── Session lifecycle & errors ─────► references/hooks.md
│
├── Agents, MCP & skills
│   ├── Custom agents ──────────────────► references/agents-mcp-skills.md
│   ├── MCP server config ─────────────► references/agents-mcp-skills.md
│   ├── Skills system ─────────────────► references/agents-mcp-skills.md
│   └── CLI extensions (.mjs) ─────────► references/agents-mcp-skills.md
│
├── Advanced patterns
│   ├── Plan / autopilot / interactive ─► references/advanced-patterns.md
│   ├── Fleet mode ─────────────────────► references/advanced-patterns.md
│   ├── Multi-client architecture ──────► references/advanced-patterns.md
│   ├── Ralph loop (autonomous dev) ───► references/advanced-patterns.md
│   ├── Steering & queueing ───────────► references/advanced-patterns.md
│   └── System message modes ──────────► references/advanced-patterns.md
│
├── Auth & BYOK
│   ├── GitHub OAuth / tokens ──────────► references/auth-and-byok.md
│   └── Bring Your Own Key ────────────► references/auth-and-byok.md
│
└── Type reference
    └── All interfaces & RPC methods ──► references/types-reference.md
```

## Quick start

### Prerequisites

Verify your environment:
```bash
node --version   # must be >= 20
copilot --version # Copilot CLI must be installed
```

### Project setup

```bash
npm init -y
npm pkg set type=module   # SDK is ESM-only
npm install @github/copilot-sdk tsx zod
```

> **ESM required.** The SDK only ships ESM exports. Your `package.json` must have `"type": "module"`.

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

session.on("session.idle", async () => {
  console.log("\n--- done ---");
  await session.disconnect();
  await client.stop();
});

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
    temperature: "62°F",
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

### Create-or-resume pattern

`createSession` always starts fresh — only `resumeSession` restores conversation context. In applications that may revisit a session:

```typescript
let session;
try {
  session = await client.resumeSession(sessionId, {
    onPermissionRequest: approveAll,
  });
} catch {
  session = await client.createSession({
    sessionId,
    model: "gpt-4.1",
    onPermissionRequest: approveAll,
  });
}
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

### Abort in-flight work

```typescript
await session.send({ prompt: "Run sleep 100" });
await session.abort(); // cancels current work; session remains usable
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
| BYOK without `model` | `model` is required when using `provider` config. Session creation succeeds silently, but `sendAndWait` will fail. |
| Race condition on event registration | Register `session.on()` before calling `session.send()`. |
