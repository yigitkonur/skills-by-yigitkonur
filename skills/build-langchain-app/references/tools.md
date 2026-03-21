# Tools Reference

Complete reference for designing and implementing tools for LangChain.js agents. All code verified against langchain@1.2.35, @langchain/core@1.1.34, @langchain/langgraph@1.2.5. TypeScript only.

---

## Tool Design Philosophy

Tools are the agent's hands. Good tool design determines whether an agent succeeds or loops forever.

### Core principles

1. **Atomic operations** — Each tool does one thing. `get_user_profile` and `update_user_email` are two tools, not one `manage_user` tool.
2. **Read/write separation** — Separate data retrieval from data mutation. Read tools are safe to retry. Write tools need confirmation flows.
3. **Semantic naming** — Tool names must clearly describe the action. The model uses the name + description to decide which tool to call.
4. **Descriptions are everything** — The description is the most important field. If the model picks the wrong tool, fix the description first.

---

## tool() Function — Full API

The `tool()` function from `@langchain/core/tools` is the primary way to create tools.

```typescript
import { tool } from "@langchain/core/tools";
import { z } from "zod";

const myTool = tool(
  // Implementation function — receives parsed, typed args
  async ({ query, limit }: { query: string; limit: number }) => {
    // Tool logic here
    return `Found ${limit} results for "${query}"`;
  },
  {
    // Tool configuration
    name: "search_documents",
    description: "Search internal documents for information. Use when the user asks about company policies, product specs, or internal knowledge.",
    schema: z.object({
      query: z.string().describe("The search query"),
      limit: z.number().default(5).describe("Maximum number of results to return"),
    }),
  }
);
```

### Configuration fields

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | Tool name. Use `snake_case`. Must be unique across all tools in the agent. |
| `description` | `string` | Yes | What the tool does AND when to use it. This is what the LLM reads to decide tool selection. |
| `schema` | `ZodObject` | Yes | Zod schema defining the input parameters. |

### Implementation function rules

- Receives a single object with typed fields matching the schema.
- Must return a `string`. The string becomes the `ToolMessage.content` the model sees.
- Can be `async`. Always prefer `async` for I/O operations.
- Errors thrown from the function become tool errors the agent sees (unless caught by middleware).

---

## Description Writing — The "What + When" Pattern

The description is the single most important field for tool selection accuracy. Write it as "what this tool does" + "when to use it."

### Pattern

```
"[What it does]. [When to use it — specific trigger conditions]."
```

### Examples

```typescript
// ❌ BAD — vague, no trigger condition
description: "Searches for things"

// ❌ BAD — too technical, no "when"
description: "Executes a vector similarity search against the Pinecone index with cosine distance"

// ✅ GOOD — what + when
description: "Search the web for current information, news, and articles. Use when the user asks about recent events or facts that may have changed since your training data."

// ✅ GOOD — what + when with specificity
description: "Look up a customer's order status by order ID. Use when the user provides an order number or asks about a specific order."

// ✅ GOOD — what + explicit exclusion
description: "Calculate mathematical expressions. Use for arithmetic, algebra, and unit conversions. Do NOT use for statistical analysis — use the analytics_query tool instead."
```

### Why this matters

The model receives all tool names, descriptions, and schemas. It decides which tool to call based primarily on the description matching the user's intent. A missing or vague description causes:
- Wrong tool selection
- Unnecessary tool calls
- Agent loops (calls tool, gets irrelevant result, tries again)

---

## Schema Design

### Flat schemas (recommended)

Flat schemas with primitive types are the safest. Models handle them reliably across all providers.

```typescript
const schema = z.object({
  query: z.string().describe("The search query"),
  maxResults: z.number().default(10).describe("Maximum results to return"),
  includeArchived: z.boolean().default(false).describe("Whether to include archived items"),
});
```

### Nested schemas (use with caution)

Nested objects work but increase the chance of malformed tool calls, especially with smaller models.

```typescript
// ⚠️ Works but riskier — some models struggle with nested objects
const schema = z.object({
  filters: z.object({
    dateRange: z.object({
      start: z.string().describe("ISO date string"),
      end: z.string().describe("ISO date string"),
    }),
    categories: z.array(z.string()).describe("Category filters"),
  }),
});

// ✅ Prefer flattening
const schema = z.object({
  filterDateStart: z.string().describe("Start date in ISO format"),
  filterDateEnd: z.string().describe("End date in ISO format"),
  filterCategories: z.string().describe("Comma-separated list of categories"),
});
```

