---
name: build-langchain-app
description: Use skill if you are building LLM applications, agents, RAG pipelines, or tool-calling workflows with LangChain.js and LangGraph in TypeScript.
---

# Build LangChain App

Build LLM-powered TypeScript applications with LangChain.js v1 (`langchain@1.2+`, `@langchain/core@1.1+`, `@langchain/langgraph@1.2+`). All patterns verified live. TypeScript only.

## Decision tree

```
What do you need?
│
├── Simple chatbot, single provider?
│   └─► Do NOT use LangChain. Use provider SDK directly or Vercel AI SDK.
│
├── Multi-provider model switching
│   └─► ChatModel abstraction ─────────────► Quick start A (below)
│
├── Tool-calling agent
│   ├── Simple (1-5 tools, no state) ──────► Quick start B — createAgent
│   └── Complex (state, cycles, HITL) ────► Quick start C — LangGraph StateGraph
│
├── Structured data extraction
│   ├── On model directly ─────────────────► model.withStructuredOutput(zodSchema)
│   └── With createAgent ─────────────────► ToolStrategy.fromSchema(schema) — NOT new ToolStrategy()
│
├── RAG pipeline
│   └─► Quick start D — text splitters + LCEL chain
│
├── Streaming to web UI
│   ├── Simple chat streams ───────────────► @ai-sdk/langchain LangChainAdapter
│   └── Agent streams with tool calls ────► Native LangGraph streaming
│
├── Production middleware
│   ├── Retry on failure ──────────────────► references/pattern-catalog.md § Production — modelRetryMiddleware
│   ├── Model fallback ───────────────────► references/pattern-catalog.md § Production — modelFallbackMiddleware
│   ├── Rate limiting ────────────────────► references/pattern-catalog.md § Production — toolCallLimitMiddleware
│   └── Human approval ───────────────────► references/pattern-catalog.md § Production — interrupt()
│
├── LCEL composition patterns
│   └─► references/pattern-catalog.md § LCEL — pipe, parallel, lambda, passthrough, branch, batch
│
├── Memory / persistence
│   ├── Thread-scoped conversation ────────► MemorySaver checkpointer
│   ├── Cross-conversation long-term ─────► InMemoryStore (dev) or database store (prod)
│   └── Auto-summarization ───────────────► summarizationMiddleware
│
├── Python → TypeScript migration
│   └─► Migration table (below)
│
├── Full pattern reference
│   └─► references/pattern-catalog.md — 47 verified patterns with exact tested code
│
├── What NOT to do
│   └─► references/antipatterns.md — 22 antipatterns with ❌/✅ pairs
│
└── Full intent-based routing
    └─► references/decision-tree.md — 13 developer intents mapped to recommendations
```

## Required packages

```bash
npm install langchain @langchain/core @langchain/openai @langchain/langgraph zod
# For OpenRouter:
npm install @langchain/openrouter
```

Node.js 20+ required. Node 18 dropped in v1.

## OpenRouter setup

Use the dedicated `@langchain/openrouter` package. Do not use the legacy `ChatOpenAI` + `baseURL` hack.

```typescript
import { ChatOpenRouter } from "@langchain/openrouter";

const model = new ChatOpenRouter({
  model: "anthropic/claude-sonnet-4-6",
  apiKey: process.env.OPENROUTER_API_KEY,
});
```

OpenRouter constraints:
- `toolStrategy` works. `providerStrategy` fails with multi-model routing.
- `withStructuredOutput()` works on direct calls. Intermittent when piped from templates — use prompt+parse lambda workaround (`references/pattern-catalog.md` § LCEL 6).
- Streaming, tool calling, batch all work.
- Embeddings NOT supported — use OpenAI directly for embeddings.

## Quick start A — Chat model with tools

