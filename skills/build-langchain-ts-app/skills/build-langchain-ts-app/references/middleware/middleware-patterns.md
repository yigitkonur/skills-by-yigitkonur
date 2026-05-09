# Middleware: Custom Patterns & Guardrails Reference

Patterns for building custom middleware and guardrails with `createMiddleware()`. APIs verified against `langchain@1.2.35`, `@langchain/core@1.1.34`, `@langchain/langgraph@1.2.5`. TypeScript only.

---

## Quick Reference — Imports

```typescript
import {
  createAgent,
  createMiddleware,
  initChatModel,
  piiMiddleware,
  piiRedactionMiddleware,
  humanInTheLoopMiddleware,
  openAIModerationMiddleware,
  modelCallLimitMiddleware,
  toolCallLimitMiddleware,
  summarizationMiddleware,
  contextEditingMiddleware,
  ClearToolUsesEdit,
  modelRetryMiddleware,
  toolRetryMiddleware,
  modelFallbackMiddleware,
} from "langchain";

import { MemorySaver, Command } from "@langchain/langgraph";
import { AIMessage, HumanMessage, SystemMessage, RemoveMessage } from "@langchain/core/messages";
import { ContextOverflowError, ModelAbortError } from "@langchain/core/errors";
import { type ToolRuntime } from "@langchain/core/tools";
import { REMOVE_ALL_MESSAGES } from "@langchain/langgraph";
import { trimMessages } from "langchain";
import { z } from "zod";
```

---

## createMiddleware() Full Signature

The `createMiddleware()` factory builds custom middleware with full TypeScript type safety.

```typescript
import { createMiddleware } from "langchain";
import { z } from "zod";

createMiddleware({
  name: string;                   // Required — displayed in LangSmith traces

  // Optional schemas for type safety
  stateSchema?: ZodObject;        // Extends agent's persisted LangGraph state
  contextSchema?: ZodObject;      // Read-only per-invocation context

  // Node-style hooks — two forms:
  // 1. Simple function (no jumpTo capability)
  // 2. Object { hook, canJumpTo } — required when hook may return jumpTo
  beforeAgent?:
    | ((state: AgentState) => HookResult | void | Promise<HookResult | void>)
    | { hook: (state: AgentState) => HookResult | void | Promise<HookResult | void>; canJumpTo: string[] };

  afterAgent?:
    | ((state: AgentState) => HookResult | void | Promise<HookResult | void>)
    | { hook: (state: AgentState) => HookResult | void | Promise<HookResult | void>; canJumpTo: string[] };

  beforeModel?:
    | ((state: AgentState) => HookResult | void | Promise<HookResult | void>)
    | { hook: (state: AgentState) => HookResult | void | Promise<HookResult | void>; canJumpTo: string[] };

  afterModel?:
    | ((state: AgentState) => HookResult | void | Promise<HookResult | void>)
    | { hook: (state: AgentState) => HookResult | void | Promise<HookResult | void>; canJumpTo: string[] };

  // Wrap-style hooks — surround execution, control retries
  wrapModelCall?: (
    request: ModelCallRequest,
    handler: (req: ModelCallRequest) => Promise<ModelResponse>
  ) => Promise<ModelResponse | Command>;

  wrapToolCall?: (
    request: ToolCallRequest,
    handler: (req: ToolCallRequest) => Promise<ToolCallResult>
  ) => Promise<ToolCallResult | Command>;
})
```

---

## HookResult Type

Returned from node-style hooks to update agent state and optionally redirect execution.

```typescript
type HookResult = {
  messages?: BaseMessage[];       // Messages to add/replace in state
  jumpTo?: "end" | "tools" | "model";  // Early exit or redirect target
  [key: string]: unknown;         // Any custom state fields defined in stateSchema
};
```

**`jumpTo` targets:**

| Target | Effect |
|---|---|
| `"end"` | Terminate agent execution; `afterAgent` hooks still run before stopping |
| `"tools"` | Jump directly to tool execution node (skip model call) |
| `"model"` | Jump to model call node (passes through `beforeModel` hooks) |

**`canJumpTo` is required** when a node-style hook may return `jumpTo`. Every target the hook might use must be declared:

