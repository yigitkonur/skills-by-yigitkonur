# LangChain.js Common Errors Reference

> Version-sensitive examples checked against langchain@1.4.0, @langchain/core@1.1.45, @langchain/langgraph@1.3.0 on 2026-05-09 UTC.
> Every error was reproduced or confirmed via testing, GitHub issues, or community reports.

---

## Contents

- Import Errors
- Zod / Schema Errors
- Provider Errors
- Streaming Errors
- Tools Errors
- Agents / LangGraph Errors
- Middleware Errors
- Memory Errors
- Quick Lookup Table

## Import Errors

### "Module not found: langchain/chains"

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

// ✅ Option 2: Gradual migration
import { LLMChain } from "@langchain/classic/chains";
```

---

### "createReactAgent is deprecated" / Wrong import

```
DeprecationWarning: createReactAgent is deprecated. Use createAgent from "langchain" instead.
```

**Cause**: `createReactAgent` from `@langchain/langgraph/prebuilt` was superseded by `createAgent` from `langchain` in v1.0. Note: `createAgent` vs `createReactAgent` is a common confusion — they are different APIs.

**Fix**:
```typescript
// ❌ WRONG — deprecated LangGraph prebuilt
import { createReactAgent } from "@langchain/langgraph/prebuilt";
const agent = createReactAgent({ llm: model, tools });

// ✅ CORRECT — v1 API
import { createAgent } from "langchain";
const agent = createAgent({ model, tools, systemPrompt: "You are a helpful assistant." });
// Key change: llm → model, prompt is a string, not ChatPromptTemplate
```

---

### Node 18 Incompatibility

```
SyntaxError: Unexpected token 'using'
```

**Cause**: LangChain v1.0 requires Node 20+ (`using` declarations, `Symbol.dispose`).
**Fix**: `nvm install 20 && nvm use 20`. For AWS Lambda: update to `nodejs20.x` runtime.

---

### Version Mismatch Between Packages

```
TypeError: Cannot read properties of undefined (reading 'lc_serializable')
```

**Cause**: All `@langchain/*` packages must be on compatible v1.x versions. Mixing v0.x integrations with v1.x core causes serialization errors.
**Fix**: `npm install langchain@latest @langchain/core@latest @langchain/openai@latest @langchain/langgraph@latest`. Pin exact versions in `package.json`.

---

## Zod / Schema Errors

### DynamicStructuredTool Discards Non-Zod Schemas (GitHub #7830)

```
// Tool receives empty {} payload on every call
```

**Cause**: `DynamicStructuredTool` constructor has: `this.schema = (isZodSchema(fields.schema) ? fields.schema : z.object({}).passthrough())`. Non-Zod schemas are silently replaced with empty schema.

**Fix**: Always use Zod schemas with `DynamicStructuredTool`. Prefer the `tool()` factory instead.

```typescript
// ❌ WRONG — JSON Schema discarded
new DynamicStructuredTool({ schema: { type: "object", properties: { q: { type: "string" } } } });

// ✅ CORRECT
import { tool } from "langchain";
import * as z from "zod";
const myTool = tool(async ({ q }) => { /* ... */ }, {
  name: "search",
  description: "Search for documents",
  schema: z.object({ q: z.string() }),
});
```

---

### Complex Zod Schema `$ref` Rejected by OpenAI / Anthropic

```
Error: 400 Invalid schema: $ref is not supported
```

**Cause**: `bindTools()` calls `zod-to-json-schema` without `$refStrategy: "none"`, producing `$ref` references that OpenAI and Anthropic reject. (Related to #7830)

**Fix**:
```typescript
import { zodToJsonSchema } from "zod-to-json-schema";
const llmWithTools = llm.bindTools([{
  type: "function",
  function: {
    name: "create_page",
    description: "Create a new page",
    parameters: zodToJsonSchema(complexSchema, { $refStrategy: "none" }),  // ← key option
  },
}]);
```

---

### Top-Level `z.array()` Schema Returns Strings (GitHub #7643)

```
// Expected: [{ id: 1 }], Got: ["[object Object]"]
```

**Cause**: Top-level `z.array()` passed to `withStructuredOutput` breaks on several providers.

**Fix**: Always wrap arrays in an object.
```typescript
// ❌ WRONG
const schema = z.array(z.object({ id: z.number() }));

