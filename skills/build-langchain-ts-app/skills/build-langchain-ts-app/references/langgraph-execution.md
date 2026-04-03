# LangGraph Execution & Persistence Reference

Complete reference for LangGraph execution, persistence, and checkpointing. All APIs verified against `@langchain/langgraph@1.2+`. TypeScript only.

---

## Quick Reference — Imports

```typescript
// Core graph primitives
import {
  StateGraph, StateSchema, ReducedValue, MessagesValue, UntrackedValue,
  GraphNode, ConditionalEdgeRouter, Command, Send, START, END,
  GraphRecursionError,
} from "@langchain/langgraph";

// Functional API
import { entrypoint, task, interrupt, getPreviousState } from "@langchain/langgraph";

// Checkpointers
import {
  MemorySaver,
  BaseCheckpointSaver,
  type Checkpoint,
  type CheckpointTuple,
  type CheckpointMetadata,
  type CheckpointListOptions,
  type PendingWrite,
  type ChannelVersions,
} from "@langchain/langgraph-checkpoint";

import { SqliteSaver } from "@langchain/langgraph-checkpoint-sqlite";
import { PostgresSaver } from "@langchain/langgraph-checkpoint-postgres";
import { MongoDBSaver } from "@langchain/langgraph-checkpoint-mongodb";
import { RedisSaver } from "@langchain/langgraph-checkpoint-redis";
import { ShallowRedisSaver } from "@langchain/langgraph-checkpoint-redis/shallow";
import { InMemoryCache } from "@langchain/langgraph-checkpoint";
```

---

## Persistence Architecture Overview

LangGraph persistence separates into two orthogonal planes. Confusing them leads to expensive and fragile designs.

```
Plane A: Thread persistence (checkpointer)
  thread_id + checkpoint_ns + checkpoint_id
    ├── checkpoint snapshot
    ├── channel versions
    ├── pending writes
    └── parent relationship

Plane B: Cross-thread memory (store)
  namespace[] + key
    ├── JSON document
    ├── timestamps
    └── optional vector search
```

**The rule:** persist graph state with a checkpointer, persist shared memory with a store, make side effects idempotent.

### Persistence Plane Comparison

| Data | Checkpointer | Store |
|------|:---:|:---:|
| Graph channels / thread state | Yes | No |
| Execution history / time-travel | Yes | No |
| Pending writes for crash recovery | Yes | No |
| Fork lineage | Yes | No |
| User profile across sessions | No | Yes |
| Semantic memory collection | No | Yes |
| Long-term facts across threads | No | Yes |

### Runtime Flow

```
1. Caller invokes graph with config.configurable.thread_id
2. Runtime asks checkpointer for the latest (or requested) checkpoint
3. Runtime reconstructs channels from the checkpoint
4. Runtime executes one or more tasks/nodes in a superstep
5. Runtime flushes pending writes according to durability mode
6. Runtime stores a new checkpoint
7. Caller can inspect state, history, or resume later
```

---

## BaseCheckpointSaver Interface

All checkpointer implementations extend this abstract class. Source: `libs/checkpoint/src/base.ts`.

```typescript
export abstract class BaseCheckpointSaver<V extends string | number = number> {
  serde: SerializerProtocol = new JsonPlusSerializer();

  constructor(serde?: SerializerProtocol);

  // Convenience wrapper — delegates to getTuple(), returns only the Checkpoint
  async get(config: RunnableConfig): Promise<Checkpoint | undefined>;

  // Primary "read checkpoint" method — returns full tuple or undefined
  abstract getTuple(
    config: RunnableConfig
  ): Promise<CheckpointTuple | undefined>;

  // Async generator of checkpoint tuples, newest first
  abstract list(
    config: RunnableConfig,
    options?: CheckpointListOptions
  ): AsyncGenerator<CheckpointTuple>;

  // Store a checkpoint snapshot; returns config pointing at new checkpoint_id
  abstract put(
    config: RunnableConfig,
    checkpoint: Checkpoint,
    metadata: CheckpointMetadata,
    newVersions: ChannelVersions
  ): Promise<RunnableConfig>;

  // Persist intermediate task writes (the crash-recovery bridge)
  abstract putWrites(
    config: RunnableConfig,
    writes: PendingWrite[],
    taskId: string
  ): Promise<void>;

  // Delete all checkpoints and writes for one thread ID
  abstract deleteThread(threadId: string): Promise<void>;

  getNextVersion(current: V | undefined): V;
}
```

**Method semantics:**
- `getTuple` — if `checkpoint_id` is in config, returns that exact checkpoint; if absent, returns the latest for that thread/namespace.
- `put` — returns a new `RunnableConfig` whose `configurable.checkpoint_id` is the freshly stored ID.
- `putWrites` — called by the runtime after each task completes; these writes survive crashes and are replayed on resume.
- `deleteThread` — may delete across all namespaces for the thread depending on implementation.

