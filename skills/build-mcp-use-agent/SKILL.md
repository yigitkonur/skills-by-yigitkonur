---
name: build-mcp-use-agent
description: Use skill if you are building TypeScript AI agents with the mcp-use MCPAgent class — LLM integration, tool calling via MCP servers, memory management, streaming, structured output, observability, server manager, code mode, remote execution, and Vercel AI SDK integration.
---

# Build MCP Use Agent

Build AI agents that connect any LLM to MCP tools using the `mcp-use` TypeScript library (v1.21+, Node 22 LTS). `MCPAgent` wraps LangChain-compatible LLMs with automatic MCP server connectivity, tool discovery, conversation memory, structured output via Zod schemas, three streaming modes (`stream`, `streamEvents`, `prettyStreamEvents`), dynamic server management, code execution mode, Langfuse observability, and Vercel AI SDK integration. Supports both **explicit mode** (pre-built LLM + MCPClient) and **simplified mode** (string `"provider/model"` + inline `mcpServers` config).

## Decision tree

```
What do you need?
│
├── New agent from scratch
│   ├── Minimal one-shot agent ───────────► Quick start (below) + references/guides/quick-start.md
│   ├── Simplified mode (string LLM) ─────► Quick start (simplified) + references/guides/quick-start.md
│   └── Interactive chat loop ────────────► references/examples/agent-recipes.md — chat example
│
├── LLM integration
│   ├── OpenAI (ChatOpenAI) ──────────────► references/guides/llm-integration.md — explicit mode
│   ├── Anthropic (ChatAnthropic) ────────► references/guides/llm-integration.md — explicit mode
│   ├── Google (ChatGoogleGenerativeAI) ──► references/guides/llm-integration.md — explicit mode
│   ├── Groq (ChatGroq) ──────────────────► references/guides/llm-integration.md — explicit mode
│   └── String format ("provider/model") ─► references/guides/llm-integration.md — simplified mode
│
├── Agent configuration
│   ├── Constructor options ──────────────► references/guides/agent-configuration.md — full MCPAgentOptions interface
│   ├── System prompt customization ──────► references/guides/agent-configuration.md — systemPrompt, systemPromptTemplate
│   ├── Tool access control ──────────────► references/guides/agent-configuration.md — disallowedTools, setDisallowedTools()
│   └── Runtime config changes ───────────► references/guides/agent-configuration.md — setDisallowedTools(), setMetadata()
│
├── Memory management
│   ├── Enable/disable memory ────────────► references/guides/memory-management.md — memoryEnabled option
│   ├── Inspect conversation history ─────► references/guides/memory-management.md — getConversationHistory()
│   └── Clear/reset memory ──────────────► references/guides/memory-management.md — clearConversationHistory()
│
├── Streaming
│   ├── Step-by-step (agent.stream) ──────► references/guides/streaming.md — AsyncGenerator<AgentStep>
│   ├── Token-level (streamEvents) ───────► references/guides/streaming.md — on_chat_model_stream events
│   ├── Pretty CLI (prettyStreamEvents) ──► references/guides/streaming.md — auto-formatted ANSI output
│   └── Vercel AI SDK integration ────────► references/guides/streaming.md — streamEventsToAISDK utilities
│
├── Structured output
│   ├── Zod schema validation ────────────► references/guides/structured-output.md — schema param in run()
│   ├── Schema-aware streaming ───────────► references/guides/structured-output.md — on_structured_output events
│   └── Retry on validation failure ──────► references/guides/structured-output.md — automatic 3x retry
│
├── Server management
│   ├── Single server setup ──────────────► references/guides/server-manager.md — MCPClient basics
│   ├── Multi-server orchestration ───────► references/guides/server-manager.md — useServerManager: true
│   ├── Dynamic server addition ──────────► references/guides/server-manager.md — add_mcp_server_from_config
│   └── HTTP/SSE remote servers ──────────► references/guides/server-manager.md — url-based config
│
├── Observability
│   ├── Verbose logging ──────────────────► references/guides/observability.md — verbose: true
│   ├── Langfuse tracing ────────────────► references/guides/observability.md — env vars + auto-init
│   ├── Custom metadata & tags ───────────► references/guides/observability.md — setMetadata(), setTags()
│   └── Custom callback handlers ─────────► references/guides/observability.md — callbacks option
│
├── Advanced patterns
│   ├── Code execution mode ──────────────► references/guides/advanced-patterns.md — codeMode, PROMPTS.CODE_MODE
│   ├── Remote agent execution ───────────► references/guides/advanced-patterns.md — RemoteAgent class
│   ├── Vercel AI SDK API routes ─────────► references/guides/advanced-patterns.md — createTextStreamResponse
│   ├── Custom server manager factory ────► references/guides/advanced-patterns.md — serverManagerFactory
│   └── Additional custom tools ──────────► references/guides/advanced-patterns.md — additionalTools option
│
├── Production patterns
│   ├── Error handling & retries ─────────► references/patterns/production-patterns.md — maxRetries, graceful shutdown
│   ├── Resource cleanup ─────────────────► references/patterns/production-patterns.md — agent.close(), try/finally
│   └── Multi-provider fallback ──────────► references/patterns/production-patterns.md — provider switching
│
├── Debugging & errors
│   ├── Common agent errors ──────────────► references/troubleshooting/common-errors.md — tool failures, LLM issues
│   └── Anti-patterns ───────────────────► references/patterns/anti-patterns.md — memory leaks, missing cleanup
│
└── Complete examples
    ├── Working agent recipes ────────────► references/examples/agent-recipes.md — chat, filesystem, browser, multi-server
    └── Integration examples ─────────────► references/examples/integration-recipes.md — AI SDK, Langfuse, code mode
```

