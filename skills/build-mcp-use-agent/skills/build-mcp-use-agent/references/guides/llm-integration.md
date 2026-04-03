# LLM Integration

Complete reference for connecting `MCPAgent` to LangChain chat models with correct provider setup, tool-calling model choice, runtime switching, and generation tuning.

---

## Overview

Use `MCPAgent` with a LangChain chat model whenever you want the agent to reason over MCP tools instead of acting as a plain text generator.

In `mcp-use`, LLM integration means one thing: give the agent a **LangChain-compatible chat model** that can decide when to call tools, format tool arguments correctly, and continue the conversation after tool results return.

Treat the model as the planning layer.
Treat MCP servers as the execution layer.
Treat `MCPAgent` as the orchestrator that binds them together.

### What the LLM does inside `MCPAgent`

| Responsibility | Why it matters | Failure symptom if the model is weak |
|---|---|---|
| `Understands the prompt` | The model must map the request to a usable plan | The agent answers vaguely or skips tools |
| `Chooses tool usage` | The agent should call MCP tools only when a tool helps | The agent hallucinates instead of executing |
| `Builds valid arguments` | Tool schemas require structured input | Tool calls fail with validation or schema errors |
| `Interprets tool results` | Raw tool output still needs synthesis | The final answer copies logs without explanation |
| `Continues multi-step flows` | Useful tasks often require several tool calls | The agent stops too early or loops aimlessly |
| `Respects instructions` | System prompts and additional instructions shape behavior | The agent ignores important constraints |

### Explicit mode vs simplified mode

Use one of two integration styles.

| Mode | What you pass to `MCPAgent` | Best when | Main tradeoff |
|---|---|---|---|
| Explicit mode | A prebuilt LangChain model instance plus `MCPClient` | You need full provider control, callbacks, tracing, or custom factories | More bootstrap code |
| Simplified string mode | A `"provider/model"` string and lightweight config | You need the shortest correct setup | Less obvious low-level control |

### Integration checklist

- Use a **chat model**, not a legacy text-completion model.
- Use a model that supports **tool calling** or **function calling**.
- Set provider API keys before constructing the model.
- Pick a temperature that matches your workload. Use lower values for automation.
- Close the agent when the run is complete so sessions do not leak.
- Prefer explicit mode when you need precise runtime ownership of the LLM instance.
- Prefer simplified mode when you want compact setup code for scripts and demos.

### Minimal architecture map

| Layer | Typical object | Purpose |
|---|---|---|
| Model layer | `ChatOpenAI`, `ChatAnthropic`, `ChatGoogleGenerativeAI`, `ChatGroq` | Generates planning and tool-call decisions |
| Agent layer | `MCPAgent` | Builds prompts, exposes tools, loops through tool results, and returns a final answer |
| Client layer | `MCPClient` | Connects to local or remote MCP servers |
| Server layer | MCP servers | Expose tools, prompts, and resources |

Use the provider sections below as concrete, runnable templates.

## Supported Providers Table

Install the provider package that matches the chat model you want to use.

| Provider | Package | Install | String shorthand |
|---|---|---|---|
| OpenAI | `@langchain/openai` | `npm install @langchain/openai` | `openai/gpt-4o` |
| Anthropic | `@langchain/anthropic` | `npm install @langchain/anthropic` | `anthropic/claude-3-5-sonnet-20241022` |
| Google Gemini | `@langchain/google-genai` | `npm install @langchain/google-genai` | `google/gemini-pro` |
| Groq | `@langchain/groq` | `npm install @langchain/groq` | `groq/llama-3.1-70b-versatile` |

### Provider environment variables

| Provider | Primary env var | Notes |
|---|---|---|
| OpenAI | `OPENAI_API_KEY` | Required for `ChatOpenAI` and for string shorthand that targets OpenAI |
| Anthropic | `ANTHROPIC_API_KEY` | Required for Claude models |
| Google Gemini | `GOOGLE_API_KEY` | Some setups also accept `GOOGLE_GENERATIVE_AI_API_KEY`, but standardize on `GOOGLE_API_KEY` in your docs and code |
| Groq | `GROQ_API_KEY` | Required for Groq-hosted models |

### Shared package setup