---

## Checkpoint Data Types

### Checkpoint

```typescript
export interface Checkpoint<
  N extends string = string,
  C extends string = string
> {
  v: number;                                          // Format version (currently 4)
  id: string;                                         // UUID6-based checkpoint ID
  ts: string;                                         // ISO timestamp
  channel_values: Record<C, unknown>;                 // Persisted channel payloads
  channel_versions: Record<C, number | string>;       // Monotonically increasing per channel
  versions_seen: Record<N, Record<C, number | string>>; // Per-node observed versions
}
```

**Field meaning:**

| Field | Purpose |
|---|---|
| `v` | Schema version; current default is `4` |
| `id` | Addresses this checkpoint; becomes `configurable.checkpoint_id` |
| `ts` | `new Date().toISOString()` at save time |
| `channel_values` | The actual state data, one entry per channel |
| `channel_versions` | Version counters; enables incremental Pregel execution |
| `versions_seen` | Per-node version observations; prevents re-running unchanged nodes |

`channel_versions` and `versions_seen` are not cosmetic — they are central to how the Pregel runtime decides which nodes need to run. A checkpoint is state + versioning + per-node observation history.

### CheckpointTuple

`CheckpointTuple` is the full "retrieval envelope." The runtime always needs more than the raw snapshot.

```typescript
export interface CheckpointTuple {
  config: RunnableConfig;             // Config that addresses this checkpoint
  checkpoint: Checkpoint;             // The state snapshot
  metadata?: CheckpointMetadata;      // Source, step, parents
  parentConfig?: RunnableConfig;      // Immediate predecessor
  pendingWrites?: CheckpointPendingWrite[];  // Writes not yet folded in
}
```

### CheckpointMetadata

```typescript
export type CheckpointMetadata<ExtraProperties extends object = object> = {
  source: "input" | "loop" | "update" | "fork";
  step: number;
  parents: Record<string, string>;
} & ExtraProperties;
```

| `source` value | When created |
|---|---|
| `"input"` | From initial call to `invoke`/`stream` |
| `"loop"` | Inside the Pregel execution loop (most checkpoints) |
| `"update"` | From manual `updateState()` call |
| `"fork"` | From `updateState(..., "__copy__")` fork operation |

`step` starts at `-1` for the input checkpoint, increments to `0` for the first loop checkpoint, then continues from there.

### CheckpointListOptions

```typescript
export type CheckpointListOptions = {
  limit?: number;          // Cap the number of results
  before?: RunnableConfig; // Cursor: list checkpoints older than this config
  filter?: Record<string, any>; // Saver-specific metadata filter
};
```

### PendingWrite Types

```typescript
export type PendingWrite<Channel = string> = [Channel, PendingWriteValue];

export type CheckpointPendingWrite<TaskId = string> = [
  TaskId,
  ...PendingWrite<string>
];
// Concretely: [taskId: string, channel: string, value: unknown]
```

---

## Checkpointer Implementations

### Class Hierarchy

```
BaseCheckpointSaver<V = number>
├── MemorySaver
├── PostgresSaver
├── SqliteSaver
├── MongoDBSaver
├── RedisSaver
└── ShallowRedisSaver
```

### Backend Comparison Table

| Saver | Durability | Setup required | Full history | ACID | TTL support | Scalability |
|---|:---:|:---:|:---:|:---:|:---:|---|
| `MemorySaver` | No | No | Yes | No | No | Single process only |
| `PostgresSaver` | Yes | Explicit `setup()` | Yes | Yes | No (use partitioning) | Horizontal via pooler |
| `SqliteSaver` | Yes | Auto (WAL mode) | Yes | Yes | No | Single node |
| `MongoDBSaver` | Yes | No helper | Yes | Document-level | Via TTL indexes | Replica sets |
| `RedisSaver` | Yes | Factory handles | Yes | No | Yes | Cluster mode |
| `ShallowRedisSaver` | Yes | Factory handles | No (latest only) | No | Yes | Cluster mode |

### MemorySaver (Development Only)

```typescript
import { MemorySaver } from "@langchain/langgraph-checkpoint";

const checkpointer = new MemorySaver();
const app = graph.compile({ checkpointer });

await app.invoke(
  { messages: [{ role: "user", content: "Hello" }] },
  { configurable: { thread_id: "user-123" } }
);
```

Internal storage model (conceptual):
```
storage[thread_id][checkpoint_ns][checkpoint_id]  → checkpoint + metadata
writes[thread_id|checkpoint_ns|checkpoint_id][taskId|idx]  → pending writes
```

`list()` supports: limiting results, metadata filtering, `before` cursor, thread/namespace scoping.

**Never use in production.** Data is lost on process restart. Multi-process environments will lose state across instances.

### SqliteSaver (Local Durable)

