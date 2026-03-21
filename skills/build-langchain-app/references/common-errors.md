# LangChain.js Common Errors Reference

> Verified against langchain@1.2.35, @langchain/core@1.1.34, @langchain/langgraph@1.2.5 — March 2026
> Every error was reproduced or confirmed via testing, GitHub issues, or community reports.

---

## Import Errors

### "Module not found: langchain/chains"

**Error**:
```
Error [ERR_MODULE_NOT_FOUND]: Cannot find module 'langchain/chains'
```

**Cause**: All legacy chain classes (`LLMChain`, `SequentialChain`, `ConversationalRetrievalChain`, `RetrievalQA`) were removed from the `langchain` package in v1.0 and moved to `@langchain/classic`.

**Fix**:
```typescript
// ❌ WRONG — removed in v1
import { LLMChain } from "langchain/chains";

// ✅ Option 1: Use v1 patterns (recommended)
import { createAgent } from "langchain";
const agent = createAgent({ model, tools, prompt: "..." });

// ✅ Option 2: Gradual migration with @langchain/classic
import { LLMChain } from "@langchain/classic/chains";
```

---

### "createReactAgent is deprecated"

**Error**:
```
DeprecationWarning: createReactAgent is deprecated. Use createAgent from "langchain" instead.
```

**Cause**: `createReactAgent` from `@langchain/langgraph/prebuilts` was superseded by `createAgent` from `langchain` in v1.0. The old function still exists but is deprecated.

**Fix**:
```typescript
// ❌ WRONG — deprecated
import { createReactAgent } from "@langchain/langgraph/prebuilts";
const agent = createReactAgent({ llm: model, tools });

// ✅ CORRECT — v1 API
import { createAgent } from "langchain";
const agent = createAgent({ model, tools, prompt: "You are a helpful assistant." });
```

Key differences: `llm` → `model`, prompt is a string (not `ChatPromptTemplate`), middleware replaces pre/post hooks.

---

### Node 18 Incompatibility

**Error**:
```
SyntaxError: Unexpected token 'using'
// or
Error: This package requires Node.js >= 20.0.0
```

**Cause**: LangChain v1.0 dropped Node 18 support. The package uses modern JavaScript features (`using` declarations, `Symbol.dispose`) that require Node 20+.

**Fix**:
```bash
# Check current version
node --version

# Update to Node 20+
nvm install 20
nvm use 20

# For AWS Lambda: update runtime to nodejs20.x in your serverless config
```

---

### Version Mismatch Between Packages

**Error**:
```
TypeError: Cannot read properties of undefined (reading 'lc_serializable')
// or
Error: @langchain/core version mismatch
```

**Cause**: All `@langchain/*` packages must be on compatible v1.x versions. Mixing v0.x integration packages with v1.x core causes serialization and type errors.

**Fix**:
```json
// package.json — all packages must be v1-aligned
{
  "langchain": "^1.2.0",
  "@langchain/core": "^1.1.0",
  "@langchain/openai": "^1.3.0",
  "@langchain/langgraph": "^1.2.0",
  "@langchain/openrouter": "^0.1.6"
}
```

```bash
# Force update all LangChain packages together
npm install langchain@latest @langchain/core@latest @langchain/openai@latest @langchain/langgraph@latest
```

---

## Runtime Errors

### "400 Bad Request" with OpenRouter Structured Output

**Error**:
```
Error: 400 Provider returned error
```

**Cause**: `providerStrategy` uses the model's native structured output API (e.g., OpenAI's `response_format: { type: "json_schema" }`). OpenRouter proxies requests to models (like Anthropic/Claude) that don't natively support OpenAI's JSON schema format. The request gets rejected at the provider level.

**Fix**:
```typescript
// ❌ WRONG — fails on OpenRouter
import { createAgent, providerStrategy } from "langchain";
const agent = createAgent({
  model,
  tools,
  responseFormat: providerStrategy(ResponseSchema),
});

// ✅ CORRECT — toolStrategy works with any model supporting tool calling
import { createAgent, ToolStrategy } from "langchain";
const agent = createAgent({
  model,
  tools,
  responseFormat: ToolStrategy.fromSchema(ResponseSchema),
});
```

