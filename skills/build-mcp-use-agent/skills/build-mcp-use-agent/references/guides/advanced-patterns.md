# Advanced Patterns

This guide covers advanced MCPAgent patterns: full agent configuration, LLM integration, memory management, server manager, structured output, streaming, and observability.

---

## When to use these patterns

Use advanced patterns when you need:

- Fine-grained control over agent configuration (steps, memory, prompts, tool restrictions)
- Multi-provider LLM support with consistent interface
- Conversation memory across multiple turns
- Dynamic multi-server routing via Server Manager
- Typed structured output from agent runs
- Real-time streaming of steps or raw events
- Production observability via Langfuse

---

## Key imports

```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";
import { ChatAnthropic } from "@langchain/anthropic";
import { ChatGoogleGenerativeAI } from "@langchain/google-genai";
import { ChatGroq } from "@langchain/groq";
import { z } from "zod";
```

---

## MCPAgent configuration reference

### Full options interface

```typescript
// Explicit mode — provide pre-instantiated LLM and client
interface ExplicitModeOptions {
  llm: LanguageModel;              // required — any LangChain-compatible LLM instance
  client?: MCPClient;              // required unless connectors are provided
  connectors?: BaseConnector[];    // alternative to client for direct connector access
  maxSteps?: number;               // default: 5
  autoInitialize?: boolean;        // default: false
  memoryEnabled?: boolean;         // default: true
  systemPrompt?: string | null;    // replaces the default system prompt entirely
  systemPromptTemplate?: string | null; // template string (overrides systemPrompt)
  additionalInstructions?: string | null; // appended to default system prompt
  disallowedTools?: string[];      // tool names hidden from the agent
  additionalTools?: StructuredToolInterface[]; // extra tools to inject alongside MCP tools
  exposeResourcesAsTools?: boolean; // default: true — expose MCP resources as tools
  exposePromptsAsTools?: boolean;   // default: true — expose MCP prompts as tools
  useServerManager?: boolean;      // default: false — enable dynamic multi-server routing
  verbose?: boolean;               // default: false — log server discovery/connections/tools
  observe?: boolean;               // default: true — enable automatic observability
  callbacks?: BaseCallbackHandler[]; // LangChain/Langfuse callback handlers
}

// Simplified mode — provide LLM as string and servers inline
interface SimplifiedModeOptions {
  llm: string;                     // Format: "provider/model" e.g. "openai/gpt-4o"
  llmConfig?: {                    // Optional LLM configuration overrides
    temperature?: number;
    maxTokens?: number;
    apiKey?: string;
  };
  mcpServers: Record<string, MCPServerConfig>; // inline server definitions
  // plus all CommonAgentOptions fields above (except client/connectors)
}
```

### Options table

| Option | Type | Default | Purpose |
|---|---|---|---|
| `llm` | LLM instance or `"provider/model"` string | — | Required. Any LangChain-compatible model or string identifier. |
| `client` | `MCPClient` | `undefined` | MCP client managing server connections (explicit mode). |
| `connectors` | `BaseConnector[]` | `[]` | Direct connectors, alternative to `client`. |
| `mcpServers` | `Record<string, MCPServerConfig>` | — | Inline server definitions (simplified mode, replaces `client`). |
| `llmConfig` | `{ temperature?, maxTokens?, apiKey? }` | `undefined` | LLM config overrides when using simplified mode. |
| `maxSteps` | `number` | `5` | Maximum reasoning loop iterations. |
| `autoInitialize` | `boolean` | `false` | Auto-calls `initialize()` on construction. |
| `memoryEnabled` | `boolean` | `true` | Retains conversation history across turns. |
| `systemPrompt` | `string \| null` | `undefined` | Replaces the default system prompt entirely. |
| `systemPromptTemplate` | `string \| null` | `undefined` | Template string (overrides `systemPrompt`). |
| `additionalInstructions` | `string \| null` | `undefined` | Extra instructions appended to default system prompt. |
| `disallowedTools` | `string[]` | `[]` | Tool names hidden from the agent. |
| `additionalTools` | `StructuredToolInterface[]` | `[]` | Extra tools injected alongside MCP tools. |
| `exposeResourcesAsTools` | `boolean` | `true` | Expose MCP resources as callable tools. |
| `exposePromptsAsTools` | `boolean` | `true` | Expose MCP prompts as callable tools. |
| `useServerManager` | `boolean` | `false` | Enables dynamic multi-server routing. |
| `verbose` | `boolean` | `false` | Logs server discovery, connections, tool calls. |
| `observe` | `boolean` | `true` | Enable automatic observability/tracing. |
| `callbacks` | `BaseCallbackHandler[]` | `[]` | LangChain/Langfuse callback handlers. |

