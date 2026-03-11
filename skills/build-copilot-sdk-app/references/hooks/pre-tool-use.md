# onPreToolUse Hook Reference

Intercept every tool call before execution. Use this hook to enforce security policies, sanitize arguments, inject context, or audit activity. The hook fires synchronously in the tool dispatch path — return promptly.

## Type Signatures

```typescript
import type {
  PreToolUseHookInput,
  PreToolUseHookOutput,
  SessionHooks,
} from "@github/copilot-sdk";

// Handler signature
type PreToolUseHandler = (
  input: PreToolUseHookInput,
  invocation: { sessionId: string }
) => Promise<PreToolUseHookOutput | void> | PreToolUseHookOutput | void;

// Register via SessionConfig.hooks
const hooks: SessionHooks = {
  onPreToolUse: async (input, invocation) => { /* ... */ },
};
```

## Input Fields

| Field | Type | Description |
|-------|------|-------------|
| `toolName` | `string` | Name of the tool about to execute (e.g. `"shell"`, `"read_file"`) |
| `toolArgs` | `unknown` | Arguments passed to the tool — cast to the specific tool's arg shape |
| `timestamp` | `number` | Unix epoch milliseconds when the hook fired |
| `cwd` | `string` | Working directory of the session at hook invocation |

Access `invocation.sessionId` for the session identifier. The `toolArgs` field is always an object but typed as `unknown` — cast explicitly before accessing properties.

## Output Fields

Return `void` or `undefined` to allow the tool with no changes. Return an object to control execution:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `permissionDecision` | `"allow" \| "deny" \| "ask"` | `"allow"` | Gate the tool call |
| `permissionDecisionReason` | `string` | — | Human-readable message shown on `"deny"` or `"ask"` |
| `modifiedArgs` | `unknown` | — | Replacement arguments forwarded to the tool instead of originals |
| `additionalContext` | `string` | — | Text injected into the conversation context before tool runs |
| `suppressOutput` | `boolean` | `false` | When `true`, the tool result is hidden from the conversation |

### Permission Decision Semantics

| Decision | Behavior |
|----------|----------|
| `"allow"` | Tool executes with original or modified args |
| `"deny"` | Tool is blocked; `permissionDecisionReason` is surfaced to user and model |
| `"ask"` | Runtime prompts the user for manual approval (interactive sessions only) |

Returning `void` is equivalent to `{ permissionDecision: "allow" }`.

## Pattern: Block Dangerous Operations

Deny specific tools unconditionally. Include a reason that tells the model what to do instead.

```typescript
const BLOCKED_TOOLS = new Set(["shell", "bash", "exec", "delete_file"]);

const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onPreToolUse: async (input) => {
      if (BLOCKED_TOOLS.has(input.toolName)) {
        return {
          permissionDecision: "deny",
          permissionDecisionReason:
            `Tool '${input.toolName}' is disabled in this environment. ` +
            `Use read_file or write_file for file operations.`,
        };
      }
      return { permissionDecision: "allow" };
    },
  },
});
```

## Pattern: Restrict File Access to an Allowlist

Inspect `toolArgs` for path fields and deny access outside approved directories.

```typescript
const ALLOWED_ROOTS = ["/workspace/project", "/tmp/sandbox"];

function isPathAllowed(p: string): boolean {
  return ALLOWED_ROOTS.some((root) => p.startsWith(root));
}

const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onPreToolUse: async (input) => {
      const FILE_TOOLS = new Set(["read_file", "write_file", "list_directory"]);
      if (FILE_TOOLS.has(input.toolName)) {
        const args = input.toolArgs as { path?: string };
        if (args.path && !isPathAllowed(args.path)) {
          return {
            permissionDecision: "deny",
            permissionDecisionReason:
              `Path '${args.path}' is outside the allowed directories: ` +
              ALLOWED_ROOTS.join(", "),
          };
        }
      }
      return { permissionDecision: "allow" };
    },
  },
});
```

## Pattern: Input Sanitization and Modification

Modify `toolArgs` before forwarding. Useful for adding defaults, normalizing paths, or stripping unsafe flags.

