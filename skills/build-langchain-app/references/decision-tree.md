# LangChain.js Decision Tree — "I want to..."

> A routing map from developer intent to the right tool, pattern, and approach.
> Honest about when LangChain adds value and when alternatives are better.
> References point to `pattern-catalog.md` patterns where applicable.

---

## Quick Decision: Do You Even Need LangChain?

```
Is your app single-provider, simple chat only?
  → YES: Skip LangChain. Use provider SDK directly or Vercel AI SDK.
  → NO: Continue below.

Do you need multi-provider switching?
  → YES: LangChain ChatModel abstraction is genuinely useful. Continue.
  → NO: Consider if your use case justifies the dependency.

Do you need complex agent orchestration (cycles, state, human-in-the-loop)?
  → YES: LangGraph.js is the right choice.
  → NO: Consider createAgent for simple tool-calling agents, or skip the framework.
```

---

## "I want to..."

### 1. Build a Simple Chatbot (Single Provider)

**→ Don't use LangChain.** Use the provider SDK directly or Vercel AI SDK.

| Option | Best For |
|--------|----------|
| **OpenAI SDK** (`openai`) | Direct OpenAI usage, maximum control |
| **Anthropic SDK** (`@anthropic-ai/sdk`) | Direct Claude usage |
| **Vercel AI SDK** (`ai` + `@ai-sdk/openai`) | Next.js apps, streaming UIs, edge deployment |

**Why not LangChain:** For single-provider chat, LangChain adds ~500KB+ bundle size, abstraction layers, and zero value over the direct SDK. Community consensus backs this — see `antipatterns.md` § "Architecture".

**If you insist on LangChain** (e.g., you might add providers later): Use only `@langchain/openai` or `@langchain/anthropic` with `.invoke()` / `.stream()`. Don't pull in chains, memory, or LCEL.

→ See **pattern-catalog.md § Core Primitives — Pattern 1: Chat Model Basics**

---

### 2. Build a Multi-Provider Chat (OpenRouter, Fallbacks)

**→ Use LangChain.** This is where the ChatModel abstraction genuinely earns its keep.

**Recommended approach:**
```typescript
import { ChatOpenRouter } from "@langchain/openrouter";

const model = new ChatOpenRouter({
  model: "anthropic/claude-sonnet-4-6",
  provider: {
    order: ["Anthropic", "Google"],
    allow_fallbacks: true,
  },
});
```

**For model fallback middleware:**
```typescript
import { createAgent, modelFallbackMiddleware } from "langchain";
import { ChatOpenRouter } from "@langchain/openrouter";

const primary = new ChatOpenRouter({ model: "anthropic/claude-sonnet-4-6" });
const fallback = new ChatOpenRouter({ model: "openai/gpt-4o" });

const agent = createAgent({
  model: primary,
  tools,
  middleware: [modelFallbackMiddleware(fallback)],
});
```

**Key gotchas:**
- Use `@langchain/openrouter`, not `ChatOpenAI` with `baseURL` hack
- Use `ToolStrategy.fromSchema()` not `providerStrategy` when routing across models
- See `antipatterns.md` § "OpenRouter / Provider-Specific"

→ See **pattern-catalog.md § Core Primitives — Pattern 2: Multi-Provider Setup**

---

### 3. Build a Tool-Calling Agent

**→ Use `createAgent` from LangChain v1.** This is a sweet spot for LangChain — cleaner than manual tool loop wiring.

```typescript
import { createAgent } from "langchain";
import { tool } from "@langchain/core/tools";
import { z } from "zod";

const searchTool = tool({
  name: "web_search",
  description: "Search the web",
  schema: z.object({ query: z.string() }),
  func: async ({ query }) => { /* ... */ },
});

const agent = createAgent({
  model,
  tools: [searchTool],
  systemPrompt: "You are a research assistant.",
});
```

**Why LangChain here:** `createAgent` handles the tool execution loop (call model → execute tool → feed result back → repeat), which is non-trivial to implement correctly. It also supports middleware for error handling, retries, and rate limiting.

