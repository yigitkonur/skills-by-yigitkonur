# Sampling Overview

`ctx.sample()` lets a tool request an LLM completion from the **client's** model. Your server doesn't need its own model key — it borrows whatever the connected client has configured.

Use for bounded reasoning tasks during a tool call: classification, summarization, extraction, lightweight rewriting.

## Required capability gate

Sampling is opt-in per client. Always guard:

```typescript
import { error } from "mcp-use/server";

if (!ctx.client.can("sampling")) {
  return error("This client does not support sampling.");
}
```

`ctx.client.*` API is documented in `../16-client-introspection/03-can-capabilities.md`.

## Two API shapes

| Shape | Signature | Use when |
|---|---|---|
| **String** | `ctx.sample(prompt, options?)` | One user message, with optional controls |
| **Extended** | `ctx.sample({ messages, maxTokens, ... }, options?)` | Multi-turn, multimodal, or explicit message arrays |

Both return the same `CreateMessageResult` shape. Details: `02-string-vs-extended-api.md`.

## Minimal example

```typescript
import { MCPServer, text, error } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({ name: "analyzer", version: "1.0.0" });

server.tool(
  {
    name: "analyze-sentiment",
    description: "Classify sentiment of provided text.",
    schema: z.object({ content: z.string().describe("Text to analyze") }),
  },
  async (args, ctx) => {
    if (!ctx.client.can("sampling")) return error("Sampling not supported.");

    const response = await ctx.sample(
      `Classify the sentiment as positive, negative, or neutral. One word only.\n\nText: ${args.content}`,
      { maxTokens: 10, temperature: 0.0 }
    );
    return text(`Sentiment: ${response.content.text.trim()}`);
  }
);
```

## Response shape

```typescript
interface CreateMessageResult {
  role: "user" | "assistant";
  content: {
    type: "text" | "image" | "audio";
    text?: string;
    data?: string;
    mimeType?: string;
  };
  model: string;                                          // Actual model used
  stopReason?: "endTurn" | "maxTokens" | "stopSequence" | string;
}
```

`content` is a **single object**, not an array. Read text directly via `response.content.text`, or guard with optional chaining:

```typescript
const text = response.content?.text?.trim() ?? "";
if (!text) return error("Model returned empty response.");
```

## Where each section lives

| Topic | File |
|---|---|
| String vs extended API choice | `02-string-vs-extended-api.md` |
| `modelPreferences` (speed / cost / intelligence) | `03-model-preferences.md` |
| `onProgress`, callbacks, streaming | `04-callbacks.md` |
| Auto-progress notifications during long samples | `05-progress-during-sampling.md` |

## Common parameters

| Parameter | Type | Default | Purpose |
|---|---|---|---|
| `maxTokens` | `number` | `1000` for string API | Cap output length; required in extended params |
| `temperature` | `number` | provider default | 0.0–1.0 sampling temperature |
| `systemPrompt` | `string` | — | Set LLM behavior/persona |
| `modelPreferences` | `object` | — | Hint at model choice (`03-model-preferences.md`) |
| `timeout` | `number` | no timeout | Milliseconds before reject; pass in the second options arg |
| `progressIntervalMs` | `number` | `5000` | Auto-progress interval when a progress token is present |
| `onProgress` | `function` | — | Callback for emitted progress events |

## Related

- Elicitation (asking the user, not the LLM): `../12-elicitation/01-overview.md`
- Notifications and progress tokens: `../14-notifications/03-progress-tokens.md`

**Canonical doc:** https://manufact.com/docs/typescript/server/sampling
