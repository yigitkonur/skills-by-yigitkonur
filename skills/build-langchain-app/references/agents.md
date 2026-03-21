# Agents Reference

Complete reference for building agents with `createAgent` and LangGraph. All code verified against langchain@1.2.35, @langchain/core@1.1.34, @langchain/langgraph@1.2.5. TypeScript only.

---

## createAgent — Full Parameter Reference

```typescript
import { createAgent } from "langchain";

const agent = createAgent({
  model,          // Required — BaseChatModel instance
  tools,          // Required — StructuredTool[] from tool()
  prompt,         // Optional — static system prompt string
  responseFormat, // Optional — ToolStrategy | providerStrategy for structured output
  middleware,     // Optional — Middleware[] hooks
  checkpointer,  // Optional — BaseCheckpointSaver for persistence
  // stateSchema and contextSchema are configured via LangGraph if using StateGraph directly
});
```

### Parameter details

| Parameter | Type | Required | Description |
|---|---|---|---|
| `model` | `BaseChatModel` | Yes | A `ChatOpenAI`, `ChatOpenRouter`, or any `@langchain/` chat model instance. Not a string. |
| `tools` | `StructuredTool[]` | Yes | Array of tools created with `tool()` from `@langchain/core/tools`. |
| `prompt` | `string` | No | Static system prompt. Omit if using `dynamicSystemPromptMiddleware`. |
| `responseFormat` | `ToolStrategy \| ProviderStrategy` | No | Forces structured output. Use `ToolStrategy.fromSchema(zodSchema)`. |
| `middleware` | `Middleware[]` | No | Array of middleware hooks. Executed in order per LLM call. |
| `checkpointer` | `BaseCheckpointSaver` | No | Enables conversation persistence. Use `MemorySaver` for dev. |

### What createAgent returns

`createAgent` returns a `ReactAgent` — a compiled LangGraph graph. It has `.invoke()`, `.stream()`, `.streamEvents()`, and `.getState()`.

---

## Model Configuration

### ChatOpenRouter (recommended for OpenRouter)

```typescript
import { ChatOpenRouter } from "@langchain/openrouter";

const model = new ChatOpenRouter({
  model: "anthropic/claude-sonnet-4-6",
  apiKey: process.env.OPENROUTER_API_KEY,
});
```

### ChatOpenAI with baseURL override (legacy fallback)

```typescript
import { ChatOpenAI } from "@langchain/openai";

const model = new ChatOpenAI({
  model: "anthropic/claude-sonnet-4-6",
  configuration: {
    baseURL: "https://openrouter.ai/api/v1",
    apiKey: process.env.OPENROUTER_API_KEY!,
  },
});
```

### initChatModel — universal provider init

```typescript
import { initChatModel } from "langchain/chat_models/universal";

const model = await initChatModel("anthropic/claude-sonnet-4-6", {
  modelProvider: "openai",
  configuration: {
    baseURL: "https://openrouter.ai/api/v1",
    apiKey: process.env.OPENROUTER_API_KEY!,
  },
});
```

Use `modelProvider: "openai"` for OpenRouter since it exposes an OpenAI-compatible API.

### Key rule

The `model` parameter must be a ChatModel **instance**. There are no string shortcuts. Always instantiate:

```typescript
// ❌ WRONG — string is not accepted
createAgent({ model: "gpt-4o", tools: [...] });

// ✅ CORRECT — pass an instance
createAgent({ model: new ChatOpenAI({ model: "gpt-4o" }), tools: [...] });
```

---

## System Prompt Patterns

### Static prompt

Pass `prompt` to `createAgent`. It becomes the system message prepended to every LLM call.

```typescript
const agent = createAgent({
  model,
  tools: [searchTool],
  prompt: "You are a helpful research assistant. Always cite sources.",
});
```

### Dynamic prompt with dynamicSystemPromptMiddleware

Use when the system prompt must change per invocation (user preferences, time-based context, RAG-injected instructions).

```typescript
import { createAgent, dynamicSystemPromptMiddleware } from "langchain";

const dynamicPrompt = dynamicSystemPromptMiddleware(async (state) => {
  const msgCount = state.messages.length;
  const now = new Date().toISOString();
  return `You are a helpful assistant. Current time: ${now}. Messages so far: ${msgCount}.`;
});

const agent = createAgent({
  model,
  tools: [searchTool],
  middleware: [dynamicPrompt],
  // Do NOT also set `prompt` — the middleware replaces it
});
```

