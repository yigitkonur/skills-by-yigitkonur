---
name: build-langchain-app
description: Use skill if you are building LLM applications, agents, RAG pipelines, or tool-calling workflows with LangChain.js and LangGraph in TypeScript.
---

# Build LangChain App

Build LLM-powered TypeScript applications with LangChain.js v1 (`langchain@1.2+`, `@langchain/core@1.1+`, `@langchain/langgraph@1.2+`). All patterns verified live against OpenRouter with `anthropic/claude-sonnet-4-6`. TypeScript only.

## Master decision tree

```
What do you need?
│
├── Simple chatbot, single provider?
│   └─► Do NOT use LangChain. Use provider SDK directly or Vercel AI SDK.
│
├── Multi-provider model switching
│   └─► ChatModel abstraction ──────────────────► Quick start A (below)
│       Deep dive ──────────────────────────────► references/agents.md § Model Configuration
│
├── Tool-calling agent
│   ├── Simple (1-5 tools, no state) ──────────► Quick start B — createAgent
│   │   Deep dive ─────────────────────────────► references/agents.md § createAgent
│   │   Tool design guidance ──────────────────► references/tools.md § Tool Design Philosophy
│   │
│   └── Complex (state, cycles, HITL) ────────► Quick start C — LangGraph StateGraph
│       Deep dive ─────────────────────────────► references/langgraph.md § StateGraph
│       HITL patterns ─────────────────────────► references/langgraph.md § Human-in-the-Loop
│
├── Tool design & implementation
│   ├── tool() API, schemas, descriptions ────► references/tools.md § tool() Function
│   ├── Error handling in tools ──────────────► references/tools.md § Error Handling
│   └── MCP tool integration ─────────────────► references/tools.md § MCP Integration
│
├── Structured data extraction
│   ├── On model directly ─────────────────────► model.withStructuredOutput(zodSchema)
│   └── With createAgent ─────────────────────► ToolStrategy.fromSchema(schema) — NOT new ToolStrategy()
│       Deep dive ─────────────────────────────► references/agents.md § Structured Output
│
├── RAG pipeline
│   ├── Do I even need RAG? ──────────────────► references/rag.md § RAG Decision Tree
│   ├── Document loading & splitting ─────────► references/rag.md § Document Loading, Text Splitting
│   ├── Embeddings & vector stores ───────────► references/rag.md § Embeddings, Vector Stores
│   ├── Basic RAG chain ──────────────────────► Quick start D (below)
│   └── Agentic RAG ─────────────────────────► references/rag.md § Agentic RAG
│
├── Memory & persistence
│   ├── Three-layer memory model ─────────────► references/memory.md § Three-Layer Memory Model
│   ├── Thread-scoped conversation ───────────► references/memory.md § Layer 1: MemorySaver
│   ├── Cross-conversation long-term ─────────► references/memory.md § Layer 2: Working Memory
│   ├── Semantic recall (RAG over history) ───► references/memory.md § Layer 3: Semantic Recall
│   └── Auto-summarization / trimming ────────► references/memory.md § trimMessages, summarizationMiddleware
│
├── Streaming to web UI
│   ├── Streaming decision tree ──────────────► references/streaming.md § Streaming Decision Tree
│   ├── Simple chat token stream ─────────────► references/streaming.md § LCEL Chain Streaming
│   ├── Agent streams with tool calls ────────► references/streaming.md § Agent Streaming Modes
│   ├── Next.js + Vercel AI SDK ──────────────► references/streaming.md § Next.js Route Handler
│   └── streamEvents v2 ─────────────────────► references/streaming.md § streamEvents v2
│
├── Multi-agent systems
│   ├── Do I need multi-agent? ───────────────► references/multi-agent.md § Do You Need Multi-Agent?
│   ├── Supervisor pattern ───────────────────► references/multi-agent.md § Supervisor Pattern
│   ├── Swarm pattern (peer-to-peer) ────────► references/multi-agent.md § Swarm Pattern
│   └── Agent-as-tool ────────────────────────► references/multi-agent.md § Agent-as-Tool
│
├── LangGraph deep dive
│   ├── StateGraph, nodes, edges ─────────────► references/langgraph.md § StateGraph
│   ├── Custom state (Annotation.Root) ───────► references/langgraph.md § Custom State
│   ├── Conditional routing ──────────────────► references/langgraph.md § Conditional Edges
│   ├── Checkpointing & time-travel ─────────► references/langgraph.md § Checkpointing
│   ├── Functional API (entrypoint/task) ────► references/langgraph.md § Functional API
│   └── Subgraphs ────────────────────────────► references/langgraph.md § Subgraphs
│
├── Production middleware
│   ├── Full middleware reference ─────────────► references/middleware.md
│   ├── Retry on failure ─────────────────────► references/middleware.md § modelRetryMiddleware
│   ├── Model fallback ───────────────────────► references/middleware.md § modelFallbackMiddleware
│   ├── Rate limiting ────────────────────────► references/middleware.md § toolCallLimitMiddleware
│   ├── Human approval ───────────────────────► references/middleware.md § humanInTheLoopMiddleware
│   └── Custom middleware ────────────────────► references/middleware.md § Custom Middleware
│
├── LCEL composition patterns
│   └─► references/pattern-catalog.md § LCEL — pipe, parallel, lambda, passthrough, branch, batch
│
├── Observability & debugging
│   ├── LangSmith setup & tracing ────────────► references/observability.md § LangSmith Setup
│   ├── Langfuse alternative ─────────────────► references/observability.md § Langfuse
│   ├── Custom callbacks ────────────────────► references/observability.md § Custom Callbacks
│   └── Cost tracking ───────────────────────► references/observability.md § Cost Tracking
│
├── Troubleshooting
│   ├── Import errors ────────────────────────► references/common-errors.md § Import Errors
│   ├── Runtime errors ───────────────────────► references/common-errors.md § Runtime Errors
│   ├── State errors ─────────────────────────► references/common-errors.md § State Errors
│   └── Performance issues ──────────────────► references/common-errors.md § Performance Issues
│
├── Python → TypeScript migration
│   └─► Migration table (below)
│
├── Full pattern reference (47 patterns)
│   └─► references/pattern-catalog.md
│
├── What NOT to do (22 antipatterns)
│   └─► references/antipatterns.md
│
└── Full intent-based routing (13 intents)
    └─► references/decision-tree.md
```

