# Streaming Reference — LangChain.js & LangGraph

> Fact-checked against official LangGraph JS docs, LangChain reference API, and GitHub source.
> Research date: 2026-03-23
> Packages: `@langchain/langgraph`, `@langchain/core`, `@ai-sdk/langchain`, `@langchain/langgraph-sdk`

---

## API Comparison

| API | Returns | Level | Best For |
|-----|---------|-------|----------|
| `graph.stream()` | `AsyncIterator<chunk>` | Graph/agent | Production agents — state updates, tokens, tool events |
| `runnable.streamEvents()` | `IterableReadableStream<StreamEvent>` | Any runnable | Debugging, LCEL chains, fine-grained filtering |
| `runnable.streamLog()` | `AsyncGenerator<RunLogPatch>` | Any runnable | Legacy — JSON-Patch run reconstruction (deprecated) |
| `toUIMessageStream()` | `ReadableStream<UIMessageChunk>` | Bridge | Connecting LangGraph to Vercel AI SDK UI hooks |

---

## 1. `graph.stream()` — The 8 Stream Modes

### Core Signature

```ts
class CompiledStateGraph {
  stream(
    inputs: Record<string, any> | CommandType | null,
    options?: {
      streamMode?: StreamMode | StreamMode[];
      subgraphs?: boolean;
      configurable?: {
        thread_id?: string;
        checkpoint_id?: string;
        checkpoint_ns?: string;
      };
      signal?: AbortSignal;
    }
  ): Promise<IterableReadableStream<any>>;
}
```

### Mode Reference

| Mode | Chunk Shape | Requires Checkpointer | When to Use |
|------|-------------|----------------------|-------------|
| `values` | Full state object | No | Snapshot UI, audit logs, simple displays |
| `updates` | `{ [nodeName]: Partial<State> }` | No | Progress dashboards, production workloads |
| `messages` | `[BaseMessageChunk, StreamMetadata]` | No | Chat UIs with typing effect |
| `custom` | Any JSON via `config.writer()` | No | Tool progress, domain-specific notifications |
| `tools` | Tool lifecycle events | No | Tool status cards, progress indicators |
| `debug` | Full trace events | No | Development only — high data volume |
| `tasks` | Task start/finish events | **Yes** | Node-level execution visibility |
| `checkpoints` | Full `StateSnapshot` per step | **Yes** | State replay, audit, HITL resume |

---

### `values` — Full State Snapshot

Yields the **complete state object** after each super-step (when all nodes in that step complete).

```ts
for await (const chunk of await graph.stream(
  { topic: "ice cream" },
  { streamMode: "values" }
)) {
  // chunk is the full state — same type as your state schema
  console.log(`topic: ${chunk.topic}, joke: ${chunk.joke}`);
}
```

**Overhead**: Highest — sends full state every step. Use for simple UIs where you always need full context.

---

### `updates` — State Deltas (Default)

Yields only what **changed** after each individual node. This is the default and most efficient mode.

```ts
for await (const chunk of await graph.stream(
  { topic: "ice cream" },
  { streamMode: "updates" }
)) {
  // chunk is { [nodeName]: partialStateUpdate }
  for (const [nodeName, state] of Object.entries(chunk)) {
    console.log(`Node "${nodeName}" updated:`, state);
  }
}
```

---

### `messages` — Token-Level Streaming

Yields `[BaseMessageChunk, StreamMetadata]` tuples token-by-token from **any LLM call** in the graph, including inside tools and subgraphs.

```ts
for await (const [token, metadata] of await graph.stream(
  { messages: [{ role: "user", content: "Weather in SF?" }] },
  { streamMode: "messages" }
)) {
  // metadata.langgraph_node, metadata.tags, metadata.run_id
  if (token.content && metadata.langgraph_node === "agent") {
    process.stdout.write(String(token.content));
  }
}
```

Filter by tag: assign `model.withConfig({ tags: ["final_answer"] })` then check `metadata.tags?.includes("final_answer")`.

**Requirement**: LLM provider must support streaming. Disable: `streaming: false` or `disableStreaming: true` on the model.

---

### `custom` — User-Defined Events

Emit any JSON-serializable data from nodes or tools via `config.writer`. No extra configuration needed — events surface automatically when consuming with `streamMode: "custom"`.

