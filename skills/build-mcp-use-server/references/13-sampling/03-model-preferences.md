# Model Preferences

`modelPreferences` is a hint to the client about which model to use. It is available in string API options and extended sampling params. The client may honor it or ignore it — your server should never assume a specific model is selected.

```typescript
const response = await ctx.sample({
  messages: [/* ... */],
  maxTokens: 200,
  modelPreferences: {
    speedPriority: 0.8,
    costPriority: 0.4,
    intelligencePriority: 0.5,
    hints: [{ name: "claude-3-5-sonnet" }],
  },
});
```

## The three priority axes

Each value is `0.0` (don't care) to `1.0` (strong preference). They are hints, not weights — clients may interpret them differently.

| Priority | Meaning | Good for |
|---|---|---|
| `speedPriority` | Prefer faster models | Lightweight classification, short summaries, real-time UX |
| `costPriority` | Prefer cheaper models | High-volume calls, batch reprocessing |
| `intelligencePriority` | Prefer smarter / larger models | Nuanced extraction, complex reasoning, long context |

Set the axes you actually care about. Leave an axis off when you do not have a preference; the client decides how to interpret missing values.

## Common profiles

| Profile | speedPriority | costPriority | intelligencePriority | Use for |
|---|---|---|---|---|
| Cheap classifier | 0.7 | 0.9 | 0.2 | Sentiment, intent, short labels |
| Fast summarizer | 0.8 | 0.5 | 0.5 | Inline summaries, headlines |
| Quality extractor | 0.2 | 0.2 | 0.9 | JSON extraction, schema-constrained generation |
| Balanced default | 0.5 | 0.5 | 0.5 | Most production tools |

## Model name hints

If your tool genuinely requires a specific model family (e.g. one with vision, or a known long-context window), pass `hints`:

```typescript
modelPreferences: {
  hints: [
    { name: "claude-3-5-sonnet" },
    { name: "claude-3-opus" },
  ],
}
```

Hints are advisory. The client decides what to honor based on user configuration and availability. Never branch logic on `response.model` matching a specific hint.

## How clients honor preferences

| Client behavior | What you can rely on |
|---|---|
| User has only one model configured | Preferences ignored — that model is used |
| Client supports preference routing | Preferences map to its model selection logic |
| Client lets the user override | User choice wins |
| Client tier-routes (free/paid) | `costPriority` may downgrade quality |

The actual model used is in `response.model` — log this if you need to attribute cost or behavior.

## Anti-pattern: branching on `response.model`

Clients don't guarantee a specific model. If your logic needs different post-processing per model, restructure the prompt instead of switching on the model name.

```typescript
// BAD
const r = await ctx.sample({ messages, maxTokens: 100, modelPreferences: { hints: [{ name: "gpt-4o" }] } });
if (r.model.includes("gpt-4o")) { /* ... */ } else { /* ... */ }

// GOOD — phrase the prompt so any model produces the right shape
const r = await ctx.sample({
  messages,
  systemPrompt: "Output strictly JSON: { label: string, confidence: number }.",
  maxTokens: 100,
  temperature: 0.0,
});
const parsed = JSON.parse(r.content.text);
```

## Combining with `temperature` and `maxTokens`

`modelPreferences` hints at model choice. `temperature` and `maxTokens` shape the output. Tune all three together:

```typescript
// Cheap, deterministic label
{ maxTokens: 5,   temperature: 0.0, modelPreferences: { costPriority: 0.9, intelligencePriority: 0.2 } }

// High-quality, creative draft
{ maxTokens: 800, temperature: 0.7, modelPreferences: { intelligencePriority: 0.9 } }
```
