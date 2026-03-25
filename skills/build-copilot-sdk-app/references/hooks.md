# Hooks

Hooks are lifecycle interceptors that fire at specific points during session execution. They can inspect, modify, or block tool calls, prompts, and session lifecycle events.

## Registering hooks

```typescript
const session = await client.createSession({
  onPermissionRequest: approveAll,
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

All hooks receive a base input:
```typescript
interface BaseHookInput {
  timestamp: number;
  cwd: string;
}
```

And an invocation context: `{ sessionId: string }`

## Hook 1: onPreToolUse

Fires **before** a tool executes. Can allow, deny, or modify the tool call.

### Input

```typescript
interface PreToolUseHookInput extends BaseHookInput {
  toolName: string;
  toolArgs: unknown;
}
```

### Output

```typescript
interface PreToolUseHookOutput {
  permissionDecision?: "allow" | "deny" | "ask";
  permissionDecisionReason?: string;
  modifiedArgs?: unknown;
  additionalContext?: string;
  suppressOutput?: boolean;
}
```

### Examples

**Block dangerous commands:**
```typescript
onPreToolUse: async (input) => {
  if (input.toolName === "bash") {
    const cmd = String(input.toolArgs?.command || "");
    if (/rm\s+-rf/i.test(cmd)) {
      return {
        permissionDecision: "deny",
        permissionDecisionReason: "Destructive commands blocked",
      };
    }
  }
  return { permissionDecision: "allow" };
}
```

**Modify tool arguments:**
```typescript
onPreToolUse: async (input) => {
  if (input.toolName === "bash") {
    return {
      modifiedArgs: {
        ...input.toolArgs,
        command: `${input.toolArgs.command} 2>&1`,
      },
    };
  }
}
```

**Inject context before tool runs:**
```typescript
onPreToolUse: async (input) => {
  if (input.toolName === "edit") {
    return {
      additionalContext: "Follow our team coding standards: no semicolons, 2-space indent.",
    };
  }
}
```

## Hook 2: onPostToolUse

Fires **after** a tool executes. Can observe or modify the result.

### Input

```typescript
interface PostToolUseHookInput extends BaseHookInput {
  toolName: string;
  toolArgs: unknown;
  toolResult: ToolResultObject;
}
```

### Output

```typescript
interface PostToolUseHookOutput {
  modifiedResult?: ToolResultObject;
  additionalContext?: string;
  suppressOutput?: boolean;
}
```

### Examples

**Run linter after file edits:**
```typescript
onPostToolUse: async (input) => {
  if (input.toolName === "edit" && input.toolArgs?.path?.endsWith(".ts")) {
    const lintResult = await runLinter(input.toolArgs.path);
    return {
      additionalContext: `Lint result: ${lintResult}`,
    };
  }
}
```

**Open edited files in VS Code:**
```typescript
onPostToolUse: async (input) => {
  if (input.toolName === "create" || input.toolName === "edit") {
    const filePath = input.toolArgs?.path;
    if (filePath) exec(`code "${filePath}"`, () => {});
  }
}
```

## Hook 3: onUserPromptSubmitted

Fires when the user submits a prompt. Can modify the prompt or inject context.

### Input

```typescript
interface UserPromptSubmittedHookInput extends BaseHookInput {
  prompt: string;
}
```

### Output

```typescript
interface UserPromptSubmittedHookOutput {
  modifiedPrompt?: string;
  additionalContext?: string;
  suppressOutput?: boolean;
}
```

### Examples

**Inject context into every prompt:**
```typescript
onUserPromptSubmitted: async (input) => ({
  additionalContext: "Always respond in bullet points. Follow coding standards.",
})
```

**Modify user prompt:**
```typescript
onUserPromptSubmitted: async (input) => ({
  modifiedPrompt: input.prompt.replace(/TODO/g, "ACTION ITEM"),
})
```

## Hook 4: onSessionStart

Fires when a session starts or resumes.

### Input

```typescript
interface SessionStartHookInput extends BaseHookInput {
  source: "startup" | "resume" | "new";
  initialPrompt?: string;
}
```

### Output

```typescript
interface SessionStartHookOutput {
  additionalContext?: string;
  modifiedConfig?: Record<string, unknown>;
}
```

### Example

```typescript
onSessionStart: async (input) => {
  if (input.source === "new") {
    return {
      additionalContext: `Project context: Using React 19, TypeScript 5.7, Vitest`,
    };
  }
}
```

## Hook 5: onSessionEnd

Fires when a session ends.

### Input

```typescript
interface SessionEndHookInput extends BaseHookInput {
  reason: "complete" | "error" | "abort" | "timeout" | "user_exit";
  finalMessage?: string;
  error?: string;
}
```

### Output

```typescript
interface SessionEndHookOutput {
  suppressOutput?: boolean;
  cleanupActions?: string[];
  sessionSummary?: string;
}
```

### Example

```typescript
onSessionEnd: async (input) => {
  if (input.reason === "error") {
    await logError(input.error);
  }
  return {
    sessionSummary: "Session completed code review of auth module",
  };
}
```

## Hook 6: onErrorOccurred

Fires when an error occurs. Can control error recovery.

### Input

```typescript
interface ErrorOccurredHookInput extends BaseHookInput {
  error: string;
  errorContext: "model_call" | "tool_execution" | "system" | "user_input";
  recoverable: boolean;
}
```

### Output

```typescript
interface ErrorOccurredHookOutput {
  suppressOutput?: boolean;
  errorHandling?: "retry" | "skip" | "abort";
  retryCount?: number;
  userNotification?: string;
}
```

### Examples

**Auto-retry model errors:**
```typescript
onErrorOccurred: async (input) => {
  if (input.recoverable && input.errorContext === "model_call") {
    return { errorHandling: "retry", retryCount: 2 };
  }
  return {
    errorHandling: "abort",
    userNotification: `Error: ${input.error}`,
  };
}
```

**Skip tool errors, abort system errors:**
```typescript
onErrorOccurred: async (input) => {
  if (input.errorContext === "tool_execution") {
    return { errorHandling: "skip" };
  }
  return { errorHandling: "abort" };
}
```

## Hooks vs permissions

| Aspect | Hooks (`onPreToolUse`) | Permissions (`onPermissionRequest`) |
|--------|------------------------|-------------------------------------|
| Fires for | ALL tool calls | Only permission-requiring tools |
| Can modify | Args, context, decision | Only approve/deny |
| Scope | Built-in + custom tools | Server-defined permission categories |
| Return type | `PreToolUseHookOutput` | `PermissionRequestResult` |

## Hook events on session

Hook execution is observable via events:

```typescript
session.on("hook.start", (event) => {
  console.log(`Hook ${event.data.hookType} starting`);
});

