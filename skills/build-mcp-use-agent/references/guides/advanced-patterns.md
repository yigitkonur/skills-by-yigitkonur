# Advanced Patterns

## Code execution mode

Agents can execute MCP tools through generated code instead of direct tool calls, enabling more efficient context usage:

```typescript
import { MCPAgent, PROMPTS } from "mcp-use";
import { MCPClient } from "mcp-use";

const client = new MCPClient(config, { codeMode: true });

const agent = new MCPAgent({
  llm,
  client,
  systemPrompt: PROMPTS.CODE_MODE,
  maxSteps: 50,
});

for await (const _ of agent.prettyStreamEvents("Process and transform the data")) {
  // code execution with syntax-highlighted output
}
await agent.close();
```

## Remote agent execution

Execute agents via the MCP Use Cloud API:

```typescript
import { RemoteAgent } from "mcp-use";

const remote = new RemoteAgent({
  agentId: "agent-abc-123",
  apiKey: process.env.MCP_USE_API_KEY,
  baseUrl: "https://cloud.mcp-use.com",
});

// Simple run
const result = await remote.run({ prompt: "Analyze data", maxSteps: 20 });

// With structured output
import { z } from "zod";
const schema = z.object({ summary: z.string(), score: z.number() });
const typed = await remote.run({ prompt: "Evaluate", schema });

// Streaming (wraps run currently)
for await (const chunk of remote.stream({ prompt: "Generate report" })) {
  console.log(chunk);
}

await remote.close();
```

## Vercel AI SDK API routes

Build streaming API endpoints:

```typescript
import { MCPAgent, MCPClient, streamEventsToAISDK, createReadableStreamFromGenerator } from "mcp-use";
import { createTextStreamResponse } from "ai";

// Next.js API route handler
export async function POST(req: Request) {
  const { prompt } = await req.json();

  const client = new MCPClient({ mcpServers: { /* ... */ } });
  const agent = new MCPAgent({ llm, client, maxSteps: 10 });

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

### With tool visibility

```typescript
import { streamEventsToAISDKWithTools } from "mcp-use";

const events = agent.streamEvents(prompt);
const enhanced = streamEventsToAISDKWithTools(events); // includes tool call markers
const readable = createReadableStreamFromGenerator(enhanced);
```

## Custom server manager factory

Provide custom management tools:

```typescript
import { ServerManager, AddMCPServerFromConfigTool } from "mcp-use";
import { LangChainAdapter } from "mcp-use/adapters";

const agent = new MCPAgent({
  llm, client,
  useServerManager: true,
  serverManagerFactory: (client) => {
    const manager = new ServerManager(client, new LangChainAdapter());
    manager.setManagementTools([
      new AddMCPServerFromConfigTool(manager),
      // add custom management tools here
    ]);
    return manager;
  },
});
```

## Additional custom tools

Register non-MCP tools alongside MCP-discovered ones:

```typescript
import { DynamicStructuredTool } from "@langchain/core/tools";
import { z } from "zod";

const customTool = new DynamicStructuredTool({
  name: "calculate",
  description: "Perform arithmetic calculations",
  schema: z.object({
    expression: z.string().describe("Math expression to evaluate"),
  }),
  func: async ({ expression }) => String(eval(expression)),
});

const agent = new MCPAgent({
  llm, client,
  additionalTools: [customTool],
});
```

## Exposing resources and prompts as tools

```typescript
const agent = new MCPAgent({
  llm, client,
  exposeResourcesAsTools: true,  // MCP resources become callable tools
  exposePromptsAsTools: true,    // MCP prompts become callable tools
});
```
