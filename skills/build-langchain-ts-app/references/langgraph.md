# LangGraph.js Reference

> `@langchain/langgraph` v1.2.x · `@langchain/core` v1.1.x · TypeScript only.
> Verified against official docs and GitHub source, 2026-03-23.

---

## 1. Installation & Packages

```bash
# Minimum
npm install @langchain/langgraph @langchain/core

# With Anthropic LLM
npm install @langchain/langgraph @langchain/core @langchain/anthropic

# Scaffold a full project (Next.js or Vite, 4 prebuilt agents)
npx create-agent-chat-app@latest

# CLI tooling
npm install --save-dev @langchain/langgraph-cli
npx @langchain/langgraph-cli dev   # in-memory dev server with hot-reload
```

**Checkpoint adapters (persistence):**

| Package | Backend |
|---|---|
| `@langchain/langgraph-checkpoint` | `MemorySaver` (in-process) |
| `@langchain/langgraph-checkpoint-sqlite` | SQLite |
| `@langchain/langgraph-checkpoint-postgres` | PostgreSQL |
| `@langchain/langgraph-checkpoint-mongodb` | MongoDB |

**Prebuilt multi-agent packages:**

| Package | Purpose |
|---|---|
| `@langchain/langgraph-supervisor` | Supervisor multi-agent architecture |
| `@langchain/langgraph-swarm` | Swarm multi-agent architecture |
| `@langchain/langgraph-sdk` | Programmatic API client for deployed graphs |

**Core imports:**

```ts
import {
  StateGraph, StateSchema, ReducedValue, MessagesValue, UntrackedValue,
  Annotation, MessagesAnnotation,
  GraphNode, ConditionalEdgeRouter,
  Command, Send, START, END,
  interrupt, entrypoint, task, getPreviousState,
  MemorySaver, InMemoryStore,
  GraphRecursionError,
} from "@langchain/langgraph";

import { ToolNode } from "@langchain/langgraph/prebuilt";
```

---

## 2. State Schema

State is the shared snapshot all nodes read from and write to. `StateSchema` (Zod-based, recommended) and `Annotation.Root` (legacy) both work.

### 2.1 StateSchema — Four Channel Types

```ts
import { StateSchema, ReducedValue, MessagesValue, UntrackedValue } from "@langchain/langgraph";
import { z } from "zod";

const AgentState = new StateSchema({
  // 1. LastValue — Zod schema, last write wins
  currentStep: z.string(),
  retryCount: z.number().default(0),

  // 2. ReducedValue — custom reducer merges concurrent writes
  allResults: new ReducedValue(
    z.array(z.string()).default(() => []),
    { reducer: (cur, nxt) => [...cur, nxt] }
  ),

  // 3. MessagesValue — append/update/delete BaseMessage[] by ID
  messages: MessagesValue,

  // 4. UntrackedValue — never checkpointed (DB handles, caches)
  tempCache: new UntrackedValue(z.record(z.string(), z.unknown())),
});

// Derive TypeScript types
type State  = typeof AgentState.State;   // full snapshot
type Update = typeof AgentState.Update;  // partial update
```

| Channel Type | Behaviour | Use Case |
|---|---|---|
| `z.*` (Zod) | Newest write wins | Scalar fields, simple objects |
| `ReducedValue` | Custom reducer merges all writes in a superstep | Aggregating lists, counters |
| `MessagesValue` | Appends new messages; updates existing by ID | Chat history |
| `UntrackedValue` | Excluded from serialisation and checkpoints | Runtime handles, sockets |

### 2.2 Annotation.Root (Legacy / Alternative)

```ts
import { Annotation, MessagesAnnotation } from "@langchain/langgraph";
import { BaseMessage } from "@langchain/core/messages";

const State = Annotation.Root({
  messages: Annotation<BaseMessage[]>({
    reducer: (left, right) => left.concat(Array.isArray(right) ? right : [right]),
    default: () => [],
  }),
  step: Annotation<string>({ reducer: (_, n) => n, default: () => "start" }),
});

// Pre-built shortcut for { messages: BaseMessage[] } only
const graph = new StateGraph(MessagesAnnotation);
```

### 2.3 Multi-Schema (Input / Output / Internal)

```ts
const graph = new StateGraph({
  state:  InternalState,   // all fields, used inside nodes
  input:  InputSchema,     // what callers pass on invoke
  output: OutputSchema,    // what callers receive on completion
});
```

