# Structured Output

Structured output lets MCPAgent validate responses against a Zod schema, returning typed data you can trust.

---

## Why structured output

Use structured output when you need:

- Typed JSON responses in production flows
- Deterministic parsing (no regex hacks)
- Automated validation and retries
- Clear contracts between agent and your application

---

## Key imports

```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";
import { z } from "zod";
```

---

## Core API surface

### `run` options

| Option | Type | Default | Purpose |
|---|---|---|---|
| `prompt` | `string` | – | Natural‑language instruction to the agent |
| `schema` | `z.ZodSchema<T>` | `undefined` | Validates and types the final response |
| `maxSteps` | `number` | agent default | Override tool‑calling steps for this run |
| `manageConnector` | `boolean` | `undefined` | Auto-initialize/close MCP connectors for this call |
| `externalHistory` | `BaseMessage[]` | `undefined` | Per-call history override (does not mutate agent buffer) |
| `signal` | `AbortSignal` | `undefined` | Cancel the run via `AbortController` |

> **`run()` does not stream.** There is no `stream` boolean on `RunOptions` — `run()` always returns a resolved `Promise`. To stream, call `agent.stream()`, `agent.streamEvents()`, or `agent.prettyStreamEvents()` instead. They return `AsyncGenerator` objects you consume with `for await`.

### Return type

- Without `schema`: resolves to `any` (raw LLM response).
- With `schema`: resolves to `Promise<T>` where `T` is inferred from the Zod schema (`z.infer<typeof schema>`).

### Full method reference

| Method | Parameters | Returns |
|---|---|---|
| `run` | `{ prompt: string; schema?: z.ZodSchema<T>; maxSteps?: number; signal?: AbortSignal }` | `Promise<T>` (typed if `schema` provided, else `string`) |
| `stream` | `{ prompt: string; maxSteps?: number; schema?: z.ZodSchema<T>; signal?: AbortSignal }` or plain `string` | `AsyncGenerator<AgentStep, string \| T, void>` |
| `prettyStreamEvents` | `{ prompt: string; maxSteps?: number; schema?: z.ZodSchema<T> }` | `AsyncGenerator<void, string, void>` |
| `streamEvents` | `{ prompt: string; schema?: z.ZodSchema<T>; maxSteps?: number; signal?: AbortSignal }` or plain `string` | `AsyncGenerator<StreamEvent, void, void>` |
| `clearConversationHistory` | `()` | `void` |
| `close` | `()` | `Promise<void>` |

---

## Quick start

```typescript
import { z } from "zod";
import { ChatOpenAI } from "@langchain/openai";
import { MCPAgent, MCPClient } from "mcp-use";

// Define schema with .describe() annotations to guide the agent
const WeatherInfo = z.object({
  city: z.string().describe("City name"),
  temperature: z.number().describe("Temperature in Celsius"),
  condition: z.string().describe("Weather condition"),
  humidity: z.number().describe("Humidity percentage"),
});

type WeatherInfo = z.infer<typeof WeatherInfo>;

const client = new MCPClient({ mcpServers: { /* ... */ } });
const agent = new MCPAgent({ llm: new ChatOpenAI({ model: "gpt-4o" }), client });

const weather: WeatherInfo = await agent.run({
  prompt: "Get the current weather in San Francisco",
  schema: WeatherInfo,
});

console.log(`Temperature in ${weather.city}: ${weather.temperature}°C`);
console.log(`Condition: ${weather.condition}`);
console.log(`Humidity: ${weather.humidity}%`);

await client.closeAllSessions();
```

---

## How validation works

When you provide a Zod schema to the agent:

1. **Schema awareness**: When using `streamEvents()`, the agent receives schema information injected into the query before execution, so the agent understands what data structure to return. When using `run()` or `stream()`, structured output conversion happens after execution completes.
2. **Automatic validation**: The response is validated against the Zod schema at runtime.
3. **Formatting retries**: If the output does not match the schema format, the system retries up to **3 times** to reformat it correctly.
4. **Guaranteed structure**: You get data matching your schema or an error is thrown.

### Retry guidance principles

Use these in your prompt to improve success rates:

- Provide an explicit JSON shape
- Avoid ambiguous fields
- Specify required and optional fields clearly
- Include enums and value ranges

---

## Structured output patterns

### Pattern: Simple object

```typescript
const schema = z.object({
  status: z.string(),
  summary: z.string(),
});

const data = await agent.run({
  prompt: "Return status and summary",
  schema,
});
```

### Pattern: Nested object

```typescript
const schema = z.object({
  project: z.object({
    name: z.string(),
    owner: z.string(),
  }),
  risks: z.array(z.object({
    id: z.string(),
    severity: z.enum(["low", "medium", "high"]),
    description: z.string(),
  })),
});
```

