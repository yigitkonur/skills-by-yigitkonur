# LangChain.js Antipatterns — What NOT to Do

> Verified against langchain@1.2.35, @langchain/core@1.1.34, @langchain/langgraph@1.2.5 — March 2026
> Every antipattern here was confirmed via community reports, rejected pattern testing, or official deprecation notices.

---

## 1. Deprecated Patterns

These APIs have been removed or moved to `@langchain/classic`. Using them will cause import errors or runtime failures.

### Using LLMChain

❌ Don't: Import `LLMChain` from `langchain` or `@langchain/core`.
```typescript
import { LLMChain } from "langchain/chains"; // ❌ Removed in v1
const chain = new LLMChain({ llm: model, prompt });
```

✅ Do: Use `createAgent` for agent workflows or LCEL `.pipe()` for simple chains.
```typescript
import { createAgent } from "langchain";
const agent = createAgent({ model, tools, systemPrompt: "..." });
// or for a simple prompt→model chain:
const chain = prompt.pipe(model).pipe(new StringOutputParser());
```

Because: `LLMChain` and all legacy chain classes (`SequentialChain`, `ConversationalRetrievalChain`, `RetrievalQA`) were moved to `@langchain/classic` in v1.0. They will not receive updates and rely on deprecated memory/prompt patterns. The v1 agent and LCEL patterns are simpler, better typed, and actively maintained.

---

### Using ConversationBufferMemory

❌ Don't: Use any legacy memory class for conversation state.
```typescript
import { ConversationBufferMemory } from "langchain/memory"; // ❌ Removed
const memory = new ConversationBufferMemory();
```

✅ Do: Use LangGraph checkpointers for persistent conversation state, or manage message arrays manually.
```typescript
import { MemorySaver } from "@langchain/langgraph";
const agent = createAgent({
  model,
  tools,
  checkpointer: new MemorySaver(), // or PostgresSaver for production
});
// Pass thread_id in config to maintain conversation
await agent.invoke({ messages }, { configurable: { thread_id: "user-123" } });
```

Because: All legacy memory classes (`ConversationBufferMemory`, `ConversationSummaryMemory`, `BufferWindowMemory`) hide important details about context window management and can cause silent token waste. LangGraph checkpointers give explicit, persistent, inspectable conversation state. Memory classes are now in `@langchain/classic` and will not be maintained.

---

### Using initialize_agent

❌ Don't: Use the legacy agent initializer from pre-v1 patterns.
```typescript
import { initializeAgentExecutorWithOptions } from "langchain/agents"; // ❌ Removed
const executor = await initializeAgentExecutorWithOptions(tools, model, {
  agentType: "openai-functions",
});
```

✅ Do: Use `createAgent` from `langchain` (v1).
```typescript
import { createAgent } from "langchain";
const agent = createAgent({
  model,
  tools,
  systemPrompt: "You are a helpful assistant.",
});
const result = await agent.invoke({ messages: [{ role: "user", content: "Hello" }] });
```

Because: `initializeAgentExecutorWithOptions` and `AgentExecutor` were removed in v1. `createAgent` provides the same functionality with a cleaner API, built-in middleware support, structured output strategies, and proper TypeScript types.

---

### Using Deprecated Method Names

❌ Don't: Call `.call()`, `.predict()`, or `.predictMessages()` on models or chains.
```typescript
const result = await model.call("Hello"); // ❌ Removed
const result = await model.predict("Hello"); // ❌ Removed
```

✅ Do: Use `.invoke()` for single calls, `.stream()` for streaming, `.batch()` for batches.
```typescript
const result = await model.invoke("Hello");
const stream = await model.stream("Hello");
const results = await model.batch(["Hello", "World"]);
```

Because: `.call()`, `.predict()`, and `.predictMessages()` were all removed in v1.0. The unified Runnable interface (`.invoke()`, `.stream()`, `.batch()`) is the only supported calling convention.

---

## 2. TypeScript-Specific

Patterns that don't translate well from Python examples or that break TypeScript's type system.

### Complex Nested Zod Schemas in Tool Definitions

❌ Don't: Use deeply nested objects, unions, or discriminated unions in tool input schemas.
```typescript
const tool = tool({
  name: "search",
  schema: z.object({
    query: z.string(),
    filters: z.discriminatedUnion("type", [  // ❌ Unreliable serialization
      z.object({ type: z.literal("date"), range: z.object({ start: z.date(), end: z.date() }) }),
      z.object({ type: z.literal("category"), values: z.array(z.enum(["a", "b"])) }),
    ]),
  }),
  func: async (input) => { /* ... */ },
});
```

