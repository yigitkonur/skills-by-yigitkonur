# LangChain.js Provider Reference

> Covers first-party and community provider packages, feature matrix, setup patterns, and known quirks.
> Research date: 2026-03-23. All examples are TypeScript.

---

## 1. Ecosystem Overview

LangChain.js organizes providers into two tiers:

**First-party** (`@langchain/<provider>`) — maintained by the LangChain team, stable APIs:
`@langchain/openai`, `@langchain/anthropic`, `@langchain/google`, `@langchain/google-genai`, `@langchain/google-vertexai`, `@langchain/aws`, `@langchain/ollama`, `@langchain/groq`, `@langchain/mistralai`, `@langchain/cohere`, `@langchain/xai`, `@langchain/deepseek`, `@langchain/cerebras`, `@langchain/openrouter`

**Community** (`@langchain/community`) — broader ecosystem, some providers live here:
Fireworks AI, Together AI, Perplexity, Novita AI, IBM watsonx.ai, Moonshot, ZhipuAI, Friendli, Deep Infra, Cloudflare Workers AI

All packages require `@langchain/core` as a peer dependency. LangChain v1 requires Node.js 20+.

---

## 2. Master Feature Matrix

| Provider | Package | Class | Env Var | Stream | Tools | Struct. Out | Vision | Embed |
|---|---|---|---|---|---|---|---|---|
| **OpenAI** | `@langchain/openai` | `ChatOpenAI` | `OPENAI_API_KEY` | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Anthropic** | `@langchain/anthropic` | `ChatAnthropic` | `ANTHROPIC_API_KEY` | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Google (new)** | `@langchain/google` | `ChatGoogle` | `GOOGLE_API_KEY` | ✅ | ✅ | ✅ | ✅ | — |
| **Google GenAI** | `@langchain/google-genai` | `ChatGoogleGenerativeAI` | `GOOGLE_API_KEY` | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Google Vertex** | `@langchain/google-vertexai` | `ChatVertexAI` | `GOOGLE_APPLICATION_CREDENTIALS` | ✅ | ✅ | ✅ | ✅ | — |
| **Azure OpenAI** | `@langchain/openai` | `AzureChatOpenAI` | `AZURE_OPENAI_API_KEY` + 3 more | ✅ | ✅ | ✅ | ✅ | ✅ |
| **AWS Bedrock** | `@langchain/aws` | `ChatBedrockConverse` | `BEDROCK_AWS_*` | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Ollama** | `@langchain/ollama` | `ChatOllama` | none (local) | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Groq** | `@langchain/groq` | `ChatGroq` | `GROQ_API_KEY` | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Cerebras** | `@langchain/cerebras` | `ChatCerebras` | `CEREBRAS_API_KEY` | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Mistral AI** | `@langchain/mistralai` | `ChatMistralAI` | `MISTRAL_API_KEY` | ✅ | ✅ | ✅ | ✅ (Pixtral) | ✅ |
| **Cohere** | `@langchain/cohere` | `ChatCohere` | `COHERE_API_KEY` | ✅ | ✅ | ✅ | ❌ | ✅ |
| **DeepSeek** | `@langchain/deepseek` | `ChatDeepSeek` | `DEEPSEEK_API_KEY` | ✅ | ✅* | ✅ | ✅ | ❌ |
| **xAI (Grok)** | `@langchain/xai` | `ChatXAI` | `XAI_API_KEY` | ✅ | ✅ | ✅ | ✅ | ❌ |
| **OpenRouter** | `@langchain/openrouter` | `ChatOpenRouter` | `OPENROUTER_API_KEY` | ✅ | ✅ | ✅ | model-dep | ❌ |
| **Fireworks AI** | `@langchain/community` | `ChatFireworks` | `FIREWORKS_API_KEY` | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Together AI** | `@langchain/community` | `ChatTogetherAI` | `TOGETHER_AI_API_KEY` | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Perplexity** | `@langchain/community` | `ChatPerplexity` | `PERPLEXITY_API_KEY` | ✅ | ❌ | ✅** | ❌ | ❌ |
| **Novita AI** | `@langchain/community` | `ChatNovitaAI` | `NOVITA_API_KEY` | ✅ | ❌ | ❌ | ❌ | ❌ |
| **IBM watsonx** | `@langchain/community` | `WatsonxLLM` | `WATSONX_AI_APIKEY` | ❌ | ❌ | ❌ | ❌ | — |
| **Moonshot** | `@langchain/community` | `ChatMoonshot` | `MOONSHOT_API_KEY` | — | — | — | — | — |
| **ZhipuAI** | `@langchain/community` | `ChatZhipuAI` | `ZHIPUAI_API_KEY` | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Friendli** | `@langchain/community` | `ChatFriendli` | `FRIENDLI_TOKEN` | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Cloudflare** | `@langchain/community` | `ChatCloudflareWorkersAI` | `CLOUDFLARE_API_TOKEN` | ✅ | ❌ | ❌ | ❌ | ✅ |