### Zod patterns that work

```typescript
import { z } from "zod";

// String with description (always add .describe())
z.string().describe("The user's email address")

// Number with default
z.number().default(10).describe("Page size")

// Optional field
z.string().optional().describe("Optional filter term")

// Enum — great for constrained choices
z.enum(["asc", "desc"]).describe("Sort direction")

// Array of strings
z.array(z.string()).describe("List of tags to filter by")

// Boolean with default
z.boolean().default(false).describe("Include deleted records")
```

### Zod patterns to avoid

```typescript
// ❌ Union types — models often pick the wrong branch
z.union([z.string(), z.number()])

// ❌ Discriminated unions — too complex for tool schemas
z.discriminatedUnion("type", [...])

// ❌ Record/map types — unpredictable key generation
z.record(z.string(), z.number())

// ❌ Deeply nested objects (3+ levels)
z.object({ a: z.object({ b: z.object({ c: z.string() }) }) })

// ❌ Missing .describe() — the model has no guidance on what to pass
z.object({ q: z.string() }) // What is "q"?
```

**Rule**: Always call `.describe()` on every schema field. The description text is sent to the model as part of the tool definition.

---

## Multi-Tool Agents — How Models Select Tools

### How tool selection works

When an agent has multiple tools, the model receives all tool definitions (name + description + schema) in the system context. For each user message, the model:

1. Reads the user query
2. Compares against all tool descriptions
3. Selects zero, one, or multiple tools to call
4. Generates the arguments for each selected tool

### Tool count guidelines

| Tool count | Reliability | Notes |
|---|---|---|
| 1–5 | High | Models reliably select the correct tool |
| 6–10 | Good | Some models start confusing similar tools |
| 11–20 | Fair | Requires very distinct descriptions. Consider splitting into sub-agents. |
| 20+ | Poor | Split into multiple agents or use tool routing |

### Multi-tool example

```typescript
import { createAgent } from "langchain";
import { tool } from "@langchain/core/tools";
import { z } from "zod";

const searchTool = tool(
  async ({ query }: { query: string }) => `Search results for "${query}"`,
  {
    name: "web_search",
    description: "Search the web for current information, news, and articles. Use when the user asks about recent events or facts.",
    schema: z.object({ query: z.string().describe("The search query") }),
  }
);

const calculatorTool = tool(
  async ({ expression }: { expression: string }) => {
    const result = Function(`"use strict"; return (${expression})`)();
    return `Result: ${result}`;
  },
  {
    name: "calculator",
    description: "Evaluate mathematical expressions. Use for arithmetic, algebra, and unit conversions.",
    schema: z.object({ expression: z.string().describe("A math expression like '2 + 3 * 4'") }),
  }
);

const weatherTool = tool(
  async ({ city }: { city: string }) => `Weather in ${city}: 22°C, partly cloudy`,
  {
    name: "get_weather",
    description: "Get the current weather for a specific city. Use when the user asks about weather conditions.",
    schema: z.object({ city: z.string().describe("The city name") }),
  }
);

const agent = createAgent({
  model,
  tools: [searchTool, calculatorTool, weatherTool],
  prompt: "You are a helpful assistant with search, calculator, and weather tools.",
});

// Agent correctly routes:
// "Search for AI news"       → web_search
// "What is 156 * 23 + 89?"  → calculator
// "What's the weather in Tokyo?" → get_weather
```

### Handling tool name conflicts

Tool names must be unique within an agent. If integrating tools from multiple sources:

```typescript
// ❌ Name conflict — both called "search"
const tools = [internalSearchTool, webSearchTool]; // Both named "search"

// ✅ Use distinct names
const internalSearchTool = tool(fn, { name: "search_internal_docs", ... });
const webSearchTool = tool(fn, { name: "search_web", ... });
```

---

## Tool Error Handling

### Default behavior

If a tool throws an error, the exception message is sent back to the model as a `ToolMessage`. The model then decides whether to retry, try a different approach, or report the error to the user.

### Tool-level try/catch

Handle expected errors inside the tool and return a helpful message:

