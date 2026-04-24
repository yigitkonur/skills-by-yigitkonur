# Common Errors — MCPAgent Troubleshooting Guide

A comprehensive reference for every error you are likely to encounter when building agents with `mcp-use`. Each scenario includes when it fires, root cause, fix steps with code, and prevention guidance.

---

## LLM Connection Errors

---

### Error: LangChain provider throws "API key not found" or "Incorrect API key"

**When:** The LangChain model you pass to `llm` cannot authenticate with the provider because the API key environment variable is missing or incorrect.

**Cause:** LangChain model classes (`ChatOpenAI`, `ChatAnthropic`, etc.) read the API key from a standard environment variable (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.) when the `apiKey` option is not explicitly set in the constructor. If that env var is absent, the provider client throws an authentication error before the first API call.

**Fix:**
1. Set the environment variable before starting your process:
```bash
export OPENAI_API_KEY="sk-proj-..."
# or for other providers:
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="AIza..."
export GROQ_API_KEY="gsk_..."
```
2. Alternatively, pass the key explicitly in the LangChain constructor (explicit mode):
```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
    },
  },
});

const agent = new MCPAgent({
  llm: new ChatOpenAI({
    model: "gpt-4o",
    apiKey: process.env.MY_CUSTOM_KEY_VAR,
  }),
  client,
});
```
3. If using a `.env` file, make sure `dotenv` is loaded at the top of your entry point:
```typescript
import "dotenv/config";
import { MCPAgent } from "mcp-use";
```

**Prevention:** Create a startup check that validates all required env vars before constructing the LangChain model. Use a `.env.example` file in your repository so collaborators know which keys are needed.

---

### Error: "Cannot find module '@langchain/openai'" / "Module not found"

**When:** You import a LangChain provider class (e.g., `ChatOpenAI`, `ChatAnthropic`) but the corresponding package is not installed.

**Cause:** `mcp-use` uses LangChain under the hood. Each LLM provider is a separate npm package that must be installed explicitly. Importing a class from an uninstalled package fails with a module resolution error.

**Fix:**
1. Install the correct provider package for your LLM:
```bash
# OpenAI (GPT-4o, GPT-4, GPT-3.5, o1, o3)
npm install @langchain/openai

# Anthropic (Claude 4, Claude 3.5)
npm install @langchain/anthropic

# Google Generative AI (Gemini)
npm install @langchain/google-genai

# Groq
npm install @langchain/groq

# AWS Bedrock
npm install @langchain/aws
```
2. Verify the import works in isolation:
```typescript
import { ChatOpenAI } from "@langchain/openai";
console.log("Provider package loaded successfully");
```
3. If using a monorepo, make sure the package is installed in the correct workspace.

**Prevention:** Add the provider package to your `dependencies` (not `devDependencies`) so it is always available in production. Pin to current stable versions — note that `mcp-use` jumped from the `0.1.x` line directly to `1.x` (no `0.6.x` ever existed on npm), so any range like `^0.6.0` will fail to install:
```json
{
  "dependencies": {
    "mcp-use": "^1.25.0",
    "@langchain/openai": "^1.4.0"
  }
}
```
Verify the current latest with `npm view mcp-use version` before committing — versions drift over time.

---

### Error: Wrong type passed to `llm` — must be a LangChain model instance or a "provider/model" string

**When:** You pass an incorrect value to the `llm` constructor option of `MCPAgent`. Common mistakes include passing a plain model name string (`"gpt-4o"`) without the provider prefix, or passing an object literal that is not a LangChain `BaseChatModel`.

**Cause:** `MCPAgent` supports two construction modes with different `llm` requirements:
- **Explicit mode**: `llm` must be an instantiated LangChain `BaseChatModel` object; you also pass a `client: MCPClient` instance.
- **Simplified mode**: `llm` must be a `"provider/model"` format string (e.g. `"openai/gpt-4o"`); you pass `mcpServers` inline and the agent manages the client internally.

Passing a bare model name (`"gpt-4o"`) to simplified mode, or passing an object literal instead of a proper LangChain instance to explicit mode, causes a type error or runtime crash.

**Fix:**
1. Use simplified mode — `llm` as a `"provider/model"` string with inline `mcpServers`:
```typescript
import { MCPAgent } from "mcp-use";

// ❌ Wrong — bare model name is not a valid provider/model string
const bad = new MCPAgent({ llm: "gpt-4o" as any, mcpServers: {} });

// ✅ Correct — simplified mode with "provider/model" string
const good = new MCPAgent({
  llm: "openai/gpt-4o",   // must be "provider/model" format
  mcpServers: {
    myServer: { command: "node", args: ["server.js"] },
  },
});
```
2. Or use explicit mode — `llm` as a LangChain model instance with a separate `MCPClient`:
```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({
  mcpServers: {
    myServer: { command: "node", args: ["server.js"] },
  },
});

const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),  // LangChain BaseChatModel instance
  client,
});
```
3. Supported LangChain model classes and their packages (for explicit mode):
```bash
npm install @langchain/openai        # ChatOpenAI
npm install @langchain/anthropic     # ChatAnthropic
npm install @langchain/google-genai  # ChatGoogleGenerativeAI
npm install @langchain/groq          # ChatGroq
npm install @langchain/aws           # ChatBedrockConverse
npm install @langchain/mistralai     # ChatMistralAI (community)
```

**Prevention:** Use TypeScript — the `llm` parameter type is a discriminated union. In explicit mode it is `BaseChatModel`; in simplified mode it is a string. The compiler will reject mismatches at build time.

---

### Error: Unsupported LLM provider — how to use any LangChain-compatible model

**When:** You want to use an LLM provider that is not OpenAI, Anthropic, Google, or Groq.

**Cause:** `MCPAgent` accepts any object that satisfies the LangChain `BaseChatModel` interface. There is no built-in restriction on which providers you can use — you simply import and instantiate the appropriate class.

**Fix:**
Instantiate the LangChain model for your provider and pass it directly:
```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatMistralAI } from "@langchain/mistralai";

const llm = new ChatMistralAI({
  model: "mistral-large-latest",
  apiKey: process.env.MISTRAL_API_KEY,
});

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
    },
  },
});

const agent = new MCPAgent({ llm, client });
try {
  await agent.run({ prompt: "List files in /tmp" });
} finally {
  await agent.close();
}
```

**Prevention:** Install the LangChain integration package for your provider before creating the agent. Check the LangChain docs for the list of available integrations.

---

### Error: "Rate limit exceeded" / HTTP 429

**When:** Your agent makes too many LLM API calls in a short period, especially with low `maxSteps` retries or rapid sequential `agent.run()` calls.

**Cause:** LLM providers enforce rate limits (requests-per-minute and tokens-per-minute). Agents that loop with tool calls can exhaust limits quickly because each step triggers a separate API call.

