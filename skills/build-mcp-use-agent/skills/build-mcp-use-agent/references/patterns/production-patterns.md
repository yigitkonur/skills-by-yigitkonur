# Production Patterns for mcp-use Agents

Battle-tested patterns for running MCPAgent in production environments. Every example uses the `mcp-use` library directly and is designed to be copy-paste runnable.

---

## 1. Graceful Shutdown

When your agent runs as a long-lived process (CLI tool, server, daemon), you must handle OS signals to avoid orphaned MCP server processes, leaked connections, and corrupted state.

---

```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

async function main() {
  const client = new MCPClient({
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
      },
    },
  });

  const agent = new MCPAgent({
    llm: new ChatOpenAI({ model: "gpt-4o" }),
    client,
    maxSteps: 25,
    autoInitialize: true, // fail fast before the long-lived process starts serving work
  });

  // Track shutdown state to prevent double-cleanup
  let isShuttingDown = false;

  async function gracefulShutdown(signal: string) {
    if (isShuttingDown) return;
    isShuttingDown = true;

    console.log(`\n[${signal}] Shutting down gracefully...`);

    try {
      // Close agent first — this stops any in-flight LLM calls
      await agent.close();
      console.log("Agent closed.");

      // Then close all MCP server sessions
      await client.closeAllSessions();
      console.log("All MCP sessions closed.");
    } catch (err) {
      console.error("Error during shutdown:", err);
    } finally {
      process.exit(0);
    }
  }

  // Register signal handlers
  process.on("SIGINT", () => gracefulShutdown("SIGINT"));
  process.on("SIGTERM", () => gracefulShutdown("SIGTERM"));

  // Handle uncaught errors too
  process.on("uncaughtException", async (err) => {
    console.error("Uncaught exception:", err);
    await gracefulShutdown("uncaughtException");
  });

  process.on("unhandledRejection", async (reason) => {
    console.error("Unhandled rejection:", reason);
    await gracefulShutdown("unhandledRejection");
  });

  // Run agent work
  const result = await agent.run({
    prompt: "List all files in /tmp and summarize them",
  });
  console.log("Result:", result);


  // Normal exit — still clean up
  await agent.close();
  await client.closeAllSessions();
}

main().catch(console.error);
```

**Key points:**

- Always close the agent before the client — stopping in-flight LLM calls first prevents dangling tool invocations.
- The `isShuttingDown` flag prevents double-cleanup if multiple signals arrive rapidly.
- Register handlers for both `SIGINT` (Ctrl+C) and `SIGTERM` (container orchestrator stop).
- In containerized environments (Docker, K8s), `SIGTERM` is sent first with a grace period before `SIGKILL`.

---

## 2. Error Recovery with Retries

Transient failures are inevitable: LLM rate limits, network blips, MCP server restarts. Use exponential backoff with jitter to retry gracefully.

---

```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

interface RetryOptions {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
  retryableErrors: string[];
}

const DEFAULT_RETRY_OPTIONS: RetryOptions = {
  maxRetries: 3,
  baseDelayMs: 1000,
  maxDelayMs: 30000,
  retryableErrors: [
    "ECONNRESET",
    "ETIMEDOUT",
    "rate_limit",
    "429",
    "503",
    "502",
    "500",
    "overloaded",
  ],
};

function isRetryable(error: unknown, patterns: string[]): boolean {
  const message =
    error instanceof Error ? error.message : String(error);
  return patterns.some(
    (p) => message.toLowerCase().includes(p.toLowerCase())
  );
}

function calculateDelay(
  attempt: number,
  baseMs: number,
  maxMs: number
): number {
  // Exponential backoff: base * 2^attempt
  const exponential = baseMs * Math.pow(2, attempt);
  // Add jitter: ±25% randomization to avoid thundering herd
  const jitter = exponential * 0.25 * (Math.random() * 2 - 1);
  return Math.min(exponential + jitter, maxMs);
}

async function runWithRetry(
  agent: MCPAgent,
  prompt: string,
  options: Partial<RetryOptions> = {}
): Promise<string> {
  const opts = { ...DEFAULT_RETRY_OPTIONS, ...options };

  for (let attempt = 0; attempt <= opts.maxRetries; attempt++) {
    try {
      const result = await agent.run({ prompt: prompt });
      return result;
    } catch (error) {
      const isLast = attempt === opts.maxRetries;

      if (isLast || !isRetryable(error, opts.retryableErrors)) {
        throw error; // Not retryable or out of retries
      }

      const delay = calculateDelay(
        attempt,
        opts.baseDelayMs,
        opts.maxDelayMs
      );
      console.warn(
        `Attempt ${attempt + 1} failed, retrying in ${Math.round(delay)}ms:`,
        error instanceof Error ? error.message : error
      );

      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }

  throw new Error("Unreachable");
}

// Usage
async function main() {
  const client = new MCPClient({
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
      },
    },
  });

  const agent = new MCPAgent({
    llm: new ChatOpenAI({ model: "gpt-4o" }),
    client,
    maxSteps: 20,
  });

  try {
    const result = await runWithRetry(
      agent,
      "Read the config file at /tmp/config.json",
      { maxRetries: 5, baseDelayMs: 2000 }
    );
    console.log("Success:", result);
  } finally {
    await agent.close();
    await client.closeAllSessions();
  }
}

main().catch(console.error);
```

**Key points:**

- Jitter prevents multiple agents from retrying at the exact same time (thundering herd problem).
- Not all errors should be retried — auth failures, validation errors, and schema mismatches are permanent.
- For LLM rate limits (429), the backoff should be longer — set `baseDelayMs: 5000` or higher.
- If your agent uses `memoryEnabled: true`, conversation history persists across retries automatically.

---

## 3. maxSteps Tuning

The `maxSteps` parameter controls how many LLM reasoning + tool-call cycles the agent can perform. Too low and tasks fail mid-execution; too high and you waste tokens on loops.

---