```typescript
import { ChatOpenRouter } from "@langchain/openrouter";
import { tool } from "@langchain/core/tools";
import { z } from "zod";

const search = tool(
  ({ query }) => `Results for: ${query}`,
  {
    name: "search",
    description: "Search for information",
    schema: z.object({ query: z.string().describe("Search terms") }),
  }
);

const model = new ChatOpenRouter({
  model: "anthropic/claude-sonnet-4-6",
  apiKey: process.env.OPENROUTER_API_KEY,
});

const modelWithTools = model.bindTools([search]);
const response = await modelWithTools.invoke("Search for TypeScript news");
const toolResult = await search.invoke(response.tool_calls[0].args);
```

## Quick start B — createAgent

The v1 standard for building agents. Built on LangGraph under the hood.

```typescript
import { createAgent } from "langchain";
import { tool } from "@langchain/core/tools";
import { MemorySaver } from "@langchain/langgraph";
import { z } from "zod";

const calculator = tool(
  ({ expression }) => String(Function(`"use strict"; return (${expression})`)()),
  {
    name: "calculator",
    description: "Evaluate math expressions",
    schema: z.object({ expression: z.string() }),
  }
);

const agent = createAgent({
  model,
  tools: [calculator],
  prompt: "You are a helpful assistant.",
  checkpointer: new MemorySaver(),
});

const result = await agent.invoke(
  { messages: [{ role: "user", content: "What is 15 * 23 + 7?" }] },
  { configurable: { thread_id: "user-123" } }
);
```

### Structured output with createAgent

```typescript
import { createAgent, ToolStrategy } from "langchain";

const schema = z.object({
  summary: z.string(),
  topics: z.array(z.string()),
  confidence: z.number().min(0).max(1),
});

const agent = createAgent({
  model,
  tools: [search],
  responseFormat: ToolStrategy.fromSchema(schema),
  prompt: "Search and return structured results.",
});

const result = await agent.invoke({ messages: [{ role: "user", content: "..." }] });
result.structuredResponse; // typed: { summary, topics, confidence }
```

### Middleware stack

```typescript
import {
  createAgent, modelRetryMiddleware, modelFallbackMiddleware,
  toolCallLimitMiddleware, dynamicSystemPromptMiddleware,
} from "langchain";

const agent = createAgent({
  model: primaryModel,
  tools,
  middleware: [
    modelRetryMiddleware({ maxRetries: 3 }),
    modelFallbackMiddleware(fallbackModel),
    toolCallLimitMiddleware({ runLimit: 10 }),
    dynamicSystemPromptMiddleware(async (state) =>
      `You are helpful. Time: ${new Date().toISOString()}`
    ),
  ],
});
```

## Quick start C — LangGraph StateGraph

```typescript
import { StateGraph, MessagesAnnotation, START, END, MemorySaver } from "@langchain/langgraph";
import { ToolNode, toolsCondition } from "@langchain/langgraph/prebuilt";
import { HumanMessage } from "@langchain/core/messages";

const tools = [calculator, search];
const modelWithTools = model.bindTools(tools);

async function callAgent(state: typeof MessagesAnnotation.State) {
  const response = await modelWithTools.invoke(state.messages);
  return { messages: [response] };
}

const graph = new StateGraph(MessagesAnnotation)
  .addNode("agent", callAgent)
  .addNode("tools", new ToolNode(tools))
  .addEdge(START, "agent")
  .addConditionalEdges("agent", toolsCondition)
  .addEdge("tools", "agent");

const app = graph.compile({ checkpointer: new MemorySaver() });

const result = await app.invoke(
  { messages: [new HumanMessage("What is 7 * 8?")] },
  { configurable: { thread_id: "t1" } }
);
```

### Custom state + conditional routing

```typescript
import { Annotation, StateGraph, START, END } from "@langchain/langgraph";

const MyState = Annotation.Root({
  input: Annotation<string>,
  category: Annotation<string>,
  result: Annotation<string>,
});

function route(state: typeof MyState.State): string {
  return state.category.includes("math") ? "handleMath" : "handleGeneral";
}

const graph = new StateGraph(MyState)
  .addNode("classify", classifyNode)
  .addNode("handleMath", mathNode)
  .addNode("handleGeneral", generalNode)
  .addEdge(START, "classify")
  .addConditionalEdges("classify", route)
  .addEdge("handleMath", END)
  .addEdge("handleGeneral", END);
```

