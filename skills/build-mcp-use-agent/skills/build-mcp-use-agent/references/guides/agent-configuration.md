# Agent Configuration

Use this guide when you need precise control over `MCPAgent` construction, runtime mutators, prompt customization, tool restrictions, memory behavior, and initialization.

---

## Configuration mental model

Configure an `MCPAgent` in three layers.

1. Pick the startup mode.
2. Set agent behavior options.
3. Apply runtime mutators only when the agent is already alive and you need to adjust behavior between calls.

Use this file when the question is not "how do I start?" but rather "which option controls this behavior, what is the default, and what tradeoff does it imply?"

## Explicit mode vs simplified mode

| Mode | Required fields | Best for | Main tradeoff |
|---|---|---|---|
| Explicit | `llm` (LangChain model instance), plus `client` or `connectors` | Maximum control, custom clients, observability-heavy setup | More code at bootstrap |
| Simplified | `llm` (a `"provider/model"` string), `mcpServers` | Short scripts, demos, runtime model selection from config | Agent creates the MCPClient internally; less direct lifecycle control |

In simplified mode the agent creates its own `MCPClient` from the `mcpServers` map and resolves the LLM from the string identifier. In explicit mode you own both objects.

## Full `MCPAgent` constructor reference

Treat the following tables as the canonical option inventory for this skill.

### Common options (both modes)

| Option | Type | Default | What it controls | Use it when | Common mistake |
|---|---|---|---|---|---|
| `maxSteps` | `number` | `5` | Maximum tool/planning cycles per call | The task is multi-step or you need a tighter ceiling | Leaving it too low for complex tasks |
| `autoInitialize` | `boolean` | `false` | Whether sessions initialize immediately after construction | You want startup failures to happen early | Forgetting that lazy init can hide config problems |
| `memoryEnabled` | `boolean` | `true` | Whether prior turns remain in agent memory | Building chat loops or disabling state intentionally | Forgetting the default is stateful |
| `systemPrompt` | `string \| null` | `null` | Full custom system prompt replacing the default instruction set | You need a strong persona or strict workflow override | Overriding too much when `additionalInstructions` is enough |
| `systemPromptTemplate` | `string \| null` | `null` | Template string for generating a system prompt dynamically | You want a stable format with injected placeholders | Not documenting placeholders clearly |
| `additionalInstructions` | `string \| null` | `null` | Extra guidance appended to the system prompt | You need narrower task-specific behavior | Using it for giant prompt rewrites |
| `disallowedTools` | `string[]` | `[]` | Tool blocklist — agent will not expose these tools | You must forbid risky or irrelevant tools | Blocking tools without re-initializing to apply changes |
| `useServerManager` | `boolean` | `false` | Dynamic multi-server routing via Server Manager | Multiple servers need explicit activation or switching | Enabling it for single-server setups |
| `verbose` | `boolean` | `false` | Detailed logging of Server Manager actions | Debugging multi-server flows | Leaving it on in production |
| `observe` | `boolean` | `true` | Enable observability callbacks | Tracing and monitoring | Disabling it accidentally in production |
| `exposeResourcesAsTools` | `boolean` | `true` | Expose MCP resources as callable tools | Controlling the agent's visible surface | Unexpectedly hiding resources |
| `exposePromptsAsTools` | `boolean` | `true` | Expose MCP prompts as callable tools | Controlling the agent's visible surface | Unexpectedly hiding prompts |

### Explicit-mode-only fields

| Option | Type | Required | What it does | Use it when |
|---|---|---|---|---|
| `llm` | any LangChain-compatible chat model instance | yes | Supplies the language model | You need provider-specific construction or runtime switching logic |
| `client` | `MCPClient` | one of `client`/`connectors` | Supplies the already-created client | You want explicit control over client construction |
| `connectors` | `BaseConnector[]` | one of `client`/`connectors` | Supplies connection objects instead of a ready client | Your local integration pattern is connector-driven |

### Simplified-mode-only fields

| Option | Type | Required | What it does | Use it when |
|---|---|---|---|---|
| `llm` | `string` (`"provider/model"`) | yes | String identifier resolved to a LangChain model | You want compact setup without manual imports |
| `mcpServers` | `Record<string, MCPServerConfig>` | yes | Server map — the agent creates the `MCPClient` internally | Short scripts, demos, config-driven provider selection |
| `llmConfig` | `LLMConfig` | no | Extra options forwarded to the LLM constructor (temperature, maxTokens, apiKey, etc.) | You need to tune generation without explicit model construction |

## Full setup example: explicit mode

