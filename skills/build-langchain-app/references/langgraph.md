# LangGraph.js Comprehensive Reference

> For `@langchain/langgraph@1.2.5`, `@langchain/core@1.1.34`, `@langchain/openai@1.3.0` — TypeScript only.
> All patterns verified against official docs and live tests (2026-03-21).

---

## 1. StateGraph: Core Abstraction

A `StateGraph` is a directed graph where nodes are async functions operating on shared state and edges define control flow.

### Constructor + MessagesAnnotation

The simplest graph uses `MessagesAnnotation`, a built-in annotation providing `{ messages: BaseMessage[] }` with an automatic message-appending reducer.

```typescript
import { StateGraph, MessagesAnnotation, START, END } from "@langchain/langgraph";
import { HumanMessage } from "@langchain/core/messages";
import { ChatOpenAI } from "@langchain/openai";

const model = new ChatOpenAI({ /* config */ });

async function callModel(state: typeof MessagesAnnotation.State) {
  const response = await model.invoke(state.messages);
  return { messages: [response] };
}

const graph = new StateGraph(MessagesAnnotation)
  .addNode("agent", callModel)
  .addEdge(START, "agent")
  .addEdge("agent", END);

const app = graph.compile();

const result = await app.invoke({
  messages: [new HumanMessage("What is 2+2?")],
});
// result.messages = [HumanMessage, AIMessage]
```

**Key points:**
- `MessagesAnnotation` provides `{ messages: BaseMessage[] }` with a built-in message reducer that appends new messages.
- Nodes return partial state — `{ messages: [newMsg] }` — the reducer handles appending.
- `START` = `"__start__"`, `END` = `"__end__"` — string constants for graph entry/exit.
- `.compile()` returns a `CompiledStateGraph` that supports `.invoke()`, `.stream()`, `.batch()`.

### Custom State with Annotation.Root

Define custom state beyond messages using `Annotation.Root`.

```typescript
import { Annotation, StateGraph, START, END } from "@langchain/langgraph";

const CustomState = Annotation.Root({
  topic: Annotation<string>,
  summary: Annotation<string>,
  wordCount: Annotation<number>,
});

async function summarize(state: typeof CustomState.State) {
  const response = await model.invoke(
    `Summarize the topic "${state.topic}" in one sentence.`
  );
  const summary = String(response.content);
  return { summary, wordCount: summary.split(/\s+/).length };
}

const graph = new StateGraph(CustomState)
  .addNode("summarize", summarize)
  .addEdge(START, "summarize")
  .addEdge("summarize", END);

const app = graph.compile();

const result = await app.invoke({
  topic: "TypeScript generics",
  summary: "",
  wordCount: 0,
});
// result.topic = "TypeScript generics" (unchanged — not returned by node)
// result.summary = "TypeScript generics allow..."
// result.wordCount = 25
```

**Key points:**
- `Annotation<T>` without a reducer uses **last-write-wins** semantics.
- Use `typeof CustomState.State` for full TypeScript typing in node functions.
- Nodes return only the fields they update — unchanged fields carry forward.

---

## 2. State Schemas and Reducers

### Default Behavior (Last-Write-Wins)

```typescript
const State = Annotation.Root({
  name: Annotation<string>,     // last write wins
  count: Annotation<number>,    // last write wins
});
```

Without a custom reducer, every field update replaces the previous value entirely.

### Custom Reducers

For fields where you need merge semantics (especially lists), define a reducer:

```typescript
import { Annotation, messagesStateReducer } from "@langchain/langgraph";
import { BaseMessage } from "@langchain/core/messages";

const State = Annotation.Root({
  // Built-in message reducer — appends, deduplicates by ID, handles RemoveMessage
  messages: Annotation<BaseMessage[]>({
    reducer: messagesStateReducer,
    default: () => [],
  }),
  // Custom append reducer for string arrays
  logs: Annotation<string[]>({
    reducer: (current, update) => [...current, ...update],
    default: () => [],
  }),
  // Last-write-wins (default, no reducer needed)
  status: Annotation<string>,
});
```

