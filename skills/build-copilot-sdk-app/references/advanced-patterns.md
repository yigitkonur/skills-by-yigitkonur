# Advanced Patterns

## Plan / autopilot / interactive modes

The session supports three execution modes:

| Mode | Behavior |
|------|----------|
| `interactive` | Default. Agent asks before executing. |
| `plan` | Agent writes a plan to `plan.md` instead of executing. |
| `autopilot` | Agent executes without asking for confirmation. |

### Mode RPC methods

```typescript
// Get current mode
const { mode } = await session.rpc.mode.get();
// mode: "interactive" | "plan" | "autopilot"

// Set mode
await session.rpc.mode.set({ mode: "plan" });
await session.rpc.mode.set({ mode: "autopilot" });
await session.rpc.mode.set({ mode: "interactive" });
```

### Plan mode workflow

```typescript
// 1. Switch to plan mode
await session.rpc.mode.set({ mode: "plan" });

// 2. Send task — agent writes a plan instead of executing
await session.send({ prompt: "Refactor the auth module" });

// 3. Listen for plan completion
session.on("exit_plan_mode.requested", (event) => {
  console.log("Plan summary:", event.data.summary);
  console.log("Plan content:", event.data.planContent);
  console.log("Available actions:", event.data.actions);
  console.log("Recommended:", event.data.recommendedAction);

  // 4. Approve: switch to autopilot to execute
  session.rpc.mode.set({ mode: "autopilot" });
});

// Mode change confirmed via event:
session.on("session.mode_changed", (event) => {
  console.log(`${event.data.previousMode} → ${event.data.newMode}`);
});
```

### Plan RPC methods

```typescript
// Read the plan
const plan = await session.rpc.plan.read();
// { exists: boolean, content: string | null, path: string | null }

// Update the plan
await session.rpc.plan.update({ content: "# Updated Plan\n..." });

// Delete the plan
await session.rpc.plan.delete();
```

### Plan change events

```typescript
session.on("session.plan_changed", (event) => {
  console.log(`Plan ${event.data.operation}`);
  // operation: "create" | "update" | "delete"
});
```

## Fleet mode

Fleet mode activates a background fleet of agents with an optional prompt:

```typescript
const result = await session.rpc.fleet.start({ prompt: "Review all files" });
// { started: boolean }
```

## Multi-client architecture

Multiple SDK clients can connect to the same CLI server and session via TCP.

### Setup

```typescript
// Client 1: starts the CLI server
const client1 = new CopilotClient({ useStdio: false });
const session1 = await client1.createSession({
  tools: [toolA],
  onPermissionRequest: approveAll,
});

// Get the port
const actualPort = (client1 as any).actualPort;

// Client 2: connects to the same server
const client2 = new CopilotClient({ cliUrl: `localhost:${actualPort}` });
const session2 = await client2.resumeSession(session1.sessionId, {
  tools: [toolB],           // toolB added to session; toolA preserved
  onPermissionRequest: approveAll,
});
// Model now sees both toolA and toolB
```

### Multi-client behaviors

- **Tools**: unioned from all connected clients. If a client disconnects, its tools are removed.
- **Events**: ALL events broadcast to ALL connected clients (via session events).
- **Permissions**: `permission.requested` broadcasts to all; first response wins.
- **External tools**: `external_tool.requested` broadcasts; the client with the matching handler responds.

### Observer client pattern

A client that only watches (never responds to permissions):

```typescript
const observer = await client2.resumeSession(sessionId, {
  onPermissionRequest: () => new Promise(() => {}), // never resolves
});
observer.on((event) => {
  console.log(`[observer] ${event.type}`);
});
```

## Ralph loop (autonomous development)

Fresh-context-per-iteration pattern for unattended AI development:

```typescript
import { CopilotClient, approveAll } from "@github/copilot-sdk";
import { readFile } from "node:fs/promises";

async function ralphLoop(promptFile: string, maxIterations = 50) {
  const client = new CopilotClient();
  await client.start();

  try {
    const prompt = await readFile(promptFile, "utf-8");

    for (let i = 1; i <= maxIterations; i++) {
      console.log(`--- Iteration ${i}/${maxIterations} ---`);

      const session = await client.createSession({
        model: "gpt-5.1-codex-mini",
        workingDirectory: process.cwd(),
        onPermissionRequest: approveAll,
      });

      session.on((event) => {
        if (event.type === "tool.execution_start") {
          console.log(`  tool: ${event.data.toolName}`);
        }
      });

      try {
        await session.sendAndWait({ prompt }, 600_000); // 10 min timeout
      } finally {
        await session.disconnect(); // fresh context next iteration
      }
    }
  } finally {
    await client.stop();
  }
}
```

### Ralph loop design principles

1. **Fresh context per iteration**: `disconnect()` after every pass — no context accumulation
2. **Disk as shared state**: `IMPLEMENTATION_PLAN.md` is the coordination mechanism between iterations
3. **Backpressure**: Tests/builds in `AGENTS.md` reject bad work before committing
4. **Two modes**: `plan` generates the plan; `build` implements from it
5. **`workingDirectory`**: pins sessions so file paths resolve correctly
6. **`approveAll`**: enables fully unattended operation