## Quick start

### Explicit mode (full control)

```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "./"],
    },
  },
});

const llm = new ChatOpenAI({ model: "gpt-4o" });

const agent = new MCPAgent({ llm, client, maxSteps: 30 });

const result = await agent.run({ prompt: "List files in the current directory" });
console.log(result);

await agent.close();
```

### Simplified mode (zero-boilerplate)

```typescript
import { MCPAgent } from "mcp-use";

const agent = new MCPAgent({
  llm: "openai/gpt-4o",            // "provider/model" string
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "./"],
    },
  },
  maxSteps: 30,
});

const result = await agent.run("What files are here?");
console.log(result);
await agent.close();
```

## Core API

### MCPAgent constructor

Two initialization modes — **explicit** and **simplified**:

```typescript
// Explicit mode — you create the LLM and client yourself
const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),  // LangChain chat model instance
  client: myMCPClient,                        // pre-configured MCPClient
  // --- common options ---
  maxSteps: 30,                               // max tool-calling cycles (default: 5)
  autoInitialize: true,                       // auto-call initialize() (default: false)
  memoryEnabled: true,                        // conversation memory (default: true)
  systemPrompt: "You are a helpful assistant", // custom system prompt
  systemPromptTemplate: null,                 // template with {tool_descriptions} placeholder
  additionalInstructions: "Be concise",       // appended to system prompt
  disallowedTools: ["dangerous_tool"],        // tool blocklist
  additionalTools: [],                        // extra StructuredToolInterface[]
  useServerManager: false,                    // dynamic multi-server routing (default: false)
  verbose: false,                             // detailed logging (default: false)
  observe: true,                              // observability integration (default: true)
  callbacks: [],                              // LangChain callback handlers
  exposeResourcesAsTools: true,               // make resources callable as tools (default: true)
  exposePromptsAsTools: true,                 // make prompts callable as tools (default: true)
});

// Simplified mode — agent creates LLM and client internally
const agent = new MCPAgent({
  llm: "openai/gpt-4o",                      // "provider/model" string
  llmConfig: { temperature: 0.7 },            // optional LLM config overrides
  mcpServers: {                               // inline server definitions
    myserver: { command: "npx", args: ["@my/server"] },
  },
  // ... same common options as above
});
```

### Supported LLM string formats

| String | Provider | Package |
|--------|----------|---------|
| `"openai/gpt-4o"` | OpenAI | `@langchain/openai` |
| `"anthropic/claude-3-5-sonnet-20241022"` | Anthropic | `@langchain/anthropic` |
| `"google/gemini-pro"` | Google | `@langchain/google-genai` |
| `"groq/llama-3.1-70b-versatile"` | Groq | `@langchain/groq` |

### MCPClient configuration

