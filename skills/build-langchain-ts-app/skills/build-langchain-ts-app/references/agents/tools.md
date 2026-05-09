# Tools Reference

Complete reference for designing and implementing tools for LangChain.js agents. All code verified against langchain@1.x, @langchain/core@1.x, @langchain/langgraph@1.x. TypeScript only.

---

## Type Hierarchy

```
Runnable
  └── StructuredTool          (base class — extend for class-based tools)
        ├── DynamicStructuredTool  (produced by tool() when schema is z.object())
        └── DynamicTool            (produced by tool() when schema is z.string())
```

Type guard utilities from `@langchain/core/tools`:

- `isLangChainTool(t)` — StructuredTool, RunnableTool, or StructuredToolParams
- `isRunnableToolLike(t)` — RunnableToolLike
- `isStructuredTool(t)` — StructuredToolInterface
- `isStructuredToolParams(t)` — has required StructuredToolParams props

Union aliases:
- `ClientTool` = `StructuredToolInterface | DynamicTool | RunnableToolLike`
- `ServerTool` = `Record<string, unknown>` (provider-native, e.g. OpenAI `webSearch`)

> There is **no `@tool` decorator in LangChain.js**. That pattern exists only in LangChain Python. Use the `tool()` function in TypeScript/JavaScript.

---

## `tool()` Factory Function

The canonical way to create tools in LangChain.js v1.

### Imports

```ts
import { tool } from "langchain";            // top-level entry point (v1)
import { tool } from "@langchain/core/tools"; // explicit package
import * as z from "zod";
```

### Minimal example

```ts
const getWeather = tool(
  ({ city }) => `It's always sunny in ${city}!`,
  {
    name: "get_weather",
    description: "Get the current weather for a given city.",
    schema: z.object({
      city: z.string().describe("The city to get weather for"),
    }),
  }
);
```

### Multi-parameter async tool

```ts
const searchDatabase = tool(
  async ({ query, limit }) => {
    const rows = await db.search(query, limit);
    return JSON.stringify(rows);
  },
  {
    name: "search_database",
    description: "Search the customer database for records matching the query.",
    schema: z.object({
      query: z.string().describe("Search terms to look for"),
      limit: z.number().int().min(1).max(100).describe("Maximum number of results"),
    }),
  }
);
```

### `tool()` configuration fields

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | `snake_case` identifier, unique per agent |
| `description` | `string` | Yes | What + when; drives model tool-selection |
| `schema` | `ZodObject \| ZodString` | Yes | Input validation; Zod required (not raw JSON Schema) |
| `responseFormat` | `"content"` \| `"content_and_artifact"` | No | Tuple return support |
| `returnDirect` | `boolean` | No | Agent stops after this tool call |
| `metadata` | `Record<string, unknown>` | No | Arbitrary metadata (appears in LangSmith traces) |
| `tags` | `string[]` | No | Tags for callbacks/tracing |
| `defaultConfig` | `ToolRunnableConfig` | No | Default runnable config |

### When `tool()` creates which concrete type

- `z.string()` schema → `DynamicTool` (single string input)
- `z.object({...})` schema → `DynamicStructuredTool` (multiple structured inputs)

---

## `ToolRuntime` — Second Argument to Every Tool

Every tool function receives an optional second argument of type `ToolRuntime`:

```ts
import { type ToolRuntime } from "langchain";

const getUserName = tool(
  (_, config: ToolRuntime) => config.context.user_name,
  {
    name: "get_user_name",
    description: "Get the current user's name from session context.",
    schema: z.object({}),
  }
);
```

| Field | Type | Description |
|---|---|---|
| `context` | `Record<string, any>` | Immutable per-invocation data (user ID, session info) |
| `store` | `BaseStore \| undefined` | Persistent key-value store (long-term memory) |
| `writer` | `((chunk: any) => void) \| undefined` | Stream writer for incremental output |
| `toolCallId` | `string` | ID of the current tool call — required when returning `Command` with `ToolMessage` |
| `config` | `RunnableConfig` | Full runnable config |

### Store access (long-term memory)

```ts
import { InMemoryStore } from "@langchain/langgraph";