```typescript
beforeAgent: {
  canJumpTo: ["end"],    // declare every possible jumpTo target
  hook: (state) => {
    if (!state.messages.length) {
      return { messages: [new AIMessage("No input.")], jumpTo: "end" };
    }
  },
},
```

---

## ModelCallRequest Shape

The `request` object passed to `wrapModelCall`. Mutate and forward to `handler()` to transform what the model sees.

```typescript
type ModelCallRequest = {
  messages: BaseMessage[];          // current message history
  systemMessage: SystemMessage;     // current system message — supports .concat()
  model: BaseChatModel;             // current model instance — can be replaced
  tools: (ClientTool | ServerTool)[];  // available tools — can be filtered/replaced
  runtime: {
    context: unknown;               // typed if contextSchema provided
    store?: BaseStore;              // long-term memory store
    streamWriter?: StreamWriter;    // write custom stream events
  };
};
```

**System message augmentation pattern:**
```typescript
import { createMiddleware } from "langchain";

const contextEnrichMiddleware = createMiddleware({
  name: "ContextEnrich",
  wrapModelCall: (req, handler) =>
    handler({
      ...req,
      systemMessage: req.systemMessage.concat("Additional context: user is in EU jurisdiction."),
    }),
});
```

**Anthropic cache-control on a system message block:**
```typescript
import { createMiddleware } from "langchain";
import { SystemMessage } from "@langchain/core/messages";

const cachedSystemPromptMiddleware = createMiddleware({
  name: "CachedSystemPrompt",
  wrapModelCall: (req, handler) =>
    handler({
      ...req,
      systemMessage: req.systemMessage.concat(
        new SystemMessage({
          content: [{
            type: "text",
            text: "Stable knowledge block that rarely changes.",
            cache_control: { type: "ephemeral", ttl: "5m" },
          }],
        })
      ),
    }),
});
```

---

## jumpTo Targets and Agent Jumps

`jumpTo` is the mechanism for early exit and conditional routing from node-style hooks.

```typescript
import { createMiddleware, AIMessage } from "langchain";

// Short-circuit the entire agent run from beforeAgent
const authCheckMiddleware = createMiddleware({
  name: "AuthCheck",
  contextSchema: z.object({ userId: z.string().optional() }),
  beforeAgent: {
    canJumpTo: ["end"],
    hook: (state, runtime) => {
      if (!runtime.context.userId) {
        return {
          messages: [new AIMessage("Authentication required.")],
          jumpTo: "end",   // afterAgent hooks still run
        };
      }
    },
  },
});

// Jump directly to tools (skip model call) — useful when tool to run is known
const forcedToolMiddleware = createMiddleware({
  name: "ForcedTool",
  beforeModel: {
    canJumpTo: ["tools"],
    hook: (state) => {
      const lastMsg = state.messages?.[state.messages.length - 1];
      if (lastMsg?.content.toString().startsWith("/run:")) {
        // Inject a pre-formed tool call and jump directly to execution
        return { jumpTo: "tools" };
      }
    },
  },
});

// Jump back to model from afterModel (re-prompt after validation failure)
const revalidationMiddleware = createMiddleware({
  name: "Revalidation",
  afterModel: {
    canJumpTo: ["model", "end"],
    hook: (state) => {
      const last = state.messages?.[state.messages.length - 1];
      if (last?._getType() === "ai" && last.content.toString().includes("I don't know")) {
        // Add a correction message and re-run the model
        return {
          messages: [new HumanMessage("Please provide a more specific answer.")],
          jumpTo: "model",
        };
      }
    },
  },
});
```

---

## Guardrail Patterns

Guardrails are middleware hooks that enforce safety, compliance, and quality at each lifecycle point.

| Strategy | Latency | Cost | Best For |
|---|---|---|---|
| **Deterministic** | ~0–5ms | Negligible | Keyword blocking, regex PII, schema validation |
| **Model-based** | ~50–500ms | API call cost | Semantic safety, nuanced content policy |

**Production best practice:** Cheapest/fastest guardrails first, model-based last.

**Four guardrail lifecycle positions:**

| Position | Hook | Best For |
|---|---|---|
| Before agent starts | `beforeAgent` | Auth check, keyword filter, schema validation |
| Before each model call | `beforeModel` | PII redaction, token budget enforcement |
| After each model response | `afterModel` | Output quality check, format validation |
| After agent completes | `afterAgent` | Final safety review, compliance logging |