**Fix:**
1. Reduce `maxSteps` to cap the number of LLM calls per run:
```typescript
import { MCPAgent } from "mcp-use";

// Simplified mode — llm as "provider/model" string with inline mcpServers
const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  maxSteps: 10,
  mcpServers: {
    myServer: { command: "node", args: ["server.js"] },
  },
});
```
2. Add retry logic with exponential backoff around `agent.run()`:
```typescript
async function runWithRetry(agent: MCPAgent, prompt: string, retries = 3) {
  for (let i = 0; i < retries; i++) {
    try {
      return await agent.run({ prompt });
    } catch (err: any) {
      if (err.message?.includes("429") && i < retries - 1) {
        const delay = Math.pow(2, i) * 1000;
        console.log(`Rate limited. Retrying in ${delay}ms...`);
        await new Promise((r) => setTimeout(r, delay));
      } else {
        throw err;
      }
    }
  }
}
```
3. Use a cheaper/faster model for high-volume tasks:
```typescript
// Simplified mode — switch to a smaller model by changing the string
const agent = new MCPAgent({
  llm: "openai/gpt-4o-mini",
  mcpServers: { /* ... */ },
});
```

**Prevention:** Monitor your API usage dashboards. Set billing alerts. Use `gpt-4o-mini` or `claude-haiku-4-5` for tasks that do not require top-tier reasoning. Batch requests where possible rather than making many small agent runs.

---

### Error: "Request timeout" / ETIMEDOUT

**When:** The LLM API call takes too long and the HTTP client aborts the request. Common with large prompts, complex tool-call chains, or when providers experience outages.

**Cause:** Default timeout settings in the HTTP client are too short for the request payload size. Provider-side load spikes can also cause slowdowns beyond the timeout threshold.

**Fix:**
1. Increase the timeout via explicit mode configuration. In `@langchain/openai@1.x`, the canonical placement is under `configuration: { ... }` (forwarded to the underlying `openai` SDK client). The top-level `timeout` and `maxRetries` are still accepted as backwards-compatible aliases, but `configuration` is the form you want for new code:
```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const llm = new ChatOpenAI({
  model: "gpt-4o",
  configuration: {
    timeout: 120_000,   // 120 seconds — forwarded to the OpenAI SDK
    maxRetries: 3,      // forwarded to the OpenAI SDK
  },
});

const client = new MCPClient({
  mcpServers: {
    myServer: { command: "node", args: ["server.js"] },
  },
});

const agent = new MCPAgent({ llm, client });
```
2. Reduce prompt size by being more concise in your system prompts and user messages.
3. Check provider status pages for outages before debugging further.

**Prevention:** Always set explicit timeouts and retries when creating LLM instances for production. Monitor latency metrics and set up alerts for p95 response times.

---

## Tool Call Errors

---

### Error: "Tool execution failed: [tool_name]"

**When:** The agent calls an MCP tool and the tool's server returns an error response. This surfaces as a tool call failure in the agent's step log.

**Cause:** The MCP server tool encountered an internal error — file not found, permission denied, invalid arguments, or an unhandled exception in the server code. The agent receives the error and may attempt to retry or report failure.

**Fix:**
1. Enable verbose mode to see the full tool call and response:
```typescript
import { MCPAgent } from "mcp-use";

// Simplified mode — use "provider/model" string with inline mcpServers
const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  verbose: true,
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
    },
  },
});
```
2. Check that the tool arguments sent by the LLM are valid. The verbose output shows the exact JSON arguments.
3. Test the MCP server tool independently to confirm it works outside of the agent:
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"read_file","arguments":{"path":"/tmp/test.txt"}}}' | npx -y @modelcontextprotocol/server-filesystem /tmp
```
4. Add a more descriptive `systemPrompt` to guide the LLM toward correct tool usage:
```typescript
const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  systemPrompt: "When using the read_file tool, always provide an absolute path.",
  mcpServers: { /* ... */ },
});
```

**Prevention:** Write clear tool descriptions in your MCP server. The better the tool description, the more accurately the LLM will call it. Validate tool arguments server-side and return descriptive error messages.

---

### Error: "Tool not found: 'search_files'"

**When:** The LLM tries to call a tool name that does not exist on any connected MCP server. This can also appear as `"No tool named 'X' available"`.

**Cause:** The LLM hallucinated a tool name, or the expected MCP server is not connected, or the tool was renamed/removed from the server. This is common when the LLM has been trained on older versions of an MCP server's tool list.

**Fix:**
1. List available tools by enabling verbose mode — the tool discovery log shows all registered tools.
2. Use `disallowedTools` to block known problematic tool names so the LLM does not attempt them:
```typescript
import { MCPAgent } from "mcp-use";

const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  disallowedTools: ["search_files", "deprecated_tool"],
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
    },
  },
});
```
3. Add a system prompt that explicitly lists the available tools:
```typescript
const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  systemPrompt: `You have access to these tools only: read_file, write_file, list_directory. Do not try to call any other tools.`,
  mcpServers: { /* ... */ },
});
```

**Prevention:** Keep your MCP server tool names stable across versions. Use `disallowedTools` to proactively block names that LLMs commonly hallucinate.

---

### Error: Tool call timeout — server not responding

**When:** The agent calls an MCP tool but the server never responds. The call hangs until the internal timeout fires, or the agent step limit is exceeded while waiting.

**Cause:** The MCP server process is alive but stuck — a blocking I/O operation, infinite loop, or resource contention. Less commonly, the server process exited mid-call and the transport layer did not detect it.

**Fix:**
1. Set explicit timeouts on the MCP server configuration:
```typescript
import { MCPAgent } from "mcp-use";

const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  mcpServers: {
    slowServer: {
      command: "node",
      args: ["slow-server.js"],
      env: { TIMEOUT: "30000" },
    },
  },
});
```
2. Test the server in isolation to confirm it responds within a reasonable time.
3. If the server is doing heavy computation, break the operation into smaller chunks on the server side.
4. Reduce `maxSteps` so the agent does not wait indefinitely:
```typescript
const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  maxSteps: 5,
  mcpServers: { /* ... */ },
});
```

**Prevention:** Implement timeouts inside your MCP server tools. Return partial results with an indication that the operation was truncated rather than hanging forever.

---

### Error: "Failed to parse tool result as JSON"

**When:** An MCP tool returns a response that cannot be parsed as valid JSON, or returns malformed content that the agent framework cannot interpret.

**Cause:** The MCP server tool is returning raw text, HTML, binary data, or truncated JSON instead of a proper MCP tool response. This can also happen when the server writes debug output (e.g. `console.log`) to stdout, which corrupts the JSON-RPC stream.

**Fix:**
1. Ensure your MCP server only writes JSON-RPC messages to stdout. All debug output must go to stderr:
```typescript
// ❌ Wrong — pollutes the JSON-RPC stdout stream
console.log("Debug: processing request");