const saveUserInfo = tool(
  async ({ user_id, name, email }, config: ToolRuntime) => {
    await config.store?.put(["users"], user_id, { name, email });
    return "Saved.";
  },
  {
    name: "save_user_info",
    description: "Persist user profile data.",
    schema: z.object({
      user_id: z.string().describe("User's unique ID"),
      name: z.string().describe("User's full name"),
      email: z.string().email().describe("User's email address"),
    }),
  }
);
```

### Tool returning `Command` (state mutation in LangGraph)

```ts
import { tool, ToolMessage, type ToolRuntime } from "langchain";
import { Command } from "@langchain/langgraph";

const setLanguage = tool(
  async ({ language }, config: ToolRuntime) =>
    new Command({
      update: {
        preferredLanguage: language,
        messages: [
          new ToolMessage({
            content: `Language set to ${language}.`,
            tool_call_id: config.toolCallId,
          }),
        ],
      },
    }),
  {
    name: "set_language",
    description: "Set the preferred response language for this session.",
    schema: z.object({ language: z.string().describe("BCP-47 language code, e.g. 'fr'") }),
  }
);
```

---

## `StructuredTool` — Class-Based Approach

Use when you need shared state, complex initialization, or class inheritance.

```ts
import { StructuredTool } from "@langchain/core/tools";
import { z } from "zod";

class DatabaseSearchTool extends StructuredTool {
  name = "search_database";
  description = "Search the customer database. Use for order lookups, customer records.";
  schema = z.object({
    query: z.string().describe("Search terms"),
    table: z.enum(["orders", "customers"]).describe("Table to search"),
  });

  constructor(private db: DatabaseClient) {
    super();
  }

  protected async _call({ query, table }: { query: string; table: string }): Promise<string> {
    const results = await this.db.search(table, query);
    return JSON.stringify(results);
  }
}

const tool = new DatabaseSearchTool(dbClient);
```

Key `StructuredTool` methods inherited by all tools:

| Method | Description |
|---|---|
| `invoke(input, config?)` | Public entry point — validates input, runs `_call` |
| `withRetry(opts)` | Returns `RunnableRetry` with retry logic |
| `withFallbacks(fallbacks)` | Returns `RunnableWithFallbacks` |
| `streamEvents()` | Emits `on_tool_start` / `on_tool_end` events |
| `batch(inputs)` | Run multiple inputs concurrently |
| `pipe(next)` | Chain with another Runnable |

---

## Zod Schema Patterns

### Always use `.describe()` on every field

```ts
schema: z.object({
  userId: z.string().describe("Unique identifier, e.g. 'usr_abc123'"),
  status: z.enum(["pending", "shipped", "delivered"]).describe("Order status to filter by"),
  limit: z.number().int().min(1).max(100).default(10)
    .describe("Maximum number of results (default: 10)"),
})
```

Field descriptions are included in the JSON Schema sent to the model. Missing descriptions degrade tool-call accuracy.

### Safe schema patterns

```ts
// Optional with default
z.number().default(10).describe("Page size")
z.string().optional().describe("Optional filter")

// Enum — best for constrained choices
z.enum(["asc", "desc"]).describe("Sort direction")

// Array
z.array(z.string()).describe("List of tag filters")

// Validation constraints
z.string().uuid().describe("UUID of the resource")
z.string().url().describe("Full HTTPS URL")
z.number().min(1).max(5).describe("Rating from 1 to 5")
```

### Patterns to avoid

```ts
// ❌ Deeply nested objects (3+ levels) — small models often fail
z.object({ a: z.object({ b: z.object({ c: z.string() }) }) })

// ❌ Union types — model may pick wrong branch
z.union([z.string(), z.number()])

// ❌ Record/map types — unpredictable key generation
z.record(z.string(), z.number())

// ❌ Missing .describe() — model has no guidance
z.object({ q: z.string() })   // what is "q"?
```

### Known issue: `$ref` in complex nested schemas

`bindTools()` calls `zod-to-json-schema` without `$refStrategy: "none"`, producing `$ref` pointers that OpenAI and Anthropic reject.

**Workaround** — pass a raw function definition with explicit `zodToJsonSchema`:

```ts
import { zodToJsonSchema } from "zod-to-json-schema";
import { ChatOpenAI } from "@langchain/openai";

const complexSchema = z.object({
  children: z.array(z.object({
    title: z.string(),
    content: z.string(),
  })).describe("Child pages"),
});