**Alternative:** Vercel AI SDK v6 also has tool support via `generateText({ tools })`. If you're already in the AI SDK ecosystem and have a single provider, that's simpler.

→ See **pattern-catalog.md § Agents — Pattern 1: Basic Tool Agent**

---

### 4. Build a Multi-Step Agent with State

**→ Use LangGraph.js.** This is LangGraph's core use case — agent workflows with conditional branching, cycles, and persistent state.

```typescript
import { StateGraph, MessagesAnnotation, START, END } from "@langchain/langgraph";
import { MemorySaver } from "@langchain/langgraph";

const graph = new StateGraph(MessagesAnnotation)
  .addNode("agent", agentNode)
  .addNode("tools", toolNode)
  .addEdge(START, "agent")
  .addConditionalEdges("agent", shouldContinue, {
    continue: "tools",
    end: END,
  })
  .addEdge("tools", "agent");

const app = graph.compile({ checkpointer: new MemorySaver() });
```

**When to use LangGraph vs createAgent:**
| Need | Use |
|------|-----|
| Simple tool loop (model ↔ tools) | `createAgent` |
| Conditional branching | LangGraph |
| Cycles / retry loops | LangGraph |
| Human-in-the-loop approval | LangGraph (with interrupts) or `createAgent` with `humanInTheLoopMiddleware` |
| Multi-agent coordination | LangGraph |
| Persistent conversation across sessions | LangGraph with checkpointer |

**Alternative:** Mastra (21.9k GitHub stars) is a TypeScript-native agent framework that's simpler for basic stateful agents. Consider it if you don't need LangGraph's full graph model.

→ See **pattern-catalog.md § LangGraph — Pattern 1: Stateful Agent Graph**

---

### 5. Add RAG to My Application

**→ Use LangChain for document loading and splitting, but consider the alternatives for the full pipeline.**

**LangChain's genuine RAG value:**
- Document loaders (~45 in TS): PDF, CSV, JSON, web, Notion, GitHub
- Text splitters with configurable overlap
- Vector store integrations (Pinecone, Weaviate, Chroma, pgvector)
- `createRetrievalChain` for composing retriever + LLM

**Simple RAG pattern:**
```typescript
import { ChatOpenAI } from "@langchain/openai";
import { MemoryVectorStore } from "langchain/vectorstores/memory";
import { OpenAIEmbeddings } from "@langchain/openai";
import { RecursiveCharacterTextSplitter } from "@langchain/textsplitters";

// 1. Load and split documents
const splitter = new RecursiveCharacterTextSplitter({ chunkSize: 1000, chunkOverlap: 200 });
const docs = await splitter.splitDocuments(rawDocs);

// 2. Create vector store
const vectorStore = await MemoryVectorStore.fromDocuments(docs, new OpenAIEmbeddings());
const retriever = vectorStore.asRetriever({ k: 4 });

// 3. Compose RAG chain
const relevantDocs = await retriever.invoke(question);
const context = relevantDocs.map(d => d.pageContent).join("\n");
const result = await model.invoke(`Context: ${context}\n\nQuestion: ${question}`);
```

**Alternatives to consider:**
| Tool | Best For |
|------|----------|
| **LlamaIndex.TS** | RAG-focused applications with better default chunking/retrieval |
| **Direct vector DB SDK** | When you only need one vector store and want minimal dependencies |
| **Vercel AI SDK** | If your RAG is simple retrieval + chat (no complex pipeline) |

**Honest take:** LangChain's RAG value is in document loaders and splitters. The retrieval chain composition is simple enough to do manually. If your RAG pipeline is the core of your app, evaluate LlamaIndex.TS — it's purpose-built for this.

→ See **pattern-catalog.md § RAG — Pattern 1: Basic RAG Pipeline**

---

### 6. Stream Responses to a Web UI (Next.js)

**→ Use the `@ai-sdk/langchain` adapter to bridge LangChain streams into Vercel AI SDK's `useChat`.**