### 2.4 Runtime Context (non-state config)

Pass per-invocation values (LLM choice, user ID) without polluting state:

```ts
const ContextSchema = z.object({ llm: z.enum(["openai", "anthropic"]) });
const graph = new StateGraph(AgentState, ContextSchema);

// Access inside a node
const myNode = async (state: typeof AgentState.State, config: LangGraphRunnableConfig) => {
  const { llm } = config.context!;
};

await graph.compile().invoke(inputs, { context: { llm: "anthropic" } });
```

---

## 3. Graph API

### 3.1 StateGraph Class — `addNode`

```ts
// Single node (most common)
graph.addNode("myNode", asyncFn, options?)

// Multiple nodes at once
graph.addNode([["nodeA", fnA], ["nodeB", fnB, { retryPolicy: { maxAttempts: 3 } }]])
graph.addNode({ nodeA: fnA, nodeB: fnB })
```

**`StateGraphAddNodeOptions`:**

```ts
interface StateGraphAddNodeOptions {
  retryPolicy?: {
    maxAttempts?: number;               // default: 3
    initialInterval?: number;           // ms; default: 500
    maxInterval?: number;               // ms; default: 128_000
    backoffFactor?: number;             // default: 2 (exponential)
    retryOn?: (err: Error) => boolean;  // default: retry all except TypeError/SyntaxError
  };
  cachePolicy?: {
    ttl?: number;                       // seconds; 0 = no expiry
    keyFunc?: (state: S) => string;     // custom cache key
  };
  ends?: string[];   // declare allowed Command.goto destinations (required for routing validation)
  input?: ZodSchema; // private node-level input schema
}
```

**Node function signature:**

```ts
type GraphNode<S, C = LangGraphRunnableConfig> = (
  state: S,
  config?: C
) => Partial<S> | Command | Promise<Partial<S> | Command>;

// Shorthand via schema
const myNode: typeof AgentState.Node = async (state) => ({ currentStep: "done" });
```

### 3.2 `addEdge` and `addConditionalEdges`

```ts
// Fixed edges
graph.addEdge(START, "firstNode");
graph.addEdge("nodeA", "nodeB");
graph.addEdge("lastNode", END);
graph.addEdge(["branchA", "branchB"], "collector"); // fan-in

// Conditional edge
const router: ConditionalEdgeRouter<typeof State, "toolNode"> = (state) =>
  state.messages.at(-1)?.tool_calls?.length ? "toolNode" : END;

graph.addConditionalEdges("llmCall", router, ["toolNode", END]);

// With named map
graph.addConditionalEdges("classify", classifyFn, {
  positive: "handlePositive",
  negative: "handleNegative",
  neutral: END,
});
```

**Router return types accepted by `addConditionalEdges`:**
- `string` — name of next node
- `string[]` — parallel execution of multiple nodes
- `END` — terminate graph
- `Send` — dynamic node with custom payload
- `Send[]` — map-reduce fan-out

### 3.3 `compile`

```ts
const app = graph.compile({
  checkpointer: new MemorySaver(),      // enables persistence, HITL, time-travel
  store: new InMemoryStore(),           // long-term cross-thread memory
  cache: new InMemoryCache(),           // node-level output cache
  interruptBefore: ["humanReview"],     // pause before node (debugging / HITL)
  interruptAfter: ["llmCall"],          // pause after node
  name: "my-agent",                     // identifies graph in registries
});
```

Compile once and reuse — compiling large graphs takes ~20 s on first call. Never compile per-request.

---

## 4. `Command` Class

`Command` returns both a state update and routing in one object. Use it when a node must decide its own next step.

```ts
import { Command } from "@langchain/langgraph";

new Command({
  update?: Partial<State> | [string, unknown][];  // state delta
  goto?:  string | Send | (string | Send)[];       // next node(s)
  graph?: string;                                  // "PARENT" = escape to parent graph
  resume?: any;                                    // resume value for interrupt()
})

Command.PARENT  // static constant = "PARENT"
```

**Four contexts where `Command` is used:**

