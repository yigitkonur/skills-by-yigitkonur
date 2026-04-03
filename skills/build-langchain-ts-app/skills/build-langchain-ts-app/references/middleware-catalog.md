# Middleware: Built-in Catalog Reference

Complete reference for all built-in LangChain.js v1 middleware. APIs verified against `langchain@1.2.35`, `@langchain/core@1.1.34`, `@langchain/langgraph@1.2.5`. TypeScript only.

---

## Quick Reference — Imports

```typescript
import {
  createAgent,
  createMiddleware,

  // All 14 built-in middleware (+ provider extras)
  summarizationMiddleware,
  humanInTheLoopMiddleware,
  modelCallLimitMiddleware,
  toolCallLimitMiddleware,
  modelFallbackMiddleware,
  toolRetryMiddleware,
  modelRetryMiddleware,
  piiMiddleware,
  piiRedactionMiddleware,
  llmToolSelectorMiddleware,
  todoListMiddleware,
  llmToolEmulatorMiddleware,
  contextEditingMiddleware,
  ClearToolUsesEdit,
  dynamicSystemPromptMiddleware,
  anthropicPromptCachingMiddleware,
  openAIModerationMiddleware,
  filesystemMiddleware,
} from "langchain";

import { MemorySaver, Command } from "@langchain/langgraph";
import { HumanMessage, AIMessage } from "@langchain/core/messages";
import { ContextOverflowError } from "@langchain/core/errors";
import { type ToolRuntime } from "@langchain/core/tools";
import { z } from "zod";
```

---

## AgentMiddleware Interface

Every built-in middleware implements this TypeScript interface. Custom middleware created with `createMiddleware()` does too.

```typescript
interface AgentMiddleware<
  TSchema = undefined,           // stateSchema — extends persisted agent state
  TContextSchema = undefined,    // contextSchema — per-invocation read-only shape
  TFullContext = unknown,
  TTools extends readonly (ClientTool | ServerTool)[] = readonly (ClientTool | ServerTool)[]
> {
  name: string;
  stateSchema?: TSchema;          // Zod object that extends LangGraph state
  contextSchema?: TContextSchema; // Zod object for per-invocation context
  tools?: TTools;                 // Tools provided by this middleware

  // Node-style hooks — intercept but cannot control retry
  beforeAgent?(state: AgentState): Promise<Partial<AgentState> | void>;
  beforeModel?(state: AgentState): Promise<Partial<AgentState> | void>;
  afterModel?(state: AgentState): Promise<Partial<AgentState> | void>;
  afterAgent?(state: AgentState): Promise<Partial<AgentState> | void>;

  // Wrap-style hooks — own the call; decide whether/how to invoke handler
  wrapModelCall?(
    request: ModelRequest,
    handler: (req: ModelRequest) => Promise<ModelResponse>
  ): Promise<ModelResponse>;

  wrapToolCall?(
    request: ToolRequest,
    handler: (req: ToolRequest) => Promise<ToolMessage | Command>
  ): Promise<ToolMessage | Command | any>;
}
```

**`stateSchema` vs `contextSchema`:**

| | `stateSchema` | `contextSchema` |
|---|---|---|
| Purpose | Extend agent's persisted LangGraph state | Per-invocation read-only metadata |
| Persisted across steps | Yes | No — single invocation only |
| Defined with | Zod object | Zod object |
| Accessed via | `state.*` in all hooks | `req.runtime.context` in wrap hooks; `runtime.context` in `dynamicSystemPromptMiddleware` fn |
| TypeScript enforcement | Compile-time type safety | Required fields enforced at `agent.invoke()` |

---

## 6 Hook Types

| Hook | Style | When It Runs | Parameters | Return |
|---|---|---|---|---|
| `beforeAgent` | Node | Once before the agent loop starts | `state` | `void \| { messages?, jumpTo? }` |
| `beforeModel` | Node | Before every model call in the loop | `state` | `void \| { messages?, jumpTo? }` |
| `afterModel` | Node | After every model response | `state` | `void \| state-update dict` |
| `afterAgent` | Node | Once after the agent loop ends | `state` | `void \| state-update dict` |
| `wrapModelCall` | Wrap | Surrounds the model invocation | `(request, handler)` | Result of `handler(request)` |
| `wrapToolCall` | Wrap | Surrounds each tool execution | `(request, handler)` | Result of `handler(request)` |

**Node-style hooks** can inspect and mutate state but cannot control retries.
**Wrap-style hooks** own the call — they decide whether, how many times, and with what arguments to invoke the underlying handler.

### Execution Order Diagram

Given `middleware: [m1, m2, m3]`:

```
m1.beforeAgent → m2.beforeAgent → m3.beforeAgent
      ↓ agent loop starts
m1.beforeModel → m2.beforeModel → m3.beforeModel
m1.wrapModelCall(
  m2.wrapModelCall(
    m3.wrapModelCall(
      → actual model call
    )
  )
)
m3.afterModel → m2.afterModel → m1.afterModel
      ↓ loop iterates or ends
m3.afterAgent → m2.afterAgent → m1.afterAgent
```

**Rules:**
- `before*` hooks execute in order (first → last in the array)
- `wrap*` hooks nest like function calls — first middleware in the array is the outermost wrapper
- `after*` hooks execute in reverse order (last → first in the array)
- Place critical middleware **early** in the array: it runs first on entry and last on exit

**State composition when multiple middleware return updates in the same hook:**
- **Messages** are additive — appended in order
- **Non-reducer fields** follow last-writer-wins — outermost (earliest) middleware overrides inner values
- `Command` objects that only update state pass through without affecting message flow
- Commands from inner calls are discarded when an outer `wrapModelCall` retries the handler

---

## Registering Middleware

All middleware attaches via the `middleware` array in `createAgent`. There is no `addMiddleware()` runtime API.

```typescript
import { createAgent, summarizationMiddleware, modelCallLimitMiddleware } from "langchain";

const agent = createAgent({
  model: "openai:gpt-4.1",
  tools: [...],
  middleware: [
    summarizationMiddleware({ model: "openai:gpt-4.1-mini", trigger: { tokens: 4000 } }),
    modelCallLimitMiddleware({ threadLimit: 15, runLimit: 8 }),
  ],
});
```

**Runtime overrides** for configurable middleware use `configurable` in the invoke config:

```typescript
await agent.invoke(
  { messages: [{ role: "user", content: "Hello" }] },
  { configurable: { threadLimit: 5 } }  // override for this run only
);
```

---

## Built-In Middleware Summary Table

| # | Function | Category | Hooks Used | Purpose |
|---|---|---|---|---|
| 1 | `summarizationMiddleware` | Context | `wrapModelCall` | Auto-summarize history at token thresholds |
| 2 | `humanInTheLoopMiddleware` | Safety | `wrapToolCall` | Pause for human approval of tool calls |
| 3 | `modelCallLimitMiddleware` | Limits | `beforeModel` | Cap total model invocations (thread or run) |
| 4 | `toolCallLimitMiddleware` | Limits | `wrapToolCall` | Cap tool invocations (global or per-tool) |
| 5 | `modelFallbackMiddleware` | Resilience | `wrapModelCall` | Auto-fallback to alternative models on failure |
| 6 | `toolRetryMiddleware` | Resilience | `wrapToolCall` | Retry failed tool calls with exponential backoff |
| 7 | `modelRetryMiddleware` | Resilience | `wrapModelCall` | Retry failed model calls with exponential backoff |
| 8 | `piiMiddleware` | Security | `beforeModel`, `afterModel` | Detect and handle PII per-type |
| 9 | `piiRedactionMiddleware` | Security | `wrapModelCall`, `afterModel` | Regex PII redaction with value restore |
| 10 | `llmToolSelectorMiddleware` | Performance | `wrapModelCall` | LLM pre-selects relevant tools before model call |
| 11 | `todoListMiddleware` | Productivity | tools | Task planning via `write_todos` tool |
| 12 | `llmToolEmulatorMiddleware` | Testing | `wrapToolCall` | Emulate tool execution via LLM responses |
| 13 | `contextEditingMiddleware` | Context | `wrapModelCall` | Clear older tool outputs when token threshold hit |
| 14 | `dynamicSystemPromptMiddleware` | Prompting | `wrapModelCall` | Set system prompt dynamically per model call |
| + | `anthropicPromptCachingMiddleware` | Performance | `wrapModelCall` | Cache Anthropic conversation prefixes |
| + | `openAIModerationMiddleware` | Safety | `beforeModel`, `afterModel` | Screen content via OpenAI Moderation API |
| + | `filesystemMiddleware` | Tools | tools | Virtual filesystem access for the agent |

---

## 1. summarizationMiddleware

Auto-summarizes conversation history when approaching token limits, preserving recent messages intact.

```typescript
summarizationMiddleware(options: {
  model: string | BaseChatModel;          // Required
  trigger?: ContextSize | ContextSize[];  // When to summarize (single=AND, array=OR)
  keep?: ContextSize;                     // What to retain after summary
  tokenCounter?: (messages: BaseMessage[]) => number;
  summaryPrompt?: string;                 // Template — must include {messages}
  trimTokensToSummarize?: number;
  summaryPrefix?: string;
})
```

