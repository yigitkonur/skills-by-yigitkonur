# Models & Chat Models

> LangChain.js v1 | Node.js 20+ | `@langchain/core` ^0.3 | `langchain` ^1

---

## BaseChatModel Abstraction

Every provider class (`ChatOpenAI`, `ChatAnthropic`, `ChatGoogleGenerativeAI`, etc.) extends `BaseChatModel` from `@langchain/core`. This guarantees identical `invoke`, `stream`, `batch`, `bindTools`, and `withStructuredOutput` behaviour across all providers — swap providers by changing a single import or model string.

```
BaseChatModel (abstract, @langchain/core/language_models/chat_models)
└── ChatOpenAI | ChatAnthropic | ChatGoogleGenerativeAI | ChatOllama | ...

BaseChatModel extends BaseLanguageModel extends Runnable
  → inherits: invoke, stream, batch, streamEvents, pipe, withConfig,
              withRetry, withFallbacks, bind, pick, assign
```

---

## Message Types

All message classes import from `@langchain/core/messages` (re-exported from `langchain`).

```
BaseMessage (abstract)
├── HumanMessage       — user input
├── AIMessage          — model response (may contain tool_calls)
├── SystemMessage      — system instructions
├── ToolMessage        — result of a tool execution
└── AIMessageChunk     — streaming partial response
```

### BaseMessage Fields

| Field | Type | Description |
|-------|------|-------------|
| `content` | `string \| ContentBlock[]` | Message content — string or structured blocks |
| `id` | `string` | Optional unique identifier (ideally UUID) |
| `name` | `string` | Optional name of message sender |
| `response_metadata` | `Record<string, any>` | Provider-specific response metadata |
| `additional_kwargs` | `Record<string, any>` | Extra kwargs (deprecated — avoid) |

### HumanMessage

```ts
import { HumanMessage } from "@langchain/core/messages";

// Plain text
const msg = new HumanMessage("Hello, world!");

// Multimodal content blocks (source_type: "url" | "base64" | "id")
const msg = new HumanMessage({
  content: [
    { type: "text", text: "Describe this image." },
    { type: "image", source_type: "url", url: "https://example.com/img.jpg" },
    // base64: { type: "image", source_type: "base64", data: "AAA...", mimeType: "image/png" }
    // file ID: { type: "image", source_type: "id", id: "file-abc123" }
  ],
});
```

**TypeScript interface:**

```ts
class HumanMessage extends BaseMessage<TStructure, "human"> {
  type: "human";
  content: string | ContentBlock[];
  contentBlocks: Standard[];   // lazily parsed, type-safe content blocks
  text: string;                // plain text shorthand (deprecated)
  id: string;
  name: string;
  response_metadata: ResponseMetadata;
}
```

### AIMessage

```ts
import { AIMessage } from "@langchain/core/messages";

const aiMsg = await model.invoke("Hello!");

aiMsg.content;           // string | ContentBlock[]
aiMsg.text;              // string — plain text shorthand
aiMsg.tool_calls;        // ToolCall[] — populated on tool-use requests
aiMsg.id;                // string — message ID from provider
aiMsg.usage_metadata;    // UsageMetadata | null
aiMsg.response_metadata; // provider-specific metadata
aiMsg.contentBlocks;     // Standard[] — lazily parsed content blocks
```

**TypeScript interface:**

```ts
interface AIMessage {
  type: "ai";
  content: string | ContentBlock[];
  contentBlocks: Standard[];
  text: string;
  tool_calls: ToolCall[];
  invalid_tool_calls: InvalidToolCall[];
  id: string;
  usage_metadata: UsageMetadata | null;
  response_metadata: ResponseMetadata | null;
  additional_kwargs: Record<string, any>;
}

interface ToolCall {
  name: string;
  args: Record<string, any>;
  id: string;
  type: "tool_call";
}

interface InvalidToolCall {
  name: string;
  args: string;     // unparseable args string
  error: string;
  id: string;
  type: "invalid_tool_call";
}

interface UsageMetadata {
  input?: number;   // prompt tokens
  output?: number;  // completion tokens
  total?: number;   // total tokens
}
```