```bash
npm install mcp-use dotenv
npm install @langchain/openai @langchain/anthropic @langchain/google-genai @langchain/groq
```

Load environment variables before you construct a model.

```typescript
import "dotenv/config";
```

## OpenAI Integration

Use `ChatOpenAI` when you want to connect `MCPAgent` to OpenAI through LangChain.

### Imports

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { MCPAgent, MCPClient } from "mcp-use";
```

### Install

```bash
npm install @langchain/openai
```

### Environment variable

Use `OPENAI_API_KEY` unless you have a very specific reason to inject the key directly at runtime.

### Full example

```typescript
import "dotenv/config";
import { ChatOpenAI } from "@langchain/openai";
import { MCPAgent, MCPClient } from "mcp-use";

async function main() {
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
    maxTokens: 2048,
    streaming: true,
    apiKey: process.env.OPENAI_API_KEY,
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
      prompt: "List the Markdown guides in this repo and summarize the role of each one.",
    });

    console.log(result);
  } finally {
    await agent.close();
  }
}

main().catch((error) => {
  console.error("OpenAI agent failed:", error);
  process.exitCode = 1;
});
```

### OpenAI options

| Option | Type | Example | Required | What it controls |
|---|---|---|---|---|
| `model` | `string` | `"gpt-4o"` | Yes | Selects the OpenAI chat model to use |
| `temperature` | `number` | `0` | No | Controls randomness. Use lower values for tool-driven workflows |
| `maxTokens` | `number` | `2048` | No | Caps output length. Raise it for long summaries |
| `topP` | `number` | `1` | No | Applies nucleus sampling. Usually leave it at the default when using temperature |
| `streaming` | `boolean` | `true` | No | Streams tokens and tool-calling events when supported by your flow |
| `apiKey` | `string` | `process.env.OPENAI_API_KEY` | No | Overrides the environment variable explicitly |

### When to use OpenAI

- Use `gpt-4o` when you want strong tool selection and balanced speed.
- Use `temperature: 0` for repeatable automation and tool-heavy workflows.
- Use `streaming: true` when your app consumes partial tokens or progressive output.
- Never rely on OpenAI defaults blindly. Set the model explicitly so upgrades stay deliberate.

### Practical guidance

- Start with `gpt-4o` unless your team has already standardized on another tool-capable model.
- Keep temperature low for tasks that inspect code, route tools, fetch data, or summarize structured output.
- Raise output limits only when you observe truncation in real runs.
- Log provider-level errors near startup so missing credentials fail early.

---

## Anthropic Integration

Use `ChatAnthropic` when you want to connect `MCPAgent` to Anthropic through LangChain.

### Imports

```typescript
import { ChatAnthropic } from "@langchain/anthropic";
import { MCPAgent, MCPClient } from "mcp-use";
```

### Install

```bash
npm install @langchain/anthropic
```

### Environment variable

Use `ANTHROPIC_API_KEY` unless you have a very specific reason to inject the key directly at runtime.

### Full example

```typescript
import "dotenv/config";
import { ChatAnthropic } from "@langchain/anthropic";
import { MCPAgent, MCPClient } from "mcp-use";

async function main() {
  const client = new MCPClient({
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", process.cwd()],
      },
    },
  });

  const llm = new ChatAnthropic({
    model: "claude-3-5-sonnet-20241022",
    temperature: 0,
    maxTokens: 2048,
    topP: 1,
    streaming: true,
    apiKey: process.env.ANTHROPIC_API_KEY,
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
      prompt: "Inspect the project structure and explain which guide a new contributor should read first.",
    });

    console.log(result);
  } finally {
    await agent.close();
  }
}