✅ Do: Keep tool schemas flat with simple types. Break complex inputs into multiple simpler tools.
```typescript
const searchByDate = tool({
  name: "search_by_date",
  schema: z.object({
    query: z.string(),
    startDate: z.string().describe("ISO date string"),
    endDate: z.string().describe("ISO date string"),
  }),
  func: async (input) => { /* ... */ },
});
```

Because: LangChain converts Zod schemas to JSON Schema for the LLM provider. Deeply nested objects, discriminated unions, and complex Zod types (`.refine()`, `.transform()`, `.pipe()`) produce unpredictable JSON Schema output that models struggle to fill correctly. Flat schemas with `.describe()` annotations work reliably across all providers. This is confirmed by community reports and official documentation.

---

### Zod v4 with Middleware stateSchema

❌ Don't: Use Zod v4 schemas for middleware `stateSchema` definitions.
```typescript
import { z } from "zod"; // v4
const middleware = createMiddleware({
  name: "MyMiddleware",
  stateSchema: z.object({ count: z.number() }), // ❌ TypeError: keyValidator._parse is not a function
  // ...
});
```

✅ Do: Use Zod v3 for middleware `stateSchema`. Zod v4 is fine for tool schemas and `withStructuredOutput`.
```typescript
import { z as z3 } from "zod/v3"; // Pin to v3 for state schemas
const middleware = createMiddleware({
  name: "MyMiddleware",
  stateSchema: z3.object({ count: z3.number() }), // ✅ Works
  // ...
});
```

Because: LangGraph's internal state validation still calls Zod v3 internals (`_parse` method) that don't exist on Zod v4 schema objects. This is a known bug (GitHub issue #9299). Tool schemas and structured output schemas work fine with Zod v4 since they go through a different code path (`toJSONSchema`).

---

### Trusting LCEL Type Inference in Complex Chains

❌ Don't: Assume `.pipe()` chains will preserve full type information through every step.
```typescript
// Types degrade to Runnable<unknown, unknown> after 3-4 pipes
const chain = prompt.pipe(model).pipe(parser).pipe(postProcess).pipe(validate);
// chain type: Runnable<unknown, unknown> — no type safety
```

✅ Do: Use explicit type annotations at chain boundaries, or break long chains into typed functions.
```typescript
const generate = async (input: { topic: string }): Promise<string> => {
  const response = await prompt.pipe(model).pipe(new StringOutputParser()).invoke(input);
  return response;
};
const validated = mySchema.parse(JSON.parse(await generate({ topic: "AI" })));
```

Because: TypeScript inference degrades through deeply nested generics. After 3-4 `.pipe()` steps, the compiler gives up and resolves to `Runnable<unknown, unknown>`, eliminating compile-time type safety. This is a fundamental limitation of TypeScript's type system with LangChain's Runnable generics, not a bug that will be fixed.

---

## 3. OpenRouter / Provider-Specific

Gotchas specific to OpenRouter and multi-provider setups.

### Using ChatOpenAI with baseURL Hack Instead of @langchain/openrouter

❌ Don't: Manually configure `ChatOpenAI` to point at OpenRouter's API.
```typescript
import { ChatOpenAI } from "@langchain/openai";
const model = new ChatOpenAI({
  modelName: "anthropic/claude-sonnet-4-6",
  configuration: { baseURL: "https://openrouter.ai/api/v1" }, // ❌ Hack
  apiKey: process.env.OPENROUTER_API_KEY,
});
```

✅ Do: Use the dedicated `@langchain/openrouter` package.
```typescript
import { ChatOpenRouter } from "@langchain/openrouter";
const model = new ChatOpenRouter({
  model: "anthropic/claude-sonnet-4-6",
  temperature: 0,
});
```

Because: `@langchain/openrouter` (v0.1.6, first-party) handles OpenRouter-specific features: provider routing (`provider.order`, `provider.sort`), `data_collection` settings, and proper model capability detection. The `ChatOpenAI` hack works for basic calls but breaks structured output, doesn't support provider routing, and misreports model capabilities.

---

### Using providerStrategy with OpenRouter Multi-Model Routing

❌ Don't: Use `providerStrategy` when routing across models via OpenRouter.
```typescript
import { createAgent, providerStrategy } from "langchain";
const agent = createAgent({
  model: new ChatOpenRouter({ model: "anthropic/claude-sonnet-4-6" }),
  responseFormat: providerStrategy(OutputSchema), // ❌ 400 Provider returned error
  tools,
});
```

✅ Do: Use `ToolStrategy.fromSchema()` which works with any model that supports tool calling.
```typescript
import { createAgent, ToolStrategy } from "langchain";
const agent = createAgent({
  model: new ChatOpenRouter({ model: "anthropic/claude-sonnet-4-6" }),
  responseFormat: ToolStrategy.fromSchema(OutputSchema), // ✅ Uses tool calling
  tools,
});
```

Because: `providerStrategy` uses the provider's native structured output API (e.g., OpenAI's `response_format: { type: "json_schema" }`). OpenRouter proxies to various backends, and not all support this format — Anthropic/Claude behind OpenRouter does not support OpenAI's JSON schema response format. The request gets rejected with a 400 error. `ToolStrategy` wraps the schema as a tool call, which is universally supported. Confirmed via testing (see `patterns/rejected/02-agents-rejected.md`).