// ✅ Correct — debug output on stderr
console.error("Debug: processing request");
```
2. Verify your tool returns properly structured content:
```typescript
// In your MCP server tool handler
return {
  content: [
    { type: "text", text: JSON.stringify(result) },
  ],
};
```
3. Enable verbose mode on the agent to inspect the raw response bytes.

**Prevention:** Always use `console.error()` for logging in MCP servers. Test your server tools independently and validate that stdout only contains valid JSON-RPC messages. Pipe stderr to a log file during development.

---

## Agent Lifecycle Errors

---

### Error: "Agent exceeded maximum steps (maxSteps: 25)"

**When:** The agent reaches the `maxSteps` limit without completing the task. The run terminates and returns the last intermediate result.

**Cause:** The task is too complex for the allotted step budget, the LLM is looping (calling the same tool repeatedly with the same arguments), or the system prompt is not guiding the LLM toward a solution efficiently.

**Fix:**
1. Increase `maxSteps` if the task genuinely requires more steps:
```typescript
import { MCPAgent } from "mcp-use";

const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  maxSteps: 50,
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
    },
  },
});
```
2. Improve the system prompt to reduce unnecessary steps:
```typescript
const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  maxSteps: 15,
  systemPrompt: "Be concise. Complete the task in as few tool calls as possible. Do not repeat tool calls with the same arguments.",
  mcpServers: { /* ... */ },
});
```
3. Break complex tasks into smaller sequential agent runs:
```typescript
const result1 = await agent.run({ prompt: "List all .ts files in /src" });
const result2 = await agent.run({ prompt: `Analyze these files: ${result1}` });
```

**Prevention:** Profile your agent's step count during development. Set `maxSteps` to 2x the typical number of steps needed, with a hard upper bound. Use `verbose: true` to identify and eliminate looping patterns.

---

### Error: "Agent not initialized — call initialize() first"

**When:** You call `agent.run({ prompt, manageConnector: false })` (or `stream` / `streamEvents` / `prettyStreamEvents` with `manageConnector: false`) on an agent that was never initialized, AND `autoInitialize` is left at its default of `false`.

**Cause:** Normal `agent.run({ prompt })` usage **never** triggers this error: `run` delegates to `stream`, whose default `manageConnector` is `true`, which auto-initializes on first call. The error only fires when **all three** of these are simultaneously true:
1. You explicitly pass `manageConnector: false` in the `RunOptions` (opting out of automatic init), AND
2. `autoInitialize: false` (the default), AND
3. You never called `await agent.initialize()` manually.

**Fix:**
1. The simplest fix is to drop `manageConnector: false` and let the default (`true`) handle initialization automatically:
```typescript
import { MCPAgent } from "mcp-use";

const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  mcpServers: { /* ... */ },
});

// No `manageConnector: false` — the agent auto-initializes on first run.
const result = await agent.run({ prompt: "Hello" });
```
2. If you intentionally pass `manageConnector: false` (e.g. to share lifecycle across multiple runs), call `initialize()` once up-front:
```typescript
import { MCPAgent } from "mcp-use";

const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  mcpServers: { /* ... */ },
});

await agent.initialize();
const r1 = await agent.run({ prompt: "Task 1", manageConnector: false });
const r2 = await agent.run({ prompt: "Task 2", manageConnector: false });
await agent.close();
```
3. Or set `autoInitialize: true` so the agent initializes on first call even when `manageConnector: false`:
```typescript
const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  autoInitialize: true,            // fallback init when manageConnector is false
  mcpServers: { /* ... */ },
});

const result = await agent.run({ prompt: "Hello", manageConnector: false });
```

**Prevention:** Hitting this error almost always means `manageConnector: false` was set somewhere in the call. Audit your call sites for that flag. Default `run({ prompt })` usage initializes automatically — if you have not opted out, look elsewhere for the bug.

---

### Error: "Agent is already closed"

**When:** You call `agent.run()`, `agent.stream()`, or other methods on an agent after calling `agent.close()`.

**Cause:** `agent.close()` shuts down all MCP server connections and cleans up resources. The agent instance is no longer usable after this call.

**Fix:**
1. Create a new agent instance if you need to run again after closing:
```typescript
import { MCPAgent } from "mcp-use";

const serverConfig = {
  filesystem: {
    command: "npx",
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
  },
};

// Simplified mode — llm as "provider/model" string
let agent = new MCPAgent({ llm: "openai/gpt-4o", mcpServers: serverConfig });
await agent.run({ prompt: "List files" });
await agent.close();

// ❌ This throws — agent is closed
// await agent.run({ prompt: "List files again" });

// ✅ Create a new agent
agent = new MCPAgent({ llm: "openai/gpt-4o", mcpServers: serverConfig });
await agent.run({ prompt: "List files again" });
await agent.close();
```
2. Structure your code so `close()` is called only in cleanup/shutdown paths:
```typescript
const agent = new MCPAgent({ llm: "openai/gpt-4o", mcpServers: serverConfig });
try {
  const r1 = await agent.run({ prompt: "Task 1" });
  const r2 = await agent.run({ prompt: "Task 2" });
  console.log(r1, r2);
} finally {
  await agent.close();
}
```

**Prevention:** Use `try/finally` to ensure `close()` is only called once at the end of your agent's lifecycle. Never call `close()` between sequential runs on the same agent.

---

### Error: Memory overflow — conversation history grows unbounded

**When:** Your agent runs many sequential tasks with `memoryEnabled: true` (the default), and each run appends to the conversation history. Eventually, the context window is exceeded and the LLM API rejects the request or truncates silently.

**Cause:** By default, `MCPAgent` retains full conversation history across `run()` calls so the agent can reference previous results. Over many calls, this accumulates thousands of tokens.

**Fix:**
1. Clear history between runs when context is not needed:
```typescript
import { MCPAgent } from "mcp-use";

const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  memoryEnabled: true,
  mcpServers: { /* ... */ },
});

const result1 = await agent.run({ prompt: "Analyze /tmp/data.csv" });
agent.clearConversationHistory();

const result2 = await agent.run({ prompt: "Analyze /tmp/other.csv" });
agent.clearConversationHistory();
```
2. Disable memory entirely for independent tasks:
```typescript
const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  memoryEnabled: false,
  mcpServers: { /* ... */ },
});
```
3. For long-running agents, implement periodic history trimming:
```typescript
let runCount = 0;
const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  memoryEnabled: true,
  mcpServers: { /* ... */ },
});