main().catch((error) => {
  console.error("Anthropic agent failed:", error);
  process.exitCode = 1;
});
```

### Anthropic options

| Option | Type | Example | Required | What it controls |
|---|---|---|---|---|
| `model` | `string` | `"claude-3-5-sonnet-20241022"` | Yes | Selects the Claude model variant |
| `temperature` | `number` | `0` | No | Controls creativity vs determinism |
| `maxTokens` | `number` | `2048` | No | Limits completion size |
| `topP` | `number` | `1` | No | Controls nucleus sampling. Change it only when you understand the tradeoff |
| `streaming` | `boolean` | `true` | No | Enables streamed output when your app supports it |
| `apiKey` | `string` | `process.env.ANTHROPIC_API_KEY` | No | Overrides the provider key manually |

### When to use Anthropic

- Use Claude Sonnet when you want careful reasoning and clear final summaries.
- Keep temperature low for deterministic MCP workflows.
- Set `maxTokens` high enough for long explanations, but do not inflate it without need.
- Verify the selected Claude model supports tool use in your deployed provider account.

### Practical guidance

- Start with `claude-3-5-sonnet-20241022` unless your team has already standardized on another tool-capable model.
- Keep temperature low for tasks that inspect code, route tools, fetch data, or summarize structured output.
- Raise output limits only when you observe truncation in real runs.
- Log provider-level errors near startup so missing credentials fail early.

---

## Google Gemini Integration

Use `ChatGoogleGenerativeAI` when you want to connect `MCPAgent` to Google Gemini through LangChain.

### Imports

```typescript
import { ChatGoogleGenerativeAI } from "@langchain/google-genai";
import { MCPAgent, MCPClient } from "mcp-use";
```

### Install

```bash
npm install @langchain/google-genai
```

### Environment variable

Use `GOOGLE_API_KEY` unless you have a very specific reason to inject the key directly at runtime.

### Full example

```typescript
import "dotenv/config";
import { ChatGoogleGenerativeAI } from "@langchain/google-genai";
import { MCPAgent, MCPClient } from "mcp-use";

async function main() {
  const client = new MCPClient({
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", process.cwd()],
      },
    },
  });

  const llm = new ChatGoogleGenerativeAI({
    model: "gemini-pro",
    temperature: 0,
    maxOutputTokens: 2048,
    topP: 1,
    streaming: true,
    apiKey: process.env.GOOGLE_API_KEY,
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
      prompt: "Find the guides that mention observability and summarize what they are for.",
    });

    console.log(result);
  } finally {
    await agent.close();
  }
}

main().catch((error) => {
  console.error("Gemini agent failed:", error);
  process.exitCode = 1;
});
```

### Google Gemini options

| Option | Type | Example | Required | What it controls |
|---|---|---|---|---|
| `model` | `string` | `"gemini-pro"` | Yes | Chooses the Gemini model ID |
| `temperature` | `number` | `0` | No | Controls output diversity |
| `maxOutputTokens` | `number` | `2048` | No | Caps generated output for Gemini responses |
| `topP` | `number` | `1` | No | Applies nucleus sampling. Leave it default unless you are tuning deliberately |
| `streaming` | `boolean` | `true` | No | Enables streamed responses in supported environments |
| `apiKey` | `string` | `process.env.GOOGLE_API_KEY` | No | Supplies the Gemini API key directly |

### When to use Google Gemini

- Use `gemini-pro` when you want fast responses and efficient tool orchestration.
- Keep the Google API key in the environment, not inside source files.
- Use `maxOutputTokens` instead of `maxTokens` for this provider class.
- Standardize on `GOOGLE_API_KEY` across your repo even if alternate variable names exist elsewhere.

### Practical guidance

- Start with `gemini-pro` unless your team has already standardized on another tool-capable model.
- Keep temperature low for tasks that inspect code, route tools, fetch data, or summarize structured output.
- Raise output limits only when you observe truncation in real runs.
- Log provider-level errors near startup so missing credentials fail early.

---

## Groq Integration

Use `ChatGroq` when you want to connect `MCPAgent` to Groq through LangChain.

### Imports

```typescript
import { ChatGroq } from "@langchain/groq";
import { MCPAgent, MCPClient } from "mcp-use";
```

### Install

```bash
npm install @langchain/groq
```

### Environment variable

Use `GROQ_API_KEY` unless you have a very specific reason to inject the key directly at runtime.

### Full example

```typescript
import "dotenv/config";
import { ChatGroq } from "@langchain/groq";
import { MCPAgent, MCPClient } from "mcp-use";

async function main() {
  const client = new MCPClient({
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", process.cwd()],
      },
    },
  });

  const llm = new ChatGroq({
    model: "llama-3.1-70b-versatile",
    temperature: 0,
    maxTokens: 2048,
    topP: 1,
    streaming: true,
    apiKey: process.env.GROQ_API_KEY,
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
      prompt: "List the LLM providers documented in this project and compare their intended use cases.",
    });

    console.log(result);
  } finally {
    await agent.close();
  }
}

