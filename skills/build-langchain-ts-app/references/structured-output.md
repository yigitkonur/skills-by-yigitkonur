# Structured Output Reference

Complete reference for structured output in LangChain.js. All code verified against langchain@1.x, @langchain/core@1.x, @langchain/openai@1.x. TypeScript only.

---

## `withStructuredOutput()` — Full API

### Method signature

```ts
model.withStructuredOutput<RunOutput extends Record<string, any> = Record<string, any>>(
  outputSchema: Record<string, any> | InteropZodType<RunOutput> | SerializableSchema<RunOutput>,
  config?: StructuredOutputMethodOptions<false>
): Runnable<BaseLanguageModelInput, RunOutput>
```

When `includeRaw: true` is passed, the return type widens:

```ts
model.withStructuredOutput(schema, { includeRaw: true })
// → Runnable<BaseLanguageModelInput, { raw: AIMessage; parsed: RunOutput | null }>
```

### `StructuredOutputMethodOptions` properties

| Property | Type | Default | Description |
|---|---|---|---|
| `name` | `string` | `undefined` | Name for the internal tool used in structured output. Appears in traces; helps observability when multiple schemas are in play. |
| `method` | `"functionCalling" \| "jsonMode" \| "jsonSchema" \| string` | `"functionCalling"` | Which enforcement strategy to use. Provider support varies — see Provider Differences. |
| `strict` | `boolean` | `false` | Enforce strict JSON Schema validation at the API level. OpenAI-only via `strict: true`; has no effect on other providers. |
| `includeRaw` | `boolean` | `false` | When `true`, returns `{ raw: AIMessage, parsed: T \| null }` alongside the parsed object for access to token usage and response metadata. |

### Schema types accepted

```ts
type ResponseFormat =
  | ZodSchema<T>             // z.object, z.array wrapping, etc.
  | StandardSchema<T>        // any Standard Schema spec library (e.g. Valibot)
  | Record<string, unknown>  // raw JSON Schema object
  | ResponseFormat[]         // array → union types via toolStrategy
```

### Type inference

Passing a concrete Zod schema enables full generic inference:

```ts
import * as z from "zod";

const Movie = z.object({
  title: z.string(),
  year: z.number(),
  director: z.string(),
  rating: z.number(),
});

const structured = model.withStructuredOutput(Movie);
const result = await structured.invoke("Tell me about Inception");
result.title; // string — fully typed
```

**Bug #8413** (LangChain v0.3.24): Importing from `"zod/v4"` breaks inference — `RunOutput` falls back to `Record<string, any>`. Always import from `"zod"` (v3 path) until v4 support lands.

### `includeRaw` for token usage and metadata

```ts
const structured = model.withStructuredOutput(Movie, { includeRaw: true });
const { raw, parsed } = await structured.invoke("Tell me about Inception");
// raw   → AIMessage with usage_metadata, response_metadata, finish reason
// parsed → { title, year, director, rating } | null
```

Use `includeRaw: true` when you need token counts, finish reason, or stop sequences alongside the parsed object. When parsing fails, `parsed` is `null` rather than throwing — useful for graceful fallback.

**Bug #9100** (LangChain 0.3.35): Calling `withStructuredOutput` with `{ includeRaw: true }` mutates the passed Zod schema and strips `.transform()` definitions. Workaround: pass a clean copy and apply transforms post-hoc:

```ts
const schemaForSO = z.object({ name: z.string() }); // clean copy
const canonical  = z.object({ name: z.string().transform(s => s.toUpperCase()) });

const structured = model.withStructuredOutput(schemaForSO, { includeRaw: true });
const { parsed } = await structured.invoke("...");
const final = canonical.parse(parsed); // apply transforms post-hoc
```

---

## Agent-Level Structured Output (LangChain v1 SDK)

For `import { createAgent } from "langchain"`, use `responseFormat` on `createAgent` rather than `model.withStructuredOutput` directly.

### `toolStrategy` (recommended default)

Enforces structured output via tool calling; works on any model with tool support:

```ts
import { createAgent, toolStrategy } from "langchain";
import * as z from "zod";

const ProductRating = z.object({
  rating: z.number().min(1).max(5).describe("Rating from 1-5"),
  comment: z.string().describe("Review comment"),
});

const agent = createAgent({
  model: "gpt-4o-mini",
  tools: [],
  responseFormat: toolStrategy(ProductRating),
});

const result = await agent.invoke({
  messages: [{ role: "user", content: "Rate this: Amazing product!" }],
});
// result.structuredResponse → { rating: number; comment: string }
// result.messages          → Message[]
```

`toolStrategy` function signature:

```ts
function toolStrategy<T>(
  responseFormat: JsonSchemaFormat | ZodSchema<T> | SerializableSchema | Array<...>,
  options?: {
    toolMessageContent?: string;
    handleError?: true | false | ((error: ToolStrategyError) => string | Promise<string>);
  }
): ToolStrategy<T>;
```

### `providerStrategy` (native provider enforcement)

Uses native provider-level schema enforcement when `model.profile.structuredOutput === true`. Falls back to `toolStrategy` when the model does not support native structured outputs:

```ts
import { createAgent, providerStrategy } from "langchain";

const agent = createAgent({
  model: "gpt-4o",
  tools: [],
  responseFormat: providerStrategy(ProductRating), // uses OpenAI jsonSchema natively
});
```

```ts
function providerStrategy<T>(
  schema: ZodSchema<T> | SerializableSchema | JsonSchemaFormat
): ProviderStrategy<T>;
```

LangChain automatically selects `providerStrategy` when the model profile reports `structuredOutput: true`; otherwise it falls back to `toolStrategy`.

---

## Zod Schema Patterns

### Rule: always import from `"zod"` not `"zod/v4"`

```ts
import * as z from "zod";  // v3 path — required for type inference and provider compatibility
```

### Flat schema (recommended baseline)

```ts
const ResponseSchema = z.object({
  answer: z.string().describe("The answer to the user's question"),
  followup: z.string().describe("A possible follow-up question"),
  confidence: z.number().min(0).max(1).describe("Confidence level 0-1"),
});
```

### Nested objects

```ts
const AddressSchema = z.object({
  street: z.string(),
  city: z.string(),
  country: z.string(),
});

const PersonSchema = z.object({
  name: z.string(),
  age: z.number().int().positive(),
  address: AddressSchema,
});
```

Deep nesting increases partial-streaming errors and reduces rendering flexibility. Prefer flat schemas when possible.

### Arrays — always wrap in an object

**Bug #7643** (`@langchain/core` 0.3.37): Passing a top-level `z.array()` to `withStructuredOutput` returns an array of strings instead of objects on Ollama.

```ts
// AVOID:
const schema = z.array(ItemSchema);

// PREFER:
const schema = z.object({ items: z.array(ItemSchema) });
const structured = model.withStructuredOutput(schema);
const { items } = await structured.invoke("...");
```

### Enum fields

```ts
const ReviewSchema = z.object({
  sentiment: z.enum(["positive", "neutral", "negative"]),
  categories: z.array(z.enum(["tech", "design", "business"])),
  score: z.number().min(1).max(5),
});
```

### Optional fields — use `.nullish()` not `.optional()`

**Bug #7787**: After a `zod-to-json-schema` update (Feb 2025), `z.string().optional()` is emitted as required in OpenAI tool schemas. Use `.nullish()` instead:

```ts
const schema = z.object({
  name: z.string(),
  description: z.string().nullish(), // optional + nullable — safe on all providers
  metadata: z.object({
    source: z.string(),
    author: z.string().nullish(),
  }),
});
```

### Discriminated unions — use a flat enum discriminant

`z.discriminatedUnion()` and `z.union()` are **not reliably supported** across providers:

- **Gemini** → 400 error (issue #8872)
- **Google Vertex AI** → throws; explicitly unsupported in reference docs
- **Anthropic** → JSON Schema union constructs ignored at API level

```ts
// AVOID:
const schema = z.discriminatedUnion("type", [
  z.object({ type: z.literal("text"), content: z.string() }),
  z.object({ type: z.literal("image"), url: z.string().url() }),
]);

// PREFER — flat schema with manual discriminant:
const schema = z.object({
  type: z.enum(["text", "image"]).describe("Response type"),
  content: z.string().nullish().describe("Text content (when type=text)"),
  url: z.string().nullish().describe("Image URL (when type=image)"),
});
// Discriminate in application code: switch (result.type) { ... }
```

### Full composite example

```ts
const AnalysisSchema = z.object({
  summary: z.string().min(1).max(1000).describe("Summary of the analysis"),
  confidence: z.number().min(0).max(1).describe("Confidence level 0-1"),
  steps: z.array(z.string()).describe("Reasoning steps"),
  categories: z.array(z.enum(["tech", "design", "business"])).describe("Matched categories"),
  metadata: z.object({
    source: z.string().describe("Data source identifier"),
    author: z.string().nullish().describe("Author name if known"),
  }),
});
```

### Field `.describe()` for model compliance

Adding `.describe()` to every field substantially improves model adherence — descriptions become part of the schema the model sees:

```ts
const ProductSchema = z.object({
  name: z.string().describe("Product name as listed in the catalog"),
  price: z.number().describe("Price in USD, positive number"),
  inStock: z.boolean().describe("Whether the item is currently available"),
  tags: z.array(z.string()).describe("Lowercase category tags"),
});
```

---

## Complete Output Parser Catalog

### Import paths

| Parser | Import Path | Streams |
|---|---|---|
| `StringOutputParser` | `@langchain/core/output_parsers` | No |
| `CommaSeparatedListOutputParser` | `@langchain/core/output_parsers` | No |
| `NumberedListOutputParser` | `@langchain/core/output_parsers` | No |
| `MarkdownListOutputParser` | `@langchain/core/output_parsers` | No |
| `JsonOutputParser` | `@langchain/core/output_parsers` | Yes (partial JSON) |
| `JsonMarkdownStructuredOutputParser` | `@langchain/core/output_parsers` | Yes (partial JSON) |
| `StructuredOutputParser` | `@langchain/core/output_parsers` | No |
| `XMLOutputParser` | `@langchain/core/output_parsers` | No |
| `BytesOutputParser` | `@langchain/core/output_parsers` | No |
| `JsonOutputToolsParser` | `@langchain/core/output_parsers/openai_tools` | No |
| `JsonOutputKeyToolsParser` | `@langchain/core/output_parsers/openai_tools` | No |
| `OutputFixingParser` | `langchain/output_parsers` | Depends on inner parser |
| `RetryOutputParser` | `langchain/output_parsers` | Depends on inner parser |

### `StringOutputParser`

Returns the model's text content as a raw string. Use for any non-structured output chain.

```ts
import { StringOutputParser } from "@langchain/core/output_parsers";

const chain = prompt.pipe(model).pipe(new StringOutputParser());
const result = await chain.invoke({ question: "Hello?" });
// result: string
```

### `CommaSeparatedListOutputParser`

Parses a comma-delimited response into `string[]`. Use `getFormatInstructions()` to inject the expected format into the prompt:

```ts
import { CommaSeparatedListOutputParser } from "@langchain/core/output_parsers";

const parser = new CommaSeparatedListOutputParser();
const result = await parser.parse("red, green, blue");
// ["red", "green", "blue"]
```

### `JsonOutputParser` (streaming-capable)

Parses raw JSON text; uses `parsePartialJson` internally for incremental streaming. Does not validate against a schema.

```ts
import { JsonOutputParser } from "@langchain/core/output_parsers";

const parser = new JsonOutputParser<{ name: string; age: number }>();
const chain = prompt.pipe(model).pipe(parser);

// Streaming — each chunk is a progressively complete partial object:
for await (const chunk of await chain.stream(input)) {
  console.log(chunk); // e.g. { name: "Alice" } before age arrives
}
```

Difference from `StructuredOutputParser`: no Zod validation, no format instructions injected.
Difference from `JsonMarkdownStructuredOutputParser`: does not strip markdown code fences before parsing.

### `JsonMarkdownStructuredOutputParser`

Identical to `JsonOutputParser` but strips triple-backtick markdown code fences before parsing. Use when the model wraps JSON in ` ```json ... ``` ` blocks.

```ts
import { JsonMarkdownStructuredOutputParser } from "@langchain/core/output_parsers";

const parser = new JsonMarkdownStructuredOutputParser();
const result = await parser.parse("```json\n{\"name\": \"Alice\"}\n```");
// { name: "Alice" }
```

### `StructuredOutputParser.fromZodSchema()`

Prompt-based structured output. Injects format instructions into the prompt and validates the model's JSON response against a Zod schema. Works on models without tool-calling.

```ts
import { StructuredOutputParser } from "@langchain/core/output_parsers";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import * as z from "zod";

const schema = z.object({
  recipe: z.string().describe("The recipe instructions"),
  ingredients: z.array(z.string()).describe("List of ingredients"),
  time: z.number().describe("Cook time in minutes"),
});

const parser = StructuredOutputParser.fromZodSchema(schema);

const prompt = ChatPromptTemplate.fromTemplate(
  "Answer the question below.\n{format_instructions}\n\nQuestion: {question}"
);

const chain = RunnableSequence.from([
  { question: (i: { question: string }) => i.question,
    format_instructions: () => parser.getFormatInstructions() },
  prompt,
  model,
  parser,
]);

const result = await chain.invoke({ question: "How do I make pasta?" });
// result: { recipe: string; ingredients: string[]; time: number }
```

Static method signature:

```ts
StructuredOutputParser.fromZodSchema<T extends InteropZodType>(schema: T): StructuredOutputParser<T>
```

When to use vs `withStructuredOutput`:
- `fromZodSchema` → any model including those without tool calling; prompt injection; ~80-90% reliability
- `withStructuredOutput` → requires tool calling or JSON mode; types inferred automatically; ~95-99% reliability

### `XMLOutputParser`

Parses XML-structured responses into a JavaScript object. All types are strings in XML responses.

```ts
import { XMLOutputParser } from "@langchain/core/output_parsers";

const parser = new XMLOutputParser();
const result = await parser.parse(
  "<response><name>Alice</name><age>30</age></response>"
);
// { name: "Alice", age: "30" }
```

Use case: Claude naturally produces XML when prompted for structured output.

### `OutputFixingParser`

Wraps an inner parser. When parsing fails, makes a second LLM call asking the model to fix the malformed output:

```ts
import { OutputFixingParser } from "langchain/output_parsers";
import { StructuredOutputParser } from "@langchain/core/output_parsers";
import { ChatOpenAI } from "@langchain/openai";

const innerParser = StructuredOutputParser.fromZodSchema(
  z.object({ name: z.string(), score: z.number() })
);

const fixingParser = OutputFixingParser.fromLLM(
  new ChatOpenAI({ temperature: 0 }),
  innerParser
);

const result = await fixingParser.parse("{'name': 'Bob', score: 8}");
// { name: "Bob", score: 8 } — repaired from invalid JSON
```

Cost note: adds one LLM call per failure. For high-volume production, `withStructuredOutput` with built-in retry is more cost-efficient.

### `RetryOutputParser`

Wraps an inner parser. On failure, re-runs the full LLM call with the original prompt rather than just asking to fix the output text:

```ts
import { RetryOutputParser } from "langchain/output_parsers";
import { JsonOutputParser } from "@langchain/core/output_parsers";

const retryParser = RetryOutputParser.fromLLM(
  new ChatOpenAI({ temperature: 0 }),
  new JsonOutputParser<{ name: string }>(),
  { maxRetries: 3 } // default: 3
);

// Requires original PromptValue that produced badOutput:
const result = await retryParser.parseWithPrompt(badOutput, originalPromptValue);
```

Key difference: `OutputFixingParser` sends the bad output to the LLM to fix; `RetryOutputParser` re-runs the original generation from scratch.

### `JsonOutputKeyToolsParser`

Extracts a single tool call's arguments from a tool-calling model response:

```ts
import { JsonOutputKeyToolsParser } from "@langchain/core/output_parsers/openai_tools";

const parser = new JsonOutputKeyToolsParser({
  keyName: "extract_location", // tool name to extract
  returnSingle: true,           // only first call when multiple returned
  zodSchema: z.object({ city: z.string(), country: z.string() }),
});

const chain = model.bindTools([locationTool]).pipe(parser);
const result = await chain.invoke("Where is the Eiffel Tower?");
// { city: "Paris", country: "France" }
```

Properties: `keyName: string`, `returnSingle: boolean`, `zodSchema?: InteropZodType<T>`. Supports `.withRetry()`, `.withFallbacks()`, `.withConfig()`.

### `parsePartialJson` utility

Standalone utility for progressive JSON parsing during streaming:

```ts
import { parsePartialJson } from "@langchain/core/utils/json";

parsePartialJson('{"name": "Al');              // → { name: "Al" }
parsePartialJson('{"name": "Alice", "ag');     // → { name: "Alice" }
parsePartialJson('{"name": "Alice", "age": 3'); // → { name: "Alice", age: 3 }
```

Use in custom streaming accumulators when granular control over partial JSON rendering is needed.

---

## LCEL Chain Patterns with Output Parsers

### Basic pipe chain with `StructuredOutputParser`

```ts
import { ChatOpenAI } from "@langchain/openai";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StructuredOutputParser } from "@langchain/core/output_parsers";
import { RunnableSequence } from "@langchain/core/runnables";
import * as z from "zod";