The callback receives the full agent state. Return a string. It fires before every LLM call, including re-invocations after tool results.

---

## Structured Output

Two strategies force the agent to return data matching a Zod schema.

### ToolStrategy.fromSchema (recommended — works everywhere)

Works by injecting a hidden tool the agent must call to produce output. Compatible with all providers and OpenRouter.

```typescript
import { createAgent, ToolStrategy } from "langchain";
import { z } from "zod";

const ResponseSchema = z.object({
  summary: z.string().describe("A brief summary of the findings"),
  topics: z.array(z.string()).describe("List of topics found"),
  confidence: z.number().min(0).max(1).describe("Confidence score"),
});

const strategy = ToolStrategy.fromSchema(ResponseSchema);

const agent = createAgent({
  model,
  tools: [searchTool],
  responseFormat: strategy,
  prompt: "Search and return structured results.",
});

const result = await agent.invoke({
  messages: [{ role: "user", content: "Search for latest JavaScript framework news" }],
});

// result.structuredResponse is the typed object
const structured: z.infer<typeof ResponseSchema> = result.structuredResponse;
// { summary: "...", topics: ["TypeScript 5.8", ...], confidence: 0.85 }
```

**Critical**: Use `ToolStrategy.fromSchema(schema)` — NOT `new ToolStrategy(schema)`. The constructor requires different arguments.

### providerStrategy (native provider structured output)

Uses the provider's native structured output API (`response_format` / `tool_choice`). Faster but not supported by all providers — fails via OpenRouter for some models.

```typescript
import { createAgent, providerStrategy } from "langchain";

const agent = createAgent({
  model,
  tools: [searchTool],
  responseFormat: providerStrategy(ResponseSchema),
  prompt: "Return structured results.",
});
```

### When to use which

| Strategy | Works with OpenRouter | Reliability | Speed |
|---|---|---|---|
| `ToolStrategy.fromSchema()` | Yes — all models | High | Slightly slower (extra tool call) |
| `providerStrategy()` | Some models only | Variable | Faster (native API) |

Default to `ToolStrategy.fromSchema()`. Use `providerStrategy()` only when targeting a known-compatible provider directly (not through OpenRouter).

---

## Conversation Persistence

### MemorySaver — in-memory (dev/testing)

```typescript
import { createAgent } from "langchain";
import { MemorySaver } from "@langchain/langgraph";

const checkpointer = new MemorySaver();

const agent = createAgent({
  model,
  tools: [searchTool],
  checkpointer,
  prompt: "You are a helpful assistant. Remember what the user tells you.",
});

const threadId = "user-alice-session-1";
const config = { configurable: { thread_id: threadId } };

// Turn 1
await agent.invoke(
  { messages: [{ role: "user", content: "My name is Alice and I'm a software engineer." }] },
  config
);

// Turn 2 — agent remembers
const result = await agent.invoke(
  { messages: [{ role: "user", content: "What is my name and what do I do?" }] },
  config
);
// Response includes "Alice" and "software engineer"
```

### Thread isolation

Each `thread_id` maintains an isolated conversation. Messages from one thread never leak to another.

```typescript
// Different thread has NO memory of Alice
await agent.invoke(
  { messages: [{ role: "user", content: "What is my name?" }] },
  { configurable: { thread_id: "different-thread" } }
);
// Response: "I don't know your name"
```

### Production checkpointers

Replace `MemorySaver` with a persistent backend for production:

```typescript
// PostgreSQL — @langchain/langgraph-checkpoint-postgres
import { PostgresSaver } from "@langchain/langgraph-checkpoint-postgres";
const checkpointer = PostgresSaver.fromConnString(process.env.DATABASE_URL!);

// SQLite — @langchain/langgraph-checkpoint-sqlite
import { SqliteSaver } from "@langchain/langgraph-checkpoint-sqlite";
const checkpointer = new SqliteSaver("./checkpoints.db");
```

All checkpointers implement `BaseCheckpointSaver` and are drop-in replacements.

### Key rules

- Always pass `{ configurable: { thread_id: "..." } }` as the second argument to `.invoke()` / `.stream()`.
- Without a `thread_id`, the agent has no memory between calls.
- `MemorySaver` data is lost when the process exits. Use PostgresSaver or SqliteSaver for persistence.

---

## Agent Streaming

### .stream() with "values" mode — full state snapshots