**`ContextSize` type:**
```typescript
type ContextSize =
  | { fraction: number }   // { fraction: 0.8 } = 80% of model's max tokens
  | { tokens: number }     // { tokens: 4000 }
  | { messages: number }   // { messages: 20 }
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `model` | `string \| BaseChatModel` | **Required** | Model used to generate summaries; prefer a cheaper model |
| `trigger` | `ContextSize \| ContextSize[]` | `{ fraction: 0.8 }` | Single object = AND condition; array = OR conditions |
| `keep` | `ContextSize` | `{ messages: 20 }` | Recent messages to retain unsummarized after the summary is prepended |
| `tokenCounter` | `(msgs: BaseMessage[]) => number` | character count / 4 | Custom counter for accurate measurement |
| `summaryPrompt` | `string` | LangChain default | Template — must include `{messages}` |
| `trimTokensToSummarize` | `number` | `4000` | Max tokens allocated to the summary generation prompt |
| `summaryPrefix` | `string` | `"Summary of prior conversation:"` | Prefix prepended to the generated summary message |

```typescript
import { createAgent, summarizationMiddleware } from "langchain";

// Default: trigger at 80% context full, keep last 20 messages
const agent = createAgent({
  model: "openai:gpt-4.1",
  tools: [...],
  middleware: [
    summarizationMiddleware({ model: "openai:gpt-4.1-mini" }),
  ],
});

// OR trigger: summarize when 4000 tokens OR 50 messages; keep last 10
summarizationMiddleware({
  model: "openai:gpt-4.1-mini",
  trigger: [{ tokens: 4000 }, { messages: 50 }],
  keep: { messages: 10 },
})
```

---

## 2. humanInTheLoopMiddleware

Pauses execution for human approval, editing, or rejection of tool calls. **Requires a checkpointer.**

```typescript
humanInTheLoopMiddleware(options: {
  interruptOn: Record<
    string,  // tool name
    false | {
      allowedDecisions?: ("approve" | "edit" | "reject")[];
      allowAccept?: boolean;   // JS variant
      allowEdit?: boolean;     // JS variant
      allowRespond?: boolean;  // JS variant
      description?: string;    // shown in interrupt message
    }
  >;
  descriptionPrefix?: string;  // prefix added to all interrupt messages
})
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `interruptOn` | `Record<string, false \| InterruptOptions>` | **Required** | Map of tool name → options. `false` = auto-approve. `true` = all decisions allowed |
| `descriptionPrefix` | `string` | `undefined` | Prefix string prepended to all interrupt description messages |

**Decision types:**

| Decision | Effect |
|---|---|
| `approve` | Execute the tool call exactly as proposed |
| `edit` | Modify tool name or arguments before execution |
| `reject` | Cancel the call; provide a feedback message |

```typescript
import { createAgent, humanInTheLoopMiddleware } from "langchain";
import { MemorySaver, Command } from "@langchain/langgraph";
import { HumanMessage } from "@langchain/core/messages";

const agent = createAgent({
  model: "openai:gpt-4.1",
  tools: [writeFileTool, executeSQLTool, readDataTool],
  middleware: [
    humanInTheLoopMiddleware({
      interruptOn: {
        write_file: true,  // shorthand — all decisions allowed
        execute_sql: {
          allowedDecisions: ["approve", "reject"],
          description: "SQL execution requires DBA approval",
        },
        read_data: false,  // auto-approve; no interrupt
      },
    }),
  ],
  checkpointer: new MemorySaver(), // REQUIRED
});

const config = { configurable: { thread_id: "thread-001" } };

// First invoke — pauses at sensitive tool call
const result = await agent.invoke(
  { messages: [new HumanMessage("Delete old records")] },
  config
);
console.log(result.__interrupt__);

// Resume: approve
await agent.invoke(new Command({ resume: { decisions: [{ type: "approve" }] } }), config);

// Resume: edit tool args
await agent.invoke(new Command({
  resume: {
    decisions: [{
      type: "edit",
      editedAction: { name: "execute_sql", args: { query: "DELETE FROM records WHERE age > 90" } },
    }],
  },
}), config);

// Resume: reject with feedback
await agent.invoke(new Command({
  resume: { decisions: [{ type: "reject", message: "Too destructive — use soft delete." }] },
}), config);
```

---

## 3. modelCallLimitMiddleware

Caps total model invocations per thread or per run. Prevents infinite loops and uncontrolled API costs.