**Server (Route Handler):**
```typescript
// app/api/chat/route.ts
import { ChatOpenAI } from "@langchain/openai";
import { LangChainAdapter } from "@ai-sdk/langchain";

export async function POST(req: Request) {
  const { messages } = await req.json();
  const model = new ChatOpenAI({ model: "gpt-4o", streaming: true });
  const stream = await model.stream(messages);
  return LangChainAdapter.toDataStreamResponse(stream);
}
```

**Client:**
```typescript
"use client";
import { useChat } from "@ai-sdk/react";

export default function Chat() {
  const { messages, input, handleInputChange, handleSubmit } = useChat();
  return (/* render messages */);
}
```

**Key caveats:**
- Works great for simple text streaming from LangChain chat models
- For complex agent streaming (tool calls, LangGraph events), use LangChain's native streaming instead of the adapter — the adapter doesn't handle complex event types well
- For LangGraph agents, use `@langchain/langgraph-sdk` streaming directly

**If you don't need LangChain at all:** Just use Vercel AI SDK natively — it's built for this use case and has zero abstraction overhead.

→ See **pattern-catalog.md § Integration — Pattern 1: Next.js Streaming**

---

### 7. Handle Errors in Production

**→ Use LangChain v1's built-in middleware for retry, fallback, and error recovery.**

**Layer 1: Model retry with exponential backoff**
```typescript
import { createAgent, modelRetryMiddleware } from "langchain";

const agent = createAgent({
  model,
  tools,
  middleware: [
    modelRetryMiddleware({ maxRetries: 3, initialDelayMs: 1000, maxDelayMs: 30000 }),
  ],
});
```

**Layer 2: Model fallback**
```typescript
import { modelFallbackMiddleware } from "langchain";
// Falls back to cheaper model on primary failure
middleware: [modelFallbackMiddleware(cheaperModel)],
```

**Layer 3: Tool error recovery**
```typescript
import { createMiddleware, ToolMessage } from "langchain";

const handleToolErrors = createMiddleware({
  name: "HandleToolErrors",
  wrapToolCall: async (request, handler) => {
    try {
      return await handler(request);
    } catch (error) {
      return new ToolMessage({
        content: `Tool error: ${error}. Please retry with different parameters.`,
        tool_call_id: request.toolCall.id!,
      });
    }
  },
});
```

**Production checklist:**
- ✅ `modelRetryMiddleware` for transient API failures
- ✅ `modelFallbackMiddleware` for provider outages
- ✅ Custom `wrapToolCall` middleware for tool errors
- ✅ `toolCallLimitMiddleware({ runLimit: N })` to prevent infinite loops
- ✅ LangSmith tracing for production observability

→ See **pattern-catalog.md § Middleware — Pattern 3: Error Handling Stack**

---

### 8. Add Conversation Memory

**→ Use LangGraph checkpointers. Do NOT use legacy memory classes.**

**Simple in-memory (development):**
```typescript
import { MemorySaver } from "@langchain/langgraph";

const agent = createAgent({
  model,
  tools,
  checkpointer: new MemorySaver(),
});

// Each thread_id maintains separate conversation history
await agent.invoke({ messages: [{ role: "user", content: "Hello" }] }, {
  configurable: { thread_id: "user-123" },
});
```

**Production (PostgreSQL):**
```typescript
import { PostgresSaver } from "@langchain/langgraph-checkpoint-postgres";

const checkpointer = PostgresSaver.fromConnString(process.env.DATABASE_URL!);
await checkpointer.setup(); // Creates tables if needed

const agent = createAgent({ model, tools, checkpointer });
```

**What NOT to do:** Don't use `ConversationBufferMemory`, `ConversationSummaryMemory`, or any class from `langchain/memory`. They're deprecated, moved to `@langchain/classic`, and hide critical details about context window management. See `antipatterns.md` § "Deprecated Patterns".

**Alternative:** For simple apps, just manage a message array yourself. It's 10 lines of code and gives you full control.