```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

// default maxSteps is 5 — far too low for most tasks; always set explicitly
// simple lookup = 5-10, multi-step = 15-30, complex workflows = 30-50

// Simple: single tool call, direct answer
// Uses simplified mode (llm as string) — no MCPClient needed
const lookupAgent = new MCPAgent({
  llm: "openai/gpt-4o-mini",  // simplified mode: string format
  maxSteps: 5,
  mcpServers: {
    weather: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-weather"],
    },
  },
});

// Medium: needs to discover tools, read data, synthesize
// Uses explicit mode — MCPClient must be created separately
const analysisClient = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/data"],
    },
  },
});

const analysisAgent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),
  client: analysisClient,
  maxSteps: 20,
});

// Complex: multi-file operations, conditional logic, iteration
// Uses explicit mode with multiple servers
const workflowClient = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
    },
    github: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-github"],
      env: { GITHUB_TOKEN: process.env.GITHUB_TOKEN ?? "" },
    },
  },
});

const workflowAgent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),
  client: workflowClient,
  maxSteps: 50,
});

// Override per-run for specific tasks that need more steps
async function main() {
  try {
    // analysisAgent was created with maxSteps: 20, but this task needs more
    const result = await analysisAgent.run({
      prompt: "Read all CSV files in /data, merge them, and create a summary report",
      maxSteps: 35,
    });
    console.log(result);
  } finally {
    await lookupAgent.close();
    await analysisAgent.close();
    await analysisClient.closeAllSessions();
    await workflowAgent.close();
    await workflowClient.closeAllSessions();
  }
}

main().catch(console.error);
```

**Tuning guidelines:**

| Task Type | Steps | Examples |
|-----------|-------|---------|
| Single lookup | 3–5 | Weather check, single file read, one API call |
| Simple transform | 5–10 | Read + write one file, format conversion |
| Multi-step analysis | 10–20 | Read multiple files, cross-reference, summarize |
| Complex workflow | 20–35 | Multi-file edits, conditional branching, iteration |
| Open-ended exploration | 35–50 | Code generation, research, multi-tool orchestration |

**Signs you need to adjust:**

- Agent returns truncated results → increase `maxSteps`
- Agent loops doing the same action → decrease `maxSteps` and improve the prompt
- Costs are too high → lower `maxSteps` and break the task into smaller prompts

---

## 4. Provider Fallback Chain

If your primary LLM provider goes down, automatically fall back to an alternative. This pattern tries providers in order until one succeeds.

---

```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";
import { ChatAnthropic } from "@langchain/anthropic";
import type { BaseChatModel } from "@langchain/core/language_models/chat_models";

interface ProviderConfig {
  name: string;
  createLLM: () => BaseChatModel;
  maxSteps: number;
}

const PROVIDERS: ProviderConfig[] = [
  {
    name: "OpenAI GPT-4o",
    createLLM: () => new ChatOpenAI({ model: "gpt-4o" }),
    maxSteps: 25,
  },
  {
    name: "Anthropic Claude 3.5 Sonnet",
    createLLM: () => new ChatAnthropic({ model: "claude-3-5-sonnet-20241022" }),
    maxSteps: 25,
  },
  {
    name: "OpenAI GPT-4o-mini",
    createLLM: () => new ChatOpenAI({ model: "gpt-4o-mini" }),
    maxSteps: 30,
  },
];

const MCP_SERVERS_CONFIG = {
  mcpServers: {
    filesystem: {
      command: "npx" as const,
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/data"],
    },
  },
};

async function runWithFallback(
  prompt: string,
  providers: ProviderConfig[] = PROVIDERS
): Promise<{ result: string; provider: string }> {
  const errors: Array<{ provider: string; error: string }> = [];

  for (const provider of providers) {
    // Each attempt creates a fresh MCPClient and agent — explicit mode requires client
    const client = new MCPClient(MCP_SERVERS_CONFIG);
    const agent = new MCPAgent({
      llm: provider.createLLM(),
      client,
      maxSteps: provider.maxSteps,
    });

    try {
      console.log(`Trying provider: ${provider.name}`);
      const result = await agent.run({ prompt: prompt });
      return { result, provider: provider.name };
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      console.warn(`Provider ${provider.name} failed: ${message}`);
      errors.push({ provider: provider.name, error: message });
    } finally {
      await agent.close();
      await client.closeAllSessions();
    }
  }

  throw new Error(
    `All providers failed:\n${errors
      .map((e) => `  - ${e.provider}: ${e.error}`)
      .join("\n")}`
  );
}

// Usage
async function main() {
  const { result, provider } = await runWithFallback(
    "List the files in /data and count the total number of lines across all text files"
  );
  console.log(`Completed via ${provider}:`, result);
}

main().catch(console.error);
```

**Key points:**

- Each provider gets its own fresh `MCPAgent` instance — don't reuse agents across providers.
- Always `close()` the agent in a `finally` block, even when falling back.
- Order providers by preference: best quality first, cheapest last.
- Consider pairing with the retry pattern: retry each provider 2–3 times before falling back to the next.
- `llm` must be a LangChain model instance (e.g., `new ChatOpenAI(...)`) — pass a factory function per provider so each fallback gets a fresh instance.

---

## 5. Rate Limiting

Prevent overloading LLM APIs or MCP servers by throttling how often `agent.run()` is called. This simple token-bucket limiter works well for most use cases.

---

```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

class RateLimiter {
  private tokens: number;
  private lastRefill: number;
  private readonly maxTokens: number;
  private readonly refillRatePerSec: number;

  constructor(maxRequestsPerMinute: number) {
    this.maxTokens = maxRequestsPerMinute;
    this.tokens = maxRequestsPerMinute;
    this.refillRatePerSec = maxRequestsPerMinute / 60;
    this.lastRefill = Date.now();
  }

  private refill(): void {
    const now = Date.now();
    const elapsed = (now - this.lastRefill) / 1000;
    this.tokens = Math.min(
      this.maxTokens,
      this.tokens + elapsed * this.refillRatePerSec
    );
    this.lastRefill = now;
  }

  async acquire(): Promise<void> {
    this.refill();

    if (this.tokens >= 1) {
      this.tokens -= 1;
      return;
    }

    // Wait until a token is available
    const waitMs = ((1 - this.tokens) / this.refillRatePerSec) * 1000;
    console.log(`Rate limited — waiting ${Math.round(waitMs)}ms`);
    await new Promise((resolve) => setTimeout(resolve, waitMs));
    this.refill();
    this.tokens -= 1;
  }
}

// Wrap agent.run with rate limiting
async function rateLimitedRun(
  agent: MCPAgent,
  limiter: RateLimiter,
  prompt: string
): Promise<string> {
  await limiter.acquire();
  return agent.run({ prompt: prompt });
}

// Usage: process a batch of prompts with rate limiting
async function main() {
  const client = new MCPClient({
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
      },
    },
  });

  const agent = new MCPAgent({
    llm: new ChatOpenAI({ model: "gpt-4o-mini" }),
    client,
    maxSteps: 10,
  });

  // Allow 20 requests per minute
  const limiter = new RateLimiter(20);

  const prompts = [
    "Read /tmp/file1.txt",
    "Read /tmp/file2.txt",
    "Read /tmp/file3.txt",
    "Read /tmp/file4.txt",
    "Read /tmp/file5.txt",
  ];

  try {
    for (const prompt of prompts) {
      const result = await rateLimitedRun(agent, limiter, prompt);
      console.log(`Done: ${prompt.slice(0, 40)}... → ${result.slice(0, 80)}`);
    }
  } finally {
    await agent.close();
    await client.closeAllSessions();
  }
}

main().catch(console.error);
```