```typescript
const apiTool = tool(
  async ({ endpoint }: { endpoint: string }) => {
    try {
      const response = await fetch(endpoint);
      if (!response.ok) {
        return `API returned error ${response.status}: ${response.statusText}. Try a different endpoint or check the URL.`;
      }
      return await response.text();
    } catch (error) {
      return `Failed to reach ${endpoint}. The service may be down. Error: ${(error as Error).message}`;
    }
  },
  {
    name: "call_api",
    description: "Call an HTTP API endpoint and return the response.",
    schema: z.object({ endpoint: z.string().describe("The full URL to call") }),
  }
);
```

Return a descriptive error string — not just "Error occurred." The model needs context to decide its next action.

### Middleware-level error handling with toolRetryMiddleware

Automatically retry failed tool calls:

```typescript
import { createAgent, toolRetryMiddleware } from "langchain";

const agent = createAgent({
  model,
  tools: [apiTool],
  middleware: [
    toolRetryMiddleware({ maxRetries: 2 }),
  ],
  prompt: "You are a helpful assistant.",
});
```

### Custom error wrapping with createMiddleware

For custom error handling logic across all tools:

```typescript
import { createMiddleware } from "langchain";

const errorHandlingMiddleware = createMiddleware({
  name: "tool-error-handler",
  // Use afterModel or beforeModel to inspect/modify tool results
  afterModel: async (state) => {
    // Inspect the last message for tool errors
    const lastMsg = state.messages[state.messages.length - 1];
    if (lastMsg.content && typeof lastMsg.content === "string" && lastMsg.content.startsWith("Error:")) {
      console.error(`Tool error detected: ${lastMsg.content}`);
    }
    return undefined;
  },
});
```

---

## DynamicTool vs StructuredTool vs tool() Function

Three ways to create tools. Use `tool()` in almost all cases.

### tool() function (recommended)

```typescript
import { tool } from "@langchain/core/tools";
import { z } from "zod";

const myTool = tool(
  async ({ input }: { input: string }) => `Processed: ${input}`,
  {
    name: "process",
    description: "Process input text",
    schema: z.object({ input: z.string() }),
  }
);
```

Use for: all new tools. Simplest API, full type safety, Zod integration.

### DynamicTool (legacy — avoid)

```typescript
import { DynamicTool } from "@langchain/core/tools";

const myTool = new DynamicTool({
  name: "process",
  description: "Process input text",
  func: async (input: string) => `Processed: ${input}`,
});
```

Use for: never. Single string input only. No schema support. Exists for backward compatibility.

### StructuredTool (class-based — rare use)

```typescript
import { StructuredTool } from "@langchain/core/tools";
import { z } from "zod";

class ProcessTool extends StructuredTool {
  name = "process";
  description = "Process input text";
  schema = z.object({ input: z.string() });

  async _call({ input }: { input: string }) {
    return `Processed: ${input}`;
  }
}

const myTool = new ProcessTool();
```

Use for: tools that need class-level state, inheritance, or complex initialization. The `tool()` function is preferred for stateless tools.

### Decision table

| Need | Use |
|---|---|
| Standard tool | `tool()` |
| Tool with internal state (DB connection, cache) | `StructuredTool` class |
| Single string input (legacy code) | `DynamicTool` |

---

## MCP Integration

Use `@langchain/mcp-adapters` to connect to Model Context Protocol servers and use their tools with LangChain agents.

```bash
npm install @langchain/mcp-adapters
```

### Basic MCP client

```typescript
import { MultiServerMCPClient } from "@langchain/mcp-adapters";
import { createAgent } from "langchain";

const client = new MultiServerMCPClient({
  servers: {
    filesystem: {
      transport: "stdio",
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
    },
    weather: {
      transport: "http",
      url: "http://localhost:3001/mcp",
    },
  },
});

// Get tools from all MCP servers
const mcpTools = await client.getTools();

// Use MCP tools alongside local tools
const agent = createAgent({
  model,
  tools: [...localTools, ...mcpTools],
  prompt: "You are a helpful assistant with file system and weather tools.",
});

const result = await agent.invoke({
  messages: [{ role: "user", content: "List files in /tmp" }],
});
```

### Transport types

