# Sampling Callbacks

`ctx.sample()` is a single-await call — it resolves once with the full message. There is no token-stream API exposed to the tool handler. What you *can* observe during the wait is **progress** via `onProgress` when the tool call includes a progress token.

## `onProgress` callback

```typescript
const response = await ctx.sample(
  "Classify this changelog: ...",
  {
    maxTokens: 64,
    timeout: 120000,
    progressIntervalMs: 2000,
    onProgress: ({ message }) => {
      console.log(`[Sampling] ${message}`);
    },
  }
);
```

| Option | Type | Default | Purpose |
|---|---|---|---|
| `progressIntervalMs` | `number` | `5000` | How often progress events fire |
| `onProgress` | `({ progress, total, message }) => void` | — | Custom handler for each event |

## What progress events contain

The callback receives `{ progress: number, total?: number, message: string }`. mcp-use generates these automatically while waiting for the client response; the runtime message is currently shaped like `"Waiting for LLM response... (5s elapsed)"`.

Progress callbacks are tied to the same progress-token path as client-facing `notifications/progress`. If the incoming tool call has no progress token, sampling still works but no progress callback is scheduled.

You don't get token deltas. If your UI needs streaming text, sample into a buffer and re-render on completion, or split the work into multiple shorter samples.

## Why use `onProgress`

| Reason | What it gives you |
|---|---|
| Server-side logging during long samples | Insight into where the call is stuck |
| Forwarding to your own observability layer | Correlate sample stages with traces |
| Driving in-process status indicators | Useful in dev or admin UIs |

For client-facing progress (the connected MCP client UI), the framework also emits `notifications/progress` automatically — see `05-progress-during-sampling.md`.

## Error and timeout handling

Sampling can reject for several reasons. Wrap in `try/catch`:

```typescript
try {
  const response = await ctx.sample(prompt, { maxTokens: 200, timeout: 30000 });
  const summaryText = response.content?.text?.trim() ?? "";
  if (!summaryText) return error("Model returned an empty response.");
  return object({ summary: summaryText, model: response.model });
} catch (err) {
  return error(`Sampling failed: ${err instanceof Error ? err.message : String(err)}`);
}
```

Common rejection causes:

| Cause | Detect by |
|---|---|
| Client doesn't support sampling | Pre-check with `ctx.client.can("sampling")` |
| Timeout exceeded | Error message contains "timeout" / `timeout` option hit |
| Client cancelled (user closed conversation) | `AbortError`-shaped message |
| Provider rate limit / quota | Error from upstream provider, surfaces verbatim |

## Empty / partial result handling

`response.content.text` can be empty or whitespace if `maxTokens` was too small or the model declined. Always normalize before passing to business logic:

```typescript
const text = response.content?.text?.trim() ?? "";
if (!text) return error("Empty model response.");
```

## Indeterminate stop reason

```typescript
if (response.stopReason === "maxTokens") {
  // Output was truncated. Either bump maxTokens, or accept truncation.
}
```

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| Polling for partial response | Just await; progress callback is the only mid-call signal |
| Trusting `response.content.text` without `?.` | Use optional chaining + fallback |
| Catching only generic `Error` and dropping context | Re-surface message with `error(\`Sampling: ${err.message}\`)` |
| Logging full prompt at debug level | Prompts may contain secrets — log a hash or length instead |