`*` DeepSeek tools not available for `deepseek-reasoner` model.
`**` Perplexity structured output is tier-dependent.

---

## 3. `initChatModel` Provider Prefix Reference

```ts
import { initChatModel } from "langchain";

const openai      = await initChatModel("openai:gpt-4.1",                            { temperature: 0 });
const anthropic   = await initChatModel("anthropic:claude-sonnet-4-6",               { temperature: 0 });
const google      = await initChatModel("google-genai:gemini-2.5-flash-lite");
const azure       = await initChatModel("azure_openai:gpt-4.1");       // needs AZURE_* env vars
const bedrock     = await initChatModel("bedrock:anthropic.claude-3-5-sonnet-20240620-v1:0");
const ollama      = await initChatModel("ollama:llama3",                             { baseUrl: "http://localhost:11434" });
const openrouter  = await initChatModel("openrouter:openai/gpt-4o");   // needs OPENROUTER_API_KEY
```

| Prefix | Provider | Required Env Vars |
|---|---|---|
| `openai:` | OpenAI | `OPENAI_API_KEY` |
| `anthropic:` | Anthropic | `ANTHROPIC_API_KEY` |
| `google-genai:` | Google GenAI | `GOOGLE_API_KEY` |
| `azure_openai:` | Azure OpenAI | `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `OPENAI_API_VERSION` |
| `bedrock:` | AWS Bedrock | `BEDROCK_AWS_REGION`, `BEDROCK_AWS_ACCESS_KEY_ID`, `BEDROCK_AWS_SECRET_ACCESS_KEY` |
| `ollama:` | Ollama | none (local) |
| `openrouter:` | OpenRouter | `OPENROUTER_API_KEY` |

---

## 4. Top-Tier Providers — Deep Reference

### 4.1 OpenAI

```ts
import { ChatOpenAI, OpenAIEmbeddings } from "@langchain/openai";
// npm install @langchain/openai @langchain/core

const llm = new ChatOpenAI({
  model: "gpt-4.1",
  temperature: 0,
  maxRetries: 2,
  configuration: {
    baseURL: "https://api.openai.com/v1",   // override for proxy / Azure routing
    defaultHeaders: { "X-Custom": "value" },
    timeout: 30000,
  },
  streamUsage: true,        // include usage in stream_options; disable for proxies
  logprobs: true,
  topLogprobs: 5,
  useResponsesApi: false,   // set true for built-in tools (web search, code interpreter, etc.)
  modalities: ["text", "audio"],
  audio: { voice: "alloy", format: "wav" },
  prediction: {             // predicted output for edit-task latency reduction
    type: "content",
    content: "...known output portion...",
  },
});

