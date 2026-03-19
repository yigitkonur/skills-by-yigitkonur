# Anti-Patterns

Common mistakes when building MCP agents with `mcp-use` and how to fix them. Each anti-pattern includes a ❌ BAD example showing the mistake and a ✅ GOOD example showing the correct approach.

---

## Lifecycle

### 1. Not Calling agent.close()

```typescript
// ❌ BAD — MCP connections, LLM sessions, and server processes leak silently
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

const llm = new ChatOpenAI({ model: "gpt-4o" });

const agent = new MCPAgent({
  llm,
  client,
  maxSteps: 10,
});

const result = await agent.run({ prompt: "List files in /tmp" });
console.log(result);
// agent is never closed — child processes keep running,
// connections stay open, memory is never freed
```

```typescript
// ✅ GOOD — always close the agent when done, even if run() throws
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

const llm = new ChatOpenAI({ model: "gpt-4o" });

const agent = new MCPAgent({
  llm,
  client,
  maxSteps: 10,
});

try {
  const result = await agent.run({ prompt: "List files in /tmp" });
  console.log(result);
} finally {
  await agent.close();
}
```

### 2. Not Using try/finally for Cleanup

```typescript
// ❌ BAD — if agent.run() throws, cleanup never happens
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

async function handleTask(prompt: string): Promise<string> {
  const client = new MCPClient({
    mcpServers: {
      search: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-brave-search"],
        env: { BRAVE_API_KEY: process.env.BRAVE_API_KEY! },
      },
    },
  });

  const agent = new MCPAgent({ llm: new ChatOpenAI({ model: "gpt-4o" }), client, maxSteps: 15 });

  const result = await agent.run({ prompt: prompt });
  await agent.close(); // never reached if run() throws
  return result;
}
```

```typescript
// ✅ GOOD — try/finally guarantees cleanup regardless of success or failure
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

async function handleTask(prompt: string): Promise<string> {
  const client = new MCPClient({
    mcpServers: {
      search: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-brave-search"],
        env: { BRAVE_API_KEY: process.env.BRAVE_API_KEY! },
      },
    },
  });

  const agent = new MCPAgent({ llm: new ChatOpenAI({ model: "gpt-4o" }), client, maxSteps: 15 });

  try {
    const result = await agent.run({ prompt: prompt });
    return result;
  } finally {
    await agent.close();
  }
}
```

### 3. Missing Process Signal Handlers for Graceful Shutdown

```typescript
// ❌ BAD — SIGINT/SIGTERM kills process immediately, leaving orphaned MCP servers
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/data"],
    },
  },
});

const agent = new MCPAgent({ llm: new ChatOpenAI({ model: "gpt-4o" }), client, maxSteps: 20 });

// No signal handlers — Ctrl+C leaves MCP server processes running
async function main() {
  const result = await agent.run({ prompt: "Organize files in /data by type" });
  console.log(result);
  await agent.close();
}

main();
```

```typescript
// ✅ GOOD — register signal handlers to close agent before exiting
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/data"],
    },
  },
});

const agent = new MCPAgent({ llm: new ChatOpenAI({ model: "gpt-4o" }), client, maxSteps: 20 });

let isShuttingDown = false;

async function shutdown(signal: string) {
  if (isShuttingDown) return;
  isShuttingDown = true;
  console.log(`\nReceived ${signal}, shutting down gracefully...`);
  try {
    await agent.close();
  } catch (err) {
    console.error("Error during shutdown:", err);
  }
  process.exit(0);
}

process.on("SIGINT", () => shutdown("SIGINT"));
process.on("SIGTERM", () => shutdown("SIGTERM"));

async function main() {
  try {
    const result = await agent.run({ prompt: "Organize files in /data by type" });
    console.log(result);
  } finally {
    await agent.close();
  }
}

main();
```

### 4. Creating Agent in Module Scope Instead of Per-Request

```typescript
// ❌ BAD — single agent instance shared across concurrent HTTP requests
// causes conversation history cross-contamination and race conditions
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";
import express from "express";

const client = new MCPClient({
  mcpServers: {
    database: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-postgres"],
      env: { DATABASE_URL: process.env.DATABASE_URL! },
    },
  },
});

// Module-level agent — all requests share the same conversation history
const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),
  client,
  memoryEnabled: true,
  maxSteps: 10,
});

const app = express();

app.post("/query", async (req, res) => {
  // Request A's context bleeds into Request B's conversation
  const result = await agent.run({ prompt: req.body.prompt });
  res.json({ result });
});
```

