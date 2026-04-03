# Quick Start Guide

Use this guide when you need a correct first `MCPAgent` quickly, including environment setup, startup mode choice, chat loops, HTTP handlers, cleanup, and failure handling.

---

## What this guide covers

Use this file for the first working version of an agent.

It covers:

- explicit mode with a hand-built LLM and `MCPClient`
- environment setup with `.env`
- one-shot calls with `run()`
- an interactive chat loop pattern
- Express and Fastify HTTP server integrations
- graceful cleanup with `try/finally` and signal handlers
- practical error handling you can keep in production

Use `references/guides/agent-configuration.md` after the first successful run if you need deeper option-by-option guidance.

## Prerequisites

| Requirement | Why it matters | Notes |
|---|---|---|
| Node.js ≥ 18 | Minimum runtime version required by the SDK | Use Node.js LTS for stability |
| `mcp-use` | Provides `MCPAgent`, `MCPClient`, and streaming helpers | Required in every setup |
| One LangChain provider package | Supplies the chat model | Install only what you use |
| A working MCP server config | Gives the agent tools to call | Local `command` or remote `url` is fine |
| Provider API keys | Required for the selected LLM | Keep them in `.env` |
| A shutdown strategy | Prevents leaked sessions or sandboxes | Always call `await agent.close()` |

Before the first `run()`, verify both sides of the setup:

- **LLM side:** confirm the needed provider key exists (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, or `GROQ_API_KEY`)
- **MCP side:** confirm each configured server command exists or each remote server URL is reachable

## Install the minimum packages

### npm

```bash
npm install mcp-use zod dotenv
npm install @langchain/openai
```

### pnpm

```bash
pnpm add mcp-use zod dotenv
pnpm add @langchain/openai
```

### bun

```bash
bun add mcp-use zod dotenv
bun add @langchain/openai
```

### Provider package matrix

| Provider | Package | Typical env var |
|---|---|---|
| OpenAI | `@langchain/openai` | `OPENAI_API_KEY` |
| Anthropic | `@langchain/anthropic` | `ANTHROPIC_API_KEY` |
| Google | `@langchain/google-genai` | `GOOGLE_API_KEY` |
| Groq | `@langchain/groq` | `GROQ_API_KEY` |

## Environment setup

Create a `.env` file for local development.

```dotenv
OPENAI_API_KEY=sk-example
ANTHROPIC_API_KEY=sk-ant-example
GOOGLE_API_KEY=google-example
GROQ_API_KEY=groq-example
BRAVE_API_KEY=brave-example
LANGFUSE_PUBLIC_KEY=pk-lf-example
LANGFUSE_SECRET_KEY=sk-lf-example
```

Load the file before constructing the model or the agent.

```typescript
import "dotenv/config";
```

### Environment variable checklist

| Variable | Needed when | Keep it in `.env`? |
|---|---|---|
| `OPENAI_API_KEY` | Using `ChatOpenAI` | Yes |
| `ANTHROPIC_API_KEY` | Using `ChatAnthropic` | Yes |
| `GOOGLE_API_KEY` | Using `ChatGoogleGenerativeAI` | Yes |
| `GROQ_API_KEY` | Using `ChatGroq` | Yes |
| Any MCP server key | The server needs provider or API access | Yes |
| Langfuse keys | You enable observability | Yes |

## MCPAgent constructor parameters

`MCPAgent` supports two construction modes. In **explicit mode** you pass a LangChain model instance plus `client` or `connectors`. In **simplified mode** you pass `llm` as a `"provider/model"` string plus `mcpServers`.

### Common options (both modes)

| Parameter | Type | Default | Description |
|---|---|---|---|
| `maxSteps` | `number` | `5` | Maximum number of tool-calling steps per `run()` call |
| `autoInitialize` | `boolean` | `false` | Whether to initialize sessions immediately after construction |
| `memoryEnabled` | `boolean` | `true` | Whether to retain conversation history across `run()` calls |
| `systemPrompt` | `string \| null` | `null` | Custom system prompt replacing the framework default |
| `systemPromptTemplate` | `string \| null` | `null` | Alternate templated system prompt |
| `additionalInstructions` | `string \| null` | `null` | Extra instructions appended to the system prompt |
| `disallowedTools` | `string[]` | `[]` | Tool names the agent will not expose or call |
| `useServerManager` | `boolean` | `false` | Enable dynamic multi-server orchestration via Server Manager |
| `verbose` | `boolean` | `false` | Enable detailed Server Manager logging |
| `observe` | `boolean` | `true` | Enable observability callbacks |
| `exposeResourcesAsTools` | `boolean` | `true` | Expose MCP resources as callable tools |
| `exposePromptsAsTools` | `boolean` | `true` | Expose MCP prompts as callable tools |

