# LangChain.js TypeScript Pattern Catalog

> All patterns tested and verified 2026-03-21
> Packages: langchain@1.2.35, @langchain/core@1.1.34, @langchain/openai@1.3.0, @langchain/langgraph@1.2.5, @langchain/textsplitters@1.0.1, @langchain/openrouter, zod@4.3.6
> Model: anthropic/claude-sonnet-4-6 via OpenRouter

---

## 1. Core Primitives

### Basic ChatModel Invocation

**When to use**: You need a simple LLM call with a string prompt or message array.
**When NOT to use**: You need structured output, tool calling, or multi-turn agents.
**Packages**: `@langchain/openai@1.3.0`
**OpenRouter**: Compatible

```typescript
import { AIMessage } from "@langchain/core/messages";
import { ChatOpenAI } from "@langchain/openai";

const model = new ChatOpenAI({
  model: "anthropic/claude-sonnet-4-6",
  configuration: {
    baseURL: "https://openrouter.ai/api/v1",
    apiKey: process.env.OPENROUTER_API_KEY!,
  },
});

const response = await model.invoke("Say hello in exactly 3 words.");
// response is AIMessage with .content (string), .id, .usage_metadata
```

**Failure modes**: Invalid API key returns 401; invalid model string returns 404 from OpenRouter.
**Notes**: Standard ChatOpenAI works with OpenRouter by setting `configuration.baseURL` and `configuration.apiKey`. Response is an `AIMessage` with string content, a unique ID, and token usage metadata.

---

### Tool Calling with Zod

**When to use**: You need the model to call a function with validated arguments.
**When NOT to use**: You only need free-form text responses without structured function calls.
**Packages**: `@langchain/core@1.1.34`, `@langchain/openai@1.3.0`, `zod@4.3.6`
**OpenRouter**: Compatible

```typescript
import { z } from "zod";
import { tool } from "@langchain/core/tools";
import { ChatOpenAI } from "@langchain/openai";

const weatherTool = tool(
  async ({ city }: { city: string }) => {
    return `The weather in ${city} is 72°F and sunny.`;
  },
  {
    name: "get_weather",
    description: "Get the current weather for a city",
    schema: z.object({
      city: z.string().describe("The city name to get weather for"),
    }),
  }
);

const model = new ChatOpenAI({ /* OpenRouter config */ });
const modelWithTools = model.bindTools([weatherTool]);

const response = await modelWithTools.invoke("What is the weather in San Francisco?");
// response.tool_calls = [{ name: "get_weather", args: { city: "San Francisco" }, id: "..." }]

const toolResult = await weatherTool.invoke(response.tool_calls[0].args);
// "The weather in San Francisco is 72°F and sunny."
```

**Failure modes**: Missing `.describe()` on schema fields degrades tool selection accuracy; forgetting `bindTools()` means the model never calls tools.
**Notes**: `tool()` from `@langchain/core/tools` works with Zod v4 schemas. Tool calls come back in `response.tool_calls` with parsed args (not raw JSON). Tools can be executed directly with `.invoke(args)`.

---

### Structured Output with withStructuredOutput

**When to use**: You need a typed object response matching a Zod schema from a single model call.
**When NOT to use**: You are piping from a `ChatPromptTemplate` on OpenRouter (use Prompt+Parse workaround instead).
**Packages**: `@langchain/openai@1.3.0`, `zod@4.3.6`
**OpenRouter**: Compatible (direct invoke only — see LCEL section for pipe workaround)

```typescript
import { z } from "zod";
import { ChatOpenAI } from "@langchain/openai";

const PersonSchema = z.object({
  name: z.string().describe("The person's full name"),
  age: z.number().describe("The person's age in years"),
  occupation: z.string().describe("The person's job or occupation"),
});

type Person = z.infer<typeof PersonSchema>;

const model = new ChatOpenAI({ /* OpenRouter config */ });
const structuredModel = model.withStructuredOutput(PersonSchema);

const result: Person = await structuredModel.invoke(
  "Tell me about a fictional character: a 35-year-old software engineer named Alice Chen."
);
// { name: "Alice Chen", age: 35, occupation: "Software Engineer" }
```

**Failure modes**: On OpenRouter, `withStructuredOutput()` returns 400 errors when piped from a prompt template. Use the Prompt+Parse LCEL workaround for chains.
**Notes**: Returns a typed object (not an AIMessage). The model uses function calling under the hood. Return type is the Zod inferred type.

---

### Streaming

**When to use**: You need real-time token-by-token output for UX responsiveness.
**When NOT to use**: You need the full response atomically (use `.invoke()` instead).
**Packages**: `@langchain/openai@1.3.0`
**OpenRouter**: Compatible

```typescript
import { ChatOpenAI } from "@langchain/openai";

const model = new ChatOpenAI({ /* OpenRouter config */ });

const stream = await model.stream("Count from 1 to 5, one number per line.");

const chunks: string[] = [];
for await (const chunk of stream) {
  const content = typeof chunk.content === "string" ? chunk.content : "";
  if (content.length > 0) {
    chunks.push(content);
  }
}

const fullText = chunks.join("");
```

**Failure modes**: OpenRouter may batch content into fewer chunks than direct API — don't assume one token per chunk.
**Notes**: `model.stream()` returns an async iterable of `AIMessageChunk` objects. Each chunk has `.content` (string). Chunks arrive incrementally and can be concatenated.

---

### ChatPromptTemplate

**When to use**: You need to compose system/human messages with variable interpolation.
**When NOT to use**: Your prompt is a static string with no variables.
**Packages**: `@langchain/core@1.1.34`
**OpenRouter**: Compatible

```typescript
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { ChatOpenAI } from "@langchain/openai";

const prompt = ChatPromptTemplate.fromMessages([
  ["system", "You are a helpful assistant that speaks {language}."],
  ["human", "Translate '{text}' to {language}. Reply with only the translation."],
]);

const model = new ChatOpenAI({ /* OpenRouter config */ });

// Option A: Format messages manually
const formatted = await prompt.formatMessages({ language: "French", text: "Hello world" });

// Option B: Pipe to model (LCEL)
const chain = prompt.pipe(model);
const response = await chain.invoke({ language: "Spanish", text: "Good morning" });
// response.content = "Buenos días"
```

**Failure modes**: Missing template variables at invoke time throws an error; using `${}` instead of `{}` syntax silently fails.
**Notes**: `.fromMessages()` accepts `[role, template]` tuples. Variables use `{varName}` syntax. `.pipe()` creates an LCEL chain.

---

### initChatModel (Universal Model Init)

**When to use**: You need provider-agnostic model instantiation (e.g., switching providers at runtime).
**When NOT to use**: You already know the provider and want direct `ChatOpenAI` instantiation.
**Packages**: `langchain@1.2.35`
**OpenRouter**: Compatible

```typescript
import { initChatModel } from "langchain/chat_models/universal";

const model = await initChatModel("anthropic/claude-sonnet-4-6", {
  modelProvider: "openai",
  configuration: {
    baseURL: "https://openrouter.ai/api/v1",
    apiKey: process.env.OPENROUTER_API_KEY!,
  },
});

const response = await model.invoke("What is 2 + 2? Reply with just the number.");
// response.content = "4"
```

**Failure modes**: Omitting `modelProvider: "openai"` for OpenRouter causes provider detection to fail.
**Notes**: For OpenRouter, use `modelProvider: "openai"` since OpenRouter exposes an OpenAI-compatible API. The `configuration` object passes through to the underlying ChatOpenAI constructor.

---

### Multiple Tools

**When to use**: You need the model to select from several tools based on query semantics.
**When NOT to use**: You have a single tool and don't need selection logic.
**Packages**: `@langchain/core@1.1.34`, `@langchain/openai@1.3.0`, `zod@4.3.6`
**OpenRouter**: Compatible