### MCPAgent public methods

> **Awaitable vs generator-returning methods.** `run()` and lifecycle methods return a `Promise` and must be `await`ed. The streaming methods (`stream`, `streamEvents`, `prettyStreamEvents`) return `AsyncGenerator` objects **synchronously** — do **not** `await` the call itself; consume the generator with `for await`. The two groups are listed together below; check the Return Type column.

#### Awaitable methods

| Method | Signature | Return Type | Description |
|---|---|---|---|
| `run` | `run(prompt: string)` or `run({ prompt, schema?, maxSteps?, signal?, manageConnector?, externalHistory? })` | `Promise<string>` or `Promise<T>` | Execute a prompt; plain string form is deprecated but works. |
| `initialize` | `initialize(): Promise<void>` | `Promise<void>` | Async setup; called automatically when `autoInitialize: true` or when `manageConnector` is true at runtime. |

#### Streaming methods (return generators synchronously — do not `await` the call)

| Method | Signature | Return Type | Description |
|---|---|---|---|
| `stream` | `stream(prompt: string)` or `stream({ prompt, schema?, maxSteps?, signal? })` | `AsyncGenerator<AgentStep, string \| T, void>` | Yield step objects; generator return value is the final result. |
| `streamEvents` | `streamEvents(prompt: string)` or `streamEvents({ prompt, schema?, maxSteps?, signal? })` | `AsyncGenerator<StreamEvent, void, void>` | Yield raw LangChain events; plain string form is deprecated. |
| `prettyStreamEvents` | `prettyStreamEvents(prompt: string)` or `prettyStreamEvents({ prompt, maxSteps?, schema? })` | `AsyncGenerator<void, string, void>` | Formatted, colored CLI output. Plain-string form is deprecated; prefer the options object. |

#### Other methods

| Method | Signature | Return Type | Description |
|---|---|---|---|
| `setDisallowedTools` | `setDisallowedTools(tools: string[]): void` | `void` | Update restricted tools at runtime. Changes take effect on next `initialize()` call. |
| `getDisallowedTools` | `getDisallowedTools(): string[]` | `string[]` | Retrieve current restricted tool list. |
| `getConversationHistory` | `getConversationHistory(): BaseMessage[]` | `BaseMessage[]` | Returns copy of current conversation history. |
| `clearConversationHistory` | `clearConversationHistory(): void` | `void` | Clears history (preserves system message if `memoryEnabled`). |
| `setMetadata` | `setMetadata(metadata: Record<string, any>): void` | `void` | Merge metadata into all subsequent traces (accumulates, does not replace). |
| `getMetadata` | `getMetadata(): Record<string, any>` | `Record<string, any>` | Returns copy of current metadata. |
| `setTags` | `setTags(tags: string[]): void` | `void` | Add tags for trace filtering (deduplicates automatically). |
| `getTags` | `getTags(): string[]` | `string[]` | Returns copy of current tags array. |
| `flush` | `flush(): Promise<void>` | `Promise<void>` | Flush pending observability traces — important in serverless. |
| `close` | `close(): Promise<void>` | `Promise<void>` | Gracefully shut down agent resources. |

### MCPClient public methods

| Method | Signature | Return Type | Description |
|---|---|---|---|
| `createAllSessions` | `createAllSessions(autoInitialize?: boolean)` | `Promise<Record<string, MCPSession>>` | Connect all configured MCP servers upfront; resolves to a map of server name → `MCPSession`. Pass `false` to skip auto-initialization. |
| `closeAllSessions` | `closeAllSessions(): Promise<void>` | `Promise<void>` | Gracefully close all active server sessions. |

---

## LLM integration

Each of the four providers below accepts a `{ model, temperature, apiKey }` core, and `apiKey` is optional when the corresponding environment variable is set. Beyond that core, each provider exposes its own options — for example `safetySettings` and `maxOutputTokens` (Google), `thinking` (Anthropic v4+), and `maxTokens` vs `maxOutputTokens` (OpenAI vs Google). For anything past the basics, check the matching `@langchain/<provider>` README.

```typescript
// OpenAI
import { ChatOpenAI } from "@langchain/openai";
const llm = new ChatOpenAI({
  model: "gpt-4o",
  temperature: 0.7,
  apiKey: process.env.OPENAI_API_KEY,
});
```