```typescript
import "dotenv/config";
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

const llm = new ChatOpenAI({
  model: "gpt-4o",
  temperature: 0,
});

const agent = new MCPAgent({
  llm,
  client,
  maxSteps: 20,
  autoInitialize: true,
  memoryEnabled: true,
  additionalInstructions: "Verify tool output before concluding.",
  disallowedTools: ["delete_file"],
});
```

## Full setup example: simplified mode

In simplified mode you pass `llm` as a `"provider/model"` string and `mcpServers` directly to the constructor. The agent builds the `MCPClient` and the LangChain model internally.

```typescript
import "dotenv/config";
import { MCPAgent } from "mcp-use";

const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  llmConfig: {
    temperature: 0,
    maxTokens: 2048,
    apiKey: process.env.OPENAI_API_KEY,
  },
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", process.cwd()],
    },
  },
  maxSteps: 20,
  autoInitialize: true,
  memoryEnabled: false,
});

try {
  const result = await agent.run({
    prompt: "List all TypeScript files.",
  });
  console.log(result);
} finally {
  await agent.close();
}
```

Do not pass `client` in simplified mode — the agent creates its own. Conversely, do not use `mcpServers` in explicit mode (pass `client` or `connectors` instead).

## Option family: `maxSteps`

Use `maxSteps` to control the maximum number of reasoning or tool cycles the agent may take per call.

### Tuning guide

| Workload | Suggested range | Why |
|---|---|---|
| Simple one-shot summary | `5-8` | One or two tool calls are usually enough |
| Typical repo inspection | `10-20` | The model may need several inspections |
| Multi-tool workflows | `20-40` | More room for planning and retries |
| Large orchestration flows | `30-50` | Only if the tools and prompt genuinely justify it |

### Practical guidance

- Start small and raise the cap only when you observe premature cutoffs.
- A high cap is not a quality feature by itself.
- If the agent loops or wanders, fix the prompt or tool surface before raising `maxSteps` again.

```typescript
const result = await agent.run({
  prompt: "Inspect the repository and summarize the architecture.",
  maxSteps: 12,
});
```

## Option family: `autoInitialize`

`autoInitialize` controls when sessions are created.

### Behavior summary

| Value | What happens | Good for |
|---|---|---|
| `false` | You control initialization manually before the first execution call | Advanced flows that adjust config after construction |
| `true` | Sessions initialize immediately after construction | Predictable startup and early failure discovery |

### Use `autoInitialize: true` when

- you want missing env vars or bad server config to fail at startup
- you are building a service that should fail fast
- you want consistent latency on the first request

### Use `autoInitialize: false` when

- you need to mutate behavior before the first call
- you want a deferred startup in short-lived tooling
- you are intentionally staging initialization manually
- you will call `await agent.initialize()` or pre-create sessions yourself before `run()` / `stream()`

```typescript
const agent = new MCPAgent({
  llm,
  client,
  autoInitialize: false,
});

agent.setDisallowedTools(["delete_file"]);
await agent.initialize();
```

## Option family: `memoryEnabled`

`memoryEnabled` controls whether the agent remembers prior turns.

### Memory strategy table

| Scenario | Recommended value | Reason |
|---|---|---|
| REPL or chat assistant | `true` | Follow-up questions should see prior context |
| HTTP route per request | `false` | Avoid cross-request contamination |
| Batch jobs | `false` | Each task should start clean |
| Interactive operator console | `true` | Context continuity helps |

### Inspecting and clearing memory

```typescript
const history = agent.getConversationHistory();
console.dir(history, { depth: 4 });

agent.clearConversationHistory();
```

## Prompt controls: `systemPrompt` vs `systemPromptTemplate` vs `additionalInstructions`

Use the smallest tool that solves the problem.

| Field | Strength | Best use | Risk |
|---|---|---|---|
| `systemPrompt` | strongest | Full persona or workflow override | Easy to replace useful defaults accidentally |
| `systemPromptTemplate` | strong but structured | Reusable prompt shell with dynamic placeholders | Requires consistent template conventions |
| `additionalInstructions` | lightest | Layer narrow extra rules onto the existing prompt | Can become noisy if overloaded |

### Recommended prompt hierarchy

1. Use `additionalInstructions` first for narrow constraints.
2. Use `systemPromptTemplate` when you need a predictable reusable structure.
3. Use `systemPrompt` only when you truly need to replace the base behavior.

### `systemPrompt`

```typescript
const agent = new MCPAgent({
  llm,
  client,
  systemPrompt: "You are a repository auditor. Be concise, cite tool findings, and never speculate beyond tool output.",
});
```

### `systemPromptTemplate`

