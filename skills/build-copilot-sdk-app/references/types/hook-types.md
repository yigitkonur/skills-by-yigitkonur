# Hook Types — `@github/copilot-sdk`

Complete type reference for the session hook system in the GitHub Copilot SDK.
Hooks let you intercept and modify behavior at key lifecycle points: before/after
tool execution, on prompt submission, at session boundaries, and on errors.

---

## Import Patterns

```typescript
// Named imports (recommended)
import type {
  SessionHooks,
  BaseHookInput,
  PreToolUseHookInput,
  PreToolUseHookOutput,
  PreToolUseHandler,
  PostToolUseHookInput,
  PostToolUseHookOutput,
  PostToolUseHandler,
  UserPromptSubmittedHookInput,
  UserPromptSubmittedHookOutput,
  UserPromptSubmittedHandler,
  SessionStartHookInput,
  SessionStartHookOutput,
  SessionStartHandler,
  SessionEndHookInput,
  SessionEndHookOutput,
  SessionEndHandler,
  ErrorOccurredHookInput,
  ErrorOccurredHookOutput,
  ErrorOccurredHandler,
} from "@github/copilot-sdk";

// Runtime import for passing hooks to session
import { createSession } from "@github/copilot-sdk";
```

---

## `SessionHooks`

Top-level interface passed to `createSession()`. Every property is optional.

```typescript
interface SessionHooks {
  onPreToolUse?: PreToolUseHandler;
  onPostToolUse?: PostToolUseHandler;
  onUserPromptSubmitted?: UserPromptSubmittedHandler;
  onSessionStart?: SessionStartHandler;
  onSessionEnd?: SessionEndHandler;
  onErrorOccurred?: ErrorOccurredHandler;
}
```

**Usage:**

```typescript
const session = createSession({
  hooks: {
    onPreToolUse: async (input, invocation) => { /* ... */ },
    onPostToolUse: async (input, invocation) => { /* ... */ },
    onUserPromptSubmitted: async (input, invocation) => { /* ... */ },
    onSessionStart: async (input, invocation) => { /* ... */ },
    onSessionEnd: async (input, invocation) => { /* ... */ },
    onErrorOccurred: async (input, invocation) => { /* ... */ },
  },
});
```

---

## `BaseHookInput`

Shared base for every hook input. All hook-specific inputs extend this.

```typescript
interface BaseHookInput {
  timestamp: number;   // Unix timestamp in milliseconds (Date.now())
  cwd: string;         // Current working directory of the session
}
```

---

## Hook 1: Pre-Tool Use

Fires **before** a tool executes. Use it to inspect/modify arguments, enforce
permissions, inject context, or suppress output.

### `PreToolUseHookInput`

```typescript
interface PreToolUseHookInput extends BaseHookInput {
  toolName: string;     // Name of the tool about to execute
  toolArgs: unknown;    // Arguments the model passed to the tool
}
```

| Property    | Type      | Description                          |
|-------------|-----------|--------------------------------------|
| `timestamp` | `number`  | Unix ms when the hook fired          |
| `cwd`       | `string`  | Session working directory            |
| `toolName`  | `string`  | Identifier of the tool to be called  |
| `toolArgs`  | `unknown` | Raw arguments passed to the tool     |

### `PreToolUseHookOutput`

```typescript
interface PreToolUseHookOutput {
  permissionDecision?: "allow" | "deny" | "ask";  // Override permission handler
  permissionDecisionReason?: string;                // Human-readable reason
  modifiedArgs?: unknown;                           // Rewritten tool arguments
  additionalContext?: string;                       // Injected into conversation
  suppressOutput?: boolean;                         // Hide tool output from model
}
```

| Property                   | Type                              | Description                                      |
|----------------------------|-----------------------------------|--------------------------------------------------|
| `permissionDecision`       | `"allow" \| "deny" \| "ask"`     | Overrides the permission handler for this call    |
| `permissionDecisionReason` | `string`                          | Reason shown when decision is `deny` or `ask`    |
| `modifiedArgs`             | `unknown`                         | Replacement arguments sent to the tool           |
| `additionalContext`        | `string`                          | Extra context injected into the conversation     |
| `suppressOutput`           | `boolean`                         | If `true`, tool output is hidden from the model  |

### `PreToolUseHandler`

```typescript
type PreToolUseHandler = (
  input: PreToolUseHookInput,
  invocation: { sessionId: string }
) => Promise<PreToolUseHookOutput | void> | PreToolUseHookOutput | void;
```

---

## Hook 2: Post-Tool Use