main().catch((error) => {
  console.error("Groq agent failed:", error);
  process.exitCode = 1;
});
```

### Groq options

| Option | Type | Example | Required | What it controls |
|---|---|---|---|---|
| `model` | `string` | `"llama-3.1-70b-versatile"` | Yes | Chooses the Groq-hosted model |
| `temperature` | `number` | `0` | No | Controls randomness for the final answer and tool-selection behavior |
| `maxTokens` | `number` | `2048` | No | Caps generated output length |
| `topP` | `number` | `1` | No | Adjusts nucleus sampling when you need it |
| `streaming` | `boolean` | `true` | No | Enables streaming when your app consumes partial output |
| `apiKey` | `string` | `process.env.GROQ_API_KEY` | No | Supplies the provider key explicitly |

### When to use Groq

- Use Groq when low latency is a priority and the selected model supports tool calling in your account.
- Set the model name explicitly so you can audit future upgrades.
- Use low temperature for deterministic automation and file-system style tool work.
- Validate the exact model ID in the Groq console before deployment because provider catalogs evolve quickly.

### Practical guidance

- Start with `llama-3.1-70b-versatile` unless your team has already standardized on another tool-capable model.
- Keep temperature low for tasks that inspect code, route tools, fetch data, or summarize structured output.
- Raise output limits only when you observe truncation in real runs.
- Log provider-level errors near startup so missing credentials fail early.

---

## Simplified String Format

Use string shorthand when you want `mcp-use` to create the LLM from a provider/model identifier instead of constructing the LangChain model yourself.

The format is always `"provider/model"`.
Use a supported provider prefix.
Use an exact model name that supports tool calling.

### Minimal shorthand example

In simplified mode `llm` is a string and `mcpServers` is required. The agent builds the `MCPClient` and the LangChain model internally. Do not pass `client` — it is mutually exclusive with `mcpServers`.

```typescript
import "dotenv/config";
import { MCPAgent } from "mcp-use";

