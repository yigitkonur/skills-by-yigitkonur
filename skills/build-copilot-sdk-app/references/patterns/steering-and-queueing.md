# Steering and Queueing

## Two Modes of Sending While Busy

When a session is actively processing a turn, `send()` accepts a `mode` field that controls delivery:

- `"enqueue"` (default) — message is queued, processed as its own full turn after the current turn completes
- `"immediate"` — message is injected into the **current** turn as a steering prompt; agent sees it before its next LLM call

When the session is idle, both modes behave identically: the message starts a new turn immediately.

## Queueing: FIFO Sequential Processing

Omit `mode` or pass `mode: "enqueue"`. Messages queue in FIFO order and each triggers a full agentic turn.

```typescript
import { CopilotClient } from "@github/copilot-sdk";

const client = new CopilotClient();
await client.start();

const session = await client.createSession({
  model: "gpt-4.1",
  onPermissionRequest: async () => ({ kind: "approved" }),
});

// Task 1 starts executing immediately
await session.send({ prompt: "Set up the project structure" });

// Task 2 queued while task 1 runs — processes after task 1 completes
await session.send({
  prompt: "Add unit tests for the auth module",
  mode: "enqueue",
});

// Task 3 queued after task 2 — FIFO order guaranteed
await session.send({
  prompt: "Update the README with setup instructions",
  mode: "enqueue",
});

// Execution order: task1 → task2 → task3
// Each task gets its own full turn with the complete conversation history
```

## Steering: Mid-Turn Course Correction

Use `mode: "immediate"` to inject a correction into the current turn. The agent sees the steering message before its next LLM request and adjusts its in-progress response.

```typescript
// Start a long-running refactor
await session.send({
  prompt: "Refactor the authentication module to use sessions",
});

// While the agent is working, steer it — no need to wait
await session.send({
  prompt: "Actually, use JWT tokens instead of sessions",
  mode: "immediate",
});
```

Steering is best-effort: if the agent has already committed to a tool call, the steering takes effect after that call completes but still within the same turn. If the turn completes before the steering message is processed, it is automatically moved to the front of the queue for the next turn.

## Combining Steering and Queueing

Use both patterns together: steer the current work while queuing follow-up tasks.

```typescript
// Start a task
await session.send({ prompt: "Refactor the database layer" });

// Steer current work (affects the active turn)
await session.send({
  prompt: "Keep backwards compatibility with the v1 API",
  mode: "immediate",
});

// Queue a follow-up (runs after current turn completes)
await session.send({
  prompt: "Add migration scripts for the schema changes",
  mode: "enqueue",
});
```

## How Queueing Works Internally

1. Message added to session `itemQueue` as a `QueuedItem`
2. When current turn completes, session becomes idle, `processQueuedItems()` runs
3. Items dequeued in FIFO order — each starts a full agentic turn
4. If a steering message was pending when the turn ended, it moves to the front of the queue
5. Queue drains until empty, then session emits `session.idle`

## How Steering Works Internally

1. Message added to `ImmediatePromptProcessor` queue
2. Before the next LLM request within the current turn, message is injected as a user message
3. Agent incorporates the steering into its in-progress reasoning
4. If turn completes before injection, message moves to the regular queue

## Conversation Flow Control

### Waiting for Queue to Drain

```typescript
// Send multiple queued tasks
await session.send({ prompt: "Task 1: implement feature A" });
await session.send({ prompt: "Task 2: implement feature B", mode: "enqueue" });
await session.send({ prompt: "Task 3: implement feature C", mode: "enqueue" });

// Wait for all three tasks to complete
await new Promise<void>((resolve) => {
  session.on((event) => {
    if (event.type === "session.idle") {
      resolve();
    }
  });
});
// All three tasks finished
```

### Building an Interactive UI

```typescript
class InteractiveChat {
  private session: CopilotSession;
  private isProcessing = false;

  constructor(session: CopilotSession) {
    this.session = session;
    session.on((event) => {
      if (event.type === "session.idle") {
        this.isProcessing = false;
      }
    });
  }

  async send(prompt: string): Promise<void> {
    if (!this.isProcessing) {
      this.isProcessing = true;
      await this.session.send({ prompt });
    } else {
      // Session busy — queue for sequential processing
      await this.session.send({ prompt, mode: "enqueue" });
    }
  }

  async correct(prompt: string): Promise<void> {
    // Steer the current turn
    await this.session.send({ prompt, mode: "immediate" });
  }
}
```

## Rate Limiting Considerations

Each queued message triggers a full LLM turn. Queueing many messages in rapid succession can exhaust rate limits. Throttle message submission when building automation:

```typescript
async function sendWithBackoff(
  session: CopilotSession,
  prompts: string[],
  delayMs = 1000
): Promise<void> {
  for (const prompt of prompts) {
    await session.send({ prompt, mode: "enqueue" });
    await new Promise(r => setTimeout(r, delayMs));
  }
}
```

## Choosing Between Steering and Queueing

| Scenario | Use | Reason |
|---|---|---|
| Agent is going down the wrong path | `"immediate"` | Redirect before damage is done |
| Additional task to add to backlog | `"enqueue"` | Doesn't disrupt current work |
| Forgot to mention a constraint | `"immediate"` | Agent incorporates it now |
| Chaining sequential tasks | `"enqueue"` | FIFO ordering, clean turns |
| Agent about to make a mistake | `"immediate"` | Intervene in current turn |
| Unrelated follow-up request | `"enqueue"` | Gets its own full context turn |

Default to `"enqueue"`. Only use `"immediate"` when the current turn is actively heading in the wrong direction.

## `pending_messages.modified` Event

The session emits `pending_messages.modified` when the queue state changes — messages added, removed, or reordered. Use this to keep UI queue indicators in sync.

```typescript
session.on((event) => {
  if (event.type === "pending_messages.modified") {
    // Update UI: show count of pending messages
    updateQueueIndicator(event.data);
  }
});
```

## Best Practices

- **Keep steering messages concise** — the agent needs to understand the correction instantly; long steering messages fragment the current turn's reasoning
- **Do not over-steer** — multiple rapid `"immediate"` messages within a single turn degrade output quality; if major redirection is needed, abort the turn and start fresh
- **Show queue state in your UI** — display pending message count; listen for `session.idle` to clear the display
- **Handle steering-to-queue fallback** — if a steering message arrives after the turn completes, it is automatically moved to the queue; design your UI to reflect this