```typescript
// Anthropic (current generation as of April 2026)
import { ChatAnthropic } from "@langchain/anthropic";
const llm = new ChatAnthropic({
  model: "claude-sonnet-4-6",   // or "claude-opus-4-7" for hardest reasoning
  temperature: 0.7,
  apiKey: process.env.ANTHROPIC_API_KEY,
});
```

```typescript
// Google Gemini
import { ChatGoogleGenerativeAI } from "@langchain/google-genai";
const llm = new ChatGoogleGenerativeAI({
  model: "gemini-2.5-pro",      // or "gemini-2.0-flash" for lower latency
  temperature: 0.7,
  apiKey: process.env.GOOGLE_API_KEY,
});
```

```typescript
// Groq
import { ChatGroq } from "@langchain/groq";
const llm = new ChatGroq({
  model: "llama-3.3-70b-versatile",
  temperature: 0.7,
  apiKey: process.env.GROQ_API_KEY,
});
```

All LLM instances are passed directly to `MCPAgent` as `llm`. Tool calling, structured output, and streaming are available for any provider that supports these features through LangChain's unified interface.

> Model IDs drift. If you see `model_not_found` / `404`, check the provider's current model list (Anthropic, Google AI Studio, Groq) — the snapshots above were current as of April 2026.

---

## Memory management

`memoryEnabled` defaults to `true`. The agent retains context across consecutive `run` calls automatically.

### Self-managed memory (default)

```typescript
const agent = new MCPAgent({
  llm,
  client,
  memoryEnabled: true,   // default — no need to set explicitly
});

await agent.run("Hello, my name is Alice");
await agent.run("What's my name?");   // remembers "Alice"

await client.closeAllSessions();
```

### Stateless agent

```typescript
const agent = new MCPAgent({
  llm,
  client,
  memoryEnabled: false,   // each call is independent
});
```

### Inspecting and clearing history

```typescript
// Inspect current history
const history = agent.getConversationHistory();
console.log(`${history.length} messages in history`);

for (const msg of history) {
  console.log(msg.constructor.name, msg.content);
}

// Clear history (system message is preserved when memoryEnabled is true)
agent.clearConversationHistory();
```

---

## Tool restrictions

### Static restrictions at construction

```typescript
const agent = new MCPAgent({
  llm,
  client,
  disallowedTools: ["file_system", "network", "shell"],
});
```

### Dynamic restrictions at runtime

```typescript
agent.setDisallowedTools(["file_system", "network", "shell", "database"]);
await agent.initialize();   // must re-initialize to apply changes

const restricted = agent.getDisallowedTools();
console.log("Restricted tools:", restricted);
```

### Tool gating by workflow step

```typescript
function toolsForStep(step: string): string[] {
  return step === "analyze" ? ["shell", "network"] : ["file_system"];
}

const agent = new MCPAgent({
  llm,
  client,
  disallowedTools: toolsForStep("analyze"),
});
```

---

## System prompt customization

```typescript
// Full replacement
const agent = new MCPAgent({
  llm,
  client,
  systemPrompt: `You are a data analysis assistant.
Always explain your reasoning step by step.
Prioritize accuracy over speed.`,
});

// Append extra instructions without replacing the default
const agent = new MCPAgent({
  llm,
  client,
  additionalInstructions: "Always respond in JSON when possible.",
});
```

---

## Server Manager

When `useServerManager: true` is set, the agent gains five built-in management tools that it can invoke autonomously to discover and route between servers.

### Built-in server management tools

| Tool | Parameters | Return Type | Description |
|---|---|---|---|
| `list_mcp_servers` | — | `Promise<ServerInfo[]>` | List available servers and their tool inventories. |
| `connect_to_mcp_server` | `serverName: string` | `Promise<void>` | Activate a server and load its tools. |
| `get_active_mcp_server` | — | `Promise<string \| null>` | Name of the currently connected server. |
| `disconnect_from_mcp_server` | — | `Promise<void>` | Deactivate current server and unload tools. |
| `add_mcp_server_from_config` | `serverName: string, serverConfig: ServerConfig` | `Promise<void>` | Register a new server at runtime. |

### ServerInfo type

```typescript
interface ServerInfo {
  name: string;
  tools: string[];
  status: "online" | "offline";
}
```

### Basic setup

