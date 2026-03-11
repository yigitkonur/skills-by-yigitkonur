# onErrorOccurred Hook Reference

React to runtime errors before they reach the user. Use this hook to classify errors by type, route them to external monitoring, customize user-facing messages, implement retry logic, and suppress non-critical noise. The hook fires for every error the runtime detects — including model failures, tool execution errors, system faults, and user input issues.

## Type Signature

```typescript
import type {
  ErrorOccurredHookInput,
  ErrorOccurredHookOutput,
  SessionHooks,
} from "@github/copilot-sdk";

// Handler signature
type ErrorOccurredHandler = (
  input: ErrorOccurredHookInput,
  invocation: { sessionId: string }
) => Promise<ErrorOccurredHookOutput | void> | ErrorOccurredHookOutput | void;

// Register via SessionConfig.hooks
const hooks: SessionHooks = {
  onErrorOccurred: async (input, invocation) => { /* ... */ },
};
```

## Input Fields

| Field | Type | Description |
|-------|------|-------------|
| `error` | `string` | Error message string |
| `errorContext` | `"model_call" \| "tool_execution" \| "system" \| "user_input"` | Category of the error source |
| `recoverable` | `boolean` | Whether the runtime considers this error recoverable |
| `timestamp` | `number` | Unix epoch milliseconds when the error occurred |
| `cwd` | `string` | Working directory of the session at error time |

Access `invocation.sessionId` for the session identifier. In e2e tests, `input.error` is always a non-empty string, `input.cwd` is always defined, and `input.recoverable` is always a boolean.

### Error Context Categories

| Value | Meaning |
|-------|---------|
| `"model_call"` | LLM API request failed (timeout, rate limit, auth, network) |
| `"tool_execution"` | A tool handler threw or returned an error |
| `"system"` | Internal runtime or infrastructure fault |
| `"user_input"` | The user's input could not be processed |

## Output Fields

Return `void` or `undefined` to use the default error handling behavior. Return an object to control the response:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `errorHandling` | `"retry" \| "skip" \| "abort"` | runtime default | How to proceed after the error |
| `retryCount` | `number` | — | Number of retry attempts when `errorHandling` is `"retry"` |
| `userNotification` | `string` | — | Custom message shown to the user instead of the raw error |
| `suppressOutput` | `boolean` | `false` | When `true`, suppress the error output entirely |

Returning `null` is equivalent to `void`.

## Pattern: Error Classification and Routing

Dispatch errors to different handlers based on `errorContext` and `recoverable`.

```typescript
const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onErrorOccurred: async (input, invocation) => {
      switch (input.errorContext) {
        case "model_call":
          // Network or API errors — log at warning level, may self-resolve
          void logWarning("model_call_error", {
            sessionId: invocation.sessionId,
            error: input.error,
            recoverable: input.recoverable,
          });
          break;

        case "tool_execution":
          // Tool errors — log at info level, usually user-actionable
          void logInfo("tool_execution_error", {
            sessionId: invocation.sessionId,
            error: input.error,
          });
          break;

        case "system":
          // System faults — always alert, may indicate infrastructure issues
          void alertOps("system_error", {
            sessionId: invocation.sessionId,
            error: input.error,
            recoverable: input.recoverable,
            timestamp: new Date(input.timestamp).toISOString(),
          });
          break;

        case "user_input":
          // User input issues — silent, no external reporting needed
          break;
      }
    },
  },
});
```

## Pattern: Retry with Exponential Backoff for Transient Failures

Request automatic retries for recoverable model call errors.

```typescript
const RATE_LIMIT_PATTERN = /rate.?limit|too many requests|429/i;
const TIMEOUT_PATTERN = /timeout|timed out|ETIMEDOUT/i;

const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onErrorOccurred: async (input) => {
      if (input.errorContext !== "model_call") return;
      if (!input.recoverable) return;

      if (RATE_LIMIT_PATTERN.test(input.error)) {
        return {
          errorHandling: "retry",
          retryCount: 3,
          userNotification: "Rate limit reached. Retrying automatically — please wait.",
        };
      }

      if (TIMEOUT_PATTERN.test(input.error)) {
        return {
          errorHandling: "retry",
          retryCount: 2,
          userNotification: "Request timed out. Retrying...",
        };
      }
    },
  },
});
```

The `retryCount` field tells the runtime how many attempts to make. The runtime controls actual backoff timing — you cannot set delay from within the hook. For custom backoff, implement retry at the call site using `session.sendAndWait()` in a loop instead.

## Pattern: Error Reporting to External Systems

Forward errors to Sentry, Datadog, or a custom monitoring endpoint without blocking recovery.

```typescript
const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onErrorOccurred: async (input, invocation) => {
      // Non-blocking — fire and forget
      void reportToMonitoring({
        service: "copilot-sdk",
        sessionId: invocation.sessionId,
        errorContext: input.errorContext,
        error: input.error,
        recoverable: input.recoverable,
        cwd: input.cwd,
        timestamp: new Date(input.timestamp).toISOString(),
        severity: input.recoverable ? "warning" : "error",
      });

      // Alert pager for critical unrecoverable system errors
      if (input.errorContext === "system" && !input.recoverable) {
        void triggerPagerAlert({
          title: `Unrecoverable system error in session ${invocation.sessionId}`,
          body: input.error,
        });
      }
    },
  },
});
```

Always use `void` for monitoring calls — blocking the error hook delays recovery and adds user-visible latency.

## Pattern: User-Friendly Error Messages