## Required packages

```bash
npm install langchain @langchain/core @langchain/openai @langchain/langgraph zod
# For OpenRouter:
npm install @langchain/openrouter
# For multi-agent:
npm install @langchain/langgraph-supervisor @langchain/langgraph-swarm
# For text splitting (RAG):
npm install @langchain/textsplitters
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
- `withStructuredOutput()` works on direct calls. Intermittent when piped from templates — use prompt+parse lambda workaround (references/pattern-catalog.md § LCEL 6).
- Streaming, tool calling, batch all work.
- Embeddings NOT supported via OpenRouter — use OpenAI directly for embeddings.

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

For full tool design guidance: `references/tools.md`

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

For full parameter reference, streaming modes, structured output: `references/agents.md`

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

For all 11 built-in middleware, custom middleware, hook execution order: `references/middleware.md`

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

For custom state, conditional routing, checkpointing, functional API, subgraphs, streaming: `references/langgraph.md`

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

For full HITL patterns, time-travel debugging: `references/langgraph.md § Human-in-the-Loop`

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

For chunking strategies, embedding selection, vector store comparison, agentic RAG, quality checklist: `references/rag.md`

## Memory quick reference

```
┌──────────────────────────────────────────────────────────┐
│ Layer 3: Semantic Recall (RAG over past conversations)   │
│   → Vector store of past interactions                    │
├──────────────────────────────────────────────────────────┤
│ Layer 2: Working Memory (key-value store)                │
│   → InMemoryStore / database-backed store                │
├──────────────────────────────────────────────────────────┤
│ Layer 1: Conversation Window (short-term)                │
│   → MemorySaver checkpointer (thread_id scoped)          │
└──────────────────────────────────────────────────────────┘
```

```typescript
// Layer 1 — conversation persistence
import { MemorySaver } from "@langchain/langgraph";
const checkpointer = new MemorySaver(); // dev only
const agent = createAgent({ model, tools, checkpointer });
await agent.invoke(input, { configurable: { thread_id: "user-123" } });

