# Streaming Patterns — Event Subscription Reference

## Core Subscription API

`CopilotSession.on()` has two overloads. Use them based on whether you need a single typed event or all events.

### Typed subscription — `session.on(eventType, handler)`

TypeScript narrows `event.data` to the exact shape for the given `eventType`. This is the preferred form when handling specific events.

```typescript
import { CopilotSession } from "@github/copilot-sdk";

// data is narrowed to { messageId: string; deltaContent: string; parentToolCallId?: string }
const unsubscribe = session.on("assistant.message_delta", (event) => {
  process.stdout.write(event.data.deltaContent);
});

// data is narrowed to { errorType: string; message: string; stack?: string; statusCode?: number }
const unsubscribeErr = session.on("session.error", (event) => {
  console.error(`[${event.data.errorType}] ${event.data.message}`);
});

// Call the returned function to stop receiving events
unsubscribe();
unsubscribeErr();
```

### Wildcard subscription — `session.on(handler)`

Receives every event type. Use a `switch` on `event.type` to discriminate. TypeScript uses the discriminated union from `SessionEvent` — narrowing works inside `case` branches.

```typescript
import type { SessionEvent } from "@github/copilot-sdk";

const unsubscribe = session.on((event: SessionEvent) => {
  switch (event.type) {
    case "assistant.message_delta":
      process.stdout.write(event.data.deltaContent);
      break;
    case "assistant.message":
      console.log("\nFull message:", event.data.content);
      break;
    case "tool.execution_start":
      console.log("Tool started:", event.data.toolName, event.data.toolCallId);
      break;
    case "session.idle":
      console.log("Session idle — turn complete");
      break;
    case "session.error":
      console.error("Session error:", event.data.message);
      break;
  }
});
```

## Unsubscribe Pattern

`session.on()` always returns `() => void`. Call it to remove the handler. Handlers registered with `on(eventType, handler)` are stored in a `Map<SessionEventType, Set<handler>>`; wildcard handlers are stored in a `Set`. Both are cleared on `session.disconnect()`.

```typescript
const unsub = session.on("assistant.message", (event) => {
  console.log(event.data.content);
});

// Remove after first message
session.on("session.idle", () => {
  unsub();
});
```

Use `await using` (TypeScript 5.2+) for automatic cleanup that calls `disconnect()`:

```typescript
await using session = await client.createSession({ streaming: true });
session.on("assistant.message_delta", (e) => process.stdout.write(e.data.deltaContent));
await session.sendAndWait({ prompt: "Hello" });
// session.disconnect() called automatically
```

## `streaming: true` Requirement

Set `streaming: true` in `SessionConfig` (passed to `client.createSession` or `client.resumeSession`) to receive ephemeral delta events. Without it, delta events (`assistant.message_delta`, `assistant.reasoning_delta`, `tool.execution_partial_result`, `tool.execution_progress`) are not emitted — only the final persisted events arrive.

```typescript
// Streaming ENABLED — delta events flow
const streamingSession = await client.createSession({
  streaming: true,
  onPermissionRequest: approveAll,
});

// Streaming DISABLED (default) — only final events
const quietSession = await client.createSession({
  streaming: false,
  onPermissionRequest: approveAll,
});
```

Confirmed by e2e test `streaming_fidelity.test.ts`: with `streaming: false`, `deltaEvents.length === 0`; with `streaming: true`, `deltaEvents.length >= 1`. The final `assistant.message` event is always emitted regardless of streaming mode.

## Delta Accumulation Pattern

Delta events are ephemeral and not persisted. Accumulate them in memory to reconstruct the full streamed response before the final `assistant.message` arrives. Key: correlate via `messageId`.

```typescript
const chunks = new Map<string, string>(); // messageId → accumulated text

session.on("assistant.message_delta", (event) => {
  const existing = chunks.get(event.data.messageId) ?? "";
  chunks.set(event.data.messageId, existing + event.data.deltaContent);
});

session.on("assistant.message", (event) => {
  const accumulated = chunks.get(event.data.messageId) ?? "";
  // accumulated === event.data.content (modulo whitespace normalization)
  chunks.delete(event.data.messageId);
  console.log("Complete response:", event.data.content);
});
```

