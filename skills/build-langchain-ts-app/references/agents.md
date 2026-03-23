# Agents Reference

Complete reference for `createAgent` (LangChain.js v1). All APIs verified against langchain@1.2.35, @langchain/core@1.1.34, @langchain/langgraph@1.2.5. TypeScript only.

---

## Quick Reference — Imports

```typescript
import { createAgent, tool, createMiddleware } from "langchain";
import {
  dynamicSystemPromptMiddleware,
  summarizationMiddleware,
  humanInTheLoopMiddleware,
  modelCallLimitMiddleware,
  toolCallLimitMiddleware,
  modelFallbackMiddleware,
  piiMiddleware,
  toolRetryMiddleware,
  modelRetryMiddleware,
  toolEmulatorMiddleware,
  contextEditingMiddleware,
  llmToolSelectorMiddleware,
  filesystemMiddleware,
  todoListMiddleware,
  providerStrategy,
  toolStrategy,
} from "langchain";
import { MemorySaver, StateSchema, Command } from "@langchain/langgraph";
import { PostgresSaver } from "@langchain/langgraph-checkpoint-postgres";
import { z } from "zod";
```

---

## createAgent — Full Parameter Reference

`createAgent` is the canonical agent factory in LangChain.js v1. It returns a `ReactAgent` instance built on a LangGraph ReAct loop.

```typescript
import { createAgent } from "langchain";

const agent = createAgent({
  model,          // Required — string ID or ChatModel instance
  tools,          // Optional — (ClientTool | ServerTool)[]
  systemPrompt,   // Optional — static system prompt (string or SystemMessage)
  responseFormat, // Optional — providerStrategy(schema) | toolStrategy(schema) | Zod schema | array
  middleware,     // Optional — AgentMiddleware[]
  checkpointer,   // Optional — MemorySaver | PostgresSaver | custom
  contextSchema,  // Optional — z.ZodObject for per-invocation runtime.context
  stateSchema,    // Optional — StateSchema for custom state fields
  name,           // Optional — snake_case ID for multi-agent setups
});
```

### Parameter Details

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `model` | `string` or `BaseChatModel` instance | Yes | — | String uses `initChatModel` internally (e.g. `"openai:gpt-4o"`, `"gpt-4.1"`, `"claude-sonnet-4-6"`). Or pass a `ChatOpenAI`, `ChatAnthropic`, etc. instance for fine-grained config. |
| `tools` | `(ClientTool \| ServerTool)[]` | No | `[]` | Tools created with `tool()`. Static; filter dynamically via middleware. |
| `systemPrompt` | `string \| SystemMessage` | No | `undefined` | Prepended to every LLM call. For dynamic prompts use `dynamicSystemPromptMiddleware`. |
| `responseFormat` | See structured output section | No | `undefined` | Forces a typed response. Result at `result.structuredResponse`. |
| `middleware` | `AgentMiddleware[]` | No | `[]` | Hooks for lifecycle, error handling, rate limits, etc. Execution order matters. |
| `checkpointer` | `BaseCheckpointSaver` | No | `undefined` | Enables persistent conversation memory via `thread_id`. |
| `contextSchema` | `z.ZodObject` | No | `undefined` | Typed schema for per-invocation context passed as `invoke(input, { context: {...} })`. |
| `stateSchema` | `StateSchema` | No | `undefined` | Extends the agent's LangGraph state with custom fields. |
| `name` | `string` | No | `undefined` | Snake_case identifier; used when this agent is a node in a multi-agent graph. |

### Return Type — ReactAgent

`createAgent` returns a `ReactAgent` with these key methods:

| Method | Signature | Description |
|---|---|---|
| `invoke` | `(input: { messages: Message[] }, config?) => Promise<AgentResult>` | Run to completion. |
| `stream` | `(input: { messages: Message[] }, options?: { streamMode?: ... }) => AsyncGenerator` | Stream incremental results. |
| `getState` | LangGraph method | Inspect current checkpoint state. |

---

## Model Configuration

### String identifier (recommended for most cases)

```typescript
// Provider-prefixed string — most explicit
const agent = createAgent({ model: "openai:gpt-4o", tools: [] });

// Short model ID — resolved via initChatModel
const agent = createAgent({ model: "gpt-4.1", tools: [] });
const agent = createAgent({ model: "claude-sonnet-4-6", tools: [] });
```