```typescript
import { z } from "zod";
import { tool } from "@langchain/core/tools";
import { ChatOpenAI } from "@langchain/openai";

const weatherTool = tool(
  async ({ city }: { city: string }) => `Weather in ${city}: 72°F, sunny`,
  {
    name: "get_weather",
    description: "Get current weather for a city",
    schema: z.object({ city: z.string().describe("City name") }),
  }
);

const calculatorTool = tool(
  async ({ expression }: { expression: string }) => {
    const result = Function(`"use strict"; return (${expression})`)();
    return `Result: ${result}`;
  },
  {
    name: "calculator",
    description: "Evaluate a mathematical expression",
    schema: z.object({ expression: z.string().describe("A math expression like '2 + 3 * 4'") }),
  }
);

const dictionaryTool = tool(
  async ({ word }: { word: string }) => `${word}: a common English word`,
  {
    name: "dictionary_lookup",
    description: "Look up the definition of a word",
    schema: z.object({ word: z.string().describe("The word to look up") }),
  }
);

const model = new ChatOpenAI({ /* OpenRouter config */ });
const modelWithTools = model.bindTools([weatherTool, calculatorTool, dictionaryTool]);

const response = await modelWithTools.invoke("What is 15 * 23 + 7?");
// Correctly selects calculator: tool_calls[0].name = "calculator", args = { expression: "15 * 23 + 7" }

const result = await calculatorTool.invoke(response.tool_calls[0].args);
// "Result: 352"
```

**Failure modes**: Vague or overlapping tool descriptions cause incorrect tool selection; too many tools can confuse the model.
**Notes**: `bindTools()` accepts an array of tools. The model correctly selects the appropriate tool based on the query. Tool names and descriptions are important for routing accuracy.

---

## 2. Agents

### createAgent Basic

**When to use**: You need a ReAct agent that can use tools and maintain conversation flow.
**When NOT to use**: You need a simple one-shot LLM call without tools or multi-step reasoning.
**Packages**: `langchain@1.2.35`, `@langchain/core@1.1.34`, `@langchain/openai@1.3.0`, `zod@4.3.6`
**OpenRouter**: Compatible

```typescript
import { createAgent } from "langchain";
import { tool } from "@langchain/core/tools";
import { z } from "zod";
import { ChatOpenAI } from "@langchain/openai";

const model = new ChatOpenAI({
  model: "anthropic/claude-sonnet-4-6",
  configuration: {
    baseURL: "https://openrouter.ai/api/v1",
    apiKey: process.env.OPENROUTER_API_KEY!,
  },
});

const searchTool = tool(
  ({ query }: { query: string }) => `Search results for: ${query}`,
  {
    name: "search",
    description: "Search for information on the web",
    schema: z.object({ query: z.string().describe("The search query") }),
  }
);

const agent = createAgent({
  model,
  tools: [searchTool],
  prompt: "You are a helpful assistant. Use the search tool when asked to find information.",
});

const result = await agent.invoke({
  messages: [{ role: "user", content: "Search for TypeScript news" }],
});

// result.messages is an array: [HumanMessage, AIMessage (tool call), ToolMessage, AIMessage (final)]
const messages = result.messages;
```

**Failure modes**: Using `systemPrompt` instead of `prompt` silently ignores the system message; passing a string model instead of ChatOpenAI instance fails.
**Notes**: `createAgent` is the high-level agent factory in langchain v1. Returns a LangGraph `ReactAgent`. The `prompt` parameter sets the system prompt. `result.messages` contains the full conversation: HumanMessage → AIMessage (with tool_calls) → ToolMessage → AIMessage (final response). The agent automatically decides whether to use tools.

---

### createAgent with Structured Output (ToolStrategy)

**When to use**: You need an agent that returns a structured, typed response matching a Zod schema.
**When NOT to use**: Free-form text responses are sufficient.
**Packages**: `langchain@1.2.35`, `zod@4.3.6`
**OpenRouter**: Compatible

```typescript
import { createAgent, ToolStrategy } from "langchain";
import { tool } from "@langchain/core/tools";
import { z } from "zod";

const ResponseSchema = z.object({
  summary: z.string().describe("A brief summary of the findings"),
  topics: z.array(z.string()).describe("List of topics found"),
  confidence: z.number().min(0).max(1).describe("Confidence score"),
});

// Use ToolStrategy.fromSchema() — NOT new ToolStrategy(schema)
const strategy = ToolStrategy.fromSchema(ResponseSchema);

const agent = createAgent({
  model,
  tools: [searchTool],
  responseFormat: strategy,
  prompt: "You are a helpful assistant. Search and return structured results.",
});

const result = await agent.invoke({
  messages: [{ role: "user", content: "Search for latest JavaScript framework news" }],
});

// result.structuredResponse contains the typed response
const structured = result.structuredResponse;
// { summary: "...", topics: ["TypeScript 5.8", ...], confidence: 0.85 }
```

**Failure modes**: Using `new ToolStrategy(schema)` instead of `ToolStrategy.fromSchema(schema)` — the constructor requires different arguments and will fail.
**Notes**: **CRITICAL**: Use `ToolStrategy.fromSchema(schema)` static method, NOT `new ToolStrategy(schema)`. `result.structuredResponse` contains the parsed, typed object. Works reliably with OpenRouter because it uses standard tool calling mechanism.

---

### createAgent with Middleware (beforeModel, afterModel, dynamicSystemPrompt)

**When to use**: You need to intercept, log, or modify model calls before/after execution.
**When NOT to use**: You don't need any custom processing hooks around model invocations.
**Packages**: `langchain@1.2.35`
**OpenRouter**: Compatible

```typescript
import { createAgent, createMiddleware, dynamicSystemPromptMiddleware } from "langchain";

// beforeModel middleware
const loggingMiddleware = createMiddleware({
  name: "logging-middleware",
  beforeModel: async (state, config) => {
    console.log(`Messages so far: ${state.messages.length}`);
    return undefined; // continue with normal flow
  },
});

// afterModel middleware
const afterModelMiddleware = createMiddleware({
  name: "after-model-middleware",
  afterModel: async (state, config) => {
    const lastMsg = state.messages[state.messages.length - 1];
    console.log(`Model produced: ${lastMsg.constructor.name}`);
    return undefined;
  },
});

// Dynamic system prompt middleware
const dynamicPrompt = dynamicSystemPromptMiddleware(async (state) => {
  const msgCount = state.messages.length;
  return `You are a helpful assistant. Current conversation has ${msgCount} messages.`;
});

const agent = createAgent({
  model,
  tools: [searchTool],
  middleware: [loggingMiddleware, afterModelMiddleware],
  prompt: "You are a helpful assistant.",
});

// Or with dynamic prompt (replaces static `prompt` parameter):
const agentDynamic = createAgent({
  model,
  tools: [searchTool],
  middleware: [dynamicPrompt],
  // No `prompt` needed — the middleware provides it dynamically
});
```

**Failure modes**: Returning a value (instead of `undefined`) from beforeModel/afterModel overrides the normal flow — return `undefined` to continue normally.
**Notes**: `beforeModel` fires before each LLM call. `afterModel` fires after each LLM response. Middleware is called on every model invocation (including after tool results), so expect multiple calls per `agent.invoke()`. `dynamicSystemPromptMiddleware` replaces the static `prompt` parameter — useful for injecting dynamic context.

---

### Agent Streaming (values, updates, streamEvents)

**When to use**: You need real-time streaming of agent execution steps or token-level output.
**When NOT to use**: You only need the final agent result without intermediate updates.
**Packages**: `langchain@1.2.35`
**OpenRouter**: Compatible

```typescript
const agent = createAgent({
  model,
  tools: [searchTool],
  prompt: "You are a helpful assistant.",
});

// "values" mode: full accumulated state after each node
const stream = await agent.stream(
  { messages: [{ role: "user", content: "Search for TypeScript news" }] },
  { streamMode: "values" }
);
for await (const chunk of stream) {
  const lastMsg = chunk.messages[chunk.messages.length - 1];
  console.log(`[${lastMsg.constructor.name}] ${lastMsg.content}`);
}

// "updates" mode: delta from each node
const stream2 = await agent.stream(
  { messages: [{ role: "user", content: "Search for news" }] },
  { streamMode: "updates" }
);
for await (const chunk of stream2) {
  for (const [node, data] of Object.entries(chunk)) {
    console.log(`Node "${node}":`, data.messages.length, "message(s)");
  }
}

// streamEvents: token-level streaming
const stream3 = agent.streamEvents(
  { messages: [{ role: "user", content: "What is 2+2?" }] },
  { version: "v2" }
);
for await (const event of stream3) {
  if (event.event === "on_chat_model_stream") {
    const token = event.data?.chunk?.content;
    process.stdout.write(token || "");
  }
}
```

**Failure modes**: Using `streamEvents` without `{ version: "v2" }` may return unexpected event format.
**Notes**: `streamMode: "values"` emits progressive snapshots. `streamMode: "updates"` emits per-node deltas (nodes are `"model_request"` and `"tools"`). `streamEvents()` provides fine-grained token-level streaming via `on_chat_model_stream` events.