Replace technical error strings with actionable user-facing messages.

```typescript
const USER_MESSAGES: Partial<Record<string, string>> = {
  model_call:
    "The AI model is temporarily unavailable. Please try again in a moment.",
  tool_execution:
    "A tool encountered an error. Check the inputs and try again.",
  system:
    "An unexpected error occurred. If this persists, contact support.",
  user_input:
    "Your input could not be processed. Please rephrase and try again.",
};

const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onErrorOccurred: async (input) => {
      const message = USER_MESSAGES[input.errorContext];
      if (message) {
        return { userNotification: message };
      }
    },
  },
});
```

## Pattern: Suppress Recoverable Noise

Hide recoverable tool errors from the conversation when they are expected and self-correcting.

```typescript
const EXPECTED_TOOL_ERRORS = new Set([
  "file not found",
  "no such file or directory",
  "ENOENT",
]);

const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onErrorOccurred: async (input) => {
      if (
        input.errorContext === "tool_execution" &&
        input.recoverable &&
        EXPECTED_TOOL_ERRORS.some((msg) =>
          input.error.toLowerCase().includes(msg.toLowerCase())
        )
      ) {
        // Suppress — the model will handle not-found errors without user notification
        return { suppressOutput: true };
      }
    },
  },
});
```

Never suppress unrecoverable or system-level errors — they indicate real failures the user needs to know about.

## Pattern: Error Frequency Tracking

Detect recurring error patterns and escalate when a threshold is crossed.

```typescript
interface ErrorFrequency {
  count: number;
  firstSeen: number;
  lastSeen: number;
}

const errorFrequency = new Map<string, ErrorFrequency>();
const ALERT_THRESHOLD = 5;
const FREQUENCY_WINDOW_MS = 5 * 60_000; // 5 minutes

const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onErrorOccurred: async (input, invocation) => {
      const key = `${input.errorContext}:${input.error.slice(0, 60)}`;
      const now = input.timestamp;

      const freq = errorFrequency.get(key) ?? {
        count: 0,
        firstSeen: now,
        lastSeen: now,
      };

      // Reset if outside the frequency window
      if (now - freq.firstSeen > FREQUENCY_WINDOW_MS) {
        freq.count = 0;
        freq.firstSeen = now;
      }

      freq.count++;
      freq.lastSeen = now;
      errorFrequency.set(key, freq);

      if (freq.count >= ALERT_THRESHOLD) {
        void alertOps("recurring_error", {
          sessionId: invocation.sessionId,
          errorKey: key,
          count: freq.count,
          windowMs: FREQUENCY_WINDOW_MS,
        });
      }
    },
  },
});
```

Clean up `errorFrequency` entries in `onSessionEnd` for long-running processes.

## Pattern: Graceful Degradation with Abort

Abort the session on unrecoverable system errors to avoid serving degraded responses.

```typescript
const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onErrorOccurred: async (input) => {
      if (input.errorContext === "system" && !input.recoverable) {
        return {
          errorHandling: "abort",
          userNotification:
            "A critical error has occurred. The session cannot continue safely. " +
            "Please start a new session. If the problem persists, contact support.",
        };
      }

      if (input.errorContext === "model_call" && !input.recoverable) {
        return {
          errorHandling: "abort",
          userNotification:
            "The AI model is unavailable. Please try again later.",
        };
      }
    },
  },
});
```

## Pattern: Cross-Hook Context for Richer Error Reports

Combine `onPreToolUse` tracking with `onErrorOccurred` to include the last tool call in error reports.

```typescript
const sessionContext = new Map<string, { lastTool?: string; lastPrompt?: string }>();

const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onUserPromptSubmitted: async (input, invocation) => {
      const ctx = sessionContext.get(invocation.sessionId) ?? {};
      ctx.lastPrompt = input.prompt.slice(0, 120);
      sessionContext.set(invocation.sessionId, ctx);
    },

    onPreToolUse: async (input, invocation) => {
      const ctx = sessionContext.get(invocation.sessionId) ?? {};
      ctx.lastTool = input.toolName;
      sessionContext.set(invocation.sessionId, ctx);
      return { permissionDecision: "allow" };
    },

    onErrorOccurred: async (input, invocation) => {
      const ctx = sessionContext.get(invocation.sessionId);
      void reportError({
        sessionId: invocation.sessionId,
        error: input.error,
        errorContext: input.errorContext,
        recoverable: input.recoverable,
        lastTool: ctx?.lastTool,
        lastPrompt: ctx?.lastPrompt,
        timestamp: new Date(input.timestamp).toISOString(),
      });
    },

    onSessionEnd: async (_input, invocation) => {
      sessionContext.delete(invocation.sessionId);
    },
  },
});
```

## Common Mistakes

- Awaiting slow monitoring calls inside the hook blocks error recovery — always use `void` for external reporting.
- Suppressing errors without logging them first creates invisible failures that are impossible to debug later. Log first, then suppress.
- Returning `{ errorHandling: "retry", retryCount: 0 }` is a no-op — if you want to retry, set `retryCount` to 1 or more.
- Using `errorHandling: "abort"` for recoverable errors is overly aggressive and worsens the user experience — only abort when `input.recoverable` is `false`.
- Not handling `errorContext === "system"` separately means critical infrastructure failures receive the same treatment as routine tool errors, delaying incident response.
- Holding growing maps (`errorFrequency`, `sessionContext`) without cleanup in `onSessionEnd` causes unbounded memory growth in multi-session processes.