const llm = new ChatOpenAI({ model: "gpt-4o" });
const llmWithTools = llm.bindTools([
  {
    type: "function",
    function: {
      name: "create_page",
      description: "Create a new page with children",
      parameters: zodToJsonSchema(complexSchema, { $refStrategy: "none" }),
    },
  },
]);
```

### Known issue: `DynamicStructuredTool` discards non-Zod schemas

The constructor replaces non-Zod schemas with `z.object({}).passthrough()`, causing empty payloads. Always use Zod schemas.

---

## Tool Description Engineering

The description is the primary signal the model uses for tool selection. Poor descriptions cause wrong tool selection, missed calls, and agent loops.

### 7 rules

1. **Action-oriented** — start with an imperative verb: "Search for...", "Get the...", "Calculate..."
2. **Trigger conditions** — state WHEN to use the tool, not just what it does
3. **Disambiguation** — if you have similar tools, explicitly distinguish them
4. **Input hints** — mention key parameters that matter to the caller
5. **Output preview** — note what the tool returns
6. **Length** — opening clause under ~150 characters; add detail in subsequent sentences
7. **Exclusions** — use "Do NOT use for X — use Y instead" to prevent wrong-tool calls

### Examples

```ts
// Rule 1+2+5 combined
description: "Get current weather conditions for any city. Use when the user asks about weather, temperature, or forecasts. Returns temperature in Celsius, conditions, humidity, and wind speed."

// Rule 3 — disambiguation
description: "Search company knowledge base for internal documentation and policies. Use instead of web_search when the question is about company-internal information."

// Rule 7 — exclusion
description: "Calculate mathematical expressions. Use for arithmetic, algebra, and unit conversions. Do NOT use for statistical analysis — use the analytics_query tool instead."

// Rule 4+5 — parameter and output hints
description: "Look up customer order by ID or email. Input: orderId (e.g. 'ORD-12345') or customerEmail. Returns order status, items, and timestamps."
```

### Name conventions

- Use `snake_case` only: `search_orders`, `get_user_info`, `create_ticket`
- Only alphanumeric, underscores, hyphens — no spaces or special chars (many providers reject them)
- Use verb-noun patterns; avoid generic names like `tool1`, `helper`

---

## Error Handling — 6 Strategies

### Strategy 1: Catch inside the tool (recommended)

Return a descriptive error string so the model can understand and retry:

```ts
const safeDbTool = tool(
  async ({ query }) => {
    try {
      return await db.query(query);
    } catch (e) {
      const errorId = crypto.randomUUID();
      console.error(`[${errorId}]`, e);
      // Return UUID — model surfaces it to user; you can find it in logs
      return `Database error. Reference ID: ${errorId}. Please try a different query.`;
    }
  },
  { name: "query_db", description: "Query the database.", schema: z.object({ query: z.string() }) }
);
```

### Strategy 2: `ToolNode.handleToolErrors`

```ts
import { ToolNode } from "@langchain/langgraph/prebuilt";

// false (default) — errors propagate
const node1 = new ToolNode(tools);

// true — catch all errors, convert to ToolMessage with status: "error"
const node2 = new ToolNode(tools, { handleToolErrors: true });

// string — custom error message returned to model
const node3 = new ToolNode(tools, {
  handleToolErrors: "Tool encountered an error. Please try a different approach.",
});
```

Note: `createAgent()` does not expose `handleToolErrors` directly. Pass a custom `ToolNode` to `createAgent({ tools: myToolNode })` to configure it.

### Strategy 3: `toolRetryMiddleware`

```ts
import { createAgent, toolRetryMiddleware } from "langchain";

const agent = createAgent({
  model: "openai:gpt-4o",
  tools: [searchTool],
  middleware: [
    toolRetryMiddleware({
      maxRetries: 3,
      backoffFactor: 1.5,
      initialDelayMs: 200,
      retryOn: [TimeoutError, NetworkError],          // specific error types
      tools: ["search_database"],                     // only retry these tools
      onFailure: (err) => `Temporarily unavailable: ${err.message}`,
    }),
  ],
});

// Predicate-based retry
const retry2 = toolRetryMiddleware({
  maxRetries: 3,
  retryOn: (err) => err.name === "HTTPError" && (err as any).statusCode >= 500,
});