```typescript
import { SqliteSaver } from "@langchain/langgraph-checkpoint-sqlite";

// File-based (persistent)
const checkpointer = SqliteSaver.fromConnString("./langgraph.db");

// In-memory SQLite (test-mode)
const checkpointer = SqliteSaver.fromConnString(":memory:");

const graph = new StateGraph(State)
  .addNode("step1", async () => ({ steps: ["step1"] }))
  .addEdge("__start__", "step1")
  .compile({ checkpointer });

await graph.invoke({}, { configurable: { thread_id: "thread-sqlite-1" } });
```

Setup is automatic — the saver enables WAL mode, creates `checkpoints` and `writes` tables, and prepares statements on first use. Use for: local durability, single-file backend, modest write volume, desktop/server single-node deployments. Avoid for: high-concurrency writers, large-scale checkpoint history, horizontal scaling.

### PostgresSaver (Production Standard)

```typescript
import { PostgresSaver } from "@langchain/langgraph-checkpoint-postgres";

const checkpointer = PostgresSaver.fromConnString(
  process.env.DATABASE_URL!,
  { schema: "langgraph" }  // Optional; defaults to "public"
);

// REQUIRED before first use on a new schema
await checkpointer.setup();

const app = graph.compile({ checkpointer });
```

Constructor signature:
```typescript
interface PostgresSaverOptions {
  schema: string;  // Default: "public"
}

class PostgresSaver extends BaseCheckpointSaver {
  constructor(pool: pg.Pool, serde?: SerializerProtocol, options?: Partial<PostgresSaverOptions>);
  static fromConnString(connString: string, options?: Partial<PostgresSaverOptions>): PostgresSaver;
  async setup(): Promise<void>;
}
```

Tables created by `setup()`: `checkpoint_migrations`, `checkpoints`, `checkpoint_blobs`, `checkpoint_writes`. Tables are schema-qualified, so multiple apps/tenants can isolate state by schema.

### MongoDBSaver

```typescript
import { MongoClient } from "mongodb";
import { MongoDBSaver } from "@langchain/langgraph-checkpoint-mongodb";

const client = new MongoClient(process.env.MONGODB_URI!);
await client.connect();

const checkpointer = new MongoDBSaver({
  client,
  dbName: "langgraph",
  checkpointCollectionName: "checkpoints",
  checkpointWritesCollectionName: "checkpoint_writes",
  enableTimestamps: true,  // Stamps upserted_at; useful for TTL indexes
});

const app = graph.compile({ checkpointer });
await graph.invoke({}, { configurable: { thread_id: "thread-mongo-1" } });
```

Params type:
```typescript
export type MongoDBSaverParams = {
  client: MongoClient;
  dbName?: string;
  checkpointCollectionName?: string;
  checkpointWritesCollectionName?: string;
  enableTimestamps?: boolean;
};
```

No `fromConnString()` helper — caller must provide a connected `MongoClient`. `enableTimestamps` stamps `upserted_at` on documents, enabling MongoDB TTL index-based expiry for retention policies.

### RedisSaver

```typescript
import { RedisSaver } from "@langchain/langgraph-checkpoint-redis";

const checkpointer = await RedisSaver.fromUrl("redis://localhost:6379", {
  defaultTTL: 3600,       // Seconds; 0 = no expiry
  refreshOnRead: true,    // Reset TTL on each read
});

const app = graph.compile({ checkpointer });
await graph.invoke({}, { configurable: { thread_id: "thread-redis-1" } });
```

Constructor surface:
```typescript
export interface TTLConfig {
  defaultTTL?: number;
  refreshOnRead?: boolean;
}

export class RedisSaver extends BaseCheckpointSaver {
  constructor(client: RedisClientType, ttlConfig?: TTLConfig);
  static async fromUrl(url: string, ttlConfig?: TTLConfig): Promise<RedisSaver>;
  static async fromCluster(
    rootNodes: Array<{ url: string }>,
    ttlConfig?: TTLConfig
  ): Promise<RedisSaver>;
}
```

Uses Redis JSON, RediSearch indexes, and sorted sets for write ordering. Stores full history: checkpoint documents, blob documents, and write documents.

**Namespace note:** empty namespace is stored internally as `"__empty__"` for RediSearch compatibility; the external API still sees `""`.

### ShallowRedisSaver (Latest-State Only)

```typescript
import { ShallowRedisSaver } from "@langchain/langgraph-checkpoint-redis/shallow";

const checkpointer = await ShallowRedisSaver.fromUrl("redis://localhost:6379", {
  defaultTTL: 1800,
});
```

Keeps only the **latest** checkpoint per `thread_id + checkpoint_ns`. Lower storage footprint; no history; no time-travel; no fork/branch introspection. Use only when latest-resumable-state is the only requirement and Redis memory pressure matters.

---

## Thread Management

### The Four Identifiers

