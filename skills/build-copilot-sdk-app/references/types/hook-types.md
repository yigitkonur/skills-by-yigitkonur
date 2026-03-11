# Hook Types Reference

## Import Patterns

```typescript
import type {
  SessionHooks,
  PreToolUseHandler,
  PreToolUseHookInput,
  PreToolUseHookOutput,
  PostToolUseHandler,
  PostToolUseHookInput,
  PostToolUseHookOutput,
  UserPromptSubmittedHandler,
  UserPromptSubmittedHookInput,
  UserPromptSubmittedHookOutput,
  SessionStartHandler,
  SessionStartHookInput,
  SessionStartHookOutput,
  SessionEndHandler,
  SessionEndHookInput,
  SessionEndHookOutput,
  ErrorOccurredHandler,
  ErrorOccurredHookInput,
  ErrorOccurredHookOutput,
} from "@github/copilot-sdk";
```

---

## `SessionHooks` Interface

```typescript
interface SessionHooks {
  // Called before a tool executes. Can allow, deny, modify args, or add context.
  onPreToolUse?: PreToolUseHandler;

  // Called after a tool executes. Can modify the result or suppress output.
  onPostToolUse?: PostToolUseHandler;

  // Called when the user submits a prompt. Can modify the prompt before the LLM sees it.
  onUserPromptSubmitted?: UserPromptSubmittedHandler;

  // Called when a session starts (startup, resume, or new).
  onSessionStart?: SessionStartHandler;

  // Called when a session ends (complete, error, abort, timeout, user_exit).
  onSessionEnd?: SessionEndHandler;

  // Called when an error occurs. Can control retry and error handling behavior.
  onErrorOccurred?: ErrorOccurredHandler;
}
```

Pass `hooks` in `SessionConfig` to register them:

```typescript
const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onPreToolUse: myPreToolHook,
    onPostToolUse: myPostToolHook,
  },
});
```

---

## Base Hook Input

All hook inputs extend `BaseHookInput`:

```typescript
interface BaseHookInput {
  timestamp: number;  // Unix timestamp (ms) when the hook was triggered
  cwd: string;        // Working directory at time of hook invocation
}
```

---

## Pre-Tool-Use Hook

Fires before each tool execution. Use it to audit, gate, modify arguments, or inject extra context.

```typescript
interface PreToolUseHookInput extends BaseHookInput {
  toolName: string;
  toolArgs: unknown;  // Raw arguments the LLM passed to the tool
}

interface PreToolUseHookOutput {
  // Permission decision:
  //   "allow"  - proceed with execution (default when omitted)
  //   "deny"   - block the tool call
  //   "ask"    - escalate to the onPermissionRequest handler
  permissionDecision?: "allow" | "deny" | "ask";

  // Human-readable reason for the decision (shown in session log).
  permissionDecisionReason?: string;

  // Replace the tool arguments before execution.
  modifiedArgs?: unknown;

  // Inject additional context into the system prompt for this call.
  additionalContext?: string;

  // Suppress tool output from the session timeline (still executes).
  suppressOutput?: boolean;
}

type PreToolUseHandler = (
  input: PreToolUseHookInput,
  invocation: { sessionId: string }
) => Promise<PreToolUseHookOutput | void> | PreToolUseHookOutput | void;
```

Return `void` or `undefined` to proceed with no changes.

### Example: Block dangerous bash commands

```typescript
const onPreToolUse: PreToolUseHandler = (input) => {
  if (input.toolName === "bash") {
    const { command } = input.toolArgs as { command: string };
    if (command.includes("rm -rf /")) {
      return {
        permissionDecision: "deny",
        permissionDecisionReason: "Dangerous command blocked by policy",
      };
    }
  }
};
```

---

## Post-Tool-Use Hook

Fires after each tool execution. Use it to transform results, add context, or suppress output.

```typescript
interface PostToolUseHookInput extends BaseHookInput {
  toolName: string;
  toolArgs: unknown;
  toolResult: ToolResultObject;  // The result produced by the tool
}

interface PostToolUseHookOutput {
  // Replace the tool result sent back to the LLM.
  modifiedResult?: ToolResultObject;

  // Inject additional context into the system prompt for the next call.
  additionalContext?: string;

  // Suppress tool output from the session timeline.
  suppressOutput?: boolean;
}

type PostToolUseHandler = (
  input: PostToolUseHookInput,
  invocation: { sessionId: string }
) => Promise<PostToolUseHookOutput | void> | PostToolUseHookOutput | void;
```

### Example: Redact secrets from tool output

```typescript
const onPostToolUse: PostToolUseHandler = (input) => {
  const text = input.toolResult.textResultForLlm;
  const redacted = text.replace(/ghp_[A-Za-z0-9]+/g, "[REDACTED]");
  if (redacted !== text) {
    return {
      modifiedResult: { ...input.toolResult, textResultForLlm: redacted },
    };
  }
};
```

---

## User Prompt Submitted Hook

Fires when the user sends a message, before the LLM processes it. Use it to modify or augment the prompt.