### Explicit mode fields

| Parameter | Type | Required | Description |
|---|---|---|---|
| `llm` | LangChain model instance | yes | Any LangChain-compatible chat model (e.g. `ChatOpenAI`) |
| `client` | `MCPClient` | one of `client`/`connectors` | Pre-built MCPClient instance |
| `connectors` | `BaseConnector[]` | one of `client`/`connectors` | Connector objects if not using a client |

### Simplified mode fields

| Parameter | Type | Required | Description |
|---|---|---|---|
| `llm` | `string` | yes | Provider/model string, e.g. `"openai/gpt-4o"` |
| `mcpServers` | `Record<string, MCPServerConfig>` | yes | Server configurations (the agent creates the MCPClient internally) |
| `llmConfig` | `LLMConfig` | no | Extra LLM constructor options (temperature, maxTokens, apiKey, etc.) |

## MCPClient server configuration

Each entry in `mcpServers` can be a STDIO server (`command` + `args`) or an HTTP/SSE server (`url`).

| Field | Type | Description |
|---|---|---|
| `command` | `string` | Executable that starts the MCP server (STDIO transport) |
| `args` | `string[]` | Arguments passed to the command |
| `env` | `Record<string, string>` | Extra environment variables for the server process |
| `url` | `string` | Base URL for HTTP or SSE transport |
| `headers` | `Record<string, string>` | HTTP headers to include with requests |
| `transport` | `"http" \| "sse"` | Force a specific HTTP transport mode |

## First working agent

The recommended construction style is explicit mode: you instantiate a LangChain model and an `MCPClient` yourself, then pass both to `MCPAgent`. Simplified mode (passing a `"provider/model"` string) is also supported — see `./llm-integration.md`.

```typescript
import "dotenv/config";
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

async function main() {
  if (!process.env.OPENAI_API_KEY) {
    throw new Error("Set OPENAI_API_KEY before running this example.");
  }

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
    memoryEnabled: false,
  });

  try {
    const result = await agent.run({
      prompt: "List the TypeScript files in this project and summarize their likely roles.",
    });

    console.log(result);
  } finally {
    await agent.close();
  }
}

main().catch((error) => {
  console.error("Agent failed:", error);
  process.exitCode = 1;
});
```

## Minimal local calculator server for agent tutorials

If the task is "build a calculator agent" and the repo does not already expose calculator tools, start a tiny MCP server first, then point the agent at it over HTTP.

**`src/mcp/calculator-server.ts`**

```typescript
import { MCPServer, error, object } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({ name: "calculator-server", version: "1.0.0" });

const numberPair = z.object({
  a: z.number().describe("First number"),
  b: z.number().describe("Second number"),
});

server.tool({ name: "add", description: "Add two numbers", schema: numberPair }, async ({ a, b }) =>
  object({ result: a + b })
);
server.tool({ name: "subtract", description: "Subtract two numbers", schema: numberPair }, async ({ a, b }) =>
  object({ result: a - b })
);
server.tool({ name: "multiply", description: "Multiply two numbers", schema: numberPair }, async ({ a, b }) =>
  object({ result: a * b })
);
server.tool({ name: "divide", description: "Divide two numbers", schema: numberPair }, async ({ a, b }) =>
  b === 0 ? error("Division by zero is not allowed") : object({ result: a / b })
);

await server.listen(3000);
```

Run it in one terminal:

```bash
npx tsx src/mcp/calculator-server.ts
```

Then point the agent at it:

```typescript
const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  llmConfig: { temperature: 0 },
  mcpServers: {
    calculator: { url: "http://127.0.0.1:3000/mcp" },
  },
  maxSteps: 10,
  memoryEnabled: false,
  autoInitialize: true,
});
```

This is the smallest self-contained tool surface for calculator-style agent tasks.

### Pre-initializing all sessions

If you want all MCP server connections established before the first `run()` call (for example, to surface startup errors early), call `createAllSessions()` on the client before constructing the agent:

```typescript
await client.createAllSessions();
```

This is optional. When `autoInitialize: true` is set on the agent, initialization happens for you before the first execution call. If you keep `autoInitialize: false`, call `await agent.initialize()` or `await client.createAllSessions()` yourself before `run()`, `stream()`, or `streamEvents()`.