**From a node:**
```ts
import { type LangGraphRunnableConfig } from "@langchain/langgraph";

const myNode = async (state: State, config: LangGraphRunnableConfig) => {
  config.writer({ type: "progress", percent: 25, message: "Fetching data..." });
  // ... do work ...
  config.writer({ type: "progress", percent: 75, message: "Processing results..." });
  config.writer({ type: "result", data: someData });
  return { answer: "done" };
};
```

**From a tool** — same pattern, `config.writer(...)` works identically.

**Consuming:**
```ts
for await (const chunk of await graph.stream(
  { query: "example" },
  { streamMode: "custom" }
)) {
  if (chunk.type === "progress") console.log(`${chunk.percent}% — ${chunk.message}`);
}
```

**Non-LangChain LLM clients** can pipe through custom mode via `config.writer({ custom_llm_chunk: chunk })` inside a node.

---

### `tools` — Tool Lifecycle Events

Streams structured tool events automatically — no extra code needed inside tool implementations.

```ts
for await (const [mode, chunk] of await graph.stream(
  { messages: [{ role: "user", content: "Find flights to Tokyo" }] },
  { streamMode: ["updates", "tools"] }
)) {
  if (mode === "tools") {
    switch (chunk.event) {
      case "on_tool_start":
        console.log(`Tool started: ${chunk.name}`, chunk.input);
        break;
      case "on_tool_event":
        // Emitted when the tool is an async generator
        console.log(`Tool progress: ${chunk.name}`, chunk.data);
        break;
      case "on_tool_end":
        console.log(`Tool finished: ${chunk.name}`, chunk.output);
        break;
      case "on_tool_error":
        console.error(`Tool failed: ${chunk.name}`, chunk.error);
        break;
    }
  }
}
```

**Event shapes:**
- `on_tool_start` — `{ event, name: string, input: JsonObject, tool_call_id: string }`
- `on_tool_event` — `{ event, name: string, data: any }` (for async generator tools only)
- `on_tool_end` — `{ event, name: string, output: JsonObject, tool_call_id: string }`
- `on_tool_error` — `{ event, name: string, error: Error }`

**Async generator tools** emit `on_tool_event` for each yielded value:
```ts
const longRunningTool = tool(
  async function* ({ query }) {
    yield { message: "Searching...", progress: 0 };
    const results = await search(query);
    yield { message: `Found ${results.length} results`, progress: 50 };
    return await processResults(results); // final return value
  },
  { name: "long_running_search", schema: z.object({ query: z.string() }) }
);
```

---

### `debug` — Full Trace (Development Only)

Combines `checkpoints` and `tasks` with extra metadata. `streamMode: "debug"` dumps full state at every step — development use only.

### `tasks` — Node Execution Events (Requires Checkpointer)

Chunk shape: `{ node: string, status: "start" | "end", result?: any, error?: Error }`. Requires `configurable: { thread_id }`.

### `checkpoints` — State Snapshot Per Step (Requires Checkpointer)

Yields a full `StateSnapshot` per step: `{ values, next, config.configurable.checkpoint_id }`. Requires `checkpointer` and `configurable: { thread_id }`.

---

## 2. Combining Multiple Stream Modes

Pass an array to `streamMode` — each chunk becomes a `[mode, chunk]` tuple. Combine 2–3 modes maximum.

```ts
for await (const [mode, chunk] of await graph.stream(
  { messages: [{ role: "user", content: "Hello" }] },
  { streamMode: ["messages", "updates", "custom"] }
)) {
  if (mode === "messages") process.stdout.write(chunk[0].content ?? "");
  if (mode === "updates")  console.log("State:", chunk);
  if (mode === "custom")   console.log("Custom:", chunk);
}
```

---

## 3. Subgraph Streaming

Set `subgraphs: true` — each chunk becomes `[namespace[], data]` where `namespace` identifies the source subgraph (e.g., `["parent_node:<task_id>"]`). For the LangSmith SDK use `streamSubgraphs: true` instead.

```ts
for await (const [ns, data] of await graph.stream({ foo: "foo" }, { streamMode: "updates", subgraphs: true })) {
  if (ns.length > 0) console.log(`Subgraph ${ns.join(".")}:`, data);
  else console.log("Parent graph:", data);
}
```