const model = new ChatOpenAI({ model: "gpt-4o-mini", temperature: 0 });

const movieSchema = z.object({
  title: z.string().describe("Movie title"),
  year: z.number().describe("Release year"),
  actors: z.array(z.string()).describe("Main actors"),
});

const parser = StructuredOutputParser.fromZodSchema(movieSchema);
const prompt = ChatPromptTemplate.fromTemplate(
  `Suggest a movie based on the genre.\n{format_instructions}\nGenre: {genre}`
);

// Using RunnableSequence to inject format_instructions automatically:
const chain = RunnableSequence.from([
  {
    format_instructions: () => parser.getFormatInstructions(),
    genre: (input: { genre: string }) => input.genre,
  },
  prompt,
  model,
  parser,
]);

const result = await chain.invoke({ genre: "sci-fi" });
// result: { title: string; year: number; actors: string[] }
```

### `withStructuredOutput` directly in LCEL

No format instructions needed in the prompt — schema binding is handled by the model:

```ts
const structuredModel = model.withStructuredOutput(movieSchema);
const chain = prompt.pipe(structuredModel);

const result = await chain.invoke({ genre: "sci-fi", format_instructions: "" });
// result: { title: string; year: number; actors: string[] }
```

### Streaming LCEL with partial JSON

For streaming partial JSON updates, use `JsonOutputParser` (not `StructuredOutputParser`):

```ts
import { JsonOutputParser } from "@langchain/core/output_parsers";

