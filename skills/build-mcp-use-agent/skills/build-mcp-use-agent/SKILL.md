---
name: build-mcp-use-agent
description: Use skill if you are building TypeScript AI agents with mcp-use MCPAgent — configuration, LLM integration, streaming, structured output, observability, and production deployment.
---

# Build MCP Use Agent

Build production-grade TypeScript agents with `MCPAgent` from `mcp-use`. This skill drives both greenfield builds and audits of existing agent code.

## Behavioral flow — what to do when this skill is invoked

### Step 1 — Detect what exists

Run `tree -L 3` or `ls -R` in the user's working directory. Look for signs of an existing mcp-use agent:

- `package.json` with `"mcp-use"` as a dependency
- Files importing `MCPAgent` from `"mcp-use"`
- `MCPAgent` constructor calls
- `agent.run()` / `agent.stream()` / `agent.streamEvents()` usage
- LangChain model imports (`@langchain/openai`, `@langchain/anthropic`, etc.)

### Step 2A — Existing mcp-use agent found

When you find an existing implementation, deploy four parallel subagents to explore and diagnose it. Each subagent must read the relevant reference files and surface three things: what is correct, what is wrong, and what is missing.

If the runtime cannot spawn subagents, do the same four audits sequentially in the order below and keep the same output contract.

**Subagent 1 — Agent configuration audit**
Explore: constructor options, initialization mode (explicit vs simplified), LLM choice and provider, `maxSteps` setting, `autoInitialize`, prompt customization.
Read: `references/guides/agent-configuration.md`, `references/guides/llm-integration.md`

**Subagent 2 — Execution and output audit**
Explore: `run()` / `stream()` / `streamEvents()` / `prettyStreamEvents()` usage, structured output with Zod, memory management, multi-turn behavior.
Read: `references/guides/streaming.md`, `references/guides/structured-output.md`, `references/guides/memory-management.md`

**Subagent 3 — MCP server connections audit**
Explore: `MCPClient` configuration, server definitions, server manager usage, tool exposure settings, resource/prompt exposure.
Read: `references/guides/server-manager.md`, `references/guides/quick-start.md`

**Subagent 4 — Production readiness audit**
Explore: observability (metadata, tags, callbacks, Langfuse), error handling, lifecycle management (`close()`, `flush()`), anti-patterns.
Read: `references/guides/observability.md`, `references/patterns/production-patterns.md`, `references/patterns/anti-patterns.md`, `references/troubleshooting/common-errors.md`

After all subagents report back:

1. Synthesize findings into a prioritized list (critical issues first, then improvements, then nice-to-haves).
2. Apply improvements directly — fix bugs, add missing cleanup, correct wrong signatures, improve configuration.
3. Only ask the user if something is genuinely ambiguous (e.g., which LLM provider they want to switch to).

### Step 2B — No existing mcp-use agent found

Check for context: is there an existing application that could benefit from an agent (e.g., an Express server, a CLI tool, a Next.js app)?

**If context exists:** Infer what kind of agent fits and build it. Read `references/guides/quick-start.md` and `references/examples/integration-recipes.md` for the right integration pattern. If the task is calculator-style and the repo does not already expose calculator tools, use the calculator server section in `references/guides/quick-start.md` before wiring the agent.

**If no context exists:** Ask the user up to 10 questions, each with 5+ concrete options:

1. **What LLM provider?** (OpenAI `gpt-4o`, Anthropic `claude-sonnet-4-6` or `claude-opus-4-7`, Google `gemini-2.5-flash` or `gemini-2.5-pro`, Groq `llama-3.3-70b-versatile`, other)
2. **Initialization mode?** (Explicit — hand-built LLM and client, Simplified — `"provider/model"` string shorthand)
3. **What MCP servers to connect?** (filesystem, database, custom stdio, remote HTTP/SSE, none yet)
4. **Output format?** (plain text via `run()`, structured Zod schema, streaming steps, streaming tokens, pretty terminal)
5. **Memory behavior?** (stateful multi-turn conversation, stateless single-shot, manual history injection)
6. **Need observability?** (Langfuse auto-init, Langfuse custom endpoint, custom callbacks, none)
7. **Execution environment?** (CLI script, HTTP handler, serverless function, Next.js route, REPL/chat loop)
8. **Max steps?** (5 default, 10-20 for complex tasks, 30+ for code-mode workflows)
9. **Tool restrictions?** (block dangerous tools via `disallowedTools`, inject extra tools via `additionalTools`, control resource/prompt surface via `exposeResourcesAsTools` / `exposePromptsAsTools`, no restrictions)
10. **Advanced needs?** (code mode, server manager for multi-server routing, provider failover, none)