**`response_metadata` by provider:**

| Provider | Key Fields |
|----------|-----------|
| OpenAI | `{ id, model, finish_reason: "stop" \| "length" \| "tool_calls" \| "content_filter", usage? }` |
| Anthropic | `{ id, model, stop_reason, stop_sequence, usage }` |
| Google GenAI | `{ candidates, usageMetadata: { promptTokenCount, candidatesTokenCount, totalTokenCount } }` |

### SystemMessage

Primes model behaviour. For Anthropic it must be the very first message (hard constraint). For Google Gemini it is merged with the first human message.

```ts
import { SystemMessage } from "@langchain/core/messages";
await model.invoke([new SystemMessage("You are a helpful assistant."), new HumanMessage("...")]);
```

### ToolMessage

Contains the result of a tool execution. Linked to the originating `AIMessage.tool_calls` entry via `tool_call_id`.

```ts
import { ToolMessage } from "@langchain/core/messages";

const toolMsg = new ToolMessage({
  content: JSON.stringify({ temperature: 72, unit: "fahrenheit" }),
  tool_call_id: "call_abc123",  // MUST match AIMessage.tool_calls[n].id
  name: "get_weather",
  artifact: { raw_data: {} },   // optional — not sent to model
});
```

### AIMessageChunk

Streaming partial response. Supports concatenation via `.concat()`.

```ts
import { AIMessageChunk } from "@langchain/core/messages";

let full: AIMessageChunk | undefined;
const stream = await model.stream("Tell me a story");

for await (const chunk of stream) {
  full = full ? full.concat(chunk) : chunk;
  process.stdout.write(chunk.text);
}

console.log(full?.text);
console.log(full?.contentBlocks);
console.log(full?.tool_call_chunks);   // partial tool calls during streaming
```

### MessagesPlaceholder

Placeholder in prompt templates for dynamically injected message arrays:

```ts
import { ChatPromptTemplate, MessagesPlaceholder } from "@langchain/core/prompts";

const prompt = ChatPromptTemplate.fromMessages([
  ["system", "You are a helpful assistant"],
  new MessagesPlaceholder("history"),  // inject BaseMessage[] here
  ["human", "{input}"],
]);
```

---

## Content Block Types

`ContentBlock.*` provides type-safe multimodal support. All 14 types:

| Block Type | Required Fields | Notes |
|-----------|----------------|-------|
| `ContentBlock.Text` | `type: "text"`, `text: string` | Optional `annotations?: Citation[]` |
| `ContentBlock.Reasoning` | `type: "reasoning"`, `reasoning: string` | Extended thinking / CoT |
| `ContentBlock.Multimodal.Image` | `type: "image"` | `url`, `data` (base64), or `fileId`; optional `mimeType` |
| `ContentBlock.Multimodal.Audio` | `type: "audio"` | `url`, `data`, or `fileId`; optional `mimeType` |
| `ContentBlock.Multimodal.Video` | `type: "video"` | `url`, `data`, or `fileId`; optional `mimeType` |
| `ContentBlock.Multimodal.File` | `type: "file"` | `url`, `data`, or `fileId`; optional `mimeType` |
| `ContentBlock.Multimodal.PlainText` | `type: "text-plain"`, `text: string` | Optional `title`, `mimeType` |
| `ContentBlock.Tools.ToolCall` | `type: "tool_call"`, `name`, `args`, `id` | Standard tool invocation |
| `ContentBlock.Tools.ToolCallChunk` | `type: "tool_call_chunk"`, `name`, `args`, `id`, `index` | Streaming partial tool call |
| `ContentBlock.Tools.InvalidToolCall` | `type: "invalid_tool_call"`, `name`, `args`, `error` | Malformed call from model |
| `ContentBlock.Tools.ServerToolCall` | `type: "server_tool_call"`, `name`, `args`, `id` | Server-side tool execution |
| `ContentBlock.Tools.ServerToolResult` | `type: "server_tool_result"`, `tool_call_id`, `id`, `status`, `output?` | Server tool result |
| `ContentBlock.NonStandard` | `type: "non_standard"`, `value: object` | Provider escape hatch |

