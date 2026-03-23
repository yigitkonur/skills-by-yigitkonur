---
name: build-langchain-ts-app
description: Use skill if you are building TypeScript agents, RAG pipelines, or tool-calling workflows with LangChain.js and LangGraph.
---

# Build LangChain TypeScript App

Build LLM-powered TypeScript applications with LangChain.js v1 (`langchain@1.2+`, `@langchain/core@1.1+`, `@langchain/langgraph@1.2+`). All patterns verified against current packages. TypeScript only.

## Master decision tree

```
What do you need?
│
├── Simple chatbot, single provider?
│   └─► Do NOT use LangChain. Use provider SDK directly or Vercel AI SDK.
│
├── Model selection & provider setup
│   ├── Which model/provider for my use case? ──────► references/models.md § Provider Selection
│   ├── Multi-provider model switching ─────────────► references/providers.md § initChatModel
│   ├── Provider feature comparison matrix ─────────► references/providers.md § Feature Matrix
│   └── OpenRouter setup ──────────────────────────► OpenRouter section (below)
│
├── Tool-calling agent
│   ├── Simple (1-5 tools, no state) ──────────────► Quick start B — createAgent
│   │   Deep dive ─────────────────────────────────► references/agents.md § createAgent
│   │   Tool design guidance ──────────────────────► references/tools.md § Tool Design
│   │
│   └── Complex (state, cycles, HITL) ────────────► Quick start C — LangGraph StateGraph
│       Deep dive ─────────────────────────────────► references/langgraph.md § StateGraph
│       HITL patterns ─────────────────────────────► references/human-in-the-loop.md
│
├── Tool design & implementation
│   ├── tool() API, schemas, descriptions ─────────► references/tools.md § tool() Function
│   ├── Error handling in tools ───────────────────► references/tools.md § Error Handling
│   └── MCP tool integration ──────────────────────► references/mcp.md § MultiServerMCPClient
│
├── Structured data extraction
│   ├── withStructuredOutput on model ─────────────► references/structured-output.md § withStructuredOutput
│   ├── providerStrategy vs toolStrategy ──────────► references/structured-output.md § Strategy Comparison
│   ├── With createAgent responseFormat ───────────► references/agents.md § Structured Output
│   └── Provider-specific bugs & workarounds ──────► references/structured-output.md § Provider Bugs
│
├── RAG pipeline
│   ├── Do I even need RAG? ───────────────────────► references/rag.md § RAG Decision Tree
│   ├── Document loading & splitting ──────────────► references/rag.md § Document Loading
│   ├── Embeddings & vector stores ────────────────► references/rag.md § Embeddings, Vector Stores
│   ├── Basic RAG chain ───────────────────────────► Quick start D (below)
│   └── Agentic RAG ──────────────────────────────► references/rag.md § Agentic RAG
│
├── Memory & persistence
│   ├── Thread-scoped conversation ────────────────► references/memory-checkpointers.md § Checkpointers
│   ├── trimMessages / filterMessages ─────────────► references/memory-checkpointers.md § Message Management
│   ├── Auto-summarization ────────────────────────► references/memory-checkpointers.md § Summarization
│   ├── Long-term memory (BaseStore) ──────────────► references/memory-stores.md § BaseStore API
│   ├── Semantic recall / caching ─────────────────► references/memory-stores.md § Caching
│   ├── GDPR compliance ───────────────────────────► references/memory-stores.md § GDPR
│   └── Legacy memory migration ───────────────────► references/memory-stores.md § Legacy Migration
│
├── Streaming to web UI
│   ├── Agent streaming (8 modes) ─────────────────► references/streaming.md § Stream Modes
│   ├── Token-by-token streaming ──────────────────► references/streaming.md § Token Streaming
│   ├── streamEvents v2 (17 event types) ──────────► references/streaming.md § streamEvents v2
│   ├── Next.js + Vercel AI SDK ───────────────────► references/streaming.md § Vercel AI SDK
│   └── LCEL chain streaming ──────────────────────► references/streaming.md § LCEL Streaming
│
├── Human-in-the-loop
│   ├── interrupt() / Command resume ──────────────► references/human-in-the-loop.md § interrupt API
│   ├── Tool approval workflows ───────────────────► references/human-in-the-loop.md § Tool Approval
│   ├── RBAC integration ──────────────────────────► references/human-in-the-loop.md § RBAC
│   └── Async approval (webhook, Slack) ───────────► references/human-in-the-loop.md § Async Approval
│
├── Multi-agent systems
│   ├── Do I need multi-agent? ────────────────────► references/multi-agent.md § Decision Guide
│   ├── Supervisor pattern ────────────────────────► references/multi-agent.md § Supervisor
│   ├── Swarm pattern (peer-to-peer) ─────────────► references/multi-agent.md § Swarm
│   ├── Agent-as-tool ─────────────────────────────► references/multi-agent.md § Agent-as-Tool
│   ├── Handoffs with Command ─────────────────────► references/multi-agent.md § Handoffs
│   └── Router / skills workflow ──────────────────► references/multi-agent.md § Router Pattern
│
├── MCP (Model Context Protocol)
│   ├── MultiServerMCPClient setup ────────────────► references/mcp.md § MultiServerMCPClient
│   ├── Transports (stdio, SSE, HTTP) ─────────────► references/mcp.md § Transports
│   ├── OAuth integration ─────────────────────────► references/mcp.md § OAuth
│   └── MCP + createAgent integration ─────────────► references/mcp.md § Agent Integration
│
├── LangGraph deep dive
│   ├── StateGraph, nodes, edges ──────────────────► references/langgraph.md § StateGraph
│   ├── 4 state channel types ─────────────────────► references/langgraph.md § State Channels
│   ├── Custom state (Annotation.Root) ────────────► references/langgraph.md § Custom State
│   ├── Conditional routing ───────────────────────► references/langgraph.md § Conditional Edges
│   ├── Functional API (entrypoint/task) ──────────► references/langgraph.md § Functional API
│   ├── Graph vs Functional API comparison ────────► references/langgraph.md § API Comparison
│   ├── Subgraphs ─────────────────────────────────► references/langgraph.md § Subgraphs
│   └── Command and Send patterns ─────────────────► references/langgraph.md § Command & Send
│
├── LangGraph execution & persistence
│   ├── Checkpointer architecture ─────────────────► references/langgraph-execution.md § Checkpointers
│   ├── Thread management ─────────────────────────► references/langgraph-execution.md § Threads
│   ├── State snapshot & replay ───────────────────► references/langgraph-execution.md § Time Travel
│   └── Parallel node execution ───────────────────► references/langgraph-execution.md § Parallel Execution
│
├── Knowledge agents
│   ├── SQL agent (safe querying) ─────────────────► references/knowledge-agents.md § SQL Agent
│   ├── Voice pipeline ────────────────────────────► references/knowledge-agents.md § Voice Pipeline
│   └── Multi-KB routing ──────────────────────────► references/knowledge-agents.md § Multi-KB Routing
│
├── Production middleware
│   ├── All 14 built-in middleware ─────────────────► references/middleware-catalog.md § Built-in Catalog
│   ├── 6 hook types & execution order ────────────► references/middleware-catalog.md § Hook Types
│   ├── Custom middleware (createMiddleware) ───────► references/middleware-patterns.md § createMiddleware
│   ├── Guardrails & PII filtering ────────────────► references/middleware-patterns.md § Guardrails
│   └── Runtime context (contextSchema) ───────────► references/middleware-patterns.md § Runtime Context
│
├── Deployment & infrastructure
│   ├── LangGraph Studio setup ────────────────────► references/deployment-local.md § LangGraph Studio
│   ├── CLI commands (dev, up, build) ─────────────► references/deployment-local.md § CLI Reference
│   ├── langgraph.json schema ─────────────────────► references/deployment-local.md § Config Schema
│   ├── Docker & Cloud deployment ─────────────────► references/deployment-production.md § Docker
│   ├── Self-hosted (Express/Fastify/Next.js) ─────► references/deployment-production.md § Self-Hosted
│   ├── Generative UI ─────────────────────────────► references/deployment-production.md § Generative UI
│   └── Pricing ───────────────────────────────────► references/deployment-production.md § Pricing
│
├── Observability & debugging
│   ├── LangSmith setup & tracing ─────────────────► references/observability-tracing.md § LangSmith Setup
│   ├── Callbacks (19 types) ──────────────────────► references/observability-tracing.md § Callbacks
│   ├── Custom callback handlers ──────────────────► references/observability-tracing.md § Custom Handlers
│   ├── Cost tracking ─────────────────────────────► references/observability-tracing.md § Cost Tracking
│   ├── LangSmith evaluation ──────────────────────► references/observability-evaluation.md § Evaluation
│   ├── OpenTelemetry integration ─────────────────► references/observability-evaluation.md § OpenTelemetry
│   └── Pricing ───────────────────────────────────► references/observability-evaluation.md § Pricing
│
├── Troubleshooting
│   ├── Import / module errors ────────────────────► references/common-errors.md § Import Errors
│   ├── Tool & structured output bugs ─────────────► references/common-errors.md § Tool Errors
│   ├── Streaming gotchas ─────────────────────────► references/common-errors.md § Streaming Errors
│   ├── LangGraph state & execution ───────────────► references/common-errors.md § LangGraph Errors
│   ├── Provider-specific issues ──────────────────► references/common-errors.md § Provider Errors
│   └── Antipatterns catalog ──────────────────────► references/common-errors.md § Antipatterns
│
└── Python → TypeScript migration
    └─► Migration table (below)
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
# For MCP integration:
npm install @langchain/mcp-adapters
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
- `withStructuredOutput()` works on direct calls. Intermittent when piped from templates.
- Streaming, tool calling, batch all work.
- Embeddings NOT supported via OpenRouter — use OpenAI directly for embeddings.

For full provider comparison and feature matrix: `references/providers.md`

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

For withStructuredOutput, parser catalog, provider-specific bugs: `references/structured-output.md`

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

For all 14 built-in middleware: `references/middleware-catalog.md`. Custom middleware, guardrails: `references/middleware-patterns.md`

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

For custom state, 4 channel types, Command/Send, functional API, subgraphs: `references/langgraph.md`

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

For full HITL patterns, RBAC, async approval, UI integration: `references/human-in-the-loop.md`

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

For chunking strategies, embedding selection, vector store comparison, agentic RAG: `references/rag.md`

## MCP quick reference

```typescript
import { MultiServerMCPClient } from "@langchain/mcp-adapters";

