# Observability

Monitor and debug your agents in production.

Observability gives you visibility into your agent's behavior in production, enabling debugging, performance optimization, and understanding of how your agents use tools and interact with LLMs.

---

## What gets traced

When observability is enabled, mcp-use automatically captures:

- **Full execution traces**: Complete agent workflow from start to finish
- **LLM calls**: Model usage, prompts, completions, and token counts
- **Tool execution**: Which tools were called, with what parameters, and their results
- **Performance metrics**: Execution times for each step
- **Errors and exceptions**: Full context when things go wrong
- **Conversation flow**: Multi-turn conversation tracking

---

## Langfuse integration

[Langfuse](https://langfuse.com) is an open-source LLM observability platform.

### Set environment variables

```bash
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."

# Optional: specify a custom Langfuse host. mcp-use reads LANGFUSE_HOST first
# and falls back to LANGFUSE_BASEURL (the standard Langfuse SDK env var name)
# if LANGFUSE_HOST is unset. Set whichever your existing config uses.
export LANGFUSE_HOST="https://your-langfuse.com"
# export LANGFUSE_BASEURL="https://your-langfuse.com"   # accepted as fallback

# Set to "false" to disable Langfuse even when env vars are present
export MCP_USE_LANGFUSE="false"
```

### Start using

Langfuse automatically initializes when mcp-use is imported and the environment variables are present. No additional code is required for basic tracing.

```typescript
// Langfuse automatically initializes when mcp-use is imported
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";
import { config } from "dotenv";

config(); // Load Langfuse environment variables

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/files"],
    },
  },
});

const llm = new ChatOpenAI({ model: "gpt-4" });
const agent = new MCPAgent({
  llm,
  client,
  maxSteps: 30,
});

// All agent runs are automatically traced
const result = await agent.run({ prompt: "Analyze the sales data" });
```

---

## Advanced configuration

### Custom metadata and tags

Add custom metadata and tags to traces for better organization and filtering.

#### setMetadata

```typescript
import { MCPAgent, MCPClient } from "mcp-use";

const agent = new MCPAgent({
  llm,
  client,
  maxSteps: 30,
});

// Set metadata that will be attached to all traces
agent.setMetadata({
  agent_id: "customer-support-agent-01",
  version: "v2.0.0",
  environment: "production",
  customer_id: "cust_12345",
});
```

#### setTags

```typescript
// Set tags for filtering and grouping
agent.setTags(["customer-support", "high-priority", "beta-feature"]);
```

#### Run with metadata and tags

```typescript
// Run your agent - metadata and tags are automatically included
const result = await agent.run({ prompt: "Process customer request" });
```

---

### Custom callbacks

Provide custom Langfuse callback handlers or other LangChain callbacks.

```typescript
import { CallbackHandler } from "langfuse-langchain";
import { MCPAgent } from "mcp-use";

// Create a custom Langfuse handler
const customHandler = new CallbackHandler({
  publicKey: "pk-lf-custom",
  secretKey: "sk-lf-custom",
  baseUrl: "https://custom-langfuse.com",
});

const agent = new MCPAgent({
  llm,
  client,
  callbacks: [customHandler], // Use custom callbacks instead of auto-detected ones
});
```

---

### Low-level event streaming

For custom observability pipelines without a third-party platform, `streamEvents` exposes raw LangChain events including model output chunks. Hook into this stream to build custom logging or monitoring.

```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const agent = new MCPAgent({ llm, client, maxSteps: 30 });

// streamEvents accepts a plain string or options object { prompt, maxSteps?, schema?, signal? }
for await (const event of agent.streamEvents("Generate content")) {
  if (event.event === "on_chat_model_stream") {
    // chunk.text for Anthropic; chunk.content for OpenAI — always check both
    const text = event.data?.chunk?.text || event.data?.chunk?.content;
    if (text) process.stdout.write(text);
  }
}
```

### Debug logging

Enable debug logging from the `Logger` class to see internal agent activity:

```typescript
import { Logger } from "mcp-use";

// true / 2 → "debug" level; 1 → "info" level; false → "info" (default)
Logger.setDebug(true);
```

---

## Key imports

```typescript
import { MCPAgent, MCPClient, Logger } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";
import { CallbackHandler } from "langfuse-langchain";
import { config } from "dotenv";
```

---

## MCPAgent observability options

| Option | Type | Purpose |
|---|---|---|
| `callbacks` | `BaseCallbackHandler[]` | Custom callbacks for tracing/logging (e.g. Langfuse `CallbackHandler`) |
| `maxSteps` | `number` | Cap tool calls per run |
| `observe` | `boolean` | Enable/disable automatic observability (default: `true`) |
| `verbose` | `boolean` | Enable verbose logging (default: `false`) |

---

## MCPAgent observability methods

| Method | Signature | Purpose |
|---|---|---|
| `setMetadata` | `(metadata: Record<string, any>) => void` | Merge metadata into all traces (accumulates; does not replace) |
| `getMetadata` | `() => Record<string, any>` | Returns a copy of the current metadata |
| `setTags` | `(tags: string[]) => void` | Add tags for filtering and grouping (deduplicates automatically) |
| `getTags` | `() => string[]` | Returns a copy of the current tags array |
| `flush` | `() => Promise<void>` | Flush pending observability traces — important in serverless environments |
| `streamEvents` | `(prompt: string \| RunOptions) => AsyncGenerator<StreamEvent, void, void>` | Low-level event stream for custom observability pipelines; emits raw LangChain events (e.g. `on_chat_model_stream`) |