### Pattern: Array of objects

```typescript
const schema = z.array(
  z.object({
    id: z.string(),
    title: z.string(),
    tags: z.array(z.string()),
  })
);
```

### Pattern: Enum fields

```typescript
const schema = z.object({
  state: z.enum(["draft", "review", "approved", "rejected"]),
  reason: z.string().optional(),
});
```

---

## Typed response handling

Use `z.infer` to type your code.

```typescript
type Decision = z.infer<typeof decisionSchema>;

const decision: Decision = await agent.run({
  prompt: "Evaluate the proposal and return the decision",
  schema: decisionSchema,
});

if (decision.state === "rejected") {
  notifyOwner(decision.reason ?? "No reason provided");
}
```

---

## Complex schema catalog

### 1) Deeply nested schema

```typescript
const schema = z.object({
  report: z.object({
    title: z.string(),
    sections: z.array(
      z.object({
        heading: z.string(),
        bullets: z.array(z.string()),
        evidence: z.object({
          source: z.string(),
          confidence: z.number().min(0).max(1),
        }),
      })
    ),
  }),
  nextSteps: z.array(z.object({
    owner: z.string(),
    task: z.string(),
    due: z.string().optional(),
  })),
});
```

### 2) Discriminated union

```typescript
const schema = z.discriminatedUnion("type", [
  z.object({ type: z.literal("bug"), severity: z.enum(["low", "high"]) }),
  z.object({ type: z.literal("feature"), effort: z.enum(["s", "m", "l"]) }),
]);
```

### 3) Tuple pattern

```typescript
const schema = z.tuple([z.string(), z.number(), z.boolean()]);
```

### 4) Optional/nullable fields

```typescript
const schema = z.object({
  owner: z.string().optional(),
  approvedBy: z.string().nullable(),
});
```

### 5) Record schema

```typescript
const schema = z.record(z.string(), z.object({
  count: z.number(),
  status: z.enum(["ok", "warn", "fail"]),
}));
```

---

## Prompt patterns for validation success

Use imperative prompts.

**Do:**

- “Return JSON matching this schema: …”
- “Only output JSON; no prose.”
- “All fields are required unless marked optional.”

**Avoid:**

- “Explain your reasoning” (adds extra text)
- “Include notes” (breaks schema)

---

## Streaming with structured output

The behavior depends on which method you use:

- **`run()` / `stream()`**: Structured output conversion happens **after** execution completes. The schema is not injected into the prompt before the run.
- **`streamEvents()`**: The query is automatically **enhanced with schema information before execution**, so the agent understands the required data structure during the run. Returns an `AsyncGenerator<StreamEvent>`; iterate with `for await` and check `event.event` to handle structured output events.

### Streaming method reference

| Method | Signature | Returns | Description |
|---|---|---|---|
| `stream` | `agent.stream(prompt: string)` or `agent.stream({ prompt, maxSteps?, schema? })` | `AsyncGenerator<AgentStep, string, void>` | Step-by-step streaming; each yielded `AgentStep` has `action.tool` and `action.toolInput`. When done, the generator return value is the final string. |
| `prettyStreamEvents` | `agent.prettyStreamEvents(prompt: string)` or `agent.prettyStreamEvents({ prompt, maxSteps?, schema? })` | `AsyncGenerator<void, string, void>` | CLI-friendly streaming with automatic syntax highlighting and formatting. Plain-string form is deprecated; prefer the options object. |
| `streamEvents` | `agent.streamEvents(prompt: string)` or `agent.streamEvents({ prompt, schema? })` | `AsyncGenerator<StreamEvent, void, void>` | Raw LangChain event stream; check `event.event` to handle structured output events |

### `streamEvents()` structured output events

When using `streamEvents()` with a schema, the generator yields standard `StreamEvent` objects. Among them, three mcp-use-specific events carry structured output state:

| Event (`event.event`) | When emitted | Relevant payload |
|---|---|---|
| `"on_structured_output_progress"` | Periodically while converting to structured format | — |
| `"on_structured_output"` | When structured output is successfully generated | `event.data.output` contains the validated object |
| `"on_structured_output_error"` | If structured output conversion fails after all retries | — |

```typescript
const schema = z.object({ plan: z.array(z.string()) });

for await (const event of agent.streamEvents({ prompt: "Draft a plan", schema })) {
  if (event.event === "on_structured_output_progress") {
    console.log("Converting output...");
  } else if (event.event === "on_structured_output") {
    const result = schema.parse(event.data.output);
    console.log("Structured result:", result);
  } else if (event.event === "on_structured_output_error") {
    console.error("Conversion failed");
  }
}
```

### Step-by-step streaming (no schema)

