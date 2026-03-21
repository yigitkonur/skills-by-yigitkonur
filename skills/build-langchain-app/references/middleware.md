# LangChain.js Middleware Reference

> Verified against langchain@1.2.35, @langchain/core@1.1.34, @langchain/langgraph@1.2.5 — March 2026
> Every middleware pattern was tested with anthropic/claude-sonnet-4-6 via OpenRouter.

---

## Overview

LangChain v1 introduced a middleware system for `createAgent` that intercepts model calls, tool calls, and agent lifecycle events. Middleware is the primary mechanism for adding retry logic, fallbacks, rate limits, logging, and human-in-the-loop approval to agents.

```typescript
import { createAgent } from "langchain";

const agent = createAgent({
  model,
  tools,
  middleware: [middleware1, middleware2, middleware3], // order matters
  prompt: "You are a helpful assistant.",
});
```

Middleware executes in array order: first middleware wraps second, which wraps third. For `beforeModel` hooks, first runs first. For `afterModel` hooks, last runs first (stack unwinding).

---

## Built-in Middleware

### modelRetryMiddleware

Automatically retries failed model calls with configurable retry count and exponential backoff.

```typescript
import { createAgent, modelRetryMiddleware } from "langchain";

// With defaults
const retry = modelRetryMiddleware();

// Custom config
const retry = modelRetryMiddleware({ maxRetries: 3 });

const agent = createAgent({
  model,
  tools: [myTool],
  middleware: [retry],
  prompt: "You are a helpful assistant.",
});
```

**API**: `modelRetryMiddleware(config?: { maxRetries?: number })` — optional config object.

---

### modelFallbackMiddleware

Falls back to alternative models when the primary model fails.

```typescript
import { createAgent, modelFallbackMiddleware } from "langchain";
import { ChatOpenAI } from "@langchain/openai";

const fallbackModel = new ChatOpenAI({
  model: "google/gemini-2.0-flash-001",
  configuration: {
    baseURL: "https://openrouter.ai/api/v1",
    apiKey: process.env.OPENROUTER_API_KEY,
  },
});

// ⚠️ CRITICAL: Spread args, NOT an options object
const fallback = modelFallbackMiddleware(fallbackModel);

// Multiple fallbacks — each is a separate argument
const fallback = modelFallbackMiddleware(fallback1, fallback2, fallback3);

const agent = createAgent({
  model: primaryModel,
  tools: [myTool],
  middleware: [fallback],
  prompt: "You are a helpful assistant.",
});
```

**API**: `modelFallbackMiddleware(...fallbackModels: BaseChatModel[])` — spread args.

⚠️ **Gotcha**: Using `{ models: [fallbackModel] }` causes `"llm [object Object] must define bindTools method"` because the plain object is treated as a "model" argument lacking `bindTools`.

⚠️ **Gotcha**: To test fallback, use a valid model name with an invalid API key. A nonexistent model name fails at setup time (not caught by fallback).

---

### modelCallLimitMiddleware

Limits the number of LLM invocations an agent can make per thread or per run.

```typescript
import { createAgent, modelCallLimitMiddleware } from "langchain";

// Thread-level limit
const limit = modelCallLimitMiddleware({ threadLimit: 10 });

// With exit behavior
const strictLimit = modelCallLimitMiddleware({
  threadLimit: 3,
  exitBehavior: "error", // throws when limit exceeded
});

// No limit (defaults)
const noLimit = modelCallLimitMiddleware();

const agent = createAgent({
  model,
  tools: [myTool],
  middleware: [limit],
  prompt: "You are a helpful assistant.",
});
```

**API**: `modelCallLimitMiddleware(options?: { threadLimit?: number, exitBehavior?: string })` — all optional.

---

### toolRetryMiddleware

Retries failed tool calls automatically.

```typescript
import { createAgent, toolRetryMiddleware } from "langchain";

const retry = toolRetryMiddleware({ maxRetries: 2 });

// Or with defaults
const retry = toolRetryMiddleware();

const agent = createAgent({
  model,
  tools: [myTool],
  middleware: [retry],
  prompt: "You are a helpful assistant.",
});
```

**API**: `toolRetryMiddleware(config?: { maxRetries?: number })` — optional config.

---

### toolCallLimitMiddleware

Limits the number of tool calls an agent can make.

```typescript
import { createAgent, toolCallLimitMiddleware } from "langchain";

// Run-level limit
const limit = toolCallLimitMiddleware({ runLimit: 5 });

// Thread-level limit
const limit = toolCallLimitMiddleware({ threadLimit: 10 });

// Both
const limit = toolCallLimitMiddleware({ threadLimit: 10, runLimit: 5 });

const agent = createAgent({
  model,
  tools: [myTool],
  middleware: [limit],
  prompt: "You are a research assistant.",
});
```

