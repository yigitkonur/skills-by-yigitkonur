# Permissions and User Input

Check `dist/types.d.ts` and `dist/generated/rpc.d.ts` for the selected package. As of stable `0.3.0`, public docs and README prose may still show older permission result names, while the exported TypeScript result type uses protocol decision names.

## Permission handler is required

Every `createSession` and `resumeSession` requires `onPermissionRequest`:

```typescript
import { approveAll } from "@github/copilot-sdk";

const session = await client.createSession({
  model: "gpt-5",
  onPermissionRequest: approveAll,
});
```

`approveAll` is useful for local demos and deliberately unattended tools. It is dangerous for production apps because it approves file writes, shell commands, MCP calls, URL access, custom tools, and memory operations.

## PermissionHandler type

```typescript
type PermissionHandler = (
  request: PermissionRequest,
  invocation: { sessionId: string },
) => Promise<PermissionRequestResult> | PermissionRequestResult;
```

Current stable `PermissionRequest.kind`:

```typescript
type PermissionRequestKind =
  | "shell"
  | "write"
  | "mcp"
  | "read"
  | "url"
  | "custom-tool"
  | "memory"
  | "hook";
```

## PermissionRequestResult

Current stable `PermissionRequestResult` is `PermissionDecisionRequest["result"] | { kind: "no-result" }`.

Use these handler decisions in TypeScript:

```typescript
type PermissionRequestResult =
  | { kind: "approve-once" }
  | { kind: "approve-for-session"; approval: ApprovalScope }
  | { kind: "approve-for-location"; approval: ApprovalScope; locationKey: string }
  | { kind: "reject"; feedback?: string }
  | { kind: "user-not-available" }
  | { kind: "no-result" };
```

Approval scopes include:

```typescript
type ApprovalScope =
  | { kind: "commands"; commandIdentifiers: string[] }
  | { kind: "read" }
  | { kind: "write" }
  | { kind: "mcp"; serverName: string; toolName: string | null }
  | { kind: "mcp-sampling"; serverName: string }
  | { kind: "memory" }
  | { kind: "custom-tool"; toolName: string };
```

`no-result` leaves v3 broadcast permission requests unanswered, but protocol v2 adapters reject it. Avoid it unless you are intentionally building an observer client.

## Permission patterns

### Selective approval

```typescript
onPermissionRequest: async (request) => {
  switch (request.kind) {
    case "read":
      return { kind: "approve-once" };
    case "shell":
    case "write":
      return { kind: "reject", feedback: "Writes and shell commands require explicit UI approval." };
    default:
      return { kind: "user-not-available" };
  }
}
```

### Session-scoped approval

```typescript
onPermissionRequest: async (request) => {
  if (request.kind === "read") {
    return { kind: "approve-for-session", approval: { kind: "read" } };
  }
  return { kind: "reject" };
}
```

### Interactive approval with UI

```typescript
onPermissionRequest: async (request) => {
  const approved = await showPermissionDialog(request);
  return approved
    ? { kind: "approve-once" }
    : { kind: "reject", feedback: "Denied by user" };
}
```

If the handler throws, current stable source responds with `{ kind: "user-not-available" }`.

## Permission events

All clients connected to a session can observe permission flow:

```typescript
session.on("permission.requested", (event) => {
  console.log(event.data.permissionRequest.kind);
});

session.on("permission.completed", (event) => {
  console.log(event.data.result.kind);
});
```

`permission.completed` event result kinds are event-facing labels, not handler return objects:

- `approved`
- `approved-for-session`
- `approved-for-location`
- `denied-by-rules`
- `denied-no-approval-rule-and-could-not-request-from-user`
- `denied-interactively-by-user`
- `denied-by-content-exclusion-policy`
- `denied-by-permission-request-hook`

## User input (ask_user)

When the model calls `ask_user`, the SDK invokes `onUserInputRequest`:

```typescript
const session = await client.createSession({
  onPermissionRequest: approveAll,
  onUserInputRequest: async (request) => {
    if (request.choices?.length) {
      return { answer: request.choices[0], wasFreeform: false };
    }
    return { answer: "Proceed", wasFreeform: true };
  },
});
```

If `onUserInputRequest` is omitted and the model asks a question, the SDK throws and the model receives an error.

## Elicitation

Elicitation is structured form input. Observing `elicitation.requested` events is useful for UI logs, but a client that should answer forms must register `onElicitationRequest`:

```typescript
const session = await client.createSession({
  onPermissionRequest: approveAll,
  onElicitationRequest: async (context) => {
    return {
      action: "accept",
      content: { confirmed: true },
    };
  },
});
```

Supported result actions are `accept`, `decline`, or `cancel` in current package docs. When `onElicitationRequest` is provided, the session advertises `session.capabilities.ui?.elicitation`.

Elicitation events:

```typescript
session.on("elicitation.requested", (event) => {
  console.log(event.data.message);
  console.log(event.data.requestedSchema);
});

session.on("elicitation.completed", (event) => {
  console.log(event.data.requestId);
});
```

## Steering notes

- Use `approveAll` only when the blast radius is acceptable.
- Match on `request.kind` first; fields are kind-specific.
- Return current protocol decisions (`approve-once`, `reject`, etc.), not stale README prose values (`approved`, `denied-interactively-by-user`) unless installed types show those values.
- For observer clients, use `{ kind: "no-result" }` only after verifying the connected protocol tolerates it.
- For unattended apps, provide both `onPermissionRequest` and `onUserInputRequest` so the agent does not block on user prompts.