**Key points:**

- Token bucket is preferred over fixed-window because it handles bursts gracefully.
- Set the rate based on your LLM provider's limits (e.g., OpenAI Tier 1 = 60 RPM for GPT-4o).
- For multi-tenant systems, use one limiter per tenant or per API key.
- This pattern composes well with the retry pattern — the limiter runs before each attempt.

---

## 6. Concurrent Agent Pool

When you need to run multiple agent tasks in parallel but want to limit concurrency to avoid overwhelming resources. Uses a semaphore pattern for bounded parallelism.

---

```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

class Semaphore {
  private current = 0;
  private queue: Array<() => void> = [];

  constructor(private readonly max: number) {}

  async acquire(): Promise<void> {
    if (this.current < this.max) {
      this.current++;
      return;
    }
    return new Promise<void>((resolve) => {
      this.queue.push(() => {
        this.current++;
        resolve();
      });
    });
  }

  release(): void {
    this.current--;
    const next = this.queue.shift();
    if (next) next();
  }
}

interface TaskResult {
  prompt: string;
  result: string;
  durationMs: number;
  error?: string;
}

async function runConcurrentTasks(
  prompts: string[],
  concurrency: number = 3
): Promise<TaskResult[]> {
  const semaphore = new Semaphore(concurrency);
  const mcpServersConfig = {
    mcpServers: {
      filesystem: {
        command: "npx" as const,
        args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
      },
    },
  };

  const tasks = prompts.map(async (prompt): Promise<TaskResult> => {
    await semaphore.acquire();
    const start = Date.now();

    // Each concurrent task gets its own MCPClient and agent instance
    // Explicit mode: LangChain llm instance requires a separate MCPClient
    const client = new MCPClient(mcpServersConfig);
    const agent = new MCPAgent({
      llm: new ChatOpenAI({ model: "gpt-4o-mini" }),
      client,
      maxSteps: 10,
    });

    try {
      const result = await agent.run({ prompt: prompt });
      return {
        prompt,
        result,
        durationMs: Date.now() - start,
      };
    } catch (error) {
      return {
        prompt,
        result: "",
        durationMs: Date.now() - start,
        error: error instanceof Error ? error.message : String(error),
      };
    } finally {
      await agent.close();
      await client.closeAllSessions();
      semaphore.release();
    }
  });

  return Promise.all(tasks);
}

// Usage
async function main() {
  const prompts = [
    "Read /tmp/report-q1.txt and summarize the key metrics",
    "Read /tmp/report-q2.txt and summarize the key metrics",
    "Read /tmp/report-q3.txt and summarize the key metrics",
    "Read /tmp/report-q4.txt and summarize the key metrics",
    "Read /tmp/inventory.csv and count the total items",
    "Read /tmp/errors.log and identify the top 3 error types",
  ];

  console.log(`Running ${prompts.length} tasks with concurrency=3`);
  const results = await runConcurrentTasks(prompts, 3);

  for (const r of results) {
    if (r.error) {
      console.error(`FAILED: ${r.prompt.slice(0, 50)} — ${r.error}`);
    } else {
      console.log(`OK (${r.durationMs}ms): ${r.prompt.slice(0, 50)}`);
    }
  }

  const succeeded = results.filter((r) => !r.error).length;
  console.log(`\n${succeeded}/${results.length} tasks completed successfully`);
}

main().catch(console.error);
```

**Key points:**

- Each concurrent task **must** get its own `MCPAgent` instance — agents are not thread-safe.
- The semaphore limits how many agents run simultaneously, preventing resource exhaustion.
- Set concurrency based on: LLM API rate limits, available memory (each MCP server subprocess uses RAM), and CPU cores.
- If tasks share an MCP server config, each agent still spawns its own server process — keep concurrency reasonable (3–5 for stdio servers).
- For high-throughput workloads, consider using SSE-based MCP servers instead of stdio to share a single server process.

---

## 7. Resource Cleanup with try/finally

Comprehensive cleanup patterns that handle every resource combination — agent-only, agent + client, multi-agent, and nested scopes.

---

```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

// Pattern A: simplified mode — llm as string + mcpServers inline
// The agent internally creates and manages its own MCPClient
async function simplifiedCleanup() {
  const agent = new MCPAgent({
    llm: "openai/gpt-4o",  // simplified mode: string format
    maxSteps: 15,
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
      },
    },
  });

  try {
    const result = await agent.run({ prompt: "List files in /tmp" });
    console.log(result);
  } finally {
    // agent.close() handles its internally-managed MCPClient too
    await agent.close();
  }
}

// Pattern B: Explicit client — you manage both lifecycles
async function explicitCleanup() {
  const client = new MCPClient({
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
      },
    },
  });

  const agent = new MCPAgent({
    llm: new ChatOpenAI({ model: "gpt-4o" }),
    client,
    maxSteps: 15,
  });

  try {
    const result = await agent.run({ prompt: "List files in /tmp" });
    console.log(result);
  } finally {
    // Close agent first, then client
    await agent.close();
    await client.closeAllSessions();
  }
}

// Pattern C: Multi-agent with shared client
async function multiAgentCleanup() {
  const client = new MCPClient({
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
      },
    },
  });

  const reader = new MCPAgent({ llm: new ChatOpenAI({ model: "gpt-4o-mini" }), client, maxSteps: 10 });
  const writer = new MCPAgent({ llm: new ChatOpenAI({ model: "gpt-4o" }), client, maxSteps: 20 });

  try {
    const data = await reader.run({
      prompt: "Read the contents of /workspace/input.json",
    });
    const result = await writer.run({ prompt: `Transform this data and write it to /workspace/output.json: ${data}` });
    console.log(result);
  } finally {
    // Close all agents before the shared client
    await Promise.all([reader.close(), writer.close()]);
    await client.closeAllSessions();
  }
}

// Pattern D: createAgent helper with automatic cleanup
async function withAgent<T>(
  config: ConstructorParameters<typeof MCPAgent>[0],
  fn: (agent: MCPAgent) => Promise<T>
): Promise<T> {
  const agent = new MCPAgent(config);
  try {
    return await fn(agent);
  } finally {
    await agent.close();
  }
}

// Usage of the helper — simplified mode (llm as string) lets agent manage its own client
async function helperExample() {
  const result = await withAgent(
    {
      llm: "openai/gpt-4o",  // simplified mode: string format
      maxSteps: 10,
      mcpServers: {
        filesystem: {
          command: "npx",
          args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
        },
      },
    } as any,  // cast needed because ConstructorParameters union type inference
    async (agent) => {
      return agent.run({ prompt: "Count files in /tmp" });
    }
  );
  console.log(result);
}
```