### Deterministic: Input Keyword Filter (`beforeAgent`)

Runs once before any processing. Zero LLM cost.

```typescript
import { createMiddleware, AIMessage } from "langchain";

const contentFilterMiddleware = (bannedKeywords: string[]) => {
  const keywords = bannedKeywords.map((k) => k.toLowerCase());
  return createMiddleware({
    name: "ContentFilterMiddleware",
    beforeAgent: {
      canJumpTo: ["end"],
      hook: (state) => {
        const first = state.messages?.[0];
        if (!first || first._getType() !== "human") return;
        const text = first.content.toString().toLowerCase();
        for (const kw of keywords) {
          if (text.includes(kw)) {
            return {
              messages: [new AIMessage("I cannot process requests containing inappropriate content.")],
              jumpTo: "end",
            };
          }
        }
      },
    },
  });
};

// Usage
middleware: [contentFilterMiddleware(["hack", "exploit", "jailbreak"])]
```

### Deterministic: Token/Cost Guard (`beforeModel`)

Runs before every model call to enforce budget limits without an LLM call.

```typescript
import { createMiddleware, AIMessage } from "langchain";

const costGuardMiddleware = (maxEstimatedTokens: number) =>
  createMiddleware({
    name: "CostGuardMiddleware",
    beforeModel: {
      canJumpTo: ["end"],
      hook: (state) => {
        const totalChars = state.messages.reduce(
          (sum, m) => sum + m.content.toString().length, 0
        );
        if (Math.ceil(totalChars / 4) > maxEstimatedTokens) {
          return {
            messages: [new AIMessage("Request too large. Please shorten your input.")],
            jumpTo: "end",
          };
        }
      },
    },
  });

const messageLimitMiddleware = (maxMessages = 50) =>
  createMiddleware({
    name: "MessageLimitMiddleware",
    beforeModel: {
      canJumpTo: ["end"],
      hook: (state) => {
        if (state.messages.length >= maxMessages) {
          return {
            messages: [new AIMessage("Conversation limit reached.")],
            jumpTo: "end",
          };
        }
      },
    },
  });
```

### Model-Based: Output Safety Check (`afterAgent`)

Runs after the full agent response is produced. Most expensive — place last.

```typescript
import { createMiddleware, AIMessage, initChatModel } from "langchain";

const safetyGuardrailMiddleware = () => {
  const safetyModel = initChatModel("openai:gpt-4.1-mini");
  return createMiddleware({
    name: "SafetyGuardrailMiddleware",
    afterAgent: {
      canJumpTo: ["end"],
      hook: async (state) => {
        const last = state.messages?.[state.messages.length - 1];
        if (!last || last._getType() !== "ai") return;
        const verdict = await safetyModel.invoke([{
          role: "user",
          content: `Evaluate: is this response safe? Reply ONLY "SAFE" or "UNSAFE".\nResponse: ${last.content}`,
        }]);
        if (verdict.content.toString().includes("UNSAFE")) {
          return {
            messages: [new AIMessage("I cannot provide that response. Please rephrase.")],
            jumpTo: "end",
          };
        }
      },
    },
  });
};
```

---

## PII Filtering Patterns

### Stack Multiple `piiMiddleware` Instances

Each instance handles one PII type. They compose additively.

```typescript
import { createAgent, piiMiddleware, type PIIMatch } from "langchain";

function detectSSN(content: string): PIIMatch[] {
  const matches: PIIMatch[] = [];
  const pattern = /\d{3}-\d{2}-\d{4}/g;
  let match: RegExpExecArray | null;
  while ((match = pattern.exec(content)) !== null) {
    matches.push({ text: match[0], start: match.index!, end: match.index! + match[0].length });
  }
  return matches;
}

const agent = createAgent({
  model: "openai:gpt-4.1",
  tools: [customerServiceTool, emailTool],
  middleware: [
    piiMiddleware("email", { strategy: "redact", applyToInput: true }),
    piiMiddleware("credit_card", { strategy: "mask", applyToInput: true }),
    piiMiddleware("email", { strategy: "redact", applyToOutput: true }),
    piiMiddleware("ssn", { detector: detectSSN, strategy: "hash", applyToInput: true }),
    piiMiddleware("api_key", {
      detector: /sk-[a-zA-Z0-9]{32}/,
      strategy: "block",
      applyToInput: true,
    }),
  ],
});
```