```typescript
const client = new MCPClient({
  mcpServers: {
    playwright: {
      command: "npx",
      args: ["@playwright/mcp@latest"],
    },
    filesystem: {
      command: "uvx",
      args: ["mcp-server-filesystem", "/tmp"],
    },
  },
});

const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),
  client,
  useServerManager: true,
});
```

### Full multi-server workflow

```typescript
const client = new MCPClient({
  mcpServers: {
    web:      { command: "npx",  args: ["@playwright/mcp@latest"] },
    files:    { command: "uvx",  args: ["mcp-server-filesystem", "/tmp"] },
    database: { command: "uvx",  args: ["mcp-server-sqlite"] },
  },
});

const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),
  client,
  useServerManager: true,
  verbose: true,   // logs discovery, connection lifecycle, tool execution
});

const result = await agent.run(`
  1. List all available servers and their tools
  2. Scrape product data from https://example-store.com
  3. Save it as JSON and CSV
  4. Load into SQLite
  5. Generate a summary report
`);

await client.closeAllSessions();
```

**Note:** The agent discovers and switches between servers automatically using the built-in management tools. You do not implement routing logic — the LLM drives it.

---

## Structured output

Pass a Zod schema to `agent.run()` to get a fully-typed response. The agent's output is validated and cast to the schema type.

### Basic structured run

```typescript
import { z } from "zod";

const WeatherInfo = z.object({
  city:        z.string().describe("City name"),
  temperature: z.number().describe("Temperature in Celsius"),
  condition:   z.string().describe("Weather condition"),
  humidity:    z.number().describe("Humidity percentage"),
});
type WeatherInfo = z.infer<typeof WeatherInfo>;

const weather = await agent.run({
  prompt: "Get the current weather in San Francisco",
  schema: WeatherInfo,
});

console.log(`${weather.city}: ${weather.temperature}°C, ${weather.condition}`);
```

### Structured output events when streaming

When `streamEvents()` is used with a `schema`, three additional events are emitted:

| Event | Frequency | Description |
|---|---|---|
| `on_structured_output_progress` | Every ~2 seconds during conversion | Conversion of raw LLM output is in progress. |
| `on_structured_output` | Once on success | Structured output is validated and ready. |
| `on_structured_output_error` | Once on failure | Conversion or validation failed after all retries. |

```typescript
const schema = z.array(z.object({ title: z.string(), rating: z.number() }));

for await (const event of agent.streamEvents({ prompt: "List the top 3 trending movies", schema })) {
  if (event.event === "on_structured_output_progress") {
    console.log("Conversion in progress...");
  } else if (event.event === "on_structured_output") {
    // Result is at event.data.output — parse it against your schema
    const result = schema.parse(event.data.output);
    console.log("Result:", result);
  } else if (event.event === "on_structured_output_error") {
    console.error("Failed to produce structured output");
  }
}
```

---

## Streaming

Three streaming methods are available, covering different levels of granularity.

### Method signatures

```typescript
// AgentStep — yielded by stream()
interface AgentStep {
  action: {
    tool: string;
    toolInput: any;
    log: string;
  };
  observation: string;
}

// StreamEvent — yielded by streamEvents() (from @langchain/core)
interface StreamEvent {
  event: string;  // e.g. "on_chat_model_stream", "on_tool_start", "on_structured_output"
  name: string;
  data?: {
    chunk?: {
      text?: string;    // Anthropic and some providers
      content?: string; // OpenAI and others
    };
    input?: any;    // on_tool_start
    output?: any;   // on_tool_end, on_structured_output
  };
}

// RunOptions — accepted by run(), stream(), streamEvents(), prettyStreamEvents()
interface RunOptions<T = string> {
  prompt: string;
  maxSteps?: number;
  schema?: ZodSchema<T>;
  signal?: AbortSignal;
  manageConnector?: boolean;
  externalHistory?: BaseMessage[];
}
```

### `agent.stream(prompt)` — step-by-step

Yields one `Step` object per tool invocation. Use this to track which tools are being called.

```typescript
for await (const step of agent.stream("Search for the latest Python news and summarize it")) {
  console.log(`Tool: ${step.action.tool}`);
  console.log(`Input: ${JSON.stringify(step.action.toolInput)}`);
}

await client.closeAllSessions();
```

### `agent.streamEvents(prompt)` — raw events

Yields raw LangChain events. Use this for custom handling of token-by-token output.