```typescript
for await (const step of agent.stream({ prompt: "Write a report" })) {
  console.log(`Tool: ${step.action.tool}`);
  console.log(`Input:`, step.action.input);
}
```

### Pretty streaming (CLI output)

```typescript
for await (const _ of agent.prettyStreamEvents({ prompt: "Analyze code", maxSteps: 20 })) {
  // auto-formatted, syntax-highlighted output
}
```

---

## Validation failure recovery

### Pattern: Safe retry wrapper

```typescript
async function runWithRetry<T>(prompt: string, schema: z.ZodSchema<T>) {
  try {
    return await agent.run({ prompt, schema });
  } catch (error) {
    const fixedPrompt = `${prompt}\n\nReturn JSON that matches the schema exactly.`;
    return await agent.run({ prompt: fixedPrompt, schema });
  }
}
```

### Pattern: Fallback to unstructured output

```typescript
async function runWithFallback(prompt: string) {
  try {
    return await agent.run({ prompt, schema: strictSchema });
  } catch {
    return await agent.run({ prompt });
  }
}
```

---

## Schema validation guidelines

- Use `z.enum` for constrained outputs
- Use `z.array` for collections
- Use `z.object` for nested structures
- Use `z.strict()` if you must forbid extra keys

```typescript
const schema = z.object({
  title: z.string(),
  tasks: z.array(z.string()),
}).strict();
```

---

## ❌ BAD / ✅ GOOD patterns

### 1) Returning prose with JSON

❌ BAD
```typescript
const schema = z.object({ title: z.string() });
await agent.run({
  prompt: "Give me a title and explain it",
  schema,
});
```

✅ GOOD
```typescript
const schema = z.object({ title: z.string() });
await agent.run({
  prompt: "Return JSON only with field title",
  schema,
});
```

### 2) Using ambiguous field names

❌ BAD
```typescript
const schema = z.object({
  data: z.string(),
  value: z.string(),
});
```

✅ GOOD
```typescript
const schema = z.object({
  summary: z.string(),
  decision: z.enum(["approve", "reject"]),
});
```

### 3) Mixing arrays and single values

❌ BAD
```typescript
const schema = z.object({ risks: z.string() });
```

✅ GOOD
```typescript
const schema = z.object({ risks: z.array(z.string()) });
```

---

## Output normalization patterns

### Normalize enums

```typescript
const schema = z.object({
  severity: z.enum(["low", "medium", "high"]),
});
```

### Normalize dates

```typescript
const schema = z.object({
  dueDate: z.string().describe("ISO 8601 date"),
});
```

---

## Structured output checklist

- [ ] Provide a strict schema for the response
- [ ] Use `z.enum` for constrained fields
- [ ] Specify optional vs required fields
- [ ] Keep fields short and unambiguous
- [ ] Avoid instructions that invite prose
- [ ] Validate and retry on failure

---

## Advanced recipes

### Recipe: Extracting a checklist

```typescript
const schema = z.object({
  checklist: z.array(z.object({
    id: z.string(),
    task: z.string(),
    owner: z.string().optional(),
  })),
});

const data = await agent.run({
  prompt: "Extract a checklist of tasks as JSON",
  schema,
});
```

### Recipe: Triage classification

```typescript
const schema = z.object({
  category: z.enum(["bug", "feature", "question"]),
  priority: z.enum(["p0", "p1", "p2", "p3"]),
  rationale: z.string(),
});
```

### Recipe: Multi‑object payload

```typescript
const schema = z.object({
  summary: z.string(),
  items: z.array(z.object({
    id: z.string(),
    impact: z.enum(["low", "medium", "high"]),
  })),
  followUps: z.array(z.string()),
});
```

---

## Debugging tips

| Symptom | Likely cause | Fix |
|---|---|---|
| Validation fails repeatedly | Prompt too vague | Provide explicit schema in prompt |
| Extra keys appear | Model adds commentary | Use `z.strict()` and “JSON only” |
| Wrong data types | Field names ambiguous | Rename fields to be explicit |

---

## Streaming events + schema logging

Use mcp-use structured output events (not generic LangChain events) when observing schema conversion. `streamEvents()` returns an `AsyncGenerator<StreamEvent>`; iterate with `for await` and check `event.event`:

```typescript
const schema = z.object({ summary: z.string(), items: z.array(z.string()) });

for await (const event of agent.streamEvents({ prompt: "Produce JSON only", schema })) {
  if (event.event === "on_structured_output_progress") {
    console.log("Converting...");
  } else if (event.event === "on_structured_output") {
    const result = schema.parse(event.data.output);
    console.log("Final structured result:", result);
  } else if (event.event === "on_structured_output_error") {
    console.error("Structured output failed");
  }
}
```

---

## Summary