### Full Round-Trip Protection with `piiRedactionMiddleware`

Redacts before model call and automatically restores original values in AI output. Suitable when the model must process anonymized data but the final user response should show real values.

```typescript
import { createAgent, piiRedactionMiddleware } from "langchain";
import { HumanMessage } from "@langchain/core/messages";

const agent = createAgent({
  model: "openai:gpt-4.1",
  tools: [lookupUserTool],
  middleware: [
    piiRedactionMiddleware({
      rules: {
        ssn:   /\b\d{3}-?\d{2}-?\d{4}\b/g,
        email: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g,
        phone: /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g,
      },
    }),
  ],
});

// Override rules per-invocation via configurable
await agent.invoke(
  { messages: [new HumanMessage("Look up SSN 123-45-6789")] },
  {
    configurable: {
      PIIRedactionMiddleware: {
        rules: { ssn: /\b\d{3}-?\d{2}-?\d{4}\b/g },
      },
    },
  }
);
```

---

## contextSchema and Runtime Context

`contextSchema` is the primary mechanism for typed dependency injection into agents, tools, and middleware without global state.

### Full Typed Dependency Injection Pattern

```typescript
import { z } from "zod";
import { createAgent, createMiddleware } from "langchain";
import { tool } from "langchain";
import { type ToolRuntime } from "@langchain/core/tools";
import { AIMessage } from "@langchain/core/messages";

// 1. Define the context shape with Zod
const contextSchema = z.object({
  userId: z.string(),
  tenantId: z.string(),
  dbConnection: z.custom<DatabaseClient>(),
  featureFlags: z.record(z.boolean()).optional(),
});

// 2. Type-safe tool — receives context via runtime second argument
const queryDatabase = tool(
  async ({ query }, runtime: ToolRuntime<any, typeof contextSchema>) => {
    const { userId, dbConnection } = runtime.context;
    const rows = await dbConnection.query(query, { userId });
    return JSON.stringify(rows);
  },
  {
    name: "query_database",
    description: "Query the database for the current user",
    schema: z.object({ query: z.string() }),
  }
);

// 3. Type-safe middleware — auth guard using context
const authMiddleware = createMiddleware({
  name: "AuthMiddleware",
  contextSchema,
  beforeAgent: {
    canJumpTo: ["end"],
    hook: (state, runtime) => {
      if (!runtime.context.userId) {
        return {
          messages: [new AIMessage("Authentication required.")],
          jumpTo: "end",
        };
      }
    },
  },
});

// 4. Assemble — all components share the same contextSchema
const agent = createAgent({
  model: "openai:gpt-4.1",
  tools: [queryDatabase],
  middleware: [authMiddleware],
  contextSchema,
});

// 5. Pass context at invocation time
await agent.invoke(
  { messages: [{ role: "user", content: "Show my orders" }] },
  { context: { userId: "u123", tenantId: "acme", dbConnection: myDb } }
);
```

### Accessing Runtime Context in Middleware Hooks

```typescript
import { createMiddleware } from "langchain";
import { z } from "zod";

const contextSchema = z.object({
  tenantId: z.string(),
  userId: z.string(),
});

const loggingMiddleware = createMiddleware({
  name: "Logging",
  contextSchema,
  // Node-style hooks receive runtime as second argument
  beforeModel: (state, runtime) => {
    console.log(`[${runtime.context.tenantId}] Processing for: ${runtime.context.userId}`);
  },
  afterModel: (state, runtime) => {
    console.log(`[${runtime.context.tenantId}] Completed.`);
  },
  // Wrap-style hooks access context via req.runtime.context
  wrapModelCall: async (req, handler) => {
    const { tenantId } = req.runtime.context as { tenantId: string };
    return handler({
      ...req,
      systemMessage: req.systemMessage.concat(`\nTenant: ${tenantId}`),
    });
  },
});
```

### `configurable` vs `context`

| Feature | `configurable` | `context` (contextSchema) |
|---|---|---|
| Where defined | `RunnableConfig.configurable` | Second arg of `.invoke()`: `{ context: {...} }` |
| Validated | No — plain object | Yes — Zod schema validation at invocation |
| Persisted | Via checkpointer across turns | No — single invocation lifetime |
| Type-safe | No | Yes — TypeScript types inferred from Zod |
| Primary use | `thread_id`, feature flags, middleware overrides | Typed DI — user ID, DB connections, API keys |