const embeddings = new OpenAIEmbeddings({
  model: "text-embedding-3-large",  // 3072-dim default
  dimensions: 1024,                  // reduce dimensions (optional)
  batchSize: 512,                    // max 2048
  configuration: { baseURL: "https://custom-endpoint.com/v1" },
});
```

**Model strings:** `"gpt-4.1"`, `"gpt-4.1-mini"`, `"gpt-4.1-nano"`, `"gpt-4o"`, `"gpt-4o-mini"`, `"o4-mini"`, `"o1"`, `"o3"`, `"gpt-5"`, `"gpt-5.1"`, `"computer-use-preview"`, `"codex-mini-latest"`, `"ft:gpt-3.5-turbo-0613:{ORG}::{MODEL_ID}"`

**Key features:**
- Prompt caching: automatic for prompts ≥1024 tokens; usage in `response_metadata.usage`
- Built-in tools via Responses API: web search, file search, code interpreter, computer use, remote MCP, image generation — activated by `useResponsesApi: true`
- Streaming audio: use `format: "pcm16"` for real-time audio streaming
- Predicted outputs: `prediction` constructor option reduces edit-task latency

---

### 4.2 Anthropic

```ts
import { ChatAnthropic } from "@langchain/anthropic";
// npm install @langchain/anthropic @langchain/core

const llm = new ChatAnthropic({
  model: "claude-sonnet-4-6",
  temperature: 0,
  maxTokens: 4096,
  maxRetries: 2,
  clientOptions: {
    defaultHeaders: {
      "anthropic-beta": "prompt-caching-2024-07-31",       // enable prompt caching
      // "anthropic-beta": "context-management-2025-06-27", // auto context window management
    },
  },
});

// Built-in tools
const llmWithTools = llm.bindTools([
  { type: "computer_20251124", name: "computer", display_width_px: 1024, display_height_px: 768, display_number: 1 },
  { type: "bash_20250124", name: "bash" },
  { type: "text_editor_20250728", name: "str_replace_based_edit_tool" },
  { type: "web_search_20250305", name: "web_search", max_uses: 5 },
]);
```

**Model strings:** `"claude-sonnet-4-6"`, `"claude-haiku-4-5-20251001"`, `"claude-3-opus-20240229"`, `"claude-3-sonnet-20240229"`, `"claude-3-haiku-20240307"`

**Key features:**
- No embeddings endpoint — use a different provider for embeddings
- System messages MUST be the first message in the prompt array
- Prompt caching: set `"anthropic-beta": "prompt-caching-2024-07-31"` header; mark tool defs with ephemeral `cache_control`
- Context management: `"anthropic-beta": "context-management-2025-06-27"` for automatic window management
- MCP toolset: `mcpToolset_20251120` built-in for connecting to MCP servers via OAuth
- Citations: document and search-result citation blocks in responses

---

### 4.3 Google

`@langchain/google` (Feb 2026+) is the new unified package. The older `@langchain/google-genai` and `@langchain/google-vertexai` are legacy but still widely used.

**New unified package (recommended):**
```ts
import { ChatGoogle } from "@langchain/google";
// npm install @langchain/google @langchain/core

const model = new ChatGoogle({
  model: "gemini-2.5-pro",
  temperature: 0,
  safetySettings: [],
  generationConfig: { maxOutputTokens: 2048 },
});
```

**Legacy GenAI (still widely used, has embeddings):**
```ts
import { ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings } from "@langchain/google-genai";
import { TaskType } from "@google/generative-ai";
// npm install @langchain/google-genai @langchain/core @google/generative-ai

const model = new ChatGoogleGenerativeAI({ model: "gemini-2.5-flash", temperature: 0 });

const embeddings = new GoogleGenerativeAIEmbeddings({
  model: "gemini-embedding-001",             // 768-dim
  taskType: TaskType.RETRIEVAL_DOCUMENT,
  title: "Optional document title",
});
```

**Legacy Vertex AI (enterprise/GCP):**
```ts
import { ChatVertexAI } from "@langchain/google-vertexai";
// npm install @langchain/google-vertexai @langchain/core
// Auth: GOOGLE_APPLICATION_CREDENTIALS (path to service account JSON)
//   or: GOOGLE_API_KEY (Express Mode)