- Pass `schema` to `run()` or `streamEvents()` to get validated, typed output.
- Use Zod for structured, typed responses with full TypeScript inference.
- `run()` / `stream()`: schema conversion happens post-execution.
- `streamEvents()`: returns an `AsyncGenerator<StreamEvent, void, void>`. Schema info is injected into the query before execution. Iterate with `for await` and check `event.event` for `"on_structured_output_progress"`, `"on_structured_output"` (result at `event.data.output`), and `"on_structured_output_error"`.
- `stream()`: returns `AsyncGenerator<AgentStep, string | T, void>` for step-by-step tool call streaming. Also accepts `schema` in the options object form.
- `prettyStreamEvents()`: returns `AsyncGenerator<void, string, void>` for CLI-friendly formatted output.
- Both `stream()` and `streamEvents()` accept either a plain `string` prompt (deprecated but supported) or a `RunOptions` object `{ prompt, schema?, maxSteps?, signal? }`.
- The system retries formatting up to **3 times** before throwing an error.
- Use `.describe()` on Zod fields to give the agent guidance on what each field should contain.
- Call `await client.closeAllSessions()` at the application level when done — this is the canonical cleanup and matches the official examples.
- Use `agent.clearConversationHistory()` to reset memory between runs.
- `agent.close()` is a superset of `client.closeAllSessions()` (it also resets internal agent state). Pick **one** of the two — calling both in sequence is redundant and will attempt session cleanup twice.


---

## Agent lifecycle methods

These methods manage agent state and resources; they are not specific to structured output but are part of the MCPAgent API.

```typescript
// Reset conversation memory between independent runs
agent.clearConversationHistory();

// Canonical cleanup at the application level — closes all active MCP server sessions
await client.closeAllSessions();

// Alternative: agent.close() is a superset of closeAllSessions() that also
// resets agent state. Pick ONE; calling both is redundant.
// await agent.close();
```

| Method | On | Purpose |
|---|---|---|
| `clearConversationHistory()` | `MCPAgent` | Wipes stored conversation memory |
| `closeAllSessions()` | `MCPClient` | Canonical cleanup — terminates all active MCP server sessions. Use when you own the `MCPClient` lifecycle (most common; matches official examples). |
| `close()` | `MCPAgent` | Superset of `client.closeAllSessions()` that also resets internal agent state. Use when you own only the agent and want a single-method cleanup. |

> Pick **one** of `client.closeAllSessions()` or `agent.close()` per shutdown — they are not complementary. Calling both will attempt session cleanup twice.

---

## Schema evolution and versioning

Treat schemas as contracts. When requirements change, version them.

```typescript
const v1 = z.object({
  title: z.string(),
  summary: z.string(),
});

const v2 = z.object({
  title: z.string(),
  summary: z.string(),
  risks: z.array(z.string()),
});
```

**Guidelines:**

- Keep old versions for backward compatibility
- Add fields as optional first
- Migrate to required fields after consumers update

---

## Handling large arrays

Large arrays increase token usage and validation time.

**Use caps:**

```typescript
const schema = z.object({
  items: z.array(z.string()).max(20),
});
```

**Use pagination in prompts:**

```typescript
await agent.run({
  prompt: "Return only the top 10 items",
  schema,
});
```

---

## Error handling with Zod issues

Capture detailed validation errors for debugging.

```typescript
try {
  await agent.run({ prompt, schema });
} catch (error) {
  if (error instanceof z.ZodError) {
    console.error("Schema errors", error.issues);
  }
  throw error;
}
```

---

## Multi‑stage extraction

For complex data, extract in stages.

```typescript
const outlineSchema = z.object({
  sections: z.array(z.string()),
});

const outline = await agent.run({
  prompt: "Outline the report sections as JSON",
  schema: outlineSchema,
});

const detailSchema = z.object({
  sections: z.array(z.object({
    title: z.string(),
    bullets: z.array(z.string()),
  })),
});

const detailed = await agent.run({
  prompt: `Expand these sections: ${JSON.stringify(outline)}`,
  schema: detailSchema,
});
```

---

## Testing structured output

Use deterministic prompts in tests.

```typescript
const schema = z.object({ ok: z.boolean() });
const data = await agent.run({ prompt: "Return { ok: true } only", schema });
expect(data.ok).toBe(true);
```

---

## Additional BAD/GOOD examples

### 4) Unbounded enums

❌ BAD
```typescript
const schema = z.object({ stage: z.string() });
```

✅ GOOD
```typescript
const schema = z.object({ stage: z.enum(["alpha", "beta", "ga"]) });
```

### 5) Missing explicit JSON instruction

❌ BAD
```typescript
await agent.run({ prompt: "List the items", schema });
```

✅ GOOD
```typescript
await agent.run({ prompt: "Return JSON only with items[]", schema });
```