### Reducer Selection Guide

| Use Case | Reducer | Example |
|----------|---------|---------|
| Chat messages | `messagesStateReducer` | `MessagesAnnotation` or custom with `messagesStateReducer` |
| Append-only list | `(a, b) => [...a, ...b]` | Logs, results, collected items |
| Keep latest value | `undefined` (default) | Status flags, classifications, counters |
| Custom merge | `(current, update) => mergeLogic(...)` | Deduplication, aggregation |

### MessagesAnnotation vs Custom Messages

`MessagesAnnotation` is a shorthand. It's equivalent to:

```typescript
const MessagesAnnotation = Annotation.Root({
  messages: Annotation<BaseMessage[]>({
    reducer: messagesStateReducer,
    default: () => [],
  }),
});
```

Use `MessagesAnnotation` for pure chat workflows. Use custom `Annotation.Root` when you need additional fields alongside messages.

---

## 3. Nodes

Nodes are async functions that receive the current state and return a partial state update.

### Basic Node Pattern

```typescript
async function myNode(state: typeof MyState.State) {
  // Read from state
  const input = state.messages;
  // Do work
  const response = await model.invoke(input);
  // Return partial state update (only changed fields)
  return { messages: [response] };
}
```

**Rules:**
- Nodes **must** return a partial state object (a plain object with state field keys).
- Never mutate state directly — always return new values.
- The graph's reducers merge the returned partial state into the current state.

### ToolNode (Prebuilt)

`ToolNode` from `@langchain/langgraph/prebuilt` automatically executes tool calls from an `AIMessage`:

```typescript
import { ToolNode } from "@langchain/langgraph/prebuilt";
import { tool } from "@langchain/core/tools";
import { z } from "zod";

const multiply = tool(
  async ({ a, b }: { a: number; b: number }) => `${a * b}`,
  {
    name: "multiply",
    description: "Multiply two numbers",
    schema: z.object({
      a: z.number().describe("First number"),
      b: z.number().describe("Second number"),
    }),
  }
);

const toolNode = new ToolNode([multiply]);
// Used in graph: .addNode("tools", toolNode)
```

`ToolNode` reads the last `AIMessage` from state, finds `tool_calls`, executes each tool, and returns `ToolMessage` results.

---

## 4. Edges

### Fixed Edges

```typescript
graph.addEdge(START, "firstNode");   // Entry: graph starts here
graph.addEdge("nodeA", "nodeB");     // nodeA always flows to nodeB
graph.addEdge("lastNode", END);      // Exit: graph ends here
```

### Conditional Edges

Route to different nodes based on state using `addConditionalEdges`:

```typescript
function route(state: typeof RouterState.State): string {
  if (state.category === "math") return "handleMath";
  if (state.category === "code") return "handleCode";
  return "handleGeneral";
}

graph
  .addConditionalEdges("classify", route)
  .addEdge("handleMath", END)
  .addEdge("handleCode", END)
  .addEdge("handleGeneral", END);
```

**Key points:**
- Router function receives current state, returns a **string** matching a node name or `END`.
- Every node name returned by the router must exist in the graph.
- Every terminal node must have an edge to `END`.

### toolsCondition (Prebuilt Router)

The built-in `toolsCondition` router checks if the last `AIMessage` has `tool_calls`:

```typescript
import { toolsCondition } from "@langchain/langgraph/prebuilt";

graph
  .addConditionalEdges("agent", toolsCondition) // → "tools" if tool_calls, else END
  .addEdge("tools", "agent");                    // loop back for next iteration
```

This creates the standard ReAct agent loop: `agent → tools → agent → ... → END`.

### START and END Constants