// ✅ CORRECT
const schema = z.object({ items: z.array(z.object({ id: z.number() })) });
```

---

### `z.optional()` Emitted as Required in OpenAI Schemas (GitHub #7787)

```
// Model fills optional fields as if required; missing field causes 400
```

**Cause**: Zod `.optional()` maps inconsistently to OpenAI's JSON Schema `required` array.

**Fix**: Use `.nullish()` instead of `.optional()` for OpenAI tool schemas.
```typescript
const schema = z.object({
  name: z.string(),
  age: z.number().nullish(),  // ✅ use nullish() not optional()
});
```

---

### Zod v4 stateSchema TypeError (GitHub #9299)

```
TypeError: keyValidator._parse is not a function
```

**Cause**: LangGraph's state validation calls `_parse` (a Zod v3 internal). Zod v4 removed this method.

**Fix**:
```typescript
// ❌ WRONG — Zod v4
import { z } from "zod";

// ✅ CORRECT — force v3 for state schemas
import { z } from "zod/v3";
// Note: Zod v4 is fine for tool schemas and withStructuredOutput
```

---

### `withStructuredOutput` + `includeRaw: true` Drops Transforms (GitHub #9100)

```
// .transform() on schema mysteriously stops running after first call
```

**Cause**: `includeRaw: true` mutates the schema object, removing `.transform()` definitions on subsequent calls.

**Fix**: Clone the schema: `model.withStructuredOutput(schema.clone(), { includeRaw: true })`

---

### `withStructuredOutput` Streaming Emits Only One Chunk (GitHub #6440)

```
// Expected token-by-token stream, got one large chunk at the end
```

**Cause**: `withStructuredOutput` buffers the complete response. `.stream()` emits only the final result.

**Fix**: Use `streamEvents` v2 — intercept raw tokens on `on_chat_model_stream`; for partial JSON use `JsonOutputParser` directly.

---

### `includeRaw: true` + `strict: true` Breaks Streaming (GitHub #7116)

```
// Streaming produces zero intermediate chunks
```

**Cause**: This combination suppresses all intermediate chunks.

**Fix**: Remove either `includeRaw` or `strict: true` when streaming; or switch to non-streaming mode.

---

### `StructuredOutputParsingError` Not Auto-Retried (GitHub #9426)

```
StructuredOutputParsingError: Failed to parse structured output
// Even with handleError: true, error is thrown instead of retried
```

**Cause**: In LangChain 1.0.4, `PregelRunner` retry logic is not entered for `StructuredOutputParsingError`.

**Fix**: Wrap in a manual retry loop catching `StructuredOutputParsingError` with up to 3 attempts.

---

### Model Wraps JSON in Markdown Code Fences (GitHub #7752)

```
SyntaxError: Unexpected token '`'
// Raw output: ```json\n{"field": "value"}\n```
```

**Cause**: Some models wrap JSON responses in triple-backtick code fences, breaking JSON parsers.

**Fix**:
```typescript
function stripMarkdownCodeFences(text: string): string {
  return text.replace(/```(?:json)?\n?([\s\S]*?)\n?```/g, "$1").trim();
}
```

---

## Provider Errors

### 400 Error with `providerStrategy` on OpenRouter

```
Error: 400 Provider returned error
```

**Cause**: `providerStrategy` uses native structured output (e.g., OpenAI's `response_format: { type: "json_schema" }`). OpenRouter proxies to backends (Anthropic, Mistral) that don't support this format.

**Fix**:
```typescript
// ❌ WRONG — fails on OpenRouter
import { createAgent, providerStrategy } from "langchain";
const agent = createAgent({ model, responseFormat: providerStrategy(Schema), tools });

// ✅ CORRECT — toolStrategy works via tool calling, universal
import { toolStrategy } from "langchain";
const agent = createAgent({ model, responseFormat: toolStrategy(Schema), tools });
```

---

### Gemini 400 Error with Numeric Refinements or Discriminated Unions (GitHub #8872)

```
Error: 400 INVALID_ARGUMENT: .positive() / z.discriminatedUnion() is not supported
```

**Cause**: Gemini 2.5 rejects JSON schemas containing numeric refinements (`.positive()`, `.int()`, `.min()`, `.max()`) and `z.discriminatedUnion()` / `z.union()`.

**Fix**: Flatten schemas; use an enum discriminant field instead of discriminated unions; remove numeric refinements on Gemini.

---

## Streaming Errors

### Streaming Known Issues (Quick Reference)

| Issue | GitHub | Fix |
|---|---|---|
| `streamLog` deprecated | — | Migrate to `streamEvents({ version: "v2" })` |
| `streamEvents` TypeScript error | langgraphjs #1086 | `// @ts-expect-error`; works at runtime |
| Double messages on stream rejoin | langgraphjs #2028 | Deduplicate by message ID on client |
| `streamEvents` on `RemoteRunnable` broken | langchainjs #5309 | Use `streamMode` on direct graph calls |