```typescript
// ✅ GOOD — create a fresh agent per request to isolate conversations
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";
import express from "express";

// Client config can be shared — it's just configuration
const serverConfig = {
  mcpServers: {
    database: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-postgres"],
      env: { DATABASE_URL: process.env.DATABASE_URL! },
    },
  },
};

const app = express();

app.post("/query", async (req, res) => {
  const client = new MCPClient(serverConfig);
  const agent = new MCPAgent({
    llm: new ChatOpenAI({ model: "gpt-4o" }),
    client,
    memoryEnabled: false,
    maxSteps: 10,
  });

  try {
    const result = await agent.run({ prompt: req.body.prompt });
    res.json({ result });
  } catch (err) {
    res.status(500).json({ error: "Agent execution failed" });
  } finally {
    await agent.close();
  }
});
```

---

## Memory

### 5. Unbounded Conversation History Growing Forever

```typescript
// ❌ BAD — memoryEnabled: true with no history management means the context
// window fills up over time, eventually causing LLM errors or truncation
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
    },
  },
});

const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),
  client,
  memoryEnabled: true,
  maxSteps: 15,
});

// Long-running loop accumulates history without bound
const tasks = [
  "Read all TypeScript files",
  "Summarize each file",
  "Find unused exports",
  "Generate a dependency graph",
  "Write documentation for public APIs",
  "Create a README",
];

for (const task of tasks) {
  const result = await agent.run({ prompt: task });
  console.log(result);
  // History keeps growing with every run — context window eventually overflows
}

await agent.close();
```

```typescript
// ✅ GOOD — clear conversation history periodically to stay within context limits
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
    },
  },
});

const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),
  client,
  memoryEnabled: true,
  maxSteps: 15,
});

const tasks = [
  "Read all TypeScript files",
  "Summarize each file",
  "Find unused exports",
  "Generate a dependency graph",
  "Write documentation for public APIs",
  "Create a README",
];

const MAX_TASKS_BEFORE_CLEAR = 3;

for (let i = 0; i < tasks.length; i++) {
  if (i > 0 && i % MAX_TASKS_BEFORE_CLEAR === 0) {
    agent.clearConversationHistory();
    console.log("Cleared conversation history to free context window");
  }
  const result = await agent.run({ prompt: tasks[i] });
  console.log(result);
}

await agent.close();
```

### 6. Not Clearing History Between Unrelated Tasks

```typescript
// ❌ BAD — context from a security audit leaks into an unrelated code generation task,
// confusing the LLM and producing worse results
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/project"],
    },
  },
});

const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),
  client,
  memoryEnabled: true,
  maxSteps: 20,
});

// Task 1: Security audit
await agent.run({ prompt: "Audit all files for hardcoded secrets and SQL injection risks" });

// Task 2: Completely unrelated — but the LLM still sees the security audit context
// which biases its code generation toward security concerns instead of features
await agent.run({ prompt: "Generate a REST API for a blog with CRUD endpoints" });

await agent.close();
```

```typescript
// ✅ GOOD — clear history between unrelated tasks so the LLM starts fresh
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/project"],
    },
  },
});

const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),
  client,
  memoryEnabled: true,
  maxSteps: 20,
});

// Task 1: Security audit
await agent.run({ prompt: "Audit all files for hardcoded secrets and SQL injection risks" });

// Clear before switching to an unrelated task
agent.clearConversationHistory();

// Task 2: Now runs with a clean context — no security audit bias
await agent.run({ prompt: "Generate a REST API for a blog with CRUD endpoints" });

await agent.close();
```

### 7. Using memoryEnabled: true in Stateless API Handlers