---

### Multi-Tool Agent Decision Making

**When to use**: You have multiple tools and need the agent to autonomously select the right one per query.
**When NOT to use**: You have a single tool or want to force a specific tool.
**Packages**: `langchain@1.2.35`, `@langchain/core@1.1.34`, `zod@4.3.6`
**OpenRouter**: Compatible

```typescript
import { createAgent } from "langchain";
import { tool } from "@langchain/core/tools";
import { z } from "zod";

const searchTool = tool(
  ({ query }: { query: string }) => `Search results for "${query}"`,
  {
    name: "web_search",
    description: "Search the web for current information, news, and articles",
    schema: z.object({ query: z.string() }),
  }
);

const calculatorTool = tool(
  ({ expression }: { expression: string }) => {
    const result = Function(`"use strict"; return (${expression})`)();
    return `Result: ${result}`;
  },
  {
    name: "calculator",
    description: "Evaluate mathematical expressions",
    schema: z.object({ expression: z.string() }),
  }
);

const weatherTool = tool(
  ({ city }: { city: string }) => `Weather in ${city}: 22°C, partly cloudy`,
  {
    name: "get_weather",
    description: "Get the current weather for a specific city",
    schema: z.object({ city: z.string() }),
  }
);

const agent = createAgent({
  model,
  tools: [searchTool, calculatorTool, weatherTool],
  prompt: "You are a helpful assistant with search, calculator, and weather tools.",
});

// Agent correctly selects:
// "Search for AI news" → web_search
// "What is 156 * 23 + 89?" → calculator
// "What's the weather in Tokyo?" → get_weather
```

**Failure modes**: Vague descriptions or overlapping tool capabilities degrade selection accuracy.
**Notes**: The agent reliably selects the correct tool based on query semantics. Tool names and descriptions are critical for routing accuracy.

---

### Agent with Conversation History (MemorySaver)

**When to use**: You need a multi-turn agent that remembers context across invocations.
**When NOT to use**: Each invocation is independent with no need for conversation history.
**Packages**: `langchain@1.2.35`, `@langchain/langgraph@1.2.5`
**OpenRouter**: Compatible

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

const threadId = "test-thread-123";
const config = { configurable: { thread_id: threadId } };

// Turn 1
await agent.invoke(
  { messages: [{ role: "user", content: "My name is Alice and I'm a software engineer." }] },
  config
);

// Turn 2 — agent remembers Alice is a software engineer
const result = await agent.invoke(
  { messages: [{ role: "user", content: "What is my name and what do I do?" }] },
  config
);
// Response includes "Alice" and "software engineer"

// Different thread has NO memory of Alice
await agent.invoke(
  { messages: [{ role: "user", content: "What is my name?" }] },
  { configurable: { thread_id: "different-thread" } }
);
// Response: "I don't know your name"
```

**Failure modes**: Forgetting to pass `config` with `thread_id` to each invoke loses conversation state; using the same thread_id for unrelated users leaks context.
**Notes**: `MemorySaver` is in-memory only (dev/testing). Each `thread_id` maintains an isolated conversation. For production, replace with `PostgresSaver` or `SqliteSaver`.

---

## 3. LangGraph

### Basic StateGraph with MessagesAnnotation

**When to use**: You need a stateful graph workflow with LLM-based nodes and message passing.
**When NOT to use**: A simple chain or single model call suffices.
**Packages**: `@langchain/langgraph@1.2.5`, `@langchain/core@1.1.34`
**OpenRouter**: Compatible

```typescript
import { StateGraph, MessagesAnnotation, START, END } from "@langchain/langgraph";
import { HumanMessage } from "@langchain/core/messages";
import { ChatOpenAI } from "@langchain/openai";

const model = new ChatOpenAI({
  model: "anthropic/claude-sonnet-4-6",
  configuration: {
    baseURL: "https://openrouter.ai/api/v1",
    apiKey: process.env.OPENROUTER_API_KEY!,
  },
});

async function callModel(state: typeof MessagesAnnotation.State) {
  const response = await model.invoke(state.messages);
  return { messages: [response] };
}

const graph = new StateGraph(MessagesAnnotation)
  .addNode("agent", callModel)
  .addEdge(START, "agent")
  .addEdge("agent", END);

const app = graph.compile();

const result = await app.invoke({
  messages: [new HumanMessage("What is 2+2? Reply with just the number.")],
});

// result.messages = [HumanMessage, AIMessage]
console.log(result.messages[result.messages.length - 1].content); // "4"
```

**Failure modes**: Returning `response` directly instead of `{ messages: [response] }` breaks the message reducer.
**Notes**: `MessagesAnnotation` provides `{ messages: BaseMessage[] }` state with built-in message reducer. Nodes return `{ messages: [newMessage] }` — the reducer appends. `START` and `END` are string constants. `.compile()` returns a `CompiledStateGraph`.

---

### ReAct Agent with Tools (ToolNode + toolsCondition)

**When to use**: You need a tool-calling agent loop: model decides → tools execute → model responds.
**When NOT to use**: You want a simpler `createAgent` without manual graph construction.
**Packages**: `@langchain/langgraph@1.2.5`, `@langchain/core@1.1.34`, `zod@4.3.6`
**OpenRouter**: Compatible

```typescript
import { StateGraph, MessagesAnnotation, START, END } from "@langchain/langgraph";
import { ToolNode, toolsCondition } from "@langchain/langgraph/prebuilt";
import { HumanMessage } from "@langchain/core/messages";
import { tool } from "@langchain/core/tools";
import { z } from "zod";

const multiply = tool(
  async ({ a, b }: { a: number; b: number }) => {
    return `${a * b}`;
  },
  {
    name: "multiply",
    description: "Multiply two numbers together",
    schema: z.object({
      a: z.number().describe("First number"),
      b: z.number().describe("Second number"),
    }),
  }
);

const tools = [multiply];
const model = new ChatOpenAI({ /* ... */ }).bindTools(tools);
const toolNode = new ToolNode(tools);

async function callAgent(state: typeof MessagesAnnotation.State) {
  const response = await model.invoke(state.messages);
  return { messages: [response] };
}

const graph = new StateGraph(MessagesAnnotation)
  .addNode("agent", callAgent)
  .addNode("tools", toolNode)
  .addEdge(START, "agent")
  .addConditionalEdges("agent", toolsCondition)  // routes to "tools" or END
  .addEdge("tools", "agent");                     // loop back after tool execution

const app = graph.compile();

const result = await app.invoke({
  messages: [new HumanMessage("What is 7 multiplied by 8?")],
});
// result.messages = [HumanMessage, AIMessage(tool_call), ToolMessage, AIMessage(final)]
```

**Failure modes**: Forgetting `model.bindTools(tools)` means the model never generates tool calls; forgetting the `tools → agent` edge breaks the ReAct loop.
**Notes**: `ToolNode` from `@langchain/langgraph/prebuilt` executes tool calls from AIMessage. `toolsCondition` is a built-in router that returns `"tools"` if AIMessage has tool_calls, else `END`. No need to specify path map.

---

### Custom State with Annotation.Root

**When to use**: You need graph state beyond just messages (e.g., custom fields, counters, classifications).
**When NOT to use**: Your workflow only needs message passing — use `MessagesAnnotation` instead.
**Packages**: `@langchain/langgraph@1.2.5`
**OpenRouter**: Compatible

```typescript
import { Annotation, StateGraph, START, END } from "@langchain/langgraph";

const CustomState = Annotation.Root({
  topic: Annotation<string>,
  summary: Annotation<string>,
  wordCount: Annotation<number>,
});

async function summarize(state: typeof CustomState.State) {
  const response = await model.invoke(
    `Summarize the topic "${state.topic}" in exactly one sentence.`
  );
  const summary = typeof response.content === "string"
    ? response.content
    : String(response.content);
  return { summary, wordCount: summary.split(/\s+/).length };
}

const graph = new StateGraph(CustomState)
  .addNode("summarize", summarize)
  .addEdge(START, "summarize")
  .addEdge("summarize", END);

const app = graph.compile();

const result = await app.invoke({
  topic: "TypeScript generics",
  summary: "",
  wordCount: 0,
});