| Identifier | Role | Set by |
|---|---|---|
| `thread_id` | Root identity of a persistent execution thread | Caller |
| `checkpoint_id` | Exact address of a specific historical snapshot | Runtime (UUID6) |
| `checkpoint_ns` | Namespace scope; `""` for root, derived paths for subgraphs | Runtime (subgraphs auto-derive) |
| `parent_checkpoint_id` | Immediate predecessor checkpoint | Runtime |

### thread_id Semantics

`thread_id` is the root identity of one conversation, workflow instance, or resumable job.

```typescript
// Reuse the same thread_id to continue an existing thread
const config = { configurable: { thread_id: "user-42:ticket-123" } };

// Change thread_id to start a fresh independent thread
const newConfig = { configurable: { thread_id: "user-42:ticket-456" } };
```

**Recommended naming patterns:**
- `conversation:123`
- `ticket:456`
- `workflow:ingest:2026-03-23:abc`
- `user:42:thread:7`

Avoid random values if you intend to resume later. Avoid values with weak uniqueness guarantees. Never overload IDs that accidentally merge unrelated workflows.

### checkpoint_id Semantics

Without `checkpoint_id` in config: returns the latest checkpoint (pending writes are applied to produce "best current state").

With `checkpoint_id` in config: returns that exact historical snapshot (pending writes are NOT applied).

```
// This distinction is source-backed:
// applyPendingWrites: !config.configurable?.checkpoint_id
```

### checkpoint_ns Semantics

`checkpoint_ns` serves two distinct roles:
1. Public scoping for graph/subgraph state — root graph uses `""`.
2. Internal runtime namespace for subgraph and task-specific progress.

Do not treat it as "just a user tag" — treating it that way breaks multi-namespace subgraph flows. Let the runtime manage subgraph namespace mechanics unless you have an explicit need.

### Checkpoint Lineage Diagram

```
thread_id = "thread-1", checkpoint_ns = ""

cp-001  ←── parent of cp-002
  |
  ▼
cp-002  ←── parent of cp-003
  |  \
  ▼   \──► cp-004 (fork) ──► cp-005
cp-003
```

Forking is driven by `updateState(..., "__copy__")`, which creates a new checkpoint lineage marked `metadata.source = "fork"`.

---

## Pregel Execution Model

LangGraph's runtime is called **Pregel** (inspired by Google Pregel and Apache Beam). Every execution proceeds through a series of super-steps.

### Super-Step Lifecycle

```
1. graph.compile({ checkpointer })  →  CompiledGraph
2. app.invoke(input, config)        →  Execution begins
3. For each super-step:
   a. Identify ready nodes (all predecessors have completed)
   b. Execute ready nodes IN PARALLEL
   c. Merge outputs via channel reducers
   d. Persist pending writes via putWrites()
   e. Save checkpoint via put()
   f. Determine next super-step (or terminate)
4. Complete when all paths reach END
```

**Key properties:**
- Nodes within a single super-step run concurrently (JavaScript event loop + Promise.all internally).
- The state after each super-step is a consistent snapshot with all reducer outputs merged.
- `channel_versions` and `versions_seen` in the checkpoint tell the runtime which channels changed, so only affected nodes re-execute in the next super-step.
- A `GraphRecursionError` is thrown if the number of super-steps exceeds `recursionLimit` (default: 25).

### Parallel Fan-Out / Fan-In

Fan-out and fan-in happen when multiple edges originate from or converge at the same nodes. All branches within a super-step execute in parallel.

```typescript
import { StateGraph, MessagesValue, StateSchema, START, END } from "@langchain/langgraph";

const State = new StateSchema({ messages: MessagesValue });

const parallelGraph = new StateGraph(State)
  .addNode("llm1", callLlm1)
  .addNode("llm2", callLlm2)
  .addNode("llm3", callLlm3)
  .addNode("aggregator", aggregator)
  // All three start simultaneously (fan-out)
  .addEdge(START, "llm1")
  .addEdge(START, "llm2")
  .addEdge(START, "llm3")
  // All three must complete before aggregator runs (fan-in)
  .addEdge("llm1", "aggregator")
  .addEdge("llm2", "aggregator")
  .addEdge("llm3", "aggregator")
  .addEdge("aggregator", END)
  .compile();
```

### Map-Reduce via Send

`Send` enables dynamic fan-out with per-instance custom payloads. Each `Send` spawns an independent parallel execution of the target node with its own sub-state.

```typescript
import { Send } from "@langchain/langgraph";

const fanOutRouter = (state: typeof State.State): Send[] =>
  state.subjects.map(subject => new Send("processSubject", { subject }));

graph.addConditionalEdges("orchestrator", fanOutRouter);
```

---

## Durable Execution

### What LangGraph Guarantees

Safe claims:
- Persists checkpointed graph progress across super-steps.
- Persists pending writes associated with successful task completions.
- Can resume from saved thread state after crashes, failures, and interrupts.
- Successful sibling task work is recovered rather than recomputed from nothing.

