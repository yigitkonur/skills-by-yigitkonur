# Session Lifecycle Hooks Reference

`onSessionStart` and `onSessionEnd` bracket every session. Use them to initialize per-session state, load user context, set up resources, collect metrics, and clean up on exit. Both hooks receive the `sessionId` via `invocation` — use it as the key for any session-scoped storage.

## onSessionStart

### Type Signature

```typescript
import type {
  SessionStartHookInput,
  SessionStartHookOutput,
  SessionHooks,
} from "@github/copilot-sdk";

// Handler signature
type SessionStartHandler = (
  input: SessionStartHookInput,
  invocation: { sessionId: string }
) => Promise<SessionStartHookOutput | void> | SessionStartHookOutput | void;

// Register via SessionConfig.hooks
const hooks: SessionHooks = {
  onSessionStart: async (input, invocation) => { /* ... */ },
};
```

### Input Fields

| Field | Type | Description |
|-------|------|-------------|
| `source` | `"startup" \| "resume" \| "new"` | How the session was initiated |
| `initialPrompt` | `string \| undefined` | First prompt if provided at creation time |
| `timestamp` | `number` | Unix epoch milliseconds when the hook fired |
| `cwd` | `string` | Working directory of the new session |

The `source` field distinguishes cold starts from resumed sessions — branch your initialization logic on it. Confirmed by e2e tests: on `client.createSession()`, `source` is `"new"` and `timestamp` is positive.

### Output Fields

| Field | Type | Description |
|-------|------|-------------|
| `additionalContext` | `string` | Context string injected into the session at start |
| `modifiedConfig` | `Record<string, unknown>` | Config overrides applied to the session |

Return `void` when no context or config override is needed. The hook must return before the session is fully ready — keep it fast.

## onSessionEnd

### Type Signature

```typescript
import type {
  SessionEndHookInput,
  SessionEndHookOutput,
  SessionHooks,
} from "@github/copilot-sdk";

// Handler signature
type SessionEndHandler = (
  input: SessionEndHookInput,
  invocation: { sessionId: string }
) => Promise<SessionEndHookOutput | void> | SessionEndHookOutput | void;
```

### Input Fields

| Field | Type | Description |
|-------|------|-------------|
| `reason` | `"complete" \| "error" \| "abort" \| "timeout" \| "user_exit"` | Termination cause |
| `finalMessage` | `string \| undefined` | Last message in the session if available |
| `error` | `string \| undefined` | Error string when `reason` is `"error"` |
| `timestamp` | `number` | Unix epoch milliseconds when the hook fired |
| `cwd` | `string` | Working directory at session end |

Always handle all five `reason` values — sessions do not always end cleanly. The hook may not fire if the host process crashes; design cleanup to be idempotent.

### Output Fields

| Field | Type | Description |
|-------|------|-------------|
| `suppressOutput` | `boolean` | Suppress the final session output |
| `cleanupActions` | `string[]` | Labels describing cleanup actions performed (for logging) |
| `sessionSummary` | `string` | Summary written to logs or analytics |

## Pattern: Session Initialization with User Context

Load user-specific settings and inject them as context at session start.

```typescript
interface SessionState {
  startTime: number;
  userId?: string;
  preferences?: Record<string, string>;
}

const sessionStore = new Map<string, SessionState>();

const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onSessionStart: async (input, invocation) => {
      // Initialize per-session state
      const state: SessionState = { startTime: input.timestamp };
      sessionStore.set(invocation.sessionId, state);

      // Load user context (cached; do not hit the DB on every session start)
      const user = await resolveUserFromCwd(input.cwd);
      if (user) {
        state.userId = user.id;
        state.preferences = user.preferences;
      }

      const contextLines: string[] = [];
      if (user?.preferences?.language) {
        contextLines.push(`Response language: ${user.preferences.language}`);
      }
      if (user?.preferences?.codeStyle) {
        contextLines.push(`Code style: ${user.preferences.codeStyle}`);
      }

      return contextLines.length
        ? { additionalContext: contextLines.join("\n") }
        : undefined;
    },
  },
});
```

## Pattern: Differentiate Resumed vs. New Sessions

Inject different context depending on whether the session is a cold start or a resume.

```typescript
const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onSessionStart: async (input, invocation) => {
      if (input.source === "resume") {
        // Load prior session state to restore continuity
        const priorState = await loadSessionSnapshot(invocation.sessionId);
        if (priorState) {
          return {
            additionalContext:
              `Session resumed. Prior context:\n` +
              `- Last topic: ${priorState.lastTopic}\n` +
              `- Open files: ${priorState.openFiles.join(", ")}`,
          };
        }
      }

      if (input.source === "new") {
        // Detect project environment on fresh start
        const project = await detectProject(input.cwd);
        return {
          additionalContext:
            `New session started.\n` +
            `Project: ${project.name} (${project.type})\n` +
            `Language: ${project.primaryLanguage}`,
        };
      }
    },
  },
});
```

