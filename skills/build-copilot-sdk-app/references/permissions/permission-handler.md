# Permission Handler Reference

## Type Signature

```typescript
import type { PermissionHandler, PermissionRequest, PermissionRequestResult } from "@github/copilot-sdk";

type PermissionHandler = (
    request: PermissionRequest,
    invocation: { sessionId: string }
) => Promise<PermissionRequestResult> | PermissionRequestResult;
```

`PermissionRequest` is the base type. Every request carries `kind` (the discriminant) and `toolCallId?` plus kind-specific fields. Access `invocation.sessionId` to scope decisions per-session.

`PermissionRequestResult` is the union of all allowed response shapes — see the Result Kinds section below.

## PermissionRequest Base Structure

```typescript
interface PermissionRequest {
    kind: "shell" | "write" | "mcp" | "read" | "url" | "memory" | "custom-tool";
    toolCallId?: string;  // ID of the tool call that triggered this request
    [key: string]: unknown;  // kind-specific fields (see permission-kinds.md)
}
```

Always narrow on `request.kind` before accessing kind-specific metadata. Never rely on extra fields without narrowing — the index signature `[key: string]: unknown` exists to allow future extensions.

## Result Kinds

Return one of these exact shapes from your handler:

```typescript
// Approve the operation — agent proceeds
{ kind: "approved" }

// Deny: user explicitly said no in an interactive UI
{ kind: "denied-interactively-by-user"; feedback?: string }

// Deny: no rule and couldn't ask the user (silent deny — agent sees "Permission denied")
{ kind: "denied-no-approval-rule-and-could-not-request-from-user" }

// Deny: matched a configured rule that blocks this operation
{ kind: "denied-by-rules"; rules: unknown[] }

// Deny: content exclusion policy blocked access to a path
{ kind: "denied-by-content-exclusion-policy"; path: string; message: string }
```

When your handler throws, the SDK automatically returns `denied-no-approval-rule-and-could-not-request-from-user`. Never let uncaught errors propagate to deny silently — explicitly return the denial kind you intend.

## approveAll Helper

`approveAll` is a pre-built handler that unconditionally approves every request. Import and use it for development, tests, or any scenario where you delegate all trust to the agent:

```typescript
import { CopilotClient, approveAll } from "@github/copilot-sdk";

const session = await client.createSession({
    onPermissionRequest: approveAll,
});
```

`approveAll` is defined as `() => ({ kind: "approved" })`. Use it as a baseline and replace with custom logic when security boundaries are needed.

## Required on Every createSession and resumeSession

`onPermissionRequest` is a required field in `SessionConfig`. There is no default — omitting it causes a TypeScript compile error. Provide it on both initial creation and every resume:

```typescript
// createSession — required
const session = await client.createSession({
    onPermissionRequest: myHandler,
    onUserInputRequest: myInputHandler,
});

// resumeSession — also required in ResumeSessionConfig
const resumed = await client.resumeSession(sessionId, {
    onPermissionRequest: myHandler,
});
```

The handler is bound per `CopilotSession` instance. Different sessions may use different handlers — use `invocation.sessionId` to look up per-session state when multiplexing.

## Protocol v3 Broadcast Behavior

In protocol v3, permission requests arrive as ephemeral `permission.requested` events broadcast to all connected clients for the same session. The SDK listens for this event inside `_handleBroadcastEvent` and dispatches it to the registered handler:

```typescript
// Internally, the SDK handles this pattern:
// event.type === "permission.requested"
// → calls permissionHandler(event.data.permissionRequest, { sessionId })
// → calls rpc.permissions.handlePendingPermissionRequest({ requestId, result })
```

All clients connected to the same session receive the same `permission.requested` broadcast. Your handler must respond exactly once per `requestId`. The SDK handles de-duplication — only the handler registered on the session that received the event responds.

For multi-client setups (e.g., multiple SDK instances connected to the same CLI server session), only the client that created or resumed the session with `onPermissionRequest` will respond. Other clients observing events will see `permission.requested` but their handlers will not be invoked unless they are the primary session holder.

## Custom Permission Handlers with Conditional Logic

### Allow/Deny by Kind