---

## Tools Errors

### `tool_call_id` Mismatch

```
Error: tool_call_id in ToolMessage does not match any tool call
```

**Cause**: `tool_call_id` in `ToolMessage` must exactly match the `ToolCall.id` from the originating `AIMessage.tool_calls[n].id`.

**Fix**:
```typescript
// ❌ WRONG — generating a new ID
new ToolMessage({ content: "done", tool_call_id: crypto.randomUUID() });

// ✅ CORRECT — use runtime.toolCallId
new ToolMessage({ content: "done", tool_call_id: runtime.toolCallId });
```

---

### `bindTools` + `withStructuredOutput` Conflict

```
// Unexpected tool calls, malformed messages
```

**Cause**: Using both `bindTools()` and `withStructuredOutput()` on the same model instance causes conflicting tool schemas and unexpected behavior.

**Fix**: Use `createAgent` with `responseFormat` option instead of combining both:
```typescript
import { createAgent, toolStrategy } from "langchain";
const agent = createAgent({ model, tools, responseFormat: toolStrategy(MySchema) });
```

---

## Agents / LangGraph Errors

### `interrupt()` Silently Skipped (No-Op)

```
// interrupt() called but graph runs straight through without pausing
```

**Cause**: `interrupt()` requires a checkpointer. Without one, the call is a no-op.

**Fix**:
```typescript
import { MemorySaver } from "@langchain/langgraph";
// ❌ WRONG
const app = graph.compile();
// ✅ CORRECT
const app = graph.compile({ checkpointer: new MemorySaver() });
const result = await app.invoke(input, { configurable: { thread_id: "my-thread" } });
```

---

### `try { interrupt(...) } catch(e) {}` Swallows GraphInterrupt

```
// Graph appears to pause but never resumes; state is corrupt
```

**Cause**: `interrupt()` throws `GraphInterrupt` internally to pause execution. A surrounding try/catch swallows it, preventing the pause mechanism from working.

**Fix**: Never wrap `interrupt()` in a try/catch. Let it propagate.

---

### Command Resume Not Working — New Interrupt Triggered

```
// Sending resume value triggers another interrupt or starts fresh execution
```

**Cause**: Resuming with a plain object `{ resume: "yes" }` is treated as new input. Only `Command` carries the resume signal.

**Fix**:
```typescript
import { Command } from "@langchain/langgraph";
// ❌ WRONG
const result = await app.invoke({ resume: "yes" }, config);
// ✅ CORRECT
const result = await app.invoke(new Command({ resume: "yes" }), config);
```

---

### Missing ToolMessage After Handoff (Most Common Multi-Agent Bug)

```
Error: tool call not followed by tool result
// or: unexpected behavior on subsequent turns
```

**Cause**: A handoff tool returned a `Command` without including a `ToolMessage` in `update.messages`. Every AIMessage tool call must be followed by a ToolMessage.

**Fix**:
```typescript
// ❌ WRONG — no ToolMessage
return new Command({ update: { currentStep: "next" } });

// ✅ CORRECT
return new Command({
  update: {
    messages: [new ToolMessage({ content: "Transferred", tool_call_id: runtime.toolCallId })],
    currentStep: "next",
  },
});
```

---

### `Command.goto` to Subgraph Parent Ignored (Missing `Command.PARENT`)

```
// goto fires but routing stays in the same subgraph
```

**Cause**: Inside a subgraph, `goto` without `graph: Command.PARENT` routes within the subgraph, not to the parent graph.

**Fix**:
```typescript
return new Command({
  goto: "specialist_node",
  update: { ... },
  graph: Command.PARENT,  // REQUIRED for cross-graph navigation
});
```

---

### `recursionLimit` Exceeded

```
GraphRecursionError: Recursion limit of 25 reached
```

**Cause**: Default recursion limit is 25 supersteps. Complex agent loops or multi-hop reasoning exceeds this.

**Fix**:
```typescript
await app.invoke(input, { configurable: { thread_id: "t1" }, recursionLimit: 100 });
```

---

## Middleware Errors

### `modelFallbackMiddleware` Receives Object Instead of Model

```
Error: llm [object Object] must define bindTools method
```

**Cause**: `modelFallbackMiddleware` takes spread args `(...models)`, not `{ models: [...] }`.

**Fix**:
```typescript
// ❌ WRONG
const fallback = modelFallbackMiddleware({ models: [fallbackModel] });
// ✅ CORRECT
const fallback = modelFallbackMiddleware(fallbackModel);
const fallback = modelFallbackMiddleware(model1, model2, model3);
```