Emits the full accumulated state after each graph node execution.

```typescript
const agent = createAgent({ model, tools: [searchTool], prompt: "You are a helpful assistant." });

const stream = await agent.stream(
  { messages: [{ role: "user", content: "Search for TypeScript news" }] },
  { streamMode: "values" }
);

for await (const chunk of stream) {
  const lastMsg = chunk.messages[chunk.messages.length - 1];
  console.log(`[${lastMsg.constructor.name}] ${lastMsg.content}`);
}
// Progressive snapshots:
// [HumanMessage] Search for TypeScript news
// [AIMessage] (tool call)
// [ToolMessage] Search results for...
// [AIMessage] Based on the search results...
```

### .stream() with "updates" mode — deltas per node

Emits only the delta from each graph node. Lighter than "values".

```typescript
const stream = await agent.stream(
  { messages: [{ role: "user", content: "Search for news" }] },
  { streamMode: "updates" }
);

for await (const chunk of stream) {
  for (const [node, data] of Object.entries(chunk)) {
    console.log(`Node "${node}":`, (data as any).messages.length, "message(s)");
  }
}
// Node "model_request": 1 message(s)   — AIMessage with tool_calls
// Node "tools": 1 message(s)           — ToolMessage with results
// Node "model_request": 1 message(s)   — AIMessage final response
```

Node names: `"model_request"` for LLM calls, `"tools"` for tool executions.

### .streamEvents() — token-level streaming

For real-time token-by-token output (chat UIs, SSE endpoints).

```typescript
const stream = agent.streamEvents(
  { messages: [{ role: "user", content: "Explain TypeScript generics" }] },
  { version: "v2" }
);

for await (const event of stream) {
  if (event.event === "on_chat_model_stream") {
    const token = event.data?.chunk?.content;
    if (token) process.stdout.write(token);
  }
}
```

Always use `version: "v2"` for the current event format.

### Key events in streamEvents

| Event | Fires when | Data |
|---|---|---|
| `on_chat_model_start` | LLM call begins | Model info |
| `on_chat_model_stream` | Each token arrives | `data.chunk.content` — the token string |
| `on_chat_model_end` | LLM call completes | Full AIMessage |
| `on_tool_start` | Tool execution begins | Tool name, input args |
| `on_tool_end` | Tool execution completes | Tool output |

---

## Agent Lifecycle — How createAgent Works Under the Hood

`createAgent` builds a LangGraph ReAct loop. Understanding the loop helps debug agent behavior.

```
┌──────────────────────────────────────────────────┐
│                  ReAct Loop                       │
│                                                   │
│  User message                                     │
│       │                                           │
│       ▼                                           │
│  ┌──────────┐    has tool_calls?    ┌──────────┐ │
│  │  Model    │──── yes ────────────►│  Tools   │ │
│  │  Request  │                      │  Execute │ │
│  └──────────┘                      └──────────┘ │
│       ▲         no tool_calls            │       │
│       │         = final answer           │       │
│       │              │                   │       │
│       │              ▼                   │       │
│       │         Return result            │       │
│       └──────────────────────────────────┘       │
│              (loop back with tool results)        │
└──────────────────────────────────────────────────┘
```

1. User message enters the graph.
2. `model_request` node: middleware fires (`beforeModel`), LLM is invoked, middleware fires (`afterModel`).
3. If the AIMessage contains `tool_calls` → `tools` node: each tool is invoked, results become `ToolMessage` entries.
4. ToolMessages feed back to `model_request` node (step 2).
5. If the AIMessage has no `tool_calls` → loop exits, result returned.

Each iteration of steps 2–4 is one "ReAct step." Middleware fires on every model invocation, including re-invocations after tool results.

---

## Middleware Stack

### beforeModel — run logic before each LLM call

```typescript
import { createAgent, createMiddleware } from "langchain";

const loggingMiddleware = createMiddleware({
  name: "logging-middleware",
  beforeModel: async (state, config) => {
    console.log(`Messages so far: ${state.messages.length}`);
    return undefined; // continue with normal flow
  },
});

const agent = createAgent({
  model,
  tools: [searchTool],
  middleware: [loggingMiddleware],
  prompt: "You are a helpful assistant.",
});
```

Return `undefined` to continue normally. The middleware fires on every model invocation (multiple times per `.invoke()` if tools are used).

### afterModel — inspect or modify LLM response

