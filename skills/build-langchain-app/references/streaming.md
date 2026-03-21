# Streaming & Batch Processing Reference

> All patterns tested and verified 2026-03-21
> Packages: langchain@1.2.35, @langchain/core@1.1.34, @langchain/openai@1.3.0, @langchain/langgraph@1.2.5, @ai-sdk/langchain, ai
> Model: anthropic/claude-sonnet-4-6 via OpenRouter

---

## Streaming Decision Tree

Use this to pick the right streaming mode:

```
Need streaming?
├── No → use .invoke() or .batch()
└── Yes
    ├── Simple chat (text tokens to UI)?
    │   ├── Next.js + Vercel AI SDK? → LangChainAdapter.toDataStreamResponse()
    │   └── Raw server? → chain.stream() with StringOutputParser
    ├── Agent with tool calls?
    │   ├── Need full state after each step? → agent.stream({ streamMode: "values" })
    │   ├── Need per-node deltas only? → agent.stream({ streamMode: "updates" })
    │   └── Need token-level + tool events? → agent.streamEvents({ version: "v2" })
    └── LangGraph custom graph?
        ├── Full state snapshots → graph.stream({ streamMode: "values" })
        ├── Node-level deltas → graph.stream({ streamMode: "updates" })
        └── Fine-grained events → graph.streamEvents({ version: "v2" })
```

**Rule of thumb**: For simple chat UIs use the Vercel AI SDK adapter. For complex agents with tool calls, use native LangGraph streaming.

---

## 1. LCEL Chain Streaming

### chain.stream() — Text Token Streaming

**When to use**: Streaming text output from a prompt → model → parser chain to the client.
**When NOT to use**: You need structured output or tool call events.
**Packages**: `@langchain/core@1.1.34`, `@langchain/openai@1.3.0`

```typescript
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";
import { ChatOpenAI } from "@langchain/openai";

const model = new ChatOpenAI({
  model: "anthropic/claude-sonnet-4-6",
  configuration: {
    baseURL: "https://openrouter.ai/api/v1",
    apiKey: process.env.OPENROUTER_API_KEY!,
  },
});

const chain = ChatPromptTemplate.fromMessages([
  ["system", "You are a helpful assistant. Reply in 2-3 sentences."],
  ["human", "{input}"],
]).pipe(model).pipe(new StringOutputParser());

const stream = await chain.stream({ input: "What is Rust?" });

let fullText = "";
for await (const chunk of stream) {
  process.stdout.write(chunk); // real-time token streaming
  fullText += chunk;
}
```

**Critical**: `StringOutputParser` is streaming-aware — it passes through text chunks as they arrive rather than buffering. Without it, you get `AIMessageChunk` objects instead of strings.

**Failure modes**: Omitting `StringOutputParser` means chunks are `AIMessageChunk` objects, not strings. Using `JsonOutputParser` breaks streaming (it buffers the entire response).

---

### Streaming Structured Output (Workaround)

**When to use**: You need structured JSON output but also want the generation to stream (for perceived latency).
**When NOT to use**: You can tolerate waiting for the full response (use `.invoke()` with `withStructuredOutput()` instead).
**Packages**: `@langchain/core@1.1.34`, `zod@4.3.6`