```typescript
const agent = new MCPAgent({
  llm,
  client,
  systemPromptTemplate: [
    "You are a repository auditor.",
    "Use tools carefully and summarize evidence before conclusions.",
    "Never claim a tool result you did not observe.",
  ].join("\n"),
});
```

### `additionalInstructions`

```typescript
const agent = new MCPAgent({
  llm,
  client,
  additionalInstructions: "Prefer numbered conclusions and mention uncertainty explicitly.",
});
```

## Tool controls: `disallowedTools`

### `disallowedTools`

Use it to block dangerous or distracting tools. When `undefined` (the default), no tools are blocked.

```typescript
const agent = new MCPAgent({
  llm,
  client,
  disallowedTools: ["delete_file", "shell_exec"],
});
```

### Runtime update with `setDisallowedTools()`

```typescript
agent.setDisallowedTools(["delete_file", "shell_exec"]);
await agent.initialize();
```

### `getDisallowedTools()`

```typescript
const blocked = agent.getDisallowedTools();
console.log(blocked);
```

## Server routing: `useServerManager`

Enable `useServerManager` only when more than one server must be orchestrated dynamically.

```typescript
const agent = new MCPAgent({
  llm,
  client,
  useServerManager: true,
});
```

### Good candidates for `useServerManager`

- one server for search and another for filesystem access
- dynamic server activation from runtime config
- flows where server availability changes over time

### Bad candidates for `useServerManager`

- single-server toy scripts
- examples where dynamic routing would hide the basic concepts
- cases where ordinary `MCPClient` setup is already sufficient

## Lifecycle methods

The `MCPAgent` exposes the following methods.

| Method | Returns | What it does |
|---|---|---|
| `initialize()` | `Promise<void>` | Creates sessions and prepares the tool set. Called automatically when `autoInitialize: true`. Call manually when `autoInitialize: false`. |
| `close()` | `Promise<void>` | Closes all open sessions. Call when the agent is no longer needed to free resources. |
| `run({ prompt, schema?, maxSteps?, signal? })` | `Promise<string \| T>` | Executes a single interaction and returns the final response. Pass a Zod `schema` for typed output. Pass a `signal` to support cancellation. |
| `stream({ prompt, schema?, maxSteps?, signal? })` | `AsyncGenerator<AgentStep, string \| T>` | Yields each `AgentStep` (`{ action: { tool, toolInput, log }, observation }`) as the agent executes. Returns the final answer when exhausted. |
| `prettyStreamEvents(prompt: string)` or `prettyStreamEvents({ prompt, maxSteps?, schema? })` | async generator | Yields formatted events suitable for CLI-style output. Plain-string form is deprecated; prefer the options object. |
| `streamEvents({ prompt, maxSteps? })` | async generator | Low-level async iterator yielding raw LangChain `StreamEvent` objects. |
| `getConversationHistory()` | `BaseMessage[]` | Returns a copy of the internal conversation history. |
| `clearConversationHistory()` | `void` | Clears conversation history. If `memoryEnabled` is `true` and a system message is present, it is preserved. |
| `setDisallowedTools(tools: string[])` | `void` | Replaces the blocked tool list at runtime. |
| `getDisallowedTools()` | `string[]` | Returns the current blocked tool list. |
| `setSystemMessage(message: string)` | `void` | Replaces the system message and recreates the agent executor. |

```typescript
const agent = new MCPAgent({ llm, client });

await agent.initialize();
const result = await agent.run({ prompt: "Inspect the repository." });
await agent.close();   // clean up sessions
```

### Streaming example

Each yielded `step` is an `AgentStep` with `action.tool`, `action.toolInput`, `action.log`, and `observation`. In the current published package, `observation` is an empty placeholder at yield time, so use the final generator return value or `streamEvents()` if you need actual tool output.

```typescript
for await (const step of agent.stream({ prompt: "Write a report" })) {
  console.log(`Tool: ${step.action.tool}`);
  console.log(`Args: ${JSON.stringify(step.action.toolInput)}`);
}
```

### Pretty streaming example

```typescript
for await (const _ of agent.prettyStreamEvents({
  prompt: "Analyze the codebase",
  maxSteps: 20,
})) {
  // formatted output handled automatically
}
```

## `connectors` vs `client`

Use this distinction clearly.

| Choose... | When... | Why |
|---|---|---|
| `client` | You already built an `MCPClient` | The ownership model is explicit |
| `connectors` | Your local integration pattern centers on connectors | The agent can build from connector abstractions |

### Recommendation

If the repo already uses `MCPClient`, keep using `client`. It is easier to explain, easier to debug, and matches the rest of this skill's examples.

## Related client option: `codeMode`

`codeMode` is not an `MCPAgent` option. It belongs to `MCPClient`. Document it here because agent builders often ask about it while configuring the agent.