// result.topic = "TypeScript generics" (unchanged)
// result.summary = "TypeScript generics allow you to write reusable..."
// result.wordCount = 25
```

**Failure modes**: Forgetting to provide initial values for all state fields at invoke time can cause undefined behavior.
**Notes**: `Annotation.Root({...})` creates a state schema; each field uses `Annotation<T>`. Without a custom reducer, each field uses last-write-wins. Node functions return partial state — only updated fields. Type `typeof CustomState.State` gives full TypeScript typing.

---

### Conditional Edges (Router Pattern)

**When to use**: You need to route to different nodes based on runtime state or classification.
**When NOT to use**: Your workflow is purely linear with no branching.
**Packages**: `@langchain/langgraph@1.2.5`
**OpenRouter**: Compatible

```typescript
import { Annotation, StateGraph, START, END } from "@langchain/langgraph";

const RouterState = Annotation.Root({
  input: Annotation<string>,
  category: Annotation<string>,
  response: Annotation<string>,
});

async function classify(state: typeof RouterState.State) {
  const response = await model.invoke(
    `Classify this input into exactly one word - either "math" or "general": "${state.input}". Reply with ONLY the category word.`
  );
  const category = String(response.content).trim().toLowerCase();
  return { category };
}

async function handleMath(state: typeof RouterState.State) {
  const response = await model.invoke(`Solve this math problem concisely: ${state.input}`);
  return { response: String(response.content) };
}

async function handleGeneral(state: typeof RouterState.State) {
  const response = await model.invoke(`Answer this general question concisely: ${state.input}`);
  return { response: String(response.content) };
}

function route(state: typeof RouterState.State): string {
  if (state.category.includes("math")) {
    return "handleMath";
  }
  return "handleGeneral";
}

const graph = new StateGraph(RouterState)
  .addNode("classify", classify)
  .addNode("handleMath", handleMath)
  .addNode("handleGeneral", handleGeneral)
  .addEdge(START, "classify")
  .addConditionalEdges("classify", route)
  .addEdge("handleMath", END)
  .addEdge("handleGeneral", END);

const app = graph.compile();

// Routes "What is 15 times 23?" → classify → handleMath → END
// Routes "What color is the sky?" → classify → handleGeneral → END
```

**Failure modes**: Router function returning a node name that doesn't exist in the graph throws a runtime error.
**Notes**: `addConditionalEdges(sourceNode, routerFunction)` — router returns target node name as string. Each terminal node needs an explicit `addEdge(node, END)`.

---

### Checkpointing with MemorySaver (LangGraph)

**When to use**: You need to persist graph state across invocations for multi-turn conversations.
**When NOT to use**: Each graph invocation is independent with no state carry-over.
**Packages**: `@langchain/langgraph@1.2.5`
**OpenRouter**: Compatible

```typescript
import { StateGraph, MessagesAnnotation, START, END, MemorySaver } from "@langchain/langgraph";
import { HumanMessage } from "@langchain/core/messages";

async function callModel(state: typeof MessagesAnnotation.State) {
  const response = await model.invoke(state.messages);
  return { messages: [response] };
}

const graph = new StateGraph(MessagesAnnotation)
  .addNode("agent", callModel)
  .addEdge(START, "agent")
  .addEdge("agent", END);

const checkpointer = new MemorySaver();
const app = graph.compile({ checkpointer });

const config = { configurable: { thread_id: "my-thread" } };

// Turn 1
const result1 = await app.invoke(
  { messages: [new HumanMessage("My name is Alice.")] },
  config
);
// result1.messages.length = 2

// Turn 2 — same thread_id, state carries over
const result2 = await app.invoke(
  { messages: [new HumanMessage("What is my name?")] },
  config
);
// result2.messages.length = 4 (Turn1 history + Turn2 messages)
// AI responds: "Your name is Alice!"
```

**Failure modes**: Omitting `checkpointer` in `compile()` means state is lost between invocations; omitting `thread_id` in config causes errors.
**Notes**: `MemorySaver` is in-memory (dev/testing only). Pass `{ configurable: { thread_id: "..." } }` as second arg to `.invoke()`. State accumulates across invocations with same thread_id. Different thread_ids get isolated state.

---

### Functional API (entrypoint + task)

**When to use**: You need a simpler, imperative-style workflow without explicit graph structure.
**When NOT to use**: You need complex branching, conditional edges, or cycles — use StateGraph instead.
**Packages**: `@langchain/langgraph@1.2.5`
**OpenRouter**: Compatible

```typescript
import { entrypoint, task } from "@langchain/langgraph";

const generateTopic = task("generateTopic", async (input: string) => {
  const response = await model.invoke(
    `Given the subject "${input}", suggest one specific subtopic in 5 words or fewer.`
  );
  return String(response.content).trim();
});

const writeSentence = task("writeSentence", async (topic: string) => {
  const response = await model.invoke(`Write exactly one sentence about: ${topic}`);
  return String(response.content).trim();
});

const workflow = entrypoint("myWorkflow", async (input: string) => {
  const topic = await generateTopic(input);
  const sentence = await writeSentence(topic);
  return { topic, sentence };
});

const result = await workflow.invoke("artificial intelligence");
// result = { topic: "AI consciousness and self-awareness", sentence: "Whether AI can ever..." }
```

**Failure modes**: Using `task` outside an `entrypoint` context won't give you resumability/checkpointing benefits.
**Notes**: `task(name, fn)` defines a resumable, named step. `entrypoint(name, fn)` defines the workflow entry point. Tasks are awaited sequentially. Works with checkpointers for durability. Simpler for linear workflows.

---

### Streaming from Graph

**When to use**: You need real-time updates as graph nodes complete execution.
**When NOT to use**: You only need the final graph result.
**Packages**: `@langchain/langgraph@1.2.5`
**OpenRouter**: Compatible

```typescript
import { StateGraph, MessagesAnnotation, START, END } from "@langchain/langgraph";
import { HumanMessage } from "@langchain/core/messages";

// (same graph setup as Basic StateGraph)
const app = graph.compile();

// Stream mode: "updates" — emits per-node output
const stream1 = await app.stream(
  { messages: [new HumanMessage("Say hello")] },
  { streamMode: "updates" }
);
for await (const chunk of stream1) {
  // chunk = { agent: { messages: [AIMessage] } }
  console.log("Node:", Object.keys(chunk));
}

// Stream mode: "values" — emits full state snapshots
const stream2 = await app.stream(
  { messages: [new HumanMessage("Say goodbye")] },
  { streamMode: "values" }
);
for await (const chunk of stream2) {
  // chunk = { messages: [HumanMessage, ...] } — full state
  console.log("Messages so far:", chunk.messages.length);
}
```

**Failure modes**: Expecting token-level streaming from `app.stream()` — it only emits node-level updates. Use `streamEvents` for token-level.
**Notes**: `streamMode: "updates"` yields `{ nodeName: nodeOutput }` after each node completes. `streamMode: "values"` yields full state snapshot after each step. For token-level streaming, use `streamMode: "messages"` or `streamEvents`.

---

## 4. LCEL Composition

### Basic Pipe Chain (prompt → model → output parser)

**When to use**: You need to compose prompt templates, models, and output parsers into a single chain.
**When NOT to use**: You have a one-off model call with no template or post-processing.
**Packages**: `@langchain/core@1.1.34`, `@langchain/openai@1.3.0`
**OpenRouter**: Compatible

```typescript
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";
import { ChatOpenAI } from "@langchain/openai";

const model = new ChatOpenAI({
  model: "anthropic/claude-sonnet-4-6",
  configuration: {
    baseURL: "https://openrouter.ai/api/v1",
    apiKey: process.env.OPENROUTER_API_KEY!,
  },
});

const chain = ChatPromptTemplate.fromMessages([
  ["system", "You are a helpful assistant. Reply in one sentence."],
  ["human", "{input}"],
]).pipe(model).pipe(new StringOutputParser());

const result = await chain.invoke({ input: "What is TypeScript?" });
// → string response
```

**Failure modes**: Piping incompatible types (e.g., model output to a parser expecting different input format).
**Notes**: `.pipe()` is the fundamental LCEL composition operator. Chain: PromptTemplate → ChatModel → OutputParser. All chains support `.invoke()`, `.stream()`, and `.batch()` automatically.

---

### RunnableParallel

**When to use**: You need to run multiple chains concurrently with the same input and collect results.
**When NOT to use**: Chains have sequential dependencies on each other's output.
**Packages**: `@langchain/core@1.1.34`
**OpenRouter**: Compatible

```typescript
import { RunnableParallel } from "@langchain/core/runnables";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";

const parser = new StringOutputParser();