const llm = new ChatVertexAI({
  model: "gemini-2.5-flash",
  location: "us-central1",
  cachedContent: "cachedContentId",   // context caching
});
```

**Model strings:** `"gemini-2.5-pro"`, `"gemini-2.5-flash"`, `"gemini-3.1-pro-preview"`, Gemma open models

**Key features:**
- Gemini 2.5 Pro supports reasoning / "thinking" mode
- Native tools: Google Search grounding, code execution, URL context, Google Maps, File Search, Computer Use, MCP servers
- Image generation and text-to-speech built-in
- Vertex AI: Google Search retrieval grounding, context caching via `cachedContent` ID, audio and video input

**Quirk — Gemini union type rejection:** Gemini rejects JSON schemas with union types (e.g., `string | null` in Zod). Use `.nullable()` carefully and test structured output schemas against Gemini before production deployment.

---

### 4.4 Azure OpenAI

```ts
import { AzureChatOpenAI, AzureOpenAIEmbeddings } from "@langchain/openai";
// npm install @langchain/openai @langchain/core
// Required env vars: AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_INSTANCE_NAME,
//                    AZURE_OPENAI_API_DEPLOYMENT_NAME, AZURE_OPENAI_API_VERSION

const llm = new AzureChatOpenAI({
  model: "gpt-4.1",
  temperature: 0,
  azureOpenAIApiKey: process.env.AZURE_OPENAI_API_KEY,
  azureOpenAIApiInstanceName: process.env.AZURE_OPENAI_API_INSTANCE_NAME,     // e.g. "my-resource"
  azureOpenAIApiDeploymentName: process.env.AZURE_OPENAI_API_DEPLOYMENT_NAME, // deployment name
  azureOpenAIApiVersion: process.env.AZURE_OPENAI_API_VERSION,                // e.g. "2024-02-01"
  azureADTokenProvider: tokenProvider,       // Managed Identity / Azure AD auth (optional)
  azureOpenAIBasePath: "https://custom-domain.openai.azure.com/", // custom domain (optional)
});
```

**Auth methods:**
1. API key via `AZURE_OPENAI_API_KEY` env var
2. Azure AD / Managed Identity via `azureADTokenProvider` constructor option

**`initChatModel` prefix:** `"azure_openai:gpt-4.1"` — requires `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `OPENAI_API_VERSION`

---

### 4.5 AWS Bedrock

`ChatBedrockConverse` is the recommended modern class. The legacy `Bedrock` class from `@langchain/community` has limited tool calling.

```ts
import { ChatBedrockConverse, BedrockEmbeddings } from "@langchain/aws";
// npm install @langchain/aws @langchain/core

const llm = new ChatBedrockConverse({
  model: "anthropic.claude-3-5-sonnet-20240620-v1:0",
  region: process.env.BEDROCK_AWS_REGION ?? "us-east-1",
  credentials: {
    accessKeyId: process.env.BEDROCK_AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.BEDROCK_AWS_SECRET_ACCESS_KEY!,
  },
  serviceTier: "standard",              // or "express"
  applicationInferenceProfile: "...",   // inference profile ARN (optional)
});

// API key auth (2025 simplification — eliminates Signature V4 complexity):
// Set AWS_BEARER_TOKEN_BEDROCK env var instead of access key credentials

const embeddings = new BedrockEmbeddings({
  region: process.env.BEDROCK_AWS_REGION!,
  credentials: {
    accessKeyId: process.env.BEDROCK_AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.BEDROCK_AWS_SECRET_ACCESS_KEY!,
  },
  model: "amazon.titan-embed-text-v1",  // default
});
```