```typescript
// ❌ BAD — memory is pointless in a per-request agent that gets destroyed after one call,
// and it adds overhead to track conversation state that's immediately discarded
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

export async function handler(req: Request): Promise<Response> {
  const client = new MCPClient({
    mcpServers: {
      search: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-brave-search"],
        env: { BRAVE_API_KEY: process.env.BRAVE_API_KEY! },
      },
    },
  });

  const agent = new MCPAgent({
    llm: new ChatOpenAI({ model: "gpt-4o" }),
    client,
    memoryEnabled: true, // wasteful — this agent handles exactly one request
    maxSteps: 10,
  });

  try {
    const body = await req.json();
    const result = await agent.run({ prompt: body.prompt });
    return new Response(JSON.stringify({ result }), { status: 200 });
  } finally {
    await agent.close();
  }
}
```

```typescript
// ✅ GOOD — disable memory for single-use request handlers
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

export async function handler(req: Request): Promise<Response> {
  const client = new MCPClient({
    mcpServers: {
      search: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-brave-search"],
        env: { BRAVE_API_KEY: process.env.BRAVE_API_KEY! },
      },
    },
  });

  const agent = new MCPAgent({
    llm: new ChatOpenAI({ model: "gpt-4o" }),
    client,
    memoryEnabled: false, // correct — no memory needed for single-shot requests
    maxSteps: 10,
  });

  try {
    const body = await req.json();
    const result = await agent.run({ prompt: body.prompt });
    return new Response(JSON.stringify({ result }), { status: 200 });
  } finally {
    await agent.close();
  }
}
```

---

## Configuration

### 8. Hardcoding API Keys in Source Code

```typescript
// ❌ BAD — API keys committed to source control are a security breach waiting to happen
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({
  mcpServers: {
    search: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-brave-search"],
      env: {
        BRAVE_API_KEY: "BSAk9x3qR7mN2vL8pT1wY5",  // hardcoded secret!
      },
    },
  },
});

const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),
  client,
  maxSteps: 10,
});

try {
  const result = await agent.run({ prompt: "Search for TypeScript best practices" });
  console.log(result);
} finally {
  await agent.close();
}
```

```typescript
// ✅ GOOD — read secrets from environment variables at runtime
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const braveApiKey = process.env.BRAVE_API_KEY;
if (!braveApiKey) {
  throw new Error("BRAVE_API_KEY environment variable is required");
}

const client = new MCPClient({
  mcpServers: {
    search: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-brave-search"],
      env: {
        BRAVE_API_KEY: braveApiKey,
      },
    },
  },
});

const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),
  client,
  maxSteps: 10,
});

try {
  const result = await agent.run({ prompt: "Search for TypeScript best practices" });
  console.log(result);
} finally {
  await agent.close();
}
```

### 9. Not Validating Environment Variables at Startup

```typescript
// ❌ BAD — missing env vars cause cryptic errors deep inside agent execution
// instead of failing fast with a clear message
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({
  mcpServers: {
    github: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-github"],
      env: {
        GITHUB_TOKEN: process.env.GITHUB_TOKEN!, // undefined → runtime crash
      },
    },
  },
});

// Agent starts, connects to server, server crashes because GITHUB_TOKEN is undefined
const agent = new MCPAgent({ llm: new ChatOpenAI({ model: "gpt-4o" }), client, maxSteps: 10 });
const result = await agent.run({ prompt: "List my repositories" });
```

```typescript
// ✅ GOOD — validate all required env vars before creating any agents
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

// Fails immediately at startup with a clear error message
const githubToken = requireEnv("GITHUB_TOKEN");
const openaiKey = requireEnv("OPENAI_API_KEY");

const client = new MCPClient({
  mcpServers: {
    github: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-github"],
      env: { GITHUB_TOKEN: githubToken },
    },
  },
});

const agent = new MCPAgent({ llm: new ChatOpenAI({ model: "gpt-4o" }), client, maxSteps: 10 });

try {
  const result = await agent.run({ prompt: "List my repositories" });
  console.log(result);
} finally {
  await agent.close();
}
```

### 10. Using Default maxSteps for Complex Multi-Tool Tasks

```typescript
// ❌ BAD — default maxSteps (5) is too few for tasks that require
// multiple tool calls, causing the agent to stop mid-task
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/project"],
    },
  },
});

const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),
  client,
  // maxSteps defaults to 5 — not enough for: read files + analyze + write output
});

try {
  // This task needs ~10-15 steps: list dirs, read files, analyze, write report
  const result = await agent.run(
    "Read all TypeScript files in src/, analyze their complexity, and write a report to /project/report.md"
  );
  console.log(result); // Incomplete — agent ran out of steps
} finally {
  await agent.close();
}
```

