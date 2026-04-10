# Feed System Architecture

The feed system transforms raw RuntimeEvents into structured display events for Athena's terminal UI.

## Overview

```
RuntimeEvent (from harness)
  → FeedMapper
    → FeedEvent[] (one runtime event can produce multiple feed events)
      → FeedStore (in-memory state)
        → Timeline (projection for UI)
          → Event Feed (rendered rows)
```

## FeedMapper

The mapper (`src/core/feed/mapper.ts`) is the core transformation engine:

1. Receives a `RuntimeEvent`
2. Tracks session state (Session entity, Run entity, Actor registry)
3. Produces one or more `FeedEvent` objects
4. Handles special cases:
   - TodoWrite tool calls → `todo.add` / `todo.update` / `todo.done` events
   - Agent messages → `agent.message` events
   - Run boundaries → `run.start` / `run.end` events

## 27 FeedEventKinds

| Kind | Source | Description |
|------|--------|-------------|
| `session.start` | Runtime | Session began |
| `session.end` | Runtime | Session ended |
| `run.start` | Derived | New run (turn) started |
| `run.end` | Derived | Run completed |
| `user.prompt` | Runtime | User submitted prompt |
| `tool.delta` | Runtime | Streaming tool output |
| `tool.pre` | Runtime | Tool invocation pending |
| `tool.post` | Runtime | Tool completed |
| `tool.failure` | Runtime | Tool errored |
| `permission.request` | Runtime | Permission needed |
| `permission.decision` | Derived | Permission granted/denied |
| `stop.request` | Runtime | Stop signal |
| `stop.decision` | Derived | Stop decision |
| `subagent.start` | Runtime | Subagent spawned |
| `subagent.stop` | Runtime | Subagent ended |
| `notification` | Runtime | Info notification |
| `compact.pre` | Runtime | Context compaction |
| `setup` | Runtime | Session setup |
| `unknown.hook` | Runtime | Unrecognized event |
| `todo.add` | Derived | Task created |
| `todo.update` | Derived | Task updated |
| `todo.done` | Derived | Task completed |
| `agent.message` | Derived | Agent text output |
| `teammate.idle` | Runtime | Teammate idle |
| `task.completed` | Runtime | Task done |
| `config.change` | Runtime | Config changed |

## Entity Tracking

### Session

```typescript
type Session = {
  id: string;
  startedAt: number;
  endedAt?: number;
};
```

### Run

```typescript
type Run = {
  id: string;
  sessionId: string;
  startedAt: number;
  endedAt?: number;
  counters: {
    tool_uses: number;
    tool_failures: number;
    permission_requests: number;
    blocks: number;
  };
};
```

### Actor

```typescript
type Actor = {
  id: string;       // 'user', 'agent:root', 'subagent:<id>'
  label: string;
  type: 'user' | 'agent' | 'subagent';
};
```

The `ActorRegistry` manages actor lifecycle — new actors created on `subagent.start`, removed on `subagent.stop`.

## FeedStore

In-memory store (`src/core/feed/feedStore.ts`) holding:
- All feed events (sequential by `seq` number)
- Active session and runs
- Actor registry
- Filter state

## Timeline Projection

The timeline (`src/core/feed/timeline.ts`) projects feed events into the UI:
- Applies filters (error-only, run-scoped, search)
- Handles viewport (scroll position, page size)
- Tracks cursor position
- Manages expand/collapse state

## Supporting Modules

| Module | Purpose |
|--------|---------|
| `toolDisplay.ts` | Renders tool calls with human-readable summaries |
| `toolSummary.ts` | Generates one-line tool summaries |
| `cellFormatters.ts` | Formats individual table cells |
| `titleGen.ts` | Generates event titles |
| `transcript.ts` | Reads transcripts from stored sessions |
| `verbMap.ts` | Maps tool names to action verbs |
| `agentChain.ts` | Tracks parent-child agent relationships |
| `filter.ts` | Event filtering logic |

## Bootstrap from Stored Sessions

When resuming a session, `bootstrap.ts` replays stored `feed_events` from SQLite back through the FeedMapper to reconstruct the in-memory state. This is how session resume populates the event feed with historical data.