```ts
// 1. Node returning update + routing together
const classifyNode = async (state: State) => {
  const cls = await classify(state.text);
  return new Command({
    update: { classification: cls },
    goto: cls === "billing" ? "humanReview" : "draftResponse",
  });
};
// Register with ends declaration:
graph.addNode("classify", classifyNode, { ends: ["humanReview", "draftResponse"] });

// 2. Subgraph node escaping to parent graph
const subgraphNode = async (state: SubState) =>
  new Command({ update: { result: "done" }, goto: "parentNode", graph: Command.PARENT });

// 3. Pass to invoke/stream to resume an interrupted graph
await app.invoke(
  new Command({ resume: { approved: true } }),
  { configurable: { thread_id: "t-1" } }
);

// 4. Fan-out: multiple Send targets
const fanOut = (state: State) =>
  new Command({ goto: [new Send("worker", { task: state.t1 }), new Send("worker", { task: state.t2 })] });
```

---

## 5. `Send` Class — Map-Reduce

`Send` dynamically dispatches a node with a custom payload instead of passing the whole graph state.

```ts
new Send(
  node: string,  // target node name
  args: any      // payload sent to that node invocation
)
```

**Map-reduce pattern:**

```ts
import { Annotation, StateGraph, Send, START, END } from "@langchain/langgraph";

const MapReduceState = Annotation.Root({
  subjects: Annotation<string[]>({ reducer: (_, n) => n, default: () => [] }),
  jokes: Annotation<string[]>({
    reducer: (left, right) => left.concat(Array.isArray(right) ? right : [right]),
    default: () => [],
  }),
});

// Router returns one Send per subject → all run in parallel
const fanOut = (state: typeof MapReduceState.State): Send[] =>
  state.subjects.map(subject => new Send("generateJoke", { subject }));

// Worker receives sub-state { subject: string }, NOT full parent state
const generateJoke = async (state: { subject: string }) => ({
  jokes: [`Why did the ${state.subject} cross the road?`],
});

const app = new StateGraph(MapReduceState)
  .addNode("generateTopics", () => ({ subjects: ["cats", "dogs", "rabbits"] }))
  .addNode("generateJoke", generateJoke)
  .addNode("bestJoke", (state) => { console.log("All jokes:", state.jokes); return {}; })
  .addEdge(START, "generateTopics")
  .addConditionalEdges("generateTopics", fanOut)
  .addEdge("generateJoke", "bestJoke")
  .addEdge("bestJoke", END)
  .compile();
```

---

## 6. `CompiledStateGraph` Execution Methods

### 6.1 `invoke` and `stream`

```ts
// invoke — returns full output state
const result = await app.invoke(
  { messages: [new HumanMessage("Hello")] },
  { configurable: { thread_id: "user-123" }, recursionLimit: 25 }
);

// stream — returns async iterator
for await (const chunk of await app.stream(input, {
  streamMode: "updates",  // or "values" | "messages" | "custom" | "tools" | "debug"
  subgraphs: true,        // include events from subgraphs
  configurable: { thread_id: "user-123" },
})) {
  console.log(chunk);
}

// Multiple stream modes simultaneously → yields [mode, chunk] tuples
for await (const [mode, chunk] of await app.stream(input, {
  streamMode: ["updates", "custom"],
})) { /* ... */ }
```

**Stream modes:**

| Mode | Yields | Best for |
|---|---|---|
| `"updates"` | `{ nodeName: partialState }` delta after each node | Low-latency step tracking |
| `"values"` | Full state after each superstep | Full state inspection |
| `"messages"` | `[LLM token, metadata]` tuples from LLM calls | Real-time token streaming |
| `"custom"` | User-defined data via `config.writer?.()` | Custom progress events |
| `"tools"` | Tool lifecycle events (`on_tool_start` etc.) | Tool execution observability |
| `"debug"` | All execution info including full state | Deep debugging |

Emit custom data from a node:

```ts
const myNode = async (state: State, config: LangGraphRunnableConfig) => {
  config.writer?.({ progress: 50, message: "halfway done" });
  return { result: "done" };
};
```

### 6.2 `getState`, `updateState`, `getStateHistory`

```ts
// Current state snapshot
const snapshot = await app.getState({ configurable: { thread_id: "user-123" } });
// snapshot.values — current state
// snapshot.next   — next nodes to execute
// snapshot.tasks  — pending tasks (with .state if subgraphs: true)

// Include subgraph states
const state = await app.getState(config, { subgraphs: true });
const subgraphState = state.tasks[0].state;

// Manually patch state (HITL — human edits a field)
await app.updateState(config, { messages: [new HumanMessage("Override")] });
// Attribute update to a specific node's reducers
await app.updateState(config, { step: "reviewed" }, "humanReview");

// Iterate all checkpoints for a thread (time-travel)
for await (const snapshot of app.getStateHistory({ configurable: { thread_id: "user-123" } })) {
  console.log(snapshot.metadata.step, snapshot.values);
}
// Resume from a specific historical checkpoint
const result = await app.invoke(null, targetSnapshot.config);
```