---

## 4. TypeScript Types

```ts
// All valid stream modes
type StreamMode =
  | "values"
  | "updates"
  | "messages"
  | "custom"
  | "tools"
  | "debug"
  | "tasks"
  | "checkpoints"
  | "events"          // LangSmith SDK only
  | "messages-tuple"; // LangSmith SDK only

// Metadata attached to each token in messages mode
interface StreamMetadata {
  langgraph_node: string;  // Graph node that produced this token
  tags: string[];
  run_id: string;
  thread_id?: string;
}

// StreamEvent (from streamEvents())
interface StreamEvent {
  event: string;               // on_[type]_(start|stream|end|error) or on_custom_event
  name: string;
  run_id: string;
  parent_ids: string[];        // v2 only
  tags: string[];
  metadata: Record<string, any>;
  data: Record<string, any>;   // Payload varies by event type
}

// AI SDK adapter part type
type UIMessageChunk = { type: "text" | "tool_call" | `data-${string}` };
```

---

## 5. `streamEvents()` — Runnable-Level Event Streaming

Works on any `Runnable` — LLM, chain, agent, tool. Returns an `IterableReadableStream<StreamEvent>` (both async iterator and ReadableStream).

```ts
streamEvents(
  input: any,
  options: Partial<RunnableConfig> & { version: "v1" | "v2" },
  streamOptions?: Omit<EventStreamCallbackHandlerInput, "autoClose">
): IterableReadableStream<StreamEvent>
```

**Always use `version: "v2"`** — v1 omits parent run metadata and is deprecated.

### StreamEvent Catalog (17 types)

| Event | Runnable Type | `data` Payload |
|-------|--------------|----------------|
| `on_chat_model_start` | Chat model | `{ input: { messages: BaseMessage[][] } }` |
| `on_chat_model_stream` | Chat model | `{ chunk: AIMessageChunk }` |
| `on_chat_model_end` | Chat model | `{ input: ..., output: AIMessageChunk }` |
| `on_llm_start` | LLM (completion) | `{ input: { prompts: string[] } }` |
| `on_llm_stream` | LLM (completion) | `{ chunk: GenerationChunk }` |
| `on_llm_end` | LLM (completion) | `{ input: ..., output: LLMResult }` |
| `on_chain_start` | Chain/Runnable | `{ input: any }` |
| `on_chain_stream` | Chain/Runnable | `{ chunk: any }` |
| `on_chain_end` | Chain/Runnable | `{ input: any, output: any }` |
| `on_tool_start` | Tool | `{ input: Record<string, any> }` |
| `on_tool_end` | Tool | `{ output: string }` |
| `on_tool_error` | Tool | `{ error: Error }` |
| `on_retriever_start` | Retriever | `{ input: { query: string } }` |
| `on_retriever_end` | Retriever | `{ output: { documents: Document[] } }` |
| `on_retriever_error` | Retriever | `{ error: Error }` |
| `on_prompt_start` | Prompt template | `{ input: Record<string, any> }` |
| `on_prompt_end` | Prompt template | `{ output: ChatPromptValue }` |
| `on_custom_event` | Any (dispatched manually) | User-defined |

### Basic Usage

```ts
import { ChatOpenAI } from "@langchain/openai";
import { HumanMessage } from "@langchain/core/messages";

const model = new ChatOpenAI({ model: "gpt-4o-mini" });

for await (const event of model.streamEvents(
  [new HumanMessage("Tell me a joke")],
  { version: "v2" }
)) {
  if (event.event === "on_chat_model_stream") {
    process.stdout.write(event.data.chunk.content);
  }
}
```

### Custom Events with `dispatchCustomEvent`

```ts
import { dispatchCustomEvent } from "@langchain/core/callbacks/dispatch";

// Inside any runnable — dispatches an on_custom_event
await dispatchCustomEvent("step_progress", { step: 1, message: "Done" });

// Consumer filters by event name:
for await (const event of runnable.streamEvents(input, { version: "v2" })) {
  if (event.event === "on_custom_event" && event.name === "step_progress") {
    console.log("Progress:", event.data);
  }
}
```

### LCEL Chain Streaming