const jokeChain = ChatPromptTemplate.fromTemplate(
  "Tell a short joke about {topic}"
).pipe(model).pipe(parser);

const factChain = ChatPromptTemplate.fromTemplate(
  "Tell a one-sentence fact about {topic}"
).pipe(model).pipe(parser);

const parallel = RunnableParallel.from({
  joke: jokeChain,
  fact: factChain,
});

const result = await parallel.invoke({ topic: "TypeScript" });
// → { joke: string, fact: string }
```

**Failure modes**: If one branch fails, the entire parallel execution fails.
**Notes**: `RunnableParallel.from({...})` runs multiple chains concurrently with the same input. Results returned in an object keyed by chain names.

---

### RunnableLambda

**When to use**: You need to insert a custom sync or async function into an LCEL chain.
**When NOT to use**: You can achieve the same with built-in runnables (avoid unnecessary wrapping).
**Packages**: `@langchain/core@1.1.34`
**OpenRouter**: Compatible

```typescript
import { RunnableLambda } from "@langchain/core/runnables";

// Sync lambda
const upperCaseLambda = new RunnableLambda({
  func: (input: string) => input.toUpperCase(),
});

const chain = prompt.pipe(model).pipe(new StringOutputParser()).pipe(upperCaseLambda);
// → uppercased string

// Async lambda
const asyncLambda = new RunnableLambda({
  func: async (input: string) => {
    await someAsyncOperation();
    return `[processed] ${input}`;
  },
});
```

**Failure modes**: Throwing inside the lambda propagates up and breaks the chain.
**Notes**: `RunnableLambda` wraps any sync or async function as a Runnable, making it composable with `.pipe()`. Useful for post-processing, validation, or side effects.

---

### RunnablePassthrough

**When to use**: You need to pass input through unchanged while adding computed fields (e.g., RAG context injection).
**When NOT to use**: You don't need to augment the input with additional computed fields.
**Packages**: `@langchain/core@1.1.34`
**OpenRouter**: Compatible

```typescript
import { RunnablePassthrough } from "@langchain/core/runnables";

// .assign() adds computed fields while passing through original data
const chain = RunnablePassthrough.assign({
  uppercaseTopic: (input: { topic: string }) => input.topic.toUpperCase(),
}).pipe(
  ChatPromptTemplate.fromMessages([
    ["system", "Reply in one sentence."],
    ["human", "Tell me about {topic} (also known as {uppercaseTopic})"],
  ])
).pipe(model).pipe(new StringOutputParser());

const result = await chain.invoke({ topic: "python" });
// input becomes { topic: "python", uppercaseTopic: "PYTHON" }

// Basic passthrough (identity function)
const identity = new RunnablePassthrough();
const out = await identity.invoke({ foo: "bar" });
// → { foo: "bar" }
```

**Failure modes**: The assign callback must return a single value per key, not an object — each key gets its own function.
**Notes**: `RunnablePassthrough.assign()` is the go-to pattern for RAG chains where you need to add retrieved context alongside the original question. It passes through existing fields and adds new computed ones.

---

### RunnableBranch (Conditional Routing)

**When to use**: You need to route input to different chains based on runtime conditions in an LCEL pipeline.
**When NOT to use**: You only have one processing path (use a simple pipe chain instead).
**Packages**: `@langchain/core@1.1.34`
**OpenRouter**: Compatible

```typescript
import { RunnableBranch } from "@langchain/core/runnables";

const techChain = ChatPromptTemplate.fromTemplate(
  "Explain {topic} as a technical concept in one sentence."
).pipe(model).pipe(parser);

const funChain = ChatPromptTemplate.fromTemplate(
  "Explain {topic} in a fun, casual way in one sentence."
).pipe(model).pipe(parser);

const defaultChain = ChatPromptTemplate.fromTemplate(
  "Tell me about {topic} in one sentence."
).pipe(model).pipe(parser);

const branch = RunnableBranch.from([
  [
    (input: { topic: string; style: string }) => input.style === "technical",
    techChain,
  ],
  [
    (input: { topic: string; style: string }) => input.style === "fun",
    funChain,
  ],
  defaultChain, // fallback (last element, no condition)
]);

await branch.invoke({ topic: "recursion", style: "technical" });
// Routes to techChain
```

**Failure modes**: Forgetting the default/fallback chain (last element without condition) causes a runtime error if no condition matches.
**Notes**: `RunnableBranch.from([...conditions, default])` evaluates conditions in order and routes to the first match. Last element (without a condition) is the default/fallback.

---

### Chain Batch

**When to use**: You need to process multiple inputs concurrently with the same chain.
**When NOT to use**: You only have a single input.
**Packages**: `@langchain/core@1.1.34`
**OpenRouter**: Compatible

```typescript
const chain = ChatPromptTemplate.fromMessages([
  ["system", "Reply in exactly one word."],
  ["human", "What color is a {item}?"],
]).pipe(model).pipe(new StringOutputParser());

const results = await chain.batch([
  { item: "banana" },
  { item: "sky" },
  { item: "grass" },
]);
// → ["Yellow", "Blue", "Green"]
```

**Failure modes**: Rate limiting from the provider when batching too many requests — OpenRouter may throttle.
**Notes**: `.batch()` processes multiple inputs concurrently. All LCEL chains support `.invoke()`, `.stream()`, and `.batch()` automatically. Tested: 3 inputs completed in ~1 second (parallel execution).

---

### Chain Streaming

**When to use**: You need real-time streaming through an entire LCEL pipe chain.
**When NOT to use**: You need the full response atomically.
**Packages**: `@langchain/core@1.1.34`
**OpenRouter**: Compatible

```typescript
const chain = ChatPromptTemplate.fromMessages([
  ["system", "You are a helpful assistant. Reply in 2-3 sentences."],
  ["human", "{input}"],
]).pipe(model).pipe(new StringOutputParser());

const stream = await chain.stream({ input: "What is Rust?" });

let fullText = "";
for await (const chunk of stream) {
  process.stdout.write(chunk); // real-time streaming
  fullText += chunk;
}
```

**Failure modes**: Not all output parsers are streaming-aware — `StringOutputParser` passes through chunks correctly.
**Notes**: `.stream()` works end-to-end through the pipe chain. The `StringOutputParser` is streaming-aware: it passes through text chunks as they arrive.

---

### Structured Output via Prompt + Parse Chain (OpenRouter Workaround)

**When to use**: You need structured output in an LCEL chain on OpenRouter (where `withStructuredOutput` fails in pipes).
**When NOT to use**: You're using a direct API (not OpenRouter) where `withStructuredOutput` works in pipes.
**Packages**: `@langchain/core@1.1.34`, `zod@4.3.6`
**OpenRouter**: Workaround needed

```typescript
import { RunnableLambda } from "@langchain/core/runnables";
import { z } from "zod";

const ReviewSchema = z.object({
  summary: z.string().describe("A one-sentence summary"),
  sentiment: z.enum(["positive", "negative", "neutral"]),
  score: z.number().min(1).max(10),
});

const chain = ChatPromptTemplate.fromMessages([
  ["system", "Analyze the review. Return ONLY valid JSON with fields: summary (string), sentiment (positive/negative/neutral), score (1-10). No markdown."],
  ["human", "{review}"],
]).pipe(model).pipe(new StringOutputParser()).pipe(
  new RunnableLambda({
    func: (text: string) => {
      const cleaned = text.replace(/```json?\n?/g, "").replace(/```/g, "").trim();
      return ReviewSchema.parse(JSON.parse(cleaned));
    },
  })
);

const result = await chain.invoke({
  review: "TypeScript is amazing!",
});
// → { summary: "...", sentiment: "positive", score: 9 }
```

**Failure modes**: Model returns markdown-wrapped JSON (hence the cleanup regex); Zod validation fails if model output doesn't match schema.
**Notes**: On OpenRouter, `model.withStructuredOutput(schema)` returns 400 errors when piped from a prompt template. This workaround (prompt → model → StringOutputParser → RunnableLambda with JSON.parse + zod.parse) is reliable.

---

## 5. RAG & Memory

### Text Splitting with RecursiveCharacterTextSplitter

**When to use**: You need to split large documents into overlapping chunks for retrieval.
**When NOT to use**: Your documents are already small enough to fit in context windows.
**Packages**: `@langchain/textsplitters@1.0.1`
**OpenRouter**: Compatible (no LLM needed)

```typescript
import { RecursiveCharacterTextSplitter } from "@langchain/textsplitters";

