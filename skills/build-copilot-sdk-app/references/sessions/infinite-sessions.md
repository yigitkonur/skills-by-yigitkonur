# Infinite Sessions and Compaction

## What Infinite Sessions Are

Every LLM has a finite context window. In a long autonomous session, the accumulated conversation history, tool outputs, and reasoning traces eventually exhaust that window. Infinite sessions solve this by automatically compacting the context when utilization crosses configurable thresholds — summarizing earlier conversation history and discarding redundant content while preserving essential state. The session continues without interruption.

Infinite sessions are enabled by default. Disable explicitly only when you need full context fidelity:

```typescript
// Explicitly disabled (full context, no compaction)
const session = await client.createSession({
  onPermissionRequest: approveAll,
  infiniteSessions: { enabled: false },
});
```

## InfiniteSessionConfig Fields

```typescript
export interface InfiniteSessionConfig {
  enabled?: boolean;                         // default: true
  backgroundCompactionThreshold?: number;    // default: 0.80 (80% context utilization)
  bufferExhaustionThreshold?: number;        // default: 0.95 (95% context utilization)
}
```

Configure both thresholds at session creation:

```typescript
const session = await client.createSession({
  onPermissionRequest: approveAll,
  infiniteSessions: {
    enabled: true,
    backgroundCompactionThreshold: 0.75,  // start compaction earlier for safety
    bufferExhaustionThreshold: 0.90,      // block sooner to guarantee headroom
  },
});
```

Thresholds are context utilization ratios (0.0 to 1.0), not raw token counts. The CLI calculates utilization as `used_tokens / max_context_window_tokens` for the active model.

## Threshold Behavior

### Background Compaction Threshold (default 0.80)

When context utilization reaches 0.80:
- Compaction starts asynchronously in the background
- The session continues processing the current turn without interruption
- The agent is not aware compaction is happening
- Compaction generates a summary of earlier conversation and replaces it

The background window (0.80 to 0.95) gives compaction time to complete before the buffer is exhausted. Tighten the gap only if you have a strong reason.

### Buffer Exhaustion Threshold (default 0.95)

When context utilization reaches 0.95:
- If background compaction has not yet completed, the session blocks the current LLM call until compaction finishes
- This prevents context overflow (which would cause an API error)
- Once compaction completes, the blocked call proceeds with the freed context
- The session emits a `session.compaction_complete` event

Do not set `bufferExhaustionThreshold` below `backgroundCompactionThreshold`. The gap between them determines how much time compaction has to run before the session must block.

## workspacePath — Session Storage Location

When infinite sessions are enabled, each session has a `workspacePath` on disk where the CLI stores checkpoints, the plan, and artifacts:

```typescript
const session = await client.createSession({
  sessionId: "long-workflow-001",
  onPermissionRequest: approveAll,
  // infiniteSessions enabled by default
});

console.log(session.workspacePath);
// e.g. ~/.copilot/session-state/long-workflow-001

// Directory structure:
// long-workflow-001/
//   checkpoints/   — conversation history snapshots
//   plan.md        — agent planning state
//   files/         — artifacts created by the agent
```

`session.workspacePath` is `undefined` when infinite sessions are disabled.

## Compaction RPC — compact()

Manually trigger compaction or inspect compaction state via the session's typed RPC:

```typescript
const result = await session.rpc.compaction.compact();
// Returns: { success: boolean; tokensRemoved: number; messagesRemoved: number }
console.log(`Compaction freed ${result.tokensRemoved} tokens`);
```

Use this to:
- Proactively free context before a large task
- Log compaction metrics for monitoring
- Verify that compaction ran after a threshold was crossed

## session.compaction_complete Event

Listen for the `session.compaction_complete` event to react when compaction completes:

```typescript
session.on("session.compaction_complete", async (event) => {
  console.log("Context compacted — session continues with freed context");

  // Optionally checkpoint application state here
  await saveCompactionRecord(session.sessionId, new Date());
});
```

Typed subscription (if `"session.compaction_complete"` is in the `SessionEventType` union):

```typescript
const unsubscribe = session.on("session.compaction_complete", (event) => {
  // handle compaction
  unsubscribe();  // one-shot if desired
});
```

## How Compaction Works Internally

1. The CLI tracks token utilization against the model's `max_context_window_tokens`
2. At `backgroundCompactionThreshold`, the compaction routine starts on a background thread
3. The compaction routine calls the LLM to produce a structured summary of the oldest portion of the conversation history (tool calls, assistant reasoning, file reads, etc.)
4. The summary replaces the compacted messages in the in-memory context; the original messages remain in checkpoints on disk for auditability
5. At `bufferExhaustionThreshold`, if compaction is still running, the next LLM call waits (blocks) until compaction finishes
6. After compaction, context utilization drops to roughly the size of the summary plus the retained recent history
7. The CLI emits `session.compacted`