```typescript
// ✅ GOOD — set maxSteps appropriately for the task complexity
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/project"],
    },
  },
});

const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),
  client,
  maxSteps: 25, // generous budget for multi-step tasks
});

try {
  const result = await agent.run(
    "Read all TypeScript files in src/, analyze their complexity, and write a report to /project/report.md"
  );
  console.log(result);
} finally {
  await agent.close();
}
```

### 11. Mixing Simplified and Explicit Mode Options

`MCPAgent` supports two distinct construction modes. Mixing them causes TypeScript type errors or runtime failures:

- **Explicit mode**: `llm` is a LangChain model instance + `client` is a pre-built `MCPClient`. The `mcpServers` key must **not** be provided.
- **Simplified mode**: `llm` is a `"provider/model"` string + `mcpServers` is provided inline. The `client` key must **not** be provided.

```typescript
// ❌ BAD — mixing explicit mode (LangChain llm instance) with simplified mode
// (mcpServers inline) is a TypeScript type violation (mcpServers: never in ExplicitModeOptions)
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/data"],
    },
  },
});

const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),  // explicit mode: LangChain instance
  client,                                      // explicit mode: pre-built client
  mcpServers: {                                // ❌ type error: not allowed with explicit mode
    search: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-brave-search"],
    },
  },
  maxSteps: 10,
});
```

```typescript
// ✅ GOOD — explicit mode: LangChain llm instance + MCPClient, no mcpServers on agent
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/data"],
    },
    search: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-brave-search"],
    },
  },
});

const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),
  client,
  maxSteps: 10,
});

try {
  const result = await agent.run("Search the web and save results to /data/results.md");
  console.log(result);
} finally {
  await agent.close();
}
```

```typescript
// ✅ GOOD — simplified mode: llm as "provider/model" string + mcpServers inline, no client
import { MCPAgent } from "mcp-use";

const agent = new MCPAgent({
  llm: "openai/gpt-4o",           // simplified mode: string provider/model
  mcpServers: {                    // simplified mode: inline server config
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/data"],
    },
    search: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-brave-search"],
    },
  },
  maxSteps: 10,
});

try {
  const result = await agent.run("Search the web and save results to /data/results.md");
  console.log(result);
} finally {
  await agent.close();
}
```

---

## Streaming

### 12. Not Handling Errors in Stream Iteration

```typescript
// ❌ BAD — if the stream throws mid-iteration, the error is unhandled
// and the agent is never cleaned up
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

const agent = new MCPAgent({ llm: new ChatOpenAI({ model: "gpt-4o" }), client, maxSteps: 10 });

// No error handling — a network hiccup or rate limit crashes the process
for await (const event of agent.streamEvents({ prompt: "List all files in /tmp" })) {
  console.log(event);
}
```

```typescript
// ✅ GOOD — wrap stream iteration in try/catch/finally
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

const agent = new MCPAgent({ llm: new ChatOpenAI({ model: "gpt-4o" }), client, maxSteps: 10 });

try {
  for await (const event of agent.streamEvents({ prompt: "List all files in /tmp" })) {
    console.log(event);
  }
} catch (err) {
  console.error("Stream error:", err);
} finally {
  await agent.close();
}
```

### 13. Using run() When Streaming Would Be Better for UX

```typescript
// ❌ BAD — run() blocks until the entire response is complete,
// leaving the user staring at a blank screen for 30+ seconds
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({
  mcpServers: {
    search: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-brave-search"],
      env: { BRAVE_API_KEY: process.env.BRAVE_API_KEY! },
    },
  },
});

const agent = new MCPAgent({ llm: new ChatOpenAI({ model: "gpt-4o" }), client, maxSteps: 15 });

try {
  // User sees nothing until the entire multi-step task finishes
  const result = await agent.run({
    prompt: "Research the latest news about AI regulation and write a summary",
  });
  console.log(result);
} finally {
  await agent.close();
}
```