Then build the agent using the quick start patterns below and the relevant references.

**Fast default for tiny, well-scoped tasks:** if the task is simple and the working directory already makes the choice obvious, skip the long questionnaire and use these defaults unless the repo says otherwise:

- simplified mode
- `llm: "openai/gpt-4o"`
- `maxSteps: 10`
- `memoryEnabled: false`
- `autoInitialize: true`
- one clearly relevant MCP server only

Before the first `run()` / `stream()` / `streamEvents()` call, verify the provider key and every MCP server command or URL. Fix missing prerequisites first instead of debugging agent logic against a broken runtime.

## Reference routing — curiosity-driven

Read these when the situation calls for it. Each trigger tells you *why* you would want that file.

| Reference file | When your curiosity should lead you there |
|---|---|
| `references/guides/quick-start.md` | Building a first agent, choosing explicit vs simplified mode, creating a chat loop, or wiring an HTTP route. Start here for any greenfield build. |
| `references/guides/agent-configuration.md` | Choosing between explicit and simplified mode, or wondering what all the constructor options do and their defaults. Has the full `MCPAgentOptions` with accurate defaults (`maxSteps=5`, `autoInitialize=false`, `memoryEnabled=true`). |
| `references/guides/llm-integration.md` | Selecting a provider, using `"provider/model"` string shortcuts, switching providers at runtime, or validating model capabilities. Covers OpenAI, Anthropic, Google, Groq, and custom adapters. |
| `references/guides/streaming.md` | Need streaming? There are 3 methods with very different signatures. All 3 accept the newer options-object form, and the plain-string overloads remain as deprecated compatibility helpers. Read this before implementing — getting the signatures wrong is the #1 streaming mistake. |
| `references/guides/structured-output.md` | Structured output with Zod schemas? The return types are `AsyncGenerator`, not `AsyncIterable`. Event payloads use `event.data.output`, not `event.data`. Read this for the correct patterns and the mcp-use-specific events (`on_structured_output`, `on_structured_output_progress`, `on_structured_output_error`). |
| `references/guides/memory-management.md` | Memory behavior matters in chat loops and multi-turn agents. Covers `memoryEnabled`, `clearConversationHistory()`, `getConversationHistory()`, `externalHistory`, and when to disable memory for stateless jobs. |
| `references/guides/server-manager.md` | Multiple MCP servers or dynamic activation. Covers `useServerManager: true`, the 5 built-in management tools, runtime server addition, and when NOT to use it. |
| `references/guides/observability.md` | Traces, callbacks, tags, metadata, and Langfuse. Covers auto-initialization via env vars, `setMetadata()`, `setTags()`, custom callback handlers, and `flush()` in serverless environments. |
| `references/guides/advanced-patterns.md` | Code mode, deep framework integrations, execution-heavy agents, and advanced strategies that go beyond the standard run/stream pattern. |
| `references/patterns/production-patterns.md` | Hardening lifecycle, graceful shutdown, retries, logging, and deployment behavior. Read before shipping to production. |
| `references/patterns/anti-patterns.md` | Reviewing an existing agent for correctness, maintainability, or safety regressions. Use during Step 2A audits. |
| `references/examples/agent-recipes.md` | Copyable end-to-end recipes beyond the quick start — interactive REPL, multi-server, typed output, and more. |
| `references/examples/integration-recipes.md` | Next.js + Vercel AI SDK, Express SSE, React frontend, Langfuse, multi-provider fallback, and dynamic server integrations. |
| `references/troubleshooting/common-errors.md` | When the agent fails to initialize, stream, call tools, or shut down cleanly. Check this before debugging from scratch. |