**Bedrock model ID strings:**
- Anthropic: `"anthropic.claude-3-5-sonnet-20240620-v1:0"`, `"anthropic.claude-haiku-4-5-20251001-v1:0"`
- Amazon: `"amazon.titan-text-express-v1"`, `"amazon.nova-pro-v1:0"`
- Meta: `"meta.llama3-8b-instruct-v1:0"`
- Mistral: `"mistral.mistral-7b-instruct-v0:2"`

**`initChatModel` prefix:** `"bedrock:anthropic.claude-3-5-sonnet-20240620-v1:0"`

---

## 5. High-Performance Inference Providers

### 5.1 Groq

```ts
import { ChatGroq } from "@langchain/groq";
// npm install @langchain/groq @langchain/core

const llm = new ChatGroq({
  model: "llama-3.3-70b-versatile",
  temperature: 0,
  maxRetries: 2,
});
```

**Model strings:** `"llama-3.3-70b-versatile"`, `"llama-3.1-8b-instant"`, `"mixtral-8x7b-32768"`, `"gemma2-9b-it"`, `"deepseek-r1-distill-llama-70b"`

**Characteristic:** LPU hardware delivers 10–20x faster token generation than GPU-based providers. No vision or embeddings. Best for latency-sensitive applications.

---

### 5.2 Cerebras

```ts
import { ChatCerebras } from "@langchain/cerebras";
// npm install @langchain/cerebras @langchain/core

const llm = new ChatCerebras({
  model: "llama-3.3-70b",
  temperature: 0,
});
```

**Model strings:** `"llama-3.3-70b"`, `"llama-3.1-8b"`

**Characteristic:** Wafer-scale AI processor — ultra-fast inference for open-source models. No vision or embeddings.

---

## 6. Local Provider — Ollama

```ts
import { ChatOllama, OllamaEmbeddings } from "@langchain/ollama";
// npm install @langchain/ollama @langchain/core

const llm = new ChatOllama({
  model: "llama3",
  temperature: 0,
  baseUrl: "http://127.0.0.1:11434",   // default; change for remote Ollama
});

const embeddings = new OllamaEmbeddings({
  model: "mxbai-embed-large",          // default
  baseUrl: "http://localhost:11434",
  requestOptions: {
    useMmap: true,    // memory-map model weights
    numThread: 6,     // CPU threads
    numGpu: 1,        // GPU layers
  },
});
```

**Local setup:**
1. Download: https://ollama.ai/
2. Pull a model: `ollama pull llama3`
3. Server starts at `http://localhost:11434` — no API key needed

**Common model strings:** `"llama3"`, `"llama3.1"`, `"llama3.2"`, `"llava"`, `"mistral"`, `"qwen2.5"`, `"deepseek-r1"`, `"gemma3"`

**`initChatModel` prefix:** `"ollama:llama3"` (pass `baseUrl` option if non-default)

---

## 7. OpenRouter

First-party `@langchain/openrouter` package launched February 2026.

```ts
import { ChatOpenRouter } from "@langchain/openrouter";
// npm install @langchain/openrouter @langchain/core

const model = new ChatOpenRouter({
  model: "openai/gpt-4o",
  temperature: 0.8,
  // Routing options:
  models: ["openai/gpt-4o", "anthropic/claude-3-5-sonnet"],  // fallback list
  route: "fallback",
  provider: { allow_fallbacks: true },
  transforms: ["middle-out"],
});

// Legacy approach (still works — useful for providers not yet in @langchain/openrouter):
import { ChatOpenAI } from "@langchain/openai";
const legacyModel = new ChatOpenAI({
  model: "anthropic/claude-sonnet-4-6",
  configuration: {
    apiKey: process.env.OPENROUTER_API_KEY,
    baseURL: "https://openrouter.ai/api/v1",
  },
});
```

**Model strings (OpenRouter slugs):** `"openai/gpt-4o"`, `"anthropic/claude-sonnet-4-6"`, `"google/gemini-2.5-flash"`, `"meta-llama/llama-3.3-70b-instruct"`, `"deepseek/deepseek-r1"` (300+ models available)