```typescript
import { START, END } from "@langchain/langgraph";
// START = "__start__" — virtual entry node
// END = "__end__" — virtual exit node
```

---

## 5. Conditional Routing Patterns

### LLM-Based Classification Router

```typescript
import { Annotation, StateGraph, START, END } from "@langchain/langgraph";

const RouterState = Annotation.Root({
  input: Annotation<string>,
  category: Annotation<string>,
  response: Annotation<string>,
});

async function classify(state: typeof RouterState.State) {
  const response = await model.invoke(
    `Classify: "${state.input}". Reply with exactly one word: "math" or "general".`
  );
  return { category: String(response.content).trim().toLowerCase() };
}

async function handleMath(state: typeof RouterState.State) {
  const response = await model.invoke(`Solve: ${state.input}`);
  return { response: String(response.content) };
}

async function handleGeneral(state: typeof RouterState.State) {
  const response = await model.invoke(`Answer: ${state.input}`);
  return { response: String(response.content) };
}

function route(state: typeof RouterState.State): string {
  return state.category.includes("math") ? "handleMath" : "handleGeneral";
}

const graph = new StateGraph(RouterState)
  .addNode("classify", classify)
  .addNode("handleMath", handleMath)
  .addNode("handleGeneral", handleGeneral)
  .addEdge(START, "classify")
  .addConditionalEdges("classify", route)
  .addEdge("handleMath", END)
  .addEdge("handleGeneral", END);
```

### Using Command for Combined Routing + State Updates

`Command` lets you update state AND route in a single return:

```typescript
import { Command } from "@langchain/langgraph";

async function routingNode(state: typeof MyState.State): Promise<Command> {
  if (state.taskType === "research") {
    return new Command({
      update: { assignedTo: "researcher", startedAt: new Date().toISOString() },
      goto: "researchAgent",
    });
  }
  return new Command({
    update: { assignedTo: "writer" },
    goto: "writerAgent",
  });
}
```

**When to use Command vs addConditionalEdges:**

| Feature | `addConditionalEdges` | `Command` |
|---------|----------------------|-----------|
| Route based on state | ✅ | ✅ |
| Update state while routing | ❌ | ✅ |
| Defined at graph build time | ✅ | ❌ (runtime) |
| Navigate across subgraphs | ❌ | ✅ (`Command.PARENT`) |

---

## 6. Checkpointing

Checkpointers persist graph state between invocations, enabling multi-turn conversations and time travel.

### MemorySaver (Development)

```typescript
import { StateGraph, MessagesAnnotation, START, END, MemorySaver } from "@langchain/langgraph";
import { HumanMessage } from "@langchain/core/messages";

const checkpointer = new MemorySaver();
const app = graph.compile({ checkpointer });

const config = { configurable: { thread_id: "my-thread" } };

// Turn 1
const result1 = await app.invoke(
  { messages: [new HumanMessage("My name is Alice.")] },
  config
);

// Turn 2 — same thread_id, state persists
const result2 = await app.invoke(
  { messages: [new HumanMessage("What is my name?")] },
  config
);
// AI responds: "Your name is Alice!"
```

### PostgresSaver (Production)

```bash
npm install @langchain/langgraph-checkpoint-postgres
```

```typescript
import { PostgresSaver } from "@langchain/langgraph-checkpoint-postgres";

const checkpointer = PostgresSaver.fromConnString(
  process.env.DATABASE_URL!
);
await checkpointer.setup(); // creates tables if needed

const app = graph.compile({ checkpointer });
```

### thread_id Patterns

```typescript
// Each user gets an isolated thread
const config = { configurable: { thread_id: `user-${userId}` } };

// Each conversation gets its own thread
const config = { configurable: { thread_id: `conv-${conversationId}` } };

// Always pass config as the second argument to invoke/stream
const result = await app.invoke(input, config);
```