## Quick start

### Explicit mode

Use when you need full control over the model instance, `MCPClient`, callbacks, or client options like code mode.

```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

// MCPClient accepts a second MCPClientOptions argument for codeMode,
// onSampling, onElicitation, onNotification handlers. Omit it for plain agents.
const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", process.cwd()],
    },
  },
});

const llm = new ChatOpenAI({ model: "gpt-4o", temperature: 0 });

const agent = new MCPAgent({
  llm,
  client,
  maxSteps: 20,
  autoInitialize: true,
});

try {
  const result = await agent.run({
    prompt: "List the top-level files and summarize what each one does.",
  });
  console.log(result);
} finally {
  await agent.close();
}
```

### Simplified mode

Use when you want the shortest correct setup. Pass `llm` as a `"provider/model"` string and `mcpServers` directly on the agent.

```typescript
import { MCPAgent } from "mcp-use";

const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  llmConfig: { temperature: 0 },
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", process.cwd()],
    },
  },
  maxSteps: 20,
  autoInitialize: true,
});

try {
  const result = await agent.run({ prompt: "List the top-level files." });
  console.log(result);
} finally {
  await agent.close();
}
```

### Build sequence

1. Pick explicit mode if you already have a LangChain model instance or need client options.
2. Pick simplified mode for compact scripts and server routes.
3. Set `maxSteps` deliberately — default is 5, which is low for most real tasks.
4. Validate provider env vars and MCP server command/URL before the first execution call.
5. If `autoInitialize` stays `false`, call `await agent.initialize()` or pre-create sessions before `run()` / `stream()` / `streamEvents()`.
6. Use object-form `run({ prompt, ... })` for production code.
7. Wrap every agent in `try/finally` with `await agent.close()`.
8. Add streaming only after the non-streaming path works.
9. Add observability after the response path is stable.

## Core API summary

### Initialization modes

| Mode | Required | When to use | What mcp-use creates for you |
|---|---|---|---|
| Explicit | `llm` (LangChain instance) + `client` or `connectors` | Full control over model, callbacks, client options | Nothing hidden |
| Simplified | `llm` as `"provider/model"` string + `mcpServers` | Shortest working setup | Model instance + client wiring |

### Key constructor options

For the full options table with all defaults, read `references/guides/agent-configuration.md`.

| Option | Type | Default | Purpose |
|---|---|---|---|
| `llm` | LangChain model or `"provider/model"` | required | The LLM to use (must support tool calling) |
| `client` / `connectors` | `MCPClient` / `BaseConnector[]` | — | MCP server connection (explicit mode) |
| `mcpServers` | server config record | — | Inline server config (simplified mode only) |
| `llmConfig` | `LLMConfig` | — | Simplified mode only — `{ apiKey, temperature, maxTokens, topP, ... }` forwarded to the LLM constructor |
| `maxSteps` | `number` | `5` | Cap on tool-call loops |
| `autoInitialize` | `boolean` | `false` | Pre-connect sessions on construction |
| `memoryEnabled` | `boolean` | `true` | Stateful conversation across turns |
| `systemPrompt` | `string \| null` | `null` | Full prompt override |
| `systemPromptTemplate` | `string \| null` | `null` | Override the default prompt template while keeping the tools/instructions scaffolding |
| `additionalInstructions` | `string \| null` | `null` | Layer extra behavior on default prompt |
| `disallowedTools` | `string[]` | `[]` | Block dangerous or irrelevant tools (real access filter) |
| `additionalTools` | `StructuredToolInterface[]` | `[]` | Inject extra LangChain tools alongside MCP-sourced tools |
| `exposeResourcesAsTools` | `boolean` | `true` | Expose MCP resources as callable tools |
| `exposePromptsAsTools` | `boolean` | `true` | Expose MCP prompts as callable tools |
| `useServerManager` | `boolean` | `false` | Multi-server routing (advanced) |
| `serverManagerFactory` | `(client: MCPClient) => ServerManager` | default | Inject a custom `ServerManager` implementation |
| `adapter` | `LangChainAdapter` | default | Override the MCP-tool → LangChain-tool adapter |
| `observe` | `boolean` | `true` | Toggle observability manager wiring; set `false` to skip Langfuse even if env vars are set |
| `callbacks` | `BaseCallbackHandler[]` | `[]` | Langfuse or custom callback hooks |
| `verbose` | `boolean` | `false` | Debug logging |
| `agentId` / `apiKey` / `baseUrl` | strings | — | Switch to **remote mode** — proxies run/stream to an mcp-use remote runtime instead of executing locally (no local LLM or client needed) |
| `toolsUsedNames` | `string[]` | `[]` | Reporting field — seeds the post-run tools-used list. **Not** an access filter; use `disallowedTools` for that |