async function runTask(prompt: string) {
  runCount++;
  if (runCount % 10 === 0) {
    agent.clearConversationHistory();
  }
  return agent.run({ prompt });
}
```

**Prevention:** Always decide upfront whether your agent needs cross-run memory. For batch processing and independent tasks, disable memory or clear it between runs. Monitor token counts in verbose mode.

---

## Schema / Structured Output Errors

---

### Error: "Structured output validation failed"

**When:** You pass a Zod `schema` to `agent.run()` and the LLM's response does not match the schema shape. The response parsing throws a Zod validation error.

**Cause:** The LLM produced output that does not conform to the expected types, is missing required fields, or contains extra fields. This is common with smaller/cheaper models that struggle with structured generation.

**Fix:**
1. Use `.describe()` on every Zod field to guide the LLM:
```typescript
import { MCPAgent } from "mcp-use";
import { z } from "zod";

const WeatherSchema = z.object({
  city: z.string().describe("The city name"),
  temperature: z.number().describe("Temperature in Celsius"),
  conditions: z.string().describe("Weather conditions like 'sunny', 'rainy', 'cloudy'"),
});

const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  mcpServers: {
    weather: { command: "node", args: ["weather-server.js"] },
  },
});

const result = await agent.run({
  prompt: "What is the weather in Tokyo?",
  schema: WeatherSchema,
});

console.log(result); // { city: "Tokyo", temperature: 22, conditions: "sunny" }
await agent.close();
```
2. Use a more capable model — `gpt-4o` and `claude-sonnet` handle schemas much better than `gpt-4o-mini`.
3. Simplify the schema — flatten nested objects and reduce the number of fields.

**Prevention:** Always use `.describe()` on Zod fields. Test your schema with the target model before deploying. Keep schemas under 10 fields when possible.

---

### Error: Schema too complex for LLM to produce matching output

**When:** The LLM consistently fails to produce output matching a deeply nested or highly constrained Zod schema, even with `.describe()` annotations.

**Cause:** LLMs have limits on how complex a structured output they can reliably produce. Deeply nested objects, recursive types, discriminated unions, and schemas with many constraints increase failure rates.

**Fix:**
1. Flatten the schema:
```typescript
import { z } from "zod";

// ❌ Too complex — nested object with array of objects
const ComplexSchema = z.object({
  report: z.object({
    sections: z.array(z.object({
      title: z.string(),
      paragraphs: z.array(z.object({
        text: z.string(),
        citations: z.array(z.string()),
      })),
    })),
  }),
});

// ✅ Flattened — easier for the LLM to produce
const SimpleSchema = z.object({
  title: z.string().describe("Report title"),
  summary: z.string().describe("Report summary in 2-3 sentences"),
  keyFindings: z.array(z.string()).describe("List of key findings as strings"),
  sources: z.array(z.string()).describe("List of source URLs or references"),
});
```
2. Break complex outputs into multiple agent runs with simpler schemas.
3. Use `gpt-4o` or `claude-sonnet-4-5` — they have the best structured output adherence.

**Prevention:** Design schemas with the LLM's capabilities in mind. Test with the cheapest model first — if `gpt-4o-mini` can handle it, any model can.

---

### Error: Missing .describe() on schema fields — LLM produces wrong types

**When:** Zod schema fields lack `.describe()` annotations and the LLM guesses the wrong format. For example, a `temperature` field is returned as a string `"22°C"` instead of a number `22`.

**Cause:** Without `.describe()`, the LLM only sees the field name and type. Field names are often ambiguous — `temperature` could be Celsius, Fahrenheit, or a string with a unit suffix.

**Fix:**
1. Add explicit `.describe()` with format instructions:
```typescript
import { z } from "zod";

// ❌ Ambiguous — LLM may guess wrong format
const Bad = z.object({
  temperature: z.number(),
  date: z.string(),
  active: z.boolean(),
});

// ✅ Clear — LLM knows exactly what to produce
const Good = z.object({
  temperature: z.number().describe("Temperature in Celsius as a number, e.g. 22.5"),
  date: z.string().describe("Date in ISO 8601 format, e.g. '2025-01-15'"),
  active: z.boolean().describe("Whether the sensor is currently active (true/false)"),
});
```

**Prevention:** Treat `.describe()` as mandatory for every schema field. Include example values in the description to eliminate ambiguity.

---

## Streaming Errors

---

### Error: Stream iteration error — exception thrown mid-stream

**When:** You are iterating over `agent.stream()` or `agent.streamEvents()` and an error is thrown partway through — for example, the LLM API returns a 500 error after streaming has started.

**Cause:** Streaming connections are long-lived and can fail at any point. Network interruptions, provider-side errors, or MCP server crashes during a tool call can all cause mid-stream failures.

**Fix:**
1. Wrap the stream iteration in a try/catch:
```typescript
import { MCPAgent } from "mcp-use";

const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
    },
  },
});

try {
  for await (const event of agent.streamEvents({ prompt: "List all files in /tmp" })) {
    if (event.event === "on_chat_model_stream") {
      // content is the primary field; text is used by older LangChain versions
      const token = event.data?.chunk?.content ?? event.data?.chunk?.text;
      if (token) process.stdout.write(String(token));
    }
  }
} catch (err) {
  console.error("Stream error:", err);
} finally {
  await agent.close();
}
```
2. Implement retry logic at the stream level:
```typescript
async function streamWithRetry(agent: MCPAgent, prompt: string, retries = 2) {
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      for await (const event of agent.streamEvents({ prompt })) {
        if (event.event === "on_chat_model_stream") {
          // content is the primary field; text is used by older LangChain versions
          const token = event.data?.chunk?.content ?? event.data?.chunk?.text;
          if (token) process.stdout.write(String(token));
        }
      }
      return; // success
    } catch (err) {
      if (attempt < retries) {
        console.error(`Stream attempt ${attempt + 1} failed, retrying...`);
        agent.clearConversationHistory();
      } else {
        throw err;
      }
    }
  }
}
```

**Prevention:** Always wrap streaming in try/catch. Consider using `agent.run()` instead of streaming for critical tasks where you need guaranteed complete output.

---

### Error: Stream cleanup failure — resource leak after error

**When:** A stream errors out but `agent.close()` is never called because the error jumps past the cleanup code. Over time, orphaned MCP server processes accumulate.

**Cause:** Without a `finally` block, errors during streaming skip the cleanup path. Each agent that is not closed leaves child processes (MCP servers) running.

**Fix:**
1. Always use `try/finally` with stream iteration:
```typescript
import { MCPAgent } from "mcp-use";

const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  mcpServers: {
    myServer: { command: "node", args: ["server.js"] },
  },
});