---

## initChatModel Factory

`initChatModel` is the recommended universal initializer. Accepts provider-prefixed strings to select any provider without changing call-site code.

```ts
import { initChatModel } from "langchain";

// Provider-prefix strings
await initChatModel("openai:gpt-4.1");
await initChatModel("anthropic:claude-sonnet-4-6");
await initChatModel("google-genai:gemini-2.5-flash-lite");
await initChatModel("azure_openai:gpt-5.2");
await initChatModel("bedrock:anthropic.claude-3-5-sonnet-20240620-v1:0");
await initChatModel("ollama:phi3");
// Without prefix — infers provider from env vars:
await initChatModel("gpt-5.2");           // OPENAI_API_KEY
await initChatModel("claude-sonnet-4-6"); // ANTHROPIC_API_KEY
```

### Common Options (apply to all providers)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `temperature` | `number` | provider default | Randomness — 0 = deterministic |
| `maxTokens` | `number` | — | Max response tokens |
| `timeout` | `number` (seconds) | — | Request timeout |
| `maxRetries` | `number` | `6` | Retries with exponential backoff |
| `apiKey` | `string` | env var | Authentication key |
| `baseUrl` | `string` | — | Custom endpoint (OpenAI-compatible) |
| `streaming` | `boolean` | `false` | Enable streaming mode |
| `logprobs` | `boolean` | `false` | Token-level log probabilities |
| `parallelToolCalls` | `boolean` | `true` | Enable parallel tool invocation |
| `promptCacheKey` | `string` | — | Explicit prompt caching key |
| `profile` | `ModelProfile` | — | Capability flags override |
| `cache` | `BaseCache` | — | Response cache instance |
| `rateLimiter` | `RateLimiter` | — | Rate limiter instance |

### ModelProfile Interface

```ts
interface ModelProfile {
  maxInputTokens?: number;
  toolCalling?: boolean;
  imageInputs?: boolean;
  audioInputs?: boolean;
  videoInputs?: boolean;
  structuredOutput?: boolean;
  reasoningOutput?: boolean;
}
// Check capabilities: model.profile.imageInputs, model.profile.toolCalling, etc.
```

### invoke

```ts
// Accepts: string | BaseMessage[] | { role, content }[]
const response = await model.invoke("Why do parrots have colorful feathers?");
// or: model.invoke([new SystemMessage("..."), new HumanMessage("...")])
console.log(response.text);
console.log(response.usage_metadata);    // { input: 12, output: 87, total: 99 }
console.log(response.response_metadata); // provider-specific
```

### stream

```ts
// Signature: stream(input, config?) => AsyncIterable<AIMessageChunk>
for await (const chunk of await model.stream("Explain quantum computing")) {
  process.stdout.write(chunk.text);
}
// Accumulate: let full; for await (chunk) full = full ? full.concat(chunk) : chunk;
```

### streamEvents

```ts
// Event types: on_chat_model_start | on_chat_model_stream | on_chat_model_end
for await (const ev of await model.streamEvents("Hello")) {
  if (ev.event === "on_chat_model_stream") process.stdout.write(ev.data.chunk.text);
  if (ev.event === "on_chat_model_end") console.log("Full:", ev.data.output.text);
}
```

### batch

```ts
// Signature: batch(inputs, config?) => Promise<AIMessage[]>
const responses = await model.batch(["Q1", "Q2", "Q3"]);
// With concurrency limit:
await model.batch(inputs, { maxConcurrency: 3 });
```