### `run()` signatures

| Style | Example | When |
|---|---|---|
| Plain string | `await agent.run("Summarize...")` | Simple one-shot (deprecated overload) |
| Object form | `await agent.run({ prompt, maxSteps, manageConnector, externalHistory, schema, signal })` | Production, typed output, cancellation |

`RunOptions` fields: `prompt` (required), `maxSteps`, `manageConnector` (defaults to `true` — pass `false` when the caller owns connector lifetime), `externalHistory` (override conversation history for this call), `schema` (Zod schema for typed output), `signal` (`AbortSignal`). Tags and metadata are **agent-wide**, not per-call — set them via `agent.setTags([...])` and `agent.setMetadata({...})` before calling `run()`.

### Streaming methods

| Method | Argument | Returns | Best for |
|---|---|---|---|
| `stream(...)` | string or options object | `AsyncGenerator<AgentStep, string \| T, void>` | Step-by-step UIs, logs |
| `streamEvents(...)` | string or options object | `AsyncGenerator<StreamEvent, void, void>` | Token streams, raw events |
| `prettyStreamEvents(...)` | string or options object | `AsyncGenerator<void, string, void>` | ANSI terminal output |

**Critical:** Prefer the options-object form for all three streaming methods: `stream({ prompt, maxSteps?, schema?, signal? })`, `streamEvents({ prompt, ... })`, and `prettyStreamEvents({ prompt, ... })`. The plain-string overloads still work, but they are deprecated compatibility paths.

#### `AgentStep` type reference

Each step yielded by `stream()` represents one tool-call cycle. `step.observation` is **empty (`""`) when yielded** — tool results are tracked internally.

```typescript
interface AgentStep {
  action: {
    tool: string;     // Tool selected by the agent
    toolInput: any;   // Arguments passed to the tool (any — could be string, object, etc.)
    log: string;      // LLM reasoning text — often empty in tool-calling agents
  };
  observation: string;  // Always "" at yield time
}
```

`step.action.log` is often empty in tool-calling agents because the model emits the intent through structured tool calls rather than reasoning text. The underlying LangChain runtime sometimes attaches `messageLog: BaseMessage[]` and `toolCallId: string` to the same `action` object — they are not declared on mcp-use's `AgentStep`, so cast to `any` to inspect them. Prefer those for correlating tool calls with `on_tool_start` / `on_tool_end` events emitted by `streamEvents()`. Also: do not `JSON.stringify(step.action.toolInput)` blindly — when it's already a string the result is double-encoded.

#### `streamEvents()` example

```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const agent = new MCPAgent({ llm: new ChatOpenAI({ model: "gpt-4o" }), client });

for await (const event of agent.streamEvents({ prompt: "Explain the architecture." })) {
  if (event.event === "on_chat_model_stream") {
    const text = event.data?.chunk?.text ?? event.data?.chunk?.content;
    if (typeof text === "string") process.stdout.write(text);
  }
}
```

#### Key `streamEvents` event types

| Event | Description | Payload |
|---|---|---|
| `on_chat_model_stream` | Every LLM token | `event.data?.chunk?.text` or `.content` |
| `on_tool_start` | Tool about to be called | `event.name`, `event.data.input` |
| `on_tool_end` | Tool finished | `event.name`, `event.data.output` |
| `on_chain_start` / `on_chain_end` | Agent loop lifecycle | `event.name`, `event.data.output` |
| `on_structured_output_progress` | Schema conversion progress (mcp-use specific) | — |
| `on_structured_output` | Structured output ready (mcp-use specific) | `event.data` |
| `on_structured_output_error` | Schema conversion failed (mcp-use specific) | `event.data` |