try {
  for await (const event of agent.streamEvents({ prompt: "Do something" })) {
    // process events
  }
} catch (err) {
  console.error("Stream failed:", err);
} finally {
  await agent.close();
}
```
2. For Express/Fastify servers, register a shutdown handler:
```typescript
process.on("SIGTERM", async () => {
  await agent.close();
  process.exit(0);
});
```

**Prevention:** Establish a project convention that every `new MCPAgent()` has a corresponding `agent.close()` in a `finally` block. Use linting rules or code review checklists to enforce this.

---

### Error: Stream timeout — no events received

**When:** You call `agent.stream()` or `agent.streamEvents()` and the async iterator never yields any events, appearing to hang.

**Cause:** The LLM provider may not support streaming, the network connection may be blocked, or the MCP server initialization is taking too long before the agent can start producing events.

**Fix:**
1. Verify that streaming is supported by your LLM provider. Not all providers and models support streaming:
```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

// Ensure streaming is explicitly enabled
const llm = new ChatOpenAI({
  model: "gpt-4o",
  streaming: true,
});

const client = new MCPClient({
  mcpServers: { /* ... */ },
});

const agent = new MCPAgent({ llm, client });
```
2. Add a timeout wrapper around the stream:
```typescript
function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  return Promise.race([
    promise,
    new Promise<never>((_, reject) =>
      setTimeout(() => reject(new Error(`Timeout after ${ms}ms`)), ms)
    ),
  ]);
}
```
3. Use `agent.prettyStreamEvents()` for development — it handles formatting and may surface issues more clearly.

**Prevention:** Test streaming in isolation before integrating into your application. Use `agent.run()` as a fallback when streaming is unreliable.

---

## Server Connection Errors

---

### Error: "Failed to spawn MCP server: command not found 'uvx'"

**When:** The `command` specified in `mcpServers` config does not exist on the system PATH. This commonly happens with Python-based MCP servers that require `uvx`, `pipx`, or a specific Python environment.

**Cause:** The MCP server process is started via `child_process.spawn()`. If the command binary is not found, the spawn fails immediately.

**Fix:**
1. Install the required command:
```bash
# For uvx (Python UV package runner)
pip install uv

# For npx (Node.js package runner) — comes with npm
npm install -g npm

# For pipx
pip install pipx
```
2. Use the full absolute path if the command is installed in a non-standard location:
```typescript
import { MCPAgent } from "mcp-use";

const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  mcpServers: {
    pythonServer: {
      command: "/usr/local/bin/uvx",
      args: ["my-mcp-server"],
    },
  },
});
```
3. For Node.js-based servers, prefer `npx` with the `-y` flag:
```typescript
mcpServers: {
  filesystem: {
    command: "npx",
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
  },
}
```

**Prevention:** Document all system-level dependencies in your project's README. Use a setup script that verifies all required commands are available. In Docker, install all dependencies in the Dockerfile.

---

### Error: Server connection timeout — server slow to start

**When:** The MCP server process starts but takes too long to become ready. The agent times out waiting for the server's initialization handshake.

**Cause:** The server is downloading dependencies on first run (e.g., `npx -y` fetching a package), performing heavy startup initialization, or waiting for an external resource (database, API).

**Fix:**
1. Pre-install packages so `npx` does not need to download them:
```bash
npm install @modelcontextprotocol/server-filesystem
```
Then use the package's direct JS entry (resolved against the current working directory). Do **not** point `node` at `node_modules/.bin/<name>` — `.bin` entries are shebang-script symlinks on Unix and `.cmd` wrappers on Windows, so `node` will throw `SyntaxError: Unexpected token` on the first line:
```typescript
import path from "node:path";

mcpServers: {
  filesystem: {
    command: "node",
    args: [
      path.resolve(
        process.cwd(),
        "node_modules/@modelcontextprotocol/server-filesystem/dist/index.js",
      ),
      "/tmp",
    ],
  },
}
```
Or, simpler: keep `npx` but pass `--no-install` so it uses the locally installed copy without touching the registry:
```typescript
mcpServers: {
  filesystem: {
    command: "npx",
    args: ["--no-install", "@modelcontextprotocol/server-filesystem", "/tmp"],
  },
}
```
2. For custom servers, optimize startup time — defer heavy initialization until the first tool call.
3. Increase the connection timeout if your server legitimately needs more time:
```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    slowServer: {
      command: "node",
      args: ["heavy-server.js"],
    },
  },
});
// The client will wait for the server to be ready during initialization
```

**Prevention:** Benchmark your server's startup time. Keep it under 5 seconds. If the server needs heavy initialization, do it lazily on first tool call.

---

### Error: Server crash during operation — mid-task server failure

**When:** An MCP server process exits unexpectedly while the agent is mid-task. The agent receives a broken pipe or connection reset error.

**Cause:** The server process ran out of memory, hit an unhandled exception, received a signal (SIGKILL/SIGTERM), or its underlying resources became unavailable.

**Fix:**
1. Enable verbose mode to see the server's exit code and signal:
```typescript
import { MCPAgent } from "mcp-use";

const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  verbose: true,
  mcpServers: {
    myServer: { command: "node", args: ["server.js"] },
  },
});
```
2. Check the server's stderr output — crash messages are written there:
```bash
node server.js 2>server-errors.log
```
3. Wrap agent runs with crash recovery:
```typescript
async function runWithRecovery(config: any, prompt: string) {
  let agent = new MCPAgent(config);
  try {
    return await agent.run({ prompt });
  } catch (err: any) {
    if (err.message?.includes("EPIPE") || err.message?.includes("connection")) {
      console.error("Server crashed, creating new agent...");
      await agent.close().catch(() => {});
      agent = new MCPAgent(config);
      return await agent.run({ prompt });
    }
    throw err;
  } finally {
    await agent.close();
  }
}
```

**Prevention:** Stress-test your MCP server with large payloads and concurrent requests. Set memory limits and add global error handlers in the server process. To handle mid-task crashes, use the recovery pattern shown above — catch `EPIPE` / connection errors from `agent.run()` and recreate the agent (which re-spawns the server process via a fresh `initialize()` call). Note that `useServerManager: true` provides **dynamic server selection** (the LLM picks which configured server to connect to via management tools), not automatic reconnection of crashed processes.

---

## Configuration Errors

---

### Error: TypeScript error when mixing simplified and explicit mode

**When:** You construct `MCPAgent` with a mismatched combination of `llm`, `client`, and `mcpServers` options, causing a runtime error or TypeScript type mismatch.

**Cause:** `MCPAgent` supports two construction styles. Mixing fields from both styles produces undefined behavior or type errors at compile time.

**Fix:**

`MCPAgent` uses a TypeScript discriminated union for its constructor options — `ExplicitModeOptions` and `SimplifiedModeOptions` are mutually exclusive:

- **Explicit mode** (`ExplicitModeOptions`): requires a `client: MCPClient` instance and a LangChain `BaseChatModel` for `llm`. The `mcpServers` field is `never` in this type — it must not be used.
- **Simplified mode** (`SimplifiedModeOptions`): requires `llm` as a `"provider/model"` string and inline `mcpServers`. The `client` field is `never` in this type.

1. Style A — explicit mode: separate `MCPClient` with a LangChain `llm` instance:
```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const llm = new ChatOpenAI({ model: "gpt-4o" });
const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
    },
  },
});