```typescript
for await (const event of agent.streamEvents("Search for the latest Python news and summarize it")) {
  if (event.event === "on_chat_model_stream") {
    // chunk property is either `text` or `content` depending on provider
    const text = event.data?.chunk?.text || event.data?.chunk?.content;
    if (text) {
      process.stdout.write(text);
    }
  }
}

await client.closeAllSessions();
```

### `agent.prettyStreamEvents(...)` — formatted CLI output

Applies syntax highlighting and colored formatting automatically. Nothing needs to be done inside the loop.

```typescript
for await (const _ of agent.prettyStreamEvents({
  prompt: "List all TypeScript files and count lines of code",
  maxSteps: 20,
})) {
  // formatting applied internally
}

await agent.close();
```

### Streaming to Vercel AI SDK (Next.js)

`mcp-use` exports three Vercel AI SDK helpers from the package root (re-exported via `./src/agents/utils/index.js`):

- `streamEventsToAISDK(events)` — yields plain text chunks from `on_chat_model_stream` events.
- `streamEventsToAISDKWithTools(events)` — same, plus surface tool start/end markers in the output.
- `createReadableStreamFromGenerator(gen)` — wrap an `AsyncGenerator<string>` as a `ReadableStream<string>`.

Use them directly instead of writing a local bridge helper:

```typescript
import {
  streamEventsToAISDK,
  createReadableStreamFromGenerator,
  // streamEventsToAISDKWithTools,  // alternative — adds 🔧 / ✅ tool markers
} from "mcp-use";
import { createTextStreamResponse } from "ai";
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({ mcpServers: { /* ... */ } });
const agent = new MCPAgent({ llm: new ChatOpenAI({ model: "gpt-4o" }), client });

export async function POST(req: Request) {
  const { prompt } = await req.json();
  const events = agent.streamEvents({ prompt });
  // createTextStreamResponse expects a ReadableStream<string>, not an AsyncGenerator —
  // wrap with createReadableStreamFromGenerator before passing.
  return createTextStreamResponse({
    textStream: createReadableStreamFromGenerator(streamEventsToAISDK(events)),
  });
}
```

Pick `streamEventsToAISDKWithTools` when you want the user to see `🔧 tool_name` and `✅` markers around tool calls in the streamed output; pick `streamEventsToAISDK` for raw text only.

### Streaming with persistence

When you need to persist events as they arrive (DB writes, logs, audit trail), inline the loop and re-use the same `createTextStreamResponse` plumbing:

```typescript
import { createTextStreamResponse } from "ai";
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({ mcpServers: { /* ... */ } });
const agent = new MCPAgent({ llm: new ChatOpenAI({ model: "gpt-4o" }), client });

function persistEvent(event: unknown) {
  // your logging / DB code
}

export async function POST(req: Request) {
  const { prompt } = await req.json();

  const stream = (async function* () {
    for await (const event of agent.streamEvents({ prompt })) {
      persistEvent(event);   // write to DB / log
      if (event.event === "on_chat_model_stream") {
        const text = event.data?.chunk?.text || event.data?.chunk?.content;
        if (text) yield text;
      }
    }
  })();

  return createTextStreamResponse(stream);
}
```

---

## Observability (Langfuse)

`mcp-use` integrates with Langfuse via LangChain callbacks. Set the environment variables and the agent traces automatically — no additional code is required for basic tracing.

### Environment variables

```bash
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."
```

### Automatic tracing

```typescript
const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4" }),
  client,
  maxSteps: 30,
});

// All runs are automatically traced when Langfuse env vars are set
const result = await agent.run({ prompt: "Analyze the sales data" });
```

Langfuse automatically captures:

- Full execution traces (traceId, sessionId)
- Per-step details (name, type, startTime, endTime, metadata)
- LLM call details (model, prompt, completion, tokenCount)
- Tool call details (toolName, input, output)
- Errors (errorMessage, stackTrace)

### Custom metadata and tags

```typescript
agent.setMetadata({
  agent_id: "customer-support-01",
  version: "v2.0.0",
  environment: "production",
  customer_id: "cust_12345",
});

agent.setTags(["customer-support", "high-priority", "beta-feature"]);
```

### Custom Langfuse callback handler

```typescript
import { CallbackHandler } from "langfuse-langchain";

const handler = new CallbackHandler({
  publicKey: "pk-lf-custom",
  secretKey: "sk-lf-custom",
  baseUrl: "https://custom-langfuse.com",
});

const agent = new MCPAgent({
  llm,
  client,
  callbacks: [handler],
});
```

---

## Advanced configuration examples