const splitter = new RecursiveCharacterTextSplitter({
  chunkSize: 200,
  chunkOverlap: 50,
});

// Split text into string chunks
const chunks = await splitter.splitText(longText);

// Split text into Document objects with metadata
const docs = await splitter.createDocuments(
  [longText],
  [{ source: "ai-article", author: "test" }]
);
// docs[0].metadata => { source: "ai-article", author: "test", loc: { lines: { from: 1, to: 1 } } }
```

**Failure modes**: Setting `chunkOverlap` >= `chunkSize` causes infinite loop or error.
**Notes**: Chunks respect `chunkSize` within reasonable tolerance. Overlap is correctly applied. `createDocuments()` auto-adds `loc` metadata with line numbers. Supports language-aware splitting: `"markdown"`, `"js"`, `"python"`, etc.

---

### Language-Aware Text Splitting

**When to use**: You need to split code or markdown respecting language-specific boundaries.
**When NOT to use**: You're splitting plain text without language-specific structure.
**Packages**: `@langchain/textsplitters@1.0.1`
**OpenRouter**: Compatible (no LLM needed)

```typescript
import { RecursiveCharacterTextSplitter } from "@langchain/textsplitters";

const markdownSplitter = RecursiveCharacterTextSplitter.fromLanguage(
  "markdown",
  { chunkSize: 200, chunkOverlap: 20 }
);
const mdChunks = await markdownSplitter.splitText(markdownText);
```

**Failure modes**: Using an unsupported language string throws an error — check `SupportedTextSplitterLanguages`.
**Notes**: Available via `.fromLanguage()` static method. Supported languages include `"markdown"`, `"js"`, `"python"`, and more.

---

### Document Objects

**When to use**: You need to represent text with associated metadata for retrieval pipelines.
**When NOT to use**: You're working with plain strings and don't need metadata.
**Packages**: `@langchain/core@1.1.34`
**OpenRouter**: Compatible (no LLM needed)

```typescript
import { Document } from "@langchain/core/documents";

// Basic document
const doc = new Document({
  pageContent: "LangChain is a framework for building LLM applications.",
  metadata: { source: "docs", page: 1, category: "framework" },
});

// Empty metadata defaults to {}
const doc2 = new Document({ pageContent: "No metadata." });
// doc2.metadata => {}

// Rich metadata (nested objects, arrays all supported)
const richDoc = new Document({
  pageContent: "Vector databases store embeddings.",
  metadata: {
    source: "textbook",
    chapter: 5,
    tags: ["vector", "database", "embeddings"],
    timestamp: new Date().toISOString(),
    nested: { key: "value" },
  },
});
```

**Failure modes**: None — Document is a simple data class.
**Notes**: Two properties: `pageContent` (string) and `metadata` (Record). Metadata can contain any JSON-serializable structure.

---

### RAG Chain with LCEL (No Embeddings)

**When to use**: You need a complete RAG pipeline answering questions from a document set.
**When NOT to use**: You don't have a document corpus or need free-form generation without grounding.
**Packages**: `@langchain/core@1.1.34`, `@langchain/openai@1.3.0`
**OpenRouter**: Compatible

```typescript
import { Document } from "@langchain/core/documents";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import {
  RunnablePassthrough,
  RunnableLambda,
  RunnableSequence,
} from "@langchain/core/runnables";
import { StringOutputParser } from "@langchain/core/output_parsers";

// 1. Knowledge base as Document objects
const knowledgeBase = [
  new Document({
    pageContent: "LCEL stands for LangChain Expression Language...",
    metadata: { source: "docs", topic: "lcel" },
  }),
  // ... more documents
];

// 2. Mock retriever: keyword matching (replace with vector store in production)
function mockRetrieve(query: string): Document[] {
  const queryLower = query.toLowerCase();
  const scored = knowledgeBase.map((doc) => {
    const words = queryLower.split(/\s+/);
    const score = words.filter((w) =>
      doc.pageContent.toLowerCase().includes(w)
    ).length;
    return { doc, score };
  });
  scored.sort((a, b) => b.score - a.score);
  return scored.slice(0, 2).map((s) => s.doc);
}

// 3. Format documents for prompt injection
function formatDocs(docs: Document[]): string {
  return docs.map((doc, i) => `[${i + 1}] ${doc.pageContent}`).join("\n\n");
}

// 4. RAG prompt template
const ragPrompt = ChatPromptTemplate.fromMessages([
  [
    "system",
    `Answer based ONLY on this context. If no answer, say "I don't have that information."

Context:
{context}`,
  ],
  ["human", "{question}"],
]);

// 5. Build the RAG chain
const ragChain = RunnableSequence.from([
  RunnablePassthrough.assign({
    context: new RunnableLambda({
      func: (input: { question: string }) => {
        const docs = mockRetrieve(input.question);
        return formatDocs(docs);
      },
    }),
  }),
  ragPrompt,
  model,
  new StringOutputParser(),
]);

// 6. Use it
const answer = await ragChain.invoke({ question: "What is LCEL?" });
```

**Failure modes**: Retriever returning empty results causes the model to hallucinate; not instructing the model to say "I don't know" leads to fabricated answers.
**Notes**: `RunnablePassthrough.assign()` merges retrieved context alongside the original question. `RunnableSequence.from([...])` chains the steps. For out-of-context questions, model correctly responds "I don't have that information." OpenRouter does NOT support embeddings — use OpenAI directly or a mock retriever.

---

### MemorySaver (Conversation Persistence)

**When to use**: You need multi-turn conversation memory with thread isolation.
**When NOT to use**: Each invocation is independent; or you need production-grade persistent storage.
**Packages**: `@langchain/langgraph@1.2.5`
**OpenRouter**: Compatible

```typescript
import { MemorySaver } from "@langchain/langgraph";
import { createReactAgent } from "@langchain/langgraph/prebuilt";

const checkpointer = new MemorySaver();

const agent = createReactAgent({
  llm: model,
  tools: [],
  checkpointSaver: checkpointer,
});

// Same thread_id = conversation persists
const config = { configurable: { thread_id: "thread-1" } };

const result1 = await agent.invoke(
  { messages: [{ role: "user", content: "My name is Alice." }] },
  config
);

// Second call on same thread remembers Alice
const result2 = await agent.invoke(
  { messages: [{ role: "user", content: "What is my name?" }] },
  config
);
// Answer: "Your name is Alice"

// Different thread_id = isolated conversation
const config2 = { configurable: { thread_id: "different-thread" } };
const result3 = await agent.invoke(
  { messages: [{ role: "user", content: "What is my name?" }] },
  config2
);
// Answer: "I don't know your name"
```

**Failure modes**: `MemorySaver` is in-memory only — all state lost on process restart.
**Notes**: `thread_id` in `configurable` isolates conversations. For production, use `PostgresSaver` or another persistent checkpointer. Works with both `createReactAgent` and `createAgent`.

---

### InMemoryStore for Long-Term Memory

**When to use**: You need key-value storage for cross-conversation data like user preferences or learned facts.
**When NOT to use**: You only need conversation history (use MemorySaver instead).
**Packages**: `@langchain/langgraph@1.2.5`
**OpenRouter**: Compatible (no LLM needed)

```typescript
import { InMemoryStore } from "@langchain/langgraph";

const store = new InMemoryStore();

// Put: store.put(namespace: string[], key: string, value: object)
await store.put(["users", "alice"], "preferences", {
  theme: "dark",
  language: "en",
});

// Get: returns Item with .value property
const item = await store.get(["users", "alice"], "preferences");
console.log(item?.value); // { theme: "dark", language: "en" }

// Search: find items in a namespace
const items = await store.search(["users", "alice"]);
// items = [{ key: "preferences", value: {...} }, { key: "profile", value: {...} }]

// Search with limit
const allUsers = await store.search(["users"], { limit: 10 });

// Update: same put overwrites
await store.put(["users", "alice"], "preferences", { theme: "light" });

// Delete
await store.delete(["users", "bob"], "preferences");
const deleted = await store.get(["users", "bob"], "preferences");
// deleted === null
```

**Failure modes**: `InMemoryStore.get()` returns a mutable reference — if you update the same key later, previously retrieved references will reflect the new value. Capture values immediately.
**Notes**: Namespace is a `string[]` creating a hierarchical key space. `put(namespace, key, value)` — value is any JSON object (do NOT wrap in `{value: ...}`). `get()` returns an `Item` with `.key` and `.value`, or `null`. Useful for cross-conversation memory.

---

### trimMessages Utility

**When to use**: You need to trim conversation history to fit within token limits before sending to the LLM.
**When NOT to use**: Your conversation history always fits within the context window.
**Packages**: `@langchain/core@1.1.34`
**OpenRouter**: Compatible (no LLM needed)

```typescript
import { trimMessages, HumanMessage, AIMessage, SystemMessage } from "@langchain/core/messages";