session.on("hook.end", (event) => {
  console.log(`Hook ${event.data.hookType}: success=${event.data.success}`);
  if (event.data.error) console.error(event.data.error.message);
});
```

## Steering notes

> Common mistakes agents make with hooks.

- **All hooks can return `void`** (no return statement). This is the most common pattern for logging-only hooks. The hook is treated as a no-op.
- **Hook errors are silently caught**. If your hook throws, execution continues as if the hook returned `undefined`. This means bugs in hooks are invisible — add try/catch with logging inside hooks for debugging.
- **`onPreToolUse` can block tools** by returning `{ permissionDecision: "deny", permissionDecisionReason: "..." }`. The model sees the reason and may try alternative approaches. Use this for security guardrails (e.g., blocking `rm -rf /`).
- **`onPostToolUse` sees the full result** via `toolResult.textResultForLlm`. Use this for audit logging, metrics, or result sanitization.
- **`onUserPromptSubmitted` can modify the prompt** by returning `{ modifiedPrompt: "..." }`. Use this to inject system context (e.g., prepending repository info). Returning the original prompt is a no-op.
- **Hook execution is synchronous relative to the SDK pipeline** — the SDK waits for your hook to resolve before proceeding. Long-running hooks will block the pipeline. Keep hooks fast.
- **Hook events** (`hook.start`, `hook.end`) fire for every hook invocation and include timing data. Use these for performance monitoring, not the hooks themselves.

## Internal hook type mapping

| Hook function | RPC hook type |
|--------------|---------------|
| `onPreToolUse` | `"preToolUse"` |
| `onPostToolUse` | `"postToolUse"` |
| `onUserPromptSubmitted` | `"userPromptSubmitted"` |
| `onSessionStart` | `"sessionStart"` |
| `onSessionEnd` | `"sessionEnd"` |
| `onErrorOccurred` | `"errorOccurred"` |

All hooks can return `void` (no return statement) — the hook is treated as a no-op and execution continues normally. If a hook throws, the error is silently caught and execution continues.