**API**: `toolCallLimitMiddleware({ threadLimit?: number, runLimit?: number })` — at least one required.

⚠️ **Gotcha**: The parameter names are `runLimit` and `threadLimit`, NOT `maxToolCalls`. Using `{ maxToolCalls: 5 }` causes `"At least one limit is specified"` error.

---

### summarizationMiddleware

Automatically summarizes long conversations to stay within context window limits.

```typescript
import { createAgent, summarizationMiddleware } from "langchain";

const summarize = summarizationMiddleware({
  maxMessages: 20,
  model, // model used for summarization (can differ from agent model)
});

const agent = createAgent({
  model,
  tools: [myTool],
  middleware: [summarize],
  prompt: "You are a helpful assistant.",
});
```

**API**: `summarizationMiddleware({ maxMessages?: number, model?: BaseChatModel })` — configures trigger point and summarization model.

---

### humanInTheLoopMiddleware

Sets up human-in-the-loop approval gates for tool calls. Requires a LangGraph checkpointer for full interrupt/resume flow.

```typescript
import { createAgent, humanInTheLoopMiddleware } from "langchain";

// All tools require approval
const hitl = humanInTheLoopMiddleware();

// Only specific tools require approval
const hitl = humanInTheLoopMiddleware({
  toolsRequiringApproval: ["dangerous_tool", "delete_records"],
});

const agent = createAgent({
  model,
  tools: [safeTool, dangerousTool],
  middleware: [hitl],
  prompt: "You are a helpful assistant.",
});
```

**API**: `humanInTheLoopMiddleware(options?: { toolsRequiringApproval?: string[] })`

**Note**: Full HITL requires running the agent with a checkpointer and handling `interrupt()` / `Command` resume. See the interrupt pattern below.

---

### dynamicSystemPromptMiddleware

Generates system prompts at runtime based on state, context, or external data.

```typescript
import { createAgent, dynamicSystemPromptMiddleware } from "langchain";

const dynamicPrompt = dynamicSystemPromptMiddleware((state) => {
  const timeOfDay = new Date().getHours() < 12 ? "morning" : "afternoon";
  return `Good ${timeOfDay}! You are a helpful assistant. User timezone: ${state.context?.timezone ?? "UTC"}.`;
});

const agent = createAgent({
  model,
  tools: [myTool],
  middleware: [dynamicPrompt],
  prompt: "Base system prompt (merged with dynamic output).",
});
```

**API**: `dynamicSystemPromptMiddleware(fn: (state) => string)` — function receives agent state, returns prompt string.

**Note**: As of v1.1.0, dynamic system prompt return values are additive — they merge with the base prompt rather than replacing it.

---

### piiRedactionMiddleware

Detects and redacts personally identifiable information from messages before they reach the model.

```typescript
import { createAgent, piiRedactionMiddleware } from "langchain";

const pii = piiRedactionMiddleware;

const agent = createAgent({
  model,
  tools: [myTool],
  middleware: [pii],
  prompt: "You are a helpful assistant.",
});
```

**API**: `piiRedactionMiddleware` — no configuration needed, used as-is.

---

### anthropicPromptCachingMiddleware

Enables Anthropic's prompt caching to reduce costs and latency for repeated prefixes.

```typescript
import { createAgent, anthropicPromptCachingMiddleware } from "langchain";

const caching = anthropicPromptCachingMiddleware;

const agent = createAgent({
  model, // must be an Anthropic model
  tools: [myTool],
  middleware: [caching],
  prompt: "You are a helpful assistant.",
});
```

**API**: `anthropicPromptCachingMiddleware` — no configuration needed. Only effective with Anthropic models.

---

### toolEmulatorMiddleware

Emulates tool calling for models that don't natively support function/tool calling.

```typescript
import { createAgent, toolEmulatorMiddleware } from "langchain";

const emulator = toolEmulatorMiddleware;

const agent = createAgent({
  model, // a model without native tool support
  tools: [myTool],
  middleware: [emulator],
  prompt: "You are a helpful assistant.",
});
```

**API**: `toolEmulatorMiddleware` — no configuration needed. Injects tool descriptions into the prompt and parses tool calls from model output.

---

## Custom Middleware

### createMiddleware

Build custom middleware with hooks for model calls, tool calls, and the full agent lifecycle.