```typescript
const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onPreToolUse: async (input) => {
      if (input.toolName === "shell") {
        const args = input.toolArgs as { command: string; timeout?: number; cwd?: string };
        return {
          permissionDecision: "allow",
          modifiedArgs: {
            ...args,
            // Enforce a maximum timeout
            timeout: Math.min(args.timeout ?? 30_000, 60_000),
            // Prevent directory traversal in cwd
            cwd: args.cwd?.includes("..") ? input.cwd : args.cwd,
          },
        };
      }
      return { permissionDecision: "allow" };
    },
  },
});
```

Important: `modifiedArgs` must satisfy the tool's expected schema. Malformed args cause the tool to fail after the hook exits.

## Pattern: Logging and Auditing

Record every tool invocation before it runs. Use `timestamp` and `sessionId` as correlation keys.

```typescript
interface AuditRecord {
  sessionId: string;
  toolName: string;
  toolArgs: unknown;
  timestamp: number;
  decision: "allow" | "deny";
}

const auditLog: AuditRecord[] = [];

const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onPreToolUse: async (input, invocation) => {
      const record: AuditRecord = {
        sessionId: invocation.sessionId,
        toolName: input.toolName,
        toolArgs: input.toolArgs,
        timestamp: input.timestamp,
        decision: "allow",
      };
      auditLog.push(record);
      // Optionally flush to persistent storage without blocking
      void writeAuditRecord(record);
      return { permissionDecision: "allow" };
    },
  },
});
```

Do not `await` blocking I/O in the audit path — fire-and-forget with `void` to avoid adding latency to every tool call.

## Pattern: Inject Per-Tool Context

Add instructions specific to a tool so the model uses it correctly in the next turn.

```typescript
const TOOL_CONTEXT: Record<string, string> = {
  query_database:
    "This database runs PostgreSQL 15. Use $1 placeholders for parameters, not string interpolation.",
  read_file:
    "File paths are relative to the session working directory unless they start with /.",
};

const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onPreToolUse: async (input) => {
      const context = TOOL_CONTEXT[input.toolName];
      return {
        permissionDecision: "allow",
        ...(context ? { additionalContext: context } : {}),
      };
    },
  },
});
```

## Pattern: Conditional Approval Requiring Escalation

Escalate sensitive operations to human review in interactive contexts.

```typescript
const SENSITIVE_TOOLS = new Set(["write_file", "delete_file", "shell"]);

const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onPreToolUse: async (input) => {
      if (SENSITIVE_TOOLS.has(input.toolName)) {
        return {
          permissionDecision: "ask",
          permissionDecisionReason:
            `'${input.toolName}' modifies the filesystem. Approve to continue.`,
        };
      }
      return { permissionDecision: "allow" };
    },
  },
});
```

`"ask"` is only meaningful in interactive (terminal/UI) contexts. In headless pipelines, treat it the same as `"deny"` or use `"deny"` directly.

## Common Mistakes

- Returning `{ permissionDecision: "deny" }` without `permissionDecisionReason` leaves the model with no corrective instruction — always include a reason.
- Mutating `input.toolArgs` directly has no effect; you must return the modified object under `modifiedArgs`.
- Performing slow I/O synchronously in the hook adds latency to every tool call in the session. Use `void` + fire-and-forget for side effects.
- Omitting `permissionDecision` from the returned object when other fields are present is valid — the runtime defaults to `"allow"`.

## Integration Example

Wire multiple policies in one handler using ordered checks:

```typescript
const session = await client.createSession({
  onPermissionRequest: approveAll,
  hooks: {
    onPreToolUse: async (input, invocation) => {
      // 1. Hard block
      if (input.toolName === "exec") {
        return { permissionDecision: "deny", permissionDecisionReason: "exec is disabled." };
      }
      // 2. Sanitize
      let modifiedArgs: unknown = undefined;
      if (input.toolName === "shell") {
        const a = input.toolArgs as { command: string; timeout?: number };
        modifiedArgs = { ...a, timeout: Math.min(a.timeout ?? 30_000, 60_000) };
      }
      // 3. Audit (non-blocking)
      void logToolCall(invocation.sessionId, input.toolName, input.timestamp);
      // 4. Allow (with optional modified args)
      return { permissionDecision: "allow", ...(modifiedArgs ? { modifiedArgs } : {}) };
    },
  },
});
```