**Not safe to claim:** exactly-once side effects, transactional atomicity across external systems, replay immunity for non-idempotent tasks.

### Durability Modes

```typescript
export type Durability = "exit" | "async" | "sync";
```

| Mode | Checkpoint timing | History | Use when |
|---|---|---|---|
| `"async"` | As progress is made (default) | Full | Good durability + performance balance |
| `"sync"` | Synchronously per step | Full | Strictest flush timing; write latency acceptable |
| `"exit"` | Deferred until final exit | Only final checkpoint | Cheapest; weak crash-recovery granularity |

**Legacy:** `checkpointDuring: false` maps to `"exit"`, `checkpointDuring: true` maps to `"async"`. New code must use `durability`.

### Crash Recovery Flow

```
Step 0:  input checkpoint saved
Step 1:  task A succeeds, task B succeeds, task C fails

Persisted state:
  - last stable checkpoint
  - pending writes from A and B

Resume:
  - load stable checkpoint
  - reapply pending writes from A and B
  - retry task C path only
```

The internal mechanism is `putWrites()`. The runtime does not re-run the whole graph from scratch — it resumes from the last checkpoint plus persisted pending writes.

### Idempotency is Required

Because retries happen, external side effects must be idempotent:

```typescript
// UNSAFE — may charge twice under retry
graph.addNode("chargeCard", async () => {
  await stripe.paymentIntents.create({ amount: 5000, currency: "usd" });
  return { charged: true };
});

// SAFE — idempotency key collapses duplicates
graph.addNode("chargeCard", async (state) => {
  await stripe.paymentIntents.create(
    { amount: 5000, currency: "usd" },
    { idempotencyKey: state.paymentOperationId }
  );
  return { charged: true };
});
```

---

## Compile Options

```typescript
const app = graph.compile({
  // Persistence backend
  checkpointer: new MemorySaver(),

  // Long-term memory store (cross-thread)
  store: new InMemoryStore(),

  // Node-level output cache
  cache: new InMemoryCache(),

  // Static debug interrupts
  interruptBefore: ["humanReview"],    // Pause BEFORE node executes
  interruptAfter: ["nodeB"],           // Pause AFTER node executes

  // Graph metadata
  name: "my-agent",
  description: "Email triage agent",
});
```

| Option | Type | Description |
|---|---|---|
| `checkpointer` | `BaseCheckpointSaver \| boolean` | Persistence backend; `false` disables checkpointing |
| `store` | `BaseStore` | Cross-thread long-term memory store |
| `cache` | `BaseCache<unknown>` | Node-level output cache |
| `interruptBefore` | `"*" \| string[]` | Node names to pause before; `"*"` pauses before all |
| `interruptAfter` | `"*" \| string[]` | Node names to pause after |
| `name` | `string` | Graph name (used in Studio and API) |

---

## Node Options

```typescript
graph.addNode("myNode", myNodeFn, {
  // Automatic retry on transient failures
  retryPolicy: {
    maxAttempts: 3,               // Default: 3
    initialInterval: 1000,        // ms; default: 500
    maxInterval: 128_000,         // ms; default: 128_000
    backoffFactor: 2,             // Default: 2 (exponential)
    retryOn: (err) => !err.message.includes("ValidationError"),
  },

  // Cache node output
  cachePolicy: {
    ttl: 3600,                    // Seconds; 0 = no expiry
    keyFunc: (state) => state.query,  // Custom cache key
  },

  // Declare allowed Command.goto destinations (required for routing validation)
  ends: ["nodeA", "nodeB"],

  // Private input schema for this node
  input: PrivateInputSchema,
});
```

| Option | Type | Description |
|---|---|---|
| `retryPolicy.maxAttempts` | `number` | Retry limit; default 3 |
| `retryPolicy.initialInterval` | `number` | Initial backoff in ms |
| `retryPolicy.maxInterval` | `number` | Max backoff cap in ms |
| `retryPolicy.backoffFactor` | `number` | Exponential multiplier |
| `retryPolicy.retryOn` | `(err: Error) => boolean` | Custom predicate; default retries on all except `TypeError`, `SyntaxError`, `ReferenceError` |
| `cachePolicy.ttl` | `number` | Cache TTL in seconds |
| `cachePolicy.keyFunc` | `(state) => string` | Custom cache key derivation |
| `ends` | `string[]` | Required when node returns `Command({ goto: ... })` |
| `input` | `ZodSchema` | Private input override (node sees only these fields) |

---

## Invocation Config Reference

```typescript
await app.invoke(input, {
  configurable: {
    thread_id: "user-123",        // Required with checkpointer
    checkpoint_id: "1ef4f...",    // Resume from specific checkpoint
    checkpoint_ns: "",            // Namespace; "" for root graph
  },
  recursionLimit: 50,             // Max super-steps; default 25
  context: { llm: "anthropic" },  // Runtime context (requires contextSchema)
  streamMode: "updates",          // Stream mode selection
  tags: ["production"],
  metadata: { project: "triage" },
});
```