### Model instance (for custom config)

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { ChatAnthropic } from "@langchain/anthropic";

const agent = createAgent({
  model: new ChatOpenAI({ model: "gpt-4o", temperature: 0.7, maxTokens: 2048 }),
  tools: [],
});

const agent = createAgent({
  model: new ChatAnthropic({ model: "claude-sonnet-4-6" }),
  tools: [],
});
```

### Decision: string vs instance

Use a **string** when you want simplicity and no custom model config. Use an **instance** when you need `temperature`, `maxTokens`, `streaming: false`, provider-specific options (e.g. `thinking`), or OpenRouter's `baseURL` override.

---

## System Prompt Configuration

### Static string

```typescript
const agent = createAgent({
  model: "gpt-4.1",
  tools: [],
  systemPrompt: "You are a concise assistant. Answer in 2 sentences max.",
});
```

### Static SystemMessage

```typescript
import { SystemMessage } from "@langchain/core/messages";

const agent = createAgent({
  model: "gpt-4.1",
  tools: [],
  systemPrompt: new SystemMessage("You are an expert TypeScript developer."),
});
```

### Dynamic — per-invocation via dynamicSystemPromptMiddleware

Use when the prompt must change per call (user roles, time, RAG-injected context). The callback receives `(state, runtime)` and returns a string. Fires before every LLM call, including re-invocations after tool results.

```typescript
import { createAgent, dynamicSystemPromptMiddleware } from "langchain";
import { z } from "zod";

const contextSchema = z.object({
  userRole: z.string(),
  deploymentEnv: z.string(),
});

const agent = createAgent({
  model: "gpt-4.1",
  tools: [],
  contextSchema,
  middleware: [
    dynamicSystemPromptMiddleware<z.infer<typeof contextSchema>>((state, runtime) => {
      const { userRole, deploymentEnv } = runtime.context;
      let prompt = "You are a helpful assistant.";
      if (userRole === "admin") prompt += "\nYou have full admin access.";
      if (deploymentEnv === "production") prompt += "\nBe extra careful with data changes.";
      return prompt;
    }),
  ],
});

await agent.invoke(
  { messages: [{ role: "user", content: "List all users" }] },
  { context: { userRole: "admin", deploymentEnv: "production" } }
);
```

**Rule:** Do not set both `systemPrompt` and `dynamicSystemPromptMiddleware` — the middleware replaces the static prompt.

---

## Tool Binding

### Defining tools

```typescript
import { tool } from "langchain"; // or "@langchain/core/tools"
import { z } from "zod";

const calculateTax = tool(
  ({ amount, rate }) => `Tax: $${(amount * rate).toFixed(2)}`,
  {
    name: "calculate_tax",
    description: "Calculate tax for a given amount and rate",
    schema: z.object({
      amount: z.number().describe("Amount in dollars"),
      rate: z.number().min(0).max(1).describe("Tax rate as decimal (0.1 = 10%)"),
    }),
  }
);

const agent = createAgent({ model: "gpt-4.1", tools: [calculateTax] });
```

### Dynamic tool filtering via middleware

```typescript
import { createMiddleware } from "langchain";

const stateBasedTools = createMiddleware({
  name: "StateBasedTools",
  wrapModelCall: (request, handler) => {
    const { authenticated = false } = request.state;
    const tools = authenticated
      ? request.tools
      : request.tools.filter(t => t.name.startsWith("public_"));
    return handler({ ...request, tools });
  },
});
```

### Accessing context in a tool

```typescript
import { type ToolRuntime } from "@langchain/core/tools";

const contextSchema = z.object({ userId: z.string(), tenantId: z.string() });

const fetchUserTool = tool(
  async (_, runtime: ToolRuntime<any, typeof contextSchema>) => {
    const { userId, tenantId } = runtime.context!;
    return `User ${userId} in tenant ${tenantId}`;
  },
  { name: "fetch_user", description: "Fetch user info", schema: z.object({}) }
);
```

---

## Agent Loop Architecture

`createAgent` builds a LangGraph ReAct loop. Middleware fires at each step.

```
User message
    │
    ▼