// Re-raise on final failure instead of swallowing
const retry3 = toolRetryMiddleware({ maxRetries: 2, onFailure: "raise" });
```

### Strategy 4: `withRetry()` and `withFallbacks()` on individual tools

Every tool inherits these from `Runnable`:

```ts
const retriableTool = myTool.withRetry({ stopAfterAttempt: 3 });
const toolWithFallback = primaryTool.withFallbacks([backupTool]);
```

### Strategy 5: `toolStrategy.handleError` for structured output

```ts
import { createAgent, toolStrategy, ToolInputParsingException } from "langchain";

const agent = createAgent({
  model: "gpt-4o",
  tools: [],
  responseFormat: toolStrategy(MySchema, {
    handleError: (error) => {
      if (error instanceof ToolInputParsingException) {
        return "Invalid format. Please provide a rating 1-5 and a comment.";
      }
      throw error;  // re-throw non-validation errors
    },
  }),
});
```

### Strategy 6: `returnDirect` and errors

```ts
const directTool = tool(
  ({ answer }) => answer,
  {
    name: "final_answer",
    description: "Return the final answer to the user.",
    schema: z.object({ answer: z.string() }),
    returnDirect: true,  // agent stops immediately after this call
  }
);
```

Warning: if a `returnDirect: true` tool throws, the agent exits with an error. Always wrap in try/catch or use `handleToolErrors` in `ToolNode`.

### Error types reference

| Error class | Package | Trigger |
|---|---|---|
| `ToolInputParsingException` | `@langchain/core/tools` | Zod schema validation fails on tool input |
| Standard `Error` | native | Any thrown error from tool logic |

---

## Model-Tool Binding

### `bindTools()`

```ts
import { initChatModel } from "langchain";

const model = await initChatModel("gpt-4o");
const modelWithTools = model.bindTools([weatherTool, searchTool]);

// With options
const modelWithOptions = model.bindTools([weatherTool], {
  toolChoice: "any",            // "auto" | "any" | "required" | "<tool_name>"
  parallel_tool_calls: true,   // default true for OpenAI/Anthropic
});

// Force a specific tool
const forced = model.bindTools([weatherTool], { toolChoice: "get_weather" });
```

`toolChoice` values:
- `"auto"` — model decides (default)
- `"any"` — model must call at least one tool
- `"required"` — model must call a tool
- `"<tool_name>"` — model must call that specific tool

Do not combine `bindTools()` and `withStructuredOutput()` on the same model instance — they conflict. Use `createAgent` with `responseFormat` instead.

### Manual tool loop with `Promise.all`

```ts
import { HumanMessage } from "langchain";

const messages = [new HumanMessage("What's the weather in Boston and NYC?")];

// Step 1: model generates tool calls
const aiMsg = await modelWithTools.invoke(messages);
messages.push(aiMsg);

// Step 2: execute all tool calls in parallel
const toolResults = await Promise.all(
  (aiMsg.tool_calls ?? []).map((toolCall) => weatherTool.invoke(toolCall))
);
messages.push(...toolResults);

// Step 3: get final answer
const finalResponse = await modelWithTools.invoke(messages);
console.log(finalResponse.text);
```

### `ToolCall` and `ToolMessage` shapes

```ts
// ToolCall (on AIMessage.tool_calls[])
interface ToolCall {
  id: string;         // must match ToolMessage.tool_call_id
  name: string;       // tool name
  args: object;       // validated arguments
  type: "tool_call";
}

// ToolMessage properties
import { ToolMessage } from "langchain";

const msg = new ToolMessage({
  content: "The weather in SF is 65°F and foggy.",  // sent to model
  tool_call_id: "call_abc123",                        // must match ToolCall.id
  name: "get_weather",
  status: "success",   // "success" | "error"
  artifact: rawBytes,  // NOT sent to model (use with responseFormat: "content_and_artifact")
});
```

### `responseFormat: "content_and_artifact"`

Return a `[content, artifact]` tuple when you need to attach raw data the model should not see:

```ts
const imageTool = tool(
  async ({ prompt }) => {
    const imageBytes = await generateImage(prompt);
    return ["Image generated successfully.", imageBytes];  // [string, binary]
  },
  {
    name: "generate_image",
    description: "Generate an image from a text prompt.",
    schema: z.object({ prompt: z.string().describe("Image description") }),
    responseFormat: "content_and_artifact",
  }
);
// ToolMessage.content = "Image generated successfully." (sent to model)
// ToolMessage.artifact = imageBytes (not sent to model, available in state)
```

### Streaming tool calls

```ts
import { AIMessageChunk } from "langchain";