**Key points:**

- Rule of thumb: close resources in reverse order of creation (agent before client).
- `Promise.all` for closing multiple agents is safe — `close()` calls are independent.
- The `withAgent` helper guarantees cleanup regardless of success or failure.
- Never rely on garbage collection for cleanup — MCP server subprocesses will leak.

---

## 8. Memory-Bounded Conversations

For long-running agents with `memoryEnabled: true`, conversation history grows unboundedly. Clear it periodically to avoid exceeding token limits and degrading performance.

---

```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";
import type { BaseChatModel } from "@langchain/core/language_models/chat_models";

class BoundedConversationAgent {
  private agent: MCPAgent;
  private client: MCPClient;
  private messageCount = 0;
  private readonly maxMessages: number;
  private readonly maxEstimatedTokens: number;
  private estimatedTokens = 0;

  constructor(options: {
    llm: BaseChatModel;
    mcpServers: Record<string, { command: string; args: string[]; env?: Record<string, string> }>;
    maxMessages?: number;
    maxEstimatedTokens?: number;
    maxSteps?: number;
  }) {
    this.maxMessages = options.maxMessages ?? 50;
    this.maxEstimatedTokens = options.maxEstimatedTokens ?? 100_000;

    // Explicit mode: LangChain llm instance requires a separate MCPClient
    this.client = new MCPClient({ mcpServers: options.mcpServers });
    this.agent = new MCPAgent({
      llm: options.llm,
      client: this.client,
      maxSteps: options.maxSteps ?? 20,
      memoryEnabled: true,  // default is true; explicit here for clarity
    });
  }

  private estimateTokens(text: string): number {
    // Rough estimate: 1 token ≈ 4 characters for English text
    return Math.ceil(text.length / 4);
  }

  private shouldClearMemory(): boolean {
    return (
      this.messageCount >= this.maxMessages ||
      this.estimatedTokens >= this.maxEstimatedTokens
    );
  }

  async run(prompt: string): Promise<string> {
    // Check if memory needs clearing before running
    if (this.shouldClearMemory()) {
      console.log(
        `Clearing memory (messages: ${this.messageCount}, ` +
        `est. tokens: ${this.estimatedTokens})`
      );
      this.agent.clearConversationHistory();
      this.messageCount = 0;
      this.estimatedTokens = 0;
    }

    const result = await this.agent.run({ prompt: prompt });

    // Track both the prompt and response
    this.messageCount += 2; // user message + assistant response
    this.estimatedTokens +=
      this.estimateTokens(prompt) + this.estimateTokens(result);

    return result;
  }

  async close(): Promise<void> {
    await this.agent.close();
    await this.client.closeAllSessions();
  }

  getStats(): { messageCount: number; estimatedTokens: number } {
    return {
      messageCount: this.messageCount,
      estimatedTokens: this.estimatedTokens,
    };
  }
}

// Usage: interactive chatbot with memory bounds
async function main() {
  const bot = new BoundedConversationAgent({
    llm: new ChatOpenAI({ model: "gpt-4o" }),
    maxMessages: 40,
    maxEstimatedTokens: 80_000,
    maxSteps: 15,
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", "/data"],
      },
    },
  });

  const prompts = [
    "What files are in /data?",
    "Read the first file and summarize it",
    "Now read the second file",
    "Compare the two files",
  ];

  try {
    for (const prompt of prompts) {
      const result = await bot.run(prompt);
      console.log(`Q: ${prompt}`);
      console.log(`A: ${result.slice(0, 200)}\n`);
      console.log(`Stats:`, bot.getStats());
    }
  } finally {
    await bot.close();
  }
}

main().catch(console.error);
```

**Key points:**

- `memoryEnabled` defaults to `true` — every agent retains conversation history unless you explicitly set `memoryEnabled: false`.
- Use `agent.getConversationHistory()` to inspect the current history before deciding whether to clear it.
- `clearConversationHistory()` empties the internal buffer; if a system message is present it is retained.
- The 4-chars-per-token estimate is rough but sufficient for bounds checking. For precise counting, use `tiktoken`.
- Clearing memory resets the conversation context — the agent loses all prior context. Log important state externally if needed.
- Set `maxMessages` based on your model's context window: GPT-4o supports 128K tokens, but performance degrades above ~60K.
- For multi-turn chatbots, consider keeping a sliding window of the last N messages instead of clearing everything.

---

## 9. Health Monitoring

Track agent run times, success rates, and errors to detect degradation early. This pattern provides structured logging suitable for production observability.

---