**`initChatModel` prefix:** `"openrouter:openai/gpt-4o"`

**Trade-offs:** OpenRouter costs ~5% more than direct provider pricing. May route to an expensive fallback when cheaper providers are down instead of throwing an error. Best for: multi-model prototyping, model fallbacks, accessing region-restricted models.

---

## 8. Model-Specific Providers

### 8.1 Mistral AI

```ts
import { ChatMistralAI, MistralAIEmbeddings } from "@langchain/mistralai";
// npm install @langchain/mistralai @langchain/core

const llm = new ChatMistralAI({
  model: "mistral-large-latest",
  temperature: 0,
  // HTTP lifecycle hooks for logging / rate-limit handling:
  beforeRequestHooks: [(req) => { console.log("Before:", req); return req; }],
  requestErrorHooks: [(err) => { console.error("Error:", err); }],
  responseHooks: [(res) => { console.log("Response:", res); }],
});

const embeddings = new MistralAIEmbeddings({ model: "mistral-embed" });
```

**Model strings:** `"mistral-large-latest"`, `"mistral-small-latest"`, `"mistral-medium-latest"`, `"mistral-7b-instruct"`, `"mixtral-8x7b-instruct"`, `"pixtral-large-latest"` (vision)

---

### 8.2 Cohere

```ts
import { ChatCohere, CohereEmbeddings } from "@langchain/cohere";
// npm install @langchain/cohere @langchain/core

const llm = new ChatCohere({
  model: "command-r-plus",
  temperature: 0,
  apiKey: process.env.COHERE_API_KEY,
});

const embeddings = new CohereEmbeddings({
  model: "embed-english-v3.0",
  batchSize: 48,   // max 96
});
```

**Model strings:** `"command-r-plus"`, `"command-r"`, `"command"`, `"command-light"`, `"c4ai-aya-23"`

**Key feature:** RAG with web-search connector; `preamble` and `chatHistory` params for conversational context.

---

### 8.3 DeepSeek

```ts
import { ChatDeepSeek } from "@langchain/deepseek";
// npm install @langchain/deepseek @langchain/core

const llm = new ChatDeepSeek({
  model: "deepseek-chat",   // use deepseek-chat for agentic workflows
  temperature: 0,
});
```

**Model strings:** `"deepseek-chat"`, `"deepseek-reasoner"` (R1 reasoning), `"deepseek-coder"`

**Critical quirk:** `deepseek-reasoner` does NOT support tool calling or function calling. Use `deepseek-chat` for any agentic workflow that requires tools.

---

### 8.4 xAI (Grok)

```ts
import { ChatXAI } from "@langchain/xai";
// npm install @langchain/xai @langchain/core

const llm = new ChatXAI({
  model: "grok-3",
  temperature: 0,
});
```

**Model strings:** `"grok-beta"`, `"grok-2"`, `"grok-2-vision-1212"`, `"grok-3"`, `"grok-3-mini"`

---

## 9. Community Providers

### 9.1 Fireworks AI

```ts
import { ChatFireworks } from "@langchain/community/chat_models/fireworks";
// npm install @langchain/community @langchain/core

const llm = new ChatFireworks({
  model: "accounts/fireworks/models/llama-v3p1-70b-instruct",
  temperature: 0,
  maxRetries: 2,
});
```

**Model strings use Fireworks slugs:** `"accounts/fireworks/models/llama-v3p1-70b-instruct"`, `"accounts/fireworks/models/mistral-7b-instruct-v0p2"`, `"accounts/fireworks/models/deepseek-r1"`

---

### 9.2 Together AI

```ts
import { ChatTogetherAI } from "@langchain/community/chat_models/togetherai";
// npm install @langchain/community @langchain/core

const llm = new ChatTogetherAI({
  model: "mistralai/Mixtral-8x7B-Instruct-v0.1",
  temperature: 0,
});
```