---

## Context Window Management

### ContextOverflowError

Thrown when input tokens exceed the model's maximum context window. Import from `@langchain/core/errors`.

```typescript
import { ContextOverflowError } from "@langchain/core/errors";

// Pattern 1: Catch and retry with trimmed messages
try {
  await agent.invoke({ messages }, config);
} catch (err) {
  if (ContextOverflowError.isInstance(err)) {
    const trimmed = messages.slice(-10);  // keep last 10 messages
    return await agent.invoke({ messages: trimmed }, config);
  }
  throw err;
}
```

**`ContextOverflowError` properties:**
- `message: string` — description of the overflow
- `name: "ContextOverflowError"`
- `cause: Error` — the wrapped original error
- `static fromError(error): ContextOverflowError` — wrap an existing error
- `static isInstance(err): boolean` — type guard

### Proactive Token Budget Check

```typescript
import { initChatModel } from "langchain";

const model = await initChatModel("openai:gpt-4.1");
const { maxInputTokens } = model.profile;  // e.g., 128000

// Token budget formula
// message_budget = maxInputTokens - systemTokens - toolsTokens - outputReserve - (maxInputTokens * 0.05)
const budget = maxInputTokens - 2000;   // 2000 reserved for output
if (estimatedTokens > budget) {
  // trigger summarization or truncation before invoking
}
```

### Custom Trim Middleware

```typescript
import { createMiddleware } from "langchain";
import { trimMessages, RemoveMessage } from "@langchain/core/messages";
import { REMOVE_ALL_MESSAGES } from "@langchain/langgraph";

const trimMessageHistory = createMiddleware({
  name: "TrimMessages",
  beforeModel: async (state) => {
    const trimmed = await trimMessages(state.messages, {
      maxTokens: 4000,
      strategy: "last",           // keep most recent (alt: "first", "median", "greedy")
      startOn: "human",
      endOn: ["human", "tool"],   // trimmed list must end on human or tool message
      tokenCounter: (msgs) => msgs.reduce((sum, m) => sum + m.content.toString().length / 4, 0),
    });
    return {
      messages: [new RemoveMessage({ id: REMOVE_ALL_MESSAGES }), ...trimmed],
    };
  },
});
```

**`trimMessages` options:**

| Option | Type | Default | Description |
|---|---|---|---|
| `maxTokens` | `number` | required | Token budget after trimming |
| `strategy` | `"last" \| "first" \| "greedy" \| "median"` | `"greedy"` | Which messages to keep |
| `startOn` | `MessageType` | `undefined` | Message type to start counting from |
| `endOn` | `MessageType \| MessageType[]` | `undefined` | Message type(s) the trimmed list must end on |
| `tokenCounter` | `(msgs: BaseMessage[]) => number` | character-length / 4 | Custom token counting function |

---

## Middleware Composition Rules

### 7-Layer Production Ordering

| Layer | Category | What to Place Here |
|---|---|---|
| 1 (first) | Rate/cost limiters | `modelCallLimitMiddleware`, `toolCallLimitMiddleware`, cost guards |
| 2 | Input validation & PII | Content filters, `piiMiddleware`, `piiRedactionMiddleware` |
| 3 | Context management | `summarizationMiddleware`, `contextEditingMiddleware` |
| 4 | Tool selection | `llmToolSelectorMiddleware` |
| 5 | Retry & resilience | `modelRetryMiddleware`, `toolRetryMiddleware` |
| 6 | Fallbacks | `modelFallbackMiddleware` |
| 7 (last) | Output validation & safety | `humanInTheLoopMiddleware`, `openAIModerationMiddleware`, semantic guardrails |

**Why this order:**
- Rate limiters first: prevent runaway costs before any processing occurs
- Input validation second: screen bad input before it touches the model
- Context management third: shape what the model sees
- Retries wrap actual execution: failures route through retry logic before fallbacks
- Output checks last: model-based checks on `afterModel`/`afterAgent` run in reverse order (last in array = first on exit), so placing them last in the array means they see output first

### Full Production Stack Example

