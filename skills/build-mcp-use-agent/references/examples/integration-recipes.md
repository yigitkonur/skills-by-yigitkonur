# Integration Recipes

Examples of integrating MCPAgent with external frameworks and services.

## Vercel AI SDK — Next.js API route

```typescript
import type { StreamEvent } from "@langchain/core/tracers/log_stream";
import { ChatAnthropic } from "@langchain/anthropic";
import { createTextStreamResponse } from "ai";
import { MCPAgent, MCPClient } from "mcp-use";

async function* streamEventsToAISDK(
  events: AsyncGenerator<StreamEvent, void, void>
): AsyncGenerator<string, void, void> {
  for await (const event of events) {
    if (event.event === "on_chat_model_stream" && event.data?.chunk?.text) {
      const text = event.data.chunk.text;
      if (typeof text === "string" && text.length > 0) yield text;
    }
  }
}

function createReadableStreamFromGenerator(
  gen: AsyncGenerator<string, void, void>
): ReadableStream<string> {
  return new ReadableStream({
    async start(ctrl) {
      try {
        for await (const chunk of gen) ctrl.enqueue(chunk);
        ctrl.close();
      } catch (e) { ctrl.error(e); }
    },
  });
}

export async function POST(req: Request) {
  const { prompt } = await req.json();

  const client = new MCPClient({
    mcpServers: {
      everything: { command: "npx", args: ["-y", "@modelcontextprotocol/server-everything"] },
    },
  });

  const agent = new MCPAgent({
    llm: new ChatAnthropic({ model: "claude-sonnet-4-20250514" }),
    client,
    maxSteps: 5,
  });

  try {
    const events = agent.streamEvents(prompt);
    const textStream = streamEventsToAISDK(events);
    const readable = createReadableStreamFromGenerator(textStream);
    return createTextStreamResponse({ textStream: readable });
  } finally {
    await client.closeAllSessions();
  }
}
```

## Enhanced streaming with tool visibility

```typescript
async function* streamEventsToAISDKWithTools(
  events: AsyncGenerator<StreamEvent, void, void>
): AsyncGenerator<string, void, void> {
  for await (const event of events) {
    switch (event.event) {
      case "on_chat_model_stream":
        if (event.data?.chunk?.text) {
          const text = event.data.chunk.text;
          if (typeof text === "string" && text.length > 0) yield text;
        }
        break;
      case "on_tool_start":
        yield `\n🔧 Using tool: ${event.name}\n`;
        break;
      case "on_tool_end":
        yield `\n✅ Tool completed: ${event.name}\n`;
        break;
    }
  }
}
```

## Code execution mode

```typescript
import { MCPAgent, PROMPTS, MCPClient } from "mcp-use";
import { ChatAnthropic } from "@langchain/anthropic";
import fs from "node:fs";

const tempDir = fs.mkdtempSync("mcp-code-mode-");
fs.writeFileSync(`${tempDir}/data.txt`, "Hello, world!");

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", tempDir],
    },
  },
}, { codeMode: true });

const agent = new MCPAgent({
  llm: new ChatAnthropic({ model: "claude-haiku-4-5-20251001" }),
  client,
  systemPrompt: PROMPTS.CODE_MODE,
  maxSteps: 50,
});

for await (const _ of agent.prettyStreamEvents("List and read all files")) {
  // syntax-highlighted code execution output
}

await agent.close();
fs.rmSync(tempDir, { recursive: true, force: true });
```

## Dynamic server addition

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { MCPAgent, MCPClient, ServerManager, AddMCPServerFromConfigTool } from "mcp-use";
import { LangChainAdapter } from "mcp-use/adapters";

const client = new MCPClient();
const llm = new ChatOpenAI({ model: "gpt-4o", temperature: 0 });

const serverManager = new ServerManager(client, new LangChainAdapter());
serverManager.setManagementTools([new AddMCPServerFromConfigTool(serverManager)]);

const agent = new MCPAgent({
  llm, client,
  maxSteps: 30,
  autoInitialize: true,
  useServerManager: true,
  serverManagerFactory: () => serverManager,
});

const serverConfig = JSON.stringify({
  command: "npx",
  args: ["@playwright/mcp@latest", "--headless"],
});

const result = await agent.run(`
  Add a Playwright server named 'browser' with config: ${serverConfig}
  Then navigate to https://example.com and summarize it.
`);

console.log(result);
await client.closeAllSessions();
```

## Structured output with streaming events

```typescript
import { z } from "zod";
import { ChatAnthropic } from "@langchain/anthropic";
import { MCPAgent, MCPClient } from "mcp-use";

const WeatherSchema = z.object({
  city: z.string(),
  temperature: z.number(),
  condition: z.string(),
  humidity: z.number(),
});

const client = new MCPClient({
  mcpServers: {
    playwright: { command: "npx", args: ["@playwright/mcp@latest"] },
  },
});

const agent = new MCPAgent({
  llm: new ChatAnthropic({ model: "claude-haiku-4-5" }),
  client,
  maxSteps: 50,
});

const eventStream = agent.streamEvents(
  "Get current weather in Tokyo",
  50, true, [], WeatherSchema
);

for await (const event of eventStream) {
  if (event.event === "on_structured_output") {
    const weather = WeatherSchema.parse(event.data.output);
    console.log(`${weather.city}: ${weather.temperature}°C, ${weather.condition}`);
    break;
  }
  if (event.event === "on_structured_output_progress") {
    process.stdout.write(".");
  }
}

await agent.close();
```

## Remote agent

```typescript
import { RemoteAgent } from "mcp-use";
import { z } from "zod";

const remote = new RemoteAgent({
  agentId: "my-deployed-agent",
  apiKey: process.env.MCP_USE_API_KEY,
});

// Simple query
const result = await remote.run({
  prompt: "Analyze the latest sales data",
  maxSteps: 20,
});
console.log(result);

// With structured output
const SalesSchema = z.object({
  total_revenue: z.number(),
  top_product: z.string(),
  growth_percentage: z.number(),
});

const sales = await remote.run({
  prompt: "Generate sales report",
  schema: SalesSchema,
  maxSteps: 30,
});
console.log(`Revenue: $${sales.total_revenue}, Growth: ${sales.growth_percentage}%`);

await remote.close();
```