```ts
const chain = ChatPromptTemplate.fromTemplate("Answer: {question}")
  .pipe(new ChatOpenAI({ model: "gpt-4o-mini" }))
  .pipe(new StringOutputParser());

// chain.stream() yields string chunks from StringOutputParser
for await (const chunk of await chain.stream({ question: "What is 2+2?" })) {
  process.stdout.write(chunk);
}
// chain.streamEvents() yields all intermediate events — filter on on_chat_model_stream
```

---

## 6. `streamLog()` — Legacy (Deprecated)

Streams JSON-Patch ops to reconstruct full run state. **Migrate to `streamEvents()` v2.** Patch shape: `{ ops: Array<{ op: "add"|"replace"|"remove", path: string, value?: any }> }`. Apply ops with `fast-json-patch`.

---

## 7. `@ai-sdk/langchain` — Vercel AI SDK Bridge

Bridges LangChain/LangGraph streaming with Vercel AI SDK's UI layer.

```bash
npm install @ai-sdk/langchain @langchain/openai ai
```

### Core Functions

| Function | Input | Output | Purpose |
|----------|-------|--------|---------|
| `toBaseMessages(messages)` | `UIMessage[]` | `Promise<BaseMessage[]>` | AI SDK → LangChain message format |
| `convertModelMessages(messages)` | `ModelMessage[]` | `BaseMessage[]` | Synchronous model message conversion |
| `toUIMessageStream(stream)` | `AsyncIterable<AIMessageChunk>` | `ReadableStream<UIMessageChunk>` | LangChain stream → AI SDK format |
| `LangSmithDeploymentTransport` | Options object | `ChatTransport` | Direct browser → LangGraph connection |

### Next.js App Router — LangGraph Agent

Pattern: `toBaseMessages` converts AI SDK messages → LangChain format, `toUIMessageStream` converts the graph stream back → AI SDK format.

```ts
// app/api/chat/route.ts
import { toBaseMessages, toUIMessageStream } from "@ai-sdk/langchain";
import { createUIMessageStreamResponse } from "ai";

export async function POST(req: Request) {
  const { messages } = await req.json();
  const langchainMessages = await toBaseMessages(messages);

  // graph.stream() with ["values", "messages"] is the standard pairing for this adapter
  const stream = await graph.stream(
    { messages: langchainMessages },
    { streamMode: ["values", "messages"] }
  );

  return createUIMessageStreamResponse({ stream: toUIMessageStream(stream) });
}
```

### Custom Data Events with the Adapter

Data emitted via `config.writer` becomes typed parts in AI SDK messages:
- **With `id`** → persistent, stored in `message.parts` as `data-{type}` part — render as `<ProgressBar>` etc.
- **Without `id`** → transient, delivered only via the `onData(data)` callback in `useChat`

```ts
// Server — with id = persistent, without id = transient
config.writer?.({ type: "progress", id: `step-${i}`, progress: 50, message: "Halfway done" });
config.writer?.({ type: "status", text: "Still working..." }); // transient
```

Client reads persistent parts via `msg.parts` (type `"data-progress"`) and transient ones via `useChat({ onData })`.

### `LangSmithDeploymentTransport` — Direct Browser Connection

```tsx
import { LangSmithDeploymentTransport } from "@ai-sdk/langchain";
import { useChat } from "@ai-sdk/react";

// Skip backend — browser connects directly to deployed LangGraph agent
const transport = new LangSmithDeploymentTransport({
  url: "https://your-agent.us.langgraph.app",
  apiKey: process.env.NEXT_PUBLIC_LANGSMITH_API_KEY,
  graphId: "agent",  // defaults to "agent"
});
const { messages, sendMessage } = useChat({ transport });
```

**Security**: Only expose `apiKey` in browser for internal tools or development.

---

## 8. `useStream` Hook — React / Vue / Svelte

Official hooks connecting directly to a LangGraph agent's streaming API.

```bash
npm install @langchain/langgraph-sdk  # includes @langchain/langgraph-sdk/react
```

### Basic Usage + Return Shape