### Lifecycle methods

| Method | Purpose | When |
|---|---|---|
| `initialize()` | Pre-connect sessions | After dynamic config changes |
| `close()` | Graceful cleanup | Always in `finally` |
| `flush()` | Send buffered traces | Before `close()` in serverless |
| `clearConversationHistory()` | Reset memory | Between unrelated turns |
| `setDisallowedTools(tools)` | Update tool restrictions | Runtime policy changes |
| `setMetadata(metadata)` | Attach trace metadata | Langfuse, request correlation |
| `setTags(tags)` | Group and filter traces | Observability queries |

### Langfuse auto-initialization

When `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` env vars are set, mcp-use auto-initializes Langfuse tracing. No manual `CallbackHandler` import needed. Only use explicit `callbacks` for custom Langfuse endpoints.

### `flush()` + `close()` in serverless

In serverless environments (Next.js API routes, Lambda, Cloud Functions), always flush before closing to ensure traces reach the backend:

```typescript
try {
  const result = await agent.run({ prompt: "Inspect the repository." });
  return result;
} finally {
  await agent.flush();   // send buffered traces
  await agent.close();   // clean up sessions
}
```

### Code mode note

`codeMode` is configured on `MCPClient`, not on `MCPAgent`. When the task involves code execution, wire the client first:

```typescript
const client = new MCPClient(
  { mcpServers: { /* ... */ } },
  { codeMode: true }
);
const agent = new MCPAgent({ llm, client, maxSteps: 30 });
```

For advanced code-mode patterns, read `references/guides/advanced-patterns.md`.

### Companion packages

`mcp-use@1.25.0` requires LangChain v1 and Zod v4 as peers. The full `mcp-use` surface includes: `MCPAgent`, `MCPClient`, `MCPSession`, `RemoteAgent`, connector classes (`StdioConnector`, `HttpConnector`, `BaseConnector`), `loadConfigFile`, `ServerManager`, `ObservabilityManager`, `Telemetry`, OAuth helpers (`BrowserOAuthClientProvider`, `onMcpAuthorization`, `probeAuthParams`), code-execution ancillaries (`BaseCodeExecutor`, `E2BCodeExecutor`, `VMCodeExecutor`), elicitation helpers (`accept`, `decline`, `reject`, `validate`), and `PROMPTS`.

#### Declared peer dependencies

| Package | Required version | Purpose |
|---|---|---|
| `@langchain/core` | `^1.1.0` | LangChain v1 core types and message classes |
| `@langchain/openai` | `^1.2.0` | `ChatOpenAI` — pair with `OPENAI_API_KEY` |
| `@langchain/anthropic` | `^1.3.0` | `ChatAnthropic` — pair with `ANTHROPIC_API_KEY` |
| `langchain` | `^1.2.10` | LangChain v1 runtime |
| `langfuse`, `langfuse-langchain` | `^3.38.6` | Observability (auto-init when env vars set) |
| `zod` | **`^4.0.0`** | Structured-output schemas (Zod v4 required) |
| `@e2b/code-interpreter` | `^2.2.0` | Code-execution sandbox |
| `react`, `react-router` | `^18 || ^19`, `^7.12.0` | React widget exports |

All `@langchain/*`, `langchain`, `langfuse`, `langfuse-langchain`, and `@e2b/code-interpreter` are marked optional in `peerDependenciesMeta` — install only the providers you actually use. `zod`, `react`, and `react-router` are strictly required.

#### Optional LLM adapters (NOT peer-declared)

| Package | Purpose | Note |
|---|---|---|
| `@langchain/google-genai` | `ChatGoogleGenerativeAI` — `GOOGLE_API_KEY` | Not a peer dep — install only if using Gemini |
| `@langchain/groq` | `ChatGroq` — `GROQ_API_KEY` | Not a peer dep — install only if using Groq |

Both must remain LangChain v1 compatible. The `"google/..."` and `"groq/..."` simplified-mode shorthands fail at runtime if the matching adapter is missing.

#### Other helpers