---

### withStructuredOutput method: "jsonSchema" on OpenRouter

❌ Don't: Use `method: "jsonSchema"` in `withStructuredOutput` when calling through OpenRouter.
```typescript
const structured = model.withStructuredOutput(schema, { method: "jsonSchema" }); // ❌ 400 error
```

✅ Do: Use default method (function calling) or explicit `method: "functionCalling"`.
```typescript
const structured = model.withStructuredOutput(schema); // ✅ defaults to functionCalling
const structured = model.withStructuredOutput(schema, { method: "functionCalling" }); // ✅ explicit
```

Because: OpenRouter's API compatibility layer does not consistently support `response_format: { type: "json_schema" }`. Function calling works reliably across all OpenRouter-proxied models. Confirmed via rejected pattern testing.

---

## 4. Architecture

Over-engineering, wrong tool for the job.

### Using LangChain for Simple Single-Provider Chat

❌ Don't: Pull in LangChain just to chat with one LLM provider.
```typescript
import { ChatOpenAI } from "@langchain/openai";
import { StringOutputParser } from "@langchain/core/output_parsers";
import { ChatPromptTemplate } from "@langchain/core/prompts";

const chain = ChatPromptTemplate.fromMessages([
  ["system", "You are helpful."],
  ["human", "{input}"],
]).pipe(new ChatOpenAI({ model: "gpt-4o" })).pipe(new StringOutputParser());

const result = await chain.invoke({ input: "Hello" });
```

✅ Do: Use the provider SDK directly, or Vercel AI SDK for streaming UIs.
```typescript
// Direct SDK — simplest
import OpenAI from "openai";
const client = new OpenAI();
const response = await client.chat.completions.create({
  model: "gpt-4o",
  messages: [{ role: "user", content: "Hello" }],
});

// Or Vercel AI SDK — best for Next.js streaming
import { generateText } from "ai";
import { openai } from "@ai-sdk/openai";
const { text } = await generateText({ model: openai("gpt-4o"), prompt: "Hello" });
```

Because: For single-provider chat, LangChain adds ~500KB+ of bundle size, introduces abstraction layers, and provides zero value over the direct SDK. Community consensus (Reddit, HN, dev blogs): "For 80% of LLM applications that use a single provider, direct SDKs are better." LangChain's value begins when you need multi-provider switching, tool calling orchestration, or complex agent state management.

---

### Using LCEL When createAgent Is Simpler

❌ Don't: Write a complex LCEL chain to build an agent that `createAgent` handles out of the box.
```typescript
// ❌ Manually wiring agent loop with LCEL
const agentRunnable = prompt
  .pipe(model.bindTools(tools))
  .pipe(new ToolCallingAgentOutputParser());

const executor = AgentExecutor.fromAgentAndTools({
  agent: agentRunnable,
  tools,
});
```

✅ Do: Use `createAgent` — it handles the agent loop, tool execution, and structured output internally.
```typescript
import { createAgent } from "langchain";
const agent = createAgent({
  model,
  tools,
  systemPrompt: "You are a helpful assistant.",
});
const result = await agent.invoke({ messages: [{ role: "user", content: "Search for X" }] });
```

Because: `createAgent` (v1) encapsulates the entire agent loop including tool execution, retry logic, middleware support, and structured output strategies. Writing it manually with LCEL duplicates this logic, loses middleware support, and produces harder-to-debug code. Use LCEL for genuinely custom chain compositions that don't fit the agent pattern.

---

### Over-Using LangGraph for Simple Flows