| Config Key | Type | Default | Description |
|---|---|---|---|
| `configurable.thread_id` | `string` | — | Required with checkpointer; root thread identity |
| `configurable.checkpoint_id` | `string` | latest | Resume from exact historical checkpoint |
| `configurable.checkpoint_ns` | `string` | `""` | Namespace; managed by runtime for subgraphs |
| `recursionLimit` | `number` | `25` | Max super-steps before `GraphRecursionError` |
| `context` | `Record<string, any>` | — | Runtime context values (defined via `contextSchema`) |
| `streamMode` | `StreamMode \| StreamMode[]` | `"values"` | `"values"`, `"updates"`, `"messages"`, `"custom"`, `"tools"`, `"debug"` |
| `tags` | `string[]` | — | Tracing tags |
| `metadata` | `Record<string, any>` | — | Metadata attached to traces |

---

## State Inspection

### getState

```typescript
const snapshot = await app.getState({
  configurable: { thread_id: "user-123" },
});

// StateSnapshot structure:
// snapshot.values          — current state values
// snapshot.next            — next nodes to execute ([] if done)
// snapshot.tasks           — pending PregelTask objects
// snapshot.metadata        — CheckpointMetadata (source, step, parents)
// snapshot.config          — RunnableConfig to resume with
// snapshot.createdAt       — ISO timestamp
// snapshot.parentConfig    — config of immediate parent checkpoint
```

With a specific `checkpoint_id`: returns that exact historical snapshot, pending writes NOT applied.

Without `checkpoint_id`: returns the latest checkpoint with pending writes applied ("best current state").

### getStateHistory

```typescript
// Iterate all snapshots (newest first)
for await (const snapshot of app.getStateHistory({
  configurable: { thread_id: "user-123" },
})) {
  console.log(snapshot.metadata.step, snapshot.values);
}

// With options
for await (const snapshot of app.getStateHistory(config, {
  limit: 10,
  filter: { source: "loop" },
})) { /* ... */ }
```

### updateState

```typescript
// Manually patch state (creates a new "update" checkpoint)
await app.updateState(
  { configurable: { thread_id: "user-123" } },
  { messages: [{ role: "user", content: "Override" }] },
  "humanReview"   // Optional: attribute update as if from this node
);
```

`asNode` applies that node's reducers to the update values. Without it, the raw values are merged directly. The resulting checkpoint has `metadata.source = "update"`.

---

## Time Travel

### Replay from Historical Checkpoint

```typescript
// Collect history
const history: StateSnapshot[] = [];
for await (const s of app.getStateHistory(config)) {
  history.push(s);
}

// Resume execution from a specific earlier checkpoint
// Pass null input to re-run from the saved state
const result = await app.invoke(null, history[2].config);
```

### Fork a Thread

Forking creates a new execution branch from a prior checkpoint. The new branch has `metadata.source = "fork"` and its own `checkpoint_id` lineage.

```typescript
// Create fork: apply new state on top of a historical checkpoint
const forkedConfig = await app.updateState(
  { configurable: { thread_id: "user-123", checkpoint_id: "1ef4f..." } },
  { messages: [{ role: "user", content: "Different path" }] },
  "__copy__"    // Internal signal to start a new branch
);

// Continue on the forked branch
await app.invoke(null, forkedConfig);
```

The original thread (`checkpoint_id: "1ef4f..."`) is unmodified. The fork produces a new independent checkpoint lineage.

### getState with Specific checkpoint_id

```typescript
const historicalState = await app.getState({
  configurable: {
    thread_id: "user-123",
    checkpoint_id: "01HZYX...",
  },
});
// Returns exact snapshot — no pending writes applied
```

---

## Interrupt and Resume

### interrupt() — Pause Execution

```typescript
import { interrupt, Command } from "@langchain/langgraph";

const humanReview = async (state: typeof State.State) => {
  // Pauses graph; surfaces payload to caller under result.__interrupt__
  const decision = interrupt({
    question: "Approve this action?",
    details: state.actionDetails,
  });
  // `decision` holds the resume value when execution continues

  if (decision === "approved") {
    return new Command({ goto: "executeAction" });
  }
  return new Command({ goto: END });
};
```

**Rules — violating any of these causes silent bugs:**
1. Never wrap `interrupt()` in `try/catch` — it throws a special internal exception.
2. Never reorder or conditionally skip `interrupt()` calls — order is index-based and must be deterministic on resume.
3. Payload must be JSON-serializable — no functions or class instances.
4. Side effects before `interrupt()` must be idempotent — the node re-executes from the start on resume.
5. A checkpointer must be configured at compile time — `interrupt()` without persistence will throw.

### Resume with Command