```typescript
import { createMiddleware, ToolMessage } from "langchain";

const loggingMiddleware = createMiddleware({
  name: "RequestLogger",

  // Runs before model is called
  beforeModel: async (request) => {
    console.log("[Model Request]", request.messages.length, "messages");
    // Return undefined to pass through, or return modified request
  },

  // Runs after model responds
  afterModel: async (response) => {
    console.log("[Model Response]", response.content?.length, "chars");
    // Return undefined to pass through, or return modified response
  },

  // Wraps the entire model call — full control
  wrapModelCall: async (request, handler) => {
    const start = Date.now();
    try {
      const result = await handler(request);
      console.log(`[Model] ${Date.now() - start}ms`);
      return result;
    } catch (error) {
      console.error(`[Model Error] ${error}`);
      throw error;
    }
  },

  // Wraps tool execution — full control
  wrapToolCall: async (request, handler) => {
    try {
      return await handler(request);
    } catch (error) {
      // Graceful recovery: return error as ToolMessage instead of crashing
      return new ToolMessage({
        content: `Tool error: ${error}. Please check input and retry.`,
        tool_call_id: request.toolCall.id!,
      });
    }
  },
});
```

**API**: `createMiddleware({ name, beforeModel?, afterModel?, wrapModelCall?, wrapToolCall? })`

### Hook Execution Order

When multiple middleware are stacked `[A, B, C]`:

1. `A.beforeModel` → `B.beforeModel` → `C.beforeModel` (forward order)
2. Model call executes (innermost `wrapModelCall` wraps the actual call)
3. `C.afterModel` → `B.afterModel` → `A.afterModel` (reverse/stack-unwinding order)

For `wrapModelCall` and `wrapToolCall`, middleware wraps like an onion: A wraps B wraps C wraps the actual call.

---

### Custom Error Handling with wrapToolCall

Gracefully recover from tool errors by returning a `ToolMessage` instead of crashing:

```typescript
import { createMiddleware, ToolMessage } from "langchain";

const handleToolErrors = createMiddleware({
  name: "HandleToolErrors",
  wrapToolCall: async (request, handler) => {
    try {
      return await handler(request);
    } catch (error) {
      return new ToolMessage({
        content: `Tool "${request.toolCall.name}" failed: ${error}. Try different parameters.`,
        tool_call_id: request.toolCall.id!,
      });
    }
  },
});
```

This lets the model see the error and decide how to proceed (retry with different params, use a different tool, or respond to the user) instead of the entire agent crashing.

---

### Custom Model Fallback with wrapModelCall

Switch models on error within a single middleware:

```typescript
import { createMiddleware } from "langchain";

const modelFallback = createMiddleware({
  name: "ModelFallback",
  wrapModelCall: async (request, handler) => {
    try {
      return await handler(request);
    } catch (error) {
      console.warn(`Primary model failed: ${error}. Falling back.`);
      // Swap to cheaper/more reliable model and retry
      return handler({ ...request, model: "openai:gpt-4o-mini" });
    }
  },
});
```

---

### Logging Middleware with beforeModel / afterModel

Log request and response metadata without modifying them:

```typescript
import { createMiddleware } from "langchain";

const requestLogger = createMiddleware({
  name: "RequestLogger",
  beforeModel: async (request) => {
    console.log(JSON.stringify({
      timestamp: new Date().toISOString(),
      messageCount: request.messages.length,
      lastMessage: request.messages.at(-1)?.content?.toString().slice(0, 100),
    }));
    // Return undefined — passes request through unmodified
  },
  afterModel: async (response) => {
    console.log(JSON.stringify({
      timestamp: new Date().toISOString(),
      responseLength: typeof response.content === "string" ? response.content.length : 0,
      toolCalls: response.tool_calls?.length ?? 0,
    }));
    // Return undefined — passes response through unmodified
  },
});
```

---

## Middleware Composition

### Stacking Multiple Middleware

Order matters. Place error-handling middleware (retry, fallback) outermost (first in array) so they catch errors from inner middleware and the model/tool call itself.

```typescript
import {
  createAgent,
  modelRetryMiddleware,
  modelFallbackMiddleware,
  modelCallLimitMiddleware,
  toolCallLimitMiddleware,
  toolRetryMiddleware,
} from "langchain";

const agent = createAgent({
  model: primaryModel,
  tools: [myTool],
  middleware: [
    // Outermost — catches all errors, retries the full chain
    modelRetryMiddleware({ maxRetries: 3 }),
    // Falls back if primary model fails even after retries
    modelFallbackMiddleware(fallbackModel1, fallbackModel2),
    // Safety limits
    modelCallLimitMiddleware({ threadLimit: 20 }),
    toolCallLimitMiddleware({ runLimit: 10 }),
    // Innermost retry — retries individual tool failures
    toolRetryMiddleware({ maxRetries: 2 }),
  ],
  prompt: "You are a production assistant.",
});
```