```typescript
const afterModelMiddleware = createMiddleware({
  name: "after-model-middleware",
  afterModel: async (state, config) => {
    const lastMsg = state.messages[state.messages.length - 1];
    console.log(`Model produced: ${lastMsg.constructor.name}`);
    return undefined;
  },
});
```

### Combined middleware: createMiddleware with both hooks

```typescript
const auditMiddleware = createMiddleware({
  name: "audit",
  beforeModel: async (state) => {
    console.log(`[AUDIT] LLM call starting. ${state.messages.length} messages.`);
    return undefined;
  },
  afterModel: async (state) => {
    console.log(`[AUDIT] LLM call complete.`);
    return undefined;
  },
});
```

---

## Production Agent Pattern — Combined Middleware Stack

Stack middleware for production-grade agents. Order matters — they execute in array order.

```typescript
import {
  createAgent,
  dynamicSystemPromptMiddleware,
  modelRetryMiddleware,
  modelFallbackMiddleware,
  modelCallLimitMiddleware,
  toolCallLimitMiddleware,
  toolRetryMiddleware,
} from "langchain";
import { ChatOpenRouter } from "@langchain/openrouter";
import { MemorySaver } from "@langchain/langgraph";
import { tool } from "@langchain/core/tools";
import { z } from "zod";

// Models
const primaryModel = new ChatOpenRouter({
  model: "anthropic/claude-sonnet-4-6",
  apiKey: process.env.OPENROUTER_API_KEY,
});

const fallbackModel = new ChatOpenRouter({
  model: "google/gemini-2.0-flash-001",
  apiKey: process.env.OPENROUTER_API_KEY,
});

// Tools
const searchTool = tool(
  async ({ query }: { query: string }) => `Results for: ${query}`,
  {
    name: "web_search",
    description: "Search the web for current information. Use when the user asks about recent events, news, or facts you don't know.",
    schema: z.object({ query: z.string().describe("The search query") }),
  }
);

// Dynamic prompt
const dynamicPrompt = dynamicSystemPromptMiddleware(async (state) => {
  const now = new Date().toISOString();
  return `You are a production research assistant. Current time: ${now}. Always cite sources.`;
});

// Checkpointer
const checkpointer = new MemorySaver(); // Replace with PostgresSaver in production

// Agent
const agent = createAgent({
  model: primaryModel,
  tools: [searchTool],
  checkpointer,
  middleware: [
    dynamicPrompt,
    modelRetryMiddleware({ maxRetries: 3 }),
    modelFallbackMiddleware(fallbackModel),
    modelCallLimitMiddleware({ threadLimit: 20 }),
    toolCallLimitMiddleware({ runLimit: 10 }),
    toolRetryMiddleware({ maxRetries: 2 }),
  ],
  // No static `prompt` — dynamicPrompt provides it
});

// Usage
const config = { configurable: { thread_id: "prod-session-1" } };

const result = await agent.invoke(
  { messages: [{ role: "user", content: "What are the latest TypeScript features?" }] },
  config
);

console.log(result.messages[result.messages.length - 1].content);
```

### Middleware execution order

| Middleware | Purpose | Fires when |
|---|---|---|
| `dynamicSystemPromptMiddleware` | Inject dynamic system prompt | Before each LLM call |
| `modelRetryMiddleware` | Retry failed LLM calls | LLM call throws |
| `modelFallbackMiddleware` | Switch to backup model | Primary model fails after retries |
| `modelCallLimitMiddleware` | Cap total LLM calls per thread | Every LLM call |
| `toolCallLimitMiddleware` | Cap tool calls per run | Every tool call |
| `toolRetryMiddleware` | Retry failed tool calls | Tool throws |

### Middleware API quick reference

```typescript
// Retry — optional config
modelRetryMiddleware({ maxRetries: 3 });
modelRetryMiddleware(); // uses defaults

// Fallback — spread args, NOT { models: [...] }
modelFallbackMiddleware(fallbackModel1, fallbackModel2);

// Model call limit
modelCallLimitMiddleware({ threadLimit: 20 });
modelCallLimitMiddleware({ threadLimit: 20, exitBehavior: "error" });

// Tool call limit — at least one of threadLimit or runLimit required
toolCallLimitMiddleware({ runLimit: 10 });
toolCallLimitMiddleware({ threadLimit: 50, runLimit: 10 });

// Tool retry
toolRetryMiddleware({ maxRetries: 2 });
```