### Required project files

```
project-root/
├── PROMPT_plan.md          # planning mode instructions
├── PROMPT_build.md         # building mode instructions
├── AGENTS.md               # build/test/lint commands (keep < 60 lines)
├── IMPLEMENTATION_PLAN.md  # shared state between iterations
├── specs/                  # requirement specifications
└── src/                    # source code
```

## Steering and queueing

### Message modes

```typescript
// Enqueue (default) — queued if session is busy
await session.send({ prompt: "Task 1", mode: "enqueue" });

// Immediate — interrupts current work
await session.send({ prompt: "URGENT: stop and do this", mode: "immediate" });
```

### Pending messages

```typescript
session.on("pending_messages.modified", () => {
  console.log("Message queue changed");
});
```

## System message modes

```typescript
// Append mode (default): adds to Copilot's built-in system prompt
systemMessage: {
  mode: "append",
  content: "Always respond in bullet points.",
}

// Replace mode: replaces the entire system prompt (removes all SDK guardrails)
systemMessage: {
  mode: "replace",
  content: "You are a specialized code reviewer. Only review code, nothing else.",
}

// Context injection pattern:
systemMessage: {
  content: `
<context>
You are analyzing PRs for: ${owner}/${repo}
Project uses: React 19, TypeScript 5.7
</context>
<instructions>
- Use GitHub MCP Server tools to fetch PR data
- Focus on security and performance
</instructions>
`,
}
```

## Workspace file operations

When infinite sessions are enabled, access workspace files:

```typescript
// List workspace files
const { files } = await session.rpc.workspace.listFiles();

// Read a workspace file
const { content } = await session.rpc.workspace.readFile({ path: "plan.md" });

// Create/update a workspace file
await session.rpc.workspace.createFile({
  path: "notes.md",
  content: "# Session Notes\n...",
});
```

### Workspace file events

```typescript
session.on("session.workspace_file_changed", (event) => {
  console.log(`File ${event.data.operation}: ${event.data.path}`);
  // operation: "create" | "update"
});
```

## Compaction (manual trigger)

```typescript
const result = await session.rpc.compaction.compact();
// { success: boolean, tokensRemoved: number, messagesRemoved: number }
```

## Abort pattern

```typescript
// Start long-running work
await session.send({ prompt: "Analyze every file in the repo" });

// Monitor progress
session.on("tool.execution_start", (event) => {
  console.log(`Running: ${event.data.toolName}`);
});

// Abort after timeout or user request
setTimeout(async () => {
  await session.abort();
  // session.idle event fires after abort completes
  // Session remains usable for new messages
}, 60_000);
```

## Backend service pattern

```typescript
import express from "express";
import { CopilotClient, approveAll } from "@github/copilot-sdk";

const client = new CopilotClient({ cliUrl: "localhost:4321" });
const app = express();

app.post("/api/chat", async (req, res) => {
  const { sessionId, message } = req.body;

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

  const response = await session.sendAndWait({ prompt: message });
  res.json({ content: response?.data.content });
});
```

## Model management

```typescript
// List available models
const models = await client.listModels();
for (const model of models) {
  console.log(`${model.id}: ${model.name}`);
  console.log(`  Vision: ${model.capabilities.supports.vision}`);
  console.log(`  Context: ${model.capabilities.limits.max_context_window_tokens}`);
  if (model.policy) console.log(`  Policy: ${model.policy.state}`);
  if (model.billing) console.log(`  Multiplier: ${model.billing.multiplier}`);
}

// Switch model mid-session
await session.setModel("gpt-5");

// Get current model
const { modelId } = await session.rpc.model.getCurrent();

// Switch with reasoning effort
await session.rpc.model.switchTo({
  modelId: "gpt-5",
  reasoningEffort: "high",
});
```

## Scaling patterns

### Isolated CLI per user

```typescript
class CLIPool {
  private servers = new Map<string, CopilotClient>();

  async getClient(userId: string, token: string): Promise<CopilotClient> {
    if (!this.servers.has(userId)) {
      const client = new CopilotClient({
        githubToken: token,
        useLoggedInUser: false,
      });
      await client.start();
      this.servers.set(userId, client);
    }
    return this.servers.get(userId)!;
  }
}
```

### Shared CLI with session isolation

```typescript
const client = new CopilotClient({ cliUrl: "localhost:4321" });

// Use unique session IDs per user
const session = await client.createSession({
  sessionId: `${userId}-${purpose}-${Date.now()}`,
  onPermissionRequest: approveAll,
});
```

### Session cleanup

```typescript
const sessions = await client.listSessions();
const maxAge = 30 * 60 * 1000; // 30 minutes
for (const s of sessions) {
  if (Date.now() - s.modifiedTime.getTime() > maxAge) {
    await client.deleteSession(s.sessionId);
  }
}
```

## Health check

```typescript
async function checkHealth(): Promise<boolean> {
  try {
    const status = await client.getStatus();
    return status !== undefined;
  } catch {
    return false;
  }
}
```