const client = new MultiServerMCPClient({
  servers: {
    filesystem: {
      transport: "stdio",
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
    },
    weather: {
      transport: "sse",
      url: "http://localhost:3001/sse",
    },
  },
});

const tools = await client.getTools();
const agent = createAgent({ model, tools });
```

For full MCP patterns, OAuth, transports, lifecycle management: `references/mcp.md`

## Memory quick reference

```
┌──────────────────────────────────────────────────────────┐
│ Long-term: BaseStore (cross-conversation, GDPR-ready)    │
│   → InMemoryStore / PostgresStore / RedisStore           │
├──────────────────────────────────────────────────────────┤
│ Short-term: Checkpointers (thread-scoped)                │
│   → MemorySaver (dev) / PostgresSaver / RedisSaver       │
├──────────────────────────────────────────────────────────┤
│ Caching: Semantic + exact-match                          │
│   → InMemoryCache / RedisCache (semantic: 0.85 threshold)│
└──────────────────────────────────────────────────────────┘
```

```typescript
// Checkpointer — conversation persistence
import { MemorySaver } from "@langchain/langgraph";
const checkpointer = new MemorySaver(); // dev only
const agent = createAgent({ model, tools, checkpointer });
await agent.invoke(input, { configurable: { thread_id: "user-123" } });