Fires **after** a tool finishes. Use it for audit logging, result transformation,
or injecting follow-up context.

### `PostToolUseHookInput`

```typescript
interface PostToolUseHookInput extends BaseHookInput {
  toolName: string;               // Name of the tool that executed
  toolArgs: unknown;              // Arguments the tool received
  toolResult: ToolResultObject;   // The actual result returned by the tool
}
```

| Property     | Type               | Description                       |
|--------------|--------------------|-----------------------------------|
| `timestamp`  | `number`           | Unix ms when the hook fired       |
| `cwd`        | `string`           | Session working directory         |
| `toolName`   | `string`           | Identifier of the executed tool   |
| `toolArgs`   | `unknown`          | Arguments the tool received       |
| `toolResult` | `ToolResultObject` | Full result object from the tool  |

### `PostToolUseHookOutput`

```typescript
interface PostToolUseHookOutput {
  modifiedResult?: ToolResultObject;   // Replacement for the entire tool result
  additionalContext?: string;          // Injected into conversation after the result
  suppressOutput?: boolean;            // Hide tool output from the model
}
```

| Property            | Type               | Description                                        |
|---------------------|--------------------|----------------------------------------------------|
| `modifiedResult`    | `ToolResultObject` | Replaces the **entire** original tool result        |
| `additionalContext` | `string`           | Extra context injected after the tool result        |
| `suppressOutput`    | `boolean`          | If `true`, tool output is hidden from the model     |

### `PostToolUseHandler`

```typescript
type PostToolUseHandler = (
  input: PostToolUseHookInput,
  invocation: { sessionId: string }
) => Promise<PostToolUseHookOutput | void> | PostToolUseHookOutput | void;
```

---

## Hook 3: User Prompt Submitted

Fires when a user submits a prompt, **before** it reaches the model. Use it for
prompt rewriting, guardrails, or context injection.

### `UserPromptSubmittedHookInput`

```typescript
interface UserPromptSubmittedHookInput extends BaseHookInput {
  prompt: string;   // The raw prompt text submitted by the user
}
```

| Property    | Type     | Description                     |
|-------------|----------|---------------------------------|
| `timestamp` | `number` | Unix ms when the hook fired     |
| `cwd`       | `string` | Session working directory       |
| `prompt`    | `string` | The user's submitted prompt     |

### `UserPromptSubmittedHookOutput`

```typescript
interface UserPromptSubmittedHookOutput {
  modifiedPrompt?: string;         // Rewritten prompt sent to the model
  additionalContext?: string;      // Context injected into the conversation
  suppressOutput?: boolean;        // Suppress from model processing
}
```

| Property            | Type      | Description                                      |
|---------------------|-----------|--------------------------------------------------|
| `modifiedPrompt`    | `string`  | Replaces the original prompt sent to the model   |
| `additionalContext` | `string`  | Extra context injected alongside the prompt      |
| `suppressOutput`    | `boolean` | If `true`, suppresses the prompt from the model  |

### `UserPromptSubmittedHandler`

```typescript
type UserPromptSubmittedHandler = (
  input: UserPromptSubmittedHookInput,
  invocation: { sessionId: string }
) => Promise<UserPromptSubmittedHookOutput | void> | UserPromptSubmittedHookOutput | void;
```

---

## Hook 4: Session Start

Fires when a session initializes. Use it for configuration overrides, loading
user preferences, or injecting system-level context.

### `SessionStartHookInput`

```typescript
interface SessionStartHookInput extends BaseHookInput {
  source: "startup" | "resume" | "new";   // How the session was initiated
  initialPrompt?: string;                  // First prompt, if available
}
```

| Property        | Type                                  | Description                           |
|-----------------|---------------------------------------|---------------------------------------|
| `timestamp`     | `number`                              | Unix ms when the hook fired           |
| `cwd`           | `string`                              | Session working directory             |
| `source`        | `"startup" \| "resume" \| "new"`     | How the session was initiated         |
| `initialPrompt` | `string \| undefined`                | The first prompt, if already known    |

### `SessionStartHookOutput`

```typescript
interface SessionStartHookOutput {
  additionalContext?: string;                    // Context injected at session start
  modifiedConfig?: Record<string, unknown>;      // Configuration overrides
}
```

| Property            | Type                          | Description                                 |
|---------------------|-------------------------------|---------------------------------------------|
| `additionalContext` | `string`                      | System-level context injected at startup    |
| `modifiedConfig`    | `Record<string, unknown>`     | Key-value overrides for session config      |

### `SessionStartHandler`