### Human-in-the-loop with interrupt()

```typescript
import { interrupt, Command, MemorySaver } from "@langchain/langgraph";

const approvalNode = async (state) => {
  const answer = interrupt({ question: "Approve?", options: ["yes", "no"] });
  return { approved: answer === "yes" };
};

const result1 = await app.invoke(input, config);
const result2 = await app.invoke(new Command({ resume: "yes" }), config);
```

## Quick start D — RAG chain (LCEL)

```typescript
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { RunnablePassthrough, RunnableLambda, RunnableSequence } from "@langchain/core/runnables";
import { StringOutputParser } from "@langchain/core/output_parsers";
import { RecursiveCharacterTextSplitter } from "@langchain/textsplitters";
import { Document } from "@langchain/core/documents";

const splitter = new RecursiveCharacterTextSplitter({ chunkSize: 1000, chunkOverlap: 200 });
const docs = await splitter.createDocuments([text], [{ source: "doc.pdf" }]);

function retrieve(query: string): Document[] { /* your retrieval logic */ }
function formatDocs(docs: Document[]): string {
  return docs.map((d, i) => `[${i + 1}] ${d.pageContent}`).join("\n\n");
}

const ragChain = RunnableSequence.from([
  RunnablePassthrough.assign({
    context: new RunnableLambda({
      func: (input: { question: string }) => formatDocs(retrieve(input.question)),
    }),
  }),
  ChatPromptTemplate.fromMessages([
    ["system", "Answer from context only:\n{context}"],
    ["human", "{question}"],
  ]),
  model,
  new StringOutputParser(),
]);

const answer = await ragChain.invoke({ question: "What is LCEL?" });
```

## Streaming

```typescript
// Agent node-level streaming
const stream = await agent.stream(
  { messages: [{ role: "user", content: "Hello" }] },
  { streamMode: "updates" }
);
for await (const chunk of stream) { /* { nodeName: { messages } } */ }

// Token-level streaming
const stream = agent.streamEvents(
  { messages: [{ role: "user", content: "Hello" }] },
  { version: "v2" }
);
for await (const event of stream) {
  if (event.event === "on_chat_model_stream") {
    process.stdout.write(event.data?.chunk?.content || "");
  }
}

// LCEL chain streaming
const stream = await chain.stream({ input: "Hello" });
for await (const chunk of stream) { process.stdout.write(chunk); }
```

## Antipatterns

Never do these. Full list with code examples in `references/antipatterns.md`.

| Don't | Do instead | Why |
|-------|-----------|-----|
| `import { LLMChain } from "langchain/chains"` | `createAgent` or LCEL `.pipe()` | Removed in v1 |
| `new ConversationBufferMemory()` | `MemorySaver` checkpointer | Legacy, unmaintained |
| `new ToolStrategy(schema)` | `ToolStrategy.fromSchema(schema)` | Constructor API differs |
| `providerStrategy` with OpenRouter | `toolStrategy` | Multi-model routing breaks it |
| `ChatOpenAI({ baseURL: "openrouter..." })` | `ChatOpenRouter({ model, apiKey })` | Dedicated package |
| `modelFallbackMiddleware({ models: [m] })` | `modelFallbackMiddleware(m1, m2)` | Spread args, not object |
| `{ maxToolCalls: 5 }` | `{ runLimit: 5 }` or `{ threadLimit: 10 }` | Wrong parameter name |
| Resume interrupt with plain object | `new Command({ resume: value })` | Must use Command class |
| LangChain for simple single-provider chat | Provider SDK or Vercel AI SDK | ~500KB overhead, zero value |
| Complex nested Zod schemas in tools | Flat schemas | Deep nesting unreliable |
| Zod v4 in middleware `stateSchema` | Zod v3 for stateSchema | Bug #9299 |

## Import reference