### 6.3 `batch`, `withConfig`, `asTool`

```ts
// Batch multiple inputs
const results = await app.batch([
  { messages: [new HumanMessage("q1")] },
  { messages: [new HumanMessage("q2")] },
]);

// Pre-bind config
const boundApp = app.withConfig({ metadata: { project: "prod" } });

// Expose compiled graph as a LangChain tool (for agent-in-agent patterns)
const graphTool = app.asTool({
  name: "research_agent",
  description: "Runs the research agent",
  schema: z.object({ query: z.string() }),
});
```

### 6.4 Visualization

```ts
const mermaid = (await app.getGraphAsync()).drawMermaid();
// Include subgraph internals with xray
const deep = app.getGraph({ xray: 1 }).drawMermaid();
```

---

## 7. `interrupt()` Function

```ts
function interrupt<T = any>(payload: T): T
```

Pauses graph execution. The payload surfaces to the caller under `result.__interrupt__`. The resume value (passed via `Command({ resume: value })`) becomes the return value of `interrupt()` when the node re-runs.

**Requires a checkpointer at compile time.**

**5 rules — violating any causes silent bugs or crashes:**

1. **Never wrap in `try/catch`** — it throws a special internal signal exception.
2. **Never place conditionally or reorder** — the position is index-based; order must be deterministic on resume.
3. **Payload must be JSON-serializable** — no functions, class instances, or circular refs.
4. **Side effects before `interrupt` must be idempotent** — the node re-executes from the beginning on resume.
5. **Subgraph's parent node re-runs** on resume after a subgraph interrupt — design accordingly.

```ts
import { interrupt, Command } from "@langchain/langgraph";

const humanReview = async (state: typeof State.State) => {
  // Pause; caller receives { question, details } under __interrupt__
  const decision = interrupt({ question: "Approve this action?", details: state.action });

  if (decision === "approved") return new Command({ goto: "execute" });
  return new Command({ goto: END });
};

// Start (pauses at interrupt)
const r1 = await app.invoke({ input: "data" }, { configurable: { thread_id: "t-1" } });
// r1.__interrupt__ → [{ value: { question: "...", details: "..." }, resumable: true }]

// Resume
const r2 = await app.invoke(
  new Command({ resume: "approved" }),
  { configurable: { thread_id: "t-1" } }
);

// Multiple parallel interrupts — resume with a map keyed by interrupt ID
await app.invoke(new Command({ resume: { "interrupt-id-abc": "yes", "interrupt-id-xyz": "no" } }), config);
```

**Static interrupts (debugging):**

```ts
graph.compile({ checkpointer: new MemorySaver(), interruptBefore: ["nodeA"], interruptAfter: ["nodeB"] });
```

---

## 8. START / END Constants

```ts
import { START, END } from "@langchain/langgraph";
// START = "__start__", END = "__end__"

graph.addEdge(START, "firstNode");
graph.addEdge("lastNode", END);

// In conditional router
const router = (state: State): string => done ? END : "nextNode";
```

---

## 9. Functional API

An alternative to `StateGraph` using regular async functions plus two decorators. Best for linear workflows and prototyping.

### 9.1 Primitives

| Primitive | Signature | Description |
|---|---|---|
| `entrypoint(opts, fn)` | `(config: { name?, checkpointer? }, fn) => Workflow` | Creates a resumable, checkpointed workflow |
| `task(name, fn)` | `(name, fn) => TaskFn` | Wraps a function as a checkpointed unit; must be called inside entrypoint/task |
| `interrupt(payload)` | `(payload) => any` | Pauses and returns resume value (same rules as Graph API) |
| `getPreviousState<T>()` | `() => T \| undefined` | Returns saved return value from previous invocation on same thread |
| `entrypoint.final` | `entrypoint.final({ value, save })` | Decouples return value from persisted checkpoint value |

### 9.2 Complete Example