const agent = new MCPAgent({ llm, client });
try {
  await agent.run({ prompt: "List files in /tmp" });
} finally {
  await agent.close();
  await client.closeAllSessions();
}
```
2. Style B — simplified mode: `llm` as a `"provider/model"` string with inline `mcpServers` (agent manages the client internally):
```typescript
import { MCPAgent } from "mcp-use";

const agent = new MCPAgent({
  llm: "openai/gpt-4o",               // must be "provider/model" string — NOT a LangChain instance
  mcpServers: {
    // Key = server name (arbitrary)
    myServer: {
      command: "node",                    // required: executable
      args: ["path/to/server.js"],        // required: array of string args
      env: {                              // optional: environment variables
        API_KEY: "secret",
        NODE_ENV: "production",
      },
    },
  },
});
try {
  await agent.run({ prompt: "Do something" });
} finally {
  await agent.close();
}
```
3. Never mix the two styles:
```typescript
// ❌ Wrong — llm is a LangChain instance but mcpServers is set (TypeScript type error: mcpServers?: never)
const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),
  mcpServers: { /* ... */ },           // TypeScript error: mcpServers is not allowed with explicit llm
});

// ❌ Wrong — passing both client AND mcpServers is ambiguous (TypeScript type error)
const agent2 = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),
  client: new MCPClient({ mcpServers: {} }),
  mcpServers: { /* ... */ },
});
```

**Prevention:** Pick one style and use it consistently. Use Style A (explicit `MCPClient`) when you need to manage server sessions manually (e.g., call `client.closeAllSessions()`) or share one `MCPClient` across multiple agents. Use Style B (simplified `"provider/model"` string) for single-agent setups where the agent owns its own client.

---

### Error: Invalid mcpServers configuration format

**When:** The `mcpServers` object has incorrect structure — missing `command`, wrong field names, or nesting issues.

**Cause:** The `mcpServers` config follows the MCP standard server configuration format. Deviations from this format (e.g., using `cmd` instead of `command`, or forgetting to wrap `args` in an array) cause startup failures.

**Fix:**
1. Follow the exact structure for stdio-based servers (simplified mode with `"provider/model"` string):
```typescript
import { MCPAgent } from "mcp-use";

const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  mcpServers: {
    // Key = server name (arbitrary)
    myServer: {
      command: "node",                    // required: executable
      args: ["path/to/server.js"],        // required: array of string args
      env: {                              // optional: environment variables
        API_KEY: "secret",
        NODE_ENV: "production",
      },
    },
  },
});
```
2. For remote servers, declare both the URL and the `transport` explicitly. mcp-use defaults to Streamable HTTP (`transport: "http"`) — pass `transport: "sse"` only when targeting a legacy SSE server:
```typescript
// Modern Streamable HTTP server (recommended for new code)
const httpAgent = new MCPAgent({
  llm: "openai/gpt-4o",
  mcpServers: {
    modernServer: {
      url: "https://mcp.example.com/mcp",
      transport: "http",                  // default — this is the current MCP standard
      headers: { Authorization: `Bearer ${process.env.MCP_TOKEN}` },
    },
  },
});

// Legacy SSE server (older reference servers)
const sseAgent = new MCPAgent({
  llm: "openai/gpt-4o",
  mcpServers: {
    legacyServer: {
      url: "http://localhost:3001/sse",
      transport: "sse",                   // required — without this, mcp-use tries Streamable HTTP
    },
  },
});
```
3. Common mistakes:
```typescript
// ❌ args must be an array, not a string
{ command: "node", args: "server.js" }

// ❌ command is required, not cmd
{ cmd: "node", args: ["server.js"] }

// ❌ env values must be strings
{ command: "node", args: ["server.js"], env: { PORT: 3000 } }
// ✅ Convert numbers to strings
{ command: "node", args: ["server.js"], env: { PORT: "3000" } }
```

**Prevention:** Define a TypeScript type or interface for your server configs and validate them at startup. Use the config structure from the MCP specification as your reference.

---

### Error: "Environment variable 'DATABASE_URL' is undefined"

**When:** Your MCP server expects environment variables that are not set in the `env` field of the server config or in the host process environment.

**Cause:** Environment variables passed via `env` in `mcpServers` replace (not merge with) the host environment. If you set `env` with only one variable, the server process loses access to all other environment variables including `PATH`.

**Fix:**
1. Spread the host environment and add your custom variables:
```typescript
import { MCPAgent } from "mcp-use";

const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  mcpServers: {
    database: {
      command: "node",
      args: ["db-server.js"],
      env: {
        ...process.env,              // inherit all host env vars
        DATABASE_URL: "postgresql://localhost:5432/mydb",
        REDIS_URL: "redis://localhost:6379",
      } as Record<string, string>,
    },
  },
});
```
2. Alternatively, set the variables on the host process before creating the agent:
```bash
export DATABASE_URL="postgresql://localhost:5432/mydb"
```
3. Use `dotenv` to load from a `.env` file:
```typescript
import "dotenv/config";
import { MCPAgent } from "mcp-use";
// DATABASE_URL is now available in process.env
```

**Prevention:** Document all required environment variables in your MCP server's README. Use a startup validation function that checks for required variables and logs clear messages when they are missing.

---

## Import Errors

---

### Error: "Cannot find module 'mcp-use'"

**When:** You try to import `mcp-use` but it is not installed in your project's `node_modules`.

**Cause:** The package has not been installed, is installed in a different workspace (monorepo), or was removed during a `node_modules` cleanup.

**Fix:**
1. Install the package:
```bash
npm install mcp-use
```
2. Verify the installation:
```bash
node -e "require('mcp-use'); console.log('OK')"
```
3. If using TypeScript, ensure your `tsconfig.json` has the correct module resolution:
```json
{
  "compilerOptions": {
    "module": "ESNext",
    "moduleResolution": "bundler",
    "esModuleInterop": true
  }
}
```
4. If in a monorepo, install in the correct workspace:
```bash
npm install mcp-use --workspace=packages/my-agent
```

**Prevention:** Pin the version in `package.json` and commit the lockfile. Run `npm ci` in CI/CD to ensure reproducible installs.

---

### Error: "Named export 'MCPAgent' not found — using wrong import path"

**When:** You import from a subpath or incorrect module name instead of the main `mcp-use` entry point.

**Cause:** Using incorrect import paths like `mcp-use/agent`, `mcp-use/dist/agent`, or confusing `mcp-use` with `@modelcontextprotocol/sdk`.

**Fix:**
1. Always import from the main `mcp-use` entry point:
```typescript
// ✅ Correct — all exports from main entry
import { MCPAgent, MCPClient } from "mcp-use";
```
2. Common wrong imports:
```typescript
// ❌ Wrong — no subpath exports
import { MCPAgent } from "mcp-use/agent";