**Key points:**
- `MemorySaver` is in-memory only — state lost on process restart. Use for dev/testing.
- `PostgresSaver` persists to PostgreSQL — use for production.
- Different `thread_id` values create completely isolated state.
- Without a checkpointer, state is lost between invocations.

---

## 7. Human-in-the-Loop

### interrupt() + Command({ resume })

The `interrupt()` function pauses graph execution at a node, waiting for human input:

```typescript
import { interrupt, Command, MemorySaver } from "@langchain/langgraph";
import { Annotation, StateGraph, START, END } from "@langchain/langgraph";

const State = Annotation.Root({
  input: Annotation<string>,
  approved: Annotation<boolean>,
  result: Annotation<string>,
});

async function prepareAction(state: typeof State.State) {
  return { result: `Prepared action for: ${state.input}` };
}

async function approvalGate(state: typeof State.State) {
  // Pauses execution — returns the value passed to Command({ resume })
  const answer = interrupt({
    question: "Do you approve this action?",
    details: state.result,
    options: ["yes", "no"],
  });
  return { approved: answer === "yes" };
}

async function executeAction(state: typeof State.State) {
  if (!state.approved) return { result: "Action cancelled." };
  return { result: `Executed: ${state.result}` };
}

const graph = new StateGraph(State)
  .addNode("prepare", prepareAction)
  .addNode("approval", approvalGate)
  .addNode("execute", executeAction)
  .addEdge(START, "prepare")
  .addEdge("prepare", "approval")
  .addEdge("approval", "execute")
  .addEdge("execute", END);

const checkpointer = new MemorySaver();
const app = graph.compile({ checkpointer }); // ⚠️ Checkpointer REQUIRED for interrupts

const config = { configurable: { thread_id: "approval-flow-1" } };

// Step 1: Run until interrupt
const result1 = await app.invoke({ input: "Deploy to prod", approved: false, result: "" }, config);
// Graph pauses at approvalGate — result1 contains interrupt metadata

// Step 2: Resume with human decision
const result2 = await app.invoke(new Command({ resume: "yes" }), config);
// Graph continues from where it paused
// result2.approved = true, result2.result = "Executed: Prepared action for: Deploy to prod"
```

**Critical rules:**
- **Checkpointer is required** — `interrupt()` without a checkpointer throws `MISSING_CHECKPOINTER`.
- **Must use `Command` to resume** — passing a plain object `{ resume: "yes" }` starts a new execution instead of resuming, creating an infinite loop.
- **Multiple interrupts in one node** work sequentially — each `interrupt()` call pauses, and each `Command({ resume })` provides the next value.

### Multiple Approval Gates

```typescript
async function multiGate(state: typeof State.State) {
  // Gate 1
  const managerApproval = interrupt({
    gate: "manager",
    question: "Manager approval required",
  });
  if (managerApproval !== "approve") {
    return { result: "Rejected by manager" };
  }

  // Gate 2 — only reached after first resume
  const complianceApproval = interrupt({
    gate: "compliance",
    question: "Compliance review required",
  });
  if (complianceApproval !== "approve") {
    return { result: "Rejected by compliance" };
  }

  return { result: "Fully approved" };
}

// Resume gate 1:
await app.invoke(new Command({ resume: "approve" }), config);
// Resume gate 2:
await app.invoke(new Command({ resume: "approve" }), config);
```

---

## 8. Functional API: entrypoint() + task()

An alternative to `StateGraph` for simpler, imperative-style workflows.

```typescript
import { entrypoint, task } from "@langchain/langgraph";

const generateTopic = task("generateTopic", async (input: string) => {
  const response = await model.invoke(
    `Given "${input}", suggest one specific subtopic in 5 words or fewer.`
  );
  return String(response.content).trim();
});

const writeSentence = task("writeSentence", async (topic: string) => {
  const response = await model.invoke(`Write one sentence about: ${topic}`);
  return String(response.content).trim();
});

const workflow = entrypoint("myWorkflow", async (input: string) => {
  const topic = await generateTopic(input);
  const sentence = await writeSentence(topic);
  return { topic, sentence };
});

const result = await workflow.invoke("artificial intelligence");
// { topic: "Neural network architectures", sentence: "Neural networks..." }
```