```typescript
type SessionStartHandler = (
  input: SessionStartHookInput,
  invocation: { sessionId: string }
) => Promise<SessionStartHookOutput | void> | SessionStartHookOutput | void;
```

---

## Hook 5: Session End

Fires when a session terminates. Use it for cleanup, summary persistence, or
analytics reporting.

### `SessionEndHookInput`

```typescript
interface SessionEndHookInput extends BaseHookInput {
  reason: "complete" | "error" | "abort" | "timeout" | "user_exit";
  finalMessage?: string;   // Last message in the session
  error?: string;          // Error message if reason is "error"
}
```

| Property       | Type                                                              | Description                              |
|----------------|-------------------------------------------------------------------|------------------------------------------|
| `timestamp`    | `number`                                                          | Unix ms when the hook fired              |
| `cwd`          | `string`                                                          | Session working directory                |
| `reason`       | `"complete" \| "error" \| "abort" \| "timeout" \| "user_exit"` | Why the session ended                    |
| `finalMessage` | `string \| undefined`                                            | The last message in the conversation     |
| `error`        | `string \| undefined`                                            | Error details when `reason` is `"error"` |

### `SessionEndHookOutput`

```typescript
interface SessionEndHookOutput {
  suppressOutput?: boolean;        // Suppress end-of-session output
  cleanupActions?: string[];       // List of cleanup tasks to execute
  sessionSummary?: string;         // Summary persisted to session metadata
}
```

| Property         | Type       | Description                                          |
|------------------|------------|------------------------------------------------------|
| `suppressOutput` | `boolean`  | If `true`, suppresses end-of-session output          |
| `cleanupActions` | `string[]` | Cleanup tasks the runtime should execute             |
| `sessionSummary` | `string`   | Persisted to session metadata for later retrieval    |

### `SessionEndHandler`

```typescript
type SessionEndHandler = (
  input: SessionEndHookInput,
  invocation: { sessionId: string }
) => Promise<SessionEndHookOutput | void> | SessionEndHookOutput | void;
```

---

## Hook 6: Error Occurred

Fires when an error happens during model calls, tool execution, or system
operations. Use it for error recovery, notifications, or custom retry logic.

### `ErrorOccurredHookInput`

```typescript
interface ErrorOccurredHookInput extends BaseHookInput {
  error: string;                                                       // Error message
  errorContext: "model_call" | "tool_execution" | "system" | "user_input";  // Where the error originated
  recoverable: boolean;                                                // Whether recovery is possible
}
```

| Property       | Type                                                               | Description                         |
|----------------|--------------------------------------------------------------------|-------------------------------------|
| `timestamp`    | `number`                                                           | Unix ms when the hook fired         |
| `cwd`          | `string`                                                           | Session working directory           |
| `error`        | `string`                                                           | The error message                   |
| `errorContext` | `"model_call" \| "tool_execution" \| "system" \| "user_input"`   | Origin of the error                 |
| `recoverable`  | `boolean`                                                          | `true` if the runtime can recover   |

### `ErrorOccurredHookOutput`

```typescript
interface ErrorOccurredHookOutput {
  suppressOutput?: boolean;                          // Suppress error output from model
  errorHandling?: "retry" | "skip" | "abort";        // Error recovery strategy
  retryCount?: number;                                // Max retries when errorHandling is "retry"
  userNotification?: string;                          // Message displayed to the user
}
```

| Property           | Type                              | Description                                            |
|--------------------|-----------------------------------|--------------------------------------------------------|
| `suppressOutput`   | `boolean`                         | If `true`, hides the error from the model              |
| `errorHandling`    | `"retry" \| "skip" \| "abort"`   | Recovery strategy the runtime should follow            |
| `retryCount`       | `number`                          | Maximum retries (only applies when `errorHandling` = `"retry"`) |
| `userNotification` | `string`                          | Human-readable message shown to the end user           |

### `ErrorOccurredHandler`

```typescript
type ErrorOccurredHandler = (
  input: ErrorOccurredHookInput,
  invocation: { sessionId: string }
) => Promise<ErrorOccurredHookOutput | void> | ErrorOccurredHookOutput | void;
```

---

## Usage Examples

### 1. Pre-Tool Use — Argument Sanitization

Strip sensitive data from tool arguments before execution:

```typescript
import { createSession, type SessionHooks } from "@github/copilot-sdk";

const hooks: SessionHooks = {
  onPreToolUse: async (input, { sessionId }) => {
    if (input.toolName === "bash" && typeof input.toolArgs === "object") {
      const args = input.toolArgs as Record<string, string>;
      if (args.command?.includes("SECRET")) {
        return {
          permissionDecision: "deny",
          permissionDecisionReason: "Command contains secrets — blocked by policy",
        };
      }
      // Sanitize: strip env vars from command
      return {
        modifiedArgs: {
          ...args,
          command: args.command.replace(/\bexport\s+\w+=\S+/g, "# [REDACTED]"),
        },
      };
    }
    // Return void — no changes
  },
};
```