**When providerStrategy works**: Only with direct connections to providers that support native structured output (e.g., OpenAI API directly, not through OpenRouter).

---

### "withStructuredOutput intermittent failures"

**Error**:
```
Error: 400 Provider returned error
// or intermittent: sometimes works, sometimes 400
```

**Cause**: `model.withStructuredOutput(schema)` uses the provider's native tool-calling API. On OpenRouter, this fails intermittently because the compatibility layer doesn't consistently support the function-calling parameters. Both default and `method: "jsonSchema"` modes are affected.

**Fix**: Use prompt + parse lambda instead of `withStructuredOutput`:
```typescript
import { RunnableLambda } from "@langchain/core/runnables";
import { StringOutputParser } from "@langchain/core/output_parsers";

// ❌ UNRELIABLE on OpenRouter
const chain = prompt.pipe(model.withStructuredOutput(schema));

// ✅ RELIABLE — prompt the model to return JSON, then parse
const chain = ChatPromptTemplate.fromMessages([
  ["system", "Return ONLY valid JSON with fields: summary, sentiment, score. No markdown."],
  ["human", "{input}"],
]).pipe(model).pipe(new StringOutputParser()).pipe(
  new RunnableLambda({
    func: (text: string) => {
      const cleaned = text.replace(/```json?\n?/g, "").replace(/```/g, "").trim();
      return schema.parse(JSON.parse(cleaned));
    },
  })
);
```

---

### ToolStrategy Constructor Error

**Error**:
```
TypeError: Cannot read properties of undefined (reading 'function')
```

**Cause**: `new ToolStrategy(schema)` is the wrong constructor call. The `ToolStrategy` constructor expects `(schema, tool, options)` where `tool` is a pre-built OpenAI function definition object. Passing only a Zod schema leaves `tool` as `undefined`, causing the error when accessing `this.tool.function.name`.

**Fix**:
```typescript
import { ToolStrategy } from "langchain";
import { z } from "zod";

const ResponseSchema = z.object({
  summary: z.string(),
  topics: z.array(z.string()),
});

// ❌ WRONG — crashes
const strategy = new ToolStrategy(ResponseSchema);

// ✅ CORRECT — use the static factory method
const strategy = ToolStrategy.fromSchema(ResponseSchema);
```

---

### modelFallbackMiddleware "not a function" / "must define bindTools"

**Error**:
```
Error: llm [object Object] must define bindTools method
```

**Cause**: `modelFallbackMiddleware` uses spread args `(...fallbackModels)`, not an options object. Passing `{ models: [fallbackModel] }` sends a plain object as if it were a model, which lacks `bindTools`.

**Fix**:
```typescript
// ❌ WRONG — object is treated as a "model"
const fallback = modelFallbackMiddleware({ models: [fallbackModel] });

// ✅ CORRECT — spread args
const fallback = modelFallbackMiddleware(fallbackModel);

// ✅ CORRECT — multiple fallbacks
const fallback = modelFallbackMiddleware(fallback1, fallback2, fallback3);
```

---

### toolCallLimitMiddleware "missing options"

**Error**:
```
Error: At least one limit is specified
```

**Cause**: The parameter names are `runLimit` and `threadLimit`, not `maxToolCalls`. Passing an unrecognized key means no limit is actually specified.

**Fix**:
```typescript
// ❌ WRONG — unrecognized parameter
const limit = toolCallLimitMiddleware({ maxToolCalls: 5 });

// ✅ CORRECT
const limit = toolCallLimitMiddleware({ runLimit: 5 });
const limit = toolCallLimitMiddleware({ threadLimit: 10 });
const limit = toolCallLimitMiddleware({ threadLimit: 10, runLimit: 5 });
```

---

### interrupt() Not Working (Silently Skipped)

**Error**: No error — `interrupt()` just doesn't pause execution. The graph runs straight through.

**Cause**: `interrupt()` requires a checkpointer (e.g., `MemorySaver`). Without one, the interrupt call is a no-op because there's nowhere to save and restore graph state.

**Fix**:
```typescript
import { MemorySaver } from "@langchain/langgraph";

// ❌ WRONG — no checkpointer, interrupt silently does nothing
const app = graph.compile();

// ✅ CORRECT — checkpointer enables interrupt/resume
const checkpointer = new MemorySaver();
const app = graph.compile({ checkpointer });

const config = { configurable: { thread_id: "my-thread" } };
const result = await app.invoke(input, config);
```

---

### Command Resume Not Working

**Error**: Instead of resuming, the graph triggers another interrupt or behaves unexpectedly.

**Cause**: Resuming with a plain object `{ resume: "yes" }` is treated as new input, not a resume signal. The `Command` class carries metadata that tells the graph to resume from the interrupt point.

**Fix**:
```typescript
import { Command } from "@langchain/langgraph";

// ❌ WRONG — triggers another interrupt
const result = await app.invoke({ resume: "yes" }, config);

// ✅ CORRECT — uses Command to signal resume
const result = await app.invoke(new Command({ resume: "yes" }), config);
```

---

### Zod v4 stateSchema Error

**Error**:
```
TypeError: keyValidator._parse is not a function
```

**Cause**: LangGraph's state validation internally uses Zod v3's `_parse` method. Zod v4 changed this internal API, breaking middleware `stateSchema` validation. This is tracked in [GitHub issue #9299](https://github.com/langchain-ai/langchainjs/issues/9299).

**Fix**:
```typescript
// ❌ WRONG — Zod v4 breaks stateSchema
import { z } from "zod";
const stateSchema = z.object({ count: z.number() });

// ✅ CORRECT — use Zod v3 for state definitions
import { z } from "zod/v3";
const stateSchema = z.object({ count: z.number() });

// ✅ NOTE: Zod v4 is fine for tool schemas and withStructuredOutput
// Only stateSchema (LangGraph state) requires v3
```

---

## State Errors

### State Mutation Bug

**Error**: State changes are lost, reverted, or cause unpredictable behavior across nodes.

**Cause**: Directly mutating state instead of returning a new partial state object. LangGraph nodes must return the fields they want to update — the framework merges them immutably.

**Fix**:
```typescript
// ❌ WRONG — mutating state directly
const myNode = async (state: typeof GraphState.State) => {
  state.messages.push(newMessage);  // mutation — changes are lost
  state.count += 1;                 // mutation — not detected
  return state;
};

// ✅ CORRECT — return partial state updates
const myNode = async (state: typeof GraphState.State) => {
  return {
    messages: [newMessage],  // appended via reducer (if defined)
    count: state.count + 1,  // new value replaces old
  };
};
```

---

### Missing Reducer — Messages Not Accumulating

**Error**: Only the last message is kept; previous messages disappear after each node.

**Cause**: Without a reducer, each state update replaces the field entirely. The `messages` field needs an `add` reducer to accumulate messages across nodes.

**Fix**:
```typescript
import { Annotation, messagesStateReducer } from "@langchain/langgraph";

// ❌ WRONG — no reducer, messages replaced each time
const GraphState = Annotation.Root({
  messages: Annotation<BaseMessage[]>,
});

// ✅ CORRECT — messagesStateReducer appends and deduplicates
const GraphState = Annotation.Root({
  messages: Annotation<BaseMessage[]>({
    reducer: messagesStateReducer,
    default: () => [],
  }),
});
```

---

### Thread Isolation — Conversations Leaking

**Error**: Different users or conversations share state, seeing each other's messages.

**Cause**: Using the same `thread_id` for different conversations, or omitting `thread_id` entirely.

**Fix**:
```typescript
// ❌ WRONG — same thread_id for all users
await agent.invoke(input, { configurable: { thread_id: "main" } });

// ✅ CORRECT — unique thread_id per conversation
await agent.invoke(input, { configurable: { thread_id: `user-${userId}-session-${sessionId}` } });

// ✅ CORRECT — generate unique IDs
import { randomUUID } from "crypto";
const threadId = randomUUID();
await agent.invoke(input, { configurable: { thread_id: threadId } });
```

---

## Performance Issues

### Token Waste with Hidden LangChain Overhead

**Error**: Higher than expected token usage and API costs.

**Cause**: LangChain adds system messages, tool descriptions, and formatting to every model call. These hidden tokens accumulate, especially with many tools or long system prompts.

**Fix**:
```typescript
// Audit actual tokens being sent
const observability = createMiddleware({
  name: "TokenAudit",
  beforeModel: async (request) => {
    const totalChars = request.messages
      .map((m) => (typeof m.content === "string" ? m.content.length : 0))
      .reduce((a, b) => a + b, 0);
    console.log(`[Tokens] ~${Math.ceil(totalChars / 4)} tokens in ${request.messages.length} messages`);
  },
});

// Mitigation strategies:
// 1. Use summarizationMiddleware to compress long conversations
// 2. Limit tool count — each tool description adds ~100-300 tokens
// 3. Keep system prompts concise
// 4. Use modelCallLimitMiddleware to cap runaway loops
```

---

### InMemoryStore Mutable References

**Error**: Store values change unexpectedly when retrieved objects are modified.

**Cause**: `InMemoryStore` returns references to the stored objects, not copies. Modifying a retrieved value mutates the stored original.

**Fix**:
```typescript
import { InMemoryStore } from "@langchain/langgraph";

const store = new InMemoryStore();

// ❌ WRONG — modifying retrieved value changes the store
const item = await store.get("namespace", "key");
item.value.data.count += 1; // mutates original in store!

// ✅ CORRECT — deep clone before modifying
const item = await store.get("namespace", "key");
const data = structuredClone(item.value.data);
data.count += 1;
await store.put("namespace", "key", { data });
```

---

### Complex Zod Schemas Producing Unreliable JSON

**Error**: Model returns malformed JSON or hallucinated fields when the schema is too complex.

**Cause**: Large, deeply nested Zod schemas get serialized into verbose JSON Schema descriptions. Models struggle with complex schemas, especially through tool calling, producing unreliable output.

**Fix**:
```typescript
// ❌ PROBLEMATIC — deeply nested, optional fields, unions
const ComplexSchema = z.object({
  analysis: z.object({
    primary: z.object({
      category: z.enum(["A", "B", "C"]),
      subcategory: z.string().optional(),
      metadata: z.record(z.unknown()).optional(),
    }),
    secondary: z.array(z.object({
      type: z.union([z.string(), z.number()]),
      tags: z.array(z.string()).optional(),
    })).optional(),
  }),
});

// ✅ BETTER — flat, required fields, simple types
const SimpleSchema = z.object({
  category: z.enum(["A", "B", "C"]),
  summary: z.string(),
  tags: z.array(z.string()),
  confidence: z.number(),
});

// ✅ ALTERNATIVE — break into multiple simpler calls
// Call 1: Get category and summary
// Call 2: Get detailed analysis based on category
```

---

## Quick Lookup Table

| Error Message | Likely Cause | Fix |
|---|---|---|
| `Cannot find module 'langchain/chains'` | Legacy import, moved to @langchain/classic | Use `createAgent` or import from `@langchain/classic` |
| `createReactAgent is deprecated` | Old API | Use `createAgent` from `"langchain"` |
| `Unexpected token 'using'` | Node 18 | Upgrade to Node 20+ |
| `lc_serializable undefined` | Package version mismatch | Align all @langchain/* to v1.x |
| `400 Provider returned error` | providerStrategy on OpenRouter | Use `ToolStrategy.fromSchema()` |
| `Cannot read 'function' of undefined` | `new ToolStrategy(schema)` | Use `ToolStrategy.fromSchema(schema)` |
| `must define bindTools method` | modelFallbackMiddleware with object | Use spread args: `modelFallbackMiddleware(model)` |
| `At least one limit is specified` | Wrong toolCallLimitMiddleware param | Use `runLimit`/`threadLimit`, not `maxToolCalls` |
| interrupt() silently skipped | No checkpointer | Add `MemorySaver` to `graph.compile()` |
| Resume triggers new interrupt | Plain object instead of Command | Use `new Command({ resume: value })` |
| `keyValidator._parse is not a function` | Zod v4 with stateSchema | Use `import { z } from "zod/v3"` for state |
| Messages disappearing | Missing reducer | Add `messagesStateReducer` to messages annotation |
| State changes lost | Direct state mutation | Return partial state object, don't mutate |