### When to Use Functional API vs StateGraph

| Use Case | Functional API | StateGraph |
|----------|---------------|------------|
| Linear pipelines (A → B → C) | ✅ Simpler | Overkill |
| Branching/conditional routing | ❌ Manual `if` | ✅ Built-in |
| Cycles/loops | ❌ Not supported | ✅ Built-in |
| Human-in-the-loop | ✅ Works with `interrupt()` | ✅ Works with `interrupt()` |
| Complex multi-agent | ❌ Hard to compose | ✅ Designed for it |
| Parallel fan-out | ❌ Manual | ✅ `Send` API |

### Functional API with Checkpointer

```typescript
import { entrypoint, task, MemorySaver } from "@langchain/langgraph";

const checkpointer = new MemorySaver();

const workflow = entrypoint(
  { name: "myWorkflow", checkpointer },
  async (input: string) => {
    const result = await myTask(input);
    return result;
  }
);
```

---

## 9. Streaming

### Graph-Level Streaming

```typescript
// "updates" mode — per-node output deltas
const stream = await app.stream(
  { messages: [new HumanMessage("Hello")] },
  { streamMode: "updates" }
);
for await (const chunk of stream) {
  // chunk = { "agent": { messages: [AIMessage] } }
  const [nodeName, nodeOutput] = Object.entries(chunk)[0];
  console.log(`Node "${nodeName}" completed`);
}

// "values" mode — full state snapshots after each node
const stream = await app.stream(
  { messages: [new HumanMessage("Hello")] },
  { streamMode: "values" }
);
for await (const chunk of stream) {
  // chunk = { messages: [...all messages so far] }
  console.log(`Total messages: ${chunk.messages.length}`);
}
```

### Stream Mode Reference

| Mode | Emits | Use Case |
|------|-------|----------|
| `"updates"` | `{ nodeName: partialState }` after each node | Track node-by-node progress |
| `"values"` | Full state snapshot after each step | Watch state evolution |
| `"messages"` | Message chunks as they are produced | Token-level streaming for chat |
| `"custom"` | Custom events emitted from nodes | Application-specific events |
| `"debug"` | Detailed internal execution info | Debugging graph execution |

### Token-Level Streaming with streamEvents

```typescript
const eventStream = app.streamEvents(
  { messages: [new HumanMessage("Tell me a story")] },
  { version: "v2" }
);

for await (const event of eventStream) {
  if (event.event === "on_chat_model_stream") {
    const token = event.data?.chunk?.content;
    if (token) process.stdout.write(token);
  }
}
```

**Key points:**
- `app.stream()` emits node-level granularity.
- `app.streamEvents()` emits fine-grained events including token-level streaming.
- Always pass `{ version: "v2" }` to `streamEvents` for the current event format.
- For `"messages"` stream mode, chunks are `AIMessageChunk` objects.

---

## 10. Subgraph Composition

### Compiled Graph as a Node

Add a compiled graph directly as a node in a parent graph:

```typescript
import { StateGraph, MessagesAnnotation, START, END, MemorySaver } from "@langchain/langgraph";

// Inner graph (subgraph)
const innerGraph = new StateGraph(MessagesAnnotation)
  .addNode("innerAgent", async (state) => {
    const response = await model.invoke(state.messages);
    return { messages: [response] };
  })
  .addEdge(START, "innerAgent")
  .addEdge("innerAgent", END)
  .compile(); // compile WITHOUT checkpointer — inherits from parent

// Outer graph (parent)
const outerGraph = new StateGraph(MessagesAnnotation)
  .addNode("preprocess", preprocessNode)
  .addNode("subgraph", innerGraph) // add compiled graph as node
  .addNode("postprocess", postprocessNode)
  .addEdge(START, "preprocess")
  .addEdge("preprocess", "subgraph")
  .addEdge("subgraph", "postprocess")
  .addEdge("postprocess", END);

const app = outerGraph.compile({ checkpointer: new MemorySaver() });
```