// Long-term memory — cross-conversation
import { InMemoryStore } from "@langchain/langgraph";
const store = new InMemoryStore();
await store.put(["users", "user-123"], "profile", { name: "Alice", plan: "pro" });
const items = await store.search(["users", "user-123"]);
```

**Warning:** InMemoryCache + InMemorySaver used together causes silent data loss. Use Redis for both in production.

For checkpointer setup, trimMessages: `references/memory-checkpointers.md`. For BaseStore, caching, GDPR: `references/memory-stores.md`

## Streaming quick reference

```typescript
// Agent streaming — 8 modes available
const stream = await agent.stream(
  { messages: [{ role: "user", content: "Hello" }] },
  { streamMode: "updates" }
);
for await (const chunk of stream) { /* { nodeName: { messages } } */ }

// Token-level streaming via streamEvents v2
const stream = agent.streamEvents(
  { messages: [{ role: "user", content: "Hello" }] },
  { version: "v2" }
);
for await (const event of stream) {
  if (event.event === "on_chat_model_stream") {
    process.stdout.write(event.data?.chunk?.content || "");
  }
}

// Next.js + Vercel AI SDK bridge
import { LangChainAdapter } from "ai";
export async function POST(req: Request) {
  const stream = await agent.stream(input, { streamMode: "messages" });
  return LangChainAdapter.toDataStreamResponse(stream);
}
```

**Warning:** `withStructuredOutput` streaming is broken — use `streamEvents` v2 workaround.

For all 8 stream modes, 17 event types, framework integrations: `references/streaming.md`

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

For 4 architecture patterns, handoffs with Command, routing strategies, τ-bench: `references/multi-agent.md`

## Antipatterns — critical mistakes

Full catalog with code examples in `references/common-errors.md § Antipatterns`.

| Don't | Do instead | Why |
|-------|-----------|-----|
| `import { LLMChain } from "langchain/chains"` | `createAgent` or LCEL `.pipe()` | Removed in v1 |
| `new ConversationBufferMemory()` | `MemorySaver` checkpointer | Legacy, unmaintained |
| `new ToolStrategy(schema)` | `ToolStrategy.fromSchema(schema)` | Constructor API differs |
| `providerStrategy` with OpenRouter | `toolStrategy` | Multi-model routing breaks it |
| `ChatOpenAI({ baseURL: "openrouter..." })` | `ChatOpenRouter({ model, apiKey })` | Dedicated package |
| `modelFallbackMiddleware({ models: [m] })` | `modelFallbackMiddleware(m1, m2)` | Spread args, not object |
| Resume interrupt with plain object | `new Command({ resume: value })` | Must use Command class |
| Zod v4 in middleware `stateSchema` | Zod v3 for stateSchema | Type inference broken |
| `withStructuredOutput` + `.stream()` | `streamEvents` v2 workaround | Known bug |
| Deep nested Zod schemas in tools | Flat schemas | Deep nesting unreliable |
| DeepSeek R1 for tool calling | Use DeepSeek V3 or other models | R1 has no tool support |
| `InMemoryCache` + `InMemorySaver` | Redis for both cache and saver | Silent data loss |

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

// MCP
import { MultiServerMCPClient } from "@langchain/mcp-adapters";

// Providers
import { ChatOpenAI } from "@langchain/openai";
import { ChatAnthropic } from "@langchain/anthropic";
import { ChatOpenRouter } from "@langchain/openrouter";
import { ChatGoogleGenerativeAI } from "@langchain/google-genai";
import { initChatModel } from "langchain/chat_models/universal";
import { RecursiveCharacterTextSplitter } from "@langchain/textsplitters";
```