```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";
import type { BaseChatModel } from "@langchain/core/language_models/chat_models";

interface RunMetrics {
  prompt: string;
  provider: string;
  durationMs: number;
  success: boolean;
  error?: string;
  timestamp: string;
}

class MonitoredAgent {
  private agent: MCPAgent;
  private client: MCPClient;
  private metrics: RunMetrics[] = [];
  private readonly provider: string;

  constructor(options: {
    llm: BaseChatModel;
    providerName: string;
    mcpServers: Record<string, { command: string; args: string[] }>;
    maxSteps?: number;
  }) {
    this.provider = options.providerName;
    // Explicit mode: LangChain llm instance requires a separate MCPClient
    this.client = new MCPClient({ mcpServers: options.mcpServers });
    this.agent = new MCPAgent({
      llm: options.llm,
      client: this.client,
      maxSteps: options.maxSteps ?? 20,
    });
  }

  async run(prompt: string): Promise<string> {
    const start = Date.now();
    const timestamp = new Date().toISOString();

    try {
      const result = await this.agent.run({ prompt: prompt });

      this.metrics.push({
        prompt: prompt.slice(0, 100),
        provider: this.provider,
        durationMs: Date.now() - start,
        success: true,
        timestamp,
      });

      return result;
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);

      this.metrics.push({
        prompt: prompt.slice(0, 100),
        provider: this.provider,
        durationMs: Date.now() - start,
        success: false,
        error: message,
        timestamp,
      });

      throw error;
    }
  }

  getHealthReport(): {
    totalRuns: number;
    successRate: number;
    avgDurationMs: number;
    p95DurationMs: number;
    recentErrors: string[];
  } {
    if (this.metrics.length === 0) {
      return {
        totalRuns: 0,
        successRate: 1,
        avgDurationMs: 0,
        p95DurationMs: 0,
        recentErrors: [],
      };
    }

    const successes = this.metrics.filter((m) => m.success);
    const durations = this.metrics
      .map((m) => m.durationMs)
      .sort((a, b) => a - b);

    const p95Index = Math.floor(durations.length * 0.95);

    return {
      totalRuns: this.metrics.length,
      successRate: successes.length / this.metrics.length,
      avgDurationMs: Math.round(
        durations.reduce((a, b) => a + b, 0) / durations.length
      ),
      p95DurationMs: durations[p95Index] ?? durations[durations.length - 1],
      recentErrors: this.metrics
        .filter((m) => !m.success)
        .slice(-5)
        .map((m) => `${m.timestamp}: ${m.error}`),
    };
  }

  async close(): Promise<void> {
    await this.agent.close();
    await this.client.closeAllSessions();
  }
}

// Usage with periodic health checks
async function main() {
  const agent = new MonitoredAgent({
    llm: new ChatOpenAI({ model: "gpt-4o-mini" }),
    providerName: "openai/gpt-4o-mini",
    maxSteps: 10,
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
      },
    },
  });

  // Periodic health logging
  const healthInterval = setInterval(() => {
    const report = agent.getHealthReport();
    console.log("[HEALTH]", JSON.stringify(report));

    // Alert if success rate drops below 90%
    if (report.totalRuns > 5 && report.successRate < 0.9) {
      console.error("[ALERT] Success rate below 90%:", report.successRate);
    }

    // Alert if latency spikes
    if (report.p95DurationMs > 30_000) {
      console.warn("[WARN] P95 latency above 30s:", report.p95DurationMs);
    }
  }, 60_000); // Every minute

  try {
    const tasks = ["Read /tmp/a.txt", "Read /tmp/b.txt", "Read /tmp/c.txt"];

    for (const task of tasks) {
      try {
        await agent.run(task);
      } catch {
        // Error is already recorded in metrics
      }
    }

    // Final report
    console.log("Final health:", agent.getHealthReport());
  } finally {
    clearInterval(healthInterval);
    await agent.close();
  }
}

main().catch(console.error);
```

**Key points:**

- Keep metrics in memory for short-lived processes; for long-lived services, flush to a time-series database (Prometheus, Datadog).
- The P95 latency metric catches outliers that averages hide.
- Set alerting thresholds based on your SLAs — 90% success rate and 30s P95 are good starting points.
- For production, integrate with `agent.setMetadata()` and `agent.setTags()` to add run context to your observability platform.

---

## 10. Environment-Based Configuration

Load agent configuration from environment variables with validation. Fail fast on missing or invalid config rather than discovering errors mid-run.

---

```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";
import { ChatAnthropic } from "@langchain/anthropic";
import type { BaseChatModel } from "@langchain/core/language_models/chat_models";

interface AgentConfig {
  llmProvider: string;
  llmModel: string;
  maxSteps: number;
  verbose: boolean;
  memoryEnabled: boolean;
  observabilityEnabled: boolean;
  mcpFilesystemRoot: string;
  rateLimitRpm: number;
}

function loadConfig(): AgentConfig {
  const errors: string[] = [];

  function required(key: string): string {
    const value = process.env[key];
    if (!value) {
      errors.push(`Missing required env var: ${key}`);
      return "";
    }
    return value;
  }

  function optional(key: string, fallback: string): string {
    return process.env[key] ?? fallback;
  }

  function optionalInt(key: string, fallback: number): number {
    const raw = process.env[key];
    if (!raw) return fallback;
    const parsed = parseInt(raw, 10);
    if (isNaN(parsed)) {
      errors.push(`Env var ${key} must be an integer, got: ${raw}`);
      return fallback;
    }
    return parsed;
  }

  function optionalBool(key: string, fallback: boolean): boolean {
    const raw = process.env[key]?.toLowerCase();
    if (!raw) return fallback;
    if (raw === "true" || raw === "1") return true;
    if (raw === "false" || raw === "0") return false;
    errors.push(`Env var ${key} must be true/false, got: ${raw}`);
    return fallback;
  }

  const config: AgentConfig = {
    llmProvider: optional("AGENT_LLM_PROVIDER", "openai"),
    llmModel: optional("AGENT_LLM_MODEL", "gpt-4o"),
    maxSteps: optionalInt("AGENT_MAX_STEPS", 20),
    verbose: optionalBool("AGENT_VERBOSE", false),
    memoryEnabled: optionalBool("AGENT_MEMORY", true),
    observabilityEnabled: optionalBool("AGENT_OBSERVABILITY", true),
    mcpFilesystemRoot: required("AGENT_FS_ROOT"),
    rateLimitRpm: optionalInt("AGENT_RATE_LIMIT_RPM", 30),
  };

  // Validate ranges
  if (config.maxSteps < 1 || config.maxSteps > 100) {
    errors.push(`AGENT_MAX_STEPS must be 1-100, got: ${config.maxSteps}`);
  }

  if (config.rateLimitRpm < 1 || config.rateLimitRpm > 1000) {
    errors.push(`AGENT_RATE_LIMIT_RPM must be 1-1000, got: ${config.rateLimitRpm}`);
  }

  if (errors.length > 0) {
    console.error("Configuration errors:");
    errors.forEach((e) => console.error(`  ✗ ${e}`));
    process.exit(1);
  }

  return config;
}

function createLLMFromConfig(config: AgentConfig): BaseChatModel {
  if (config.llmProvider === "anthropic") {
    return new ChatAnthropic({ model: config.llmModel });
  }
  return new ChatOpenAI({ model: config.llmModel });
}

function createAgentFromConfig(config: AgentConfig): { agent: MCPAgent; client: MCPClient } {
  // Explicit mode: LangChain llm instance requires a separate MCPClient
  const client = new MCPClient({
    mcpServers: {
      filesystem: {
        command: "npx",
        args: [
          "-y",
          "@modelcontextprotocol/server-filesystem",
          config.mcpFilesystemRoot,
        ],
      },
    },
  });

  const agent = new MCPAgent({
    llm: createLLMFromConfig(config),
    client,
    maxSteps: config.maxSteps,
    verbose: config.verbose,
    memoryEnabled: config.memoryEnabled,
    observe: config.observabilityEnabled,  // explicit opt-out via AGENT_OBSERVABILITY=false
  });

  return { agent, client };
}

// Usage
async function main() {
  const config = loadConfig();
  console.log("Loaded config:", {
    llm: `${config.llmProvider}/${config.llmModel}`,
    maxSteps: config.maxSteps,
    verbose: config.verbose,
    fsRoot: config.mcpFilesystemRoot,
  });

  const { agent, client } = createAgentFromConfig(config);

  try {
    const result = await agent.run({
      prompt: "List files in the configured directory",
    });
    console.log(result);
  } finally {
    await agent.close();
    await client.closeAllSessions();
  }
}

main().catch(console.error);
```