❌ Don't: Build a LangGraph state machine for a linear, non-branching workflow.
```typescript
// ❌ Overkill for a simple prompt→model→parse flow
const graph = new StateGraph(MyAnnotation)
  .addNode("format", formatNode)
  .addNode("generate", generateNode)
  .addNode("parse", parseNode)
  .addEdge(START, "format")
  .addEdge("format", "generate")
  .addEdge("generate", "parse")
  .addEdge("parse", END);
```

✅ Do: Use LCEL `.pipe()` or plain async functions for linear flows. Reserve LangGraph for workflows with cycles, branching, human-in-the-loop, or persistent state.
```typescript
const result = await prompt.pipe(model).pipe(parser).invoke(input);
```

Because: LangGraph's value is in graph-based state management with cycles, conditional branching, persistence, and interrupts. For linear A→B→C flows, it adds complexity with no benefit. The state graph setup, annotation definition, and node wiring are unnecessary overhead for simple chains.

---

## 5. Common Bugs

Gotchas that cause runtime failures — confirmed by testing and community reports.

### Using `new ToolStrategy(schema)` Instead of `ToolStrategy.fromSchema(schema)`

❌ Don't: Construct `ToolStrategy` directly with a Zod schema.
```typescript
import { ToolStrategy } from "langchain";
const strategy = new ToolStrategy(ResponseSchema); // ❌ Throws: Cannot read properties of undefined
```

✅ Do: Use the static factory method.
```typescript
const strategy = ToolStrategy.fromSchema(ResponseSchema); // ✅
```

Because: The `ToolStrategy` constructor expects `(schema, tool, options)` where `tool` is a pre-built OpenAI function definition object. Passing a Zod schema as the first argument leaves `tool` undefined, causing `Cannot read properties of undefined (reading 'function')` when accessing `this.tool.function.name`. The `.fromSchema()` factory correctly converts the Zod schema into the required tool definition. Confirmed via testing.

---

### Using `{ models: [...] }` for modelFallbackMiddleware

❌ Don't: Pass an options object with a `models` array.
```typescript
import { modelFallbackMiddleware } from "langchain";
const fallback = modelFallbackMiddleware({ models: [fallbackModel] });
// ❌ Error: llm [object Object] must define bindTools method
```

✅ Do: Pass fallback models as spread arguments.
```typescript
const fallback = modelFallbackMiddleware(fallbackModel);
const fallback = modelFallbackMiddleware(model1, model2, model3);
```

Because: The function signature is `modelFallbackMiddleware(...fallbackModels)`, not `modelFallbackMiddleware(options)`. Passing `{ models: [...] }` is interpreted as a single "model" argument — a plain object that lacks `bindTools`, causing the error. Confirmed via testing.

---

### Using `maxToolCalls` Instead of `runLimit`/`threadLimit`

❌ Don't: Use the non-existent `maxToolCalls` option.
```typescript
import { toolCallLimitMiddleware } from "langchain";
const limit = toolCallLimitMiddleware({ maxToolCalls: 5 });
// ❌ Error: At least one limit is specified
```

✅ Do: Use `runLimit` (per-invocation) or `threadLimit` (per-thread, cumulative).
```typescript
const limit = toolCallLimitMiddleware({ runLimit: 5 }); // Max 5 tool calls per .invoke()
const limit = toolCallLimitMiddleware({ threadLimit: 20 }); // Max 20 across all invocations in thread
```

Because: The API uses `runLimit` and `threadLimit` — not `maxToolCalls`. There is no `maxToolCalls` parameter. Using it silently passes validation but results in no limits being set, triggering the "at least one limit" error. Confirmed via testing.

---

### Resuming Interrupts with Plain Object Instead of Command

❌ Don't: Pass a plain object to resume a human-in-the-loop interrupt.
```typescript
// ❌ Triggers another interrupt instead of resuming
const result = await app.invoke({ resume: "approved" }, config);
```

✅ Do: Use the `Command` class from `@langchain/langgraph`.
```typescript
import { Command } from "@langchain/langgraph";
const result = await app.invoke(new Command({ resume: "approved" }), config);
```

Because: The graph's `invoke` method checks for `instanceof Command` to determine whether to resume an interrupted node or start a new execution. A plain object `{ resume: "approved" }` is treated as new input, which re-enters the graph from the start and hits the same interrupt again — creating an infinite loop. Confirmed via testing.

---

### InMemoryStore Mutable References

