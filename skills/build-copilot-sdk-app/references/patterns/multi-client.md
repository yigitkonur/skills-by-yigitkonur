# Multi-Client Architecture

## Broadcast Behavior

The SDK broadcasts session events to all connected clients. When multiple `CopilotClient` instances connect to the same CLI server and join the same session, every client receives every event: `external_tool.requested`, `permission.requested`, `permission.completed`, `external_tool.completed`, `assistant.message`, `session.idle`, and all other session event types.

This is not a subscription model — all clients see everything. Design your client logic to handle receiving events you did not initiate.

## Connecting Multiple Clients to the Same CLI Server

Multi-client requires TCP transport. Use `cliUrl` on at least the second client to point to the running CLI server. The first client can auto-spawn the CLI or connect via TCP.

```typescript
import { CopilotClient } from "@github/copilot-sdk";

// Client 1: auto-spawns CLI via stdio (default), or connects via TCP
const client1 = new CopilotClient();
await client1.start();

// Create a session with client 1
const session1 = await client1.createSession({
  onPermissionRequest: async () => ({ kind: "approved" }),
  tools: [myPrimaryTool],
});

// Read the actual port the CLI is listening on
// (The SDK exposes this after connection is established)
const actualPort = (client1 as any).actualPort;

// Client 2: connects to the SAME CLI process via TCP
const client2 = new CopilotClient({ cliUrl: `localhost:${actualPort}` });
await client2.start();

// Resume the same session from client 2
const session2 = await client2.resumeSession(session1.sessionId, {
  onPermissionRequest: async () => ({ kind: "approved" }),
  tools: [mySecondaryTool],  // Registers additional tools on the session
});
```

## TCP Transport Requirement

Multi-client is only possible with TCP transport. The default stdio transport uses stdin/stdout of the CLI process, which cannot be shared between processes.

```typescript
// WRONG: stdio transport — second client cannot share the CLI process
const client1 = new CopilotClient({ useStdio: true });

// CORRECT: TCP transport — multiple clients can connect to same port
const client1 = new CopilotClient({ useStdio: false }); // TCP is default when cliUrl is omitted but CLI is headless
const client2 = new CopilotClient({ cliUrl: "localhost:4321" });
```

In test environments, the first client spawns the CLI and then you read `actualPort` to connect subsequent clients to the same process.

## `external_tool.requested` Broadcast Semantics

When the agent requests an external tool call, the `external_tool.requested` event broadcasts to all connected clients. The SDK routes the tool call to whichever client registered that tool name. If multiple clients register the same tool name, the first responder wins.

```typescript
// Client 1 registers tool A
const session1 = await client1.createSession({
  tools: [defineTool("city_lookup", { ... })],
  onPermissionRequest: approveAll,
});

// Client 2 resumes the session with tool B — both tools are now available
const session2 = await client2.resumeSession(session1.sessionId, {
  tools: [defineTool("currency_lookup", { ... })],
  onPermissionRequest: approveAll,
});

// Both clients see external_tool.requested events, but:
// - city_lookup calls are handled by client1's tool handler
// - currency_lookup calls are handled by client2's tool handler
// Both clients see external_tool.completed for all tool calls

session1.on((event) => {
  if (event.type === "external_tool.requested") {
    console.log("Client1 sees tool request:", event.data.toolName);
  }
});
session2.on((event) => {
  if (event.type === "external_tool.requested") {
    console.log("Client2 sees tool request:", event.data.toolName);
  }
});
```

## `permission.requested` Broadcast and First-Responder Semantics

Permission requests broadcast to all clients. The first client whose `onPermissionRequest` handler returns a response wins. Other clients' handlers are ignored for that request, but all clients see the `permission.completed` event with the result.

```typescript
// Client 1: approves all — will respond quickly
const session1 = await client1.createSession({
  onPermissionRequest: (request) => {
    console.log("Client1 handling permission:", request);
    return { kind: "approved" };
  },
});

// Client 2: never resolves — client1 always wins
const session2 = await client2.resumeSession(session1.sessionId, {
  onPermissionRequest: () => new Promise(() => {}), // intentionally never settles
});

// Both clients see permission.requested
// Both clients see permission.completed with result kind: "approved"
// Only client1 actually handled the request
```

This first-responder pattern enables a monitoring client that observes permission decisions without interfering with the primary handler.

## Tool Lifecycle: Disconnect Removes Tools

When a client disconnects, all tools it registered are removed from the session. Tools registered by still-connected clients remain available.

```typescript
// Client 1: stable_tool persists
const session1 = await client1.createSession({
  tools: [defineTool("stable_tool", { ... })],
  onPermissionRequest: approveAll,
});

// Client 2: ephemeral_tool disappears on disconnect
const session2 = await client2.resumeSession(session1.sessionId, {
  tools: [defineTool("ephemeral_tool", { ... })],
  onPermissionRequest: approveAll,
});

// After client2 disconnects, ephemeral_tool is gone from the session
await client2.stop(); // or forceStop()
// Allow server-side cleanup
await new Promise(r => setTimeout(r, 500));

// Now only stable_tool is available — agent cannot invoke ephemeral_tool
```

## Client Coordination Patterns

### IDE + Dashboard + Monitor

```typescript
// IDE client: primary tool provider, handles permissions
const ideClient = new CopilotClient({ cliUrl: "localhost:4321" });
const ideSession = await ideClient.createSession({
  tools: [editFileTool, runTestsTool, gitCommitTool],
  onPermissionRequest: async (req) => {
    // Show permission dialog in IDE UI
    return await ideUI.requestPermission(req);
  },
});

// Dashboard client: observes all events for web UI, provides web tools
const dashClient = new CopilotClient({ cliUrl: "localhost:4321" });
const dashSession = await dashClient.resumeSession(ideSession.sessionId, {
  tools: [searchDocsTool, createIssueTool],
  onPermissionRequest: () => new Promise(() => {}), // defers to IDE
});

// Monitoring client: pure observer, no tools, no permission handling
const monitorClient = new CopilotClient({ cliUrl: "localhost:4321" });
const monitorSession = await monitorClient.resumeSession(ideSession.sessionId, {
  onPermissionRequest: () => new Promise(() => {}),
});

monitorSession.on((event) => {
  metrics.record(event.type, event);
});
```

### Avoiding Tool Conflicts

When resuming a session with `tools: []` or no tools array, the existing tool registrations from other clients are preserved. Passing an empty tools array does NOT clear tools registered by other clients.

```typescript
// Client 2 resumes with NO tools — client 1's tools remain intact
const session2 = await client2.resumeSession(session1.sessionId, {
  onPermissionRequest: approveAll,
  // No tools: property — existing tools from client1 are preserved
});
```

## Use Cases Requiring Multi-Client

- **IDE plugin + web dashboard**: IDE manages coding tools, web UI displays progress in real time
- **Operator + observer**: One process drives the session, another records all events to a log or database
- **Multi-tool distribution**: Different processes own different tool categories (file system tools vs. API tools vs. browser tools)
- **Redundant permission handlers**: Primary handler in main process, fallback handler in supervisor process

## Summary of Broadcast Rules

| Event Type | Who receives | Who handles |
|---|---|---|
| `external_tool.requested` | All clients | Client that owns the tool |
| `external_tool.completed` | All clients | N/A (informational) |
| `permission.requested` | All clients | First client whose handler responds |
| `permission.completed` | All clients | N/A (informational) |
| `assistant.message` | All clients | N/A (informational) |
| `session.idle` | All clients | N/A (informational) |