What compaction preserves:
- The agent's current plan (`plan.md`)
- Recent conversation turns (the tail of the context window)
- Artifacts written to disk (`files/`)
- The final summary of earlier history

What compaction discards from the live context (still on disk in checkpoints):
- Detailed intermediate tool outputs
- Step-by-step reasoning traces from earlier turns
- Verbose file contents that were read and are no longer active

## Long-Running Autonomous Session Patterns

### Pattern 1: Monitor-and-Extend

Start a long task, subscribe to key events, handle compaction gracefully:

```typescript
const session = await client.createSession({
  sessionId: "autonomous-refactor-001",
  model: "gpt-4.1",
  onPermissionRequest: approveAll,
  infiniteSessions: {
    enabled: true,
    backgroundCompactionThreshold: 0.80,
    bufferExhaustionThreshold: 0.95,
  },
});

let compactionCount = 0;

session.on("session.compaction_complete", async () => {
  compactionCount++;
  console.log(`Compaction #${compactionCount} completed`);
});

session.on("session.error", (event) => {
  console.error("Session error:", event.data.message);
});

// Queue multiple phases as a pipeline
await session.send({ prompt: "Phase 1: audit all TypeScript files for type safety issues" });
await session.send({ prompt: "Phase 2: fix the issues found in Phase 1", mode: "enqueue" });
await session.send({ prompt: "Phase 3: add unit tests for the fixed code", mode: "enqueue" });
await session.send({ prompt: "Phase 4: update the documentation", mode: "enqueue" });

// Wait for the entire pipeline with a long timeout
await session.sendAndWait(
  { prompt: "Phase 5: summarize all changes made" },
  30 * 60 * 1000  // 30 minutes
);

console.log(`Completed. Compactions triggered: ${compactionCount}`);
await session.disconnect();
```

### Pattern 2: Checkpoint-Aware Resumable Workflow

Use `sessionId` + `disconnect()` between phases to allow recovery from process crashes:

```typescript
async function runPhase(sessionId: string, phase: number, prompt: string) {
  const client = new CopilotClient();
  await client.start();

  const sessions = await client.listSessions();
  const exists = sessions.some(s => s.sessionId === sessionId);

  const session = exists
    ? await client.resumeSession(sessionId, { onPermissionRequest: approveAll })
    : await client.createSession({ sessionId, onPermissionRequest: approveAll });

  session.on("session.compaction_complete", () => {
    console.log(`Phase ${phase}: compaction ran, continuing`);
  });

  const response = await session.sendAndWait({ prompt }, 10 * 60 * 1000);
  console.log(`Phase ${phase} done:`, response?.data.content?.slice(0, 100));

  await session.disconnect();
  await client.stop();
}

const sessionId = "multi-phase-workflow-001";
await runPhase(sessionId, 1, "Analyze the codebase and identify refactoring targets");
await runPhase(sessionId, 2, "Implement the refactoring for the top 3 targets");
await runPhase(sessionId, 3, "Write regression tests for all changes");
```

### Pattern 3: Compaction-Triggered Logging

Use compaction events to build an external activity log:

```typescript
const compactionLog: { timestamp: Date; iteration: number }[] = [];
let compactionCount = 0;

session.on("session.compaction_complete", async () => {
  compactionCount++;
  compactionLog.push({ timestamp: new Date(), iteration: compactionCount });
  await writeCompactionLog(session.sessionId, compactionLog);
});
```

## When Compaction Triggers — Decision Matrix

| Context Utilization | State | Action |
|---|---|---|
| 0.0 – 0.79 | Normal | No action |
| 0.80 – 0.94 | Background compaction running | Session processes normally |
| 0.95+ (compaction done) | Context freed | Session continues normally |
| 0.95+ (compaction still running) | Buffer exhaustion | Next LLM call blocks until done |
| Compaction complete | — | `session.compaction_complete` event fired |

## Disabling Infinite Sessions

Disable when:
- You need the full unmodified context for analysis or auditing
- The workflow is short and will never approach context limits
- You are building a test harness that requires deterministic context

```typescript
const session = await client.createSession({
  onPermissionRequest: approveAll,
  infiniteSessions: { enabled: false },
});
// session.workspacePath is undefined
// No background compaction, no blocking at 95%
// Context overflow at max_context_window_tokens throws an API error
```

## Threshold Tuning Guidelines

- Narrow the gap between thresholds (e.g., 0.85 / 0.90) when compaction is fast (small context, capable hardware)
- Widen the gap (e.g., 0.70 / 0.95) for very long turns with heavy tool use where compaction may take longer
- Lower `backgroundCompactionThreshold` (e.g., 0.70) for mission-critical sessions where you cannot afford any blocking
- Never set `bufferExhaustionThreshold` lower than `backgroundCompactionThreshold`