```ts
import { entrypoint, task, interrupt, getPreviousState, Command, MemorySaver } from "@langchain/langgraph";
import { v4 as uuidv4 } from "uuid";

// Reusable tasks with retry + cache options
const generateContent = task(
  { name: "generate", retry: { maxAttempts: 3 } },
  async (topic: string): Promise<string> => `Draft content about ${topic}`
);

const refineContent = task(
  { name: "refine", cache: { ttl: 300 } },
  async (content: string): Promise<string> => `Refined: ${content}`
);

// Entrypoint = the workflow
const contentWorkflow = entrypoint(
  { name: "contentWorkflow", checkpointer: new MemorySaver() },
  async (topic: string) => {
    const previous = getPreviousState<{ draft: string }>();

    // Parallel execution
    const [content, alt] = await Promise.all([
      generateContent(topic),
      generateContent(`${topic} (alternative)`),
    ]);

    const draft = await refineContent(content);

    // Pause for human feedback
    const feedback: string = interrupt({ question: "Review draft", draft });

    const final = feedback === "reject" ? await refineContent(alt) : draft;

    return entrypoint.final({
      value: { approved: true, content: final },
      save: { draft: final },  // stored in checkpoint; read by getPreviousState next time
    });
  }
);

const config = { configurable: { thread_id: uuidv4() } };

// First run — pauses at interrupt
for await (const chunk of contentWorkflow.stream("machine learning", config)) {
  console.log(chunk);
}

// Resume after human review
for await (const chunk of contentWorkflow.stream(new Command({ resume: "approve" }), config)) {
  console.log(chunk);
}
```

### 9.3 Graph API vs Functional API

| Aspect | Graph API (`StateGraph`) | Functional API (`entrypoint` / `task`) |
|---|---|---|
| Control flow | Declarative: nodes, edges, routing | Imperative: `if`, `for`, `await` |
| State scope | Shared `StateSchema` across all nodes | Scoped to each entrypoint |
| Visualization | Built-in graph view | None |
| Checkpoints | One per superstep (fine-grained) | One per entrypoint call (coarser) |
| Time travel | Node-level replay | Entrypoint-boundary replay only |
| Parallelism | Native fan-out via multiple edges | Manual `Promise.all()` |
| Boilerplate | Schema + node registration + edges | Near-zero; add decorators |
| Best for | Complex multi-agent, sub-graphs, HITL | Linear pipelines, prototyping |

Both can be mixed: a graph node can call a functional entrypoint, and an entrypoint can launch a `StateGraph` subgraph.

---

## 10. Subgraphs

A compiled `StateGraph` used as a node inside another graph.

### Pattern 1: Shared State Keys (Direct Node)

When parent and subgraph share at least one state key, add the compiled subgraph directly:

```ts
const SharedState = new StateSchema({ foo: z.string() });

const childSubgraph = new StateGraph(SharedState)
  .addNode("process", (s) => ({ foo: "processed: " + s.foo }))
  .addEdge(START, "process").addEdge("process", END)
  .compile();

const parentGraph = new StateGraph(SharedState)
  .addNode("child", childSubgraph)  // direct — no wrapper needed
  .addEdge(START, "child").addEdge("child", END)
  .compile();
```

State flows through unchanged; subgraph updates merge back into parent automatically.

### Pattern 2: Different Schemas (Wrapper Node)

When schemas differ, transform state in a wrapper node:

```ts
const ParentState = new StateSchema({ foo: z.string() });
const ChildState  = new StateSchema({ bar: z.string() });

const childSubgraph = new StateGraph(ChildState)
  .addNode("work", (s) => ({ bar: "done: " + s.bar }))
  .addEdge(START, "work").addEdge("work", END)
  .compile();

const parentGraph = new StateGraph(ParentState)
  .addNode("wrapperNode", async (parentState) => {
    const out = await childSubgraph.invoke({ bar: parentState.foo });  // map in
    return { foo: out.bar };                                            // map out
  })
  .addEdge(START, "wrapperNode").addEdge("wrapperNode", END)
  .compile();
```

### Persistence Modes

```ts
builder.compile()                         // per-invocation (default): fresh state each call
builder.compile({ checkpointer: null })   // same as above
builder.compile({ checkpointer: true })   // per-thread: accumulates per thread_id
builder.compile({ checkpointer: false })  // stateless: no checkpointing
builder.compile({ checkpointer: new MemorySaver() }) // custom saver
```

