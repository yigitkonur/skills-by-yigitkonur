# Observability

Monitor, trace, and debug MCPAgent execution.

## Verbose logging

```typescript
const agent = new MCPAgent({
  llm, client,
  verbose: true,  // prints step-by-step execution details
});
```

Verbose mode logs:
- Step start/end timestamps
- Tool discovery and execution details
- LLM request/response payloads
- Error details with context

## Debug logging (Logger class)

```typescript
import { Logger } from "mcp-use";

Logger.setDebug(true);  // enables all debug-level log messages
```

## Langfuse integration

### Automatic setup

Set environment variables — Langfuse is auto-detected:

```bash
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."
# Optional:
export LANGFUSE_HOST="https://cloud.langfuse.com"  # or self-hosted URL
```

The agent automatically captures:
- Full execution traces (step-by-step workflow)
- LLM calls (model, prompts, completions, token counts)
- Tool executions (name, parameters, results)
- Performance metrics (per-step timings)
- Errors/exceptions with full context
- Multi-turn conversation flow

### Custom Langfuse callback

```typescript
import { CallbackHandler } from "langfuse-langchain";

const customHandler = new CallbackHandler({
  publicKey: "pk-lf-custom",
  secretKey: "sk-lf-custom",
  baseUrl: "https://custom-langfuse.com",
});

const agent = new MCPAgent({
  llm, client,
  callbacks: [customHandler],
});
```

## Metadata and tags

Attach custom metadata for trace filtering:

```typescript
agent.setMetadata({
  agent_id: "customer-support-agent-01",
  version: "v2.0.0",
  environment: "production",
  customer_id: "cust_12345",
});

agent.setTags(["customer-support", "high-priority", "beta-feature"]);

const result = await agent.run("Process customer request");
// Traces in Langfuse will include these metadata and tags
```

## Custom callback handlers

Pass any LangChain callback handler:

```typescript
import { BaseCallbackHandler } from "@langchain/core/callbacks/base";

class MyHandler extends BaseCallbackHandler {
  name = "my-handler";

  async handleToolStart(tool: any, input: string) {
    console.log(`Tool started: ${tool.name}`);
  }

  async handleToolEnd(output: string) {
    console.log(`Tool result: ${output.slice(0, 100)}`);
  }
}

const agent = new MCPAgent({
  llm, client,
  callbacks: [new MyHandler()],
});
```

## Best practices

1. **Use `verbose: true` during development** — turn off in production for cleaner logs.
2. **Set metadata per-request** — include request IDs, user IDs, environment info.
3. **Use tags for categorization** — filter traces by feature, priority, or team.
4. **Monitor token usage** — Langfuse tracks token counts automatically.
5. **Set up alerts on errors** — use Langfuse dashboards for error rate monitoring.