## Pattern: Resource Setup and Teardown

Allocate resources on start, release them on end. Track open handles in a session-keyed map.

```typescript
interface SessionResources {
  dbConnection: DatabaseConnection;
  tempDir: string;
  openHandles: Set<string>;
}

const resources = new Map<string, SessionResources>();

const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onSessionStart: async (input, invocation) => {
      const dbConnection = await openDatabaseConnection();
      const tempDir = await createTempDir(`session-${invocation.sessionId}`);

      resources.set(invocation.sessionId, {
        dbConnection,
        tempDir,
        openHandles: new Set(),
      });
    },

    onSessionEnd: async (input, invocation) => {
      const res = resources.get(invocation.sessionId);
      if (!res) return;

      // Release all resources regardless of end reason
      await res.dbConnection.close();
      await removeTempDir(res.tempDir);

      resources.delete(invocation.sessionId);

      return {
        cleanupActions: ["db_connection_closed", "temp_dir_removed"],
      };
    },
  },
});
```

## Pattern: Metrics Collection and Reporting

Measure session duration, count prompts and tool calls, and report on end.

```typescript
interface SessionMetrics {
  startTime: number;
  promptCount: number;
  toolCallCount: number;
  errorCount: number;
}

const metrics = new Map<string, SessionMetrics>();

const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onSessionStart: async (input, invocation) => {
      metrics.set(invocation.sessionId, {
        startTime: input.timestamp,
        promptCount: 0,
        toolCallCount: 0,
        errorCount: 0,
      });
    },

    onUserPromptSubmitted: async (_input, invocation) => {
      const m = metrics.get(invocation.sessionId);
      if (m) m.promptCount++;
    },

    onPreToolUse: async (_input, invocation) => {
      const m = metrics.get(invocation.sessionId);
      if (m) m.toolCallCount++;
      return { permissionDecision: "allow" };
    },

    onErrorOccurred: async (_input, invocation) => {
      const m = metrics.get(invocation.sessionId);
      if (m) m.errorCount++;
    },

    onSessionEnd: async (input, invocation) => {
      const m = metrics.get(invocation.sessionId);
      if (!m) return;

      const durationMs = input.timestamp - m.startTime;

      void reportMetrics({
        sessionId: invocation.sessionId,
        durationMs,
        promptCount: m.promptCount,
        toolCallCount: m.toolCallCount,
        errorCount: m.errorCount,
        endReason: input.reason,
      });

      metrics.delete(invocation.sessionId);

      return {
        sessionSummary:
          `Duration: ${durationMs}ms, ` +
          `Prompts: ${m.promptCount}, ` +
          `Tools: ${m.toolCallCount}, ` +
          `Errors: ${m.errorCount}, ` +
          `End: ${input.reason}`,
      };
    },
  },
});
```

## Pattern: Save State for Resumable Sessions

Persist session state on clean exit so `onSessionStart` can restore it on `source === "resume"`.

```typescript
const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onSessionEnd: async (input, invocation) => {
      // Only persist on clean exits
      if (input.reason === "error" || input.reason === "abort") return;

      await saveSessionSnapshot(invocation.sessionId, {
        endTime: input.timestamp,
        cwd: input.cwd,
        reason: input.reason,
        finalMessage: input.finalMessage,
      });
    },
  },
});
```

## Pattern: Error Handling Within Lifecycle Hooks

Wrap hook body in try/catch to prevent hook failures from propagating into the session.

```typescript
const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onSessionStart: async (input, invocation) => {
      try {
        const ctx = await loadHeavyContext(input.cwd);
        return { additionalContext: ctx };
      } catch (err) {
        // Log but do not rethrow — let the session start without context
        console.error(
          `[${invocation.sessionId}] onSessionStart failed:`,
          err instanceof Error ? err.message : String(err)
        );
        return;
      }
    },

    onSessionEnd: async (input, invocation) => {
      try {
        await persistState(invocation.sessionId, input);
      } catch (err) {
        console.error(
          `[${invocation.sessionId}] onSessionEnd cleanup failed:`,
          err instanceof Error ? err.message : String(err)
        );
        // Return cleanupActions to record what was attempted
        return { cleanupActions: ["persist_state_failed"] };
      }
    },
  },
});
```

## Common Mistakes

- Throwing an unhandled error from `onSessionStart` may block session initialization. Always catch and handle errors internally.
- Keeping large objects in `sessionStore` / `metrics` maps without deleting them in `onSessionEnd` causes process-level memory leaks over many sessions.
- Assuming `onSessionEnd` always fires is wrong — if the host process is killed, it will not. Make cleanup idempotent and run it in process shutdown handlers as a backstop.
- Performing slow synchronous operations in `onSessionStart` delays session readiness for the user. Cache expensive lookups (project detection, DB queries) across sessions where possible.
- Not checking `input.source` in `onSessionStart` and injecting "new session" context on every resume creates confusing duplicate context on resumed sessions.
