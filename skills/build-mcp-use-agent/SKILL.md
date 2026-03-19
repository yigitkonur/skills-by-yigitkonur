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

**If context exists:** Infer what kind of agent fits and build it. Read `references/guides/quick-start.md` and `references/examples/integration-recipes.md` for the right integration pattern.

**If no context exists:** Ask the user up to 10 questions, each with 5+ concrete options:

1. **What LLM provider?** (OpenAI `gpt-4o`, Anthropic `claude-3-5-sonnet-20241022`, Google `gemini-pro`, Groq `llama-3.3-70b-versatile`, other)
2. **Initialization mode?** (Explicit — hand-built LLM and client, Simplified — `"provider/model"` string shorthand)
3. **What MCP servers to connect?** (filesystem, database, custom stdio, remote HTTP/SSE, none yet)
4. **Output format?** (plain text via `run()`, structured Zod schema, streaming steps, streaming tokens, pretty terminal)
5. **Memory behavior?** (stateful multi-turn conversation, stateless single-shot, manual history injection)
6. **Need observability?** (Langfuse auto-init, Langfuse custom endpoint, custom callbacks, none)
7. **Execution environment?** (CLI script, HTTP handler, serverless function, Next.js route, REPL/chat loop)
8. **Max steps?** (5 default, 10-20 for complex tasks, 30+ for code-mode workflows)
9. **Tool restrictions?** (block dangerous tools via `disallowedTools`, narrow tool set via `toolsUsedNames`, no restrictions)
10. **Advanced needs?** (code mode, server manager for multi-server routing, provider failover, none)

Then build the agent using the quick start patterns below and the relevant references.

## Reference routing — curiosity-driven

Read these when the situation calls for it. Each trigger tells you *why* you would want that file.

| Reference file | When your curiosity should lead you there |
|---|---|
| `references/guides/quick-start.md` | Building a first agent, choosing explicit vs simplified mode, creating a chat loop, or wiring an HTTP route. Start here for any greenfield build. |
| `references/guides/agent-configuration.md` | Choosing between explicit and simplified mode, or wondering what all the constructor options do and their defaults. Has the full `MCPAgentOptions` with accurate defaults (`maxSteps=5`, `autoInitialize=false`, `memoryEnabled=true`). |
| `references/guides/llm-integration.md` | Selecting a provider, using `"provider/model"` string shortcuts, switching providers at runtime, or validating model capabilities. Covers OpenAI, Anthropic, Google, Groq, and custom adapters. |
| `references/guides/streaming.md` | Need streaming? There are 3 methods with very different signatures. `stream()` takes a plain string, `streamEvents()` takes a string or options object, `prettyStreamEvents()` always takes an options object. Read this before implementing — getting the signatures wrong is the #1 streaming mistake. |
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
4. Use object-form `run({ prompt, ... })` for production code.
5. Wrap every agent in `try/finally` with `await agent.close()`.
6. Add streaming only after the non-streaming path works.
7. Add observability after the response path is stable.

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
| `mcpServers` | server config record | — | Inline server config (simplified mode) |
| `maxSteps` | `number` | `5` | Cap on tool-call loops |
| `autoInitialize` | `boolean` | `false` | Pre-connect sessions on construction |
| `memoryEnabled` | `boolean` | `true` | Stateful conversation across turns |
| `systemPrompt` | `string \| null` | `null` | Full prompt override |
| `additionalInstructions` | `string \| null` | `null` | Layer extra behavior on default prompt |
| `disallowedTools` | `string[]` | `[]` | Block dangerous or irrelevant tools |
| `useServerManager` | `boolean` | `false` | Multi-server routing (advanced) |
| `callbacks` | `BaseCallbackHandler[]` | `[]` | Langfuse or custom callback hooks |
| `verbose` | `boolean` | `false` | Debug logging |

### `run()` signatures

| Style | Example | When |
|---|---|---|
| Plain string | `await agent.run("Summarize...")` | Simple one-shot |
| Object form | `await agent.run({ prompt, maxSteps, schema, tags, metadata, signal })` | Production, typed output, cancellation |