```tsx
import { useStream } from "@langchain/langgraph-sdk/react";

function Chat() {
  // Return shape: { values, messages, tools, interrupts, history, status, isLoading, error,
  //                 submit(), stop(), joinStream() }
  const { values, isLoading, interrupt, resume } = useStream({
    apiUrl: process.env.NEXT_PUBLIC_LANGGRAPH_API_URL!,
    streamMode: ["messages", "updates"],
  });

  if (interrupt) {
    return <div>
      <p>{interrupt.value}</p>
      <button onClick={() => resume(true)}>Approve</button>
      <button onClick={() => resume(false)}>Reject</button>
    </div>;
  }

  return <div>
    {values?.messages?.map((msg, i) => <div key={i}>{msg.content}</div>)}
    {isLoading && <span>Streaming...</span>}
  </div>;
}
```

`submit(input, opts)` options: `onDisconnect: "cancel" | "continue"` (default `"cancel"`), `streamResumable: boolean` (default `false`), `threadId: string`.

### Join & Rejoin Pattern (Resumable Streams)

Save `run.run_id` from `onCreated`, then call `stream.joinStream(runId)` on reconnect:

```tsx
const stream = useStream<typeof myAgent>({
  apiUrl: "http://localhost:2024",
  assistantId: "my-agent",
  onCreated(run) { localStorage.setItem("activeRunId", run.run_id); },
});

// On send — must set both flags:
stream.submit(
  { messages: [{ type: "human", content: text }] },
  { onDisconnect: "continue", streamResumable: true }
);

// On reconnect:
await stream.joinStream(localStorage.getItem("activeRunId")!);
```

**Both `onDisconnect: "continue"` and `streamResumable: true` must be set** — without them the agent stops when the client disconnects and `joinStream` will fail.

---

## 9. Framework Integrations

### Next.js App Router — SSE with `graph.stream()`

```ts
// app/api/chat/route.ts
export const maxDuration = 300; // Required for long runs on Vercel Pro

import { graph } from "@/lib/graph";

export async function POST(req: Request) {
  const { messages } = await req.json();
  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    async start(controller) {
      try {
        for await (const [mode, chunk] of await graph.stream(
          { messages },
          {
            streamMode: ["messages", "updates"],
            configurable: { thread_id: crypto.randomUUID() },
          }
        )) {
          if (mode === "messages") {
            const [msgChunk] = chunk;
            if (msgChunk.content) {
              controller.enqueue(
                encoder.encode(`data: ${JSON.stringify({ type: "token", content: msgChunk.content })}\n\n`)
              );
            }
          } else if (mode === "updates") {
            controller.enqueue(
              encoder.encode(`data: ${JSON.stringify({ type: "update", data: chunk })}\n\n`)
            );
          }
        }
        controller.enqueue(encoder.encode("data: [DONE]\n\n"));
      } catch (err) {
        controller.enqueue(
          encoder.encode(`event: error\ndata: ${JSON.stringify({ error: String(err) })}\n\n`)
        );
      } finally {
        controller.close();
      }
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      "Connection": "keep-alive",
    },
  });
}
```

### Express.js

Set SSE headers with `res.flushHeaders()`, then use `BaseCallbackHandler.fromMethods({ handleLLMNewToken, handleLLMEnd, handleLLMError })` to write `data: ...\n\n` lines. Call `res.flush()` if compression middleware is active.

### Hono (Edge-compatible)

```ts
import { Hono } from "hono";
import { streamSSE } from "hono/streaming";
import { ChatOpenAI } from "@langchain/openai";

const app = new Hono();
app.post("/chat", async (c) => {
  const { message } = await c.req.json();
  return streamSSE(c, async (stream) => {
    for await (const chunk of await new ChatOpenAI({ model: "gpt-4o-mini" }).stream(message)) {
      await stream.writeSSE({ data: String(chunk.content) });
    }
    await stream.writeSSE({ data: "[DONE]" });
  });
});
export default app;
```

### Cloudflare Workers

Wrap the `AsyncIterator` in a `ReadableStream` — CF Workers do not support async iterators directly as response bodies.