❌ Don't: Assume objects stored in `InMemoryStore` are copied.
```typescript
const store = new InMemoryStore();
const data = { count: 0 };
await store.put("ns", "key", data);
data.count = 999; // ❌ Mutates the stored value!
const retrieved = await store.get("ns", "key");
console.log(retrieved.value.count); // 999 — not 0!
```

✅ Do: Clone data before storing, or treat stored objects as immutable.
```typescript
await store.put("ns", "key", structuredClone(data)); // ✅ Deep copy
// or
await store.put("ns", "key", JSON.parse(JSON.stringify(data))); // ✅ Serialize/deserialize
```

Because: `InMemoryStore` stores object references, not copies. Mutating the original object after storing it silently corrupts the stored state. This is particularly dangerous in agent loops where state is accumulated across iterations. In production, use a proper persistent store (PostgreSQL, Redis) which naturally serializes/deserializes data.

---

## 6. Performance

Token waste and unnecessary overhead.

### Not Using LangSmith for Debugging

❌ Don't: Debug LangChain applications by adding `console.log` everywhere and guessing at token usage.
```typescript
const result = await agent.invoke({ messages }); // What happened internally? 🤷
```

✅ Do: Enable LangSmith tracing during development. It's free for the development tier.
```bash
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY=lsv2_pt_...
export LANGSMITH_PROJECT=my-project
```

Because: LangChain does things behind the scenes — retry loops, internal validation calls, schema conversion. Without tracing, you can't see how many LLM calls were actually made, what prompts were sent, or how many tokens were consumed. A documented case showed 2.7× token waste that was invisible without tracing. LangSmith shows every call, its inputs/outputs, latency, and cost — even if you later switch away from LangChain for production.

---

### Not Setting Verbose Mode in Development

❌ Don't: Run LangChain in silent mode during development.
```typescript
const model = new ChatOpenAI({ model: "gpt-4o" }); // No visibility into calls
```

✅ Do: Enable verbose mode or callbacks during development.
```typescript
const model = new ChatOpenAI({
  model: "gpt-4o",
  verbose: true, // ✅ Logs all calls to console
});
// Or use callbacks for structured logging
const model = new ChatOpenAI({
  model: "gpt-4o",
  callbacks: [new ConsoleCallbackHandler()],
});
```

Because: Without verbose mode, LangChain silently makes API calls, retries on failures, and performs internal operations you don't see. When debugging issues like unexpected token usage, slow responses, or wrong outputs, the first step is always seeing what's actually happening. Enable tracing in development, disable in production.

---

### Not Pinning Package Versions

❌ Don't: Use caret ranges for LangChain packages.
```json
{
  "@langchain/core": "^1.0.0",
  "@langchain/openai": "^1.0.0",
  "langchain": "^1.0.0"
}
```

✅ Do: Pin exact versions or use narrow ranges, and keep all `@langchain/*` packages aligned.
```json
{
  "@langchain/core": "1.1.34",
  "@langchain/openai": "1.3.0",
  "langchain": "1.2.35"
}
```

Because: LangChain's ecosystem has many independently-versioned packages. Version mismatches between `@langchain/core` and provider packages cause cryptic runtime errors — wrong method signatures, missing types, or silent behavior changes. The LangChain team publishes packages frequently (sometimes daily). Even post-v1.0, minor version bumps can change behavior. Pin versions, update deliberately, and test after every update. Multiple production users report this as a top source of mysterious bugs.

---

### Hidden Token Waste from Abstraction Overhead

❌ Don't: Assume LangChain's built-in token count is accurate, or that it makes only the calls you expect.
```typescript
const result = await chain.invoke(input);
console.log(result.usage?.totalTokens); // May show $0.00 or wrong numbers
```

✅ Do: Track token usage independently via LangSmith or provider-level callbacks.
```typescript
// Track via LangSmith (recommended)
// Set LANGSMITH_TRACING=true — see full token breakdown per call

// Or track via callback
import { BaseCallbackHandler } from "@langchain/core/callbacks/base";
class TokenTracker extends BaseCallbackHandler {
  name = "token-tracker";
  totalTokens = 0;
  async handleLLMEnd(output: any) {
    const usage = output.llmOutput?.tokenUsage;
    if (usage) this.totalTokens += usage.totalTokens;
  }
}
```

Because: A documented case showed a RAG system using LangChain consumed 2.7× more tokens than an equivalent manual implementation (1,017 vs 487 tokens). Causes included suboptimal batching, hidden internal validation calls, and inefficient context management. LangChain's built-in cost tracking was also broken (showing $0.00). Always verify token usage independently.