| Package | Purpose |
|---|---|
| `dotenv` | Local dev env loading |

If your codebase is on LangChain v0.x or Zod v3, plan the upgrade before adopting `mcp-use@1.25.0` — peer-dep mismatches surface as runtime tool-calling failures and JSON-schema serialization bugs.

## Provider quick reference

| Provider | Model | String shorthand | Package | Peer? | Env var |
|---|---|---|---|---|---|
| OpenAI | `gpt-4o` | `"openai/gpt-4o"` | `@langchain/openai` | peer (optional) | `OPENAI_API_KEY` |
| Anthropic | `claude-sonnet-4-6` | `"anthropic/claude-sonnet-4-6"` | `@langchain/anthropic` | peer (optional) | `ANTHROPIC_API_KEY` |
| Google | `gemini-2.5-flash` | `"google/gemini-2.5-flash"` | `@langchain/google-genai` | NOT a peer dep | `GOOGLE_API_KEY` |
| Groq | `llama-3.3-70b-versatile` | `"groq/llama-3.3-70b-versatile"` | `@langchain/groq` | NOT a peer dep | `GROQ_API_KEY` |

`@langchain/google-genai` and `@langchain/groq` are not declared peers of `mcp-use@1.25.0`; install them separately if you use those providers. Anthropic models: prefer `claude-opus-4-7` for deep reasoning, `claude-sonnet-4-6` for general MCP-agent workloads. Verify Google and Groq model IDs against their respective consoles before shipping — model IDs are deprecated frequently.

For full provider details, failover, and custom adapters, read `references/guides/llm-integration.md`.

## Server manager quick reference

When `useServerManager: true` is set, the agent gains five built-in management tools:

| Tool | Purpose |
|---|---|
| `list_mcp_servers` | List configured servers and their tools |
| `connect_to_mcp_server` | Activate a server and load its tools |
| `get_active_mcp_server` | Check the currently connected server |
| `disconnect_from_mcp_server` | Deactivate and remove tools |
| `add_mcp_server_from_config` | Register a new server at runtime |

For dynamic server switching and multi-server patterns, read `references/guides/server-manager.md`.

## Rules

1. Use `import { MCPAgent, MCPClient } from "mcp-use"` — never import from `@modelcontextprotocol/sdk` in agent code.
2. Set `maxSteps` intentionally; explain the chosen value.
3. Close the agent with `await agent.close()` in `try/finally` in every example.
4. Put secrets in environment variables, never string literals.
5. Use object-form `run()` in production code and typed flows.
6. Prefer the options-object form for `stream()`, `streamEvents()`, and `prettyStreamEvents()`; the plain-string overloads still exist but are deprecated.
7. Use the object form whenever you need `schema`, `maxSteps`, `signal`, or other per-call controls.
8. `prettyStreamEvents()` also has a deprecated plain-string overload, but the object form is the stable shape to document and extend.
9. `step.observation` is always empty at yield time — never claim it contains tool output.
10. Call `flush()` before `close()` in serverless environments.
11. Langfuse auto-initializes via env vars — do not manually wire `CallbackHandler` unless using a custom endpoint.
12. Call `client.closeAllSessions()` when managing client lifetime separately from the agent.
13. `codeMode` is configured on `MCPClient`, not on `MCPAgent`.
14. Treat `useServerManager` as advanced — do not enable by default.
15. Explain memory behavior whenever showing multi-turn code.
16. Check both `chunk.text` and `chunk.content` for cross-provider streaming compatibility.
17. Use mcp-use structured output events (`on_structured_output`, `on_structured_output_progress`, `on_structured_output_error`) — not generic LangChain events.

## Common pitfalls