┌─────────────────────────────────────────────────────┐
│                    ReAct Loop                        │
│                                                      │
│  middleware: beforeAgent (once)                      │
│       │                                              │
│       ▼                                              │
│  middleware: beforeModel ──► LLM call                │
│                             (wrapModelCall)          │
│                                    │                 │
│                     ┌─── has tool_calls?             │
│                     │                                │
│                  yes│              no                │
│                     ▼               ▼                │
│               tools node      middleware: afterAgent │
│             (wrapToolCall)         │                 │
│                     │              ▼                 │
│                     │         Return result          │
│                     ▼                                │
│              middleware: afterModel                  │
│              (reverse order)                         │
│                     │                                │
│                     └────────────────────────────────┘
│                     (loop back with tool results)    │
└─────────────────────────────────────────────────────┘
```

**Loop steps:**
1. `beforeAgent` fires once.
2. `beforeModel` fires → `wrapModelCall` wraps each LLM invocation → LLM called.
3. If AIMessage has `tool_calls` → tools node executes (`wrapToolCall` wraps each tool).
4. `afterModel` fires (reverse array order) → loop returns to step 2.
5. If no `tool_calls` → `afterAgent` fires → result returned.

**Streaming node names:** `"model"` for LLM calls, `"tools"` for tool executions.

---

## Structured Output

`responseFormat` forces the agent to return a typed, validated object accessible at `result.structuredResponse`.

### Strategy 1: toolStrategy (works with all models)

Injects a hidden tool the model must call. Compatible with every provider, including OpenRouter. Default choice.

```typescript
import { createAgent, toolStrategy } from "langchain";
import { z } from "zod";

const ProductReview = z.object({
  rating: z.number().min(1).max(5),
  sentiment: z.enum(["positive", "negative", "neutral"]),
  keyPoints: z.array(z.string()),
  summary: z.string(),
});

const agent = createAgent({
  model: "gpt-4.1",
  tools: [],
  responseFormat: toolStrategy(ProductReview, {
    toolMessageContent: "Review analyzed successfully.",
    handleError: (err) => "Please provide a rating 1-5, sentiment, and key points.",
  }),
});

const result = await agent.invoke({
  messages: [{ role: "user", content: "Analyze: This product exceeded my expectations! 5 stars." }],
});

const structured: z.infer<typeof ProductReview> = result.structuredResponse;
```

### toolStrategy options

| Option | Type | Default | Description |
|---|---|---|---|
| `toolMessageContent` | `string` | Auto-generated | Shown in conversation when structured output is produced. |
| `handleError` | `true \| false \| (err) => string` | `true` | `true` = retry with template; `false` = throw; function = custom message. |

### Strategy 2: providerStrategy (native — faster but limited)

Uses the provider's native structured output API. Faster, but not supported by all providers or OpenRouter models.

```typescript
import { createAgent, providerStrategy } from "langchain";

const ContactInfo = z.object({
  name: z.string(),
  email: z.string().email(),
  phone: z.string(),
});

const agent = createAgent({
  model: "gpt-5",  // must support native structured output
  tools: [],
  responseFormat: providerStrategy(ContactInfo),
});

const result = await agent.invoke({
  messages: [{ role: "user", content: "Extract: John Doe, john@example.com, (555) 123-4567" }],
});
console.log(result.structuredResponse);
// { name: "John Doe", email: "john@example.com", phone: "(555) 123-4567" }
```

### Decision: toolStrategy vs providerStrategy

| | `toolStrategy` | `providerStrategy` |
|---|---|---|
| Works with OpenRouter | Yes — all models | Some models only |
| Reliability | High | Variable |
| Speed | Slightly slower (extra tool call) | Faster (native API) |
| **Use when** | Default; any provider | Targeting known-compatible provider directly |

### Multiple response format options (union)

```typescript
const emailFormat = z.object({ subject: z.string(), body: z.string(), to: z.array(z.string()) });
const calendarFormat = z.object({ title: z.string(), startTime: z.string(), attendees: z.array(z.string()) });

const agent = createAgent({
  model: "gpt-4.1",
  tools: [],
  responseFormat: [emailFormat, calendarFormat], // agent picks the appropriate format
});
```

### Accessing the result

```typescript
const result = await agent.invoke({ messages: [...] });

const textResponse = result.messages.at(-1)?.content;  // last AI message text
const structuredResponse = result.structuredResponse;  // typed structured object
```

---

## Middleware Integration

Middleware is the primary extensibility mechanism. Each middleware runs at defined points in the agent loop.

### createMiddleware API

```typescript
import { createMiddleware } from "langchain";