```typescript
import {
  createAgent,
  contentFilterMiddleware,
  piiMiddleware,
  piiRedactionMiddleware,
  summarizationMiddleware,
  contextEditingMiddleware,
  ClearToolUsesEdit,
  llmToolSelectorMiddleware,
  modelRetryMiddleware,
  toolRetryMiddleware,
  modelFallbackMiddleware,
  humanInTheLoopMiddleware,
  openAIModerationMiddleware,
  modelCallLimitMiddleware,
  toolCallLimitMiddleware,
} from "langchain";
import { MemorySaver } from "@langchain/langgraph";

const productionAgent = createAgent({
  model: "openai:gpt-4.1",
  tools: [...],
  middleware: [
    // Layer 1: Cost & call limits (synchronous, ~0ms)
    modelCallLimitMiddleware({ threadLimit: 50, runLimit: 20, exitBehavior: "end" }),
    toolCallLimitMiddleware({ runLimit: 30, exitBehavior: "end" }),

    // Layer 2: Input screening
    contentFilterMiddleware(["hack", "exploit", "malware"]),
    piiMiddleware("email", { strategy: "redact", applyToInput: true }),
    piiMiddleware("credit_card", { strategy: "mask", applyToInput: true }),

    // Layer 3: Context management
    summarizationMiddleware({
      model: "openai:gpt-4.1-mini",
      trigger: { fraction: 0.75 },
      keep: { messages: 25 },
    }),
    contextEditingMiddleware({
      edits: [new ClearToolUsesEdit({ trigger: { tokens: 80000 }, keep: { messages: 5 } })],
    }),

    // Layer 4: Tool selection (for agents with many tools)
    llmToolSelectorMiddleware({ model: "openai:gpt-4.1-mini", maxTools: 8 }),

    // Layer 5: Resilience
    modelRetryMiddleware({
      maxRetries: 3,
      retryOn: (err) => (err as any).status === 429 || (err as any).status >= 500,
    }),
    toolRetryMiddleware({ maxRetries: 2, backoffFactor: 2, jitter: true }),

    // Layer 6: Fallback
    modelFallbackMiddleware("openai:gpt-4.1-mini"),

    // Layer 7: Human approval + output safety
    humanInTheLoopMiddleware({
      interruptOn: { delete_records: true, send_email: true },
    }),
    openAIModerationMiddleware({ checkInput: false, checkOutput: true }),
    safetyGuardrailMiddleware(),
  ],
  checkpointer: new MemorySaver(),
  contextSchema,
});
```

### Hook Decision Guide

| Need | Use |
|---|---|
| Log before model call | `beforeModel` (node-style) |
| Modify what goes to model | `wrapModelCall` with `systemMessage.concat()` or modified `messages` |
| Retry model calls | `wrapModelCall` with retry loop, or `modelRetryMiddleware` |
| Inspect model output | `afterModel` (node-style) |
| Block bad output | `afterModel` or `afterAgent` with `jumpTo: "end"` |
| Retry tool calls | `wrapToolCall` (wrap-style), or `toolRetryMiddleware` |
| Cache tool results | `wrapToolCall` with cache check before calling handler |
| Run once at agent start | `beforeAgent` |
| Clean up after agent | `afterAgent` |
| Dynamic system prompt | `dynamicSystemPromptMiddleware` or `wrapModelCall` |
| Inject per-request data | `contextSchema` + `wrapModelCall` with `req.runtime.context` |

---

## Advanced Custom Patterns

### Telemetry Middleware (stateSchema + contextSchema)

```typescript
import { createMiddleware } from "langchain";
import { z } from "zod";

const telemetryMiddleware = createMiddleware({
  name: "TelemetryMiddleware",
  stateSchema: z.object({
    modelCalls: z.number().default(0),
  }),
  contextSchema: z.object({ tenantId: z.string() }),

  beforeAgent: async (_state) => ({ modelCalls: 0 }),   // reset on start

  beforeModel: async (state, runtime) => {
    console.log(`[${runtime.context.tenantId}] model call #${state.modelCalls + 1}`);
  },

  wrapModelCall: async (request, handler) => {
    const start = Date.now();
    const response = await handler(request);
    console.log(`Model call: ${Date.now() - start}ms`);
    return response;
  },

  afterModel: async (state) => ({
    modelCalls: state.modelCalls + 1,
  }),

  afterAgent: async (state, runtime) => {
    console.log(`[${runtime.context.tenantId}] completed in ${state.modelCalls} model calls`);
  },
});
```

### Retry with Exponential Backoff (wrapModelCall)

```typescript
import { createMiddleware } from "langchain";