### Return Type Summary

| Method | Return Type | Notes |
|--------|-------------|-------|
| `invoke(input)` | `Promise<AIMessage>` | Full response after completion |
| `stream(input)` | `AsyncIterable<AIMessageChunk>` | Partial tokens as generated |
| `streamEvents(input)` | `AsyncIterable<{event, data}>` | Lifecycle events with metadata |
| `batch(inputs, config?)` | `Promise<AIMessage[]>` | Parallel, order-preserving |
| `bindTools(...).invoke(input)` | `Promise<AIMessage>` | May include `tool_calls` |
| `withStructuredOutput(schema).invoke(input)` | `Promise<T>` | Parsed schema object |
| `withStructuredOutput(schema, {includeRaw:true}).invoke(input)` | `Promise<{raw: AIMessage, parsed: T}>` | Both raw and parsed |

---

## Tool Binding

### bindTools

```ts
import { tool } from "langchain";
import * as z from "zod";
import { ChatOpenAI } from "@langchain/openai";

const getWeather = tool(
  (input: { location: string }) => `It's sunny in ${input.location}.`,
  {
    name: "get_weather",
    description: "Get the current weather for a location.",
    schema: z.object({
      location: z.string().describe("The city and state, e.g. 'Boston, MA'"),
    }),
  }
);

const model = new ChatOpenAI({ model: "gpt-4.1" });
const modelWithTools = model.bindTools([getWeather]);

const response = await modelWithTools.invoke("What's the weather in Boston?");
console.log(response.tool_calls);
// [{ name: "get_weather", args: { location: "Boston, MA" }, id: "call_abc123" }]
```

**bindTools options:**

```ts
// Force any tool
model.bindTools([getWeather], { toolChoice: "any" });

// Force specific tool by name
model.bindTools([getWeather], { toolChoice: "get_weather" });

// Disable parallel tool calls
model.bindTools([getWeather, otherTool], { parallelToolCalls: false });

// Strict schema validation (ChatOpenAI >= 0.2.6)
model.bindTools([getWeather], { strict: true, tool_choice: "get_weather" });
```

**TypeScript signature:**

```ts
bindTools(
  tools: BindToolsInput[],
  kwargs?: Partial<CallOptions>
): Runnable<BaseLanguageModelInput, OutputMessageType, CallOptions>

// BindToolsInput accepts:
// - StructuredTool (LangChain tool instance)
// - OpenAI-formatted tool { type: "function", function: {...} }
// - Provider-specific tool schema objects
```

### Full Tool Calling Loop

```ts
const messages = [new HumanMessage("Weather in Boston?")];
const aiResponse = await modelWithTools.invoke(messages);
messages.push(aiResponse);

for (const tc of aiResponse.tool_calls) {
  messages.push(new ToolMessage({
    content: await getWeather.invoke(tc.args),
    tool_call_id: tc.id,   // MUST match tool_calls[n].id
    name: tc.name,
  }));
}
console.log((await modelWithTools.invoke(messages)).text);
```

### Streaming Tool Calls

```ts
for await (const chunk of await modelWithTools.stream("Weather in Boston and Tokyo?")) {
  chunk.tool_call_chunks?.forEach(tc => console.log(`${tc.name}: ${tc.args}`));
  if (chunk.text) process.stdout.write(chunk.text);
}
```

---

## Structured Output

### withStructuredOutput — Basic Usage

```ts
import * as z from "zod";

const MovieSchema = z.object({
  title: z.string().describe("Movie title"),
  year: z.number().describe("Release year"),
  director: z.string().describe("Director name"),
  rating: z.number().min(0).max(10).describe("Rating out of 10"),
});

const modelWithStructure = model.withStructuredOutput(MovieSchema);
const movie = await modelWithStructure.invoke("Tell me about Inception");
// { title: "Inception", year: 2010, director: "Christopher Nolan", rating: 8.8 }