When the **parent** is compiled with a checkpointer it **propagates** to all child subgraphs automatically (unless child explicitly sets `false`).

### Viewing Subgraph State

```ts
const state = await parentGraph.getState(config, { subgraphs: true });
const subgraphState = state.tasks[0].state;
```

Each nesting level gets its own checkpoint namespace — no manual namespace management needed.

### `Command.PARENT` — Subgraph Escaping to Parent

```ts
const subgraphNode = async (state: SubState) =>
  new Command({ update: { result: "done" }, goto: "parentNode", graph: Command.PARENT });
```

### RemoteGraph (Distributed Subgraphs)

```ts
import { RemoteGraph } from "@langchain/langgraph";

const remoteAgent = new RemoteGraph({
  graphId: "research_agent",
  url: process.env.LANGGRAPH_API_URL!,
  apiKey: process.env.LANGSMITH_API_KEY,
});

// Use like a local subgraph
parentGraph.addNode("research", remoteAgent);
```

Do not use `RemoteGraph` to call a graph within the **same deployment** — causes deadlocks.

---

## 11. Application Structure

### Single App

```
my-app/
├── src/
│   ├── agent.ts              # Graph construction + export (app = graph.compile())
│   └── utils/
│       ├── state.ts          # StateSchema / Annotation.Root definitions
│       ├── nodes.ts          # Node function implementations
│       └── tools.ts          # Tool definitions
├── langgraph.json            # Deployment descriptor
├── tsconfig.json
└── .env
```

### Subgraph Layout

```
my-app/src/
├── graphs/
│   ├── parentGraph.ts
│   └── subgraphs/
│       ├── researchAgent.ts
│       ├── writerAgent.ts
│       └── reviewAgent.ts
├── types/
│   └── stateSchemas.ts       # All StateSchema exports
├── nodes/
│   ├── shared.ts
│   └── supervisor.ts
└── tools/
```

### `langgraph.json`

```json
{
  "node_version": "24",
  "dependencies": ["."],
  "graphs": {
    "agent": "./src/agent.ts:app",
    "research": "./src/graphs/researchAgent.ts:researchGraph"
  },
  "env": ".env"
}
```

| Field | Required | Description |
|---|---|---|
| `node_version` | Recommended | Node.js version for the runtime |
| `dependencies` | Yes | Paths to install (use `[".", "../../shared"]` in monorepos) |
| `graphs` | Yes | `"name": "./path/to/file.ts:exportedVar"` |
| `env` | No | Path to `.env` file or inline `{ "KEY": "value" }` object |
| `dockerfile_lines` | No | Additional Dockerfile instructions |

### Monorepo Layout

```
my-monorepo/
├── apps/
│   ├── agent1/
│   │   ├── src/graph.ts
│   │   ├── langgraph.json    # per-agent config
│   │   └── package.json
│   └── agent2/
│       └── ...
├── libs/
│   └── shared/
│       └── src/index.ts      # exported shared utilities
├── package.json              # workspaces: ["apps/*", "libs/*"]
└── turbo.json
```

Per-agent `langgraph.json` references shared lib:

```json
{
  "dependencies": [".", "../../libs/shared"],
  "graphs": { "agent1": "./src/graph.ts:graph" }
}
```

---

## 12. Graph Factory & Module Patterns

### Factory Function (Parameterized Graph)

```ts
// src/graphs/researchAgent.ts
interface ResearchAgentConfig { model?: string; maxSources?: number; }

export function createResearchAgent(config: ResearchAgentConfig = {}) {
  const llm = new ChatOpenAI({ model: config.model ?? "gpt-4o" });
  const graph = new StateGraph(ResearchState)
    .addNode("research", async (state) => ({ sources: [] }))
    .addEdge(START, "research").addEdge("research", END);
  return graph.compile();
}

export const researchAgent = createResearchAgent();
```

### Graph Registry (Lazy Initialization)

```ts
const registry = new Map<string, CompiledStateGraph<any>>();

function getGraph(name: "research" | "writer" | "review") {
  if (!registry.has(name)) {
    registry.set(name, name === "research" ? createResearchAgent()
      : name === "writer" ? createWriterAgent() : createReviewAgent());
  }
  return registry.get(name)!;
}
```

### Dynamic Module Loading