```typescript
// ✅ GOOD — use streaming to show progress as the agent works
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({
  mcpServers: {
    search: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-brave-search"],
      env: { BRAVE_API_KEY: process.env.BRAVE_API_KEY! },
    },
  },
});

const agent = new MCPAgent({ llm: new ChatOpenAI({ model: "gpt-4o" }), client, maxSteps: 15 });

try {
  // User sees tokens as they arrive — much better UX for long tasks
  for await (const event of agent.streamEvents({
    prompt: "Research the latest news about AI regulation and write a summary",
  })) {
    if (event.event === "on_chat_model_stream") {
      // content is the primary field; text is used by older LangChain versions
      const token = event.data?.chunk?.content ?? event.data?.chunk?.text;
      if (token) process.stdout.write(token);
    }
  }
  console.log(); // newline after streaming
} catch (err) {
  console.error("Stream error:", err);
} finally {
  await agent.close();
}
```

### 14. Not Cleaning Up After Stream Errors

```typescript
// ❌ BAD — partial stream failure leaves the agent in an inconsistent state
// with open connections and potentially half-written files
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/output"],
    },
  },
});

const agent = new MCPAgent({ llm: new ChatOpenAI({ model: "gpt-4o" }), client, maxSteps: 20 });

async function streamTask(prompt: string): Promise<void> {
  for await (const event of agent.streamEvents({ prompt })) {
    // content is the primary field; text is used by older LangChain versions
    const token = event.data?.chunk?.content ?? event.data?.chunk?.text;
    if (token) {
      process.stdout.write(token);
    }
  }
  // If the stream errors, this function throws but agent is never closed,
  // and caller has no way to know which tools were partially executed
}

// If this throws, the agent and server processes leak
await streamTask("Write a report to /output/report.md");
```

```typescript
// ✅ GOOD — catch stream errors, clean up, and give caller a clear result
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/output"],
    },
  },
});

const agent = new MCPAgent({ llm: new ChatOpenAI({ model: "gpt-4o" }), client, maxSteps: 20 });

async function streamTask(prompt: string): Promise<{ ok: boolean; error?: string }> {
  try {
    for await (const event of agent.streamEvents({ prompt })) {
      // content is the primary field; text is used by older LangChain versions
      const token = event.data?.chunk?.content ?? event.data?.chunk?.text;
      if (token) {
        process.stdout.write(token);
      }
    }
    return { ok: true };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    console.error(`\nStream failed: ${message}`);
    return { ok: false, error: message };
  }
}

try {
  const result = await streamTask("Write a report to /output/report.md");
  if (!result.ok) {
    console.error("Task failed:", result.error);
  }
} finally {
  await agent.close();
}
```

---

## LLM

### 15. Hardcoding Model Names Instead of Using Environment Variables

```typescript
// ❌ BAD — changing the model requires a code change and redeployment
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/data"],
    },
  },
});

// Hardcoded — switching to a different model requires editing source code
const llm = new ChatOpenAI({ model: "gpt-4o" });

const agent = new MCPAgent({ llm, client, maxSteps: 10 });

try {
  const result = await agent.run({ prompt: "Summarize the files in /data" });
  console.log(result);
} finally {
  await agent.close();
}
```

```typescript
// ✅ GOOD — read model name from env var with a sensible default
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";
import { ChatAnthropic } from "@langchain/anthropic";

const model = process.env.LLM_MODEL ?? "gpt-4o";
const provider = process.env.LLM_PROVIDER ?? "openai";

// Instantiate the correct LangChain class based on the provider env var
function createLLM() {
  if (provider === "anthropic") {
    return new ChatAnthropic({ model });
  }
  return new ChatOpenAI({ model });
}

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/data"],
    },
  },
});

const agent = new MCPAgent({ llm: createLLM(), client, maxSteps: 10 });

try {
  const result = await agent.run({ prompt: "Summarize the files in /data" });
  console.log(result);
} finally {
  await agent.close();
}
```

### 16. Not Installing Required LLM Provider Packages