// Layer 2 — cross-conversation working memory
import { InMemoryStore } from "@langchain/langgraph";
const store = new InMemoryStore();
await store.put(["users", "user-123"], "profile", { name: "Alice", plan: "pro" });
const items = await store.search(["users", "user-123"]);
```

For full three-layer architecture, trimMessages, summarizationMiddleware, production persistence: `references/memory.md`

## Streaming quick reference

```typescript
// Agent node-level streaming
const stream = await agent.stream(
  { messages: [{ role: "user", content: "Hello" }] },
  { streamMode: "updates" }
);
for await (const chunk of stream) { /* { nodeName: { messages } } */ }

// Token-level streaming via streamEvents
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

// Next.js + Vercel AI SDK bridge
import { LangChainAdapter } from "ai";
export async function POST(req: Request) {
  const stream = await agent.stream(input, { streamMode: "messages" });
  return LangChainAdapter.toDataStreamResponse(stream);
}
```

For full streaming decision tree, all 5 stream modes, batch processing: `references/streaming.md`

## Multi-agent quick reference

```typescript
// Supervisor pattern — one coordinator delegates to specialist agents
import { createSupervisor } from "@langchain/langgraph-supervisor";

const supervisor = await createSupervisor({
  agents: [researchAgent, writerAgent],
  model,
  prompt: "Coordinate research and writing tasks.",
});
const app = supervisor.compile();

// Swarm pattern — peer-to-peer handoffs
import { createSwarm } from "@langchain/langgraph-swarm";

const swarm = createSwarm({
  agents: [triageAgent, billingAgent, techAgent],
  defaultActiveAgent: "triage",
});
const app = swarm.compile();
```

For decision tree, pattern comparison, agent-as-tool, failure handling: `references/multi-agent.md`

## Antipatterns — critical mistakes

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

For all 22 antipatterns with full ❌/✅/Because code examples: `references/antipatterns.md`

## Import reference

```typescript
// langchain (v1 high-level)
import { createAgent, createMiddleware, ToolStrategy } from "langchain";
import { modelRetryMiddleware, modelFallbackMiddleware } from "langchain";
import { toolCallLimitMiddleware, toolRetryMiddleware } from "langchain";
import { dynamicSystemPromptMiddleware, summarizationMiddleware } from "langchain";
import { humanInTheLoopMiddleware, tool, trimMessages } from "langchain";

// @langchain/core
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";
import { RunnableSequence, RunnableParallel, RunnableLambda } from "@langchain/core/runnables";
import { RunnablePassthrough, RunnableBranch } from "@langchain/core/runnables";
import { HumanMessage, AIMessage, SystemMessage, ToolMessage } from "@langchain/core/messages";
import { Document } from "@langchain/core/documents";

// @langchain/langgraph
import { StateGraph, Annotation, MessagesAnnotation, START, END } from "@langchain/langgraph";
import { MemorySaver, InMemoryStore, interrupt, Command } from "@langchain/langgraph";
import { ToolNode, toolsCondition } from "@langchain/langgraph/prebuilt";
import { entrypoint, task } from "@langchain/langgraph";

// Multi-agent
import { createSupervisor } from "@langchain/langgraph-supervisor";
import { createSwarm } from "@langchain/langgraph-swarm";

// Providers
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
| `@langchain/langgraph-supervisor` | 1.0.0 | createSupervisor |
| `@langchain/langgraph-swarm` | 1.0.0 | createSwarm |
| `@langchain/openrouter` | 0.1.6 | Dedicated OpenRouter support |
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
| `from langgraph.prebuilt import create_react_agent` | `import { createAgent } from "langchain"` |
| `from langgraph.graph import StateGraph` | `import { StateGraph } from "@langchain/langgraph"` |

TS advantages: middleware system, edge/browser runtime, Zod type inference, createAgent convenience.
Python advantages: ~75 more document loaders, `lazy_load()`, LangServe, broader community ecosystem.

## Observability quick reference

```bash
# Enable automatic tracing — zero code changes
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY="lsv2_pt_..."
export LANGSMITH_PROJECT="my-project"
```

```typescript
// Manual tracing for custom functions
import { traceable } from "langsmith";

const myFunc = traceable(async (input: string) => {
  // your logic — automatically traced in LangSmith
  return result;
}, { name: "my-custom-function" });
```