### Streaming methods

| Method | Argument | Returns | Best for |
|---|---|---|---|
| `stream(prompt)` | plain string only | `AsyncIterable<AgentStep>` | Step-by-step UIs, logs |
| `streamEvents(prompt)` | string or options object | `AsyncIterable<StreamEvent>` | Token streams, raw events |
| `prettyStreamEvents(options)` | options object always | `AsyncIterable<void>` | ANSI terminal output |

**Critical:** `stream()` takes a plain string only — never pass an object. `streamEvents()` takes either a plain string or `{ prompt, schema?, tags?, metadata?, onStructuredOutput?, ... }` — use the object form for structured output. `prettyStreamEvents()` always takes `{ prompt, maxSteps?, schema?, metadata?, flush?, onComplete?, onError? }`.

#### `AgentStep` type reference

Each step yielded by `stream()` represents one tool-call cycle. `step.observation` is **empty (`""`) when yielded** — tool results are tracked internally.

```typescript
interface AgentStep {
  action: {
    tool: string;            // Tool selected by the agent
    toolInput: Record<string, any>; // Arguments passed to the tool
    log: string;             // LLM reasoning before tool selection
  };
  observation: string;       // Always "" at yield time
}
```

#### `streamEvents()` example

```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const agent = new MCPAgent({ llm: new ChatOpenAI({ model: "gpt-4o" }), client });

for await (const event of agent.streamEvents("Explain the architecture.")) {
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

| Package | Purpose |
|---|---|
| `mcp-use` | `MCPAgent`, `MCPClient`, streaming helpers |
| `@langchain/openai` | `ChatOpenAI` — pair with `OPENAI_API_KEY` |
| `@langchain/anthropic` | `ChatAnthropic` — pair with `ANTHROPIC_API_KEY` |
| `@langchain/google-genai` | `ChatGoogleGenerativeAI` — pair with `GOOGLE_API_KEY` |
| `@langchain/groq` | `ChatGroq` — pair with `GROQ_API_KEY` |
| `zod` | Structured output schemas |
| `langfuse-langchain` | Custom Langfuse endpoint callbacks only |
| `dotenv` | Local dev env loading |

## Provider quick reference

| Provider | Model | String shorthand | Package | Env var |
|---|---|---|---|---|
| OpenAI | `gpt-4o` | `"openai/gpt-4o"` | `@langchain/openai` | `OPENAI_API_KEY` |
| Anthropic | `claude-3-5-sonnet-20241022` | `"anthropic/claude-3-5-sonnet-20241022"` | `@langchain/anthropic` | `ANTHROPIC_API_KEY` |
| Google | `gemini-pro` | `"google/gemini-pro"` | `@langchain/google-genai` | `GOOGLE_API_KEY` |
| Groq | `llama-3.3-70b-versatile` | `"groq/llama-3.3-70b-versatile"` | `@langchain/groq` | `GROQ_API_KEY` |

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
6. `stream()` accepts a plain string only — never pass an options object.
7. `streamEvents()` accepts a plain string or an options object — use the object form when passing `schema` or callbacks.
8. `prettyStreamEvents()` always accepts an options object.
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
| Passing options object to `stream()` | Wrong signature — string only | `agent.stream("prompt")` |
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

## Do / Don't

| Do | Don't |
|---|---|
| Use `mcp-use` imports in all examples | Import from `@modelcontextprotocol/sdk` in agent code |
| Use explicit mode for fine-grained control | Hide important client configuration |
| Use simplified mode for getting-started paths | Combine explicit and simplified in one example |
| Show complete imports and cleanup | Leave readers guessing about packages or shutdown |
| Explain defaults when they matter | Present options without operational guidance |
| Route advanced topics to reference files | Inflate the quick start with every edge case |
| Pass a plain string to `stream()` | Pass `{ prompt: "..." }` to `stream()` |
| Pass options object to `streamEvents()` for schema | Pass plain string when you need structured output |
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
