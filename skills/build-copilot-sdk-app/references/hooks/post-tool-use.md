# onPostToolUse Hook Reference

Inspect and transform every tool result after execution. Use this hook to redact sensitive data, reshape output for the model, record audit trails, inject follow-up context, or suppress noisy results. The hook fires after the tool handler returns but before its result enters the conversation.

## Type Signatures

```typescript
import type {
  PostToolUseHookInput,
  PostToolUseHookOutput,
  ToolResultObject,
  SessionHooks,
} from "@github/copilot-sdk";

// Handler signature
type PostToolUseHandler = (
  input: PostToolUseHookInput,
  invocation: { sessionId: string }
) => Promise<PostToolUseHookOutput | void> | PostToolUseHookOutput | void;

// Register via SessionConfig.hooks
const hooks: SessionHooks = {
  onPostToolUse: async (input, invocation) => { /* ... */ },
};
```

## Input Fields

| Field | Type | Description |
|-------|------|-------------|
| `toolName` | `string` | Name of the tool that executed |
| `toolArgs` | `unknown` | Arguments that were passed to the tool |
| `toolResult` | `ToolResultObject` | Full result returned by the tool |
| `timestamp` | `number` | Unix epoch milliseconds when the hook fired |
| `cwd` | `string` | Working directory of the session |

Access `invocation.sessionId` for the session identifier.

### ToolResultObject Shape

```typescript
interface ToolResultObject {
  textResultForLlm: string;              // Primary text the model sees
  binaryResultsForLlm?: ToolBinaryResult[]; // Optional binary attachments
  resultType: "success" | "failure" | "rejected" | "denied";
  error?: string;                         // Present on failure/rejection
  sessionLog?: string;                    // Execution log
  toolTelemetry?: Record<string, unknown>; // Arbitrary telemetry data
}
```

When modifying results, always reconstruct from the original `toolResult` — spread and override only the fields you need to change.

## Output Fields

Return `void` or `undefined` to pass the result through unchanged. Return an object to alter what the model sees:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `modifiedResult` | `ToolResultObject` | — | Replacement result forwarded to the model |
| `additionalContext` | `string` | — | Text injected into the conversation after the tool result |
| `suppressOutput` | `boolean` | `false` | When `true`, the tool result is hidden from the conversation entirely |

Returning `null` is also valid and equivalent to `void`.

## Pattern: Output Redaction

Scrub secrets and credentials from tool output before the model receives it.

```typescript
const SENSITIVE_PATTERNS: Array<[RegExp, string]> = [
  [/api[_-]?key\s*[:=]\s*["']?[\w\-]{16,}["']?/gi, "[API_KEY_REDACTED]"],
  [/password\s*[:=]\s*["']?[^\s"',]+["']?/gi, "[PASSWORD_REDACTED]"],
  [/Bearer\s+[A-Za-z0-9\-._~+/]+=*/g, "Bearer [TOKEN_REDACTED]"],
  [/-----BEGIN[^-]+-----[\s\S]+?-----END[^-]+-----/g, "[PRIVATE_KEY_REDACTED]"],
];

function redactText(text: string): string {
  let result = text;
  for (const [pattern, replacement] of SENSITIVE_PATTERNS) {
    result = result.replace(pattern, replacement);
  }
  return result;
}

const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onPostToolUse: async (input) => {
      const redacted = redactText(input.toolResult.textResultForLlm);
      if (redacted === input.toolResult.textResultForLlm) return; // no change
      return {
        modifiedResult: {
          ...input.toolResult,
          textResultForLlm: redacted,
        },
      };
    },
  },
});
```

Note: Apply redaction before any logging — log `modifiedResult`, not the raw `input.toolResult`.

## Pattern: Result Transformation

Reshape large or noisy tool output into a concise form the model can use more effectively.

```typescript
const MAX_OUTPUT_CHARS = 8_000;

const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onPostToolUse: async (input) => {
      const text = input.toolResult.textResultForLlm;
      if (text.length <= MAX_OUTPUT_CHARS) return;

      const truncated = text.slice(0, MAX_OUTPUT_CHARS);
      const omitted = text.length - MAX_OUTPUT_CHARS;
      return {
        modifiedResult: {
          ...input.toolResult,
          textResultForLlm:
            truncated +
            `\n\n[... ${omitted} characters omitted. Ask to see more if needed.]`,
        },
        additionalContext:
          `The ${input.toolName} result was truncated from ${text.length} to ${MAX_OUTPUT_CHARS} characters.`,
      };
    },
  },
});
```

