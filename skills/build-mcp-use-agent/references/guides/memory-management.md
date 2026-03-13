# Memory Management

MCPAgent supports automatic conversation memory that retains context across multiple `run()` calls.

## Configuration

```typescript
// Memory enabled (default)
const agent = new MCPAgent({ llm, client, memoryEnabled: true });

// Memory disabled (stateless)
const agent = new MCPAgent({ llm, client, memoryEnabled: false });
```

## How memory works

When `memoryEnabled: true`:
- Each `run()` call appends the user prompt and agent response to an internal message history.
- The full history is sent to the LLM on subsequent calls, providing conversational context.
- System messages are preserved even after clearing history.
- History is stored per-agent instance (not shared between agents).

## Multi-turn conversation

```typescript
const agent = new MCPAgent({ llm, client, memoryEnabled: true });

await agent.run("Hello, my name is Alice");
await agent.run("What tools do you have?");
const result = await agent.run("What's my name?");
// → "Alice" (remembered from first message)
```

## Inspecting history

```typescript
const history = agent.getConversationHistory();
console.log(`Messages: ${history.length}`);

history.forEach(msg => {
  // msg.constructor.name: "HumanMessage", "AIMessage", "ToolMessage", "SystemMessage"
  console.log(`[${msg.constructor.name}] ${msg.content}`);
});
```

## Clearing history

```typescript
agent.clearConversationHistory();
// If memoryEnabled=true and a system message exists, the system message is retained.
// All user/assistant/tool messages are removed.
```

## External history injection

```typescript
import { HumanMessage, AIMessage } from "langchain";

const externalHistory = [
  new HumanMessage("Previous context message"),
  new AIMessage("Previous assistant response"),
];

const result = await agent.run({
  prompt: "Continue from where we left off",
  externalHistory,
});
```

## When to use memory

| Scenario | memoryEnabled |
|----------|---------------|
| Interactive chat | `true` |
| One-shot task | `false` |
| Multi-step workflow | `true` |
| Stateless API endpoint | `false` |
| Long-running conversation | `true` (with periodic clear) |

## Best practices

1. **Clear memory for topic switches** — `clearConversationHistory()` prevents confusion.
2. **Monitor history length** — very long histories increase token usage and latency.
3. **Use external history for resumption** — pass `externalHistory` to resume interrupted conversations.
4. **Disable for stateless APIs** — each request should be independent in API handlers.