→ See **pattern-catalog.md § State Management — Pattern 1: Conversation Memory**

---

### 9. Add Human-in-the-Loop Approval

**→ Use LangGraph interrupts or `humanInTheLoopMiddleware` from createAgent.**

**Option A: createAgent middleware (simpler)**
```typescript
import { createAgent, humanInTheLoopMiddleware } from "langchain";

const agent = createAgent({
  model,
  tools: [deleteTool, sendEmailTool],
  middleware: [
    humanInTheLoopMiddleware({
      toolsRequiringApproval: ["delete_record", "send_email"],
    }),
  ],
  checkpointer: new MemorySaver(),
});
```

**Option B: LangGraph interrupt (more control)**
```typescript
import { interrupt } from "@langchain/langgraph";

function reviewNode(state: typeof MessagesAnnotation.State) {
  const approval = interrupt("Please review this action. Approve? (yes/no)");
  if (approval !== "yes") {
    return { messages: [{ role: "assistant", content: "Action cancelled." }] };
  }
  // proceed with action
}
```

**Critical: Resuming an interrupt requires `Command`:**
```typescript
import { Command } from "@langchain/langgraph";
// ✅ CORRECT
const result = await app.invoke(new Command({ resume: "yes" }), config);
// ❌ WRONG — see antipatterns.md
const result = await app.invoke({ resume: "yes" }, config);
```

→ See **pattern-catalog.md § LangGraph — Pattern 3: Human-in-the-Loop**

---

### 10. Extract Structured Output from LLM Responses

**→ Use `.withStructuredOutput()` with Zod schemas. This is one of LangChain's strongest TypeScript features.**

```typescript
import { z } from "zod";

const MovieReview = z.object({
  title: z.string().describe("The movie title"),
  rating: z.number().min(1).max(10).describe("Rating out of 10"),
  summary: z.string().describe("Brief summary"),
});

const structured = model.withStructuredOutput(MovieReview);
const result = await structured.invoke("Review the movie Inception");
// result is typed: { title: string, rating: number, summary: string }
```

**In an agent context, use `ToolStrategy.fromSchema()`:**
```typescript
import { createAgent, ToolStrategy } from "langchain";
const agent = createAgent({
  model,
  tools,
  responseFormat: ToolStrategy.fromSchema(OutputSchema),
});
```

**Key rules:**
- Keep schemas flat — avoid deeply nested objects and discriminated unions
- Use `.describe()` on every field — this becomes the LLM's instruction
- For OpenRouter: use default method (function calling), not `method: "jsonSchema"`
- Use `ToolStrategy.fromSchema()`, not `new ToolStrategy()` or `providerStrategy` on OpenRouter

**Alternative:** For one-off extractions without LangChain, Vercel AI SDK's `generateObject()` does the same with less setup.

→ See **pattern-catalog.md § Core Primitives — Pattern 3: Structured Output**

---

### 11. Build Multi-Agent Orchestration

**→ Use LangGraph.js with subgraphs or a supervisor pattern.**

**Supervisor pattern (recommended for most cases):**
```typescript
const supervisorGraph = new StateGraph(OrchestratorAnnotation)
  .addNode("supervisor", supervisorNode)
  .addNode("researcher", researcherSubgraph)
  .addNode("writer", writerSubgraph)
  .addConditionalEdges("supervisor", routeToAgent, {
    researcher: "researcher",
    writer: "writer",
    done: END,
  })
  .addEdge("researcher", "supervisor")
  .addEdge("writer", "supervisor")
  .addEdge(START, "supervisor");
```

**When to use what:**
| Pattern | Best For |
|---------|----------|
| **Supervisor** | Central coordinator routes tasks to specialized agents |
| **Subgraphs** | Encapsulated agent workflows that compose into a larger graph |
| **Sequential** | Agent A output feeds into Agent B (pipeline) |

**Alternatives:**
- **Mastra** has a cleaner multi-agent API for TypeScript if you don't need LangGraph's full graph model
- **Direct orchestration** with plain async functions works for simple 2-3 agent pipelines — you don't always need a framework