**Model strings:** `"mistralai/Mixtral-8x7B-Instruct-v0.1"`, `"meta-llama/Meta-Llama-3.1-8B-Instruct"`, `"deepseek-ai/deepseek-r1"`, `"Qwen/Qwen2.5-72B-Instruct"`

**Notable:** The only community chat provider with full vision support (images + audio + video).

---

### 9.3 Perplexity

```ts
import { ChatPerplexity } from "@langchain/community/chat_models/perplexity";
// npm install @langchain/community @langchain/core

const llm = new ChatPerplexity({
  model: "sonar-pro",
  temperature: 0,
  maxRetries: 2,
});
```

**Model strings:** `"sonar"`, `"sonar-pro"`, `"sonar-reasoning"`, `"sonar-deep-research"`

**Key feature:** Web-search integrated into inference; citations returned in `additional_kwargs`. No tool calling.

---

### 9.4 Novita AI

```ts
import { ChatNovitaAI } from "@langchain/community/chat_models/novita";

const llm = new ChatNovitaAI({ model: "deepseek/deepseek-r1", temperature: 0 });
```

---

### 9.5 IBM watsonx.ai

```ts
import { WatsonxLLM } from "@langchain/community/llms/ibm";
// npm install @langchain/community @langchain/core

const llm = new WatsonxLLM({
  version: "2024-05-31",
  serviceUrl: process.env.WATSONX_AI_URL,
  projectId: "<PROJECT_ID>",
  watsonxAIAuthType: "iam",        // "iam" | "bearertoken" | "cp4d"
  watsonxAIApikey: process.env.WATSONX_AI_APIKEY,
  model: "ibm/granite-13b-instruct-v2",
  decoding_method: "sample",
  maxNewTokens: 100,
  temperature: 0.5,
});
```

**Auth env vars:** `WATSONX_AI_AUTH_TYPE` + `WATSONX_AI_APIKEY` (IAM) or `WATSONX_AI_BEARER_TOKEN` or `WATSONX_AI_USERNAME` + `WATSONX_AI_PASSWORD` + `WATSONX_AI_URL` (CP4D)

---

### 9.6 Regional / Niche Providers

```ts
// Moonshot (Kimi)
import { ChatMoonshot } from "@langchain/community/chat_models/moonshot";
const moonshot = new ChatMoonshot({
  apiKey: process.env.MOONSHOT_API_KEY,
  model: "moonshot-v1-128k",  // "moonshot-v1-8k" | "moonshot-v1-32k" | "moonshot-v1-128k"
});

// ZhipuAI (GLM) — requires: npm install jsonwebtoken
import { ChatZhipuAI } from "@langchain/community/chat_models/zhipuai";
const zhipu = new ChatZhipuAI({
  zhipuAIApiKey: process.env.ZHIPUAI_API_KEY,
  model: "glm-4",   // "glm-3-turbo" | "glm-4"
});

// Friendli
import { ChatFriendli } from "@langchain/community/chat_models/friendli";
const friendli = new ChatFriendli({
  model: "meta-llama-3-8b-instruct",
  friendliToken: process.env.FRIENDLI_TOKEN,
  friendliTeam: process.env.FRIENDLI_TEAM,
});
```

---

## 10. Embedding Models Reference