```ts
const graphCache = new Map<string, CompiledStateGraph<any>>();

export async function loadGraph(graphId: string) {
  if (graphCache.has(graphId)) return graphCache.get(graphId)!;
  const module = await import(`../graphs/${graphId}`);
  const graph = module.default ?? module.graph ?? module.app;
  if (!graph) throw new Error(`Graph "${graphId}" not found`);
  graphCache.set(graphId, graph);
  return graph;
}
```

---

## 13. API Layer Integration

### Fastify (Recommended for Production)

```ts
import fastify from "fastify";
import { Command } from "@langchain/langgraph";
import { PostgresSaver } from "@langchain/langgraph-checkpoint-postgres";

const server = fastify({ logger: true });
const checkpointer = process.env.DATABASE_URL
  ? await PostgresSaver.fromConnString(process.env.DATABASE_URL)
  : new MemorySaver();

const graphs = { agent: createAgent({ checkpointer }) };

// Invoke
server.post("/:app/invoke", async (req, reply) => {
  const { messages, thread_id } = req.body as any;
  const result = await graphs[req.params.app].invoke(
    { messages },
    thread_id ? { configurable: { thread_id } } : undefined
  );
  return reply.send(result);
});

// Streaming (Server-Sent Events)
server.post("/:app/stream", async (req, reply) => {
  reply.raw.writeHead(200, { "Content-Type": "text/event-stream", "Cache-Control": "no-cache" });
  const stream = await graphs[req.params.app].stream(req.body as any);
  for await (const chunk of stream) reply.raw.write(`data: ${JSON.stringify(chunk)}\n\n`);
  reply.raw.end();
});

// Resume after interrupt
server.post("/:app/resume", async (req, reply) => {
  const { thread_id, decision } = req.body as any;
  const result = await graphs[req.params.app].invoke(
    new Command({ resume: decision }),
    { configurable: { thread_id } }
  );
  return reply.send(result);
});

await server.listen({ port: Number(process.env.PORT) || 3000 });
```

### Express

```ts
import express from "express";
const server = express();
server.use(express.json());

server.post("/invoke", async (req, res) => {
  const { input, thread_id } = req.body;
  const result = await graph.invoke(input, thread_id ? { configurable: { thread_id } } : undefined);
  res.json(result);
});
```

### Next.js (App Router — API Passthrough)

```ts
// src/app/api/[..._path]/route.ts
import { initApiPassthrough } from "@langchain/langgraph-api-passthrough";

const { GET, POST, PUT, PATCH, DELETE, OPTIONS, runtime } = initApiPassthrough({
  apiUrl: process.env.LANGGRAPH_API_URL,
  apiKey: process.env.LANGSMITH_API_KEY,
  headers: (req) => ({ Authorization: `Bearer ${process.env.INTERNAL_TOKEN}` }),
  bodyParameters: (req, body) => ({
    ...body,
    configurable: { ...body.configurable, userId: req.headers.get("x-user-id") },
  }),
});

export { GET, POST, PUT, PATCH, DELETE, OPTIONS, runtime };
```

---

## 14. Workflow Patterns

### Prompt Chaining (Sequential)

```ts
const State = new StateSchema({ topic: z.string(), joke: z.string(), improvedJoke: z.string() });

const chain = new StateGraph(State)
  .addNode("generate", async (s) => ({ joke: await llm.invoke(`Write joke about ${s.topic}`) }))
  .addNode("improve",  async (s) => ({ improvedJoke: await llm.invoke(`Improve: ${s.joke}`) }))
  .addEdge(START, "generate").addEdge("generate", "improve").addEdge("improve", END)
  .compile();
```

### LLM Routing

```ts
const router: ConditionalEdgeRouter<typeof State, "story" | "joke" | "poem"> = (state) =>
  state.decision === "story" ? "story" : state.decision === "joke" ? "joke" : "poem";

new StateGraph(State)
  .addNode("route", routerNode)
  .addNode("story", storyNode).addNode("joke", jokeNode).addNode("poem", poemNode)
  .addEdge(START, "route")
  .addConditionalEdges("route", router, ["story", "joke", "poem"])
  .addEdge("story", END).addEdge("joke", END).addEdge("poem", END)
  .compile();
```

### Evaluator-Optimizer Loop

```ts
new StateGraph(State)
  .addNode("generate", generatorNode)
  .addNode("evaluate", evaluatorNode)
  .addEdge(START, "generate")
  .addEdge("generate", "evaluate")
  .addConditionalEdges("evaluate",
    (state) => state.quality === "good" ? "Accepted" : "Feedback",
    { Accepted: END, Feedback: "generate" }
  )
  .compile();
```