// ❌ Wrong — this is a different package entirely
import { MCPAgent } from "@modelcontextprotocol/sdk";

// ❌ Wrong — internal dist path
import { MCPAgent } from "mcp-use/dist/index.js";
```
3. If you need types, they are also exported from the main entry:
```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import type { MCPAgentOptions } from "mcp-use";
```

**Prevention:** Use your IDE's auto-import feature — it will suggest the correct path. Add an ESLint `no-restricted-imports` rule to block incorrect paths:
```json
{
  "rules": {
    "no-restricted-imports": ["error", {
      "patterns": ["mcp-use/*", "@modelcontextprotocol/sdk"]
    }]
  }
}
```

---

## Callback and Event Errors

---

### Error: "Cannot read properties of undefined (reading 'callbacks')"

**When:** You pass malformed `callbacks` configuration to the agent constructor or try to access callback data in an event handler that does not exist for the current event type.

**Cause:** The `callbacks` option expects LangChain-compatible callback handlers. Passing a plain object or incorrect structure causes runtime errors when the agent tries to invoke callback methods.

**Fix:**
1. Use the correct callback handler structure. The `callbacks` option is typed as `BaseCallbackHandler[]` — `BaseCallbackHandler` is an **abstract class** (not an interface), so subclass it instead of passing a plain object literal (which fails under `strict: true` with `Property 'name' is missing`):
```typescript
import { MCPAgent } from "mcp-use";
import { BaseCallbackHandler } from "@langchain/core/callbacks/base";

class AgentCallbacks extends BaseCallbackHandler {
  name = "agent-callbacks";

  async handleLLMStart(_llm: unknown, prompts: string[]) {
    console.log("LLM started with", prompts.length, "prompts");
  }
  async handleLLMEnd(_output: unknown) {
    console.log("LLM finished");
  }
  async handleToolStart(tool: { name: string }, _input: string) {
    console.log("Tool called:", tool.name);
  }
  async handleToolEnd(output: string) {
    console.log("Tool result:", output.substring(0, 100));
  }
}

const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  mcpServers: { /* ... */ },
  callbacks: [new AgentCallbacks()],
});
```
2. Each callback method is optional — only override the ones you need.
3. If you want a plain-object form for minimal boilerplate, cast it explicitly. Note that handlers without a `name` get grouped as `unknown_handler` in observability platforms like Langfuse:
```typescript
import type { BaseCallbackHandler } from "@langchain/core/callbacks/base";

callbacks: [
  {
    handleLLMStart: async (_llm, prompts: string[]) => {
      console.log("LLM started with", prompts.length, "prompts");
    },
  } as unknown as BaseCallbackHandler,
],
```

**Prevention:** Subclass `BaseCallbackHandler` and set a `name` property — this satisfies strict TypeScript and gives observability tools a clear handler identity.

---

### Error: Unhandled promise rejection in callback handler

**When:** A callback handler throws an error (e.g., a logging service is down) and the rejection is not caught, causing a Node.js `UnhandledPromiseRejection` warning or crash.

**Cause:** Callback handlers run asynchronously during agent execution. If they throw, the error may not be caught by the agent's own try/catch, resulting in unhandled rejections.

**Fix:**
1. Wrap callback handlers in try/catch:
```typescript
const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  mcpServers: { /* ... */ },
  callbacks: [
    {
      handleToolEnd: async (output: string) => {
        try {
          await externalLogger.log("tool_result", output);
        } catch (err) {
          console.error("Callback error (non-fatal):", err);
        }
      },
    },
  ],
});
```
2. Add a global unhandled rejection handler as a safety net:
```typescript
process.on("unhandledRejection", (reason) => {
  console.error("Unhandled rejection:", reason);
});
```

**Prevention:** Treat callback handlers as untrusted code — always wrap them in try/catch. Never let a non-critical callback crash the agent.

---

## Process and Cleanup Errors

---

### Error: Orphaned MCP server processes after agent crash

**When:** Your Node.js process crashes or exits without calling `agent.close()`. The MCP server child processes (spawned via `child_process.spawn`) continue running in the background, consuming resources.

**Cause:** Child processes spawned by `MCPClient` are not automatically killed when the parent Node.js process exits unless cleanup handlers are registered.

**Fix:**
1. Register process exit handlers:
```typescript
import { MCPAgent } from "mcp-use";

const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  mcpServers: {
    myServer: { command: "node", args: ["server.js"] },
  },
});

async function shutdown() {
  console.log("Shutting down agent...");
  await agent.close();
  process.exit(0);
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
process.on("uncaughtException", async (err) => {
  console.error("Uncaught exception:", err);
  await agent.close().catch(() => {});
  process.exit(1);
});
```
2. Find and kill orphaned processes manually:
```bash
# Find orphaned MCP server processes
ps aux | grep "mcp-server"

# Kill by PID
kill <PID>
```

**Prevention:** Always register SIGINT/SIGTERM handlers that call `agent.close()`. Use process managers like `pm2` that handle child process cleanup automatically.

---

### Error: "ENOENT: no such file or directory" for server working directory

**When:** The MCP server expects to run from a specific working directory (e.g., to find config files) but is spawned from the wrong directory.

**Cause:** `child_process.spawn` inherits the parent process's working directory by default. If your agent runs from a different directory than the server expects, file lookups fail.

**Fix:**
1. Set the working directory via `cwd` in the server environment if supported, or use absolute paths in the server's `args`:
```typescript
import { MCPAgent } from "mcp-use";
import path from "path";

const serverDir = path.resolve(__dirname, "../mcp-servers/my-server");

const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  mcpServers: {
    myServer: {
      command: "node",
      args: [path.join(serverDir, "index.js")],
      env: {
        ...process.env,
        SERVER_ROOT: serverDir,
      } as Record<string, string>,
    },
  },
});
```
2. Use absolute paths for all file arguments:
```typescript
mcpServers: {
  filesystem: {
    command: "npx",
    args: ["-y", "@modelcontextprotocol/server-filesystem", path.resolve("/data")],
  },
}
```

**Prevention:** Always use `path.resolve()` or absolute paths in MCP server configurations. Never rely on relative paths that depend on the agent's current working directory.

---

## Debugging

---

### Complete debugging checklist

When an `MCPAgent` is not behaving as expected, work through this checklist systematically before filing a bug report.

**Step 1: Enable verbose mode**

Verbose mode logs every LLM call, tool invocation, and server interaction:

```typescript
import { MCPAgent } from "mcp-use";