// Include raw AIMessage alongside parsed output
const modelWithRaw = model.withStructuredOutput(MovieSchema, { includeRaw: true });
const result = await modelWithRaw.invoke("Tell me about Inception");
result.raw;    // AIMessage
result.parsed; // { title: "Inception", ... }
```

**Options:**

```ts
model.withStructuredOutput(schema, {
  method?: "jsonSchema" | "functionCalling" | "jsonMode",
  includeRaw?: boolean,
  name?: string,    // tool name for OpenAI
  strict?: boolean, // strict schema validation (OpenAI)
})
```

> For advanced structured output patterns, multi-step extraction, and `createAgent` `responseFormat`, see `structured-output.md`.

---

## Fallbacks and Retry

### withFallbacks

```ts
import { ChatOpenAI } from "@langchain/openai";
import { ChatAnthropic } from "@langchain/anthropic";

const primary = new ChatOpenAI({ model: "gpt-4.1" });
const backup1 = new ChatAnthropic({ model: "claude-sonnet-4-6" });
const backup2 = new ChatOpenAI({ model: "gpt-4.1-mini" });

// Falls to backup models on error
const chainWithFallbacks = primary.withFallbacks([backup1, backup2]);
const result = await chainWithFallbacks.invoke("Tell me a joke");
```

### withRetry

```ts
// Via constructor
const model = new ChatOpenAI({ model: "gpt-4.1", maxRetries: 3 });

// Via method — returns new Runnable
const modelWithRetry = model.withRetry({
  maxAttempts: 3,
  delayScaling: 2,       // exponential backoff multiplier
  maxDelayMs: 120000,    // max delay between retries
  retryOnFailed: true,   // retry on 429, 5xx, timeouts
});
```

---

## Response Caching, Rate Limiting, Token Usage

```ts
import { InMemoryCache } from "@langchain/core/caches";
import { RateLimiter } from "@langchain/core/utils/rate_limit";

// Response caching (identical inputs return cached response)
const model = new ChatOpenAI({ model: "gpt-4.1", cache: new InMemoryCache() });
// or: model.withCaching(new InMemoryCache())

// Rate limiting
const limiter = new RateLimiter({ requestsPerMinute: 60 });
const modelWithRL = model.withRateLimit(limiter);
// or: initChatModel("gpt-4.1", { rateLimiter: limiter })

// Batch concurrency control
await model.batch(inputs, { maxConcurrency: 5 });
```

### Token Usage Tracking

```ts
const response = await model.invoke("Hello");
console.log(response.usage_metadata);  // { input: 10, output: 25, total: 35 }
// Provider-specific fields in response.response_metadata:
// OpenAI:    usage.prompt_tokens / completion_tokens
// Anthropic: usage.input_tokens / output_tokens
// Google:    usageMetadata.promptTokenCount / candidatesTokenCount
```

### Prompt Caching

```ts
// OpenAI — implicit (automatic for long prompts) or explicit key
new ChatOpenAI({ model: "gpt-4.1", promptCacheKey: "my-key" });

// Anthropic — beta header + cache_control on content blocks
new ChatAnthropic({ clientOptions: { defaultHeaders: { "anthropic-beta": "prompt-caching-2024-07-31" } } });
// Mark blocks: { type: "text", text: "...", cache_control: { type: "ephemeral" } }