const myMiddleware = createMiddleware({
  name: "MyMiddleware",          // required string identifier
  stateSchema?: StateSchema,     // optional: extend agent state
  contextSchema?: z.ZodSchema,   // optional: type runtime.context
  beforeAgent?: (state) => Partial<AgentState> | void,
  beforeModel?: (state) => Partial<AgentState> | void
             | { canJumpTo?: JumpTarget[]; hook: (state) => ... },
  afterModel?: (state) => Partial<AgentState> | void,
  afterAgent?: (state) => Partial<AgentState> | void,
  wrapModelCall?: (request: ModelCallRequest, handler) => Promise<ModelCallResponse | Command>,
  wrapToolCall?: (request: ToolCallRequest, handler) => Promise<ToolCallResponse | Command>,
});
```

### Hook types

| Hook | Style | When it runs | Can return |
|---|---|---|---|
| `beforeAgent` | Node | Once before loop starts | `Partial<AgentState>` or `void` |
| `beforeModel` | Node (or object with `canJumpTo`) | Before each LLM call | State update, jump dict, or `void` |
| `afterModel` | Node | After each LLM response | `Partial<AgentState>` or `void` |
| `afterAgent` | Node | Once after loop ends | `Partial<AgentState>` or `void` |
| `wrapModelCall` | Wrap | Wraps the entire model call | `ModelCallResponse` or `Command` |
| `wrapToolCall` | Wrap | Wraps each tool execution | `ToolCallResponse` or `Command` |

### Execution order (multiple middleware in array)

1. `beforeAgent` — array order (first to last)
2. `beforeModel` — array order
3. `wrapModelCall` — nested (first middleware wraps all others)
4. Model executes
5. `afterModel` — **reverse** array order (last to first)
6. `afterAgent` — **reverse** array order

### ModelCallRequest shape

```typescript
interface ModelCallRequest {
  messages: Message[];        // current message list
  tools: Tool[];              // available tools
  model: BaseChatModel;       // current model instance (can be swapped)
  responseFormat?: ZodSchema; // structured output schema
  systemMessage: string;      // current system message
  state: AgentState;          // mutable short-term state
  runtime: AgentRuntime;      // context + store
}
```

### Agent jumps

From `beforeModel`, jump to a different node:

```typescript
const messageLimitMiddleware = createMiddleware({
  name: "MessageLimitCheck",
  beforeModel: {
    canJumpTo: ["end"],
    hook: (state) => {
      if (state.messages.length > 100) {
        return {
          messages: [new AIMessage("Conversation too long. Please start a new session.")],
          jumpTo: "end",
        };
      }
    },
  },
});
```

Valid `JumpTarget` values: `"end"` | `"tools"` | `"model"`

### State updates with Command from wrap hooks

```typescript
import { Command } from "@langchain/langgraph";

wrapModelCall: async (request, handler) => {
  const response = await handler(request);
  return new Command({
    update: { modelCallCount: (request.state.modelCallCount ?? 0) + 1 },
  });
}
```

---

## Built-in Middleware Reference

All importable from `"langchain"`.

| Middleware | Import name | Key Options |
|---|---|---|
| Summarization | `summarizationMiddleware` | `model` (req), `trigger: { tokens?, fraction?, messages? }`, `keep: { messages?, tokens?, fraction? }` (default `{ messages: 20 }`) |
| Human-in-the-loop | `humanInTheLoopMiddleware` | `interruptOn: Record<toolName, false \| { allowedDecisions: ("approve"\|"edit"\|"reject")[] }>` |
| Dynamic system prompt | `dynamicSystemPromptMiddleware` | Callback: `(state, runtime) => string` |
| Model call limit | `modelCallLimitMiddleware` | `threadLimit?`, `runLimit?`, `exitBehavior?: "end"\|"error"` (default `"end"`) |
| Tool call limit | `toolCallLimitMiddleware` | `toolName?`, `threadLimit?`, `runLimit?`, `exitBehavior?: "continue"\|"error"\|"end"` (default `"continue"`) |
| Model fallback | `modelFallbackMiddleware` | Variadic model string IDs, tried in order |
| PII protection | `piiMiddleware` | `piiType`: `"email"\|"credit_card"\|"ip"\|"mac_address"\|"url"`, `strategy?: "block"\|"redact"\|"mask"\|"hash"` |
| Todo list | `todoListMiddleware` | None — injects `write_todos` tool |
| LLM tool selector | `llmToolSelectorMiddleware` | `model?`, `systemPrompt?`, `maxTools?`, `alwaysInclude?: string[]` |
| Tool retry | `toolRetryMiddleware` | `maxRetries?` (2), `backoffFactor?` (2.0), `initialDelayMs?` (1000), `onFailure?: "error"\|"continue"\|fn` |
| Model retry | `modelRetryMiddleware` | Same options as `toolRetryMiddleware` |
| Tool emulator | `toolEmulatorMiddleware` | `tools?`, `model?` |
| Context editing | `contextEditingMiddleware` | `edits: ContextEdit[]` (default `[new ClearToolUsesEdit()]`) |
| Filesystem | `filesystemMiddleware` | None — provides `ls`, `read_file`, `write_file`, `edit_file` tools |

---

## Conversation Persistence

The `checkpointer` enables memory across invocations via a `thread_id`.

### MemorySaver (dev/testing)

```typescript
import { createAgent } from "langchain";
import { MemorySaver } from "@langchain/langgraph";