```typescript
// First invocation — pauses at interrupt
const result1 = await app.invoke(input, config);
// result1.__interrupt__ contains the interrupt payload

// Resume — always use new Command({ resume: value }), never a plain object
const result2 = await app.invoke(new Command({ resume: "approved" }), config);
```

### Multiple Parallel Interrupts

```typescript
// When multiple nodes interrupt simultaneously, resume with a map keyed by interrupt ID
const result = await app.invoke(
  new Command({
    resume: {
      "interrupt-id-abc": "yes",
      "interrupt-id-xyz": "no",
    },
  }),
  config
);
```

### Static Debug Interrupts

```typescript
const app = graph.compile({
  checkpointer: new MemorySaver(),
  interruptBefore: ["nodeA"],   // Pause before nodeA executes
  interruptAfter: ["nodeB"],    // Pause after nodeB executes
});
```

---

## Functional API

### Overview

The Functional API (`entrypoint` + `task`) uses regular TypeScript control flow and checkpoints at the `entrypoint` boundary rather than per super-step.

### entrypoint

```typescript
function entrypoint<InputT, OutputT>(
  optionsOrName: string | EntrypointOptions,
  func: EntrypointFunc<InputT, OutputT>
): EntrypointWorkflow<InputT, OutputT>

interface EntrypointOptions {
  name?: string;
  checkpointer?: BaseCheckpointSaver;
}

type EntrypointFunc<InputT, OutputT> = (
  input: InputT,
  config?: LangGraphRunnableConfig
) => Promise<OutputT> | OutputT;

interface EntrypointWorkflow<InputT, OutputT> {
  invoke(input: InputT | Command, config?: LangGraphRunnableConfig): Promise<OutputT>;
  stream(input: InputT | Command, options?: { streamMode?: StreamMode | StreamMode[]; configurable?: Record<string, any> }): AsyncIterable<[mode: StreamMode, chunk: any]>;
}
```

**Rules:**
- Input must be the first and only positional argument; use an object for multiple inputs.
- Input and output must be JSON-serializable when a checkpointer is enabled.
- Non-deterministic code (random, `Date.now()`) must live inside `task()`.

### task

```typescript
function task<ArgsT extends unknown[], OutputT>(
  optionsOrName: string | TaskOptions,
  func: TaskFunc<ArgsT, OutputT>
): (...args: ArgsT) => Promise<OutputT>

interface TaskOptions {
  name?: string;
  retry?: { maxAttempts: number; [key: string]: any };
  cache?: CachePolicy;
}
```

- Can only be called from within an `entrypoint`, another `task`, or a `StateGraph` node.
- Task outputs are automatically persisted to the calling `entrypoint`'s checkpoint.
- Returns a `Promise`; enables parallel execution with `Promise.all()`.

### getPreviousState

```typescript
function getPreviousState<StateT>(): StateT | undefined
```

Returns the state value saved by `entrypoint.final` (or the last return value) from the **previous invocation** on the same `thread_id`. Returns `undefined` on first invocation.

### entrypoint.final

```typescript
entrypoint.final<ValueT, SaveT>(obj: {
  value: ValueT;  // Returned to the caller
  save: SaveT;    // Persisted to checkpoint; read next time via getPreviousState()
}): ValueT
```

Decouples what is returned to the caller from what is saved in the checkpoint.

### Complete Functional API Example

```typescript
import {
  entrypoint, task, interrupt, getPreviousState, Command,
  MemorySaver,
} from "@langchain/langgraph";

const generateContent = task(
  { name: "generate", retry: { maxAttempts: 3 } },
  async (topic: string): Promise<string> => {
    return `Generated content about ${topic}`;
  }
);

const refineContent = task(
  { name: "refine", cache: { ttl: 300 } },
  async (content: string): Promise<string> => {
    return `Refined: ${content}`;
  }
);

const contentWorkflow = entrypoint(
  { name: "contentWorkflow", checkpointer: new MemorySaver() },
  async (topic: string) => {
    // Read state from previous invocation on this thread
    const previous = getPreviousState<{ draft: string }>();

    // Parallel execution
    const [content, altContent] = await Promise.all([
      generateContent(topic),
      generateContent(`${topic} alternative`),
    ]);

    const draft = await refineContent(content);

    // Human-in-the-loop
    const feedback = interrupt({ question: "Review this draft", draft });

    if (feedback === "reject") {
      const revised = await refineContent(altContent);
      return entrypoint.final({
        value: { approved: false, content: revised },
        save: { draft: revised },
      });
    }

    return entrypoint.final({
      value: { approved: true, content: draft },
      save: { draft },
    });
  }
);

const config = { configurable: { thread_id: "topic-thread-1" } };

// First run — pauses at interrupt
const result1 = await contentWorkflow.invoke("machine learning", config);

// Resume after human review
const result2 = await contentWorkflow.invoke(
  new Command({ resume: "approve" }),
  config
);

// Next run — getPreviousState() returns { draft: "..." }
const result3 = await contentWorkflow.invoke("deep learning", config);
```