```typescript
const client = new MCPClient({
  mcpServers: {
    serverName: {
      command: "npx",           // executable
      args: ["@pkg/server"],    // CLI arguments
      env: { KEY: "value" },    // environment variables
    },
    remoteServer: {
      url: "https://my-mcp.example.com/mcp",  // HTTP/SSE endpoint
      headers: { "Authorization": "Bearer token" },
      transport: "http",         // "http" | "sse"
    },
  },
});
```

### Public methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `run` | `run(prompt: string \| RunOptions): Promise<any>` | Execute agent, return final result |
| `stream` | `stream(prompt, opts?): AsyncGenerator<AgentStep>` | Yield each tool-call step |
| `streamEvents` | `streamEvents(prompt, opts?): AsyncGenerator<StreamEvent>` | Low-level LangChain events |
| `prettyStreamEvents` | `prettyStreamEvents(opts): AsyncGenerator<void>` | Auto-formatted CLI output |
| `close` | `close(): Promise<void>` | Shut down agent + server connections |
| `initialize` | `initialize(): Promise<void>` | Manually create sessions (if not auto) |
| `clearConversationHistory` | `clearConversationHistory(): void` | Reset memory |
| `getConversationHistory` | `getConversationHistory(): BaseMessage[]` | Get current memory |
| `setMetadata` | `setMetadata(meta: Record<string, any>): void` | Attach observability metadata |
| `setTags` | `setTags(tags: string[]): void` | Attach observability tags |
| `setDisallowedTools` | `setDisallowedTools(tools: string[]): void` | Update tool blocklist |
| `getDisallowedTools` | `getDisallowedTools(): string[]` | Get current blocklist |

### RunOptions interface

```typescript
interface RunOptions<T = string> {
  prompt: string;              // the user query
  maxSteps?: number;           // override constructor maxSteps
  schema?: ZodSchema<T>;       // Zod schema for structured output
  manageConnector?: boolean;   // auto-manage connector lifecycle
  externalHistory?: BaseMessage[];  // inject external conversation history
  signal?: AbortSignal;        // abort signal for request cancellation
}
```

### Streaming patterns

```typescript
// 1. Step-by-step streaming — yields AgentStep { action, observation }
for await (const step of agent.stream("Analyze the codebase")) {
  console.log(`Tool: ${step.action.tool}`);
  console.log(`Input: ${JSON.stringify(step.action.toolInput)}`);
  console.log(`Result: ${step.observation}`);
}

// 2. Token-level streaming — raw LangChain events
for await (const event of agent.streamEvents("Generate a report")) {
  if (event.event === "on_chat_model_stream") {
    process.stdout.write(event.data?.chunk?.text ?? "");
  }
}

// 3. Pretty CLI streaming — auto-styled ANSI output
for await (const _ of agent.prettyStreamEvents({
  prompt: "Build a summary",
  maxSteps: 20,
})) {
  // output formatted automatically
}
```

### Structured output

```typescript
import { z } from "zod";

const WeatherSchema = z.object({
  city: z.string().describe("City name"),
  temperature: z.number().describe("Temperature in Celsius"),
  condition: z.string().describe("Weather condition"),
});

// Via run()
const weather = await agent.run({
  prompt: "Get weather in San Francisco",
  schema: WeatherSchema,
});
console.log(weather.city, weather.temperature); // fully typed

// Via streamEvents() — listen for structured output events
for await (const event of agent.streamEvents("Get weather", 50, true, [], WeatherSchema)) {
  if (event.event === "on_structured_output") {
    const parsed = WeatherSchema.parse(event.data.output);
    console.log(parsed);
  }
  if (event.event === "on_structured_output_progress") {
    console.log("Converting...");
  }
  if (event.event === "on_structured_output_error") {
    console.error("Conversion failed");
  }
}
```

### Memory management

```typescript
// Memory enabled by default (memoryEnabled: true)
const agent = new MCPAgent({ llm, client, memoryEnabled: true });

await agent.run("My name is Alice");
await agent.run("What's my name?"); // → "Alice" (remembered)

// Inspect history
const history = agent.getConversationHistory();
history.forEach(msg => console.log(msg.constructor.name, msg.content));

// Clear memory
agent.clearConversationHistory();

// Stateless mode
const stateless = new MCPAgent({ llm, client, memoryEnabled: false });
```

### Server Manager (multi-server orchestration)