```typescript
// ❌ BAD — importing a LangChain provider package that is not installed
// causes a "Cannot find module" error at runtime
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatAnthropic } from "@langchain/anthropic"; // crashes if not installed

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
    },
  },
});

const agent = new MCPAgent({
  llm: new ChatAnthropic({ model: "claude-3-5-sonnet-20241022" }),
  client,
  maxSteps: 10,
});

const result = await agent.run({ prompt: "List files" });
// Error: Cannot find module '@langchain/anthropic'
```

```typescript
// ✅ GOOD — install the provider package first, then import and use it
// npm install @langchain/anthropic
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatAnthropic } from "@langchain/anthropic";

// Required LangChain provider packages:
//   OpenAI (GPT-4o, o3, etc.)    → npm install @langchain/openai
//   Anthropic (Claude)            → npm install @langchain/anthropic
//   Google Gemini                 → npm install @langchain/google-genai
//   Groq                          → npm install @langchain/groq
//   AWS Bedrock                   → npm install @langchain/aws

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
    },
  },
});

const agent = new MCPAgent({
  llm: new ChatAnthropic({ model: "claude-3-5-sonnet-20241022" }),
  client,
  maxSteps: 10,
});

try {
  const result = await agent.run({ prompt: "List files" });
  console.log(result);
} finally {
  await agent.close();
}
```

### 17. Mixing Simplified and Explicit Mode — TypeScript Type Violation

`MCPAgent` accepts two **mutually exclusive** construction modes defined by a TypeScript discriminated union. Mixing fields from both modes is a compile-time type error.

- **Simplified mode**: `llm` is a `"provider/model"` string (e.g., `"openai/gpt-4o"`) + `mcpServers` inline. The agent creates and owns its `MCPClient` internally. `client` must not be set.
- **Explicit mode**: `llm` is a LangChain `BaseChatModel` instance + `client: MCPClient`. The caller creates and manages the `MCPClient`. `mcpServers` must not be set directly on the agent.

```typescript
// ❌ BAD — TypeScript type error: mixing a LangChain instance with inline mcpServers
// ExplicitModeOptions has mcpServers?: never — this is a compile-time error
import { MCPAgent } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const bad = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),  // LangChain instance → triggers ExplicitModeOptions
  mcpServers: {                              // mcpServers?: never in ExplicitModeOptions → TYPE ERROR
    filesystem: { command: "npx", args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"] },
  },
});

// ❌ BAD — also wrong: bare model name without provider prefix is not valid for simplified mode
const bad2 = new MCPAgent({
  llm: "gpt-4o" as any,    // must be "provider/model" format — "gpt-4o" alone is invalid
  mcpServers: { /* ... */ },
});
```

```typescript
// ✅ GOOD — simplified mode: llm as "provider/model" string + inline mcpServers
import { MCPAgent } from "mcp-use";

const agentSimplified = new MCPAgent({
  llm: "openai/gpt-4o",      // simplified mode: "provider/model" string
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
    },
  },
  maxSteps: 10,
});

// Other valid simplified mode strings:
// llm: "anthropic/claude-3-5-sonnet-20241022"
// llm: "groq/llama-3.1-70b-versatile"
// llm: "google/gemini-pro"

try {
  const result = await agentSimplified.run({ prompt: "List files" });
  console.log(result);
} finally {
  await agentSimplified.close();
}
```

```typescript
// ✅ GOOD — explicit mode: LangChain instance + separate MCPClient
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

const agentExplicit = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),  // explicit mode: LangChain instance
  client,                                     // explicit mode: separate MCPClient
  maxSteps: 10,
});

try {
  const result = await agentExplicit.run({ prompt: "List files" });
  console.log(result);
} finally {
  await agentExplicit.close();
  await client.closeAllSessions();
}
```

---

## Tool Access

### 18. Not Restricting Dangerous Tools in Production

```typescript
// ❌ BAD — giving the agent unrestricted access to all tools including
// destructive ones like file deletion and shell execution
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/"],
    },
    shell: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-shell"],
    },
  },
});

// Agent has access to EVERY tool — including rm, shell exec, etc.
const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),
  client,
  maxSteps: 20,
});

try {
  // A prompt injection or hallucination could cause:
  //   rm -rf /, DROP TABLE, or arbitrary shell commands
  const result = await agent.run({ prompt: userProvidedPrompt });
  console.log(result);
} finally {
  await agent.close();
}
```