### Full-featured agent

```typescript
const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o", temperature: 0.7 }),
  client: new MCPClient({ mcpServers: { /* ... */ } }),
  maxSteps: 30,
  autoInitialize: true,
  memoryEnabled: true,
  systemPrompt: "You are a data analysis specialist.",
  additionalInstructions: "Always cite your sources.",
  disallowedTools: ["shell", "network"],
  verbose: true,
});
```

### Server Manager with verbose logging

```typescript
const agent = new MCPAgent({
  llm,
  client,
  useServerManager: true,
  verbose: true,
});
```

### Stateless agent with tool restrictions

```typescript
const agent = new MCPAgent({
  llm,
  client,
  memoryEnabled: false,
  disallowedTools: ["file_system", "database"],
});
```

---

## BAD / GOOD patterns

### 1) Wrong `memoryEnabled` assumption

BAD — assuming memory is off by default:
```typescript
const agent = new MCPAgent({ llm, client });
// Memory IS enabled by default; previous turns are retained
```

GOOD — be explicit when you want stateless behavior:
```typescript
const agent = new MCPAgent({ llm, client, memoryEnabled: false });
```

### 2) Forgetting `initialize()` after `setDisallowedTools`

BAD:
```typescript
agent.setDisallowedTools(["shell"]);
// changes are NOT applied until initialize() is called
await agent.run("do something");
```

GOOD:
```typescript
agent.setDisallowedTools(["shell"]);
await agent.initialize();
await agent.run("do something");
```

### 3) Not consuming stream events

BAD:
```typescript
agent.streamEvents(prompt);  // generator is created but never iterated — events are lost
```

GOOD:
```typescript
for await (const event of agent.streamEvents(prompt)) {
  handle(event);
}
```

### 4) Assuming structured output streaming only emits one event

BAD:
```typescript
for await (const event of agent.streamEvents(prompt)) {
  if (event.event === "on_structured_output") save(event.data);
  // missing: on_structured_output_progress, on_structured_output_error
}
```

GOOD:
```typescript
for await (const event of agent.streamEvents(prompt)) {
  if (event.event === "on_structured_output_progress") showSpinner();
  else if (event.event === "on_structured_output") save(event.data);
  else if (event.event === "on_structured_output_error") handleError(event.data?.error ?? "Structured output failed");
}
```

### 5) Using deprecated positional string form for `streamEvents()` when a schema is needed

BAD — cannot pass a schema with the plain string form:
```typescript
for await (const event of agent.streamEvents("...")) {
  // no way to attach a schema here
}
```

GOOD — use the options object to include a schema:
```typescript
for await (const event of agent.streamEvents({ prompt: "...", schema: mySchema })) {
  if (event.event === "on_structured_output") {
    const result = mySchema.parse(event.data.output);
  }
}
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Agent doesn't remember previous turns | `memoryEnabled` is `false` | Set `memoryEnabled: true` (it is the default) |
| Tool restriction not applied after `setDisallowedTools` | `initialize()` not called after the update | Call `await agent.initialize()` after updating restrictions |
| Streaming stalls | Generator not iterated | Ensure `for await` loop consumes events |
| Schema not applied in `streamEvents()` | Using deprecated string form instead of options object | Use `agent.streamEvents({ prompt, schema })` options object form |
| Structured output result not found | Reading `event.data` instead of `event.data.output` | Access `event.data.output` for `on_structured_output` events |
| No traces in Langfuse | Env vars not set | Set `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` |
| Langfuse enabled but traces not wanted | Env vars set but tracing should be off | Set `MCP_USE_LANGFUSE=false` or `observe: false` in constructor |
| Unexpected tools available | `disallowedTools` not set | Pass tool names to `disallowedTools` option |
| Agent picks wrong server | `useServerManager` not enabled | Set `useServerManager: true` |

---

## Summary checklist (advanced)

- [ ] `memoryEnabled` set explicitly for stateless agents (default is `true`)
- [ ] `maxSteps` tuned for the workflow depth (default is `5`)
- [ ] `disallowedTools` restricts dangerous or irrelevant tools
- [ ] `initialize()` called after any `setDisallowedTools` update
- [ ] `useServerManager: true` when routing across multiple servers
- [ ] Structured output schema uses `.describe()` annotations for best results
- [ ] All three streaming events handled for structured output
- [ ] Langfuse env vars set and `setMetadata`/`setTags` used for production tracing
- [ ] `client.closeAllSessions()` called on shutdown