| Client option | Type | Meaning |
|---|---|---|
| `codeMode` | `boolean` or config object | Enables code execution workflows through the client |

```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient(
  {
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", process.cwd()],
      },
    },
  },
  {
    codeMode: true,
  }
);

const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o", temperature: 0 }),
  client,
  maxSteps: 30,
});
```

## Runtime change checklist

Use this checklist when changing an existing agent between calls.

- update `disallowedTools` with `setDisallowedTools()`
- re-initialize when your workflow expects the updated tool state to be reflected immediately
- clear conversation history if the next task must start from a blank slate
- call `close()` when the agent is no longer needed to release session resources

## `❌ BAD` / `✅ GOOD` patterns

### Pair 1: Do not use `systemPrompt` when `additionalInstructions` is enough

#### ❌ BAD

```typescript
const agent = new MCPAgent({
  llm,
  client,
  systemPrompt: "You are a repository auditor. Be concise. Mention uncertainty. Use numbered lists. Prefer direct evidence. Summarize findings. Stay brief.",
});
```

Why it is bad:

- It replaces more of the prompt stack than the change requires.
- Small behavioral tweaks become harder to maintain.

#### ✅ GOOD

```typescript
const agent = new MCPAgent({
  llm,
  client,
  additionalInstructions: "Be concise, use numbered lists, and mention uncertainty explicitly.",
});
```

### Pair 2: Do not enable memory accidentally in request/response APIs

#### ❌ BAD

```typescript
const agent = new MCPAgent({
  llm,
  client,
  autoInitialize: true,
});
```

Why it is bad:

- `memoryEnabled` defaults to `true`.
- Stateless HTTP routes can leak context between requests if the same agent instance is reused.

#### ✅ GOOD

```typescript
const agent = new MCPAgent({
  llm,
  client,
  autoInitialize: true,
  memoryEnabled: false,
});
```

### Pair 3: Do not misdocument `codeMode`

#### ❌ BAD

```typescript
const agent = new MCPAgent({
  llm,
  client,
  codeMode: true,
});
```

Why it is bad:

- It teaches the wrong ownership boundary.
- `codeMode` belongs to the client, not the agent.

#### ✅ GOOD

```typescript
const client = new MCPClient(
  { mcpServers },
  { codeMode: true }
);

const agent = new MCPAgent({
  llm,
  client,
});
```

### Pair 4: Do not over-enable `useServerManager`

#### ❌ BAD

```typescript
const agent = new MCPAgent({
  llm,
  client,
  useServerManager: true,
});
```

Why it is bad:

- The option adds complexity if only one server exists.
- Beginners learn a harder path than necessary.

#### ✅ GOOD

```typescript
const agent = new MCPAgent({
  llm,
  client,
  useServerManager: false,
  maxSteps: 12,
});
```

### Pair 5: Do not block tools without verifying runtime state

#### ❌ BAD

```typescript
agent.setDisallowedTools(["delete_file"]);
const result = await agent.run({ prompt: "Inspect the repository" });
```

Why it is bad:

- The call site never verifies the active tool state.
- In some workflows you want a fresh initialization boundary.

#### ✅ GOOD

```typescript
agent.setDisallowedTools(["delete_file"]);
await agent.initialize();
console.log(agent.getDisallowedTools());
const result = await agent.run({ prompt: "Inspect the repository" });
```

## Troubleshooting configuration issues

| Symptom | Likely cause | Fix |
|---|---|---|
| The first request is slow and inconsistent | Lazy initialization is happening on the first call | Set `autoInitialize: true` |
| Follow-up calls reference prior work unexpectedly | Memory is still enabled | Set `memoryEnabled: false` or clear history |
| The agent still uses tools you meant to block | Runtime tool restrictions were not applied as expected | Use `setDisallowedTools()` and re-initialize if needed |
| Prompt changes seem too weak | You used `additionalInstructions` for a full prompt override case | Move to `systemPrompt` or `systemPromptTemplate` |
| The example becomes too complex | Too many options are enabled at once | Start from the baseline and add one option family at a time |

## Recommended configuration order

Use this order when building a production-ready agent:

1. choose explicit or simplified mode
2. set `maxSteps`
3. decide `memoryEnabled`
4. decide `autoInitialize`
5. add prompt controls
6. add tool controls (`disallowedTools`)
7. add server manager only if the problem demands it
8. add code mode at the client level only if necessary

## Related guides

- Read `./quick-start.md` for startup patterns and server integrations.
- Read `./llm-integration.md` for provider-specific model guidance.
- Read `./streaming.md` for run-time output mode selection.
- Read `../patterns/production-patterns.md` for deployment hardening.