const createRetryMiddleware = (maxRetries = 3) =>
  createMiddleware({
    name: "RetryMiddleware",
    wrapModelCall: async (request, handler) => {
      for (let attempt = 0; attempt < maxRetries; attempt++) {
        try {
          return await handler(request);
        } catch (e) {
          if (attempt === maxRetries - 1) throw e;
          const delay = 1000 * Math.pow(2, attempt);
          console.log(`Retry ${attempt + 1}/${maxRetries} after ${delay}ms`);
          await new Promise((r) => setTimeout(r, delay));
        }
      }
      throw new Error("Unreachable");
    },
  });
```

### Circuit Breaker (wrapModelCall)

```typescript
import { createMiddleware } from "langchain";

const circuitBreakerMiddleware = (() => {
  let failureCount = 0;
  let lastFailureTime = 0;
  const THRESHOLD = 5;
  const RESET_TIMEOUT = 60_000;

  return createMiddleware({
    name: "CircuitBreakerMiddleware",
    wrapModelCall: async (request, handler) => {
      const now = Date.now();
      if (failureCount >= THRESHOLD && now - lastFailureTime < RESET_TIMEOUT) {
        throw new Error("Circuit breaker open: too many recent failures");
      }
      try {
        const result = await handler(request);
        failureCount = 0;   // reset on success
        return result;
      } catch (e) {
        failureCount++;
        lastFailureTime = Date.now();
        throw e;
      }
    },
  });
})();
```

### State-Based Model Selection (wrapModelCall)

Switch between models based on conversation length to balance cost and capability.

```typescript
import { createMiddleware, initChatModel } from "langchain";

const stateBasedModelMiddleware = createMiddleware({
  name: "StateBasedModel",
  wrapModelCall: (req, handler) => {
    const msgCount = req.messages.length;
    const model =
      msgCount > 20 ? initChatModel("openai:gpt-4.1") :    // complex/long
      msgCount > 10 ? initChatModel("openai:gpt-4.1") :    // medium
      initChatModel("openai:gpt-4.1-mini");                 // short/simple
    return handler({ ...req, model });
  },
});
```

### Usage Tracking (wrapModelCall + stateSchema)

```typescript
import { createMiddleware } from "langchain";
import { Command } from "@langchain/langgraph";
import { z } from "zod";

const usageTrackingMiddleware = createMiddleware({
  name: "UsageTrackingMiddleware",
  stateSchema: z.object({
    totalInputTokens: z.number().default(0),
    totalOutputTokens: z.number().default(0),
    modelCalls: z.number().default(0),
  }),
  wrapModelCall: async (request, handler) => {
    const response = await handler(request);
    const usage = (response as any).response_metadata?.usage;
    const tokens = usage?.total_tokens ?? 150;  // fallback estimate
    return new Command({
      update: {
        totalTokensUsed: (request as any).state.totalInputTokens + tokens,
        lastModelCallTokens: tokens,
        modelCalls: (request as any).state.modelCalls + 1,
      },
    });
  },
  afterAgent: async (state) => {
    console.log(`Session stats: ${state.modelCalls} calls, ~${state.totalInputTokens} tokens`);
  },
});
```

### Store-Based Context Injection (Long-Term Memory)

```typescript
import { createMiddleware } from "langchain";
import { z } from "zod";

const contextSchema = z.object({ userId: z.string() });

const personalizeFromStoreMiddleware = createMiddleware({
  name: "PersonalizeFromStore",
  contextSchema,
  wrapModelCall: async (req, handler) => {
    const { userId } = req.runtime.context as { userId: string };
    const prefs = await req.runtime.store?.get(["users"], userId);
    if (!prefs) return handler(req);

    return handler({
      ...req,
      systemMessage: req.systemMessage.concat(
        `User preferences: ${JSON.stringify(prefs.value)}`
      ),
    });
  },
});
```

### Few-Shot Example Injection (wrapModelCall)

```typescript
import { createMiddleware } from "langchain";