```typescript
modelCallLimitMiddleware(options: {
  threadLimit?: number;            // Max calls across entire thread (requires checkpointer)
  runLimit?: number;               // Max calls per single invoke()
  exitBehavior?: "end" | "error";  // default: "end"
})
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `threadLimit` | `number` | unlimited | Max model calls across the thread; requires checkpointer for persistence |
| `runLimit` | `number` | unlimited | Max model calls per single `invoke()` call |
| `exitBehavior` | `"end" \| "error"` | `"end"` | `"end"` = stop gracefully; `"error"` = throw `ModelCallLimitMiddlewareError` |

```typescript
import { createAgent, modelCallLimitMiddleware } from "langchain";

// 10 calls per thread, 3 per run — graceful exit
const agent = createAgent({
  model: "openai:gpt-4.1",
  middleware: [
    modelCallLimitMiddleware({ threadLimit: 10, runLimit: 3 }),
  ],
});

// Strict: throw on limit breach
modelCallLimitMiddleware({ runLimit: 5, exitBehavior: "error" })
```

---

## 4. toolCallLimitMiddleware

Caps tool invocations globally or per specific tool. Create multiple instances for per-tool limits.

```typescript
toolCallLimitMiddleware(options: {
  toolName?: string;                          // Specific tool; undefined = all tools
  threadLimit?: number;
  runLimit?: number;
  exitBehavior?: "continue" | "error" | "end"; // default: "continue"
})
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `toolName` | `string` | `undefined` (all tools) | Restrict limit to a specific named tool |
| `threadLimit` | `number` | unlimited | Max calls across the thread |
| `runLimit` | `number` | unlimited | Max calls per run |
| `exitBehavior` | `"continue" \| "error" \| "end"` | `"continue"` | `"continue"` = skip remaining calls; `"error"` = throw; `"end"` = stop agent |

```typescript
import { createAgent, toolCallLimitMiddleware } from "langchain";

const agent = createAgent({
  model: "openai:gpt-4.1",
  tools: [webSearchTool, codeExecutorTool],
  middleware: [
    toolCallLimitMiddleware({ toolName: "web_search", runLimit: 5 }),
    toolCallLimitMiddleware({ toolName: "code_executor", runLimit: 3, exitBehavior: "error" }),
    toolCallLimitMiddleware({ runLimit: 30 }),  // global cap on all tools
  ],
});
```

---

## 5. modelFallbackMiddleware

Tries alternative models in order when the primary model fails.

```typescript
modelFallbackMiddleware(
  ...fallbackModels: (string | LanguageModelLike)[]
): AgentMiddleware
```

**Parameters:** Variadic list of fallback model IDs (strings) or model instances. Tried in sequence on primary failure.

```typescript
import { createAgent, modelFallbackMiddleware } from "langchain";
import { ChatOpenAI } from "@langchain/openai";
import { ChatAnthropic } from "@langchain/anthropic";

const agent = createAgent({
  model: "openai:gpt-4.1",
  middleware: [
    // Two fallbacks — tried in sequence on primary failure
    modelFallbackMiddleware("openai:gpt-4.1-mini", "anthropic:claude-sonnet-4-5"),
  ],
});

// With model instances for fine-grained config
modelFallbackMiddleware(
  new ChatOpenAI({ model: "gpt-4o-mini" }),
  new ChatAnthropic({ model: "claude-haiku" })
)
```

---

## 6. toolRetryMiddleware

Retries failed tool calls with exponential backoff.

```typescript
toolRetryMiddleware(config?: {
  maxRetries?: number;
  tools?: (string | BaseTool)[];
  retryOn?: ErrorConstructor[] | ((error: Error) => boolean);
  onFailure?: "raise" | ((error: Error) => string);
  backoffFactor?: number;
  initialDelayMs?: number;
  jitter?: boolean;
})
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `maxRetries` | `number` | `2` | Retry attempts after first failure (total attempts = `maxRetries + 1`) |
| `tools` | `(string \| BaseTool)[]` | all tools | Restrict retries to specific tools; others fail immediately |
| `retryOn` | `ErrorConstructor[] \| (err) => boolean` | all errors | Filter which errors trigger a retry |
| `onFailure` | `"raise" \| (err) => string` | formatted message | `"raise"` re-throws after exhaustion; function returns a custom error message string |
| `backoffFactor` | `number` | `1` | Exponential multiplier between retries |
| `initialDelayMs` | `number` | `0` | Base delay before first retry in milliseconds |
| `jitter` | `boolean` | `false` | Add ±25% random jitter to delays |

```typescript
import { createAgent, toolRetryMiddleware } from "langchain";