### Why this example is the recommended baseline

- It shows complete imports.
- It isolates secrets in environment variables.
- It sets `memoryEnabled: false` explicitly for a one-shot script (the default is `true`).
- It sets `autoInitialize: true` so startup problems happen early (the default is `false`).
- It sets `maxSteps: 20` explicitly (the default is `5`).
- It guarantees cleanup with `finally`.

## Passing prompts to `run()`

`run()` accepts an options object. Passing a plain string is also still supported but deprecated. Use the object form in all new code.

```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";
import { z } from "zod";

const SummarySchema = z.object({
  files: z.array(z.string()),
  summary: z.string(),
});

// agent already constructed ...

const result = await agent.run({
  prompt: "List the top-level files and summarize the repository.",
  schema: SummarySchema,
});

// result is fully typed here
console.log(result.files);
console.log(result.summary);
```

### `run()` parameters

| Parameter | Type | Description |
|---|---|---|
| `prompt` | `string` | The task or question for the agent |
| `schema` | `ZodSchema<T>` | Optional; when provided, the agent returns a typed object instead of a string |
| `maxSteps` | `number` | Optional per-call override for the maximum number of steps |
| `signal` | `AbortSignal` | Optional; allows cancelling the run via `AbortController` |

## Tool access control

Use `disallowedTools` to restrict which tools the agent can call. Pass the list at construction time or update it dynamically.

### At construction time

```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({ mcpServers: { /* ... */ } });
const llm = new ChatOpenAI({ model: "gpt-4o" });

const agent = new MCPAgent({
  llm,
  client,
  disallowedTools: ["file_system", "network", "shell"],
});
```

### After initialization

```typescript
// Update restrictions at runtime
agent.setDisallowedTools(["file_system", "network", "shell", "database"]);
await agent.initialize(); // Reinitialize to apply changes

// Inspect current restrictions
const restricted = agent.getDisallowedTools();
console.log("Restricted tools:", restricted);
```

## Server Manager

Enable the Server Manager when connecting to many MCP servers. It dynamically selects which server to use, reducing LLM confusion when many tools are available.

```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({
  mcpServers: {
    filesystem: { command: "npx", args: ["-y", "@modelcontextprotocol/server-filesystem", process.cwd()] },
    // ... other servers
  },
});

const llm = new ChatOpenAI({ model: "gpt-4o" });

const agent = new MCPAgent({
  llm,
  client,
  useServerManager: true,
});
```

## Chat loop pattern

Use this pattern when you need a long-lived interactive loop and want memory between turns.

```typescript
import "dotenv/config";
import readline from "node:readline/promises";
import { stdin as input, stdout as output } from "node:process";
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

async function chat() {
  const rl = readline.createInterface({ input, output });

  const client = new MCPClient({
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", process.cwd()],
      },
    },
  });

  const llm = new ChatOpenAI({ model: "gpt-4o", temperature: 0.2 });

  const agent = new MCPAgent({
    llm,
    client,
    maxSteps: 20,
    autoInitialize: true,
    memoryEnabled: true,
  });

  try {
    console.log("Type 'exit' to quit, 'clear' to reset memory, 'history' to inspect memory.");

    while (true) {
      const userInput = (await rl.question("\nYou: ")).trim();

      if (!userInput) {
        continue;
      }

      if (userInput === "exit") {
        break;
      }

      if (userInput === "clear") {
        agent.clearConversationHistory();
        console.log("Conversation memory cleared.");
        continue;
      }

      if (userInput === "history") {
        console.dir(agent.getConversationHistory(), { depth: 4 });
        continue;
      }

      const response = await agent.run({
        prompt: userInput,
      });

      console.log(`\nAssistant: ${response}`);
    }
  } finally {
    rl.close();
    await agent.close();
  }
}

chat().catch((error) => {
  console.error("Chat loop failed:", error);
  process.exitCode = 1;
});
```

### Chat loop notes

- Keep memory enabled for a conversational agent. `memoryEnabled` defaults to `true`; set it explicitly for clarity.
- Add a `clear` command so operators can reset state quickly.
- Print a clear prompt so the operator understands available control commands.

## HTTP server pattern: Express

Use Express when the repo already uses it. Keep the agent lifecycle explicit.