const chain = ChatPromptTemplate.fromTemplate(
  "Return JSON with title and year for a {genre} movie"
).pipe(model).pipe(new JsonOutputParser<typeof movieSchema._type>());

for await (const chunk of await chain.stream({ genre: "action" })) {
  // Progressive updates: { title: "..." } then { title: "...", year: 2024 }
  renderPartialUI(chunk);
}
```

### Adding retry and fallback to any runnable

```ts
// Retry up to 3 attempts on failure:
const robustModel = model
  .withStructuredOutput(MySchema)
  .withRetry({ stopAfterAttempt: 3, onFailedAttempt: (err) => console.warn(err) });

// Fallback to a secondary model on failure:
const modelWithFallback = model
  .withStructuredOutput(MySchema)
  .withFallbacks({
    fallbacks: [backupModel.withStructuredOutput(MySchema)],
  });
```

### Chaining transforms after a parser

Every output parser exposes `pipe()`, enabling composable post-processing:

```ts
const pipeline = parser
  .pipe((parsed) => ({ ...parsed, processedAt: new Date().toISOString() }));
```

---

## Streaming Structured Output

### The core limitation

`withStructuredOutput` validates the **complete** message. Calling `.stream()` on a chain that uses it emits only **one chunk** (the final complete result), not incremental partial objects — **Bug #6440**.

### Recommended approach: `streamEvents` v2

```ts
import { StructuredOutputParser } from "@langchain/core/output_parsers";

const parser = StructuredOutputParser.fromZodSchema(mySchema);
const structuredModel = model.withStructuredOutput(parser);
const chain = prompt.pipe(structuredModel);

const stream = await chain.streamEvents(input, {
  version: "v2",
  encoding: "text/event-stream",
});