let finalChunk: AIMessageChunk | undefined;
for await (const chunk of await modelWithTools.stream("Get weather and time for Tokyo")) {
  finalChunk = finalChunk ? finalChunk.concat(chunk) : chunk;
  if (chunk.tool_call_chunks) {
    for (const tc of chunk.tool_call_chunks) {
      process.stdout.write(tc.args ?? "");  // stream args as they arrive
    }
  }
}
// finalChunk.tool_calls now has complete tool_calls[]
```

---

## `ToolNode` — LangGraph Prebuilt Node

`ToolNode` executes tool calls in parallel from an `AIMessage` and returns `ToolMessage` results.

### Basic usage

```ts
import { ToolNode, toolsCondition } from "@langchain/langgraph/prebuilt";
import { StateGraph, MessagesAnnotation } from "@langchain/langgraph";
import { ChatAnthropic } from "@langchain/anthropic";

const modelWithTools = new ChatAnthropic({ model: "claude-3-haiku-20240307" })
  .bindTools([getWeather]);

const toolNode = new ToolNode([getWeather]);

const graph = new StateGraph(MessagesAnnotation)
  .addNode("agent", async (state) => ({
    messages: await modelWithTools.invoke(state.messages),
  }))
  .addNode("tools", toolNode)
  .addEdge("__start__", "agent")
  .addConditionalEdges("agent", toolsCondition)  // routes to "tools" or "__end__"
  .addEdge("tools", "agent")
  .compile();

for await (const { messages } of await graph.stream(
  { messages: [{ role: "user", content: "Weather in SF?" }] },
  { streamMode: "values" }
)) {
  console.log(messages.at(-1)?.content);
}
```

### `ToolNode` constructor options

```ts
new ToolNode(tools, options?)
```

| Option | Type | Default | Description |
|---|---|---|---|
| `tools` | `StructuredToolInterface[] \| RunnableToolLike[]` | required | Tools to execute |
| `handleToolErrors` | `boolean \| string` | `false` | Error handling: `true` = catch all; `string` = custom message |

### `ToolNode` vs `createAgent()`

| Aspect | `ToolNode` | `createAgent()` |
|---|---|---|
| Level | Low-level graph node | High-level abstraction |
| Control | Full graph composition | Limited to `createAgent` options |
| `handleToolErrors` | Direct option | Pass custom `ToolNode` instance |
| Parallel tool calls | Automatic | Automatic |
| Use case | Custom multi-agent graphs | Standard agent workflows |

---

## Human-in-the-Loop Tool Approval

### `interrupt_on` configuration

```ts
import { createAgent, tool } from "langchain";
import { MemorySaver, Command } from "@langchain/langgraph";

const agent = createAgent({
  model: "claude-sonnet-4-6",
  tools: [deleteFileTool, sendEmailTool],
  interrupt_on: {
    delete_file: true,                                          // approve / edit / reject
    send_email: { allowedDecisions: ["approve", "reject"] },   // no edit option
  },
  checkpointer: new MemorySaver(),  // REQUIRED for interrupt/resume
});
```

### Handling the interrupt

```ts
import { v4 as uuidv4 } from "uuid";

const config = { configurable: { thread_id: uuidv4() } };  // reuse same ID to resume

let result = await agent.invoke(
  { messages: [{ role: "user", content: "Delete temp.txt" }] },
  config
);

if (result.__interrupt__) {
  const { actionRequests } = result.__interrupt__[0].value;
  // actionRequests: [{ name: "delete_file", args: { path: "temp.txt" } }]

  // Resume with a decision
  result = await agent.invoke(
    new Command({ resume: { decisions: [{ type: "approve" }] } }),
    config
  );
}
```

Decision types:

| Decision | Effect |
|---|---|
| `approve` | Execute tool with original arguments |
| `edit` | Execute with modified args: `{ type: "edit", editedAction: { name, args } }` |
| `reject` | Skip the tool call entirely |

### Custom interrupt inside a tool

```ts
import { interrupt } from "@langchain/langgraph";

