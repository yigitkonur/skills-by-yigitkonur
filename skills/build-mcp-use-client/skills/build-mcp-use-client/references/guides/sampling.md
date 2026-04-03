# Sampling

Complete reference for client-side sampling — handling server LLM completion requests via callbacks.

---

## What Is Sampling

Sampling is a callback mechanism where an MCP server requests an LLM completion from the client. The flow:

1. Client calls a tool on the server
2. Server needs LLM reasoning and sends a `CreateMessageRequest` back to the client
3. Client executes the LLM call using whatever model it has configured
4. Client returns a `CreateMessageResult` to the server
5. Server continues tool execution with the LLM response

The server never needs its own LLM — it borrows the client's.

---

## Type Definitions

### OnSamplingCallback

```typescript
import { type OnSamplingCallback } from "mcp-use";

const onSampling: OnSamplingCallback = async (
  params: CreateMessageRequestParams
): Promise<CreateMessageResult> => {
  // Process the request and return a result
};
```

### CreateMessageRequestParams

```typescript
interface CreateMessageRequestParams {
  messages: Array<{
    role: "user" | "assistant";
    content: {
      type: "text" | "image";
      text?: string;       // For text content
      data?: string;       // For image content (base64-encoded)
      mimeType?: string;   // For image content (e.g. "image/png")
    };
  }>;

  modelPreferences?: {
    hints?: Array<{ name?: string }>;
    costPriority?: number;            // 0.0 to 1.0
    speedPriority?: number;           // 0.0 to 1.0
    intelligencePriority?: number;    // 0.0 to 1.0
  };

  systemPrompt?: string;
  maxTokens?: number;
  temperature?: number;
  stopSequences?: string[];
  includeContext?: "none" | "thisServer" | "allServers";
  metadata?: Record<string, unknown>;
}
```

| Field | Type | Description |
|---|---|---|
| `messages` | `Array<SamplingMessage>` | Conversation messages to complete |
| `modelPreferences` | `object` | Hints for model selection (not binding) |
| `systemPrompt` | `string` | System prompt for the LLM |
| `maxTokens` | `number` | Maximum tokens in the response |
| `temperature` | `number` | Sampling temperature (0.0–1.0) |
| `stopSequences` | `string[]` | Sequences that stop generation |
| `includeContext` | `"none" \| "thisServer" \| "allServers"` | What context to include |
| `metadata` | `Record<string, unknown>` | Arbitrary metadata from the server |

### CreateMessageResult

```typescript
interface CreateMessageResult {
  role: "assistant";
  content: {
    type: "text" | "image";
    text?: string;       // For text content
    data?: string;       // For image content (base64)
    mimeType?: string;   // For image content
  };
  model: string;
  stopReason?: "endTurn" | "maxTokens" | "stopSequence";
}
```

| Field | Type | Description |
|---|---|---|
| `role` | `"assistant"` | Always `"assistant"` |
| `content` | `object` | Response content (text or image) |
| `model` | `string` | The model that generated the response |
| `stopReason` | `string` | Why generation stopped |

---

## Setting the Global Sampling Callback

Pass `onSampling` as part of the second argument to `MCPClient`. The same options object also accepts `onElicitation` and `onNotification` if needed:

```typescript
import { MCPClient, type OnSamplingCallback } from "mcp-use";

const onSampling: OnSamplingCallback = async (params) => {
  const lastMessage = params.messages?.[params.messages.length - 1];
  const text =
    typeof lastMessage?.content === "object" && lastMessage?.content && "text" in lastMessage.content
      ? (lastMessage.content as { text?: string }).text
      : "";

  return {
    role: "assistant",
    content: { type: "text", text: (await yourLLM.complete(text)) ?? "" },
    model: "your-model",
    stopReason: "endTurn",
  };
};

const client = new MCPClient(
  { mcpServers: { myServer: { url: "http://localhost:3000/mcp" } } },
  { onSampling }
);
```

---

## Per-Server Sampling Callbacks

Override the global callback for individual servers by setting `onSampling` inside the server config entry:

```typescript
import { MCPClient, type OnSamplingCallback } from "mcp-use";

const claudeSampling: OnSamplingCallback = async (params) => {
  const response = await anthropic.messages.create({
    model: "claude-sonnet-4-20250514",
    max_tokens: params.maxTokens ?? 1024,
    system: params.systemPrompt ?? "",
    messages: params.messages.map((m) => ({
      role: m.role,
      content: typeof m.content === "string" ? m.content : m.content.text ?? "",
    })),
  });
  return {
    role: "assistant",
    content: { type: "text", text: response.content[0].text },
    model: "claude-sonnet-4-20250514",
    stopReason: "endTurn",
  };
};

const gptSampling: OnSamplingCallback = async (params) => {
  const response = await openai.chat.completions.create({
    model: "gpt-4o",
    max_tokens: params.maxTokens ?? 1024,
    messages: [
      ...(params.systemPrompt ? [{ role: "system" as const, content: params.systemPrompt }] : []),
      ...params.messages.map((m) => ({
        role: m.role as "user" | "assistant",
        content: typeof m.content === "string" ? m.content : m.content.text ?? "",
      })),
    ],
  });
  return {
    role: "assistant",
    content: { type: "text", text: response.choices[0].message.content ?? "" },
    model: "gpt-4o",
    stopReason: "endTurn",
  };
};

const fallbackSampling: OnSamplingCallback = async (params) => {
  return {
    role: "assistant",
    content: { type: "text", text: "Sampling not configured for this server." },
    model: "fallback",
    stopReason: "endTurn",
  };
};

const client = new MCPClient(
  {
    mcpServers: {
      codeServer: {
        url: "https://code.example.com/mcp",
        onSampling: claudeSampling,     // Uses Claude
      },
      creativeServer: {
        url: "https://creative.example.com/mcp",
        onSampling: gptSampling,        // Uses GPT-4o
      },
      utilityServer: {
        url: "https://util.example.com/mcp",
        // No callback — uses the global fallback
      },
    },
  },
  { onSampling: fallbackSampling }
);
```

---

## Callback Precedence Order

| Priority | Source | Example |
|---|---|---|
| 1 (highest) | Per-server `onSampling` | `mcpServers.myServer.onSampling` |
| 2 | Per-server `samplingCallback` (deprecated — use `onSampling`) | `mcpServers.myServer.samplingCallback` |
| 3 | Global `onSampling` | `new MCPClient(config, { onSampling })` |
| 4 (lowest) | Global `samplingCallback` (deprecated — use `onSampling`) | `new MCPClient(config, { samplingCallback })` |

If no callback matches, the server's sampling request fails.

---

## Model Preference Handling

The server sends `modelPreferences` as hints. The client is free to ignore them, but should respect them when possible.

```typescript
const onSampling: OnSamplingCallback = async (params) => {
  let model = "gpt-4o-mini"; // default

  // 1. Check explicit model hints first
  if (params.modelPreferences?.hints?.[0]?.name) {
    model = params.modelPreferences.hints[0].name;
  }
  // 2. Fall back to priority-based selection
  else if ((params.modelPreferences?.intelligencePriority ?? 0) > 0.8) {
    model = "gpt-4o";
  } else if ((params.modelPreferences?.speedPriority ?? 0) > 0.8) {
    model = "gpt-4o-mini";
  } else if ((params.modelPreferences?.costPriority ?? 0) > 0.8) {
    model = "gpt-4o-mini";
  }

  const response = await openai.chat.completions.create({
    model,
    max_tokens: params.maxTokens ?? 1024,
    temperature: params.temperature,
    stop: params.stopSequences,
    messages: [
      ...(params.systemPrompt ? [{ role: "system" as const, content: params.systemPrompt }] : []),
      ...params.messages.map((m) => ({
        role: m.role as "user" | "assistant",
        content: typeof m.content === "string" ? m.content : m.content.text ?? "",
      })),
    ],
  });

  return {
    role: "assistant",
    content: { type: "text", text: response.choices[0].message.content ?? "" },
    model,
    stopReason: "endTurn",
  };
};
```

| Preference Field | Type | Meaning |
|---|---|---|
| `hints` | `Array<{ name?: string }>` | Explicit model name suggestions |
| `costPriority` | `number` (0–1) | Higher = prefer cheaper models |
| `speedPriority` | `number` (0–1) | Higher = prefer faster models |
| `intelligencePriority` | `number` (0–1) | Higher = prefer smarter models |

---

## Image Content in Sampling

Servers can send image content for multimodal LLM processing:

```typescript
const onSampling: OnSamplingCallback = async (params) => {
  const messages = params.messages.map((m) => {
    if (m.content.type === "image" && m.content.data && m.content.mimeType) {
      return {
        role: m.role,
        content: [
          {
            type: "image_url" as const,
            image_url: { url: `data:${m.content.mimeType};base64,${m.content.data}` },
          },
        ],
      };
    }
    return {
      role: m.role,
      content: m.content.text ?? "",
    };
  });

  const response = await openai.chat.completions.create({
    model: "gpt-4o",
    messages: messages as any,
    max_tokens: params.maxTokens ?? 1024,
  });

  return {
    role: "assistant",
    content: { type: "text", text: response.choices[0].message.content ?? "" },
    model: "gpt-4o",
    stopReason: "endTurn",
  };
};
```

---

## Integration with Real LLMs

### OpenAI Pattern

```typescript
import OpenAI from "openai";
import { MCPClient, type OnSamplingCallback } from "mcp-use";

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

const onSampling: OnSamplingCallback = async (params) => {
  const response = await openai.chat.completions.create({
    model: "gpt-4o",
    max_tokens: params.maxTokens ?? 1024,
    temperature: params.temperature,
    stop: params.stopSequences,
    messages: [
      ...(params.systemPrompt ? [{ role: "system" as const, content: params.systemPrompt }] : []),
      ...params.messages.map((m) => ({
        role: m.role as "user" | "assistant",
        content: typeof m.content === "string" ? m.content : m.content.text ?? "",
      })),
    ],
  });

  return {
    role: "assistant",
    content: { type: "text", text: response.choices[0].message.content ?? "" },
    model: response.model,
    stopReason: "endTurn",
  };
};
```