// Google Gemini — context caching for inputs >= 32,768 tokens
// GoogleAICacheManager.create() → model.useCachedContent(cached)
```

---

## fakeModel — Testing API

`fakeModel` is the recommended way to unit-test agents without making real API calls.

```ts
import { fakeModel } from "langchain";
import { AIMessage, HumanMessage, ToolMessage } from "@langchain/core/messages";
import { tool } from "@langchain/core/tools";
import { z } from "zod";
```

### Complete API

| Method | Signature | Description |
|--------|-----------|-------------|
| `fakeModel()` | `() => FakeChatModel` | Create a fake model |
| `.respond(response)` | `(AIMessage \| HumanMessage \| ToolMessage \| ((msgs) => BaseMessage \| Error) \| Error) => this` | Queue a response |
| `.respondWithTools(toolCalls)` | `({ name, args, id? }[]) => this` | Queue a tool-call response |
| `.alwaysThrow(error)` | `(Error) => this` | Force every call to throw |
| `.structuredResponse(value)` | `(any) => this` | Set structured output return value |
| `.withStructuredOutput(schema)` | `<T>(ZodSchema<T>) => StructuredFakeModel<T>` | Emulate withStructuredOutput |
| `.bindTools(tools)` | `(Tool[]) => this` | Bind tools (shares queue) |
| `callCount` | `number` | Number of `invoke()` calls made |
| `calls` | `{ messages: BaseMessage[], options?: any }[]` | Call log for assertions |

### Examples

```ts
import { fakeModel } from "langchain";
import { AIMessage, HumanMessage, SystemMessage } from "@langchain/core/messages";
import { z } from "zod";

// Queued responses
const m = fakeModel()
  .respond(new AIMessage("First"))
  .respond(new AIMessage("Second"));
await m.invoke([new HumanMessage("Hi")]);  // "First"

// Tool calling scenario
fakeModel()
  .respondWithTools([{ name: "get_weather", args: { city: "SF" }, id: "call-1" }])
  .respond(new AIMessage("It's 72°F in SF."));

// Dynamic callback
fakeModel().respond((msgs) => new AIMessage(`You said: ${msgs.at(-1)!.text}`));

// Error handling
fakeModel()
  .respond(new Error("Rate limit"))    // 1st call throws
  .respond(new AIMessage("Success!")); // 2nd succeeds

// Always throw
fakeModel().alwaysThrow(new Error("Unavailable"));

// Structured output
const structured = fakeModel()
  .structuredResponse({ temperature: 72, unit: "fahrenheit" })
  .withStructuredOutput(z.object({ temperature: z.number(), unit: z.string() }));

// Assertions
const m2 = fakeModel().respond(new AIMessage("Done"));
await m2.invoke([new SystemMessage("..."), new HumanMessage("Hi")]);
console.log(m2.callCount);           // 1
console.log(m2.calls[0].messages);   // [SystemMessage, HumanMessage]
```

---

## Provider Reference

### ChatOpenAI (`@langchain/openai`)

```bash
npm install @langchain/openai
export OPENAI_API_KEY="sk-..."
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `string` | required | `"gpt-4.1"`, `"gpt-4.1-mini"`, `"o1"` |
| `temperature` | `number` | `0` | Randomness (0–2) |
| `maxTokens` | `number` | — | Max output tokens |
| `stream` | `boolean` | `false` | Enable streaming |
| `streamUsage` | `boolean` | `true` | Include usage in stream chunks |
| `logprobs` | `boolean` | `false` | Return log probabilities |
| `topLogprobs` | `number` | — | Top logprobs per token |
| `useResponsesApi` | `boolean` | `false` | Use OpenAI Responses API |
| `modalities` | `("text" \| "audio")[]` | — | Output modalities |
| `audio` | `{ voice?, format? }` | — | Audio output config |
| `strict` | `boolean` | — | Strict tool schema (>= 0.2.6) |
| `configuration.baseURL` | `string` | — | Custom endpoint |
| `configuration.defaultHeaders` | `Record<string, string>` | — | Custom headers |

```ts
import { ChatOpenAI } from "@langchain/openai";

const llm = new ChatOpenAI({ model: "gpt-4.1", temperature: 0 });

// OpenAI Responses API with built-in web search
const llmSearch = new ChatOpenAI({ model: "gpt-4.1-mini", useResponsesApi: true })
  .bindTools([{ type: "web_search_preview" }]);

// Audio output
const audioModel = new ChatOpenAI({
  model: "gpt-4o-audio-preview",
  modalities: ["text", "audio"],
  audio: { voice: "alloy", format: "wav" },
});
```