const dangerousTool = tool(
  async ({ command }) => {
    const decision = interrupt({
      message: `Confirm execution of: ${command}`,
      type: "approval_request",
    }) as { approved: boolean };

    return decision.approved
      ? `Executed: ${command}`
      : `Rejected by user.`;
  },
  {
    name: "run_command",
    description: "Run a system command after human approval.",
    schema: z.object({ command: z.string().describe("Shell command to run") }),
  }
);
```

Always use a checkpointer when using `interrupt()`. Reuse the same `thread_id` to resume.

---

## Built-in Tools Catalog

### Search

```ts
// Tavily — recommended for production agents
import { TavilySearch } from "@langchain/tavily";
// npm install @langchain/tavily; requires TAVILY_API_KEY

const tavily = new TavilySearch({
  maxResults: 5,
  searchDepth: "basic",      // "basic" | "advanced"
  timeRange: "week",         // "day" | "week" | "month"
  includeAnswer: true,
  includeDomains: [],
  excludeDomains: [],
});

// DuckDuckGo — free, no API key
import { DuckDuckGoSearch } from "@langchain/community/tools/duckduckgo_search";
// npm install @langchain/community duck-duck-scrape
const ddg = new DuckDuckGoSearch({ maxResults: 3 });

// Wikipedia
import { WikipediaQueryRun } from "@langchain/community/tools/wikipedia_query_run";
const wiki = new WikipediaQueryRun({ topKResults: 2, maxDocContentLength: 4000 });

// Calculator
import { Calculator } from "@langchain/community/tools/calculator";
const calc = new Calculator();
await calc.invoke("2 + 2 * 10"); // "22"
```

### Integration catalog

| Tool | Package | Notes |
|---|---|---|
| TavilySearch | `@langchain/tavily` | AI-optimized; also TavilyCrawl, TavilyExtract, TavilyMap |
| DuckDuckGoSearch | `@langchain/community` | Free, no API key |
| ExaSearchResults | `@langchain/community` | Neural/semantic search |
| SerpApi | `@langchain/community` | Google SERP scraping |
| Wikipedia | `@langchain/community` | Article retrieval |
| WolframAlpha | `@langchain/community` | Computational knowledge |
| Calculator | `@langchain/community` | Math expression evaluation |
| Gmail Tool | `@langchain/community` | Gmail read/write |
| Google Calendar | `@langchain/community` | Calendar operations |
| Composio | `@langchain/community` | 500+ integrations with OAuth |
| Stagehand | `@langchain/community` | AI web automation |
| SQL Toolkit | `@langchain/classic` | 4 SQL tools (see SQL section) |
| FalkorDB | `@langchain/community` | Graph database |
| GOAT | `@langchain/community` | On-chain/Web3 tools |

### OpenAI provider-native tools (run on OpenAI infrastructure)

```ts
import { ChatOpenAI } from "@langchain/openai";

const model = new ChatOpenAI({ model: "gpt-4o" });
const modelWithNativeTools = model.bindTools([
  { type: "web_search_preview" },       // web search
  { type: "code_interpreter" },         // Python sandbox execution
  { type: "file_search", vector_store_ids: ["vs_xxx"] },
]);
```

| Tool | Purpose |
|---|---|
| `webSearch` | Web search with domain filters |
| `mcp` | Remote MCP server via OpenAI |
| `codeInterpreter` | Python sandbox (1 GB–64 GB) |
| `fileSearch` | Semantic search over uploaded files |
| `imageGeneration` | Generate/edit images |
| `computerUse` | Control simulated computer |
| `localShell` | Run local shell commands |

---

## MCP Tool Integration

Connect to Model Context Protocol servers and use their tools as LangChain tools.

```bash
npm install @langchain/mcp-adapters
```

### `MultiServerMCPClient`

```ts
import { MultiServerMCPClient } from "@langchain/mcp-adapters";
import { createAgent } from "langchain";

const client = new MultiServerMCPClient({
  math: {
    transport: "stdio",      // local subprocess
    command: "node",
    args: ["/path/to/math_server.js"],
  },
  weather: {
    transport: "http",       // remote HTTP (streamable-http)
    url: "http://localhost:8000/mcp",
  },
  data: {
    transport: "sse",        // Server-Sent Events
    url: "http://localhost:9000/mcp",
    headers: { Authorization: "Bearer token" },
  },
});