// SSE-compatible response (Next.js / Express):
return new Response(stream, {
  headers: {
    Connection: "keep-alive",
    "Content-Encoding": "none",
    "Cache-Control": "no-cache, no-transform",
    "Content-Type": "text/event-stream; charset=utf-8",
  },
});
```

Client-side consumption with `@microsoft/fetch-event-source`:

```ts
import { fetchEventSource } from "@microsoft/fetch-event-source";

await fetchEventSource("/api/chat", {
  method: "POST",
  body: JSON.stringify({ prompt }),
  onmessage: (message) => {
    const evt = JSON.parse(message.data);
    if (evt.event === "on_chain_stream" && evt.data.chunk) {
      // Update UI progressively
    }
  },
});
```

### True incremental streaming with `JsonOutputParser`

Bypasses `withStructuredOutput` entirely and delivers incremental partial objects via `parsePartialJson`:

```ts
import { JsonOutputParser } from "@langchain/core/output_parsers";

const chain = prompt.pipe(model).pipe(new JsonOutputParser());

for await (const chunk of await chain.stream(input)) {
  // Each chunk is a partial JSON object as tokens arrive
  console.log(chunk);
}
```

### `includeRaw: true` + `strict: true` breaks streaming — Bug #7116

Combining both options suppresses intermediate chunks; only the final `raw` and `parsed` arrive:

```ts
// AVOID for streaming:
model.withStructuredOutput(schema, { strict: true, method: "jsonSchema", includeRaw: true });
```

Workarounds: (1) disable `includeRaw` during streaming and collect raw separately if needed; (2) remove `strict: true`; (3) switch to non-streaming mode when both flags are required.

### Progressive rendering with partial structured data (React)

```ts
function extractStructuredOutput<T>(
  messages: Message[],
  requiredFields?: (keyof T)[]
): Partial<T> | null {
  const aiMsg = messages.findLast(m => m.role === "assistant");
  const args = aiMsg?.tool_calls?.[0]?.args;
  if (!args) return null;
  if (requiredFields?.some(f => !(f in args))) return null;
  return args as Partial<T>;
}

// In a React component:
const partial = extractStructuredOutput<Recipe>(stream.messages, ["title", "ingredients"]);
if (partial) {
  // Render what's available; re-render as more fields arrive
}
```

---

## Provider Differences

### Method support matrix

| Provider | `functionCalling` | `jsonMode` | `jsonSchema` | `strict` | Notes |
|---|---|---|---|---|---|
| **OpenAI** | Yes (default) | Yes | Yes (gpt-4o-mini-2024-07-18+, gpt-4o-2024-08-06+) | Yes (`jsonSchema` only) | Most reliable; strict mode guarantees 100% conformance |
| **Anthropic** | Yes | No | No (beta only) | No | Tool calling only; native beta via `anthropic-beta: structured-outputs-2025-11-13` header on Sonnet 4.5+, Opus 4.1+ |
| **Google Gemini** | Yes (fallback) | Yes (`responseMimeType: "application/json"`) | Partial | No | Discriminated unions → 400 error; numeric refinements → 400 error on Gemini 2.5 |
| **Google Vertex AI** | Yes | Yes | Partial | No | `z.discriminatedUnion()` and `z.union()` throw; complex nested schemas may fail |
| **Groq** | Yes | Yes | Partial | No | Tool calling added Apr 2024; union type incompatibility with TypeScript — see #6795 |
| **Ollama** | Yes | Yes | Experimental | No | Top-level `z.array` bug; adherence depends on local model behavior |

### OpenAI

Most reliable provider for structured output.

```ts
// jsonSchema + strict mode — 100% schema conformance at API level:
const structured = model.withStructuredOutput(MySchema, {
  method: "jsonSchema",
  strict: true,
});
```

- Cannot use `bindTools()` and `withStructuredOutput()` simultaneously — choose one
- Optional Zod fields may be serialized as required (bug #7787); use `.nullish()` as workaround

### Anthropic

Works via function/tool calling internally. `jsonMode` and `jsonSchema` method options are not supported in LangChain for Anthropic.

```ts
import { ChatAnthropic } from "@langchain/anthropic";