### Invoking a Graph Inside a Node (Different State Schemas)

When subgraph and parent have different state schemas, invoke the subgraph manually:

```typescript
async function callSubgraph(state: typeof ParentState.State) {
  // Transform parent state → subgraph input
  const subgraphInput = { query: state.userInput, context: state.relevantDocs };

  // Invoke subgraph
  const subgraphResult = await compiledSubgraph.invoke(subgraphInput);

  // Transform subgraph output → parent state update
  return { answer: subgraphResult.response };
}

parentGraph.addNode("subgraphCall", callSubgraph);
```

### Subgraph Checkpointer Behavior

- **Default (no subgraph checkpointer):** Parent treats entire subgraph as a single super-step. One checkpoint for the whole subgraph execution. Cannot time-travel to points inside the subgraph.
- **With `checkpointer: true`:** Subgraph gets its own checkpoint history. Can time-travel to points between subgraph nodes. Use `getState(config, { subgraphs: true })` to access subgraph checkpoints.

```typescript
// Subgraph with its own checkpointing
const subgraph = innerGraphBuilder.compile({ checkpointer: true });
```

---

## 11. Time-Travel Debugging

Requires a checkpointer. Uses `getState`, `getStateHistory`, and `updateState`.

### Replay from a Past Checkpoint

```typescript
import { MemorySaver } from "@langchain/langgraph";

const checkpointer = new MemorySaver();
const app = graph.compile({ checkpointer });

const config = { configurable: { thread_id: "debug-thread" } };

// Step 1: Run the graph
const result = await app.invoke({ topic: "TypeScript" }, config);

// Step 2: Get state history
const states: any[] = [];
for await (const state of app.getStateHistory(config)) {
  states.push(state);
}
// states[0] = most recent, states[states.length-1] = earliest

// Step 3: Replay from a specific checkpoint
const beforeJoke = states.find((s) => s.next.includes("writeJoke"));
const replayResult = await app.invoke(null, beforeJoke.config);
// Nodes after the checkpoint re-execute; earlier nodes use cached results
```

### Fork (Branch with Modified State)

```typescript
// Find the checkpoint before a specific node
const beforeNode = states.find((s) => s.next.includes("targetNode"));

// Fork: update state and create a new branch
const forkConfig = await app.updateState(
  beforeNode.config,
  { topic: "different topic" } // modified state
);

// Resume from the fork
const forkResult = await app.invoke(null, forkConfig);
```

### Get Current State

```typescript
const currentState = await app.getState(config);
console.log(currentState.values);  // current state values
console.log(currentState.next);    // array of next node names to execute
console.log(currentState.config);  // checkpoint config

// With subgraph state
const stateWithSubs = await app.getState(config, { subgraphs: true });
```

**Key points:**
- **Replay** re-executes nodes — LLM calls and API requests fire again (may produce different results).
- **Fork** creates a new branch; the original history remains intact.
- `updateState` can accept `{ asNode: "nodeName" }` to specify which node "produced" the update.

---

## 12. Error Handling

### Try-Catch in Nodes

```typescript
async function resilientNode(state: typeof MyState.State) {
  try {
    const response = await model.invoke(state.messages);
    return { messages: [response], error: null };
  } catch (err) {
    const errorMsg = err instanceof Error ? err.message : "Unknown error";
    return { error: errorMsg };
  }
}
```

### Error State Routing

Route to error-handling nodes based on state:

```typescript
const State = Annotation.Root({
  input: Annotation<string>,
  result: Annotation<string>,
  error: Annotation<string | null>,
});

function routeAfterProcess(state: typeof State.State): string {
  if (state.error) return "errorHandler";
  return "successHandler";
}

graph
  .addNode("process", processNode)
  .addNode("errorHandler", errorHandlerNode)
  .addNode("successHandler", successHandlerNode)
  .addEdge(START, "process")
  .addConditionalEdges("process", routeAfterProcess)
  .addEdge("errorHandler", END)
  .addEdge("successHandler", END);
```

### Retry Pattern in Nodes

```typescript
async function retryNode(state: typeof MyState.State) {
  const maxRetries = 3;
  let lastError: Error | null = null;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const response = await model.invoke(state.messages);
      return { messages: [response], retryCount: attempt };
    } catch (err) {
      lastError = err instanceof Error ? err : new Error(String(err));
      if (attempt < maxRetries) {
        await new Promise((resolve) => setTimeout(resolve, 1000 * attempt)); // exponential backoff
      }
    }
  }

  return { error: `Failed after ${maxRetries} attempts: ${lastError?.message}` };
}
```

### Common Error Codes

| Error | Cause | Fix |
|-------|-------|-----|
| `INVALID_CONCURRENT_GRAPH_UPDATE` | Parallel nodes update same key without reducer | Add a reducer to the state field |
| `INVALID_GRAPH_NODE_RETURN_VALUE` | Node returned non-object | Return `{ field: value }`, not a raw value |
| `GRAPH_RECURSION_LIMIT` | Agent loop doesn't terminate | Add max iterations check or use `recursionLimit` |
| `INVALID_CHAT_HISTORY` | Malformed message sequence | Ensure proper HumanMessage/AIMessage/ToolMessage pairing |
| `MISSING_CHECKPOINTER` | `interrupt()` called without checkpointer | Pass `checkpointer` to `.compile()` |

### Recursion Limit

```typescript
const app = graph.compile({
  checkpointer,
  recursionLimit: 25, // default is 25; set lower for safety
});
```

---

## 13. Best Practices

### State Design

- **Keep state flat.** Deeply nested objects are hard to merge and debug.
- **Use explicit fields** for important data (IDs, flags, classifications) — don't bury them in messages.
- **Always define reducers** for list/array fields that multiple nodes may update.
- **Treat state as immutable** — always return new values from nodes, never mutate.

### Node Design

- **Single-responsibility nodes.** Each node should do one thing (classify, process, respond).
- **Return partial state.** Only return the fields you changed.
- **Keep node functions pure** (given same state, same output) when possible.
- **Name nodes descriptively** — names appear in streaming output and debug traces.

### Graph Structure

- **Explicit error states.** Route errors to dedicated handler nodes rather than swallowing them.
- **Ensure all paths reach END.** Orphan nodes (unreachable from START) or nodes without a path to END cause runtime errors.
- **Add recursion limits** for any graph with cycles to prevent infinite loops.
- **Test with deterministic inputs** before adding LLM calls.

### Production

- Use `PostgresSaver` (not `MemorySaver`) for production persistence.
- Pin `@langchain/langgraph` version exactly — minor versions can change behavior.
- Enable LangSmith tracing (`LANGSMITH_TRACING=true`) for visibility into graph execution.
- Use `InMemoryStore` (dev) or a database-backed store for cross-conversation memory.

---

## 14. Common Bugs and Antipatterns

### ❌ State Mutation Instead of Return

```typescript
// BAD — mutates state directly
function myNode(state: typeof MessagesAnnotation.State) {
  state.messages.push(newMessage); // ❌ Mutation!
  return state;
}

// GOOD — returns partial update; let the reducer handle it
function myNode(state: typeof MessagesAnnotation.State) {
  return { messages: [newMessage] }; // ✅
}
```

### ❌ Missing Reducer for Collection Fields