| Provider | Package | Class | Env Var | Default Model | Dimensions | Batch Size |
|---|---|---|---|---|---|---|
| **OpenAI** | `@langchain/openai` | `OpenAIEmbeddings` | `OPENAI_API_KEY` | `text-embedding-3-large` | 3072 (reducible) | 512 (max 2048) |
| **Google GenAI** | `@langchain/google-genai` | `GoogleGenerativeAIEmbeddings` | `GOOGLE_API_KEY` | `gemini-embedding-001` | 768 | — |
| **Cohere** | `@langchain/cohere` | `CohereEmbeddings` | `COHERE_API_KEY` | `embed-english-v3.0` | — | 48 (max 96) |
| **Mistral AI** | `@langchain/mistralai` | `MistralAIEmbeddings` | `MISTRAL_API_KEY` | `mistral-embed` | — | input array |
| **Ollama** | `@langchain/ollama` | `OllamaEmbeddings` | none | `mxbai-embed-large` | model-dep | — |
| **AWS Bedrock** | `@langchain/aws` | `BedrockEmbeddings` | `BEDROCK_AWS_*` | `amazon.titan-embed-text-v1` | model-dep | — |
| **Azure OpenAI** | `@langchain/openai` | `AzureOpenAIEmbeddings` | `AZURE_OPENAI_API_KEY` | deployment-dep | — | — |

---

## 11. Base URL / Proxy Configuration

Any OpenAI-compatible endpoint can be used with `ChatOpenAI`:

```ts
import { ChatOpenAI } from "@langchain/openai";

const model = new ChatOpenAI({
  model: "any-model-name",
  configuration: {
    apiKey: process.env.CUSTOM_API_KEY,
    baseURL: "https://your-proxy.example.com/v1",
  },
  streamUsage: false,   // disable if proxy doesn't support stream_options
});
```

**Compatible via this pattern:** LiteLLM proxy, local vLLM, local llama.cpp, Helicone, Portkey, any OpenAI-compatible API

---

## 12. Provider Switching Patterns and Pitfalls

**One-line swap via `initChatModel`:**
```ts
import { initChatModel } from "langchain";

// Change provider without touching any other code:
const model = await initChatModel(process.env.LLM_MODEL ?? "openai:gpt-4.1", {
  temperature: 0,
});
```

**Known pitfalls when switching providers mid-conversation:**
- Message format differences between providers can break agents (tool call format, message roles, content block structure)
- Switching models mid-conversation requires resetting conversation history or transforming message formats
- Some providers reject certain message sequences (e.g., Anthropic requires system messages first)

**Provider-specific structured output incompatibilities:**
- Gemini rejects JSON schemas with union types — test `.withStructuredOutput(schema)` schemas against each provider before deploying
- DeepSeek R1 (`deepseek-reasoner`) does not support tools at all — use `deepseek-chat` instead
- Perplexity structured output depends on subscription tier

---

## 13. Custom Provider Skeleton

```ts
import { BaseChatModel, BaseChatModelCallOptions } from "@langchain/core/language_models/chat_models";
import { BaseMessage, AIMessage } from "@langchain/core/messages";
import { ChatResult } from "@langchain/core/outputs";

class ChatMyProvider extends BaseChatModel {
  _llmType(): string {
    return "my-provider";
  }

  async _generate(
    messages: BaseMessage[],
    options: BaseChatModelCallOptions,
    runManager?: any
  ): Promise<ChatResult> {
    const response = await myProviderClient.chat(messages);
    return {
      generations: [{
        text: response.text,
        message: new AIMessage(response.text),
        generationInfo: {},
      }],
      llmOutput: { tokenUsage: response.usage },
    };
  }
}
```

---

## 14. Package Version Notes (Mar 2026)

- `@langchain/openai`: latest — supports `gpt-5.1`, `gpt-5.2`, Responses API
- `@langchain/anthropic`: latest — supports Claude Sonnet 4.6, all built-in tools
- `@langchain/google`: new unified package replacing `google-genai` + `google-vertexai` (Feb 2026)
- `@langchain/google-genai`: uses consolidated `@google/genai` SDK (v4.0.0+ changed from `@google/generative-ai`)
- `@langchain/aws`: v1.3.1 — `ChatBedrockConverse` recommended over legacy `Bedrock` class
- `@langchain/openrouter`: first-party package launched Feb 2026
- `@langchain/deepseek`: launched Nov 2024, supports DeepSeek-V3 and R1
- `@langchain/cerebras`: launched Aug 2024