```ts
export default {
  async fetch(req: Request): Promise<Response> {
    const { message } = await req.json<{ message: string }>();
    const encoder = new TextEncoder();
    const iterator = await new ChatOpenAI({ model: "gpt-4o-mini" })
      .stream([new HumanMessage(message)]);

    return new Response(new ReadableStream({
      async start(c) {
        for await (const chunk of iterator) c.enqueue(encoder.encode(`data: ${chunk.content}\n\n`));
        c.enqueue(encoder.encode("data: [DONE]\n\n"));
        c.close();
      },
    }), { headers: { "Content-Type": "text/event-stream", "Cache-Control": "no-cache" } });
  },
};
```

**CF Workers limitations**: Free tier: 30s timeout. Paid: up to 30 min. `@langchain/langgraph` can get stuck — use LangSmith deployment + `LangSmithDeploymentTransport`. Durable Objects required for stateful execution.

---

## 10. LangSmith Deployment Streaming

```ts
import { Client } from "@langchain/langgraph-sdk";

const client = new Client({
  apiUrl: "https://your-deployment.us.langgraph.app",
  apiKey: process.env.LANGSMITH_API_KEY,
});

const thread = await client.threads.create();

// Stateful stream — note "messages-tuple" replaces "messages" in LangSmith SDK
for await (const chunk of client.runs.stream(thread.thread_id, "agent", {
  input: { messages: [{ type: "human", content: "Hello" }] },
  streamMode: ["updates", "messages-tuple"],
  streamSubgraphs: true,  // LangSmith SDK uses streamSubgraphs (not subgraphs)
})) {
  // chunk.event: "values" | "updates" | "messages" | "debug" | "custom" | "events" | string
  if (chunk.event === "messages") {
    const [msgChunk] = chunk.data;
    process.stdout.write(msgChunk.content);
  }
  if (chunk.event === "updates") console.log("State update:", chunk.data);
}

// Stateless run — pass null as thread_id
for await (const chunk of client.runs.stream(null, "agent", { input, streamMode: "updates" })) {
  console.log(chunk.data);
}

// Rejoin a background run
for await (const chunk of client.runs.joinStream(thread.thread_id, runId)) {
  console.log(chunk);
}
```

---

## 11. Structured Output Streaming Workarounds

### The Core Problem

`withStructuredOutput()` with JSON schema **buffers the entire response** before parsing. Token-level streaming is disabled — you receive one chunk with the complete parsed object.

```ts
// This will NOT stream token-by-token:
const structuredModel = new ChatOpenAI({ model: "gpt-4o" }).withStructuredOutput(MySchema);
for await (const chunk of await structuredModel.stream(input)) {
  console.log(chunk); // Complete object, not partial
}
```

### Option A: Stream raw tokens, parse on completion

```ts
const rawStream = await model.stream(input);
let fullText = "";
for await (const chunk of rawStream) {
  fullText += chunk.content;
  updateUI(fullText); // Show partial JSON as it accumulates
}
const parsed = MySchema.parse(JSON.parse(fullText));
```

### Option B: Use `streamEvents` to intercept raw tokens

```ts
const structuredModel = model.withStructuredOutput(MySchema);
let partial = "";

for await (const event of structuredModel.streamEvents(input, { version: "v2" })) {
  if (event.event === "on_chat_model_stream") {
    partial += event.data.chunk.content ?? "";
    // Show partial JSON to user
  }
  if (event.event === "on_chain_end") {
    const structured = event.data.output; // Parsed structured object
  }
}
```

**Option C**: Pass `chain.streamEvents(input, { version: "v2", encoding: "text/event-stream" })` directly as a `Response` body and filter `on_chain_stream` events on the client.

### Tool Call Streaming Limitation

Token-level streaming for tool calls is disabled on older OpenAI models and some Ollama models. Workaround: use `graph.stream()` with `streamMode: "messages"` — LangGraph handles tool streaming at the graph level. GPT-4o and Claude 3.x+ stream tool calls natively.

---

## 12. Error Handling & Cancellation

Wrap the `for await` loop in `try/catch`. Save partial responses before rethrowing.

**AbortSignal cancellation** — pass `signal` in options (RunnableConfig):

```ts
const controller = new AbortController();
setTimeout(() => controller.abort(), 30_000);

try {
  for await (const chunk of await agent.stream(input, {
    streamMode: "messages",
    signal: controller.signal,
  })) {
    processChunk(chunk);
  }
} catch (error) {
  if (controller.signal.aborted) console.log("Cancelled");
  else throw error;
}
```