```typescript
// BAD — parallel nodes overwrite each other's results
const State = Annotation.Root({
  results: Annotation<string[]>, // ❌ No reducer — last write wins
});

// GOOD — reducer merges results from parallel nodes
const State = Annotation.Root({
  results: Annotation<string[]>({
    reducer: (current, update) => [...current, ...update],
    default: () => [],
  }),
});
```

### ❌ Orphan / Unreachable Nodes

```typescript
// BAD — "orphanNode" has no incoming edge
graph
  .addNode("nodeA", nodeA)
  .addNode("orphanNode", orphanNode) // ❌ Never reached
  .addEdge(START, "nodeA")
  .addEdge("nodeA", END);
```

### ❌ Resume Interrupt with Plain Object

```typescript
// BAD — creates new execution instead of resuming
await app.invoke({ resume: "yes" }, config); // ❌ Infinite loop!

// GOOD — uses Command class to resume
import { Command } from "@langchain/langgraph";
await app.invoke(new Command({ resume: "yes" }), config); // ✅
```

### ❌ Missing Checkpointer for Interrupts

```typescript
// BAD — interrupt without checkpointer
const app = graph.compile(); // ❌ No checkpointer
// interrupt() in a node will throw MISSING_CHECKPOINTER

// GOOD
const app = graph.compile({ checkpointer: new MemorySaver() }); // ✅
```

### ❌ ToolNode Without Matching tool_calls

If an `AIMessage` has no `tool_calls`, `ToolNode` has nothing to execute. Always route through `toolsCondition` first:

```typescript
// GOOD pattern
graph
  .addConditionalEdges("agent", toolsCondition) // only routes to "tools" if tool_calls exist
  .addEdge("tools", "agent");
```

### ❌ Large State in Every Update

```typescript
// BAD — storing large data in state
return { fullDocument: entirePDFContent }; // ❌ Copied to every checkpoint

// GOOD — store large data externally, reference by ID
import { InMemoryStore } from "@langchain/langgraph";
const store = new InMemoryStore();
await store.put(["docs"], docId, { content: entirePDFContent });
return { documentId: docId }; // ✅ Only store the reference
```

---

## 15. Import Reference

```typescript
// Core graph building
import { StateGraph, Annotation, MessagesAnnotation, START, END } from "@langchain/langgraph";
import { MemorySaver, InMemoryStore } from "@langchain/langgraph";
import { interrupt, Command, Send } from "@langchain/langgraph";
import { entrypoint, task } from "@langchain/langgraph";
import { messagesStateReducer } from "@langchain/langgraph";

// Prebuilt components
import { ToolNode, toolsCondition } from "@langchain/langgraph/prebuilt";
import { createReactAgent } from "@langchain/langgraph/prebuilt";

// Production checkpointers
import { PostgresSaver } from "@langchain/langgraph-checkpoint-postgres";

// Messages
import { HumanMessage, AIMessage, SystemMessage, ToolMessage } from "@langchain/core/messages";

// Tools
import { tool } from "@langchain/core/tools";
import { z } from "zod";
```

---

## 16. Quick Reference: Graph Building Checklist

```typescript
// 1. Define state
const State = Annotation.Root({ /* fields */ });
// or use: MessagesAnnotation

// 2. Create graph
const graph = new StateGraph(State);

// 3. Add nodes (async functions: state → partial state)
graph.addNode("name", async (state) => ({ field: newValue }));

// 4. Add edges
graph.addEdge(START, "firstNode");         // entry
graph.addEdge("nodeA", "nodeB");           // fixed
graph.addConditionalEdges("nodeA", router); // conditional
graph.addEdge("lastNode", END);            // exit

// 5. Compile with optional checkpointer
const app = graph.compile({ checkpointer: new MemorySaver() });

// 6. Use
const result = await app.invoke(input, { configurable: { thread_id: "t1" } });
const stream = await app.stream(input, { streamMode: "updates" });
```