```typescript
interface UserPromptSubmittedHookInput extends BaseHookInput {
  prompt: string;  // The user's message text
}

interface UserPromptSubmittedHookOutput {
  // Replace the prompt sent to the LLM.
  modifiedPrompt?: string;

  // Inject additional context into the system prompt for this turn.
  additionalContext?: string;

  // Suppress the prompt from the session timeline.
  suppressOutput?: boolean;
}

type UserPromptSubmittedHandler = (
  input: UserPromptSubmittedHookInput,
  invocation: { sessionId: string }
) => Promise<UserPromptSubmittedHookOutput | void> | UserPromptSubmittedHookOutput | void;
```

---

## Session Start Hook

Fires when a session starts. `source` distinguishes startup, resume, and new session creation.

```typescript
interface SessionStartHookInput extends BaseHookInput {
  source: "startup" | "resume" | "new";
  initialPrompt?: string;  // The first prompt sent to this session, if any
}

interface SessionStartHookOutput {
  // Inject context into the system prompt at session start.
  additionalContext?: string;

  // Modify session configuration at startup.
  modifiedConfig?: Record<string, unknown>;
}

type SessionStartHandler = (
  input: SessionStartHookInput,
  invocation: { sessionId: string }
) => Promise<SessionStartHookOutput | void> | SessionStartHookOutput | void;
```

---

## Session End Hook

Fires when a session ends. Use it to emit summaries, trigger cleanup, or suppress output.

```typescript
interface SessionEndHookInput extends BaseHookInput {
  reason: "complete" | "error" | "abort" | "timeout" | "user_exit";
  finalMessage?: string;  // Last assistant message, if any
  error?: string;         // Error description when reason is "error"
}

interface SessionEndHookOutput {
  suppressOutput?: boolean;

  // Actions to perform during cleanup (e.g., file paths to remove).
  cleanupActions?: string[];

  // Summary text to attach to the session record.
  sessionSummary?: string;
}

type SessionEndHandler = (
  input: SessionEndHookInput,
  invocation: { sessionId: string }
) => Promise<SessionEndHookOutput | void> | SessionEndHookOutput | void;
```

---

## Error Occurred Hook

Fires when an error occurs. Use it to control retry behavior, suppress error output, or notify users.

```typescript
interface ErrorOccurredHookInput extends BaseHookInput {
  error: string;
  // Where the error originated.
  errorContext: "model_call" | "tool_execution" | "system" | "user_input";
  // Whether the runtime considers this error recoverable.
  recoverable: boolean;
}

interface ErrorOccurredHookOutput {
  suppressOutput?: boolean;

  // How to handle the error:
  //   "retry"  - retry the failed operation
  //   "skip"   - skip the failed operation and continue
  //   "abort"  - abort the session
  errorHandling?: "retry" | "skip" | "abort";

  // Number of retry attempts (used when errorHandling is "retry").
  retryCount?: number;

  // Message to surface to the user about the error.
  userNotification?: string;
}

type ErrorOccurredHandler = (
  input: ErrorOccurredHookInput,
  invocation: { sessionId: string }
) => Promise<ErrorOccurredHookOutput | void> | ErrorOccurredHookOutput | void;
```

### Example: Retry model call errors

```typescript
const onErrorOccurred: ErrorOccurredHandler = (input) => {
  if (input.errorContext === "model_call" && input.recoverable) {
    return { errorHandling: "retry", retryCount: 2 };
  }
  if (input.errorContext === "tool_execution") {
    return { errorHandling: "skip", userNotification: `Tool failed: ${input.error}` };
  }
};
```

---

## Hook Event Correlation

The `hook.start` and `hook.end` session events are emitted around each hook invocation:

```typescript
session.on("hook.start", (e) => {
  // e.data.hookInvocationId — unique ID for this invocation
  // e.data.hookType — e.g. "preToolUse", "postToolUse", "sessionStart"
  // e.data.input — the input passed to the hook
});

session.on("hook.end", (e) => {
  // e.data.hookInvocationId — matches the corresponding hook.start
  // e.data.output — what the hook returned
  // e.data.success — whether the hook completed without error
  // e.data.error?{message, stack?} — error details if hook threw
});
```

---

## Hook Output Action Summary

| Output field | Hook(s) | Effect when set |
|--------------|---------|-----------------|
| `permissionDecision: "allow"` | `onPreToolUse` | Tool proceeds (default) |
| `permissionDecision: "deny"` | `onPreToolUse` | Tool is blocked |
| `permissionDecision: "ask"` | `onPreToolUse` | Escalates to `onPermissionRequest` handler |
| `modifiedArgs` | `onPreToolUse` | Replaces tool arguments before execution |
| `modifiedResult` | `onPostToolUse` | Replaces tool result sent to LLM |
| `modifiedPrompt` | `onUserPromptSubmitted` | Replaces user prompt before LLM sees it |
| `additionalContext` | `onPreToolUse`, `onPostToolUse`, `onUserPromptSubmitted`, `onSessionStart` | Injected into system prompt |
| `suppressOutput` | All except `onSessionStart` | Hides event from session timeline |
| `errorHandling: "retry"` | `onErrorOccurred` | Retries the failed operation |
| `errorHandling: "skip"` | `onErrorOccurred` | Skips and continues |
| `errorHandling: "abort"` | `onErrorOccurred` | Aborts the session |
| `modifiedConfig` | `onSessionStart` | Modifies session config at startup |
| `cleanupActions` | `onSessionEnd` | Actions to run during cleanup |
| `sessionSummary` | `onSessionEnd` | Text attached to session record |