const agent = createAgent({
  model: "claude-sonnet-4-6",
  tools: [],
  checkpointer: new MemorySaver(),
});

const config = { configurable: { thread_id: "conversation-42" } };

// Turn 1
await agent.invoke(
  { messages: [{ role: "user", content: "Hi, I'm Bob!" }] },
  config
);

// Turn 2 — agent remembers Bob
const result = await agent.invoke(
  { messages: [{ role: "user", content: "What's my name?" }] },
  config
);
// result.messages.at(-1).content → "Your name is Bob."
```

### Production checkpointers

| Checkpointer | Package | Notes |
|---|---|---|
| `MemorySaver` | `@langchain/langgraph` | In-memory; lost on process restart |
| `PostgresSaver` | `@langchain/langgraph-checkpoint-postgres` | Durable; recommended for production |
| `AsyncPostgresSaver` | same | Async variant |
| Custom | Implement checkpoint interface | Redis, DynamoDB, etc. |

```typescript
import { PostgresSaver } from "@langchain/langgraph-checkpoint-postgres";

const checkpointer = PostgresSaver.fromConnString(
  "postgresql://user:pass@localhost:5432/mydb?sslmode=disable"
);

const agent = createAgent({ model: "gpt-4.1", tools: [], checkpointer });
```

**Rules:**
- Always pass `{ configurable: { thread_id: "..." } }` to `.invoke()` / `.stream()`.
- Without `thread_id`, agent has no memory between calls.
- Each `thread_id` is an isolated conversation — no cross-thread leakage.

### Conversation summarization

```typescript
import { createAgent, summarizationMiddleware } from "langchain";

const agent = createAgent({
  model: "gpt-4.1",
  tools: [],
  middleware: [
    summarizationMiddleware({
      model: "gpt-4.1-mini",       // cheaper model for summaries
      trigger: { tokens: 4000 },   // summarize when > 4000 tokens
      keep: { messages: 20 },      // keep latest 20 messages after summary
      trimTokensToSummarize: 4000,
    }),
  ],
  checkpointer: new MemorySaver(),
});
```

### Custom state schema for extended memory

```typescript
import { StateSchema } from "@langchain/langgraph";

const AgentState = new StateSchema({
  userId: z.string().optional(),
  preferences: z.record(z.string(), z.any()).default(() => ({})),
  sessionCount: z.number().default(0),
  // Underscore prefix fields are private — excluded from invoke() result
  _internalFlag: z.boolean().default(false),
});