## Version requirements

| Package | Min version | Notes |
|---------|------------|-------|
| `langchain` | 1.2.0 | `createAgent`, middleware, `initChatModel` |
| `@langchain/core` | 1.1.0 | Stable types, Runnable interface |
| `@langchain/langgraph` | 1.2.0 | StateGraph, functional API, 8 stream modes |
| `@langchain/langgraph-supervisor` | 1.0.0 | createSupervisor |
| `@langchain/langgraph-swarm` | 1.0.0 | createSwarm |
| `@langchain/openrouter` | 0.1.6 | First-party OpenRouter support (Feb 2026) |
| `@langchain/mcp-adapters` | latest | MCP tool integration |
| `zod` | 3.x | v4 type inference broken — stay on v3 |
| Node.js | 20+ | v18 dropped |
| TypeScript | 5.x | Required |

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

LangSmith Deployment pricing: $0.001/node executed.

For LangSmith tracing, callbacks, cost tracking: `references/observability-tracing.md`. For evaluation, OTEL: `references/observability-evaluation.md`

## Common errors quick lookup

| Error | Cause | Fix |
|-------|-------|-----|
| `Cannot find module 'langchain/chains'` | Legacy chains removed in v1 | Use `createAgent` or LCEL |
| `createReactAgent is deprecated` | Old API (LangGraph < v0.3) | Use `createAgent` from `"langchain"` |
| `Tool input did not match expected schema` | Zod schema mismatch | Check `.describe()` on all fields |
| `Cannot read properties of undefined (reading 'messages')` | Missing MessagesAnnotation | Use `MessagesAnnotation` or custom `Annotation.Root` |
| `Checkpoint not found` | Missing checkpointer | Add `checkpointer: new MemorySaver()` to compile() |
| `@langchain/core version mismatch` | Pinning issue | Pin all `@langchain/*` to same minor version |
| `withStructuredOutput` returns empty | Provider streaming bug | Use `streamEvents` v2 workaround |
| DeepSeek R1 tool calls fail | No tool calling support | Use DeepSeek V3 or another model |