### Anthropic Pattern

```typescript
import Anthropic from "@anthropic-ai/sdk";
import { MCPClient, type OnSamplingCallback } from "mcp-use";

const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

const onSampling: OnSamplingCallback = async (params) => {
  const response = await anthropic.messages.create({
    model: "claude-sonnet-4-20250514",
    max_tokens: params.maxTokens ?? 1024,
    temperature: params.temperature,
    system: params.systemPrompt ?? "",
    stop_sequences: params.stopSequences,
    messages: params.messages.map((m) => ({
      role: m.role,
      content: typeof m.content === "string" ? m.content : m.content.text ?? "",
    })),
  });

  return {
    role: "assistant",
    content: { type: "text", text: response.content[0].type === "text" ? response.content[0].text : "" },
    model: response.model,
    stopReason: "endTurn",
  };
};
```

---

## React Hook Sampling

### useMcp with onSampling

```typescript
import { useMcp } from "mcp-use/react";

function ChatComponent() {
  const mcp = useMcp({
    url: "http://localhost:3000/mcp",
    onSampling: async (params) => {
      const response = await fetch("/api/llm", {
        method: "POST",
        body: JSON.stringify(params),
      });
      return response.json();
    },
  });

  if (mcp.state !== "ready") return <div>Connecting...</div>;
  return <div>{mcp.tools.length} tools available</div>;
}
```

### McpClientProvider with onSamplingRequest

```typescript
import { McpClientProvider, useMcpServer } from "mcp-use/react";

function App() {
  return (
    <McpClientProvider
      onSamplingRequest={(request, serverId, serverName, approve, reject) => {
        // Show approval UI, then:
        approve({
          role: "assistant",
          content: { type: "text", text: "Approved response" },
          model: "gpt-4o",
        });
        // Or reject:
        // reject();
      }}
    >
      <MyApp />
    </McpClientProvider>
  );
}
```

---

## Error Handling

```typescript
const onSampling: OnSamplingCallback = async (params) => {
  try {
    const response = await openai.chat.completions.create({ /* ... */ });
    return {
      role: "assistant",
      content: { type: "text", text: response.choices[0].message.content ?? "" },
      model: response.model,
      stopReason: "endTurn",
    };
  } catch (error) {
    // Return an error message as text — do not throw
    return {
      role: "assistant",
      content: {
        type: "text",
        text: `LLM call failed: ${error instanceof Error ? error.message : String(error)}`,
      },
      model: "error",
      stopReason: "endTurn",
    };
  }
};
```

❌ **BAD** — Throwing from the callback crashes the tool execution:

```typescript
const onSampling: OnSamplingCallback = async (params) => {
  const response = await openai.chat.completions.create({ /* ... */ });
  // No error handling — exceptions propagate and break the server
  return { role: "assistant", content: { type: "text", text: response.choices[0].message.content ?? "" }, model: "gpt-4o", stopReason: "endTurn" };
};
```

✅ **GOOD** — Wrap in try/catch and return a graceful error result:

```typescript
const onSampling: OnSamplingCallback = async (params) => {
  try {
    const response = await openai.chat.completions.create({ /* ... */ });
    return {
      role: "assistant",
      content: { type: "text", text: response.choices[0].message.content ?? "" },
      model: response.model,
      stopReason: "endTurn",
    };
  } catch (error) {
    return {
      role: "assistant",
      content: { type: "text", text: `Error: ${error instanceof Error ? error.message : "Unknown"}` },
      model: "error",
      stopReason: "endTurn",
    };
  }
};
```

---

## Available Imports

```typescript
// Core client and callback types
import {
  MCPClient,
  type OnSamplingCallback,
  type OnElicitationCallback,
  type OnNotificationCallback,
} from "mcp-use";

// Sampling-specific types (re-exported from mcp-use)
import type {
  CreateMessageRequestParams,
  CreateMessageResult,
} from "mcp-use";

// Browser client
import { MCPClient } from "mcp-use/browser";

// React hooks
import { useMcp, McpClientProvider, useMcpClient, useMcpServer } from "mcp-use/react";
```

---

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| No callback registered | Server sampling request fails silently | Always set at least a global `onSampling` |
| Throwing errors from callback | Crashes the entire tool execution | Wrap in try/catch, return error as text |
| Ignoring `modelPreferences` | Server's model hints wasted | Check `hints`, then priority fields |
| Hardcoding a single model | No flexibility across server needs | Use preference-based model selection |
| No `maxTokens` in LLM call | Unbounded token usage | Forward `params.maxTokens` or set a default |
| Blocking callback with slow I/O | Tool execution hangs | Set timeouts on LLM API calls |
