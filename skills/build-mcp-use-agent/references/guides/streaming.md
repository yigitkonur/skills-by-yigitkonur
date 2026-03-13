# Streaming

MCPAgent provides three streaming modes for real-time output.

## 1. Step-by-step streaming (`agent.stream`)

Yields `AgentStep` objects for each tool-call cycle:

```typescript
const stream = agent.stream("Analyze the codebase");

for await (const step of stream) {
  console.log(`Tool: ${step.action.tool}`);
  console.log(`Input: ${JSON.stringify(step.action.toolInput)}`);
  console.log(`Result: ${step.observation}`);
}
```

### Capturing the final result

```typescript
const stream = agent.stream("Search for news");
let result: string = "";

while (true) {
  const { done, value } = await stream.next();
  if (done) {
    result = value; // final result when generator completes
    break;
  }
  console.log(`Step: ${value.action.tool}`);
}

console.log(`Final: ${result}`);
```

## 2. Token-level streaming (`agent.streamEvents`)

Yields raw LangChain `StreamEvent` objects — access individual tokens:

```typescript
for await (const event of agent.streamEvents("Generate a report")) {
  switch (event.event) {
    case "on_chat_model_stream":
      const text = event.data?.chunk?.text || event.data?.chunk?.content;
      if (text) process.stdout.write(text);
      break;
    case "on_tool_start":
      console.log(`\n🔧 Tool: ${event.name}`);
      break;
    case "on_tool_end":
      console.log(`✅ Done: ${event.name}`);
      break;
    case "on_chain_start":
      if (event.name === "AgentExecutor") console.log("🏁 Started");
      break;
    case "on_chain_end":
      if (event.name === "AgentExecutor") console.log("🏁 Completed");
      break;
  }
}
```

### Key event types

| Event | When | Data |
|-------|------|------|
| `on_chat_model_stream` | LLM emits a token | `data.chunk.text` or `data.chunk.content` |
| `on_tool_start` | Tool execution begins | `name`, `data.input` |
| `on_tool_end` | Tool execution ends | `name`, `data.output` |
| `on_chain_start` | Agent executor starts | `name: "AgentExecutor"` |
| `on_chain_end` | Agent executor ends | `name: "AgentExecutor"` |
| `on_structured_output` | Structured output ready | `data.output` |
| `on_structured_output_progress` | Converting to struct | (no data) |
| `on_structured_output_error` | Conversion failed | error info |

## 3. Pretty CLI streaming (`agent.prettyStreamEvents`)

Auto-formatted with ANSI colors, syntax highlighting, and progress indicators:

```typescript
for await (const _ of agent.prettyStreamEvents({
  prompt: "List TypeScript files and count lines",
  maxSteps: 20,
})) {
  // output is formatted automatically — no manual handling needed
}
```

## Vercel AI SDK integration

Convert streamEvents to AI SDK compatible streams:

```typescript
import {
  streamEventsToAISDK,
  streamEventsToAISDKWithTools,
  createReadableStreamFromGenerator,
} from "mcp-use";
import { createTextStreamResponse } from "ai";

// In a Next.js API route:
export async function POST(req: Request) {
  const { prompt } = await req.json();
  const streamEvents = agent.streamEvents(prompt);

  // Basic — text tokens only
  const textStream = streamEventsToAISDK(streamEvents);

  // Enhanced — includes tool call notifications
  const enhancedStream = streamEventsToAISDKWithTools(streamEvents);

  const readable = createReadableStreamFromGenerator(textStream);
  return createTextStreamResponse({ textStream: readable });
}
```

## Streaming with options

All streaming methods accept the same options:

```typescript
// String prompt
agent.stream("query");
agent.streamEvents("query");

// With options
agent.stream("query", maxSteps);
agent.streamEvents("query", maxSteps, manageConnector, externalHistory, schema);

// Pretty stream takes an options object
agent.prettyStreamEvents({ prompt: "query", maxSteps: 20, schema: MySchema });
```