```typescript
// ✅ GOOD — use disallowedTools to block dangerous operations
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
    },
  },
});

const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),
  client,
  maxSteps: 20,
  disallowedTools: [
    "delete_file",
    "move_file",
    "write_file",       // read-only access only
    "execute_command",
    "run_shell",
  ],
});

try {
  const result = await agent.run({ prompt: userProvidedPrompt });
  console.log(result);
} finally {
  await agent.close();
}
```

### 19. Giving Agent Access to All Servers When Only Some Are Needed

```typescript
// ❌ BAD — connecting to 5 MCP servers when the task only needs one
// wastes resources, increases attack surface, and confuses the LLM
// with too many tool options
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/data"],
    },
    github: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-github"],
      env: { GITHUB_TOKEN: process.env.GITHUB_TOKEN! },
    },
    postgres: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-postgres"],
      env: { DATABASE_URL: process.env.DATABASE_URL! },
    },
    search: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-brave-search"],
      env: { BRAVE_API_KEY: process.env.BRAVE_API_KEY! },
    },
    slack: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-slack"],
      env: { SLACK_TOKEN: process.env.SLACK_TOKEN! },
    },
  },
});

const agent = new MCPAgent({ llm: new ChatOpenAI({ model: "gpt-4o" }), client, maxSteps: 10 });

try {
  // This task only needs filesystem — but agent sees 50+ tools from 5 servers
  const result = await agent.run({ prompt: "Count the number of JSON files in /data" });
  console.log(result);
} finally {
  await agent.close();
}
```

```typescript
// ✅ GOOD — only connect the servers the task actually needs
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/data"],
    },
  },
});

const agent = new MCPAgent({ llm: new ChatOpenAI({ model: "gpt-4o" }), client, maxSteps: 10 });

try {
  // Agent only sees filesystem tools — faster, cheaper, more accurate
  const result = await agent.run({ prompt: "Count the number of JSON files in /data" });
  console.log(result);
} finally {
  await agent.close();
}
```

---

## Observability

### 20. No Logging or Tracing in Production

```typescript
// ❌ BAD — no way to debug failures, track costs, or understand agent behavior
// in production; when something goes wrong, you have zero visibility
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/data"],
    },
  },
});

const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),
  client,
  maxSteps: 15,
  // No verbose flag, no callbacks, no metadata — flying blind
});

try {
  const result = await agent.run({ prompt: "Process all CSV files in /data" });
  console.log(result);
} catch (err) {
  // "Something went wrong" — but what? Which step? Which tool call?
  console.error("Failed:", err);
} finally {
  await agent.close();
}
```

```typescript
// ✅ GOOD — enable verbose mode and use callbacks for production observability
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/data"],
    },
  },
});

const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),
  client,
  maxSteps: 15,
  verbose: true, // logs each step, tool call, and LLM interaction
  callbacks: [
    {
      handleLLMStart: async (_llm: any, prompts: string[]) => {
        console.log(`[LLM] Starting with ${prompts.length} prompt(s)`);
      },
      handleToolStart: async (tool: any, input: string) => {
        console.log(`[Tool] ${tool.name} called with: ${input.slice(0, 100)}`);
      },
      handleLLMError: async (err: Error) => {
        console.error(`[LLM Error] ${err.message}`);
      },
      handleToolError: async (err: Error) => {
        console.error(`[Tool Error] ${err.message}`);
      },
    },
  ],
});

try {
  const result = await agent.run({ prompt: "Process all CSV files in /data" });
  console.log(result);
} catch (err) {
  console.error("Failed:", err);
} finally {
  await agent.close();
}
```

### 21. Not Setting Metadata and Tags for Trace Filtering

```typescript
// ❌ BAD — without metadata or tags, you cannot filter or search traces
// in your observability platform; all agent runs look identical
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({
  mcpServers: {
    search: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-brave-search"],
      env: { BRAVE_API_KEY: process.env.BRAVE_API_KEY! },
    },
  },
});

const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),
  client,
  maxSteps: 10,
});

// No metadata or tags — impossible to correlate traces with users or features
try {
  const result = await agent.run({ prompt: "Search for MCP protocol documentation" });
  console.log(result);
} finally {
  await agent.close();
}
```