```typescript
const agent = new MCPAgent({
  llm, client,
  useServerManager: true,  // enables dynamic server switching
  verbose: true,
});

// Agent auto-discovers and switches between servers using these built-in tools:
// - list_mcp_servers() → available server identifiers
// - connect_to_mcp_server(id) → activate server, load its tools
// - get_active_mcp_server() → current active server
// - disconnect_from_mcp_server() → deactivate current
// - add_mcp_server_from_config(id, config) → add server at runtime
```

### Observability

```typescript
// 1. Verbose logging
const agent = new MCPAgent({ llm, client, verbose: true });

// 2. Langfuse auto-integration (set env vars)
// LANGFUSE_PUBLIC_KEY=pk-lf-...
// LANGFUSE_SECRET_KEY=sk-lf-...

// 3. Custom metadata and tags
agent.setMetadata({ agent_id: "support-01", environment: "production" });
agent.setTags(["customer-support", "high-priority"]);

// 4. Custom Langfuse callback
import { CallbackHandler } from "langfuse-langchain";
const agent = new MCPAgent({
  llm, client,
  callbacks: [new CallbackHandler({ publicKey: "...", secretKey: "..." })],
});
```

### RemoteAgent (cloud execution)

```typescript
import { RemoteAgent } from "mcp-use";

const remote = new RemoteAgent({
  agentId: "agent-abc-123",
  apiKey: process.env.MCP_USE_API_KEY,   // or set env var
  baseUrl: "https://cloud.mcp-use.com",  // default
});

const result = await remote.run({ prompt: "Analyze data", maxSteps: 20 });
// Supports structured output via schema option
await remote.close();
```

### Code execution mode

```typescript
import { MCPAgent, PROMPTS } from "mcp-use";

const client = new MCPClient(config, { codeMode: true }); // enable code mode on client

const agent = new MCPAgent({
  llm,
  client,
  systemPrompt: PROMPTS.CODE_MODE,  // specialized prompt for code execution
  maxSteps: 50,
});

for await (const _ of agent.prettyStreamEvents("Process the data files")) {
  // code execution with syntax-highlighted output
}
```

## Key types

```typescript
// Agent options — union of explicit and simplified modes
type MCPAgentOptions = ExplicitModeOptions | SimplifiedModeOptions;

// Explicit mode: pass LLM instance + optional client/connectors
interface ExplicitModeOptions extends CommonAgentOptions {
  llm: LanguageModel;        // any LangChain chat model
  client?: MCPClient;
  connectors?: BaseConnector[];
}

// Simplified mode: pass LLM string + inline server config
interface SimplifiedModeOptions extends CommonAgentOptions {
  llm: string;               // "provider/model" format
  llmConfig?: LLMConfig;
  mcpServers: Record<string, MCPServerConfig>;
}

// LLM config for simplified mode
interface LLMConfig {
  apiKey?: string;
  temperature?: number;
  maxTokens?: number;
  topP?: number;
  [key: string]: any;
}

// Server config for simplified mode
interface MCPServerConfig {
  command?: string;
  args?: string[];
  env?: Record<string, string>;
  url?: string;
  headers?: Record<string, string>;
  transport?: "http" | "sse";
  auth_token?: string;         // authentication token (snake_case variant)
  authToken?: string;          // authentication token (camelCase variant)
  preferSse?: boolean;         // prefer SSE transport
}

// Supported LLM providers
type LLMProvider = "openai" | "anthropic" | "google" | "groq";
```

## Important conventions

1. **Always close the agent** — call `await agent.close()` or `await client.closeAllSessions()` in a `finally` block.
2. **Install provider packages** — `@langchain/openai`, `@langchain/anthropic`, `@langchain/google-genai`, or `@langchain/groq` depending on which LLM you use.
3. **Set API keys** — via env vars (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.) or `llmConfig.apiKey`.
4. **Prefer simplified mode** for quick scripts; use explicit mode when you need custom MCPClient configuration.
5. **Use `maxSteps`** to prevent runaway agent loops — set it proportional to task complexity.
6. **Memory is enabled by default** — set `memoryEnabled: false` for stateless one-shot tasks.
7. **Import from `mcp-use`** — the main package exports `MCPAgent`, `MCPClient`, `RemoteAgent`, `Logger`, `PROMPTS`.