### Production Middleware Stack Example

A comprehensive stack for production agents:

```typescript
import {
  createAgent,
  createMiddleware,
  modelRetryMiddleware,
  modelFallbackMiddleware,
  modelCallLimitMiddleware,
  toolCallLimitMiddleware,
  toolRetryMiddleware,
  summarizationMiddleware,
  ToolMessage,
} from "langchain";

// Custom: log all model calls for observability
const observability = createMiddleware({
  name: "Observability",
  beforeModel: async (request) => {
    console.log(`[${new Date().toISOString()}] Model call: ${request.messages.length} msgs`);
  },
  afterModel: async (response) => {
    console.log(`[${new Date().toISOString()}] Response: ${response.tool_calls?.length ?? 0} tool calls`);
  },
});

// Custom: graceful tool error recovery
const toolErrorRecovery = createMiddleware({
  name: "ToolErrorRecovery",
  wrapToolCall: async (request, handler) => {
    try {
      return await handler(request);
    } catch (error) {
      return new ToolMessage({
        content: `Tool "${request.toolCall.name}" error: ${error}. Try a different approach.`,
        tool_call_id: request.toolCall.id!,
      });
    }
  },
});

const agent = createAgent({
  model: primaryModel,
  tools,
  middleware: [
    observability,                                    // logging (outermost)
    modelRetryMiddleware({ maxRetries: 3 }),           // retry on transient failures
    modelFallbackMiddleware(fallbackModel),            // model failover
    modelCallLimitMiddleware({ threadLimit: 50 }),     // prevent runaway loops
    toolCallLimitMiddleware({ runLimit: 20 }),         // limit tool usage
    summarizationMiddleware({ maxMessages: 30 }),      // context window management
    toolRetryMiddleware({ maxRetries: 2 }),            // retry failed tools
    toolErrorRecovery,                                 // graceful tool failures
  ],
  prompt: "You are a production assistant.",
});
```

---

## LangGraph interrupt() for Human-in-the-Loop

The `interrupt()` function pauses graph execution and waits for human input. Resume with `Command`.

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

// ⚠️ CRITICAL: Must use checkpointer — interrupt() is a no-op without one
const checkpointer = new MemorySaver();
const app = graph.compile({ checkpointer });

const config = { configurable: { thread_id: "my-thread" } };

// Step 1: Run until interrupt
const result1 = await app.invoke({ input: "test data" }, config);
// result1.__interrupt__ contains the interrupt payload

// Step 2: Resume with Command
const result2 = await app.invoke(new Command({ resume: "yes" }), config);
// result2 = { input: "test data", approved: true, result: "Processed: test data" }
```

⚠️ **Gotcha**: `interrupt()` requires a `MemorySaver` (or other checkpointer). Without one, it silently does nothing.

⚠️ **Gotcha**: Resume with `new Command({ resume: value })`, NOT `{ resume: value }`. A plain object triggers another interrupt instead of resuming.

---

## Summary Table

| Middleware | Import | API | Key Options |
|---|---|---|---|
| `modelRetryMiddleware` | `langchain` | `(config?)` | `maxRetries` |
| `modelFallbackMiddleware` | `langchain` | `(...models)` | Spread args — NOT object |
| `modelCallLimitMiddleware` | `langchain` | `(opts?)` | `threadLimit`, `exitBehavior` |
| `toolRetryMiddleware` | `langchain` | `(config?)` | `maxRetries` |
| `toolCallLimitMiddleware` | `langchain` | `({ threadLimit?, runLimit? })` | NOT `maxToolCalls` |
| `summarizationMiddleware` | `langchain` | `({ maxMessages?, model? })` | Summarization trigger + model |
| `humanInTheLoopMiddleware` | `langchain` | `(opts?)` | `toolsRequiringApproval` |
| `dynamicSystemPromptMiddleware` | `langchain` | `(fn)` | Function receiving state |
| `piiRedactionMiddleware` | `langchain` | constant | No config |
| `anthropicPromptCachingMiddleware` | `langchain` | constant | No config, Anthropic only |
| `toolEmulatorMiddleware` | `langchain` | constant | No config |
| `createMiddleware` | `langchain` | `({ name, ...hooks })` | `beforeModel`, `afterModel`, `wrapModelCall`, `wrapToolCall` |
| `interrupt()` | `@langchain/langgraph` | `(payload)` | Requires checkpointer |
| `Command` | `@langchain/langgraph` | `new Command({ resume })` | Resume interrupted graphs |
