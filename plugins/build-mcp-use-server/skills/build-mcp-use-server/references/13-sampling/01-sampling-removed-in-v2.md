# Sampling Removed in v2

*Read this if you have v1 code using `ctx.sample()` and are migrating to v2.*

Server-side sampling (`ctx.sample()`) has been **removed** from mcp-use v2. The boundary has shifted: the **model generates first**, then calls deterministic tools with the results. A deprecated legacy-interop path (`inputRequired.createMessage()`) still exists for bridging old sampling-based integrations — see "No `ctx.sample()` — but a deprecated compatibility path exists" below — but it is not the v2 design pattern.

## Why it was removed

v2 is stateless: HTTP requests cannot pause to await host LLM generation. Giving the server control over when and how to generate LLM responses breaks the request-per-exchange model.

**Architectural shift:**
- **v1:** Server calls `ctx.sample()` → client LLM generates → server gets result → server continues
- **v2:** Client/model generates → calls server tool with result → server validates and returns

## Migration pattern: host generates first

Replace server-side sampling with this flow:

1. **Prompt description** guides the model on what to generate
2. **Model generates** using its own credentials and compute
3. **Model calls your tool** with the generated result
4. **Tool validates** input (Zod schema enforces constraints)
5. **Tool performs** deterministic work

Example: sentiment classification

**v1 (server-side sampling):**
```typescript
// REMOVED — NOT AVAILABLE IN v2
// const result = await ctx.sample(
//   `Classify as positive/negative/neutral: ${text}`,
//   { maxTokens: 10 }
// );
```

**v2 (host-first generation):**
```typescript
export const classifySentiment = server.tool(
  {
    name: "classify-sentiment",
    description: "Classify text sentiment as positive, negative, or neutral. One word only.",
    inputSchema: z.object({
      text: z.string().describe("Text to analyze"),
      sentiment: z.enum(["positive", "negative", "neutral"]).describe("Classification"),
    }),
    outputSchema: z.object({
      sentiment: z.enum(["positive", "negative", "neutral"]),
      confidence: z.number().min(0).max(1),
    }),
  },
  async ({ text, sentiment }, ctx) => {
    // Model has already done the classification; we validate and score
    const confidence = calculateConfidence(text, sentiment);
    return {
      content: [{ type: "text", text: `Classified as ${sentiment}` }],
      structuredContent: { sentiment, confidence },
    };
  }
);
```

The **tool description** acts as the prompt: "Classify text sentiment as positive, negative, or neutral."

The **inputSchema** enforces that the model must provide a choice — not freeform text.

## When to use multi-step host generation

For complex reasoning, break it into multiple tool calls:

```typescript
// Step 1: Tool to extract entities
export const extractEntities = server.tool({
  name: "extract-entities",
  description: "Extract named entities (person, org, location) from text.",
  inputSchema: z.object({
    text: z.string(),
    entities: z.array(z.object({
      name: z.string(),
      type: z.enum(["person", "org", "location"]),
    })),
  }),
  // ...
});

// Step 2: Tool to classify entities
export const classifyEntities = server.tool({
  name: "classify-entities",
  description: "Classify extracted entities by sentiment and importance.",
  inputSchema: z.object({
    entities: z.array(z.object({ name: z.string(), type: z.string(), importance: z.enum(["high", "medium", "low"]) })),
  }),
  // ...
});
```

The model chains them: call extract → call classify → return to user.

## No `ctx.sample()` — but a deprecated compatibility path exists

There is no `ctx.sample()` and no dedicated "sampling" input-required helper family for the primary v2 pattern above — this is the pattern to design new tools around. Server-initiated sampling is genuinely gone as an ergonomic, first-class API.

A narrower, deprecated compatibility path does still exist for legacy interop: a sessionless server can request sampling through the same `input_required` multi-round-trip mechanism elicitation uses, via `inputRequired.createMessage({ messages, maxTokens, ... })`. The client answers through the `onSampling` callback (see the client-side `sampling.mdx` doc: "A sessionless server enters the temporary `input_required` multi-round-trip compatibility flow"), and the server reads the result with `inputResponse(ctx.inputResponses, key)`, checking `.kind === "sampling"` and reading `.result`:

```typescript
import { inputRequired, inputResponse } from "mcp-use";

if (!ctx.client.can("sampling")) {
  return {
    isError: true,
    content: [{ type: "text", text: "Client does not support sampling/createMessage." }],
  };
}

const response = inputResponse(ctx.inputResponses, "sample");
if (response.kind === "missing") {
  return inputRequired({
    inputRequests: {
      sample: inputRequired.createMessage({
        messages: [{ role: "user", content: { type: "text", text: prompt } }],
        maxTokens: 100,
      }),
    },
  });
}
if (response.kind === "sampling") {
  const blocks = Array.isArray(response.result.content) ? response.result.content : [response.result.content];
  // ... consume the generated content
}
```

Treat this as a legacy interop path for clients that only understand the old `sampling/createMessage` shape, not as the recommended v2 design. Prefer the host-generates-first pattern above for new tools; reach for `inputRequired.createMessage()` only when you must bridge an existing sampling-based integration.

Client capability advertisement follows the same legacy boundary: `sampling/createMessage` is available only when the current request advertises the top-level `sampling` capability. Gate `inputRequired.createMessage()` with `ctx.client.can("sampling")`; elicitation support does not imply sampling support. The mcp-use client advertises `sampling: {}` only when an `onSampling` callback is configured.

If you need to offer a calculation that *looks* like sampling to users without legacy interop constraints, use elicitation instead: ask the user for their preference, then perform the work.

## Full migration guide

For all v1→v2 changes, see `../28-migration/02-v1-to-v2-overview.md`.

## Related

- Elicitation (interactive user prompts): `../12-elicitation/01-overview.md`
- Tool design with constraints: `../04-tools/02-registering-a-tool.md`
- Production patterns: `../24-production/02-error-strategy.md`