```typescript
import "dotenv/config";
import express from "express";
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const app = express();
app.use(express.json());

function createAgent() {
  const client = new MCPClient({
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", process.cwd()],
      },
    },
  });

  const llm = new ChatOpenAI({ model: "gpt-4o", temperature: 0 });

  return new MCPAgent({
    llm,
    client,
    maxSteps: 20,
    autoInitialize: true,
    memoryEnabled: false,
  });
}

app.post("/agent", async (req, res) => {
  const prompt = String(req.body?.prompt ?? "").trim();

  if (!prompt) {
    res.status(400).json({ error: "prompt is required" });
    return;
  }

  const agent = createAgent();

  try {
    const result = await agent.run({ prompt });
    res.status(200).json({ result });
  } catch (error) {
    console.error("Express agent route failed:", error);
    res.status(500).json({ error: "agent execution failed" });
  } finally {
    await agent.close();
  }
});

const server = app.listen(3000, () => {
  console.log("Express agent server listening on http://localhost:3000");
});

async function shutdown(signal: string) {
  console.log(`Received ${signal}. Closing HTTP server.`);
  await new Promise<void>((resolve, reject) => {
    server.close((error) => {
      if (error) reject(error);
      else resolve();
    });
  });
}

for (const signal of ["SIGINT", "SIGTERM"] as const) {
  process.on(signal, () => {
    shutdown(signal).catch((error) => {
      console.error("Express shutdown failed:", error);
      process.exitCode = 1;
    });
  });
}
```

### Express design choices

- Build a fresh agent per request when memory is not required.
- Validate the prompt before constructing expensive downstream work.
- Always close the agent even on error.
- Close the HTTP server cleanly on shutdown.

## HTTP server pattern: Fastify

Use Fastify when the repo already relies on it, or when you want explicit schema hooks and tighter server ergonomics.

```typescript
import "dotenv/config";
import Fastify from "fastify";
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const fastify = Fastify({ logger: true });

function createAgent() {
  const client = new MCPClient({
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", process.cwd()],
      },
    },
  });

  const llm = new ChatOpenAI({ model: "gpt-4o", temperature: 0 });

  return new MCPAgent({
    llm,
    client,
    maxSteps: 20,
    autoInitialize: true,
    memoryEnabled: false,
  });
}

fastify.post<{ Body: { prompt?: string } }>("/agent", async (request, reply) => {
  const prompt = String(request.body?.prompt ?? "").trim();

  if (!prompt) {
    return reply.status(400).send({ error: "prompt is required" });
  }

  const agent = createAgent();

  try {
    const result = await agent.run({ prompt });
    return reply.status(200).send({ result });
  } catch (error) {
    request.log.error({ error }, "Fastify agent route failed");
    return reply.status(500).send({ error: "agent execution failed" });
  } finally {
    await agent.close();
  }
});

async function start() {
  try {
    await fastify.listen({ port: 3000, host: "0.0.0.0" });
  } catch (error) {
    fastify.log.error(error);
    process.exit(1);
  }
}

start();

for (const signal of ["SIGINT", "SIGTERM"] as const) {
  process.on(signal, async () => {
    try {
      await fastify.close();
    } catch (error) {
      fastify.log.error(error);
      process.exitCode = 1;
    }
  });
}
```

## Graceful cleanup patterns

### Minimal `try/finally`

Use this everywhere.

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

const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),
  client,
});

try {
  const result = await agent.run({
    prompt: "Summarize this project.",
  });
  console.log(result);
} finally {
  await agent.close();
}
```

### Process signal handling

Use signal handlers for long-lived processes.

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

const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),
  client,
  autoInitialize: true,
});

for (const signal of ["SIGINT", "SIGTERM"] as const) {
  process.on(signal, () => {
    void agent.close().finally(() => process.exit(0));
  });
}
```

### Cleanup checklist

- close readline interfaces
- close HTTP servers
- close the agent
- flush observability callbacks if you added them
- let the process exit after cleanup completes

## Error handling

Use defensive error handling from the first draft. Do not wait for production bugs.

### Recommended structure

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

const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),
  client,
});