### 2. Post-Tool Use — Audit Logging

Log every tool execution to an external service:

```typescript
const hooks: SessionHooks = {
  onPostToolUse: async (input, { sessionId }) => {
    await fetch("https://audit.internal/api/events", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sessionId,
        tool: input.toolName,
        args: input.toolArgs,
        timestamp: input.timestamp,
        cwd: input.cwd,
      }),
    });
    // Return void — don't modify the result
  },
};
```

### 3. User Prompt Submitted — Prompt Rewriting & Context Injection

Prepend project-specific instructions to every prompt:

```typescript
import { readFileSync, existsSync } from "node:fs";
import { join } from "node:path";

const hooks: SessionHooks = {
  onUserPromptSubmitted: async (input, { sessionId }) => {
    const guidelinesPath = join(input.cwd, ".copilot-guidelines.md");
    if (existsSync(guidelinesPath)) {
      const guidelines = readFileSync(guidelinesPath, "utf-8");
      return {
        additionalContext: `Project guidelines:\n${guidelines}`,
      };
    }
  },
};
```

### 4. Error Occurred — Retry with User Notification

Retry transient model errors up to 3 times, notify the user:

```typescript
const hooks: SessionHooks = {
  onErrorOccurred: async (input, { sessionId }) => {
    if (input.errorContext === "model_call" && input.recoverable) {
      return {
        errorHandling: "retry",
        retryCount: 3,
        userNotification: `Model error encountered — retrying (${input.error})`,
      };
    }
    if (input.errorContext === "tool_execution") {
      return {
        errorHandling: "skip",
        userNotification: `Tool failed: ${input.error}. Skipping and continuing.`,
      };
    }
  },
};
```

### 5. Session Start & End — Lifecycle Tracking

Track session duration and persist a summary on exit:

```typescript
const sessionTimers = new Map<string, number>();

const hooks: SessionHooks = {
  onSessionStart: async (input, { sessionId }) => {
    sessionTimers.set(sessionId, input.timestamp);
    console.log(`[${sessionId}] Session started via ${input.source}`);
    return {
      additionalContext: "Always respond in the user's preferred language.",
    };
  },

  onSessionEnd: async (input, { sessionId }) => {
    const startTime = sessionTimers.get(sessionId);
    const duration = startTime ? input.timestamp - startTime : 0;
    sessionTimers.delete(sessionId);

    return {
      sessionSummary: `Session ended (${input.reason}). Duration: ${duration}ms.`,
      cleanupActions: ["flush-logs", "release-locks"],
    };
  },
};
```

---

## Important Caveats

1. **All handlers receive `invocation: { sessionId: string }` as the second parameter.**
   Use this to correlate events across hooks within the same session.

2. **Returning `void` or `undefined` means "no changes."**
   The original behavior is fully preserved. Only return an output object when
   you need to modify something.

3. **Hooks must be fast.**
   Every hook runs in the critical path. Slow I/O (network calls, disk reads)
   adds latency to every tool call or prompt. Use fire-and-forget patterns for
   non-critical operations like logging.

4. **`PreToolUseHookOutput.permissionDecision` overrides the permission handler.**
   Setting `"deny"` blocks the tool call entirely. Setting `"allow"` bypasses
   the normal permission check. Setting `"ask"` defers to the user.

5. **`PostToolUseHookOutput.modifiedResult` replaces the entire tool result.**
   The model sees only the modified result. Use with caution — the model may
   behave unexpectedly if the result shape changes.

6. **`SessionEndHookOutput.sessionSummary` is persisted to session metadata.**
   It survives session teardown and can be retrieved later for analytics or
   session resumption.

7. **`ErrorOccurredHookOutput.errorHandling: "retry"` respects `retryCount`.**
   If `retryCount` is not set, the runtime uses its default retry limit.
   Setting `retryCount: 0` effectively means "don't retry" despite the strategy.

8. **Hooks are not the place for business logic or orchestration.**
   Keep them lightweight. They are interception points, not workflow engines.
   Complex logic belongs in tools or the application layer.

9. **All hook inputs extend `BaseHookInput`.**
   Every input always has `timestamp` (Unix ms) and `cwd` (working directory).
   You can rely on these in any hook without type narrowing.