const mcpTools = await client.getTools();  // returns LangChain-compatible tools

const agent = createAgent({
  model: "claude-sonnet-4-6",
  tools: mcpTools,
});
```

Transport options:

| Transport | Config key | Use case |
|---|---|---|
| `stdio` | `transport: "stdio"` | Local subprocess |
| `http` | `transport: "http"` | Remote HTTP server (streamable-http) |
| `sse` | `transport: "sse"` | Remote server via Server-Sent Events |

`MultiServerMCPClient` is stateless by default — each `getTools()` call creates a fresh `ClientSession`. `stdio` transport is stateful on the server side (subprocess persists for connection lifetime).

### Building an MCP server (stdio)

```ts
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";

const server = new Server(
  { name: "math-server", version: "0.1.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [{
    name: "add",
    description: "Add two numbers",
    inputSchema: {
      type: "object",
      properties: {
        a: { type: "number", description: "First number" },
        b: { type: "number", description: "Second number" },
      },
      required: ["a", "b"],
    },
  }],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "add") {
    const { a, b } = request.params.arguments as { a: number; b: number };
    return { content: [{ type: "text", text: String(a + b) }] };
  }
  throw new Error(`Unknown tool: ${request.params.name}`);
});

await server.connect(new StdioServerTransport());
```

---

## SQL Toolkit

```bash
npm install langchain @langchain/core @langchain/classic typeorm
```

Four tools provided by `SqlToolkit`:

| Tool | Description |
|---|---|
| `query-sql` | Execute SQL; returns error if query fails |
| `info-sql` | Get schema + sample rows for given tables |
| `list-tables-sql` | List all tables (empty string input) |
| `query-checker` | Validate SQL before running it — always call this first |

```ts
import { ChatOpenAI } from "@langchain/openai";
import { SqlToolkit } from "@langchain/classic/agents/toolkits/sql";
import { SqlDatabase } from "@langchain/classic/sql_db";
import { DataSource } from "typeorm";
import { createAgent } from "langchain";

const datasource = new DataSource({ type: "sqlite", database: "./Chinook.db" });
const db = await SqlDatabase.fromDataSourceParams({ appDataSource: datasource });
const toolkit = new SqlToolkit(db, new ChatOpenAI({ model: "gpt-4o-mini", temperature: 0 }));

const agent = createAgent({
  model: "openai:gpt-4o-mini",
  tools: toolkit.getTools(),
});

for await (const event of await agent.stream(
  { messages: [["user", "List 10 artists"]] },
  { streamMode: "values" }
)) {
  const lastMsg = event.messages.at(-1);
  if (lastMsg?.content) console.log(lastMsg.content);
}
```

---

## Retriever as Tool

Convert any LangChain retriever into an agent tool for agentic RAG:

```ts
import { createRetrieverTool } from "langchain/tools/retriever";

const retrieverTool = createRetrieverTool(retriever, {
  name: "search_knowledge_base",
  description: "Search the company knowledge base for policies, documentation, and internal data. Use when answering questions about company-internal information.",
});

// Or manually for full control:
import { tool } from "langchain";

const retrieverTool2 = tool(
  async ({ query }) => {
    const docs = await retriever.invoke(query);
    return docs.map((d) => d.pageContent).join("\n\n");
  },
  {
    name: "search_knowledge_base",
    description: "Search internal knowledge base. Use for company-specific questions.",
    schema: z.object({ query: z.string().describe("The search query") }),
  }
);
```

---

## Toolkit Pattern

Group related tools with `BaseToolkit`:

```ts
import { BaseToolkit } from "@langchain/core/tools";
import { tool } from "langchain";
import { z } from "zod";

class EmailToolkit extends BaseToolkit {
  tools = [
    tool(
      async ({ to, subject, body }) => `Sent email to ${to}`,
      {
        name: "send_email",
        description: "Send an email. Use when the user wants to email someone.",
        schema: z.object({
          to: z.string().email().describe("Recipient email address"),
          subject: z.string().describe("Email subject line"),
          body: z.string().describe("Email body text"),
        }),
      }
    ),
    tool(
      async ({ query }) => `Found emails matching '${query}'`,
      {
        name: "search_emails",
        description: "Search sent/received emails by keyword.",
        schema: z.object({ query: z.string().describe("Search term") }),
      }
    ),
  ];

