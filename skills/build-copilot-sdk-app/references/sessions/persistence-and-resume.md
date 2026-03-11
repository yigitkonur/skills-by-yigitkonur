# Session Persistence and Resumption

## How Persistence Works

Session state is persisted to disk automatically during normal operation. The CLI writes incremental checkpoints to `~/.copilot/session-state/{sessionId}/`. When `disconnect()` is called, in-memory resources are released but disk state remains intact. Call `client.resumeSession(sessionId)` from any client instance — even a different process — to restore the session and continue the conversation.

State lifecycle:

```
createSession()  →  Active  →  disconnect()  →  Persisted on disk
                                                        ↓
                                               resumeSession()  →  Active
```

## Creating a Resumable Session

Provide a stable `sessionId`. Without one, the CLI generates a random ID that is hard to reference later.

```typescript
import { CopilotClient, approveAll } from "@github/copilot-sdk";

const client = new CopilotClient();
await client.start();

const session = await client.createSession({
  sessionId: "user-alice-pr-review-42",  // encode ownership and purpose
  model: "gpt-4.1",
  onPermissionRequest: approveAll,
});

await session.sendAndWait({ prompt: "Review the diff in PR #42" });

// Persist to disk and release in-memory resources
await session.disconnect();
await client.stop();
```

Session ID naming conventions:

| Pattern | Example | Use case |
|---|---|---|
| `user-{userId}-{taskId}` | `user-alice-pr-review-42` | Multi-user apps |
| `tenant-{tenantId}-{workflow}` | `tenant-acme-onboarding` | Multi-tenant SaaS |
| `{userId}-{taskType}-{timestamp}` | `alice-deploy-1706932800` | Time-based cleanup |

Generate IDs programmatically:

```typescript
function makeSessionId(userId: string, taskType: string): string {
  return `${userId}-${taskType}-${Date.now()}`;
}
```

## What Is Persisted to Disk

Files are written to `~/.copilot/session-state/{sessionId}/`:

```
~/.copilot/session-state/user-alice-pr-review-42/
├── checkpoints/
│   ├── 001.json    # Initial state snapshot
│   ├── 002.json    # After first turn
│   └── ...         # Incremental checkpoints
├── plan.md         # Agent planning state (if any)
└── files/
    ├── analysis.md # Artifacts created by the agent
    └── notes.txt
```

| Data | Persisted | Notes |
|---|---|---|
| Conversation history | Yes | Full message thread including tool calls |
| Tool call results | Yes | Cached in checkpoints for context |
| Agent planning state | Yes | Written to `plan.md` |
| Session artifacts | Yes | Stored under `files/` |
| Provider / API keys | No | Never written to disk; must re-provide on resume |
| In-memory tool state | No | Design tools to be stateless |

The `session.workspacePath` property exposes the absolute path to this directory when infinite sessions are enabled. Use it to access artifacts the agent created:

```typescript
if (session.workspacePath) {
  const planPath = `${session.workspacePath}/plan.md`;
  // read plan.md, list files/, etc.
}
```

## resumeSession() — Restoring a Session

```typescript
// Minimal resume — all original settings are restored from disk
const session = await client.resumeSession("user-alice-pr-review-42", {
  onPermissionRequest: approveAll,
});

await session.sendAndWait({ prompt: "What did we discuss earlier?" });
await session.disconnect();
```

`resumeSession` accepts a `ResumeSessionConfig` which is a subset of `SessionConfig`. It lets you override runtime settings without touching persisted conversation state:

```typescript
const session = await client.resumeSession("user-alice-pr-review-42", {
  onPermissionRequest: approveAll,
  model: "claude-sonnet-4.5",   // switch model for this session
  reasoningEffort: "high",
  streaming: true,
  workingDirectory: "/new/workspace/path",
  systemMessage: { mode: "append", content: "Focus on security." },
  availableTools: ["read_file", "list_directory"],
  mcpServers: { /* updated servers */ },
  customAgents: [ /* updated agents */ ],
  agent: "code-reviewer",
  skillDirectories: ["/updated/skills"],
  disabledSkills: ["old-skill"],
  infiniteSessions: { enabled: true },
  disableResume: false,  // true = reconnect without emitting session.resume event
});
```

`disableResume: true` is for reconnecting to an already-active session without triggering resume-related side effects (e.g. the agent sending a "welcome back" message).

## BYOK Sessions — Re-Provide Credentials on Resume

API keys are never persisted. When you created the session with a custom provider, you must re-supply `provider` on every resume:

```typescript
// Original session creation
const session = await client.createSession({
  sessionId: "byok-session-001",
  provider: {
    type: "azure",
    baseUrl: "https://my-resource.openai.azure.com",
    apiKey: process.env.AZURE_OPENAI_KEY,
    azure: { apiVersion: "2024-10-21" },
  },
  onPermissionRequest: approveAll,
});

// Resume — credentials must be provided again
const resumed = await client.resumeSession("byok-session-001", {
  onPermissionRequest: approveAll,
  provider: {
    type: "azure",
    baseUrl: "https://my-resource.openai.azure.com",
    apiKey: process.env.AZURE_OPENAI_KEY,  // required every time
    azure: { apiVersion: "2024-10-21" },
  },
});
```

## Cross-Client Session Resumption

Any `CopilotClient` instance that can read `~/.copilot/session-state/` can resume a session. This enables migration across processes, containers, and machines (when storage is shared):

```typescript
// Process A — creates and persists session
const clientA = new CopilotClient();
await clientA.start();
const sessionA = await clientA.createSession({
  sessionId: "shared-workflow-001",
  onPermissionRequest: approveAll,
});
await sessionA.sendAndWait({ prompt: "Step 1: gather requirements" });
await sessionA.disconnect();
await clientA.stop();

// Process B — resumes the same session (different process, same storage)
const clientB = new CopilotClient();
await clientB.start();
const sessionB = await clientB.resumeSession("shared-workflow-001", {
  onPermissionRequest: approveAll,
});
await sessionB.sendAndWait({ prompt: "Step 2: implement the plan" });
await sessionB.disconnect();
await clientB.stop();
```

For containerized deployments, mount session state to persistent storage:

```yaml
# Docker Compose example
volumes:
  - copilot-sessions:/home/app/.copilot/session-state
```

## Session State Lifecycle

```
createSession(sessionId)
    → Active: sends/receives messages, events flow
    ↓
disconnect()
    → Persisted: conversation on disk, in-memory cleared, no events
    ↓
resumeSession(sessionId)
    → Active: conversation restored, new events flow
    ↓
deleteSession(sessionId)   [irreversible]
    → Deleted: all disk data removed, cannot be resumed
```

Key invariants:
- `disconnect()` preserves disk state; `deleteSession()` destroys it permanently
- After `disconnect()`, the `CopilotSession` object is unusable; get a new one from `resumeSession()`
- Calling `disconnect()` on an already-disconnected session is safe (idempotent on the CLI side)

## Session Listing and Cleanup

```typescript
// List all sessions
const sessions = await client.listSessions();
for (const s of sessions) {
  console.log(s.sessionId, s.startTime, s.modifiedTime, s.summary);
}

// Filter by git context
const repoSessions = await client.listSessions({
  repository: "owner/repo",
  branch: "main",
});

// Delete permanently (cannot be resumed after this)
await client.deleteSession("user-alice-pr-review-42");

// Cleanup sessions older than 7 days
async function purgeOldSessions(client: CopilotClient, maxAgeMs: number) {
  const sessions = await client.listSessions();
  const cutoff = Date.now() - maxAgeMs;
  for (const s of sessions) {
    if (new Date(s.modifiedTime).getTime() < cutoff) {
      await client.deleteSession(s.sessionId);
    }
  }
}
await purgeOldSessions(client, 7 * 24 * 60 * 60 * 1000);
```

## Complete Persistence Example with Error Handling

```typescript
import { CopilotClient, approveAll } from "@github/copilot-sdk";

async function runWithPersistence(sessionId: string, prompt: string) {
  const client = new CopilotClient();
  await client.start();

  let session;
  const sessions = await client.listSessions();
  const exists = sessions.some(s => s.sessionId === sessionId);

  try {
    if (exists) {
      session = await client.resumeSession(sessionId, {
        onPermissionRequest: approveAll,
      });
      console.log(`Resumed session: ${sessionId}`);
    } else {
      session = await client.createSession({
        sessionId,
        model: "gpt-4.1",
        onPermissionRequest: approveAll,
      });
      console.log(`Created new session: ${sessionId}`);
    }

    const response = await session.sendAndWait({ prompt }, 120_000);
    console.log("Response:", response?.data.content);
    return response;
  } catch (err) {
    console.error("Session error:", err);
    throw err;
  } finally {
    if (session) {
      // Always disconnect to flush state to disk cleanly
      await session.disconnect().catch(() => {});
    }
    await client.stop();
  }
}
```

## Concurrency Warning

The SDK has no built-in session locking. If two clients resume and write to the same session concurrently, behavior is undefined. Implement application-level locking:

```typescript
// Redis-based distributed lock
async function withSessionLock<T>(sessionId: string, fn: () => Promise<T>): Promise<T> {
  const lockKey = `copilot:session-lock:${sessionId}`;
  const acquired = await redis.set(lockKey, "1", "NX", "EX", 300);
  if (!acquired) throw new Error(`Session ${sessionId} is in use`);
  try {
    return await fn();
  } finally {
    await redis.del(lockKey);
  }
}
```