---

### `toolCallLimitMiddleware` "At Least One Limit" Error

```
Error: At least one limit is specified
```

**Cause**: The option is `runLimit` / `threadLimit`, not `maxToolCalls`.

**Fix**:
```typescript
// ❌ WRONG
const limit = toolCallLimitMiddleware({ maxToolCalls: 5 });
// ✅ CORRECT
const limit = toolCallLimitMiddleware({ runLimit: 5 });
const limit = toolCallLimitMiddleware({ threadLimit: 10 });
```

---

### `humanInTheLoopMiddleware` Fails Without Checkpointer

```
Error: Checkpointer required for humanInTheLoopMiddleware
```

**Cause**: `humanInTheLoopMiddleware` uses interrupt/resume which requires a checkpointer. (By design — GH #33217)

**Fix**: Always add `checkpointer: new MemorySaver()` (or persistent equivalent) when using `humanInTheLoopMiddleware`.

---

### `middleware` + `state_schema` Mutually Exclusive in `createAgent` (GH #33217)

```
Error: Cannot specify both middleware and state_schema in createAgent
```

**Cause**: Tracked open issue. `createAgent` currently does not allow both options.

**Fix**: Define `stateSchema` inside the middleware's own config instead of on `createAgent`.

---

## Memory Errors

### PostgresSaver / SqliteSaver Throws on First Use (Missing `setup()`)

```
Error: relation "checkpoints" does not exist
```

**Cause**: DB-backed savers require `setup()` to create the necessary tables before first use.

**Fix**:
```typescript
const checkpointer = PostgresSaver.fromConnString(process.env.DATABASE_URL!);
await checkpointer.setup();  // ← must call before graph.compile()
const graph = workflow.compile({ checkpointer });
```

---

### `RemoveMessage` Has No Effect

```
// Messages persist after RemoveMessage; deletion silently ignored
```

**Cause**: `RemoveMessage` only works when the `messages` field uses `MessagesValue` reducer. Plain `z.array()` does not process removal markers.

**Fix**:
```typescript
import { MessagesValue } from "@langchain/langgraph";
// ❌ WRONG
const State = new StateSchema({ messages: z.array(z.any()) });
// ✅ CORRECT
const State = new StateSchema({ messages: MessagesValue });
```

---

## Quick Lookup Table

| Error Message | Likely Cause | Fix |
|---|---|---|
| `Cannot find module 'langchain/chains'` | Legacy import | Use `createAgent` or `@langchain/classic` |
| `createReactAgent is deprecated` | Old API | Use `createAgent` from `"langchain"` |
| `Unexpected token 'using'` | Node 18 | Upgrade to Node 20+ |
| `lc_serializable undefined` | Package version mismatch | Align all `@langchain/*` to v1.x |
| `400 Provider returned error` (OpenRouter) | `providerStrategy` used | Use `toolStrategy(Schema)` |
| `$ref is not supported` | Complex Zod + `bindTools` | Use `zodToJsonSchema({ $refStrategy: "none" })` |
| Top-level array returns strings | `z.array()` at top level (#7643) | Wrap: `z.object({ items: z.array(...) })` |
| `keyValidator._parse is not a function` | Zod v4 with stateSchema (#9299) | Use `import { z } from "zod/v3"` |
| `.transform()` stops working | `includeRaw: true` schema mutation (#9100) | Clone schema before passing |
| Single chunk instead of stream | `withStructuredOutput` + `.stream()` (#6440) | Use `streamEvents` v2 |
| `must define bindTools method` | `modelFallbackMiddleware({ models: [...] })` | Use spread args |
| `At least one limit is specified` | `maxToolCalls` param | Use `runLimit` / `threadLimit` |
| `interrupt()` silently skipped | No checkpointer | Add `MemorySaver` to `graph.compile()` |
| Resume triggers new run | Plain `{}` instead of `Command` | Use `new Command({ resume: value })` |
| `tool call not followed by tool result` | Missing `ToolMessage` in handoff | Include `ToolMessage` in `Command.update.messages` |
| `GraphRecursionError: 25 reached` | Default limit too low | Set `recursionLimit: 100` in config |
| `relation "checkpoints" does not exist` | Missing `setup()` call | `await checkpointer.setup()` before compile |
| `RemoveMessage` has no effect | Plain array, not `MessagesValue` | Use `MessagesValue` reducer |
| `Cannot specify both middleware and state_schema` | createAgent limitation (#33217) | Use middleware's own `stateSchema` |
