# LLM Integration

MCPAgent works with any LangChain-compatible chat model. The LLM must support **tool calling** (function calling). Streaming and structured output support are optional but recommended.

## Explicit mode (LLM instance)

### OpenAI

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { MCPAgent, MCPClient } from "mcp-use";

const llm = new ChatOpenAI({
  model: "gpt-4o",
  temperature: 0.7,
  apiKey: process.env.OPENAI_API_KEY,
});

const agent = new MCPAgent({ llm, client });
```

Install: `npm install @langchain/openai`
Env var: `OPENAI_API_KEY`

### Anthropic

```typescript
import { ChatAnthropic } from "@langchain/anthropic";

const llm = new ChatAnthropic({
  model: "claude-sonnet-4-20250514",
  temperature: 0.7,
  apiKey: process.env.ANTHROPIC_API_KEY,
});

const agent = new MCPAgent({ llm, client });
```

Install: `npm install @langchain/anthropic`
Env var: `ANTHROPIC_API_KEY`

### Google Gemini

```typescript
import { ChatGoogleGenerativeAI } from "@langchain/google-genai";

const llm = new ChatGoogleGenerativeAI({
  model: "gemini-pro",
  temperature: 0.7,
  apiKey: process.env.GOOGLE_API_KEY,
});

const agent = new MCPAgent({ llm, client });
```

Install: `npm install @langchain/google-genai`
Env vars: `GOOGLE_API_KEY` or `GOOGLE_GENERATIVE_AI_API_KEY`

### Groq

```typescript
import { ChatGroq } from "@langchain/groq";

const llm = new ChatGroq({
  model: "llama-3.1-70b-versatile",
  temperature: 0.7,
  apiKey: process.env.GROQ_API_KEY,
});

const agent = new MCPAgent({ llm, client });
```

Install: `npm install @langchain/groq`
Env var: `GROQ_API_KEY`

## Simplified mode (string format)

Instead of manually creating the LLM, pass a `"provider/model"` string. The agent handles package import and instantiation:

```typescript
const agent = new MCPAgent({
  llm: "openai/gpt-4o",         // auto-creates ChatOpenAI
  mcpServers: { /* ... */ },
});
```

### Supported string formats

| String | Provider | Default model |
|--------|----------|---------------|
| `"openai/<model>"` | OpenAI | `gpt-4o` |
| `"anthropic/<model>"` | Anthropic | `claude-3-5-sonnet-20241022` |
| `"google/<model>"` | Google Gemini | `gemini-pro` |
| `"groq/<model>"` | Groq | `llama-3.1-70b-versatile` |

### With custom config

```typescript
const agent = new MCPAgent({
  llm: "anthropic/claude-3-5-sonnet-20241022",
  llmConfig: {
    temperature: 0.3,
    maxTokens: 4096,
    apiKey: "sk-ant-...",  // override env var
  },
  mcpServers: { /* ... */ },
});
```

## LLM requirements

| Feature | Required? | Purpose |
|---------|-----------|---------|
| Tool calling | **Yes** | MCP tool execution |
| Streaming | Optional | Real-time token output |
| Structured output | Optional | Zod schema validation |

## Provider package summary

```bash
# Install only what you need
npm install @langchain/openai      # for OpenAI models
npm install @langchain/anthropic   # for Claude models
npm install @langchain/google-genai # for Gemini models
npm install @langchain/groq        # for Groq models
```