```typescript
import { createAgent, createMiddleware, ToolStrategy } from "langchain";
import { modelRetryMiddleware, modelFallbackMiddleware } from "langchain";
import { toolCallLimitMiddleware, toolRetryMiddleware } from "langchain";
import { dynamicSystemPromptMiddleware, summarizationMiddleware } from "langchain";
import { humanInTheLoopMiddleware, tool, trimMessages } from "langchain";

import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";
import { RunnableSequence, RunnableParallel, RunnableLambda } from "@langchain/core/runnables";
import { RunnablePassthrough, RunnableBranch } from "@langchain/core/runnables";
import { HumanMessage, AIMessage, SystemMessage, ToolMessage } from "@langchain/core/messages";
import { Document } from "@langchain/core/documents";

import { StateGraph, Annotation, MessagesAnnotation, START, END } from "@langchain/langgraph";
import { MemorySaver, InMemoryStore, interrupt, Command } from "@langchain/langgraph";
import { ToolNode, toolsCondition } from "@langchain/langgraph/prebuilt";
import { entrypoint, task } from "@langchain/langgraph";

import { ChatOpenAI } from "@langchain/openai";
import { ChatOpenRouter } from "@langchain/openrouter";
import { RecursiveCharacterTextSplitter } from "@langchain/textsplitters";
```

## Version requirements

| Package | Min version | Notes |
|---------|------------|-------|
| `langchain` | 1.0.0 | `createAgent`, middleware |
| `@langchain/core` | 1.1.0 | Stable types, Zod v4 support |
| `@langchain/langgraph` | 1.0.0 | StateGraph, functional API |
| `zod` | 3.x or 4.x | v4 works for tools/schemas; use v3 for stateSchema |
| Node.js | 20+ | v18 dropped |
| TypeScript | 5.x | Required for Zod v4 |

Pin all `@langchain/*` versions together. Mismatches cause cryptic errors.

## Python to TypeScript migration

| Python | TypeScript |
|--------|-----------|
| `from langchain_openai import ChatOpenAI` | `import { ChatOpenAI } from "@langchain/openai"` |
| `@tool` decorator with docstring | `tool(fn, { name, description, schema: z.object({}) })` |
| `TypedDict` + `Annotated[list, add_messages]` | `Annotation.Root({ messages: MessagesAnnotation })` |
| `HumanMessage(content="hi")` | `new HumanMessage("hi")` |
| `chain = prompt \| llm \| parser` | `chain = prompt.pipe(llm).pipe(parser)` |
| `config={"configurable": {"thread_id": "t1"}}` | `{ configurable: { thread_id: "t1" } }` |
| Pydantic `BaseModel` | Zod `z.object({})` |
| `create_react_agent` | `createAgent` from `"langchain"` |
| `ConversationBufferMemory` | `MemorySaver` checkpointer |
| `langchain-community` (PyPI) | `@langchain/community` (npm) |

TS advantages: middleware system, edge/browser runtime, Zod type inference.
Python advantages: ~75 more document loaders, `lazy_load()`, LangServe.

## Reference routing

| Document | What it contains | Load when |
|----------|-----------------|-----------|
| `references/pattern-catalog.md` | 47 verified patterns with exact tested TypeScript code, organized by category | You need specific pattern implementation details beyond the quick starts |
| `references/antipatterns.md` | 22 antipatterns with ❌ Don't / ✅ Do / Because format and code examples | You are reviewing or writing LangChain code and need to avoid common mistakes |
| `references/decision-tree.md` | 13 developer intents mapped to specific recommendations with honest alternative assessments | You are choosing an approach for a new task and need full routing guidance |

## Scope boundaries

This skill covers LangChain.js and LangGraph.js in TypeScript only. It does not cover:
- Python LangChain (different APIs and patterns)
- LangSmith setup (set `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY`)
- Database checkpointers (PostgresSaver, SqliteSaver need separate install)
- LangGraph Platform cloud deployment
- Embeddings via OpenRouter (use OpenAI directly)