const agent = createAgent({
  model: "openai:gpt-4.1",
  tools: [webSearchTool, databaseTool],
  middleware: [
    // Retry up to 4 times on HTTP 5xx errors only
    toolRetryMiddleware({
      maxRetries: 4,
      retryOn: (error: Error) => {
        if ("statusCode" in error) return (error as any).statusCode >= 500;
        return false;
      },
      backoffFactor: 1.5,
      initialDelayMs: 500,
    }),
  ],
});

// Retry specific tools; return custom failure message
toolRetryMiddleware({
  maxRetries: 3,
  tools: ["web_search", "database_query"],
  onFailure: (err) => `Tool failed after retries: ${err.message}. Try a different approach.`,
})
```

---

## 7. modelRetryMiddleware

Retries failed model calls with exponential backoff. Mirrors the Tool Retry API with one extra `onFailure` option.

```typescript
modelRetryMiddleware(config?: {
  maxRetries?: number;
  retryOn?: ErrorConstructor[] | ((error: Error) => boolean);
  onFailure?: "continue" | "error" | ((error: Error) => string);
  backoffFactor?: number;
  initialDelayMs?: number;
  jitter?: boolean;
})
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `maxRetries` | `number` | `2` | Max retry attempts |
| `retryOn` | `ErrorConstructor[] \| (err) => boolean` | all errors | Filter which errors trigger a retry |
| `onFailure` | `"continue" \| "error" \| (err) => string` | `"error"` | `"continue"` = return `AIMessage` with error text and continue; `"error"` = re-throw |
| `backoffFactor` | `number` | `2` | Exponential multiplier |
| `initialDelayMs` | `number` | `1000` | Base delay in milliseconds |
| `jitter` | `boolean` | `false` | Add random jitter to delays |

```typescript
import { createAgent, modelRetryMiddleware } from "langchain";

const agent = createAgent({
  model: "openai:gpt-4.1",
  middleware: [
    // Retry on rate limits and server errors
    modelRetryMiddleware({
      maxRetries: 4,
      retryOn: (error: Error) => {
        if (error.name === "RateLimitError") return true;
        if ("statusCode" in error) {
          const sc = (error as any).statusCode;
          return sc === 429 || sc === 503;
        }
        return false;
      },
      initialDelayMs: 2000,
      backoffFactor: 2,
    }),
  ],
});

// Gracefully continue on failure instead of throwing
modelRetryMiddleware({ maxRetries: 3, onFailure: "continue" })
```

---

## 8. piiMiddleware

Detects and handles a single PII type per instance. Stack multiple instances for multiple types.

```typescript
piiMiddleware(
  piiType: string,
  options?: {
    strategy?: "block" | "redact" | "mask" | "hash";  // default: "redact"
    detector?: string | RegExp | ((text: string) => PIIMatch[]);
    applyToInput?: boolean;         // default: true
    applyToOutput?: boolean;        // default: false
    applyToToolResults?: boolean;   // default: false
  }
)
```

**Built-in `piiType` values:**

| `piiType` | Detection Method |
|---|---|
| `"email"` | Regex + validation |
| `"credit_card"` | Luhn algorithm |
| `"ip"` | Regex + validation |
| `"mac_address"` | Regex |
| `"url"` | Regex |

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `strategy` | `"block" \| "redact" \| "mask" \| "hash"` | `"redact"` | How to handle detected PII |
| `detector` | `string \| RegExp \| (text) => PIIMatch[]` | built-in | Override with custom pattern or detection function |
| `applyToInput` | `boolean` | `true` | Scan user messages before model call |
| `applyToOutput` | `boolean` | `false` | Scan AI messages after model call |
| `applyToToolResults` | `boolean` | `false` | Scan tool result messages |

**Strategy reference:**

| Strategy | Effect | Example output |
|---|---|---|
| `"redact"` | Replace with `[REDACTED_{TYPE}]` | `[REDACTED_EMAIL]` |
| `"mask"` | Partial obscurement | `****-****-****-1234` |
| `"hash"` | Deterministic SHA hash | `a8f5f167…` |
| `"block"` | Throw exception, halt execution | — |

```typescript
import { createAgent, piiMiddleware, type PIIMatch } from "langchain";

// Custom SSN detector with hash strategy
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
  tools: [customerServiceTool],
  middleware: [
    piiMiddleware("email", { strategy: "redact", applyToInput: true }),
    piiMiddleware("credit_card", { strategy: "mask", applyToInput: true }),
    piiMiddleware("ssn", { detector: detectSSN, strategy: "hash", applyToInput: true }),
    piiMiddleware("api_key", {
      detector: /sk-[a-zA-Z0-9]{32}/,
      strategy: "block",
      applyToInput: true,
    }),
  ],
});
```

---

## 9. piiRedactionMiddleware

Regex-rule-based PII redaction that **restores original values** in tool calls and AI responses. More powerful than `piiMiddleware` for full round-trip protection.