**Environment variables reference:**

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AGENT_LLM_PROVIDER` | No | `openai` | LLM provider name |
| `AGENT_LLM_MODEL` | No | `gpt-4o` | Model identifier |
| `AGENT_MAX_STEPS` | No | `20` | Max reasoning steps |
| `AGENT_VERBOSE` | No | `false` | Enable verbose logging |
| `AGENT_MEMORY` | No | `true` | Enable conversation memory |
| `AGENT_OBSERVABILITY` | No | `true` | Auto-emit traces to Langfuse / configured platform; set `false` to opt out |
| `AGENT_FS_ROOT` | **Yes** | — | Root directory for filesystem MCP server |
| `AGENT_RATE_LIMIT_RPM` | No | `30` | Max requests per minute |

**Key points:**

- Fail fast with all errors at once — don't make the user fix one missing var, restart, discover the next.
- Use sensible defaults for everything except security-sensitive values (API keys, filesystem roots).
- Never log API keys or secrets — only log the structure of the config.
- For production, consider using `dotenv` for local development and real env vars in deployment.
- `observe` defaults to `true`, so every agent emits traces if Langfuse / OTel env vars are set. For high-throughput batch jobs or cost-sensitive deployments, pass `observe: false` explicitly to opt out — this is the only way to silence the auto-init "ObservabilityManager: Observability disabled" debug log on initialize.

---

## 11. Streaming Error Handling

When using `agent.stream()` or `agent.prettyStreamEvents()`, errors can occur mid-stream after partial results have been yielded. Handle these gracefully without losing the partial output.

---

```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

// Pattern A: Basic stream with error boundary
// Uses explicit mode: LangChain llm instance requires a separate MCPClient
async function basicStreamWithErrorHandling() {
  const client = new MCPClient({
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
      },
    },
  });

  const agent = new MCPAgent({
    llm: new ChatOpenAI({ model: "gpt-4o" }),
    client,
    maxSteps: 20,
  });

  try {
    // stream() accepts RunOptions object (preferred) or plain string (deprecated)
    const stream = agent.stream({ prompt: "Analyze all log files in /tmp" });
    let stepCount = 0;

    for await (const step of stream) {
      stepCount++;
      console.log(`Step ${stepCount}:`, JSON.stringify(step).slice(0, 200));
    }

    console.log(`Stream completed after ${stepCount} steps`);
  } catch (error) {
    // Error during streaming — some steps may have already executed
    console.error("Stream error:", error instanceof Error ? error.message : error);
    console.warn("Partial results may have been produced. Check tool side-effects.");
  } finally {
    await agent.close();
    await client.closeAllSessions();
  }
}

// Pattern B: Collect partial results during streaming
async function streamWithPartialResults() {
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
  });

  const collectedSteps: unknown[] = [];

  try {
    const stream = agent.stream({ prompt: "Read and summarize every file in /data" });

    for await (const step of stream) {
      collectedSteps.push(step);
    }

    console.log("All steps collected:", collectedSteps.length);
    return { success: true, steps: collectedSteps };
  } catch (error) {
    console.error(
      `Stream failed after ${collectedSteps.length} steps:`,
      error instanceof Error ? error.message : error
    );

    // Return partial results so caller can decide what to do
    return { success: false, steps: collectedSteps, error };
  } finally {
    await agent.close();
    await client.closeAllSessions();
  }
}

// Pattern C: prettyStreamEvents with error handling
async function streamWithStepTimeout() {
  const client = new MCPClient({
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
      },
    },
  });

  const agent = new MCPAgent({
    llm: new ChatOpenAI({ model: "gpt-4o" }),
    client,
    maxSteps: 20,
  });

  try {
    // prettyStreamEvents auto-formats output with ANSI colors
    const stream = agent.prettyStreamEvents({
      prompt: "Find all .log files in /tmp and extract error counts",
      maxSteps: 20,
    });

    for await (const event of stream) {
      // Output is already formatted — just write to stdout
      process.stdout.write(String(event));
    }
  } catch (error) {
    console.error("\nStream error:", error instanceof Error ? error.message : error);
  } finally {
    await agent.close();
    await client.closeAllSessions();
  }
}

// Run examples
async function main() {
  await basicStreamWithErrorHandling();
  await streamWithPartialResults();
  await streamWithStepTimeout();
}

main().catch(console.error);
```

**Key points:**

- Streaming errors can happen after tool calls have already executed — those side-effects (file writes, API calls) are not rolled back.
- Collect partial results during streaming so you can inspect what completed before the error.
- `prettyStreamEvents()` is best for CLI tools — it handles ANSI formatting automatically.
- `stream(prompt)` takes a plain string and returns `AgentStep` objects per tool call. Note: `step.observation` is empty when the step is yielded — tool results are tracked internally by the agent.
- `streamEvents(prompt)` takes a plain string and returns LangChain-compatible events for token-level streaming and observability.

---

## 12. Structured Output Validation

Use Zod schemas with `agent.run()` to get validated, typed output. Retry on validation failure with a more explicit prompt.

---

```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";
import { z } from "zod";

// Define your expected output schema
const FileAnalysisSchema = z.object({
  totalFiles: z.number().int().nonneg(),
  totalSizeBytes: z.number().nonneg(),
  fileTypes: z.array(
    z.object({
      extension: z.string(),
      count: z.number().int().positive(),
      totalBytes: z.number().nonneg(),
    })
  ),
  largestFile: z.object({
    name: z.string(),
    sizeBytes: z.number().nonneg(),
  }),
  summary: z.string().min(10),
});

type FileAnalysis = z.infer<typeof FileAnalysisSchema>;