const model = new ChatAnthropic({ model: "claude-opus-4-1" });
const structured = model.withStructuredOutput(MySchema); // uses tool-calling internally
```

Cannot use reasoning/thinking mode (`thinking: { type: "enabled" }`) simultaneously with forced tool-calling for structured output — disable thinking or handle missing tool-call gracefully.

### Gemini

Keep schemas flat and constraint-free on Gemini:

```ts
// Gemini-safe schema — no z.union, no numeric refinements:
const schema = z.object({
  type: z.enum(["text", "image"]),
  content: z.string().nullish(),
  score: z.number(), // no .min()/.max()/.positive()/.int()
});
```

- Numeric refinements like `.positive()`, `.int()`, `.min()`, `.max()` cause 400 errors on Gemini 2.5
- Zod 4 schemas incompatible with Gemini's schema generator (bug #8769)
- `z.discriminatedUnion()` → 400 error (bug #8872)

### Groq

```ts
// TypeScript union type workaround for ChatGroq | ChatOpenAI:
type AnyModel = { withStructuredOutput: typeof model.withStructuredOutput };
```

### Model profile `structuredOutput` flag

```ts
import { initChatModel } from "langchain";

const model = await initChatModel("gpt-4o", { temperature: 0 });
console.log(model.profile);
// { structuredOutput: true, toolCalling: true, maxInputTokens: 128000, ... }
```

`providerStrategy` is selected automatically when `structuredOutput: true`; `toolStrategy` is used as fallback.

---

## Error Handling and Retry

### `toolStrategy` built-in error handling

```ts
// Default: automatic retry on schema validation errors
const fmt = toolStrategy(ProductRating);

// Custom static error message:
const fmt = toolStrategy(ProductRating, {
  handleError: "Please provide a rating between 1-5 and a comment.",
});

// Custom function-based handling:
const fmt = toolStrategy(ProductRating, {
  handleError: (err) => {
    if (err instanceof ToolInputParsingException) {
      return "Please provide a valid rating between 1-5 and a comment.";
    }
    return err.message;
  },
});

// Disable error handling:
const fmt = toolStrategy(ProductRating, { handleError: false });
```

Errors handled: multiple tool calls returned (emits `ToolMessage` error, retries for single call); Zod/JSON schema validation failures (reports in `ToolMessage`, agent retries with corrected output).

### Bug #9426 — automatic retry does not always fire

`PregelRunner` retry logic is not entered on `StructuredOutputParsingError` in LangChain 1.0.4. Workaround — manual retry:

```ts
import { StructuredOutputParsingError } from "langchain";

async function invokeWithRetry(
  agent: ReturnType<typeof createAgent>,
  messages: Message[],
  maxAttempts = 3
) {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      return await agent.invoke({ messages });
    } catch (e) {
      if (e instanceof StructuredOutputParsingError && attempt < maxAttempts - 1) {
        continue;
      }
      throw e;
    }
  }
}
```

### `toolRetryMiddleware` — exponential backoff for tool failures

```ts
import { createAgent, toolRetryMiddleware } from "langchain";

const agent = createAgent({
  model: "gpt-4o-mini",
  tools: [myTool],
  middleware: [
    toolRetryMiddleware({
      maxRetries: 2,         // default: 2 (total attempts = maxRetries + 1)
      initialDelayMs: 1000,  // default: 1000ms
      backoffFactor: 2.0,    // default: 2.0 (exponential)
      maxDelayMs: 60000,     // default: 60000ms cap
      jitter: true,          // default: true (±25% random jitter)
      retryOn: () => true,   // default: retry on all errors
      onFailure: "continue", // "continue" | "error" | (err) => string
      tools: [myTool],       // omit = apply to all tools
    }),
  ],
});
```

### `includeRaw` for graceful parse-failure handling

When `includeRaw: true`, failures return `parsed: null` rather than throwing:

```ts
const structured = model.withStructuredOutput(schema, { includeRaw: true });
const { raw, parsed } = await structured.invoke(messages);