```typescript
piiRedactionMiddleware(options?: {
  rules?: Record<string, RegExp>;
})
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `rules` | `Record<string, RegExp>` | built-in default rules | Named regex patterns — each name appears in the redaction marker |

**Default built-in rules:**
```typescript
const defaultRules = {
  ssn:         /\b\d{3}-?\d{2}-?\d{4}\b/g,
  email:       /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g,
  phone:       /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g,
  employee_id: /EMP-\d{6}/g,
  api_key:     /sk-[a-zA-Z0-9]{32}/g,
  credit_card: /\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b/g,
};
```

**Redaction marker format:** `[REDACTED_{RULE_NAME}_{ID}]` — e.g., `[REDACTED_SSN_abc123]`

**Behavior:** `wrapModelCall` scans all message types (HumanMessage, ToolMessage, SystemMessage, AIMessage) and tool-call arguments, replaces matches with markers, stores a `{ id → originalValue }` map. `afterModel` searches AIMessage output for markers and restores original values, handling both plain text and structured JSON.

```typescript
import { createAgent, piiRedactionMiddleware } from "langchain";
import { HumanMessage } from "@langchain/core/messages";

const PII_RULES = {
  ssn:   /\b\d{3}-?\d{2}-?\d{4}\b/g,
  email: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g,
};

const agent = createAgent({
  model: "openai:gpt-4.1",
  tools: [lookupUserTool],
  middleware: [piiRedactionMiddleware({ rules: PII_RULES })],
});

// Runtime rule injection per invocation (overrides constructor rules for this run)
await agent.invoke(
  { messages: [new HumanMessage("Look up SSN 123-45-6789")] },
  { configurable: { PIIRedactionMiddleware: { rules: PII_RULES } } }
);
```

---

## 10. llmToolSelectorMiddleware

Uses an LLM to pre-select the most relevant tools before each model call. Critical for agents with large tool sets — reduces token usage and improves routing accuracy.

```typescript
llmToolSelectorMiddleware(options?: {
  model?: string | BaseChatModel;   // default: agent's main model
  systemPrompt?: string;
  maxTools?: number;                // default: unlimited
  alwaysInclude?: string[];         // default: []
})
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `model` | `string \| BaseChatModel` | Agent's model | Model for tool selection; use a cheaper model |
| `maxTools` | `number` | unlimited | Max tools passed to the main model call |
| `alwaysInclude` | `string[]` | `[]` | Tools always included; exempt from `maxTools` count |
| `systemPrompt` | `string` | built-in | Custom selection prompt |

```typescript
import { createAgent, llmToolSelectorMiddleware } from "langchain";

const agent = createAgent({
  model: "openai:gpt-4.1",
  tools: [tool1, tool2, tool3, tool4, tool5, tool6, tool7, tool8],
  middleware: [
    llmToolSelectorMiddleware({
      model: "openai:gpt-4.1-mini",  // cheaper model for selection
      maxTools: 5,
      alwaysInclude: ["memory_lookup", "user_profile"],
    }),
  ],
});
```

---

## 11. todoListMiddleware

Provides a `write_todos` tool and system prompt instructions for task planning and tracking. No configuration required.

```typescript
todoListMiddleware(): AgentMiddleware
```

```typescript
import { createAgent, todoListMiddleware } from "langchain";

const agent = createAgent({
  model: "openai:gpt-4.1",
  tools: [...],
  middleware: [todoListMiddleware()],
});
```

---

## 12. llmToolEmulatorMiddleware

Replaces real tool execution with LLM-generated responses. For testing and prototyping without live APIs.

```typescript
llmToolEmulatorMiddleware(options?: {
  tools?: (string | BaseTool)[];  // specific tools to emulate; default: all
  model?: string | BaseChatModel; // default: agent's model
})
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `tools` | `(string \| BaseTool)[]` | all tools | Restrict emulation to specific tools; others execute normally |
| `model` | `string \| BaseChatModel` | agent's model | Model to use for generating emulated responses |

```typescript
import { createAgent, llmToolEmulatorMiddleware } from "langchain";

// Emulate all tools with a cheaper model (safe for cost-free testing)
const testAgent = createAgent({
  model: "openai:gpt-4.1",
  tools: [productionTool],
  middleware: [
    llmToolEmulatorMiddleware({ model: "openai:gpt-4o-mini" }),
  ],
});