async function getStructuredOutput(
  agent: MCPAgent,
  prompt: string,
  schema: z.ZodSchema,
  maxAttempts: number = 3
): Promise<z.infer<typeof schema>> {
  let lastError: Error | undefined;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      // Pass the Zod schema to agent.run for structured output
      const result = await agent.run({ prompt, schema });

      // Parse and validate the result
      const parsed = typeof result === "string" ? JSON.parse(result) : result;
      return schema.parse(parsed);
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));

      if (attempt < maxAttempts) {
        console.warn(
          `Attempt ${attempt} validation failed: ${lastError.message}. Retrying...`
        );

        // Retry with the validation error message in the prompt
        prompt = `${prompt}\n\nIMPORTANT: Your previous response failed validation with error: "${lastError.message}". Please ensure your response is valid JSON matching the required schema exactly.`;
      }
    }
  }

  throw new Error(
    `Failed to get valid structured output after ${maxAttempts} attempts: ${lastError?.message}`
  );
}

// Usage
async function main() {
  const client = new MCPClient({
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
      },
    },
  });

  const agent = new MCPAgent({
    llm: new ChatOpenAI({ model: "gpt-4o" }),
    client,
    maxSteps: 15,
  });

  try {
    const analysis = await getStructuredOutput(
      agent,
      "Analyze all files in /tmp. Return a structured analysis with: total file count, total size in bytes, breakdown by file extension (count and total bytes per type), the largest file (name and size), and a brief summary.",
      FileAnalysisSchema
    );

    console.log("Analysis result:");
    console.log(`  Total files: ${analysis.totalFiles}`);
    console.log(`  Total size: ${(analysis.totalSizeBytes / 1024).toFixed(1)} KB`);
    console.log(`  File types: ${analysis.fileTypes.length}`);
    console.log(`  Largest: ${analysis.largestFile.name}`);
    console.log(`  Summary: ${analysis.summary}`);
  } finally {
    await agent.close();
    await client.closeAllSessions();
  }
}

main().catch(console.error);
```

**Key points:**

- The `schema` parameter in `agent.run({ prompt, schema })` tells the LLM to output structured JSON.
- Always validate the result with `schema.parse()` — LLMs can still produce slightly malformed output.
- Retrying with the validation error message in the prompt helps the LLM self-correct.
- Use `.nonneg()`, `.positive()`, `.min()` etc. in your Zod schemas to catch semantic errors, not just structural ones.
- 3 attempts is usually sufficient — if it fails 3 times, the schema or prompt likely needs redesigning.

---

## 13. Timeout Handling

Prevent agent runs from hanging indefinitely by wrapping them with a timeout using `Promise.race` and `AbortController`.

---

```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

class TimeoutError extends Error {
  constructor(public readonly timeoutMs: number) {
    super(`Agent run timed out after ${timeoutMs}ms`);
    this.name = "TimeoutError";
  }
}

async function runWithTimeout(
  agent: MCPAgent,
  prompt: string,
  timeoutMs: number
): Promise<string> {
  const controller = new AbortController();
  let timer: ReturnType<typeof setTimeout> | undefined;

  const timeoutPromise = new Promise<never>((_, reject) => {
    timer = setTimeout(() => {
      controller.abort();
      reject(new TimeoutError(timeoutMs));
    }, timeoutMs);

    // Don't let the timer keep the process alive
    if (timer.unref) timer.unref();
  });

  try {
    const result = await Promise.race([
      agent.run({ prompt: prompt, signal: controller.signal }),
      timeoutPromise,
    ]);
    return result;
  } catch (error) {
    if (error instanceof TimeoutError) {
      console.warn(`Timeout: "${prompt.slice(0, 50)}..." exceeded ${timeoutMs}ms`);
      // Agent might still be running — close it to clean up
      await agent.close();
    }
    throw error;
  } finally {
    if (timer) clearTimeout(timer);
  }
}

// Tiered timeouts based on task complexity
const TIMEOUTS = {
  simple: 15_000,    // 15 seconds — single lookup
  medium: 60_000,    // 1 minute — multi-step task
  complex: 180_000,  // 3 minutes — complex workflow
  batch: 300_000,    // 5 minutes — batch processing
} as const;

// Usage: run with timeout
async function main() {
  const client = new MCPClient({
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
      },
    },
  });

  const agent = new MCPAgent({
    llm: new ChatOpenAI({ model: "gpt-4o" }),
    client,
    maxSteps: 25,
  });

  try {
    const result = await runWithTimeout(
      agent,
      "List all files in /tmp and identify the largest one",
      TIMEOUTS.medium
    );
    console.log("Result:", result);
  } catch (error) {
    if (error instanceof TimeoutError) {
      console.error(`Timed out after ${error.timeoutMs}ms`);
    } else {
      throw error;
    }
  } finally {
    await agent.close();
    await client.closeAllSessions();
  }
}

main().catch(console.error);
```

**Key points:**

- After a timeout, call `agent.close()` to stop any in-flight LLM calls and clean up MCP server processes.
- Use `timer.unref()` to prevent the timeout timer from keeping the Node.js event loop alive if the main task finishes first.
- Set timeouts based on observed P95 latencies plus a safety margin (typically 2–3x P95).
- Combine with the retry pattern: timeout → retry with a higher timeout on the second attempt.
- The `AbortController` is set up for future use when `mcp-use` adds native abort signal support.

---

## 14. Disallowed Tools

Restrict which MCP tools an agent can call based on environment, user role, or security policy. Use `disallowedTools` to block dangerous operations in production.

---

```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

// Define tool restrictions per environment
const TOOL_RESTRICTIONS: Record<string, string[]> = {
  production: [
    "write_file",
    "delete_file",
    "move_file",
    "create_directory",
    "execute_command",
    "run_script",
  ],
  staging: [
    "delete_file",
    "execute_command",
    "run_script",
  ],
  development: [],
};

function getDisallowedTools(): string[] {
  const env = process.env.NODE_ENV ?? "development";
  const tools = TOOL_RESTRICTIONS[env] ?? [];

  // Allow explicit overrides via env var
  const extraBlocked = process.env.AGENT_BLOCKED_TOOLS;
  if (extraBlocked) {
    tools.push(...extraBlocked.split(",").map((t) => t.trim()));
  }

  return [...new Set(tools)]; // Deduplicate
}

// Usage: read-only agent in production
async function main() {
  const disallowedTools = getDisallowedTools();
  console.log(`Environment: ${process.env.NODE_ENV ?? "development"}`);
  console.log(`Disallowed tools: ${disallowedTools.join(", ") || "(none)"}`);

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
    disallowedTools,
  });

  try {
    // In production, this agent can read but not write
    const result = await agent.run({
      prompt: "Analyze the data files and suggest improvements",
    });
    console.log(result);

    // Dynamically update restrictions if needed
    agent.setDisallowedTools([...disallowedTools, "list_directory"]);
    console.log("Updated disallowed:", agent.getDisallowedTools());
  } finally {
    await agent.close();
    await client.closeAllSessions();
  }
}