```typescript
// ✅ GOOD — set metadata and tags so traces can be filtered and analyzed
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({
  mcpServers: {
    search: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-brave-search"],
      env: { BRAVE_API_KEY: process.env.BRAVE_API_KEY! },
    },
  },
});

const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),
  client,
  maxSteps: 10,
});

// Tag and annotate every run for downstream filtering
agent.setMetadata({
  userId: "user-abc-123",
  feature: "documentation-search",
  environment: process.env.NODE_ENV ?? "development",
  requestId: crypto.randomUUID(),
});

agent.setTags(["search", "docs", "production"]);

try {
  const result = await agent.run({ prompt: "Search for MCP protocol documentation" });
  console.log(result);
} finally {
  await agent.close();
}
```

---

## Bonus: Compound Anti-Patterns

### 22. God Agent — One Agent Doing Everything

```typescript
// ❌ BAD — a single agent connected to every server with an enormous prompt
// that tries to do everything in one run; slow, expensive, and unreliable
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/project"],
    },
    github: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-github"],
      env: { GITHUB_TOKEN: process.env.GITHUB_TOKEN! },
    },
    postgres: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-postgres"],
      env: { DATABASE_URL: process.env.DATABASE_URL! },
    },
  },
});

const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),
  client,
  maxSteps: 50,
});

try {
  const result = await agent.run({ prompt: `
    1. Read all source files in /project/src
    2. Find any files referencing deprecated APIs
    3. Query the database for migration status
    4. Create a GitHub issue for each deprecated usage
    5. Write a migration plan to /project/MIGRATION.md
    6. Update all deprecated references in the source code
  ` });
  console.log(result);
} finally {
  await agent.close();
}
```

```typescript
// ✅ GOOD — decompose into focused agents, each with minimal server access
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

async function analyzeDeprecations(): Promise<string[]> {
  const client = new MCPClient({
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", "/project"],
      },
    },
  });
  const agent = new MCPAgent({ llm: new ChatOpenAI({ model: "gpt-4o" }), client, maxSteps: 15 });
  try {
    const result = await agent.run({
      prompt: "Read all TypeScript files in /project/src and list any deprecated API usages. Return as JSON array of file paths.",
    });
    return JSON.parse(result);
  } finally {
    await agent.close();
  }
}

async function createIssues(files: string[]): Promise<void> {
  const client = new MCPClient({
    mcpServers: {
      github: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-github"],
        env: { GITHUB_TOKEN: process.env.GITHUB_TOKEN! },
      },
    },
  });
  const agent = new MCPAgent({ llm: new ChatOpenAI({ model: "gpt-4o" }), client, maxSteps: 20 });
  try {
    await agent.run({ prompt: `Create a GitHub issue for each of these files with deprecated API usage: ${JSON.stringify(files)}` });
  } finally {
    await agent.close();
  }
}

// Orchestrate focused agents sequentially
const deprecatedFiles = await analyzeDeprecations();
if (deprecatedFiles.length > 0) {
  await createIssues(deprecatedFiles);
}
```

### 23. Fire-and-Forget Agent Without Awaiting Results

```typescript
// ❌ BAD — not awaiting the agent's run() means errors are silently swallowed
// and the process might exit before the agent finishes
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/logs"],
    },
  },
});

const agent = new MCPAgent({ llm: new ChatOpenAI({ model: "gpt-4o" }), client, maxSteps: 10 });

// Fire and forget — no await, no error handling, no cleanup
agent.run({ prompt: "Archive old log files in /logs" });

console.log("Done!"); // Lies — the agent hasn't finished yet
// Process exits, agent is killed mid-task, files may be half-written
```

```typescript
// ✅ GOOD — always await agent operations and handle the result
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/logs"],
    },
  },
});

const agent = new MCPAgent({ llm: new ChatOpenAI({ model: "gpt-4o" }), client, maxSteps: 10 });

try {
  const result = await agent.run({ prompt: "Archive old log files in /logs" });
  console.log("Agent completed:", result);
} catch (err) {
  console.error("Agent failed:", err);
  process.exitCode = 1;
} finally {
  await agent.close();
  console.log("Cleanup complete");
}
```