const messages = [
  new SystemMessage("You are helpful."),
  new HumanMessage("Question 1"),
  new AIMessage("Answer 1"),
  // ... many more messages
  new HumanMessage("Latest question"),
];

// Strategy "last": keep most recent messages within budget
const trimmed = await trimMessages(messages, {
  maxTokens: 150,
  tokenCounter: (msgs) => {
    // Simple char-based approximation (~4 chars per token)
    if (Array.isArray(msgs)) {
      return msgs.reduce(
        (sum, m) => sum + Math.ceil(String(m.content).length / 4),
        0
      );
    }
    return Math.ceil(String(msgs.content).length / 4);
  },
  strategy: "last",
});

// Keep system message + recent messages
const trimmedWithSystem = await trimMessages(messages, {
  maxTokens: 100,
  tokenCounter: /* same as above */,
  strategy: "last",
  includeSystem: true, // Always preserves the system message
});

// Strategy "first": keep oldest messages
const trimmedFirst = await trimMessages(messages, {
  maxTokens: 80,
  tokenCounter: /* same as above */,
  strategy: "first",
});
```

**Failure modes**: `tokenCounter` must handle both single message and array inputs — forgetting the array case causes runtime errors.
**Notes**: `strategy: "last"` keeps most recent messages (most common for chat). `includeSystem: true` always preserves the system message. Works with a custom token counter — no real tokenizer needed.

---

### summarizationMiddleware

**When to use**: You need automatic conversation summarization to compress long histories.
**When NOT to use**: Your conversations are short enough that trimMessages suffices.
**Packages**: `langchain@1.2.35`, `@langchain/langgraph@1.2.5`
**OpenRouter**: Compatible

```typescript
import { MemorySaver } from "@langchain/langgraph";
import { createReactAgent } from "@langchain/langgraph/prebuilt";
import { summarizationMiddleware } from "langchain";

const checkpointer = new MemorySaver();

const agent = createReactAgent({
  llm: model,
  tools: [],
  checkpointSaver: checkpointer,
  messageMiddleware: summarizationMiddleware({
    maxMessages: 6, // Summarize when history exceeds this
    model,          // Model used for summarization
  }),
});

const config = { configurable: { thread_id: "my-thread" } };

// Send many messages; middleware auto-summarizes when history grows
for (const msg of conversations) {
  const result = await agent.invoke(
    { messages: [{ role: "user", content: msg }] },
    config
  );
}
```

**Failure modes**: Requires a `checkpointSaver` — without it, summarization state is lost between calls.
**Notes**: Automatically compresses conversation history when it exceeds `maxMessages`. Uses the provided `model` to generate summaries. After summarization, the agent retains knowledge from earlier turns.

---

## 6. Production

### modelRetryMiddleware

**When to use**: You need automatic retries on transient model failures (network errors, rate limits).
**When NOT to use**: You want to handle errors manually with try/catch.
**Packages**: `langchain@1.2.35`
**OpenRouter**: Compatible

```typescript
import { createAgent, modelRetryMiddleware } from "langchain";

// Default config (uses built-in defaults)
const retryDefault = modelRetryMiddleware();

// Custom config
const retryCustom = modelRetryMiddleware({ maxRetries: 3 });

const agent = createAgent({
  model,
  tools: [myTool],
  middleware: [retryCustom],
  prompt: "You are a helpful assistant.",
});
```

**Failure modes**: Setting `maxRetries` too high on a permanently failing model wastes time and tokens.
**Notes**: Takes an optional config object with `maxRetries`. Works with defaults and custom configuration.

---

### modelFallbackMiddleware

**When to use**: You need automatic failover to backup models when the primary model is unavailable.
**When NOT to use**: You only have one model provider with no alternatives.
**Packages**: `langchain@1.2.35`, `@langchain/openai@1.3.0`
**OpenRouter**: Compatible

```typescript
import { createAgent, modelFallbackMiddleware } from "langchain";
import { ChatOpenAI } from "@langchain/openai";

const primaryModel = new ChatOpenAI({
  model: "anthropic/claude-sonnet-4-6",
  configuration: {
    baseURL: "https://openrouter.ai/api/v1",
    apiKey: process.env.OPENROUTER_API_KEY,
  },
});

const fallbackModel = new ChatOpenAI({
  model: "google/gemini-2.0-flash-001",
  configuration: {
    baseURL: "https://openrouter.ai/api/v1",
    apiKey: process.env.OPENROUTER_API_KEY,
  },
});

// ⚠️ CRITICAL: API is spread args, NOT { models: [...] }
const fallback = modelFallbackMiddleware(fallbackModel);
// Multiple fallbacks: modelFallbackMiddleware(fallback1, fallback2)

const agent = createAgent({
  model: primaryModel,
  tools: [myTool],
  middleware: [fallback],
  prompt: "You are a helpful assistant.",
});
```

**Failure modes**: Using `{ models: [fallbackModel] }` instead of spread args — this is a common mistake that silently fails.
**Notes**: **CRITICAL**: API is `modelFallbackMiddleware(...fallbackModels)` with spread args, NOT an options object. Primary model triggers fallback when it has a bad API key or is unavailable.

---

### toolRetryMiddleware

**When to use**: You need automatic retries when tool execution fails transiently.
**When NOT to use**: Tool failures are deterministic and retrying won't help.
**Packages**: `langchain@1.2.35`
**OpenRouter**: Compatible

```typescript
import { createAgent, toolRetryMiddleware } from "langchain";

const retry = toolRetryMiddleware({ maxRetries: 2 });
// Or with defaults:
const retryDefault = toolRetryMiddleware();

const agent = createAgent({
  model,
  tools: [myTool],
  middleware: [retry],
  prompt: "You are a helpful assistant.",
});
```

**Failure modes**: Retrying a tool that modifies external state (e.g., database writes) can cause duplicate operations.
**Notes**: Optional config with `maxRetries`. Works with defaults and custom config.

---

### toolCallLimitMiddleware

**When to use**: You need to cap the number of tool calls to prevent runaway agents.
**When NOT to use**: Your agent is well-behaved and doesn't loop excessively.
**Packages**: `langchain@1.2.35`
**OpenRouter**: Compatible

```typescript
import { createAgent, toolCallLimitMiddleware } from "langchain";

// ⚠️ CRITICAL: Requires at least threadLimit OR runLimit (not maxToolCalls)
const limit = toolCallLimitMiddleware({ runLimit: 5 });
// Or thread-level limit:
const threadLimit = toolCallLimitMiddleware({ threadLimit: 10 });
// Or both:
const bothLimits = toolCallLimitMiddleware({ threadLimit: 10, runLimit: 5 });

const agent = createAgent({
  model,
  tools: [myTool],
  middleware: [limit],
  prompt: "You are a research assistant.",
});
```

**Failure modes**: Using `{ maxToolCalls: N }` — this is incorrect. The correct keys are `threadLimit` and `runLimit`.
**Notes**: At least one of `threadLimit` or `runLimit` is required. `runLimit` caps per-invocation; `threadLimit` caps across the entire thread.

---

### modelCallLimitMiddleware

**When to use**: You need to limit the number of LLM invocations to control costs or prevent infinite loops.
**When NOT to use**: You trust your graph/agent to terminate naturally.
**Packages**: `langchain@1.2.35`
**OpenRouter**: Compatible

```typescript
import { createAgent, modelCallLimitMiddleware } from "langchain";

// With thread limit
const limit = modelCallLimitMiddleware({ threadLimit: 10 });

// With exit behavior on limit exceeded
const strictLimit = modelCallLimitMiddleware({
  threadLimit: 3,
  exitBehavior: "error", // "error" throws, other behaviors may end gracefully
});

// Defaults (no limit)
const defaults = modelCallLimitMiddleware();

