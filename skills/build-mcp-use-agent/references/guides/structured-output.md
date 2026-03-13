# Structured Output

Get typed, validated responses from MCPAgent using Zod schemas.

## Basic usage

```typescript
import { z } from "zod";

const schema = z.object({
  summary: z.string().describe("Brief summary"),
  confidence: z.number().min(0).max(1).describe("Confidence score"),
  tags: z.array(z.string()).describe("Relevant tags"),
});

const result = await agent.run({
  prompt: "Analyze this codebase",
  schema,
});

// result is fully typed: { summary: string; confidence: number; tags: string[] }
console.log(result.summary);
console.log(result.confidence);
```

## How it works

1. The agent runs tool calls as normal until it reaches a "finish" point.
2. The LLM's final response is validated against your Zod schema.
3. If validation fails, the agent automatically retries formatting up to **3 times**.
4. On success, the typed result is returned.
5. On final failure, a `ValidationError` is thrown.

## Complex schema example

```typescript
const RepoInfoSchema = z.object({
  name: z.string().describe("Repository name"),
  description: z.string().describe("Repository description"),
  stars: z.number().describe("GitHub stars count"),
  contributors: z.number().describe("Number of contributors"),
  language: z.string().describe("Primary language"),
  license: z.string().nullable().describe("License type"),
  created_at: z.string().describe("Creation date"),
  last_updated: z.string().describe("Last update date"),
});

type RepoInfo = z.infer<typeof RepoInfoSchema>;

const info: RepoInfo = await agent.run({
  prompt: "Research the mcp-use repository on GitHub",
  schema: RepoInfoSchema,
});
```

## Streaming with structured output

Use `streamEvents()` to monitor structured output conversion:

```typescript
const eventStream = agent.streamEvents(
  "Get weather data",
  50,           // maxSteps
  true,         // manageConnector
  [],           // externalHistory
  WeatherSchema // outputSchema
);

for await (const event of eventStream) {
  if (event.event === "on_structured_output") {
    const weather = WeatherSchema.parse(event.data.output);
    console.log(`Temperature: ${weather.temperature}`);
    break;
  }
  if (event.event === "on_structured_output_progress") {
    console.log("Converting to structured format...");
  }
  if (event.event === "on_structured_output_error") {
    console.error("Failed to convert");
  }
}
```

### Structured output events

| Event | Description |
|-------|-------------|
| `on_structured_output_progress` | Emitted ~every 2s during conversion |
| `on_structured_output` | Conversion succeeded — `event.data.output` has the result |
| `on_structured_output_error` | All retry attempts failed |

## Best practices

1. **Use `.describe()` on every field** — helps the LLM understand what data to provide.
2. **Use `z.nullable()` for optional data** — the LLM may not find all information.
3. **Keep schemas focused** — avoid overly complex nested schemas.
4. **Set higher `maxSteps`** — structured output may need extra steps to gather all required data.
5. **Handle validation errors** — wrap in try/catch for graceful degradation.