For all errors with full Error→Cause→Fix format, antipatterns catalog: `references/common-errors.md`

## Reference routing

| Document | What it contains | Load when |
|----------|-----------------|-----------|
| `references/agents.md` | createAgent full parameter reference, 9 overloads, model config, structured output, streaming modes, ReAct lifecycle | Building an agent with createAgent |
| `references/models.md` | 15+ provider configs, 14 content block types, fakeModel API, model selection guide | Choosing or configuring chat models |
| `references/providers.md` | 24+ providers, feature matrix, initChatModel universal interface, provider-specific setup | Setting up providers or comparing capabilities |
| `references/tools.md` | tool() factory, schema design, 35+ built-in tools, type hierarchy, error handling, 9 known issues | Designing or debugging tools |
| `references/structured-output.md` | withStructuredOutput, providerStrategy vs toolStrategy, parser catalog, provider-specific bugs | Extracting structured data from models |
| `references/streaming.md` | 8 LangGraph stream modes, 17 event types, streamEvents v2, Vercel AI SDK, Next.js, Express | Streaming responses to UI |
| `references/memory-checkpointers.md` | MemorySaver, PostgresSaver, RedisSaver, trimMessages, summarization, thread management | Thread-scoped conversation memory |
| `references/memory-stores.md` | BaseStore API, InMemoryStore, PostgresStore, caching, GDPR compliance, legacy migration | Long-term memory, caching, compliance |
| `references/middleware-catalog.md` | All 14 built-in middleware with signatures, 6 hook types, execution order | Using built-in middleware |
| `references/middleware-patterns.md` | createMiddleware API, guardrails, PII filtering, runtime context, composition rules | Custom middleware and guardrails |
| `references/mcp.md` | MultiServerMCPClient, stdio/SSE/HTTP transports, OAuth, tool discovery, lifecycle management | Integrating MCP servers |
| `references/human-in-the-loop.md` | interrupt() API, Command resume, RBAC, async approval, useStream UI, tool confirmation | Adding human approval to workflows |
| `references/multi-agent.md` | 4 architecture patterns, handoffs, routing strategies, SubAgent interface, τ-bench benchmarks | Coordinating multiple agents |
| `references/rag.md` | Document loaders, text splitters, embeddings (13+ providers), vector stores (17), retriever types, RAGAS metrics | Building RAG pipelines |
| `references/langgraph.md` | StateGraph, 4 channel types, Graph vs Functional API, Command/Send, subgraphs, conditional routing | Building custom graphs |
| `references/langgraph-execution.md` | Checkpointer architecture, thread management, state serialization, parallel execution, time travel | LangGraph persistence and execution |
| `references/knowledge-agents.md` | SQL agent safety, voice pipelines, multi-KB routing, query validation | Building knowledge-domain agents |
| `references/deployment-local.md` | LangGraph Studio, CLI commands, langgraph.json schema, local dev server, Agent Chat UI | Local development and Studio |
| `references/deployment-production.md` | Docker, Cloud, self-hosted servers, Generative UI, CI/CD, pricing, scaling | Production deployment |
| `references/observability-tracing.md` | LangSmith setup, 19 callback types, tracing, cost tracking, dashboards, alerts | Tracing and monitoring |
| `references/observability-evaluation.md` | LangSmith evaluation, datasets, LLM-as-judge, OpenTelemetry, third-party tools, pricing | Testing and evaluation |
| `references/common-errors.md` | Error catalog by category, antipatterns, v0→v1 migration, provider-specific gotchas | Debugging errors or reviewing code |

## Scope boundaries

This skill covers LangChain.js and LangGraph.js in TypeScript only. It does not cover:
- Python LangChain (different APIs and patterns)
- LangServe (Python-only)
- Embeddings via OpenRouter (use OpenAI directly)
- Database-specific setup beyond connection patterns (PostgresSaver, SqliteSaver need separate install)