| Pitfall | Why it fails | Fix |
|---|---|---|
| Missing `await agent.close()` | Sessions and sandboxes stay open | `try/finally` in every example |
| Mixing explicit and simplified mode | Internally inconsistent code | Pick one mode |
| Assuming `stream()` rejects options objects | Published `mcp-use` types accept `RunOptions` | Prefer `agent.stream({ prompt, maxSteps, schema, signal })` |
| Passing plain string to `streamEvents()` with schema | No way to pass `schema` or callbacks | Use object form: `agent.streamEvents({ prompt, schema })` |
| Reading `step.observation` during streaming | Always empty at yield time | Log only `step.action.tool` and `step.action.toolInput` |
| Leaving `maxSteps` at default 5 | Agent stops too early on real tasks | Set explicitly per workload |
| Claiming `codeMode` is an agent option | It belongs on `MCPClient` | Configure the client, pass to agent |
| Hard-coding API keys | Unsafe to copy | Use `.env` and `process.env` |
| Omitting `flush()` in serverless | Traces lost on process exit | `await agent.flush()` then `await agent.close()` |
| Checking only `chunk.text` or `chunk.content` | Breaks across providers | Check both: `event.data?.chunk?.text ?? event.data?.chunk?.content` |
| Manual `CallbackHandler` for basic Langfuse | Unnecessary boilerplate | Use env var auto-initialization |
| Enabling `useServerManager` by default | Adds complexity to simple agents | Enable only for multi-server routing |
| Forgetting `client.closeAllSessions()` | Orphaned server processes | Call in `finally` when you own the client |
| Passing `tags` / `metadata` inside `RunOptions` | Not fields of `RunOptions` — TypeScript rejects them, Langfuse never receives them | Use `agent.setTags([...])` / `agent.setMetadata({...})` once, before `run()` |
| Using `toolsUsedNames` to narrow allowed tools | It is a reporting field populated as the agent runs, not an access filter | Use `disallowedTools` to remove tools, `additionalTools` to add, `exposeResourcesAsTools` / `exposePromptsAsTools` for the resource/prompt surface |

## Do / Don't

| Do | Don't |
|---|---|
| Use `mcp-use` imports in all examples | Import from `@modelcontextprotocol/sdk` in agent code |
| Use explicit mode for fine-grained control | Hide important client configuration |
| Use simplified mode for getting-started paths | Combine explicit and simplified in one example |
| Show complete imports and cleanup | Leave readers guessing about packages or shutdown |
| Explain defaults when they matter | Present options without operational guidance |
| Route advanced topics to reference files | Inflate the quick start with every edge case |
| Pass `{ prompt: "..." }` to `stream()` | Default to the deprecated plain-string form |
| Pass options object to `streamEvents()` when you need schema or extensibility | Use plain string when you need structured output or callbacks |
| Call `flush()` before `close()` in serverless | Skip `flush()` and lose traces |
| Rely on Langfuse auto-init via env vars | Manually wire `CallbackHandler` for basic tracing |
| Call `client.closeAllSessions()` when owning client | Leave server processes running |

## Minimal reading sets

### "I need a minimal agent now"
- `references/guides/quick-start.md`
- `references/guides/llm-integration.md`

### "I need to choose constructor options"
- `references/guides/agent-configuration.md`
- `references/guides/quick-start.md`

### "I need streaming output"
- `references/guides/streaming.md`
- `references/examples/integration-recipes.md`

### "I need structured output"
- `references/guides/structured-output.md`
- `references/guides/streaming.md`

### "I need observability and production safety"
- `references/guides/observability.md`
- `references/patterns/production-patterns.md`
- `references/patterns/anti-patterns.md`

### "I need advanced execution or code mode"
- `references/guides/agent-configuration.md`
- `references/guides/advanced-patterns.md`
- `references/examples/agent-recipes.md`

### "Something is broken"
- `references/troubleshooting/common-errors.md`
- `references/patterns/anti-patterns.md`

## Guardrails

- Do not import MCP SDK primitives directly — use `mcp-use`.
- Do not omit cleanup from long-lived examples.
- Do not describe `codeMode` as an `MCPAgent` constructor field.
- Do not recommend raw `streamEvents()` when `prettyStreamEvents()` or `stream()` suffices.
- Do not leave `maxSteps` unexplained in production examples.
- Do not hard-code secrets in copyable snippets.
- Do not enable `useServerManager` by default.
- Do not answer with thin pseudo-code when runnable TypeScript is needed.
- Do not add new reference files unless a topic cannot fit the routed structure.
- Do not break the header and routing conventions of sibling `build-mcp-use-*` skills.