const agent = createAgent({
  model: "gpt-4.1",
  tools: [],
  stateSchema: AgentState,
  checkpointer: new MemorySaver(),
});
```

---

## Agent Streaming

Three streaming modes, usable individually or combined.

### Mode comparison

| Mode | What it emits | Chunk shape | Use case |
|---|---|---|---|
| `"updates"` | State delta after each step | `{ [stepName]: { messages: Message[] } }` | Track agent progress |
| `"messages"` | LLM token tuples | `[token, { langgraph_node: string }]` | Token-by-token display |
| `"custom"` | User-defined data via `config.writer` | Any value | Progress indicators, tool logs |

### Mode: updates

```typescript
for await (const chunk of await agent.stream(
  { messages: [{ role: "user", content: "Weather in NYC?" }] },
  { streamMode: "updates" }
)) {
  const [stepName, content] = Object.entries(chunk)[0];
  console.log(`Step: ${stepName}`);  // "model" or "tools"
  console.log(JSON.stringify(content, null, 2));
}
```

Node names in v1: `"model"` (LLM calls), `"tools"` (tool executions). **Note:** In v0 the LLM node was named `"agent"` — this changed in v1.

### Mode: messages (token-by-token)

```typescript
for await (const [token, metadata] of await agent.stream(
  { messages: [{ role: "user", content: "Tell me about TypeScript" }] },
  { streamMode: "messages" }
)) {
  console.log(`Node: ${metadata.langgraph_node}`);
  for (const block of token.contentBlocks ?? []) {
    if (block.type === "text") process.stdout.write(block.text);
  }
}
```

### Mode: custom (tool-emitted progress)

```typescript
import { LangGraphRunnableConfig } from "@langchain/langgraph";

const progressTool = tool(
  async (input, config: LangGraphRunnableConfig) => {
    config.writer?.("Starting data fetch...");
    const data = await fetchData(input.query);
    config.writer?.("Data fetched, processing...");
    return data;
  },
  { name: "fetch_data", description: "Fetch and process data", schema: z.object({ query: z.string() }) }
);

for await (const message of await agent.stream(
  { messages: [{ role: "user", content: "Get report data" }] },
  { streamMode: "custom" }
)) {
  console.log(message); // "Starting data fetch...", "Data fetched, processing..."
}
```

### Multiple modes simultaneously

```typescript
for await (const [mode, chunk] of await agent.stream(
  { messages: [{ role: "user", content: "What is 2+2?" }] },
  { streamMode: ["updates", "messages", "custom"] }
)) {
  if (mode === "messages") {
    const [token] = chunk;
    process.stdout.write(token.contentBlocks?.find(b => b.type === "text")?.text ?? "");
  } else if (mode === "updates") {
    console.log("\n[step]", Object.keys(chunk)[0]);
  } else if (mode === "custom") {
    console.log("[custom]", chunk);
  }
}
```

### Streaming with thread_id

```typescript
const config = { configurable: { thread_id: "user-123-session-1" } };

for await (const chunk of await agent.stream(
  { messages: [{ role: "user", content: "Continue where we left off" }] },
  { ...config, streamMode: "updates" }
)) {
  console.log(Object.keys(chunk)[0]);
}
```

### Streaming reasoning tokens (Anthropic extended thinking)

```typescript
import { ChatAnthropic } from "@langchain/anthropic";

const agent = createAgent({
  model: new ChatAnthropic({
    model: "claude-sonnet-4-6",
    thinking: { type: "enabled", budget_tokens: 5000 },
  }),
  tools: [],
});

for await (const [token] of await agent.stream(
  { messages: [{ role: "user", content: "Solve this reasoning puzzle..." }] },
  { streamMode: "messages" }
)) {
  if (!token.contentBlocks) continue;
  for (const block of token.contentBlocks) {
    if (block.type === "reasoning") process.stdout.write(`[thinking] ${block.reasoning}`);
    if (block.type === "text") process.stdout.write(block.text);
  }
}
```

---

## Error Handling

### Tool error recovery via middleware

```typescript
const toolErrorMiddleware = createMiddleware({
  name: "ToolErrorHandler",
  wrapToolCall: async (request, handler) => {
    try {
      return await handler(request);
    } catch (error) {
      return {
        output: `Error executing ${request.toolCall.name}: ${error.message}. Try a different approach.`,
      };
    }
  },
});

const agent = createAgent({
  model: "gpt-4.1",
  tools: [unreliableTool],
  middleware: [toolErrorMiddleware],
});
```

### Automatic retry (built-in)

```typescript
import { toolRetryMiddleware, modelRetryMiddleware } from "langchain";

const agent = createAgent({
  model: "gpt-4.1",
  tools: [],
  middleware: [
    toolRetryMiddleware({
      maxRetries: 3,
      backoffFactor: 2.0,
      initialDelayMs: 1000,
      maxDelayMs: 60000,
      jitter: true,
      onFailure: "continue",   // send error message to agent; do not throw
    }),
    modelRetryMiddleware({
      maxRetries: 2,
      onFailure: "error",      // throw after max retries
    }),
  ],
});
```

### Model fallback (built-in)

```typescript
import { modelFallbackMiddleware } from "langchain";