For reasoning deltas, correlate via `reasoningId`:

```typescript
const reasoningChunks = new Map<string, string>();

session.on("assistant.reasoning_delta", (event) => {
  const existing = reasoningChunks.get(event.data.reasoningId) ?? "";
  reasoningChunks.set(event.data.reasoningId, existing + event.data.deltaContent);
});

session.on("assistant.reasoning", (event) => {
  // event.data.content is the complete reasoning block
  reasoningChunks.delete(event.data.reasoningId);
});
```

## Event Ordering Guarantees

The agentic turn flow emits events in this deterministic order (confirmed by `event_fidelity.test.ts`):

```
user.message
assistant.turn_start
  assistant.intent              (ephemeral, streaming only)
  assistant.reasoning_delta*    (ephemeral, streaming only, repeated)
  assistant.reasoning
  assistant.message_delta*      (ephemeral, streaming only, repeated)
  assistant.message
  assistant.usage               (ephemeral)
  [if tools requested:]
    permission.requested        (ephemeral)
    permission.completed        (ephemeral)
    tool.execution_start
    tool.execution_partial_result* (ephemeral, repeated)
    tool.execution_progress*    (ephemeral, repeated)
    tool.execution_complete
    [agent loops: more turns...]
assistant.turn_end
session.idle                    (ephemeral) — ALWAYS last
```

`session.idle` is guaranteed to be the final event in the turn. `sendAndWait()` internally waits for `session.idle` before resolving.

The `parentId` field on each event points to the UUID of the immediately preceding event, forming a linked chain. Walk the chain by indexing events by `id`.

## Backpressure and Async Handler Considerations

Handlers in `_dispatchEvent` are called synchronously inside a `try/catch`. Handler errors are silently swallowed — the event loop continues to other handlers. If your handler is async, the promise is not awaited; rejections become unhandled promise rejections.

```typescript
// WRONG — async handler, rejection not caught by SDK
session.on("assistant.message", async (event) => {
  await writeToDatabase(event.data.content); // rejection lost if this throws
});

// CORRECT — catch errors explicitly
session.on("assistant.message", async (event) => {
  try {
    await writeToDatabase(event.data.content);
  } catch (err) {
    console.error("Failed to persist:", err);
  }
});
```

For high-throughput streaming (many `message_delta` events), avoid blocking I/O in the handler. Buffer deltas in an array and flush asynchronously:

```typescript
const buffer: string[] = [];
let flushScheduled = false;

session.on("assistant.message_delta", (event) => {
  buffer.push(event.data.deltaContent);
  if (!flushScheduled) {
    flushScheduled = true;
    setImmediate(() => {
      process.stdout.write(buffer.join(""));
      buffer.length = 0;
      flushScheduled = false;
    });
  }
});
```

## Multiple Handlers

Multiple handlers can be registered for the same event type. All fire for every event. Typed handlers fire before wildcard handlers (per `_dispatchEvent` implementation: typed map iterated first, then `eventHandlers` Set).

```typescript
session.on("assistant.message", (e) => logToFile(e));       // typed handler #1
session.on("assistant.message", (e) => updateUI(e));        // typed handler #2
session.on((e) => auditLog(e));                             // wildcard — fires after both typed handlers
```

## Event Envelope — Always Present

Every `SessionEvent` carries these fields regardless of type:

```typescript
interface EventEnvelope {
  id: string;          // UUID v4 — unique per event
  timestamp: string;   // ISO 8601
  parentId: string | null; // UUID of preceding event; null for first event in session
  ephemeral?: boolean; // true = not persisted; absent/false = persisted to disk
  type: SessionEventType;
  data: object;        // shape depends on type
}
```

Ephemeral events are not replayed when you call `client.resumeSession()`. Persisted events (no `ephemeral` flag or `ephemeral: false`) are included in `session.getMessages()`.
