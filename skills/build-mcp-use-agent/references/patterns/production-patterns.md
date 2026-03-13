# Production Patterns

## Always clean up resources

```typescript
// Pattern 1: try/finally
const agent = new MCPAgent({ llm, client, maxSteps: 30 });
try {
  const result = await agent.run("Do something");
} finally {
  await agent.close(); // always runs
}

// Pattern 2: With MCPClient cleanup
try {
  const result = await agent.run("Do something");
} finally {
  await client.closeAllSessions();
}
```

## Error handling

```typescript
try {
  const result = await agent.run({ prompt: "Complex task", maxSteps: 50 });
  return result;
} catch (error) {
  if (error instanceof Error) {
    if (error.message.includes("max steps")) {
      // Agent hit step limit — try with more steps or simplify prompt
      console.error("Task too complex, increase maxSteps");
    } else if (error.message.includes("API key")) {
      // Missing or invalid API key
      console.error("Check your API key configuration");
    } else if (error.message.includes("MODULE_NOT_FOUND")) {
      // Missing provider package
      console.error("Install the required LLM provider package");
    }
  }
  throw error;
} finally {
  await agent.close();
}
```

## Graceful shutdown

```typescript
import { MCPAgent, MCPClient } from "mcp-use";

let agent: MCPAgent | null = null;
let client: MCPClient | null = null;

async function init() {
  client = new MCPClient({ mcpServers: { /* ... */ } });
  agent = new MCPAgent({ llm, client, maxSteps: 30 });
}

async function shutdown() {
  if (agent) await agent.close();
  if (client) await client.closeAllSessions();
  process.exit(0);
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
```

## Retry with fallback providers

```typescript
const providers = [
  "openai/gpt-4o",
  "anthropic/claude-3-5-sonnet-20241022",
  "groq/llama-3.1-70b-versatile",
];

async function runWithFallback(prompt: string) {
  for (const provider of providers) {
    const agent = new MCPAgent({
      llm: provider,
      mcpServers: { /* ... */ },
      maxSteps: 20,
    });

    try {
      return await agent.run(prompt);
    } catch (error) {
      console.warn(`${provider} failed, trying next...`);
    } finally {
      await agent.close();
    }
  }
  throw new Error("All providers failed");
}
```

## Stateless API handler

```typescript
export async function handleRequest(prompt: string): Promise<string> {
  const agent = new MCPAgent({
    llm: "openai/gpt-4o",
    mcpServers: { /* ... */ },
    maxSteps: 15,
    memoryEnabled: false,  // stateless for API
  });

  try {
    return await agent.run(prompt);
  } finally {
    await agent.close();
  }
}
```

## Timeout handling

```typescript
async function runWithTimeout(prompt: string, timeoutMs: number) {
  const agent = new MCPAgent({ llm, client, maxSteps: 20 });

  try {
    const result = await Promise.race([
      agent.run(prompt),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error("Agent timeout")), timeoutMs)
      ),
    ]);
    return result;
  } finally {
    await agent.close();
  }
}

// 30-second timeout
const result = await runWithTimeout("Analyze data", 30_000);
```

## Monitoring best practices

1. **Set metadata per-request** — include unique request IDs
2. **Log maxSteps vs actual steps** — detect over-provisioned limits
3. **Track token usage** — monitor costs per query
4. **Alert on repeated tool failures** — indicates misconfiguration
5. **Monitor agent close() timing** — slow cleanup suggests connection issues