// Emulate only specific tools; others execute against real APIs
llmToolEmulatorMiddleware({ tools: ["web_search", "database_query"] })
```

---

## 13. contextEditingMiddleware

Clears older tool outputs when token limits are reached, preserving the most recent tool results. Mirrors Anthropic's `clear_tool_uses_20250919` behavior.

```typescript
contextEditingMiddleware(options?: {
  edits?: ContextEdit[];
  tokenCountMethod?: "approximate" | "model";  // default: "approximate"
})
```

**`ClearToolUsesEdit` constructor:**
```typescript
import { contextEditingMiddleware, ClearToolUsesEdit } from "langchain";

new ClearToolUsesEdit({
  trigger: ContextSize | ContextSize[];  // Required — when to trigger clearing
  keep: { messages?: number; fraction?: number };  // Required — what to retain
  excludeTools?: string[];       // Tools exempt from clearing
  clearToolInputs?: boolean;     // Also clear tool call args (default: false)
  clearAtLeast?: number;         // Minimum tokens to reclaim when triggered (default: 0)
  placeholder?: string;          // Replacement text (default: "[cleared]")
  model?: BaseLanguageModel;     // Model for fractional token calculation
})
```

**`ClearToolUsesEdit` parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `trigger` | `ContextSize \| ContextSize[]` | **Required** | Token/message/fraction threshold to start clearing |
| `keep` | `{ messages?: number; fraction?: number }` | **Required** | How many recent tool results to retain |
| `excludeTools` | `string[]` | `[]` | Tools exempt from clearing (e.g., memory tools) |
| `clearToolInputs` | `boolean` | `false` | Also clear the original tool call argument messages |
| `clearAtLeast` | `number` | `0` | Minimum tokens to reclaim when triggered |
| `placeholder` | `string` | `"[cleared]"` | Text replacing cleared tool outputs |
| `model` | `BaseLanguageModel` | `undefined` | Model for accurate fractional token calculation |

**`tokenCountMethod`:**
- `"approximate"` — fast character-count approximation (default)
- `"model"` — actual tokenizer (slower, more accurate)

```typescript
import { createAgent, contextEditingMiddleware, ClearToolUsesEdit } from "langchain";

// Default: clear tool outputs beyond 100k tokens, keep last 3
const agent = createAgent({
  model: "openai:gpt-4.1",
  middleware: [contextEditingMiddleware()],
});

// Custom: clear at 50k tokens, keep last 5, never clear memory tools
contextEditingMiddleware({
  edits: [
    new ClearToolUsesEdit({
      trigger: { tokens: 50000 },
      keep: { messages: 5 },
      excludeTools: ["memory_read", "memory_write"],
      placeholder: "[tool output cleared to save context]",
    }),
  ],
  tokenCountMethod: "approximate",
})

// OR-condition trigger (50k tokens OR 50 messages — whichever comes first)
contextEditingMiddleware({
  edits: [
    new ClearToolUsesEdit({
      trigger: [{ tokens: 100000 }, { messages: 50 }],
      keep: { fraction: 0.1 },
    }),
  ],
})
```

---

## 14. dynamicSystemPromptMiddleware

Sets the system prompt dynamically before every model call based on agent state and runtime context.

```typescript
dynamicSystemPromptMiddleware<TContextSchema = unknown>(
  fn: (state: AgentState, runtime: { context: TContextSchema }) => string
): AgentMiddleware
```

**Parameters:** A single function receiving `(state, runtime)` that returns a string system prompt.

```typescript
import { z } from "zod";
import { createAgent, dynamicSystemPromptMiddleware } from "langchain";

const contextSchema = z.object({
  region: z.string().optional(),
  userTier: z.enum(["free", "pro", "enterprise"]).default("free"),
});

const agent = createAgent({
  model: "openai:gpt-4.1",
  contextSchema,
  middleware: [
    dynamicSystemPromptMiddleware((_state, runtime) =>
      `You are a helpful assistant.
Region: ${runtime.context.region ?? "global"}
User tier: ${runtime.context.userTier}
${runtime.context.userTier === "enterprise" ? "You have access to advanced features." : ""}`
    ),
  ],
});

await agent.invoke(
  { messages: [{ role: "user", content: "What can I do?" }] },
  { context: { region: "EU", userTier: "enterprise" } }
);
```

---

## anthropicPromptCachingMiddleware

Adds Anthropic cache-control headers to reduce latency and cost on repeated prompts. Cached tokens billed at 10% of base price; cache writes at 25%.

```typescript
anthropicPromptCachingMiddleware(options?: {
  ttl?: "5m" | "1h";           // default: "5m"
  minMessagesToCache?: number; // minimum messages before caching applies
  enableCaching?: boolean;     // default: true
})
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `ttl` | `"5m" \| "1h"` | `"5m"` | Cache time-to-live |
| `minMessagesToCache` | `number` | `undefined` | Minimum message count before caching is applied |
| `enableCaching` | `boolean` | `true` | Runtime toggle — can disable per-invocation via `configurable` |