### AzureChatOpenAI (`@langchain/openai`)

```ts
import { AzureChatOpenAI } from "@langchain/openai";
import { DefaultAzureCredential, getBearerTokenProvider } from "@azure/identity";

// Managed Identity — recommended for production
const llm = new AzureChatOpenAI({
  azureADTokenProvider: getBearerTokenProvider(
    new DefaultAzureCredential(),
    "https://cognitiveservices.azure.com/.default"
  ),
  azureOpenAIApiInstanceName: "<instance>",
  azureOpenAIApiDeploymentName: "<deployment>",
  azureOpenAIApiVersion: "2024-02-01",
});
// API-key auth: set azureOpenAIApiKey + AZURE_OPENAI_* env vars
```

### ChatAnthropic (`@langchain/anthropic`)

```bash
npm install @langchain/anthropic && export ANTHROPIC_API_KEY="sk-ant-..."
```

```ts
import { ChatAnthropic } from "@langchain/anthropic";

const llm = new ChatAnthropic({ model: "claude-haiku-4-5-20251001", temperature: 0 });

// Extended thinking
const llmThinking = new ChatAnthropic({
  model: "claude-sonnet-4-6",
  thinking: { type: "enabled", budget_tokens: 5000 },
});

// Prompt caching (beta)
const modelCaching = new ChatAnthropic({
  model: "claude-haiku-4-5-20251001",
  clientOptions: { defaultHeaders: { "anthropic-beta": "prompt-caching-2024-07-31" } },
});
```

**Constraints:** SystemMessage must be the very first message; cannot end with system or assistant.
**Model strings:** `"claude-sonnet-4-6"`, `"claude-haiku-4-5-20251001"`, `"claude-3-sonnet-20240229"`

### ChatGoogleGenerativeAI / ChatGoogle

```bash
npm install @langchain/google-genai   # or @langchain/google (recommended)
export GOOGLE_API_KEY="..."
```

```ts
import { ChatGoogleGenerativeAI } from "@langchain/google-genai";
// or: import { ChatGoogle } from "@langchain/google";  — unified + Vertex AI

const llm = new ChatGoogleGenerativeAI({ model: "gemini-2.5-pro", temperature: 0 });

// Built-in Google Search Retrieval
llm.bindTools([{ googleSearchRetrieval: { dynamicRetrievalConfig: { mode: "MODE_DYNAMIC", dynamicThreshold: 0.7 } } }]);

// Code execution
llm.bindTools([{ codeExecution: {} }]);
```

**Constraint:** System messages are merged into the first human message.
**Model strings:** `"gemini-2.5-pro"`, `"gemini-2.5-flash"`, `"gemini-2.5-flash-lite"`
**`@langchain/google` extras:** image generation, TTS, Vertex AI, Computer Use, MCP server tools.

### BedrockChat / ChatOllama / ChatGroq / ChatMistralAI / ChatCohere

```ts
// AWS Bedrock
import { BedrockChat } from "@langchain/community/chat_models/bedrock";
const llm = new BedrockChat({
  model: "anthropic.claude-3-5-sonnet-20240620-v1:0",
  region: process.env.BEDROCK_AWS_REGION,
  credentials: { accessKeyId: "...", secretAccessKey: "..." },
  modelKwargs: { anthropic_version: "bedrock-2023-05-31" },
});

// Ollama (local, http://127.0.0.1:11434 default)
import { ChatOllama } from "@langchain/ollama";
const llm = new ChatOllama({ model: "llama3", temperature: 0.7 });

// Groq — fast inference; supports JSON mode
import { ChatGroq } from "@langchain/groq";
const llm = new ChatGroq({ model: "llama-3.3-70b-versatile", temperature: 0 });
await llm.invoke(messages, { response_format: { type: "json_object" } });

// Mistral — messages must alternate human/assistant, cannot end with assistant
import { ChatMistralAI } from "@langchain/mistralai";
const llm = new ChatMistralAI({ model: "mistral-large-latest", temperature: 0 });

// Cohere — RAG document injection, web connectors
import { ChatCohere } from "@langchain/cohere";
const llm = new ChatCohere({ model: "command-r-plus", temperature: 0 });
await llm.invoke([new HumanMessage("Where did Harrison work?")], {
  documents: [{ title: "Work history", snippet: "Harrison worked at Kensho." }],
});
```