const agent = createAgent({
  model,
  tools: [myTool],
  middleware: [limit],
  prompt: "You are a helpful assistant.",
});
```

**Failure modes**: Setting `exitBehavior: "error"` without a try/catch causes unhandled exceptions when limit is hit.
**Notes**: All options are optional. `threadLimit` caps LLM calls across the entire thread. `exitBehavior: "error"` throws when limit exceeded.

---

### humanInTheLoopMiddleware

**When to use**: You need human approval before executing certain tool calls.
**When NOT to use**: All tools are safe to execute without human review.
**Packages**: `langchain@1.2.35`
**OpenRouter**: Compatible

```typescript
import { createAgent, humanInTheLoopMiddleware } from "langchain";

// No args — all tools require approval
const hitl = humanInTheLoopMiddleware();

// Selective approval — only specified tools require approval
const selectiveHitl = humanInTheLoopMiddleware({
  toolsRequiringApproval: ["dangerous_tool", "delete_records"],
});

const agent = createAgent({
  model,
  tools: [safeTool, dangerousTool],
  middleware: [selectiveHitl],
  prompt: "You are a helpful assistant.",
});

// NOTE: Full HITL requires running the agent graph with a checkpointer
// and handling interrupts. See interrupt() pattern below.
```

**Failure modes**: Without a checkpointer, the interrupt cannot be resumed — the agent just stops.
**Notes**: Full HITL requires LangGraph interrupts and a checkpointer. `toolsRequiringApproval` selectively gates only specified tools.

---

### interrupt() for Human-in-the-Loop

**When to use**: You need to pause graph execution, get human input, and resume.
**When NOT to use**: Your workflow is fully automated with no human checkpoints.
**Packages**: `@langchain/langgraph@1.2.5`
**OpenRouter**: Compatible

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
  // Pauses execution here — returns value to caller
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

// ⚠️ CRITICAL: Must use checkpointer for interrupt to work
const checkpointer = new MemorySaver();
const app = graph.compile({ checkpointer });

const config = { configurable: { thread_id: "my-thread" } };

// Step 1: Run until interrupt
const result1 = await app.invoke({ input: "test data" }, config);
// result1.__interrupt__ contains the interrupt payload

// Step 2: Check state
const state = await app.getState(config);
console.log(state.next); // ["approval"] — waiting at this node

// Step 3: Resume with Command
const result2 = await app.invoke(new Command({ resume: "yes" }), config);
// result2 = { input: "test data", approved: true, result: "Processed: test data" }
```

**Failure modes**: Forgetting the checkpointer — interrupt has nowhere to save state. Using `{ resume: "value" }` instead of `new Command({ resume: "value" })`.
**Notes**: `interrupt(payload)` pauses graph execution and returns payload to caller. Resume with `new Command({ resume: value })`. Must use a checkpointer. `app.getState(config)` shows which node is waiting.

---

### Combined Middleware Stack

**When to use**: You need a production-grade agent with retries, fallbacks, and limits.
**When NOT to use**: You're prototyping and don't need resilience yet.
**Packages**: `langchain@1.2.35`
**OpenRouter**: Compatible

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
    modelRetryMiddleware({ maxRetries: 3 }),
    modelFallbackMiddleware(fallbackModel1, fallbackModel2),
    modelCallLimitMiddleware({ threadLimit: 20 }),
    toolCallLimitMiddleware({ runLimit: 10 }),
    toolRetryMiddleware({ maxRetries: 2 }),
  ],
  prompt: "You are a production assistant.",
});
```

**Failure modes**: Middleware order may matter — retries should generally come before fallbacks.
**Notes**: All middleware composes cleanly in the `middleware` array. Stack retries + fallbacks + limits for maximum resilience.

---

## 7. OpenRouter

### ChatOpenRouter (Native Package)

**When to use**: You want simpler OpenRouter integration without `configuration.baseURL` overrides.
**When NOT to use**: You're already using `ChatOpenAI` with OpenRouter config and don't want another dependency.
**Packages**: `@langchain/openrouter`
**OpenRouter**: Compatible (native)

```typescript
import { ChatOpenRouter } from "@langchain/openrouter";

const model = new ChatOpenRouter({
  model: "anthropic/claude-sonnet-4-6",
  apiKey: process.env.OPENROUTER_API_KEY,
});

const response = await model.invoke("Hello!");
console.log(response.content);
```

**Failure modes**: Requires `npm install @langchain/openrouter --legacy-peer-deps` due to peer dependency conflicts.
**Notes**: Simpler API than using `ChatOpenAI` with `configuration.baseURL` override. Also exports: `OPENROUTER_MODEL_PROFILES`, `OpenRouterAuthError`, `OpenRouterError`, `OpenRouterRateLimitError`.

---

### ChatOpenAI with OpenRouter (Provider Routing)

**When to use**: You want to use OpenRouter without installing the dedicated package.
**When NOT to use**: You have `@langchain/openrouter` installed and prefer the simpler API.
**Packages**: `@langchain/openai@1.3.0`
**OpenRouter**: Compatible

```typescript
import { ChatOpenAI } from "@langchain/openai";

const model = new ChatOpenAI({
  model: "anthropic/claude-sonnet-4-6",
  configuration: {
    baseURL: "https://openrouter.ai/api/v1",
    apiKey: process.env.OPENROUTER_API_KEY!,
  },
});

const response = await model.invoke("Hello!");
```

**Failure modes**: Omitting `configuration.baseURL` sends requests to OpenAI directly instead of OpenRouter.
**Notes**: This is the standard pattern used throughout this catalog. Works with all LangChain features: tools, structured output (direct invoke), streaming, agents, graphs.

---

### Structured Output Workaround for OpenRouter

**When to use**: You need structured (typed) output in an LCEL chain on OpenRouter.
**When NOT to use**: Direct `model.withStructuredOutput(schema).invoke(string)` works for your use case (no pipe chain).
**Packages**: `@langchain/core@1.1.34`, `zod@4.3.6`
**OpenRouter**: Workaround needed

```typescript
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";
import { RunnableLambda } from "@langchain/core/runnables";
import { z } from "zod";

const MySchema = z.object({
  summary: z.string(),
  sentiment: z.enum(["positive", "negative", "neutral"]),
  score: z.number().min(1).max(10),
});

const structuredChain = ChatPromptTemplate.fromMessages([
  ["system", "Return ONLY valid JSON with fields: summary (string), sentiment (positive/negative/neutral), score (1-10). No markdown."],
  ["human", "{input}"],
]).pipe(model).pipe(new StringOutputParser()).pipe(
  new RunnableLambda({
    func: (text: string) => {
      const cleaned = text.replace(/```json?\n?/g, "").replace(/```/g, "").trim();
      return MySchema.parse(JSON.parse(cleaned));
    },
  })
);

const result = await structuredChain.invoke({ input: "Analyze this review..." });
// Typed result matching MySchema
```

**Failure modes**: Model may occasionally wrap JSON in markdown code fences (the regex handles this); malformed JSON causes parse errors.
**Notes**: `withStructuredOutput()` via tool-calling returns 400 errors on OpenRouter when piped from prompts. This prompt → parse workaround is the reliable alternative. Includes Zod validation for type safety.

---

## Import Quick Reference

```typescript
// Core Model
import { ChatOpenAI } from "@langchain/openai";
import { ChatOpenRouter } from "@langchain/openrouter";
import { initChatModel } from "langchain/chat_models/universal";

// Messages
import { HumanMessage, AIMessage, SystemMessage } from "@langchain/core/messages";
import { trimMessages } from "@langchain/core/messages";

// Tools
import { tool } from "@langchain/core/tools";
import { z } from "zod";

// Prompts & Parsers
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";

// LCEL Runnables
import {
  RunnableParallel,
  RunnableLambda,
  RunnablePassthrough,
  RunnableBranch,
  RunnableSequence,
} from "@langchain/core/runnables";

// Documents
import { Document } from "@langchain/core/documents";
import { RecursiveCharacterTextSplitter } from "@langchain/textsplitters";

// Agents
import { createAgent, ToolStrategy } from "langchain";
import { createMiddleware, dynamicSystemPromptMiddleware } from "langchain";
import { summarizationMiddleware } from "langchain";

// LangGraph
import {
  StateGraph, MessagesAnnotation, Annotation,
  START, END, MemorySaver, InMemoryStore, Command,
  entrypoint, task, interrupt,
} from "@langchain/langgraph";
import { ToolNode, toolsCondition, createReactAgent } from "@langchain/langgraph/prebuilt";

// Production Middleware
import {
  modelRetryMiddleware,
  modelFallbackMiddleware,
  toolRetryMiddleware,
  toolCallLimitMiddleware,
  modelCallLimitMiddleware,
  humanInTheLoopMiddleware,
} from "langchain";
```