### Quality Gate

```ts
.addConditionalEdges("generate",
  (state) => state.joke?.includes("?") ? "Pass" : "Fail",
  { Pass: "improve", Fail: END }
)
```

### Fan-Out / Fan-In (Parallel Nodes)

```ts
new StateGraph(State)
  .addNode("callLlm1", fn1).addNode("callLlm2", fn2).addNode("callLlm3", fn3)
  .addNode("aggregate", aggregateFn)
  .addEdge(START, "callLlm1").addEdge(START, "callLlm2").addEdge(START, "callLlm3")
  .addEdge(["callLlm1", "callLlm2", "callLlm3"], "aggregate")
  .addEdge("aggregate", END)
  .compile();
```

### Cycles (ReAct Loop)

```ts
new StateGraph(MessagesAnnotation)
  .addNode("llm", llmNode)
  .addNode("tools", new ToolNode(tools))
  .addEdge(START, "llm")
  .addConditionalEdges("llm",
    (state) => state.messages.at(-1)?.tool_calls?.length ? "tools" : END,
    ["tools", END]
  )
  .addEdge("tools", "llm")  // cycle back
  .compile();
```

---

## 15. Checkpointers & Long-Term Memory

```ts
// Development
const checkpointer = new MemorySaver();

// Production — PostgreSQL
import { PostgresSaver } from "@langchain/langgraph-checkpoint-postgres";
const checkpointer = await PostgresSaver.fromConnString(process.env.DATABASE_URL!);

// Environment-aware factory
function createCheckpointer() {
  if (process.env.DATABASE_URL) return PostgresSaver.fromConnString(process.env.DATABASE_URL);
  if (process.env.NODE_ENV === "test") return SqliteSaver.fromConnString(":memory:");
  return new MemorySaver();
}
```

Thread config keys:

```ts
{
  configurable: {
    thread_id: "user-session-id",    // primary isolation key
    checkpoint_ns: "subgraph-ns",    // for nested checkpoints (auto-managed)
    checkpoint_id: "abc123",         // resume from specific historical checkpoint
  }
}
```

**Long-term memory store** (cross-thread, cross-session):

```ts
const store = new InMemoryStore();
const app = graph.compile({ checkpointer, store });

// Inside a node
const myNode = async (state: State, config: LangGraphRunnableConfig) => {
  await config.store!.put(["users", userId], "profile", { name: "Alice" });
  const [profile] = await config.store!.get([["users", userId, "profile"]]);
  const results = await config.store!.search(["users", userId], { query: "preferences" });
  return { context: profile?.value };
};
```

---

## 16. Common Pitfalls

1. **Missing `ends` declaration.** When a node returns `Command({ goto: "x" })`, you must declare `ends: ["x"]` in `addNode` options. Omitting it causes a validation error at runtime.

2. **Compiling per-request.** Compile once at module load; reuse the instance. Large graphs take ~20 s to compile.

3. **No `ReducedValue` for parallel-write fields.** If multiple branches write the same state key concurrently, a plain Zod field keeps only one write. Use `ReducedValue` to merge all writes.

4. **`interrupt()` inside `try/catch`.** `interrupt()` throws internally. Wrapping it silences the signal and breaks human-in-the-loop.

5. **Non-deterministic code outside `task()`.** Any `Math.random()`, `Date.now()`, or external call not inside a `task()` (Functional API) or node (Graph API) re-executes on resume with a different result, corrupting state.

6. **`UntrackedValue` for serializable data.** Use `UntrackedValue` only for runtime handles. Storing serializable data there means it is lost on resume from checkpoint.

7. **`MemorySaver` in production.** `MemorySaver` is process-local and lost on restart. Always use `PostgresSaver` or another persistent checkpointer in production.

8. **Forgetting `thread_id` in config.** Without `configurable.thread_id`, calls on a checkpointed graph each start a new thread — no memory across turns.

9. **`RemoteGraph` calling itself.** Using `RemoteGraph` to call a graph in the same deployment causes deadlocks. Use local composition instead.

10. **Using `MessageGraph`.** `MessageGraph` is deprecated. Replace with `new StateGraph(new StateSchema({ messages: MessagesValue }))` or `new StateGraph(MessagesAnnotation)`.