if (parsed === null) {
  console.error("Parsing failed, raw output:", raw.content);
  // log, retry with adjusted prompt, or return a default value
}
```

### Markdown code fence stripping — Bug #7752

If the model wraps its JSON in triple-backtick blocks, `withStructuredOutput` may fail to parse:

```ts
function stripMarkdownCodeFences(text: string): string {
  return text.replace(/```(?:json)?\n?([\s\S]*?)\n?```/g, "$1").trim();
}
```

Or use `JsonMarkdownStructuredOutputParser` which handles this automatically.

---

## Testing with `FakeListChatModel`

Use `FakeListChatModel` for deterministic unit tests without real LLM calls:

```ts
import { FakeListChatModel } from "@langchain/core/utils/testing";
import * as z from "zod";

const movieSchema = z.object({
  title: z.string(),
  year: z.number(),
  actors: z.array(z.string()),
});

const fakeModel = new FakeListChatModel({
  responses: ['{"title": "Test Movie", "year": 2024, "actors": ["Actor A"]}'],
});

const structured = fakeModel.withStructuredOutput(movieSchema);
const result = await structured.invoke("test prompt");
// result: { title: "Test Movie", year: 2024, actors: ["Actor A"] }
```

For multiple responses in sequence, provide an array:

```ts
const fakeModel = new FakeListChatModel({
  responses: [
    '{"title": "Movie A", "year": 2023, "actors": []}',
    '{"title": "Movie B", "year": 2024, "actors": ["Actor X"]}',
  ],
});
```

---

## Production Decision Matrix

### Which approach to use

| Use Case | Recommended Approach |
|---|---|
| TypeScript with tool-calling model | `model.withStructuredOutput(zodSchema)` |
| OpenAI with maximum reliability | `withStructuredOutput(schema, { method: "jsonSchema", strict: true })` |
| Model without tool calling | `StructuredOutputParser.fromZodSchema()` |
| Raw JSON without Zod validation | `JsonOutputParser` |
| Streaming partial JSON updates | `JsonOutputParser` with `.stream()` |
| Streaming from structured chain | `chain.streamEvents(input, { version: "v2" })` |
| XML output from Claude | `XMLOutputParser` |
| Single tool extraction | `JsonOutputKeyToolsParser` |
| Error auto-fix via second LLM call | `OutputFixingParser` |
| Retry entire generation on failure | `RetryOutputParser` |
| Agent-level structured output | `createAgent({ responseFormat: toolStrategy(schema) })` |
| Model supports native structured output | `createAgent({ responseFormat: providerStrategy(schema) })` |

### Reliability ranking (2025)

1. **OpenAI `jsonSchema` + `strict: true`** — 99.9%+ conformance; API-level guarantee
2. **`withStructuredOutput` via tool calling** — 95-99%; relies on model behavior
3. **`StructuredOutputParser.fromZodSchema`** (prompt-based) — 80-90%; depends on instruction following
4. **JSON Mode** — 70-85%; valid JSON not guaranteed to match schema shape
5. **Plain text + regex** — 50-70%; fragile to model output variation

### Schema design rules

1. Always wrap arrays in a containing object — top-level `z.array()` breaks on Ollama (bug #7643)
2. Add `.describe()` to every field — directly improves model compliance
3. Use `.nullish()` instead of `.optional()` — avoids OpenAI required-field serialization bug (#7787)
4. Avoid numeric refinements on Gemini — `.positive()`, `.int()`, `.min()`, `.max()` cause 400 errors
5. Avoid `z.union()` and `z.discriminatedUnion()` — not reliably supported; use flat enum discriminant
6. Clone schemas before `includeRaw: true` — prevents transform-stripping mutation bug (#9100)
7. Stay on Zod v3 (`import * as z from "zod"`) — Zod v4 breaks type inference and Gemini compat (#8413)

### Token efficiency

- Use `temperature: 0` for structured output to minimize schema-violation "creativity"
- Cache `parser.getFormatInstructions()` outside hot paths — it is deterministic
- Minimize schema field count and avoid verbose `.describe()` strings in high-volume use
- The tool schema is sent with every request when using `withStructuredOutput`

### Observability

```ts
// Name schemas for trace readability:
model.withStructuredOutput(schema, { name: "extract_movie_data" });

// Enable LangSmith tracing:
// LANGSMITH_TRACING=true in environment — traces every call with raw vs parsed output

// Use includeRaw to log raw output alongside parsed result:
const { raw, parsed } = await model.withStructuredOutput(schema, { includeRaw: true }).invoke(msg);
```