```typescript
import { RunnableLambda } from "@langchain/core/runnables";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";
import { z } from "zod";

const ReviewSchema = z.object({
  summary: z.string().describe("A one-sentence summary"),
  sentiment: z.enum(["positive", "negative", "neutral"]),
  score: z.number().min(1).max(10),
});

const chain = ChatPromptTemplate.fromMessages([
  [
    "system",
    "Analyze the review. Return ONLY valid JSON with fields: summary (string), sentiment (positive/negative/neutral), score (1-10). No markdown.",
  ],
  ["human", "{review}"],
])
  .pipe(model)
  .pipe(new StringOutputParser())
  .pipe(
    new RunnableLambda({
      func: (text: string) => {
        const cleaned = text
          .replace(/```json?\n?/g, "")
          .replace(/```/g, "")
          .trim();
        return ReviewSchema.parse(JSON.parse(cleaned));
      },
    })
  );

const result = await chain.invoke({
  review: "TypeScript is amazing! Best language ever.",
});
// → { summary: "...", sentiment: "positive", score: 9 }
```

**Note**: The `RunnableLambda` parse step does NOT stream — it runs after all tokens are collected. The streaming benefit is that the LLM generation itself streams (reducing TTFB on the server side). For true client-side streaming of structured output, you need to use `streamEvents()` and accumulate tokens manually.

**Why not `withStructuredOutput()`?**: On OpenRouter, `withStructuredOutput()` via tool-calling can return 400 errors when piped from a prompt template. The prompt+parse pattern is more reliable.

---

## 2. Agent Streaming

### stream() with streamMode "values" — Full State Snapshots

**When to use**: You want the complete conversation state after each graph node executes (e.g., to render a full message list in the UI).
**When NOT to use**: You only need the delta from each step (use "updates" instead).
**Packages**: `langchain@1.2.35`, `@langchain/langgraph@1.2.5`

```typescript
import { createAgent } from "langchain";
import { tool } from "@langchain/core/tools";
import { z } from "zod";
import { ChatOpenAI } from "@langchain/openai";

const model = new ChatOpenAI({
  model: "anthropic/claude-sonnet-4-6",
  configuration: {
    baseURL: "https://openrouter.ai/api/v1",
    apiKey: process.env.OPENROUTER_API_KEY!,
  },
});

const searchTool = tool(
  ({ query }: { query: string }) => `Results for: ${query}`,
  {
    name: "search",
    description: "Search the web",
    schema: z.object({ query: z.string() }),
  }
);

const agent = createAgent({
  model,
  tools: [searchTool],
  prompt: "You are a helpful assistant.",
});

const stream = await agent.stream(
  { messages: [{ role: "user", content: "Search for TypeScript news" }] },
  { streamMode: "values" }
);

for await (const chunk of stream) {
  // chunk.messages is the FULL message array at this point in execution
  const lastMsg = chunk.messages[chunk.messages.length - 1];
  console.log(`[${lastMsg.constructor.name}] ${lastMsg.content}`);
}
```

**Chunk progression**:
1. `{ messages: [HumanMessage] }` — initial state
2. `{ messages: [HumanMessage, AIMessage(tool_calls)] }` — model decided to call a tool
3. `{ messages: [HumanMessage, AIMessage, ToolMessage] }` — tool executed
4. `{ messages: [HumanMessage, AIMessage, ToolMessage, AIMessage(final)] }` — final response

**Key insight**: Each chunk contains the **full accumulated state**, not just the new messages. This makes UI rendering simple — just replace the entire message list.

---

### stream() with streamMode "updates" — Per-Node Deltas

**When to use**: You want only the new messages from each graph node (lower bandwidth, useful for logging/debugging).
**When NOT to use**: You need the full message history at each step (use "values" instead).

```typescript
const stream = await agent.stream(
  { messages: [{ role: "user", content: "Search for news" }] },
  { streamMode: "updates" }
);

for await (const chunk of stream) {
  // chunk is { [nodeName]: { messages: [...new messages only...] } }
  for (const [node, data] of Object.entries(chunk)) {
    console.log(`Node "${node}" produced ${data.messages.length} message(s)`);
    for (const msg of data.messages) {
      console.log(`  [${msg.constructor.name}] ${msg.content}`);
    }
  }
}
```

**Node names**: In a `createAgent` graph, nodes are named `"model_request"` (LLM calls) and `"tools"` (tool executions).

**Key insight**: Each chunk only contains the **delta** — the new messages that a specific node produced. You must accumulate messages yourself if you need the full history.

---

### streamEvents() — Token-Level + Event Streaming

**When to use**: You need fine-grained control — token-by-token streaming, tool call start/end events, or custom event handling.
**When NOT to use**: Simple state-based streaming is sufficient (use `stream()` instead).
**Packages**: `langchain@1.2.35`, `@langchain/langgraph@1.2.5`

```typescript
const agent = createAgent({
  model,
  tools: [searchTool],
  prompt: "You are a helpful assistant.",
});

const stream = agent.streamEvents(
  { messages: [{ role: "user", content: "What is 2+2?" }] },
  { version: "v2" }
);

for await (const event of stream) {
  switch (event.event) {
    case "on_chat_model_stream":
      // Token-level streaming — each chunk is a partial token
      const token = event.data?.chunk?.content;
      if (typeof token === "string") {
        process.stdout.write(token);
      }
      break;

    case "on_tool_start":
      console.log(`\n🔧 Tool started: ${event.name}`);
      console.log(`   Input: ${JSON.stringify(event.data?.input)}`);
      break;

    case "on_tool_end":
      console.log(`✅ Tool finished: ${event.name}`);
      console.log(`   Output: ${event.data?.output}`);
      break;

    case "on_chat_model_start":
      console.log(`\n🤖 Model call started`);
      break;

    case "on_chat_model_end":
      console.log(`\n🤖 Model call ended`);
      break;
  }
}
```

**Critical**: Always pass `{ version: "v2" }` — v1 event format is deprecated and has different event structures.

**Event types reference**:

| Event | Fired when | `event.data` contains |
|-------|------------|----------------------|
| `on_chat_model_start` | LLM call begins | `{ input: messages[] }` |
| `on_chat_model_stream` | Each token arrives | `{ chunk: AIMessageChunk }` |
| `on_chat_model_end` | LLM call completes | `{ output: AIMessage }` |
| `on_tool_start` | Tool execution begins | `{ input: toolArgs }` |
| `on_tool_end` | Tool execution completes | `{ output: string }` |
| `on_chain_start` | Chain/graph node begins | `{ input: ... }` |
| `on_chain_end` | Chain/graph node completes | `{ output: ... }` |

---

## 3. LangGraph Custom Graph Streaming

### graph.stream() with streamMode Options

**When to use**: You've built a custom `StateGraph` (not `createAgent`) and want to stream results.
**Packages**: `@langchain/langgraph@1.2.5`

```typescript
import { StateGraph, START, END, Annotation } from "@langchain/langgraph";

const GraphState = Annotation.Root({
  messages: Annotation<any[]>({ reducer: (a, b) => [...a, ...b] }),
  result: Annotation<string>(),
});

const graph = new StateGraph(GraphState)
  .addNode("process", async (state) => {
    // ... node logic
    return { result: "processed" };
  })
  .addEdge(START, "process")
  .addEdge("process", END)
  .compile();

// Option A: Full state snapshots
const valuesStream = await graph.stream(
  { messages: [{ role: "user", content: "hello" }] },
  { streamMode: "values" }
);
for await (const state of valuesStream) {
  console.log("Full state:", state);
}

// Option B: Per-node deltas
const updatesStream = await graph.stream(
  { messages: [{ role: "user", content: "hello" }] },
  { streamMode: "updates" }
);
for await (const update of updatesStream) {
  for (const [nodeName, delta] of Object.entries(update)) {
    console.log(`Node "${nodeName}" update:`, delta);
  }
}

// Option C: Token-level events
const eventStream = graph.streamEvents(
  { messages: [{ role: "user", content: "hello" }] },
  { version: "v2" }
);
for await (const event of eventStream) {
  if (event.event === "on_chat_model_stream") {
    process.stdout.write(event.data?.chunk?.content || "");
  }
}
```

**Key insight**: All three streaming modes work the same way for custom graphs as for `createAgent` — because `createAgent` returns a compiled `StateGraph` under the hood.

---

## 4. Next.js Integration

### Route Handler with ReadableStream

**When to use**: You're building a Next.js app and need to stream LangChain output to the browser without Vercel AI SDK.
**When NOT to use**: You're using Vercel AI SDK (use the adapter instead — see section 5).

```typescript
// app/api/chat/route.ts
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";
import { ChatOpenAI } from "@langchain/openai";

const model = new ChatOpenAI({
  model: "anthropic/claude-sonnet-4-6",
  streaming: true,
  configuration: {
    baseURL: "https://openrouter.ai/api/v1",
    apiKey: process.env.OPENROUTER_API_KEY!,
  },
});

export async function POST(req: Request) {
  const { messages } = await req.json();

  const chain = ChatPromptTemplate.fromMessages([
    ["system", "You are a helpful assistant."],
    ["human", "{input}"],
  ]).pipe(model).pipe(new StringOutputParser());

  const stream = await chain.stream({
    input: messages[messages.length - 1].content,
  });

  const encoder = new TextEncoder();
  const readable = new ReadableStream({
    async start(controller) {
      try {
        for await (const chunk of stream) {
          controller.enqueue(encoder.encode(chunk));
        }
        controller.close();
      } catch (error) {
        controller.error(error);
      }
    },
  });

  return new Response(readable, {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "no-cache",
      "Transfer-Encoding": "chunked",
    },
  });
}
```

**Client-side consumption**:

```typescript
// app/page.tsx (client component)
"use client";
import { useState } from "react";

export default function Chat() {
  const [response, setResponse] = useState("");

  async function handleSubmit(input: string) {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages: [{ role: "user", content: input }] }),
    });

    const reader = res.body!.getReader();
    const decoder = new TextDecoder();
    let text = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      text += decoder.decode(value, { stream: true });
      setResponse(text);
    }
  }

  return <div>{response}</div>;
}
```

**Note**: This is the manual approach. For most Next.js apps, the Vercel AI SDK adapter (next section) is simpler and provides better client-side hooks.

---

## 5. Vercel AI SDK Bridge

### LangChainAdapter.toDataStreamResponse()

**When to use**: You want to bridge LangChain streaming into Vercel AI SDK's data stream protocol, enabling `useChat` on the client.
**When NOT to use**: You have complex LangGraph agent streams with tool calls — those may not translate cleanly to the AI SDK data stream format.
**Packages**: `@ai-sdk/langchain`, `ai`, `@ai-sdk/react`

```bash
npm install @ai-sdk/langchain ai @ai-sdk/react
```

**Server (Route Handler)**:

```typescript
// app/api/chat/route.ts
import { ChatOpenAI } from "@langchain/openai";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";
import { LangChainAdapter } from "@ai-sdk/langchain";

const model = new ChatOpenAI({
  model: "anthropic/claude-sonnet-4-6",
  streaming: true,
  configuration: {
    baseURL: "https://openrouter.ai/api/v1",
    apiKey: process.env.OPENROUTER_API_KEY!,
  },
});

export async function POST(req: Request) {
  const { messages } = await req.json();

  const chain = ChatPromptTemplate.fromMessages([
    ["system", "You are a helpful assistant."],
    ["human", "{input}"],
  ]).pipe(model).pipe(new StringOutputParser());

  const stream = await chain.stream({
    input: messages[messages.length - 1].content,
  });

  return LangChainAdapter.toDataStreamResponse(stream);
}
```

**Client (useChat hook)**:

```typescript
// app/page.tsx
"use client";
import { useChat } from "@ai-sdk/react";

export default function Chat() {
  const { messages, input, handleInputChange, handleSubmit, isLoading } =
    useChat();

  return (
    <div>
      <div>
        {messages.map((m) => (
          <div key={m.id}>
            <strong>{m.role}:</strong> {m.content}
          </div>
        ))}
      </div>
      <form onSubmit={handleSubmit}>
        <input
          value={input}
          onChange={handleInputChange}
          placeholder="Type a message..."
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading}>
          Send
        </button>
      </form>
    </div>
  );
}
```

**What works**:
- ✅ Basic text streaming from LangChain chains → AI SDK data stream
- ✅ `useChat` and `useCompletion` hooks on client
- ✅ Works with any LangChain chat model

**What has limitations**:
- ⚠️ Tool call streaming from LangGraph agents may need manual handling
- ⚠️ Complex agent events (multi-tool, branching) don't map cleanly to AI SDK data stream
- ⚠️ Some users report errors with certain LangChain stream types (GitHub issue #6624)

**Recommendation**: Use the AI SDK adapter for simple chat/chain streaming. For agents with tool calls, use native LangGraph streaming (sections 2–3) with manual ReadableStream (section 4).

---

## 6. When to Use Which Streaming Mode

| Scenario | Recommended Approach | Why |
|----------|---------------------|-----|
| Simple chat UI (Next.js) | `LangChainAdapter.toDataStreamResponse()` + `useChat` | Minimal code, great UX with AI SDK hooks |
| Simple chat UI (non-Next.js) | `chain.stream()` + `StringOutputParser` | Direct text chunks, no framework dependency |
| Agent with UI showing tool progress | `agent.stream({ streamMode: "values" })` | Full state snapshots make UI rendering trivial |
| Agent logging/debugging | `agent.stream({ streamMode: "updates" })` | Per-node deltas show exactly what each step produced |
| Token-by-token display + tool events | `agent.streamEvents({ version: "v2" })` | Most granular control over all events |
| Custom LangGraph workflow | `graph.stream()` or `graph.streamEvents()` | Same modes as agent (it's the same API underneath) |
| Bulk processing (no streaming) | `chain.batch(inputs)` | Parallel execution, no streaming overhead |

---

## 7. Batch Processing

### chain.batch() — Parallel Non-Streaming Execution

**When to use**: You need to process multiple inputs concurrently and don't need streaming.
**When NOT to use**: You need real-time output or have rate-limit concerns.
**Packages**: `@langchain/core@1.1.34`

```typescript
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";
import { ChatOpenAI } from "@langchain/openai";

const model = new ChatOpenAI({
  model: "anthropic/claude-sonnet-4-6",
  configuration: {
    baseURL: "https://openrouter.ai/api/v1",
    apiKey: process.env.OPENROUTER_API_KEY!,
  },
});

const chain = ChatPromptTemplate.fromMessages([
  ["system", "Reply in exactly one word."],
  ["human", "What color is a {item}?"],
]).pipe(model).pipe(new StringOutputParser());

const results = await chain.batch([
  { item: "banana" },
  { item: "sky" },
  { item: "grass" },
]);
// → ["Yellow", "Blue", "Green"]
```

**Key insight**: `.batch()` processes all inputs concurrently (not sequentially). All LCEL chains support `.invoke()`, `.stream()`, and `.batch()` automatically.

**With concurrency limit**:

```typescript
const results = await chain.batch(
  [{ item: "banana" }, { item: "sky" }, { item: "grass" }],
  {}, // config (empty)
  { maxConcurrency: 2 } // process at most 2 at a time
);
```

---

## 8. Common Streaming Bugs

### Bug 1: Not Awaiting the Stream

```typescript
// ❌ WRONG — stream is a Promise, not an iterable
const stream = agent.stream({ messages });
for await (const chunk of stream) { /* ... */ }

// ✅ CORRECT — await the stream first
const stream = await agent.stream({ messages });
for await (const chunk of stream) { /* ... */ }
```

**Exception**: `streamEvents()` does NOT need `await` — it returns an async iterable directly:

```typescript
// ✅ CORRECT — streamEvents returns iterable directly (no await)
const stream = agent.streamEvents({ messages }, { version: "v2" });
for await (const event of stream) { /* ... */ }
```

### Bug 2: Missing StringOutputParser for Text Streaming

```typescript
// ❌ WRONG — chunks are AIMessageChunk objects
const chain = prompt.pipe(model);
const stream = await chain.stream({ input: "hello" });
for await (const chunk of stream) {
  console.log(chunk); // AIMessageChunk { content: "Hello", ... }
}

// ✅ CORRECT — chunks are plain strings
const chain = prompt.pipe(model).pipe(new StringOutputParser());
const stream = await chain.stream({ input: "hello" });
for await (const chunk of stream) {
  console.log(chunk); // "Hello"
}
```

### Bug 3: OpenRouter Chunk Batching

Some OpenRouter providers batch multiple tokens into single chunks rather than streaming token-by-token. This means:
- Chunks may contain multiple tokens (e.g., `"Hello, how"` instead of `"Hello"`, `","`, `" how"`)
- Chunk count varies by provider (Anthropic direct ≈ 30 chunks vs some providers ≈ 10 chunks for same response)
- This is an OpenRouter behavior, not a LangChain bug

**Workaround**: Don't rely on chunk count or per-token granularity. Always accumulate the full text.

### Bug 4: Forgetting streamMode Defaults

```typescript
// Default streamMode for agent.stream() is "updates" (deltas only)
const stream = await agent.stream({ messages });
// ^ Returns per-node deltas, NOT full state

// If you want full state snapshots, explicitly set "values"
const stream = await agent.stream({ messages }, { streamMode: "values" });
```

### Bug 5: Using streamEvents Without version: "v2"

```typescript
// ❌ WRONG — defaults to v1 format (deprecated, different event structure)
const stream = agent.streamEvents({ messages });

// ✅ CORRECT — always specify version "v2"
const stream = agent.streamEvents({ messages }, { version: "v2" });
```

### Bug 6: Streaming Structured Output Expects Tokens

```typescript
// ❌ WRONG — withStructuredOutput doesn't produce streaming tokens
const model = new ChatOpenAI({ /* ... */ }).withStructuredOutput(schema);
const stream = await model.stream("Analyze this"); // chunks are partial objects, not text

// ✅ CORRECT — use prompt+parse pattern for structured output
// (see section 1 "Streaming Structured Output" above)
```

---

## Import Reference

```typescript
// Chain streaming
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";
import { RunnableLambda } from "@langchain/core/runnables";

// Agent streaming
import { createAgent } from "langchain";
import { tool } from "@langchain/core/tools";

// LangGraph streaming
import { StateGraph, START, END, Annotation } from "@langchain/langgraph";

// Vercel AI SDK bridge
import { LangChainAdapter } from "@ai-sdk/langchain";

// Client-side
import { useChat } from "@ai-sdk/react";

// Model
import { ChatOpenAI } from "@langchain/openai";

// Schema
import { z } from "zod";
```