  getTools() {
    return this.tools;
  }
}

const agent = createAgent({
  model: "gpt-4o",
  tools: new EmailToolkit().getTools(),
});
```

---

## Tool Observability

### LangSmith auto-tracing

All tool calls are automatically traced when `LANGSMITH_TRACING=true`:

```bash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your-api-key
LANGSMITH_PROJECT=my-project
```

Each tool span captures: name, input args, output, duration, error details, and parent/child agent relationship.

### Adding metadata and tags

```ts
const tracedTool = tool(
  async ({ query }) => `Results for ${query}`,
  {
    name: "search",
    description: "Search the web.",
    schema: z.object({ query: z.string() }),
    metadata: { version: "2.0", team: "search" },
    tags: ["search", "external-api"],
  }
);

// Per-invocation metadata
await tracedTool.invoke(
  { query: "LangChain" },
  { metadata: { user_id: "usr_123" }, tags: ["production"] }
);
```

### `streamEvents()` for real-time tool monitoring

```ts
for await (const event of agent.streamEvents(
  { messages: [{ role: "user", content: "Search for LangChain docs" }] },
  { version: "v2" }
)) {
  if (event.event === "on_tool_start") {
    console.log(`Tool started: ${event.name}`, event.data.input);
  }
  if (event.event === "on_tool_end") {
    console.log(`Tool ended: ${event.name}`, event.data.output);
  }
}
```

---

## Known Issues and Workarounds

| Issue | Cause | Fix |
|---|---|---|
| `DynamicStructuredTool` discards JSON Schema | Constructor replaces non-Zod schemas with empty passthrough | Always use Zod schemas |
| Complex Zod schema `$ref` rejected by providers | `bindTools()` does not set `$refStrategy: "none"` | Use `zodToJsonSchema(schema, { $refStrategy: "none" })` and pass raw function definition |
| `bindTools` + `withStructuredOutput` conflict | Both modify model binding; second call overwrites first | Use `createAgent` with `responseFormat` |
| `createAgent` cannot configure `ToolNode` errors | No direct `handleToolErrors` passthrough | Create `ToolNode` manually, pass as `createAgent({ tools: myToolNode })` |
| `returnDirect` tool throws → agent exits | Exception propagates before graph routing handles it | Wrap in try/catch returning error string, or use `handleToolErrors` in `ToolNode` |
| TypeScript OOM on complex `tool()` schemas | Type inference blows up on very complex Zod schemas | Add explicit type annotations to the function argument |
| Small models fail tool calling | Models <7B often cannot select tools or format args | Use capable models: Qwen3, DeepSeek, GPT-4o, Claude, Gemini Flash |
| `tool_call_id` mismatch validation error | `ToolMessage.tool_call_id` does not match `ToolCall.id` | Ensure IDs match exactly; use `tool.invoke(toolCall)` which handles this automatically |
| `AgentExecutor` deprecated | Removed in LangChain.js v1 | Use `createAgent()` or `ToolNode` + `StateGraph` |

---

## Decision Tree

```
Need a tool?
├── Single string input?
│   └── tool(fn, { schema: z.string() })  → DynamicTool
├── Multiple structured inputs?
│   ├── Stateless / functional?
│   │   └── tool(fn, { schema: z.object({...}) })  ← PREFERRED
│   ├── Needs class-level state (DB conn, cache)?
│   │   └── class MyTool extends StructuredTool { _call() {...} }
│   └── Need raw DynamicStructuredTool features?
│       └── new DynamicStructuredTool({ name, description, schema, func })
└── MCP server tools?
    └── new MultiServerMCPClient({...}).getTools()
```

### Canonical imports

```ts
import { tool, createAgent, toolRetryMiddleware, ToolMessage } from "langchain";
import { ToolNode, toolsCondition } from "@langchain/langgraph/prebuilt";
import { StructuredTool, DynamicStructuredTool } from "@langchain/core/tools";
import { MultiServerMCPClient } from "@langchain/mcp-adapters";
import * as z from "zod";
```