const fewShotMiddleware = createMiddleware({
  name: "FewShot",
  wrapModelCall: async (req, handler) => {
    const query = req.messages[req.messages.length - 1]?.content.toString() ?? "";
    const examples = await retrieveRelevantExamples(query, 3);  // your retrieval function

    if (!examples.length) return handler(req);

    const examplesText = examples
      .map((e, i) => `Example ${i + 1}:\nInput: ${e.input}\nOutput: ${e.output}`)
      .join("\n\n");

    return handler({
      ...req,
      systemMessage: req.systemMessage.concat(`\n\nExamples:\n${examplesText}`),
    });
  },
});
```

---

## Testing Custom Middleware

```typescript
import { createAgent } from "langchain";
import { GenericFakeChatModel } from "langchain/testing";

// Unit test: wrap middleware in a minimal fake-model agent
const fakeModel = new GenericFakeChatModel({
  responses: ["Test response 1", "Test response 2"],
});

const testAgent = createAgent({
  model: fakeModel,
  tools: [],
  middleware: [myCustomMiddleware],
});

const result = await testAgent.invoke({ messages: [{ role: "user", content: "Hello" }] });
// Assert on result.messages, captured logs, state mutations

// Test tools without real APIs using the emulator
import { llmToolEmulatorMiddleware } from "langchain";

const testAgentWithEmulatedTools = createAgent({
  model: "openai:gpt-4o",
  tools: [productionTool],
  middleware: [
    llmToolEmulatorMiddleware({ tools: ["production_tool"], model: "openai:gpt-4o-mini" }),
  ],
});
```

---

## Known Pitfalls

| Issue | Context | Workaround |
|---|---|---|
| `canJumpTo` omitted when hook returns `jumpTo` | If you return `jumpTo` from a hook without declaring `canJumpTo`, LangChain throws at runtime | Always use the `{ hook, canJumpTo }` form when the hook may jump |
| `jumpTo: "end"` does not skip `afterAgent` hooks | By design — `afterAgent` always runs for cleanup | Do not rely on `afterAgent` not running after early exit; it will |
| `jumpTo: "model"` from `afterModel` can create infinite loops | If the condition is never resolved, the agent loops forever | Add a counter in `stateSchema` and cap retries; or use `modelCallLimitMiddleware` |
| Node-style hooks in `beforeModel` receive a `runtime` second argument but it is typed as `unknown` unless `contextSchema` is declared on the middleware | TypeScript will not auto-infer the type | Always declare `contextSchema` on the middleware and type `runtime.context` explicitly |
| `wrapModelCall` receives `req.runtime.context` typed as `unknown` unless middleware declares `contextSchema` | Same as above | Declare `contextSchema` on the middleware or cast manually |
| `stateSchema` fields defined in middleware are not visible in `createAgent`'s top-level types | The schema merging is internal to the runtime | Access custom fields via `state.*` inside the same middleware — do not read them in other middleware without also declaring `stateSchema` |
| Middleware declared with `contextSchema` does not receive context if the agent's `contextSchema` does not include the same fields | Each middleware validates its own schema subset | Ensure the agent-level `contextSchema` is a superset of each middleware's `contextSchema` |
| `piiRedactionMiddleware` may restore incorrect values when markers appear in model output embedded in JSON | Partial restoration of complex JSON structures | Use `piiMiddleware` with `applyToOutput: true` as a fallback; test with your schema |
| `ContextOverflowError` is not thrown by all providers | Some providers return a 400 error without the LangChain wrapper | Catch both `ContextOverflowError.isInstance(err)` and raw HTTP 400 errors |
| `trimMessages` with `strategy: "last"` may produce an invalid conversation if it trims the system message | System messages are treated as regular messages | Use `startOn: "human"` to ensure the trimmer starts from the first human message |
| Abort signal cancels the local promise but not the remote HTTP request to the provider | Provider limitation | Use `timeout` in `RunnableConfig` and `modelCallLimitMiddleware` as additional guards |
| `middleware` is not supported on raw LangGraph custom graphs — only on `createAgent` | By design | Use `createAgent` or add manual hook nodes to your LangGraph graph |
| Zod v4 in `stateSchema` / `contextSchema` throws `TypeError: keyValidator.parse is not a function` | Open bug (GH langchainjs #9299) | Use `import { z } from "zod/v3"` for all middleware schemas |