For LangSmith setup, Langfuse alternative, custom callbacks, cost tracking, debugging workflow: `references/observability.md`

## Common errors quick lookup

| Error | Cause | Fix |
|-------|-------|-----|
| `Cannot find module 'langchain/chains'` | Legacy chains removed in v1 | Use `createAgent` or LCEL |
| `createReactAgent is deprecated` | Old API | Use `createAgent` from `"langchain"` |
| `Tool input did not match expected schema` | Zod schema mismatch | Check `.describe()` on all fields |
| `Cannot read properties of undefined (reading 'messages')` | Missing MessagesAnnotation | Use `MessagesAnnotation` or custom `Annotation.Root` |
| `Checkpoint not found` | Missing checkpointer | Add `checkpointer: new MemorySaver()` to compile() |
| `@langchain/core version mismatch` | Pinning issue | Pin all `@langchain/*` to same minor version |

For all 18 errors with full Error→Cause→Fix format: `references/common-errors.md`

## Reference routing

| Document | Lines | What it contains | Load when |
|----------|-------|-----------------|-----------|
| `references/agents.md` | 692 | createAgent full parameter reference, model config, system prompts, structured output, MemorySaver, streaming modes, ReAct lifecycle, middleware integration | Building an agent with createAgent |
| `references/tools.md` | 613 | Tool design philosophy, tool() API, schema design, descriptions, multi-tool selection, error handling, MCP integration, 6 common bugs | Designing or debugging tools |
| `references/langgraph.md` | 1014 | StateGraph, MessagesAnnotation, Annotation.Root, reducers, nodes, edges, conditional routing, checkpointing, HITL with interrupt/Command, functional API, streaming, subgraphs, time-travel | Building custom graphs or complex workflows |
| `references/multi-agent.md` | 918 | Decision tree, Supervisor with createSupervisor, Swarm with createSwarm, agent-as-tool, communication patterns, failure handling, production patterns | Coordinating multiple agents |
| `references/rag.md` | 743 | RAG decision tree, document loaders, text splitters, chunking strategies, embeddings, vector stores with decision matrix, RAG chain patterns, agentic RAG, quality checklist | Building retrieval-augmented generation |
| `references/memory.md` | 734 | Three-layer memory model, MemorySaver, PostgresSaver, InMemoryStore CRUD, semantic recall, trimMessages, summarizationMiddleware, production architecture | Adding memory or persistence |
| `references/streaming.md` | 701 | Streaming decision tree, agent streaming modes, streamEvents v2, LCEL chain.stream(), LangGraph streaming, Next.js integration, Vercel AI SDK bridge, batch processing | Streaming responses to UI |
| `references/middleware.md` | 639 | All 11 built-in middleware with APIs, custom middleware via createMiddleware, hook execution order, error/fallback/logging patterns, composition, interrupt/Command flow | Adding middleware to agents |
| `references/observability.md` | 590 | LangSmith setup, automatic tracing, manual traceable/wrapOpenAI, evaluation, Langfuse alternative, verbose mode, custom callbacks, production metrics, cost tracking | Setting up tracing or debugging |
| `references/common-errors.md` | 507 | 4 import errors, 8 runtime errors, 3 state errors, 3 performance issues, all with Error→Cause→Fix format, quick lookup table | Debugging errors |
| `references/pattern-catalog.md` | 1992 | 47 verified patterns with exact tested TypeScript code across 7 categories (primitives, agents, LangGraph, LCEL, RAG/memory, production middleware, advanced) | Need specific implementation code |
| `references/antipatterns.md` | 547 | 22 antipatterns with ❌ Don't / ✅ Do / Because format and full code examples | Reviewing code or avoiding mistakes |
| `references/decision-tree.md` | 536 | 13 developer intents mapped to specific recommendations with honest alternative assessments | Choosing approach for a new task |

## Scope boundaries

This skill covers LangChain.js and LangGraph.js in TypeScript only. It does not cover:
- Python LangChain (different APIs and patterns)
- Database checkpointers beyond setup guidance (PostgresSaver, SqliteSaver need separate install)
- LangGraph Platform cloud deployment
- Embeddings via OpenRouter (use OpenAI directly)
- LangServe (Python-only)