// Role-based restrictions for multi-tenant systems
function getDisallowedToolsForRole(role: string): string[] {
  const roleRestrictions: Record<string, string[]> = {
    viewer: [
      "write_file",
      "delete_file",
      "move_file",
      "create_directory",
      "execute_command",
    ],
    editor: [
      "delete_file",
      "execute_command",
    ],
    admin: [],
  };

  return roleRestrictions[role] ?? roleRestrictions["viewer"];
}

async function createAgentForUser(
  userId: string,
  role: string
): Promise<MCPAgent> {
  const disallowedTools = getDisallowedToolsForRole(role);

  console.log(`Creating agent for user ${userId} (role: ${role})`);
  console.log(`  Blocked tools: ${disallowedTools.join(", ") || "(none)"}`);

  // Each user gets their own MCPClient and agent with appropriate permissions
  const userClient = new MCPClient({
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", "/data"],
      },
    },
  });

  return new MCPAgent({
    llm: new ChatOpenAI({ model: "gpt-4o" }),
    client: userClient,
    maxSteps: 15,
    disallowedTools,
  });
  // Note: caller is responsible for closing the agent and its client
}

main().catch(console.error);
```

**Key points:**

- In production, always start with a restrictive set and add permissions as needed, not the other way around.
- `setDisallowedTools()` and `getDisallowedTools()` allow dynamic updates without recreating the agent.
- Tool names are MCP server-defined — check your server's tool list to know the exact names to block.
- For multi-tenant systems, combine environment-level restrictions with role-based restrictions.
- Disallowed tools are enforced at the agent level — the LLM never sees them as available options.

---

## Combining Patterns

These patterns compose naturally. Here is a production-ready agent that combines graceful shutdown, retries, rate limiting, timeouts, health monitoring, and environment config:

---

```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";
import { ChatAnthropic } from "@langchain/anthropic";

// === Config ===
interface Config {
  llmProvider: string;
  llmModel: string;
  maxSteps: number;
  timeoutMs: number;
  maxRetries: number;
  rateLimitRpm: number;
  fsRoot: string;
  disallowedTools: string[];
}

function loadConfig(): Config {
  const env = process.env.NODE_ENV ?? "development";
  return {
    llmProvider: process.env.LLM_PROVIDER ?? "openai",
    llmModel: process.env.LLM_MODEL ?? "gpt-4o",
    maxSteps: parseInt(process.env.MAX_STEPS ?? "20", 10),
    timeoutMs: parseInt(process.env.TIMEOUT_MS ?? "60000", 10),
    maxRetries: parseInt(process.env.MAX_RETRIES ?? "3", 10),
    rateLimitRpm: parseInt(process.env.RATE_LIMIT_RPM ?? "30", 10),
    fsRoot: process.env.FS_ROOT ?? "/tmp",
    disallowedTools: env === "production"
      ? ["write_file", "delete_file", "execute_command"]
      : [],
  };
}

// === Rate Limiter (from Pattern 5) ===
class RateLimiter {
  private tokens: number;
  private lastRefill: number;
  private readonly maxTokens: number;
  private readonly refillRate: number;

  constructor(rpm: number) {
    this.maxTokens = rpm;
    this.tokens = rpm;
    this.refillRate = rpm / 60;
    this.lastRefill = Date.now();
  }

  async acquire(): Promise<void> {
    const now = Date.now();
    this.tokens = Math.min(
      this.maxTokens,
      this.tokens + ((now - this.lastRefill) / 1000) * this.refillRate
    );
    this.lastRefill = now;

    if (this.tokens < 1) {
      const wait = ((1 - this.tokens) / this.refillRate) * 1000;
      await new Promise((r) => setTimeout(r, wait));
      this.tokens = 0;
    }
    this.tokens--;
  }
}

// === Main ===
async function main() {
  const config = loadConfig();
  let isShuttingDown = false;

  const llm = config.llmProvider === "anthropic"
    ? new ChatAnthropic({ model: config.llmModel })
    : new ChatOpenAI({ model: config.llmModel });

  // Explicit mode: LangChain llm instance requires a separate MCPClient
  const client = new MCPClient({
    mcpServers: {
      filesystem: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", config.fsRoot],
      },
    },
  });

  const agent = new MCPAgent({
    llm,
    client,
    maxSteps: config.maxSteps,
    disallowedTools: config.disallowedTools,
  });

  const limiter = new RateLimiter(config.rateLimitRpm);
  const metrics: Array<{ ok: boolean; ms: number }> = [];

  // Graceful shutdown (Pattern 1)
  async function shutdown(signal: string) {
    if (isShuttingDown) return;
    isShuttingDown = true;
    console.log(`\n[${signal}] Shutting down...`);
    await agent.close();
    await client.closeAllSessions();
    const successRate = metrics.length
      ? metrics.filter((m) => m.ok).length / metrics.length
      : 1;
    console.log(`Final stats: ${metrics.length} runs, ${(successRate * 100).toFixed(1)}% success`);
    process.exit(0);
  }

  process.on("SIGINT", () => shutdown("SIGINT"));
  process.on("SIGTERM", () => shutdown("SIGTERM"));

  // Run with all patterns combined
  async function safeRun(prompt: string): Promise<string> {
    for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
      await limiter.acquire();
      const start = Date.now();

      try {
        const result = await Promise.race([
          agent.run({ prompt: prompt }),
          new Promise<never>((_, reject) =>
            setTimeout(() => reject(new Error("Timeout")), config.timeoutMs)
          ),
        ]);
        metrics.push({ ok: true, ms: Date.now() - start });
        return result;
      } catch (error) {
        metrics.push({ ok: false, ms: Date.now() - start });
        if (attempt === config.maxRetries) throw error;
        const delay = 1000 * Math.pow(2, attempt);
        console.warn(`Retry ${attempt + 1} in ${delay}ms`);
        await new Promise((r) => setTimeout(r, delay));
      }
    }
    throw new Error("Unreachable");
  }

  // Process work
  try {
    const result = await safeRun("List and summarize all files in the directory");
    console.log("Result:", result);
  } finally {
    await agent.close();
    await client.closeAllSessions();
  }
}

main().catch(console.error);
```

This combined pattern gives you a resilient, observable, rate-limited agent with graceful shutdown — suitable for production deployment.