// Simplified mode — use "provider/model" string
const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  verbose: true,
  mcpServers: {
    myServer: { command: "node", args: ["server.js"] },
  },
});
```

**Step 2: Enable debug-level logging**

For even more detail, enable the mcp-use logger's debug mode. `setDebug` accepts either a boolean or a numeric level (`0` silent, `1` info, `2` debug):

```typescript
import { MCPAgent, Logger } from "mcp-use";

// Quick: turn on debug logs (equivalent to Logger.setDebug(2))
Logger.setDebug(true);

// Or use the richer API for finer control:
//   level:  "silent" | "error" | "warn" | "info" | "http" | "verbose" | "debug" | "silly"
//   format: "minimal" | "detailed" | "emoji"
Logger.configure({ level: "debug", format: "minimal" });

// To silence in production:
// Logger.configure({ level: "warn" });

const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  mcpServers: { /* ... */ },
});
```

Use `Logger.configure({ format: "minimal" })` in CI environments — emoji-formatted logs can break some log aggregators.

**Step 3: Inspect the tool discovery**

Check which tools the agent discovered from the MCP servers:

```typescript
const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  verbose: true,
  mcpServers: { /* ... */ },
});

await agent.initialize();
// Verbose output will log all discovered tools with their schemas
```

**Step 4: Test the MCP server independently**

Run the MCP server outside of the agent to confirm it works:

```bash
# Start the server manually
node server.js

# In another terminal, send a JSON-RPC request
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | node server.js
```

**Step 5: Check the LLM is responding correctly**

Test the LLM in isolation without MCP tools:

```typescript
import { MCPAgent } from "mcp-use";

const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  mcpServers: {},  // no servers — pure LLM test
});

const result = await agent.run({ prompt: "Say hello" });
console.log(result);
await agent.close();
```

**Step 6: Reduce maxSteps for faster iteration**

When debugging, use a low `maxSteps` so runs complete quickly:

```typescript
const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  maxSteps: 3,
  verbose: true,
  mcpServers: { /* ... */ },
});
```

**Step 7: Use prettyStreamEvents for visual debugging**

The `prettyStreamEvents` method formats and displays all events in a human-readable way. It returns an `AsyncGenerator<void, string, void>` — you must iterate it with `for await`. Writing `await agent.prettyStreamEvents(...)` silently does nothing because awaiting an async-generator expression returns the generator object without running its body:

```typescript
// ✅ Correct — iterate the async generator
for await (const _ of agent.prettyStreamEvents({ prompt: "List files in /tmp" })) {
  // prettyStreamEvents yields void; pretty-printed output goes to stdout as a side effect
}
```

**Step 8: Check Node.js version and dependencies**

Ensure you are running a supported Node.js version and all dependencies are up to date. `mcp-use@1.25.0` declares `"engines": { "node": "^20.19.0 || >=22.12.0" }` — Node 18.x and 21.x are NOT supported, and Node 20.x must be at least `20.19.0`:

```bash
node --version          # mcp-use@1.25.0 requires ^20.19.0 || >=22.12.0
npm list mcp-use        # Check installed version
npm outdated mcp-use    # Check for updates
```

A more precise check:
```bash
node -e "const [maj, min] = process.versions.node.split('.').map(Number); console.log((maj === 20 && min >= 19) || maj >= 22 ? 'OK: ' + process.versions.node : 'UPGRADE REQUIRED: ' + process.versions.node);"
```

If you see unexpected errors, confirm the engine constraint with `cat node_modules/mcp-use/package.json | grep -A1 engines`.

**Step 9: Verify network connectivity**

If the LLM API calls are failing, verify network access:

```bash
# Test OpenAI API
curl -s https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY" | head -c 200

# Test Anthropic API
curl -s https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" | head -c 200
```

**Step 10: File a bug report with diagnostics**

If nothing above resolves the issue, file a bug report with:

1. Node.js version (`node --version`)
2. `mcp-use` version (`npm list mcp-use`)
3. LLM provider and model name
4. Full verbose output
5. MCP server configuration (redact secrets)
6. Minimal reproduction script

---

## Quick Reference — Error → Fix Table

| Error Message | Category | Quick Fix |
|---|---|---|
| API key not found | LLM Connection | Set env var or pass `apiKey` on LangChain constructor |
| Package not installed | LLM Connection | `npm install @langchain/openai` (or other provider) |
| Wrong type passed to `llm` | LLM Connection | Use `"provider/model"` string (simplified) or `new ChatOpenAI(...)` + `client` (explicit) |
| Unsupported LLM provider | LLM Connection | Install matching `@langchain/<provider>` package |
| Rate limit exceeded (429) | LLM Connection | Add retry with backoff, reduce `maxSteps` |
| Request timeout | LLM Connection | Increase timeout in LLM config |
| Tool execution failed | Tool Call | Enable verbose, check server logs |
| Tool not found | Tool Call | Check tool names, use `disallowedTools` |
| Tool call timeout | Tool Call | Set server-side timeouts |
| Failed to parse tool result | Tool Call | Fix server stdout (use stderr for logs) |
| Max steps exceeded | Lifecycle | Increase `maxSteps`, improve system prompt |
| Agent not initialized | Lifecycle | Call `initialize()` or use `autoInitialize` |
| Agent already closed | Lifecycle | Create new agent instance |
| Memory overflow | Lifecycle | `clearConversationHistory()` between runs |
| Structured output validation | Schema | Add `.describe()` to all Zod fields |
| Schema too complex | Schema | Flatten schema, use better model |
| Missing .describe() | Schema | Add `.describe()` with examples |
| Stream iteration error | Streaming | Wrap in try/catch/finally |
| Stream cleanup failure | Streaming | Always use `finally { agent.close() }` |
| Stream timeout | Streaming | Check provider streaming support |
| Server spawn failure | Server | Install command, use absolute paths |
| Server connection timeout | Server | Pre-install packages, optimize startup |
| Server crash | Server | Add error handlers, use verbose mode |
| Mixing client styles | Configuration | Use Style A (`client`) OR Style B (`mcpServers`), never both |
| Invalid mcpServers config | Configuration | Follow exact structure (command + args array) |
| Missing env vars | Configuration | Spread `process.env` in server `env` |
| Cannot find module | Import | `npm install mcp-use` |
| Wrong import path | Import | Import from `"mcp-use"` only |
| Callback error | Callback | Use correct handler structure |
| Unhandled rejection | Callback | Wrap handlers in try/catch |
| Orphaned processes | Process | Register SIGINT/SIGTERM handlers |
| ENOENT working directory | Process | Use `path.resolve()` for all paths |