```typescript
import { createAgent, anthropicPromptCachingMiddleware } from "langchain";
import { HumanMessage } from "@langchain/core/messages";

const agent = createAgent({
  model: "anthropic:claude-sonnet-4-6",
  systemPrompt: "You are an expert support agent. <knowledge>... thousands of tokens ...</knowledge>",
  middleware: [
    anthropicPromptCachingMiddleware({ ttl: "1h", minMessagesToCache: 1 }),
  ],
});

// Disable caching for a specific run
await agent.invoke(
  { messages: [new HumanMessage("One-off query")] },
  { configurable: { middleware_context: { enableCaching: false } } }
);
```

---

## openAIModerationMiddleware

Calls the OpenAI Moderation API to screen content in input, output, or tool results.

```typescript
openAIModerationMiddleware(options: {
  checkInput?: boolean;           // default: true
  checkOutput?: boolean;          // default: false
  checkToolResults?: boolean;     // default: false
  moderationModel?: string;       // default: "text-moderation-latest"
  exitBehavior?: "end" | "error" | "replace";  // default: "end"
  violationMessage?: string;      // Placeholders: {categories}, {category_scores}, {original_content}
})
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `checkInput` | `boolean` | `true` | Check user input messages |
| `checkOutput` | `boolean` | `false` | Check model output messages |
| `checkToolResults` | `boolean` | `false` | Check tool result messages |
| `moderationModel` | `string` | `"text-moderation-latest"` | OpenAI moderation model to use |
| `exitBehavior` | `"end" \| "error" \| "replace"` | `"end"` | How to handle flagged content |
| `violationMessage` | `string` | built-in template | Custom message; supports `{categories}`, `{category_scores}`, `{original_content}` |

**`exitBehavior` options:**

| Value | Effect |
|---|---|
| `"end"` | Terminate agent and return the violation message |
| `"error"` | Throw error when content is flagged |
| `"replace"` | Replace flagged content with `violationMessage` and continue |

```typescript
import { createAgent, openAIModerationMiddleware } from "langchain";

const agent = createAgent({
  model: "openai:gpt-4.1",
  tools: [searchTool, sendEmailTool],
  middleware: [
    openAIModerationMiddleware({
      checkInput: true,
      checkOutput: true,
      exitBehavior: "end",
      violationMessage: "Content policy violation detected in: {categories}",
    }),
  ],
});
```

---

## Known Pitfalls

| Middleware | Issue | Workaround |
|---|---|---|
| `humanInTheLoopMiddleware` | Throws at runtime without a checkpointer | Always include `checkpointer: new MemorySaver()` or a persistent saver |
| `modelCallLimitMiddleware` | Thread-level tracking (`threadLimit`) requires a checkpointer | Add a checkpointer; omit `threadLimit` if you cannot use one |
| `toolCallLimitMiddleware` | Does not support per-tool limits in a single instance | Create one instance per tool with different `toolName` values |
| `piiMiddleware` | Does not protect LangGraph state checkpoints | Add encryption or access controls on the checkpointer store |
| `piiRedactionMiddleware` | Restores values in `AIMessage` output only — tool-call arguments may still contain originals | Combine with `piiMiddleware` on `applyToToolResults: true` |
| `contextEditingMiddleware` | May not trigger if the agent loop ends before the token threshold is reached | Lower the `trigger` threshold or combine with `summarizationMiddleware` |
| `summarizationMiddleware` | Persistent summarization requires a checkpointer | Add `checkpointer: new MemorySaver()` to `createAgent` |
| `llmToolSelectorMiddleware` | The `alwaysInclude` list does not count toward `maxTools` — the actual number of tools passed to the model can exceed `maxTools` | Account for `alwaysInclude` length when setting `maxTools` |
| `anthropicPromptCachingMiddleware` | Cache content must exceed 1,024 tokens to be stored | Ensure long system prompts; short prompts will not cache |
| All middleware | `middleware` parameter is mutually exclusive with `stateSchema` in `createAgent` (GH #33217) | Use each middleware's own `stateSchema` field to extend state |
| All middleware | Zod v4 in `stateSchema` / `contextSchema` throws `TypeError: keyValidator.parse is not a function` | Use `import { z } from "zod/v3"` for all middleware schemas |
| All middleware | Not supported on raw LangGraph custom graphs | Use `createAgent` or add manual hook nodes to your LangGraph graph |
| All JS hooks | All hooks are async — blocking I/O in node-style hooks delays the entire pipeline | Use wrap-style hooks for async-heavy operations |