// Auto-creates LLM and MCPClient from the string + mcpServers map
const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", process.cwd()],
    },
  },
});
```

### Recommended full shorthand example

```typescript
import "dotenv/config";
import { MCPAgent } from "mcp-use";
async function main() {
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
    autoInitialize: true,
    maxSteps: 20,
    memoryEnabled: false,
  });
  try {
    const result = await agent.run({
      prompt: "List the guides in this repo and identify the best starting point for an LLM setup.",
    });
    console.log(result);
  } finally {
    await agent.close();
  }
}
main().catch((error) => {
  console.error("String shorthand agent failed:", error);
  process.exitCode = 1;
});
```

### Supported shorthand providers

| Provider prefix | Example string | Required env var | Install this package |
|---|---|---|---|
| `openai` | `"openai/gpt-4o"` | `OPENAI_API_KEY` | `@langchain/openai` |
| `anthropic` | `"anthropic/claude-3-5-sonnet-20241022"` | `ANTHROPIC_API_KEY` | `@langchain/anthropic` |
| `google` | `"google/gemini-pro"` | `GOOGLE_API_KEY` | `@langchain/google-genai` |
| `groq` | `"groq/llama-3.1-70b-versatile"` | `GROQ_API_KEY` | `@langchain/groq` |

### When to choose string shorthand

- Use it for quick scripts and demos.
- Use it when provider selection comes from configuration instead of code imports.
- Use it when you do not need provider-specific constructor logic beyond simple `llmConfig` values.
- Never use it as an excuse to hide missing dependency installation or missing environment variables.

### String shorthand rules

| Rule | Why it exists |
|---|---|
| Use the exact `provider/model` shape | The internal provider resolver expects a provider prefix and a model name |
| Install the matching `@langchain/*` package | `mcp-use` still needs the provider package to be present in your project |
| Set the correct env var before startup | The shorthand does not remove the need for provider credentials |
| Keep provider names stable in config | Stable names make runtime switching and deployment easier |

---

## Provider Switching at Runtime

Switch providers between runs when you need different speed, cost, or reasoning profiles for different tasks.

Do **not** mutate a live production setup carelessly.
Do create a fresh agent or a fresh model instance when the provider, credentials, or generation settings materially change.

### Recommended strategy

| Approach | Use it when | Why it is safe |
|---|---|---|
| Create a new `MCPAgent` per run | Provider choice comes from request config or CLI flags | Each run gets a clean model and config boundary |
| Reuse one `MCPClient`, replace only the LLM | MCP server connections are expensive but the model choice changes often | You keep server sessions while swapping planning behavior |
| Recreate both client and agent | The server set also changes with the provider or environment | You avoid mixed lifecycle state |

### Runtime switching with explicit mode

```typescript
import "dotenv/config";
import { ChatOpenAI } from "@langchain/openai";
import { ChatAnthropic } from "@langchain/anthropic";
import { MCPAgent, MCPClient } from "mcp-use";
type Provider = "openai" | "anthropic";
function createLlm(provider: Provider) {
  if (provider === "openai") {
    return new ChatOpenAI({
      model: "gpt-4o",
      temperature: 0,
      apiKey: process.env.OPENAI_API_KEY,
    });
  }
  return new ChatAnthropic({
    model: "claude-3-5-sonnet-20241022",
    temperature: 0,
    apiKey: process.env.ANTHROPIC_API_KEY,
  });
}
async function main(provider: Provider) {
  const client = new MCPClient({
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", process.cwd()],
      },
    },
  });
  const agent = new MCPAgent({
    llm: createLlm(provider),
    client,
    autoInitialize: true,
    maxSteps: 20,
  });
  try {
    const result = await agent.run({
      prompt: `Summarize this repo using provider ${provider}.`,
    });
    console.log(result);
  } finally {
    await agent.close();
  }
}
main((process.argv[2] as Provider) ?? "openai").catch(console.error);
```

### Runtime switching with string shorthand

```typescript
import "dotenv/config";
import { MCPAgent } from "mcp-use";
type ProviderString =
  | "openai/gpt-4o"
  | "anthropic/claude-3-5-sonnet-20241022"
  | "google/gemini-pro"
  | "groq/llama-3.1-70b-versatile";
async function runWithModel(llm: ProviderString) {
  const agent = new MCPAgent({
    llm,
    llmConfig: { temperature: 0 },
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", process.cwd()],
      },
    },
    autoInitialize: true,
  });
  try {
    return await agent.run({
      prompt: "Describe the repository layout and identify all guide files.",
    });
  } finally {
    await agent.close();
  }
}
```

### Switching rules

- Create a new agent when the provider changes between runs.
- Reuse the client only when the MCP server topology stays the same.
- Close the previous agent before replacing it in long-lived services.
- Never assume one provider setting maps perfectly to another provider class.
- Store model names in config so switching does not require code edits.

---

## Model Requirements for Tool Calling

Use a model that can perform **tool calling** or **function calling**. This is the minimum non-negotiable requirement for useful MCP agent behavior.

### Minimum capability requirements

| Capability | Required | Why it matters | What happens if missing |
|---|---|---|---|
| Chat interface | Yes | `MCPAgent` integrates with LangChain chat models | Legacy completion-only models do not fit the expected interface well |
| Tool or function calling | Yes | The model must emit structured tool calls | The agent can only guess in plain text |
| Multi-turn reasoning | Yes | Tool results must feed back into the next model step | The agent stops after one weak attempt |
| Reasonable context window | Strongly recommended | Tool descriptions, prompts, and results consume context fast | Instructions or tool schemas may get lost |
| Streaming support | Optional | Helps UX and observability | The agent still works without it |
| Structured output support | Optional | Helpful for advanced schemas and downstream validation | Only some advanced flows need it |

### Provider-level model guidance

| Provider | Safe starting model | Why it is a good baseline |
|---|---|---|
| OpenAI | `gpt-4o` | Strong tool use, balanced latency, widely used baseline |
| Anthropic | `claude-3-5-sonnet-20241022` | Strong reasoning and good instruction following for tool-heavy flows |
| Google Gemini | `gemini-pro` | Fast and practical for many agent tasks |
| Groq | `llama-3.1-70b-versatile` | Fast serving plus broad general capability when tool calling is supported in your environment |

### Models to avoid

- Avoid legacy completion models that do not expose chat-style tool calling.
- Avoid very old or tiny chat models unless you have validated tool behavior in real tasks.
- Avoid choosing a model only because it is cheap. Bad tool selection costs more in retries and wrong answers.
- Avoid undocumented aliases in production. Use exact model IDs that your team can audit.

### Validation questions before you ship

| Question | Expected answer |
|---|---|
| Can this exact model call tools in the provider account we use? | Yes |
| Does the model stay reliable at low temperature with our MCP tool set? | Yes |
| Does the context window hold our prompt, tool list, and tool results comfortably? | Yes |
| Have we tested at least one multi-step task end to end? | Yes |

### Practical rule of thumb

If you are unsure, start with the provider examples in this guide, keep temperature at `0`, and run a real tool-calling scenario before you optimize anything else.

---

## Temperature and Generation Config

Tune generation settings for the job you actually want the agent to do.
Use lower-variance settings for tool-driven automation.
Use higher-variance settings only when the final answer needs more stylistic range or brainstorming value.

### Core knobs

| Setting | Typical type | What it changes | Use lower values when | Use higher values when |
|---|---|---|---|---|
| `temperature` | `number` | Randomness and creativity | You need deterministic tool selection and stable summaries | You want broader ideation or alternate phrasings |
| `maxTokens` / `maxOutputTokens` | `number` | Maximum completion size | The final answer is short and structured | The final answer or reasoning summary may be long |
| `topP` | `number` | Nucleus sampling | You want simple, predictable behavior | You are deliberately shaping diversity and know why |

### Recommended starting points

| Workload | Temperature | Token cap | `topP` | Why |
|---|---|---|---|---|
| File or repo inspection | `0` | `1024-2048` | `1` | Determinism matters more than style |
| Structured extraction | `0` | `1024-2048` | `1` | The tool result should be normalized consistently |
| Multi-step debugging | `0-0.2` | `2048-4096` | `1` | The agent may need more space but still needs stable tool choices |
| General assistant answers after tool calls | `0.2-0.5` | `2048-4096` | `1` | Mild flexibility helps wording without destabilizing the workflow |
| Brainstorming or ideation with optional tools | `0.5-0.8` | `2048-4096` | `0.9-1` | Creativity matters more than strict repeatability |

### OpenAI tuning example

```typescript
const llm = new ChatOpenAI({
  model: "gpt-4o",
  temperature: 0,
  maxTokens: 2048,
  topP: 1,
  streaming: true,
});
```

### Anthropic tuning example

```typescript
const llm = new ChatAnthropic({
  model: "claude-3-5-sonnet-20241022",
  temperature: 0.1,
  maxTokens: 4096,
  topP: 1,
  streaming: true,
});
```

### Gemini tuning example

```typescript
const llm = new ChatGoogleGenerativeAI({
  model: "gemini-pro",
  temperature: 0,
  maxOutputTokens: 2048,
  topP: 1,
  streaming: true,
});
```

### Groq tuning example

```typescript
const llm = new ChatGroq({
  model: "llama-3.1-70b-versatile",
  temperature: 0,
  maxTokens: 2048,
  topP: 1,
  streaming: true,
});
```

### Tuning rules

- Start with `temperature: 0` for any workflow where tools are mandatory.
- Raise temperature only after the tool flow itself is stable.
- Do not tune `temperature` and `topP` aggressively at the same time unless you are testing carefully.
- Raise the token limit only when the model truncates useful answers.
- Keep provider-specific field names straight. Gemini commonly uses `maxOutputTokens`, while several other providers use `maxTokens`.

---

## Streaming and Structured Output

`MCPAgent` exposes three additional run APIs beyond `agent.run()`. Use them when your application needs token-level streaming, structured typed output, or step-by-step event processing.

### agent.run() with optional Zod schema

Pass a Zod schema to `agent.run()` to receive a fully typed result instead of a plain string.

```typescript
import { z } from "zod";

const result = await agent.run({
  prompt: "Analyze the file structure",
  schema: z.object({
    totalFiles: z.number(),
    fileTypes: z.array(z.string()),
    largestFile: z.string(),
  }),
});
// result.totalFiles, result.fileTypes, result.largestFile are fully typed
```

| Parameter | Type | Required | What it does |
|---|---|---|---|
| `prompt` | `string` | Yes | The task the agent should perform |
| `schema` | `ZodSchema<T>` | No | When provided, the agent returns a typed object instead of a string |
| `maxSteps` | `number` | No | Per-call override for the step ceiling |
| `signal` | `AbortSignal` | No | Cancel the run via `AbortController` |

### agent.stream()

Iterate step-by-step through the agent's reasoning and tool-call sequence.

```typescript
for await (const step of agent.stream({ prompt })) {
  console.log(step.action.tool);
}
```

Use `agent.stream()` when you need to observe or react to each individual tool call or reasoning step as it happens.

### agent.prettyStreamEvents()

Stream agent events with built-in formatting for console output or logging.

```typescript
await agent.prettyStreamEvents({ prompt, maxSteps: 20 });
```

Use this API for quick observability during development or in CLI tools where formatted output is preferable to raw events.

### agent.streamEvents()

Consume low-level LangChain events emitted during the agent run. Use this to extract token chunks, tool calls, or model turn boundaries at the framework level.

```typescript
for await (const event of agent.streamEvents({ prompt })) {
  if (event.event === "on_chat_model_stream") {
    process.stdout.write(event.data?.chunk?.content || "");
  }
}
```

### Memory management

Enable conversation memory by setting `memoryEnabled: true` in the `MCPAgent` constructor. Clear the history explicitly when you want a fresh context.

```typescript
const agent = new MCPAgent({
  llm,
  client,
  memoryEnabled: true,
});

// Clear history between sessions or tenants
agent.clearConversationHistory();
```

---

## Common ❌ BAD / ✅ GOOD Patterns

Use these pairs as guardrails when you wire an LLM into `MCPAgent`.

### ❌ BAD: Starting without API key validation

```typescript
import { ChatOpenAI } from "@langchain/openai";
const llm = new ChatOpenAI({
  model: "gpt-4o",
  temperature: 0,
});
// Fails later with a provider auth error that could have been caught at startup
```

### ✅ GOOD: Failing fast when the key is missing

```typescript
import "dotenv/config";
import { ChatOpenAI } from "@langchain/openai";
if (!process.env.OPENAI_API_KEY) {
  throw new Error("OPENAI_API_KEY is required before creating ChatOpenAI.");
}
const llm = new ChatOpenAI({
  model: "gpt-4o",
  temperature: 0,
  apiKey: process.env.OPENAI_API_KEY,
});
```

---

### ❌ BAD: Choosing a model that does not support tool calling

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { MCPAgent, MCPClient } from "mcp-use";
const llm = new ChatOpenAI({
  model: "some-unknown-model",
  temperature: 0.7,
});
const agent = new MCPAgent({ llm, client: new MCPClient({ mcpServers: {} }) });
// The model may never call tools correctly
```

### ✅ GOOD: Standardizing on a known tool-capable model

```typescript
import "dotenv/config";
import { ChatAnthropic } from "@langchain/anthropic";
const llm = new ChatAnthropic({
  model: "claude-3-5-sonnet-20241022",
  temperature: 0,
  apiKey: process.env.ANTHROPIC_API_KEY,
});
```

---

### ❌ BAD: Hardcoding model names in many files

```typescript
const summaryModel = "gpt-4o";
const searchModel = "gpt-4o";
const reviewModel = "gpt-4o";
// Every future model migration now touches multiple files
```

### ✅ GOOD: Centralizing provider and model config

```typescript
export const agentModel = process.env.AGENT_MODEL ?? "openai/gpt-4o";
const agent = new MCPAgent({
  llm: agentModel,
  llmConfig: { temperature: 0 },
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", process.cwd()],
    },
  },
});
```

---

### ❌ BAD: Using high temperature for deterministic tool work

```typescript
const llm = new ChatGroq({
  model: "llama-3.1-70b-versatile",
  temperature: 1,
});
// Tool choice and phrasing become needlessly unstable
```

### ✅ GOOD: Keeping temperature low until the workflow is proven

```typescript
const llm = new ChatGroq({
  model: "llama-3.1-70b-versatile",
  temperature: 0,
  maxTokens: 2048,
  streaming: true,
});
```

---

## Quick Reference

### Minimal explicit-mode setup

```typescript
import "dotenv/config";
import { ChatOpenAI } from "@langchain/openai";
import { MCPAgent, MCPClient } from "mcp-use";
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
  apiKey: process.env.OPENAI_API_KEY,
});
const agent = new MCPAgent({ llm, client, autoInitialize: true });
const result = await agent.run({ prompt: "Describe this repo." });
console.log(result);
await agent.close();
```

### Minimal simplified-mode setup

```typescript
import "dotenv/config";
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
  autoInitialize: true,
});
const result = await agent.run({ prompt: "Describe this repo." });
console.log(result);
await agent.close();
```

### Decision table

| If you need... | Use... |
|---|---|
| Maximum provider control | Explicit mode |
| Runtime model selection from config | String shorthand or a factory |
| The shortest first script | String shorthand |
| Fine-grained provider constructors | Explicit mode |

---

## Checklist

Before you consider the integration complete, verify each item below.

1. A chat model from the correct `@langchain/*` package is installed.
2. The provider API key exists in the environment before startup.
3. The selected model supports tool calling in the provider account you use.
4. The `MCPAgent` imports come from `"mcp-use"`.
5. The provider model import comes from the matching `@langchain/*` package.
6. The agent closes cleanly after each script or request lifecycle.
7. Temperature is low for tool-driven workflows unless you intentionally chose otherwise.
8. The model name is centralized in config or constants instead of scattered across files.
9. You have run at least one real tool-calling task end to end.
10. You have documented the chosen provider and model for future maintainers.

## Appendix: Provider Selection Notes

- Use OpenAI when you want a familiar baseline and strong tool-calling behavior.
- Use Anthropic when instruction fidelity and detailed explanations matter most.
- Use Gemini when speed and pragmatic general performance are your priority.
- Use Groq when low-latency serving is valuable and the chosen model has been validated for tool use.
- Never switch providers in production without re-running tool-calling smoke tests.
- Never assume model aliases remain stable forever. Pin exact names deliberately.
- Document provider-specific field names so teammates do not confuse `maxTokens` and `maxOutputTokens`.
- Prefer one well-tested model per environment over many half-tested options.
- Keep examples runnable. Complete imports and explicit env vars reduce copy-paste failures.
- Use runtime factories when you need per-tenant or per-environment provider selection.
- Use explicit mode for advanced tracing, callbacks, or nontrivial provider setup.
- Use simplified mode when you need compact code and predictable bootstrap patterns.
- Verify tool calling with a real MCP server, not just a plain text prompt.
- Keep your examples imperative and concrete so maintainers can apply them immediately.
- Prefer early failure for credential issues because delayed auth errors waste debugging time.
- Treat generation tuning as a workload decision, not a provider identity decision.
- Start conservative. Optimize only after you confirm correctness.
- Use provider-specific docs to verify the newest model names before rollout.
- Record the chosen model in deployment config, not just in local scripts.
- Re-test when upgrading `mcp-use`, LangChain packages, or provider SDK behavior.

## FAQ

### Do I have to use LangChain chat models?

Yes. In the `mcp-use` agent context described here, the agent uses LangChain chat model classes or the string shorthand that resolves to those classes.

### Do I need streaming?

No. Streaming is optional, but it improves UX and observability when your app can consume partial output.

### Can I reuse one `MCPClient` with multiple models?

Yes. Reuse the client when the server set stays the same and only the model choice changes.

### Can I mix provider examples in one repo?

Yes. Install only the packages you actually use in production, but keeping multiple examples in docs is fine.

### Should I hide model names deep inside helper code?

No. Prefer a visible constant or environment variable so provider migrations are simple and reviewable.

### What should I test first?

Run a task that definitely requires at least one MCP tool call, then verify the model actually calls the tool and uses the result.

### Why keep temperature low?

Because tool-driven workflows need stable planning and stable argument construction more than stylistic variety.

### When should I choose explicit mode?

Choose it when you need full constructor control, custom callbacks, tracing, or advanced lifecycle ownership.

### When should I choose shorthand mode?

Choose it when you want the shortest path to a valid agent and your provider config is simple.

### What breaks most often?

Missing environment variables, unsupported models, and inconsistent model naming conventions break the most setups.