const agent = createAgent({
  model: "gpt-4.1",
  tools: [],
  middleware: [
    modelFallbackMiddleware(   // variadic string IDs, tried in order
      "gpt-4.1-mini",
      "openai:gpt-3.5-turbo",
    ),
  ],
});
```

### Call limits (prevent infinite loops)

```typescript
import { modelCallLimitMiddleware, toolCallLimitMiddleware } from "langchain";

const agent = createAgent({
  model: "gpt-4.1",
  tools: [],
  middleware: [
    modelCallLimitMiddleware({
      runLimit: 10,             // max 10 model calls per invocation
      exitBehavior: "end",     // gracefully end (default); "error" throws instead
    }),
    toolCallLimitMiddleware({
      toolName: "web_search",  // omit to apply to all tools
      runLimit: 5,
      exitBehavior: "continue",
    }),
  ],
});
```

### PII protection

```typescript
import { piiMiddleware } from "langchain";

const agent = createAgent({
  model: "gpt-4.1",
  tools: [],
  middleware: [
    piiMiddleware("email", {
      strategy: "redact",   // "block" | "redact" | "mask" | "hash"
      applyToInput: true,   // redact incoming messages
      applyToOutput: false, // do not redact responses
    }),
    piiMiddleware("credit_card", { strategy: "mask" }),
  ],
});
```

---

## Human-in-the-Loop

Pauses agent execution before tool calls for human approval, editing, or rejection. Requires a `checkpointer`.

### Setup

```typescript
import { createAgent, humanInTheLoopMiddleware } from "langchain";
import { MemorySaver } from "@langchain/langgraph";

const agent = createAgent({
  model: "gpt-4.1",
  tools: [writeFileTool, executeSQLTool, readDataTool],
  middleware: [
    humanInTheLoopMiddleware({
      interruptOn: {
        write_file: true,                   // all decisions: approve, edit, reject
        execute_sql: {
          allowedDecisions: ["approve", "reject"],  // no editing allowed
          description: "SQL execution requires DBA approval",
        },
        read_data: false,                   // never interrupt
      },
    }),
  ],
  checkpointer: new MemorySaver(),          // required for HITL
});
```

### Invoking and handling interrupts

```typescript
import { Command } from "@langchain/langgraph";
import { HumanMessage } from "@langchain/core/messages";

const config = { configurable: { thread_id: "session_xyz" } };

// 1. Initial invocation — may pause at an interrupt
const result = await agent.invoke(
  { messages: [new HumanMessage("Delete records older than 1 year")] },
  config
);

// 2. Check for interrupt
if (result.__interrupt__) {
  console.log("Pending actions:", result.__interrupt__.action_requests);
}

// 3a. Approve
await agent.invoke(new Command({ resume: { decisions: [{ type: "approve" }] } }), config);

// 3b. Edit before execution
await agent.invoke(
  new Command({
    resume: {
      decisions: [{
        type: "edit",
        editedAction: {
          name: "execute_sql",
          args: { query: "UPDATE records SET status='archived' WHERE date < '2023-01-01'" },
        },
      }],
    },
  }),
  config
);

// 3c. Reject with feedback
await agent.invoke(
  new Command({
    resume: {
      decisions: [{ type: "reject", message: "Archive instead of deleting." }],
    },
  }),
  config
);
```

### humanInTheLoopMiddleware options

| Option | Type | Required | Description |
|---|---|---|---|
| `interruptOn` | `Record<toolName, false \| { allowedDecisions, description?, descriptionPrefix? }>` | Yes | Per-tool interrupt policy |
| `descriptionPrefix` | `string` | No | Global prefix for interrupt messages |

**Per-tool interrupt config:**

| Field | Type | Description |
|---|---|---|
| `allowedDecisions` | `("approve" \| "edit" \| "reject")[]` | Which decisions are available |
| `description` | `string` | Human-readable description |
| `descriptionPrefix` | `string` | Overrides global prefix for this tool |

---

## contextSchema and runtime.context

Use `contextSchema` + `runtime.context` to inject per-invocation, read-only data (user identity, tenant ID, feature flags) without polluting conversation messages.

```typescript
const contextSchema = z.object({
  userId: z.string(),
  tenantId: z.string(),
  apiKey: z.string().optional(),
});