---

## Human-in-the-Loop with interrupt()

For agents that need human approval before executing certain actions.

### Setup with humanInTheLoopMiddleware

```typescript
import { createAgent, humanInTheLoopMiddleware } from "langchain";
import { MemorySaver } from "@langchain/langgraph";

// All tools require approval
const hitl = humanInTheLoopMiddleware();

// Or selective — only specific tools require approval
const selectiveHitl = humanInTheLoopMiddleware({
  toolsRequiringApproval: ["delete_records", "send_email"],
});

const agent = createAgent({
  model,
  tools: [safeTool, dangerousTool],
  middleware: [selectiveHitl],
  checkpointer: new MemorySaver(), // Required for interrupt/resume
  prompt: "You are a helpful assistant.",
});
```

### Manual interrupt() in custom LangGraph graphs

```typescript
import {
  interrupt,
  MemorySaver,
  StateGraph,
  Annotation,
  START,
  END,
  Command,
} from "@langchain/langgraph";

const GraphState = Annotation.Root({
  input: Annotation<string>,
  approved: Annotation<boolean>,
  result: Annotation<string>,
});

const approvalNode = async (state: typeof GraphState.State) => {
  const humanResponse = interrupt({
    question: `Do you approve: "${state.input}"?`,
    options: ["yes", "no"],
  });
  return { approved: humanResponse === "yes" };
};

const processNode = async (state: typeof GraphState.State) => {
  return { result: state.approved ? `Processed: ${state.input}` : "Rejected" };
};

const graph = new StateGraph(GraphState)
  .addNode("approval", approvalNode)
  .addNode("process", processNode)
  .addEdge(START, "approval")
  .addConditionalEdges("approval", () => "process", ["process"])
  .addEdge("process", END);

const checkpointer = new MemorySaver();
const app = graph.compile({ checkpointer });

const config = { configurable: { thread_id: "my-thread" } };

// Step 1: Run until interrupt
const result1 = await app.invoke({ input: "test data" }, config);
// result1.__interrupt__ contains the interrupt payload

// Step 2: Check state
const state = await app.getState(config);
console.log(state.next); // ["approval"]

// Step 3: Resume with Command
const result2 = await app.invoke(new Command({ resume: "yes" }), config);
// { input: "test data", approved: true, result: "Processed: test data" }
```

**Critical**: Resume with `new Command({ resume: value })` — NOT a plain object `{ resume: value }`.

---

## Key Import Paths

```typescript
// Agent creation + middleware
import {
  createAgent,
  createMiddleware,
  dynamicSystemPromptMiddleware,
  ToolStrategy,
  providerStrategy,
  modelRetryMiddleware,
  modelFallbackMiddleware,
  modelCallLimitMiddleware,
  toolCallLimitMiddleware,
  toolRetryMiddleware,
  humanInTheLoopMiddleware,
} from "langchain";

// Tools
import { tool } from "@langchain/core/tools";

// Memory / Graph
import { MemorySaver, interrupt, Command } from "@langchain/langgraph";

// Models
import { ChatOpenAI } from "@langchain/openai";
import { ChatOpenRouter } from "@langchain/openrouter";
import { initChatModel } from "langchain/chat_models/universal";

// Messages
import { HumanMessage, AIMessage, SystemMessage, ToolMessage } from "@langchain/core/messages";

// Prompts
import { ChatPromptTemplate } from "@langchain/core/prompts";

// Schema
import { z } from "zod";
```

---

## Common Agent Mistakes

| Mistake | Fix |
|---|---|
| Passing a string as `model` | Always pass a ChatModel instance |
| `new ToolStrategy(schema)` | Use `ToolStrategy.fromSchema(schema)` |
| `modelFallbackMiddleware({ models: [...] })` | Use spread args: `modelFallbackMiddleware(model1, model2)` |
| `toolCallLimitMiddleware({ maxToolCalls: 5 })` | Use `{ runLimit: 5 }` or `{ threadLimit: 5 }` |
| Setting both `prompt` and `dynamicSystemPromptMiddleware` | Use one or the other. The middleware replaces the static prompt. |
| Forgetting `thread_id` with checkpointer | Always pass `{ configurable: { thread_id: "..." } }` |
| Resuming interrupt with plain object | Use `new Command({ resume: value })` |
| Expecting `.invoke()` to stream | Use `.stream()` or `.streamEvents()` for streaming |