| Transport | Use case | Config |
|---|---|---|
| `stdio` | Local MCP server as subprocess | `command`, `args` |
| `http` | Remote MCP server | `url` |

### MCP considerations

- MCP tools have their own names and descriptions from the server. Verify they don't conflict with local tool names.
- MCP tools are async. The agent handles this transparently.
- Close the client when done: `await client.close()`.

---

## Tool Performance

### Response time expectations

| Tool type | Target latency | Notes |
|---|---|---|
| In-memory computation | < 10ms | Math, string processing, data transformation |
| Local database query | < 100ms | SQLite, local PostgreSQL |
| External API call | < 2s | REST APIs, search engines |
| Complex retrieval (RAG) | < 3s | Vector search + reranking |

Tools that exceed 5 seconds risk model timeout or context confusion. For long-running operations, return a status message and provide a separate "check status" tool.

### Token efficiency

The tool's return string is injected into the model's context as a `ToolMessage`. Keep responses concise:

```typescript
// ❌ BAD — returns entire API response
return JSON.stringify(apiResponse); // 5000+ tokens

// ✅ GOOD — extract and summarize relevant data
return `Found ${results.length} orders. Most recent: Order #${results[0].id} (${results[0].status}) placed on ${results[0].date}.`;
```

Large tool responses consume context window tokens and reduce the model's capacity for reasoning. Summarize or truncate to the relevant information.

---

## Common Tool Bugs

### 1. Missing description

```typescript
// ❌ BUG — model has no idea when to use this tool
const myTool = tool(fn, {
  name: "do_thing",
  description: "",
  schema,
});

// ✅ FIX — always provide a meaningful description
description: "Process and validate user input data. Use when the user submits a form or provides structured data."
```

### 2. Overly complex schemas

```typescript
// ❌ BUG — model generates malformed args
schema: z.object({
  config: z.object({
    filters: z.array(z.object({
      field: z.string(),
      operator: z.enum(["eq", "ne", "gt", "lt"]),
      value: z.union([z.string(), z.number()]),
    })),
    sort: z.object({
      field: z.string(),
      direction: z.enum(["asc", "desc"]),
    }).optional(),
  }),
})

// ✅ FIX — flatten or simplify
schema: z.object({
  filterField: z.string().describe("Field to filter on"),
  filterValue: z.string().describe("Value to filter for"),
  sortField: z.string().optional().describe("Field to sort by"),
  sortDirection: z.enum(["asc", "desc"]).default("asc").describe("Sort direction"),
})
```

### 3. Tool name conflicts

```typescript
// ❌ BUG — two tools named "search" causes undefined behavior
tools: [
  tool(fn1, { name: "search", description: "Search web", schema: s1 }),
  tool(fn2, { name: "search", description: "Search docs", schema: s2 }),
]

// ✅ FIX — unique names
tools: [
  tool(fn1, { name: "search_web", description: "Search web", schema: s1 }),
  tool(fn2, { name: "search_docs", description: "Search docs", schema: s2 }),
]
```

### 4. Returning non-string from tool

```typescript
// ❌ BUG — returns object, not string
const myTool = tool(
  async ({ id }) => ({ user: "Alice", age: 30 }), // Object, not string
  { name: "get_user", description: "Get user", schema }
);

// ✅ FIX — always return a string
const myTool = tool(
  async ({ id }) => JSON.stringify({ user: "Alice", age: 30 }),
  { name: "get_user", description: "Get user", schema }
);
```

### 5. Missing .describe() on schema fields

```typescript
// ❌ BUG — model doesn't know what "q" means
schema: z.object({ q: z.string(), n: z.number() })

// ✅ FIX — describe every field
schema: z.object({
  q: z.string().describe("The search query text"),
  n: z.number().describe("Number of results to return"),
})
```

### 6. Tool that never returns

```typescript
// ❌ BUG — infinite loop or hang
const myTool = tool(
  async () => {
    while (true) { /* polling */ }
  },
  { name: "poll", description: "Poll for updates", schema }
);

// ✅ FIX — add timeout
const myTool = tool(
  async () => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);
    try {
      const result = await fetch(url, { signal: controller.signal });
      return await result.text();
    } catch {
      return "Request timed out after 5 seconds.";
    } finally {
      clearTimeout(timeout);
    }
  },
  { name: "poll", description: "Poll for updates", schema }
);
```