### OpenRouter (via ChatOpenAI)

No dedicated class. Use `ChatOpenAI` with custom `configuration`:

```ts
import { ChatOpenAI } from "@langchain/openai";

const createOpenRouterLLM = (modelName: string) => new ChatOpenAI({
  model: modelName,
  configuration: {
    baseURL: process.env.OPENROUTER_BASE_URL!, // https://openrouter.ai/api/v1
    apiKey: process.env.OPENROUTER_API_KEY!,
  },
});

const llama70 = createOpenRouterLLM("meta-llama/llama-3.3-70b-instruct");
const gemini  = createOpenRouterLLM("google/gemini-2.0-flash-001");
```

---

## Provider Comparison Table

| Provider | Class | Package | Streaming | Tool Calling | Structured Output | Multimodal | Logprobs | Prompt Caching |
|----------|-------|---------|-----------|--------------|-------------------|------------|----------|----------------|
| OpenAI | `ChatOpenAI` | `@langchain/openai` | ✅ | ✅ | ✅ | ✅ image, audio | ✅ | ✅ implicit + explicit |
| Anthropic | `ChatAnthropic` | `@langchain/anthropic` | ✅ | ✅ | ✅ | ✅ image | ✅ | ✅ beta header |
| Google | `ChatGoogle` | `@langchain/google` | ✅ | ✅ | ✅ | ✅ image, audio, video | — | ✅ |
| Google GenAI | `ChatGoogleGenerativeAI` | `@langchain/google-genai` | ✅ | ✅ | ✅ | ✅ image, audio, video | ✅ | ✅ |
| Azure OpenAI | `AzureChatOpenAI` | `@langchain/openai` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| AWS Bedrock | `BedrockChat` | `@langchain/community` | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ explicit |
| Bedrock Converse | `ChatBedrockConverse` | `@langchain/community` | ✅ | ✅ | ✅ | ✅ | — | — |
| Ollama | `ChatOllama` | `@langchain/ollama` | ✅ | ✅ | ✅ | ✅ model-dependent | ❌ | — |
| Groq | `ChatGroq` | `@langchain/groq` | ✅ | ✅ | ✅ | ❌ | ✅ | — |
| Mistral | `ChatMistralAI` | `@langchain/mistralai` | ✅ | ✅ | ✅ | ✅ | ❌ | — |
| Cohere | `ChatCohere` | `@langchain/cohere` | ✅ | ✅ | ✅ | ❌ | ❌ | — |
| Fireworks | `ChatFireworks` | `@langchain/community` | ✅ | ✅ | ✅ | ✅ | — | — |
| Together AI | `ChatTogetherAI` | `@langchain/community` | ✅ | ✅ | ✅ | — | — | — |
| xAI (Grok) | `ChatXAI` | `@langchain/xai` | ✅ | ✅ | ✅ | ❌ | — | — |
| Cloudflare | `ChatCloudflareWorkersAI` | `@langchain/cloudflare` | ✅ | ❌ | ❌ | ❌ | — | — |

**`initChatModel` provider prefix strings:**

| Provider | Prefix |
|----------|--------|
| OpenAI | `openai:` |
| Anthropic | `anthropic:` |
| Google GenAI | `google-genai:` |
| Azure OpenAI | `azure_openai:` |
| AWS Bedrock | `bedrock:` |
| Ollama | `ollama:` |