```typescript
const session = await client.createSession({
    onPermissionRequest: (request) => {
        switch (request.kind) {
            case "read":
                return { kind: "approved" };
            case "write":
                return { kind: "denied-interactively-by-user", feedback: "Write operations not allowed" };
            case "shell":
                return { kind: "denied-no-approval-rule-and-could-not-request-from-user" };
            default:
                return { kind: "approved" };
        }
    },
});
```

### Path-Based Write Filtering

```typescript
import type { PermissionRequest } from "@github/copilot-sdk";

const ALLOWED_WRITE_PATHS = ["/tmp/", "/workspace/output/"];

const session = await client.createSession({
    onPermissionRequest: (request) => {
        if (request.kind === "write") {
            const fileName = (request as any).fileName as string;
            const allowed = ALLOWED_WRITE_PATHS.some((prefix) => fileName.startsWith(prefix));
            if (!allowed) {
                return {
                    kind: "denied-interactively-by-user",
                    feedback: `Write to ${fileName} is outside allowed directories`,
                };
            }
        }
        return { kind: "approved" };
    },
});
```

### Async Handler (User Prompt / External Check)

```typescript
const session = await client.createSession({
    onPermissionRequest: async (request, invocation) => {
        // Simulate async check — e.g., database lookup, user prompt, audit log
        await logPermissionRequest(invocation.sessionId, request);

        const approved = await askUserViaUI(request);
        if (approved) {
            return { kind: "approved" };
        }
        return { kind: "denied-interactively-by-user", feedback: "User denied via UI" };
    },
});
```

Handlers may return `Promise<PermissionRequestResult>` or `PermissionRequestResult` synchronously. The SDK awaits both.

## Permission Caching and Stateful Approval Patterns

The SDK does not cache permission decisions. Every new tool call that requires a permission triggers a fresh handler invocation. Implement caching inside your handler when you want to remember decisions:

```typescript
const approvedKinds = new Set<string>();

const session = await client.createSession({
    onPermissionRequest: async (request) => {
        // Cache at kind granularity — approve a kind once, remember for the session
        if (approvedKinds.has(request.kind)) {
            return { kind: "approved" };
        }

        const approved = await promptUser(`Allow all "${request.kind}" operations?`);
        if (approved) {
            approvedKinds.add(request.kind);
            return { kind: "approved" };
        }
        return { kind: "denied-interactively-by-user" };
    },
});
```

### Fine-Grained Caching by Operation

```typescript
const approvedOperations = new Map<string, PermissionRequestResult>();

function getCacheKey(request: PermissionRequest): string {
    if (request.kind === "shell") return `shell:${(request as any).fullCommandText}`;
    if (request.kind === "write") return `write:${(request as any).fileName}`;
    if (request.kind === "read") return `read:${(request as any).path}`;
    return request.kind;
}

const session = await client.createSession({
    onPermissionRequest: async (request) => {
        const key = getCacheKey(request);
        if (approvedOperations.has(key)) {
            return approvedOperations.get(key)!;
        }

        const result = await promptUserForDecision(request);
        approvedOperations.set(key, result);
        return result;
    },
});
```

Cache state is held entirely in your closure. Calling `session.disconnect()` does not clear your cache — scope cache lifetime deliberately if you resume sessions.

## Error Behavior

- Handler throws → SDK returns `{ kind: "denied-no-approval-rule-and-could-not-request-from-user" }`
- Handler returns invalid shape → protocol error; return one of the five documented result kinds
- Connection drops before handler responds → the pending RPC call times out on the CLI side

Test error paths explicitly. The e2e tests confirm throwing handlers produce a graceful denial rather than crashing the session.

## toolCallId Field

Every `PermissionRequest` may carry `toolCallId?: string`. This correlates the permission request to the specific tool call that triggered it. Use `toolCallId` for audit logging, per-call approval UIs, or correlating permission events with `tool.execution_complete` events in the event stream.

```typescript
onPermissionRequest: (request) => {
    if (request.toolCallId) {
        console.log(`Permission for tool call ${request.toolCallId}: kind=${request.kind}`);
    }
    return { kind: "approved" };
},
```