---

## Graph API vs Functional API Comparison

| Dimension | Graph API (`StateGraph`) | Functional API (`entrypoint`) |
|---|---|---|
| Style | Declarative graph structure | Imperative procedural code |
| Control flow | `addEdge`, `addConditionalEdges`, `Command` | `if`, `for`, `await`, function calls |
| State | Explicit schema with reducers; shared across all nodes | Scoped to each `entrypoint`; not shared |
| Checkpointing | New checkpoint after every super-step | One checkpoint per `entrypoint` execution |
| Visualization | `getGraphAsync()`, `drawMermaidPng()` | No built-in visualization |
| Time-travel granularity | Per super-step (fine-grained) | Per entrypoint boundary (coarse) |
| Parallel execution | Declarative via multiple edges | `Promise.all()` inside entrypoint |
| Subgraph composition | Compile subgraph, add as node | Nest `entrypoint` calls |
| Best for | Complex agents, branching, multi-actor, human-in-loop | Sequential chains, prototyping, simple pipelines |

**Decision rule:** use Graph API when you need explicit branching, parallel execution, reusable subgraphs, or visualization. Use Functional API when standard language control flow is more readable and you do not need per-node checkpointing.

---

## Production Deployment Pattern

```typescript
import { StateGraph } from "@langchain/langgraph";
import { PostgresSaver } from "@langchain/langgraph-checkpoint-postgres";
import { PostgresStore } from "@langchain/langgraph-checkpoint-postgres/store";

// Same Postgres cluster; separate tables
const checkpointer = PostgresSaver.fromConnString(process.env.DATABASE_URL!, {
  schema: "langgraph",
});
await checkpointer.setup();  // Run once; idempotent

const store = PostgresStore.fromConnString(process.env.DATABASE_URL!, {
  schema: "public",
});
await store.setup();

const graph = new StateGraph(StateSchema).compile({
  checkpointer,
  store,
});
```

**Pre-production checklist:**
- `thread_id` is always present in every invocation config.
- Checkpointer backend is a durable store (not `MemorySaver`).
- `PostgresSaver.setup()` has been run on the target schema.
- Store backend is persistent if long-term memory matters.
- All tasks with external side effects use idempotency keys.
- Checkpoint history retention policy is understood and handled.
- Large message growth is controlled (use `UntrackedValue` for transient data, trim messages periodically).
- Test coverage includes failure/resume behavior.

---

## Known Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| Missing `thread_id` in config | State not persisted; each call starts fresh | Always pass `configurable: { thread_id }` when using a checkpointer |
| `MemorySaver` in production | State lost on restart or across processes | Use `PostgresSaver`, `RedisSaver`, or `SqliteSaver` depending on deployment |
| Forgetting `await checkpointer.setup()` | `PostgresSaver` throws on first use (missing tables) | Call `setup()` once at application startup, before any graph invocations |
| Graph compiled on every request | Memory leak; increased latency | Compile once at module load, reuse the `CompiledStateGraph` instance |
| `recursionLimit` too low for multi-hop agents | `GraphRecursionError` thrown mid-workflow | Increase `recursionLimit` in invoke config or add explicit termination conditions |
| Non-deterministic code outside `task()` | Different result on replay; resume produces wrong branch | Wrap random, `Date.now()`, and mutable external fetches in `task()` |
| Resuming with plain object instead of `Command` | Resume value ignored; graph re-runs from start | Always use `new Command({ resume: value })`; plain objects are treated as new input |
| Side effects in node without idempotency key | Duplicate charges, emails, or records under retry | Add idempotency keys to all external writes; wrap in `task()` in Functional API |
| Wrapping `interrupt()` in `try/catch` | Interrupt exception swallowed; graph hangs or errors | Never catch the `interrupt()` throw; it is an internal control signal |
| Zod v4 in `StateSchema` | TypeScript errors; runtime schema parse failures | Stay on Zod v3; `StateSchema` is not compatible with Zod v4 |
| Large state objects checkpointed every super-step | High storage cost; slow serialization | Mark transient fields with `UntrackedValue`; they are never checkpointed |
| Using `ShallowRedisSaver` when history is needed | `getStateHistory()` returns only one entry; time-travel fails | Use full `RedisSaver` when history or fork/replay functionality is required |
| `"exit"` durability mode with crash-sensitive workflows | Only final checkpoint saved; partial progress lost on crash | Use `"async"` (default) or `"sync"` for workflows that need intermediate crash recovery |
| Calling `task()` outside of `entrypoint` or another task | Runtime error: task invoked in wrong context | Only call tasks from within an `entrypoint` function body or another task |
| `checkpoint_ns` treated as a user-visible tag | Subgraph checkpoint isolation breaks; namespaces collide | Let the runtime manage `checkpoint_ns`; do not fabricate values for subgraph flows |