**Note:** Python has `langgraph-swarm` for agent handoffs; this doesn't exist in TypeScript yet. For swarm-style patterns in TS, implement handoffs manually within LangGraph.

→ See **pattern-catalog.md § LangGraph — Pattern 4: Multi-Agent Orchestration**

---

### 12. Process Items in Batch

**→ Use LangChain's built-in `.batch()` method — it's actually better in TypeScript than Python thanks to native async concurrency.**

```typescript
const questions = ["What is AI?", "What is ML?", "What is DL?"];
const results = await model.batch(
  questions.map(q => [{ role: "user" as const, content: q }]),
  { maxConcurrency: 5 }, // Control parallelism
);
```

**For agent batches:**
```typescript
const tasks = items.map(item => ({
  messages: [{ role: "user" as const, content: `Process: ${item}` }],
}));
const results = await agent.batch(tasks, { maxConcurrency: 3 });
```

**Why LangChain here:** The `.batch()` method handles concurrency limiting, error isolation (one failure doesn't kill the batch), and consistent output format. TypeScript's event loop makes this naturally efficient for I/O-bound LLM calls.

**Alternative:** `Promise.all` with manual concurrency control (e.g., `p-limit` package) works fine without LangChain.

→ See **pattern-catalog.md § Core Primitives — Pattern 5: Batch Processing**

---

### 13. When NOT to Use LangChain

**Use direct provider SDKs when:**
- You use a single LLM provider and won't switch
- Your app is a simple chatbot or completion API
- Bundle size matters (serverless, edge, browser)
- You need maximum control over prompts and API calls
- You want the simplest possible debugging experience

**Use Vercel AI SDK when:**
- You're building a Next.js app with streaming chat UI
- You want TypeScript-native, minimal-API-surface tooling
- You need edge runtime compatibility
- You want `useChat` / `useCompletion` hooks out of the box
- AI SDK v6 covers your agent needs (tool calling, MCP support)

**Use Mastra when:**
- You want a TypeScript-native agent framework (not a Python port)
- Clean agent declaration is a priority (`new Agent({ name, instructions, model, tools })`)
- You're building agent-style apps but don't need LangChain's ecosystem
- You want a rapidly growing community (21.9k GitHub stars)

**Use LlamaIndex.TS when:**
- Your primary use case is RAG
- You need better default chunking and retrieval strategies
- You don't need agent orchestration features

**Use LangChain when:**
- You need multi-provider model switching (the core value proposition)
- You need complex tool-calling agent orchestration
- You want LangSmith for observability (works with any framework, but integrates best with LangChain)
- You're building with LangGraph for stateful, multi-step, branching agent workflows
- You need the ecosystem: document loaders, text splitters, vector store integrations
- You're prototyping and plan to evaluate whether to keep or replace it

---

## Decision Matrix Summary

| Intent | Recommended Tool | LangChain? |
|--------|-----------------|------------|
| Simple single-provider chat | Provider SDK / Vercel AI SDK | ❌ No |
| Streaming chat in Next.js | Vercel AI SDK | ❌ No (or bridge via `@ai-sdk/langchain`) |
| Multi-provider chat | LangChain ChatModels | ✅ Yes |
| Basic tool-calling agent | `createAgent` from LangChain | ✅ Yes |
| Complex stateful agent | LangGraph.js | ✅ Yes |
| RAG pipeline | LangChain or LlamaIndex.TS | ✅ Maybe |
| Structured output | LangChain `.withStructuredOutput()` | ✅ Yes |
| Conversation memory | LangGraph checkpointers | ✅ Yes |
| Human-in-the-loop | LangGraph interrupts / middleware | ✅ Yes |
| Multi-agent orchestration | LangGraph.js | ✅ Yes |
| Batch processing | LangChain `.batch()` or `Promise.all` | ⚪ Optional |
| Production error handling | LangChain middleware | ✅ Yes |
| Observability | LangSmith (framework-agnostic) | ⚪ Independent |