const agent = createAgent({
  model: "gpt-4.1",
  tools: [fetchUserTool],
  contextSchema,
  middleware: [loggingMiddleware],
});

// Pass context at invocation time
await agent.invoke(
  { messages: [{ role: "user", content: "What's my account status?" }] },
  { context: { userId: "usr_123", tenantId: "tenant_abc" } }
);
```

Accessing in middleware:

```typescript
const loggingMiddleware = createMiddleware({
  name: "Logging",
  contextSchema,
  beforeModel: (_, runtime) => {
    console.log(`Request from userId: ${runtime.context?.userId}`);
  },
});
```

---

## Production Pattern — Full Stack

```typescript
import {
  createAgent,
  tool,
  dynamicSystemPromptMiddleware,
  modelRetryMiddleware,
  modelFallbackMiddleware,
  modelCallLimitMiddleware,
  toolCallLimitMiddleware,
  toolRetryMiddleware,
  piiMiddleware,
} from "langchain";
import { ChatOpenAI } from "@langchain/openai";
import { MemorySaver } from "@langchain/langgraph";
import { z } from "zod";

const contextSchema = z.object({ userId: z.string(), env: z.enum(["dev", "production"]) });

const searchTool = tool(
  async ({ query }) => `Results for: ${query}`,
  {
    name: "web_search",
    description: "Search the web for current information.",
    schema: z.object({ query: z.string().describe("Search query") }),
  }
);

const agent = createAgent({
  model: new ChatOpenAI({ model: "gpt-4o", temperature: 0 }),
  tools: [searchTool],
  contextSchema,
  checkpointer: new MemorySaver(),  // Replace with PostgresSaver in production
  middleware: [
    dynamicSystemPromptMiddleware<z.infer<typeof contextSchema>>((state, runtime) => {
      const now = new Date().toISOString();
      return `You are a production research assistant. Time: ${now}. User: ${runtime.context.userId}.`;
    }),
    piiMiddleware("email", { strategy: "redact", applyToInput: true }),
    modelRetryMiddleware({ maxRetries: 3 }),
    modelFallbackMiddleware("gpt-4o-mini", "openai:gpt-3.5-turbo"),
    modelCallLimitMiddleware({ runLimit: 10, exitBehavior: "end" }),
    toolCallLimitMiddleware({ runLimit: 15, exitBehavior: "continue" }),
    toolRetryMiddleware({ maxRetries: 2, onFailure: "continue" }),
  ],
});

const result = await agent.invoke(
  { messages: [{ role: "user", content: "Latest TypeScript features?" }] },
  {
    configurable: { thread_id: "prod-session-1" },
    context: { userId: "usr_123", env: "production" },
  }
);

console.log(result.messages.at(-1)?.content);
```

---

## v0 → v1 Migration Reference

| Aspect | v0 (createReactAgent) | v1 (createAgent) |
|---|---|---|
| Import | `@langchain/langgraph/prebuilt` | `langchain` |
| Function name | `createReactAgent` | `createAgent` |
| Model param | `llm: modelInstance` | `model: "provider:model"` or instance |
| System prompt param | `prompt: "..."` | `systemPrompt: "..."` |
| Dynamic prompts | Function arg | `dynamicSystemPromptMiddleware` |
| Pre/post hooks | `preModelHook`, `postModelHook` | `middleware: [createMiddleware({ beforeModel, afterModel })]` |
| Custom state | `stateSchema` annotation (`Annotation.Root`) | `stateSchema: new StateSchema({ ... })` |
| Return type | `CompiledStateGraph` | `ReactAgent` |
| LLM node name in streaming | `"agent"` | `"model"` |
| Runtime config | `config.configurable.*` | `invoke(input, { context: {...} })` |
| Structured output | `responseFormat: zodSchema` (bare) | `providerStrategy(schema)` or `toolStrategy(schema)` |
| Node.js minimum | 18+ | 20+ |

**Note:** `createReactAgent` from `@langchain/langgraph/prebuilt` is deprecated since LangGraph v0.3 and still present in v1.2.5 for migration purposes only. Do not use it for new code.