try {
  const result = await agent.run({
    prompt: "Inspect the repository and describe the architecture.",
  });

  console.log(result);
} catch (error) {
  console.error("Agent execution failed:", error);
} finally {
  await agent.close();
}
```

### Error categories to plan for

| Category | What it usually means | What to do |
|---|---|---|
| Missing API key | Provider auth is not configured | Validate env at startup |
| MCP server launch failure | Bad command, bad args, or missing dependency | Test the server command directly |
| Tool selection loops | `maxSteps` too low or prompt too vague | Clarify the task and tune `maxSteps` |
| Stream handling failure | Raw event consumer made invalid assumptions | Switch to `stream()` or `prettyStreamEvents()` if possible |
| Request timeout | Provider or tool call took too long | Pass an `AbortSignal` via `run({ prompt, signal })` to support cancellation |
| Simplified mode missing `mcpServers` | `llm` is a string but `mcpServers` was not provided | Add `mcpServers` to the constructor options |

### Validate configuration early

```typescript
function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

requireEnv("OPENAI_API_KEY");
```

## `❌ BAD` / `✅ GOOD` patterns

### Pair 1: Do not skip cleanup

#### ❌ BAD

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

const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),
  client,
});

const result = await agent.run({
  prompt: "Summarize the project",
});
console.log(result);
```

Why it is bad:

- The agent is never closed.
- Leaked sessions become harder to debug in long-lived processes.

#### ✅ GOOD

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

const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),
  client,
});

try {
  const result = await agent.run({
    prompt: "Summarize the project",
  });
  console.log(result);
} finally {
  await agent.close();
}
```

### Pair 2: Do not pass `llm` as a string without also providing `mcpServers`

Simplified mode accepts a `"provider/model"` string for `llm`, but it **requires** `mcpServers` in the same constructor options. Omitting `mcpServers` throws at runtime.

#### ❌ BAD

```typescript
import { MCPAgent } from "mcp-use";

// Missing required mcpServers — throws: "Simplified mode requires 'mcpServers' configuration"
const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  maxSteps: 20,
});
```

Why it is bad:

- `mcpServers` is required when `llm` is a string.
- The constructor will throw before the agent can run.

#### ✅ GOOD — simplified mode with `mcpServers`

```typescript
import { MCPAgent } from "mcp-use";

const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", process.cwd()],
    },
  },
  maxSteps: 20,
  autoInitialize: true,
});
```

#### ✅ GOOD — explicit mode (full control)

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

const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o", temperature: 0 }),
  client,
  maxSteps: 20,
  autoInitialize: true,
});
```

### Pair 3: Never hard-code secrets

#### ❌ BAD

```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const agent = new MCPAgent({
  llm: new ChatOpenAI({
    model: "gpt-4o",
    apiKey: "sk-live-real-secret",
  }),
  client: new MCPClient({ mcpServers: { /* ... */ } }),
});
```

Why it is bad:

- The snippet teaches insecure habits.
- Secrets leak into shell history, repos, and screenshots.

#### ✅ GOOD

```typescript
import "dotenv/config";
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const agent = new MCPAgent({
  llm: new ChatOpenAI({
    model: "gpt-4o",
    apiKey: process.env.OPENAI_API_KEY,
    temperature: 0,
  }),
  client: new MCPClient({ mcpServers: { /* ... */ } }),
});
```

### Pair 4: Never bypass `mcp-use` with direct MCP SDK imports in good examples

#### ❌ BAD

```typescript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const transport = new StdioClientTransport({
  command: "npx",
  args: ["-y", "@modelcontextprotocol/server-filesystem", process.cwd()],
});

const client = new Client({ name: "raw-sdk", version: "1.0.0" }, { capabilities: {} });
await client.connect(transport);
```

Why it is bad:

- It skips the library this skill is about.
- It teaches a lower-level path that does not match the repo's guidance.

#### ✅ GOOD

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

const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o", temperature: 0 }),
  client,
  autoInitialize: true,
});
```

## Production-ready startup checklist

Before you ship a first version, confirm all of the following:

- construction uses explicit mode: a LangChain model instance and an `MCPClient` are both passed to `MCPAgent` (do not pass `llm` as a string)
- the LLM provider package is installed
- the API key is loaded from `.env` or the runtime environment
- the MCP server command or URL is valid
- `maxSteps` is documented and intentional (default is `5`)
- memory is enabled or disabled on purpose (`memoryEnabled` defaults to `true`)
- `await agent.close()` is guaranteed
- HTTP routes validate prompt input
- the operator can see clear startup and failure logs

## What to read next

- Read `./agent-configuration.md` for option-by-option constructor guidance.
- Read `./llm-integration.md` for provider-specific model setup.
- Read `./streaming.md` for `stream()`, `streamEvents()`, `prettyStreamEvents()`, and Vercel AI SDK integration.
- Read `../examples/agent-recipes.md` for longer end-to-end patterns.
