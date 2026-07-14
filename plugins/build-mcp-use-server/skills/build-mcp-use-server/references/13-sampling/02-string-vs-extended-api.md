# String vs Extended Sampling API

`ctx.sample()` accepts either a string prompt or a full params object. Both shapes return the same `CreateMessageResult`.

## Decision matrix

| You need | Use |
|---|---|
| One user message, with optional controls | String API |
| System prompt / persona for one prompt | String API with `systemPrompt` option |
| Multi-turn message history | Extended API |
| Image / audio content (multimodal) | Extended API |
| `modelPreferences` for one prompt | String API with `modelPreferences` option |
| Plain classification or summarization | String API |

## String API

Simplest form — pass the prompt as the first arg, options second:

```typescript
const response = await ctx.sample(
  `Classify the sentiment as positive, negative, or neutral. One word.\n\nText: ${args.content}`,
  { maxTokens: 10, temperature: 0.0 }
);
return text(response.content.text.trim());
```

The string is wrapped internally as `[{ role: "user", content: { type: "text", text: prompt } }]`.
The second options object can also include `systemPrompt`, `modelPreferences`, `stopSequences`, and `metadata`.

### String API options

```typescript
const response = await ctx.sample(
  `Summarize in one sentence: ${args.content}`,
  {
    maxTokens: 100,
    temperature: 0.3,
    timeout: 30000,
    progressIntervalMs: 2000,
    onProgress: ({ message }) => console.log(message),
  }
);
```

## Extended API

Pass a params object with a `messages` array:

```typescript
const response = await ctx.sample({
  messages: [
    { role: "user", content: { type: "text", text: `Analyze: ${args.content}` } },
  ],
  systemPrompt: "You are an expert data analyst. Be concise.",
  maxTokens: 200,
  temperature: 0.2,
  modelPreferences: {
    intelligencePriority: 0.8,
    speedPriority: 0.5,
  },
});
return text(response.content.text);
```

Include `maxTokens` in the extended params object. The package type is `CreateMessageRequest["params"]`, where `maxTokens` is required.

### Multi-turn

```typescript
const response = await ctx.sample({
  messages: [
    { role: "user",      content: { type: "text", text: "What's 2+2?" } },
    { role: "assistant", content: { type: "text", text: "4" } },
    { role: "user",      content: { type: "text", text: "Multiply that by 3." } },
  ],
  maxTokens: 50,
});
```

### Multimodal (image content)

```typescript
const response = await ctx.sample({
  messages: [
    { role: "user", content: { type: "image", data: base64Png, mimeType: "image/png" } },
    { role: "user", content: { type: "text",  text: "Describe this image." } },
  ],
  maxTokens: 200,
});
```

## Combining classification then summary

A common shape — first sample for a label, then sample again with the label as context:

```typescript
const classification = await ctx.sample({
  messages: [
    { role: "user", content: { type: "text",
      text: `Classify into: technology, business, science, health. One word.\n\n${args.document}` } },
  ],
  maxTokens: 10,
  temperature: 0.0,
});
const category = classification.content.text.trim().toLowerCase();

const summary = await ctx.sample(
  `Summarize this ${category} document in 2-3 sentences:\n\n${args.document}`,
  { maxTokens: 150, temperature: 0.3 }
);

return object({
  category,
  summary: summary.content.text.trim(),
  model:   summary.model,
});
```

## Cost rule

Always set `maxTokens`. The string API defaults it to 1000, but extended sampling requires it in the params object. Cost guidance: `03-model-preferences.md`.