**Mid-stream SSE errors**: Status code is already 200 — encode errors in the data stream:

```ts
// Server — catch block inside ReadableStream.start():
catch (error) {
  controller.enqueue(encoder.encode(
    `event: error\ndata: ${JSON.stringify({ message: (error as Error).message })}\n\n`
  ));
}

// Client — check ev.event === "error" in onmessage handler
```

### Infrastructure Error Reference

| Issue | Symptom | Fix |
|-------|---------|-----|
| Nginx proxy buffering | Tokens arrive in batches | `proxy_buffering off; proxy_cache off;` |
| Nginx timeout | Stream drops after 60s | `proxy_read_timeout 3600s;` |
| Vercel function timeout | Stream cut off | `export const maxDuration = 300;` (Pro required for >60s) |
| Cloudflare stream stuck | Stream never resolves | Use LangSmith deployment + `LangSmithDeploymentTransport` |
| SSE auto-reconnect loses state | `EventSource` reconnects but partial state lost | Use `@microsoft/fetch-event-source` with manual state tracking |
| Gzip breaks SSE | Compressed response | Add `Content-Encoding: none` header |

---

## 13. Extended Thinking / Reasoning Tokens

Enable with `new ChatAnthropic({ model: "claude-sonnet-4-6", thinking: { type: "enabled", budget_tokens: 5000 } })`. In `messages` mode, tokens arrive as `token.contentBlocks` — check `block.type === "reasoning"` for thinking text and `block.type === "text"` for regular output.

---

## 14. Known Gotchas

| # | Issue | Context | Workaround |
|---|-------|---------|------------|
| 1 | Structured output disables token streaming | `withStructuredOutput()` buffers full response | Use `streamEvents` v2, intercept raw tokens, parse on `on_chain_end` |
| 2 | Token streaming disabled with bound tools | Older OpenAI models, some Ollama models | Upgrade to GPT-4o / Claude 3.x+; use `graph.stream()` with `messages` mode |
| 3 | `streamEvents` v1 lacks parent metadata | v1 of the API | Always pass `{ version: "v2" }` |
| 4 | LangGraph 0.4.x breaking change | `tools` stream mode format changed | Update `streamMode` values after 0.4.x upgrade |
| 5 | Cloudflare Workers streaming stuck | Edge runtime incompatibility | Use LangSmith deployment + `LangSmithDeploymentTransport` |
| 6 | `streamLog` deprecated | Newer LangChain versions | Migrate to `streamEvents` v2 |
| 7 | `streamEvents` on `RemoteRunnable` broken | Issue #5309 in langchainjs | Use `streamMode` on direct graph/agent calls |
| 8 | Token usage missing in streaming | `usage_metadata` delivered separately | Collect `on_chat_model_end` which includes `llm_output.tokenUsage` |
| 9 | Streaming breaks after LangGraph 0.4.x | Token-by-token stopped | Check `streamMode` config; re-enable `streaming: true` on the model |
| 10 | `await agent.streamEvents()` TypeScript error | Type definition issue in langgraphjs (#1086) | Use `// @ts-expect-error` or cast; works at runtime |
| 11 | Double messages on stream rejoin | Bug #2028 in langgraphjs | Deduplicate by message ID on the client side until patched |

---

## 15. Production Decision Reference

| Use Case | Recommended API | Mode |
|----------|----------------|------|
| Interactive chat UI | `graph.stream()` | `messages` |
| Agent progress dashboard | `graph.stream()` | `updates` |
| Tool execution feedback | `graph.stream()` | `["custom", "tools"]` |
| Background processing (no UI) | `.invoke()` | — |
| Debugging/observability | `streamEvents()` v2 | — |
| Analytics pipeline | `.invoke()` + `.batch()` | — |
| LangSmith deployment | `client.runs.stream()` | `["updates", "messages-tuple"]` |
| Full audit log | `graph.stream()` | `["values", "checkpoints"]` |

**SSE keep-alive** for long-running agents behind proxies:
```ts
const pingInterval = setInterval(() => {
  if (!res.writableEnded) {
    res.write(": ping\n\n"); // SSE comment — ignored by clients, resets proxy timeout
  }
}, 15_000);

res.on("close", () => clearInterval(pingInterval));
```
