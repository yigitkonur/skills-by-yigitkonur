# Permissions and User Input

## Permission handler (required)

Every `createSession` and `resumeSession` requires `onPermissionRequest`:

```typescript
import { approveAll } from "@github/copilot-sdk";

// Auto-approve everything (unattended operation):
const session = await client.createSession({
  onPermissionRequest: approveAll,
});

// Custom handler:
const session = await client.createSession({
  onPermissionRequest: async (request, invocation) => {
    // request: PermissionRequest
    // invocation: { sessionId: string }
    console.log(`Permission request: ${request.kind}`);
    return { kind: "approved" };
  },
});
```

## PermissionHandler type

```typescript
type PermissionHandler = (
  request: PermissionRequest,
  invocation: { sessionId: string },
) => Promise<PermissionRequestResult> | PermissionRequestResult;
```

## PermissionRequest

```typescript
interface PermissionRequest {
  kind: "shell" | "write" | "read" | "mcp" | "url" | "memory" | "custom-tool";
  toolCallId?: string;
  [key: string]: unknown;
}
```

### Permission request kinds and their fields

**shell** — execute a shell command:
```typescript
{
  kind: "shell",
  toolCallId?: string,
  fullCommandText: string,
  intention: string,
  commands: Array<{ identifier: string; readOnly: boolean }>,
  possiblePaths: string[],
  possibleUrls: Array<{ url: string }>,
  hasWriteFileRedirection: boolean,
  canOfferSessionApproval: boolean,
  warning?: string,
}
```

**write** — write/edit a file:
```typescript
{
  kind: "write",
  toolCallId?: string,
  intention: string,
  fileName: string,
  diff: string,
  newFileContents?: string,
}
```

**read** — read a file:
```typescript
{
  kind: "read",
  toolCallId?: string,
  intention: string,
  path: string,
}
```

**mcp** — invoke an MCP tool:
```typescript
{
  kind: "mcp",
  toolCallId?: string,
  serverName: string,
  toolName: string,
  toolTitle: string,
  args?: unknown,
  readOnly: boolean,
}
```

**url** — access a URL:
```typescript
{
  kind: "url",
  toolCallId?: string,
  intention: string,
  url: string,
}
```

**memory** — store a memory:
```typescript
{
  kind: "memory",
  toolCallId?: string,
  subject: string,
  fact: string,
  citations: unknown,
}
```

**custom-tool** — invoke a custom tool:
```typescript
{
  kind: "custom-tool",
  toolCallId?: string,
  toolName: string,
  toolDescription: string,
  args?: unknown,
}
```

## PermissionRequestResult

```typescript
type PermissionRequestResult =
  | { kind: "approved" }
  | { kind: "denied-by-rules"; rules: unknown[] }
  | { kind: "denied-no-approval-rule-and-could-not-request-from-user" }
  | { kind: "denied-interactively-by-user"; feedback?: string }
  | { kind: "denied-by-content-exclusion-policy"; path: string; message: string };
```

## Permission patterns

### Selective approval

```typescript
onPermissionRequest: async (request) => {
  // Approve reads and shell, deny writes
  if (request.kind === "read" || request.kind === "shell") {
    return { kind: "approved" };
  }
  if (request.kind === "write") {
    return {
      kind: "denied-interactively-by-user",
      feedback: "Write operations are not allowed in this session",
    };
  }
  return { kind: "approved" };
}
```

### Interactive approval with UI

```typescript
onPermissionRequest: async (request, { sessionId }) => {
  const userApproval = await showPermissionDialog({
    kind: request.kind,
    details: request.kind === "shell" ? request.fullCommandText : request.fileName,
  });
  if (userApproval) {
    return { kind: "approved" };
  }
  return { kind: "denied-interactively-by-user" };
}
```

### Multi-client permission handling

When multiple clients connect to the same session:
- `permission.requested` event broadcasts to ALL clients
- First client to respond wins
- Use a never-resolving handler on observer clients:

```typescript
// Observer client — never responds to permission requests
const observerSession = await client2.resumeSession(sessionId, {
  onPermissionRequest: () => new Promise(() => {}), // never resolves
});
```

## User input (askUser)

When the model calls the `ask_user` tool, the SDK invokes `onUserInputRequest`.

```typescript
const session = await client.createSession({
  onPermissionRequest: approveAll,
  onUserInputRequest: async (request, invocation) => {
    // request.question: string    — the model's question
    // request.choices?: string[]  — optional choice list
    // request.allowFreeform?: boolean — default true

    // Pick from choices:
    if (request.choices?.length) {
      return { answer: request.choices[0], wasFreeform: false };
    }

    // Freeform answer:
    return { answer: "Yes, proceed with the changes", wasFreeform: true };
  },
});
```

### UserInputRequest

```typescript
interface UserInputRequest {
  question: string;
  choices?: string[];
  allowFreeform?: boolean; // default true
}
```

### UserInputResponse

```typescript
interface UserInputResponse {
  answer: string;
  wasFreeform: boolean;
}
```

### Without onUserInputRequest

If `onUserInputRequest` is not provided and the model calls `ask_user`, the SDK throws. The model receives an error and may retry or proceed differently.

## Elicitation (MCP forms)

For MCP-style structured data collection, the SDK emits `elicitation.requested` events:

```typescript
session.on("elicitation.requested", (event) => {
  console.log("Form request:", event.data.message);
  console.log("Schema:", event.data.requestedSchema);
  // requestedSchema: { type: "object", properties: {...}, required: [...] }
  // mode?: "form"
});
```

## Permission events on session

All clients connected to a session can observe permission flow:

```typescript
session.on("permission.requested", (event) => {
  console.log(`Permission needed: ${event.data.permissionRequest.kind}`);
});

session.on("permission.completed", (event) => {
  console.log(`Result: ${event.data.result.kind}`);
});
```

## User input events

```typescript
session.on("user_input.requested", (event) => {
  console.log(`Question: ${event.data.question}`);
  console.log(`Choices: ${event.data.choices}`);
});

session.on("user_input.completed", (event) => {
  console.log(`Answered request: ${event.data.requestId}`);
});
```