## Pattern: Summarize Directory Listings

Replace verbose listing output with a count-plus-sample summary.

```typescript
const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onPostToolUse: async (input) => {
      if (input.toolName !== "list_directory") return;

      const lines = input.toolResult.textResultForLlm
        .split("\n")
        .filter(Boolean);

      if (lines.length <= 20) return; // small enough, pass through

      const sample = lines.slice(0, 10).join("\n");
      return {
        modifiedResult: {
          ...input.toolResult,
          textResultForLlm:
            `Directory contains ${lines.length} entries. First 10:\n${sample}\n` +
            `[Use a more specific path or filter to see the rest]`,
        },
      };
    },
  },
});
```

## Pattern: Side-Effect Execution After Tool Completion

Trigger external actions (webhooks, metrics, notifications) once a tool succeeds. Fire-and-forget to avoid blocking the conversation.

```typescript
const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onPostToolUse: async (input, invocation) => {
      // Fire metrics without blocking
      void recordToolMetric({
        sessionId: invocation.sessionId,
        toolName: input.toolName,
        resultType: input.toolResult.resultType,
        durationMs: Date.now() - input.timestamp,
      });

      // Notify on destructive operations
      if (
        input.toolName === "delete_file" &&
        input.toolResult.resultType === "success"
      ) {
        void sendWebhook("file_deleted", {
          sessionId: invocation.sessionId,
          args: input.toolArgs,
        });
      }

      return; // pass through unchanged
    },
  },
});
```

## Pattern: Audit Trail for Compliance

Record the full input/output pair for every tool call with tamper-evident storage.

```typescript
interface AuditEntry {
  sessionId: string;
  toolName: string;
  toolArgs: unknown;
  result: ToolResultObject;
  timestamp: number;
}

const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onPostToolUse: async (input, invocation) => {
      const entry: AuditEntry = {
        sessionId: invocation.sessionId,
        toolName: input.toolName,
        toolArgs: input.toolArgs,
        result: input.toolResult,
        timestamp: input.timestamp,
      };
      // Non-blocking persistence
      void appendAuditLog(entry);
      return;
    },
  },
});
```

Store `toolArgs` alongside `toolResult` so auditors can reconstruct what was requested and what the tool returned.

## Pattern: Inject Recovery Hints on Failure

Add context that helps the model self-correct when tools fail.

```typescript
const FAILURE_HINTS: Record<string, string> = {
  shell:
    "If the command failed due to a missing binary, check whether it needs to be installed first.",
  read_file:
    "If the file was not found, verify the path is relative to the session working directory.",
  write_file:
    "If the write failed, the parent directory may not exist. Create it first.",
};

const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onPostToolUse: async (input) => {
      if (input.toolResult.resultType !== "failure") return;

      const hint = FAILURE_HINTS[input.toolName];
      if (!hint) return;

      return { additionalContext: hint };
    },
  },
});
```

## Pattern: Suppress Verbose Internal Tools

Hide tool results the model does not need to reason over but that must still execute.

```typescript
const SILENT_TOOLS = new Set(["log_event", "emit_metric", "send_telemetry"]);

const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onPostToolUse: async (input) => {
      if (SILENT_TOOLS.has(input.toolName)) {
        return { suppressOutput: true };
      }
    },
  },
});
```

When `suppressOutput` is `true`, the tool still executes and its result is still passed to `onPostToolUse` — only the model's view is suppressed.

## Common Mistakes

- Do not mutate `input.toolResult` in place. Always spread into a new object under `modifiedResult`.
- Omitting `resultType` when constructing `modifiedResult` will break the runtime's result handling — always carry it through from the original.
- Logging raw `input.toolResult` before redaction exposes secrets to your log sink. Redact first, then log.
- Returning `{ modifiedResult: undefined }` is not the same as returning `void` — explicitly return `void` or `undefined` when passing through unchanged.
- Heavy synchronous computation inside the hook adds latency after every tool execution. Move expensive work to `void` async calls.
