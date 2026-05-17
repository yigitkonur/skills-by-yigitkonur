# When to Use a Widget vs Plain Tools

A widget is not free. It adds an iframe, a CSP surface, a build pipeline, and a user-perceived latency between "tool returned" and "UI rendered". Use a widget only when text loses something the user actually needs.

## Decision matrix

| Signal | Plain `text()` / `object()` | Widget |
|---|---|---|
| Output is a sentence or short paragraph | Yes | No |
| Output is a list of <10 items the user reads linearly | Yes | No |
| Output is dense tabular data (>10 rows, multiple columns) | No | Yes |
| Output is inherently visual (chart, map, timeline, image grid) | No | Yes |
| User must select/filter/sort within the result | No | Yes |
| Output drives multi-step interaction (wizard, picker, builder) | No | Yes |
| Client likely doesn't render widgets (CLI, dumb chat) | Yes | No (or fallback) |
| Output must be quotable in chat / appear in transcripts | Yes | No (or duplicate as `output`) |
| User will ask the LLM to follow up on this result | Yes | Either, with `output:` text summary |

## Quick test

> *"If the user reads the model's text-only fallback, do they get the answer?"*

- **Yes** → tools-only is fine. Adding a widget gold-plates.
- **No, they need to interact with it** → widget.
- **They get a summary but lose detail** → widget, with a meaningful `output: text(...)` summary.

## When `uiResource` alone suffices

If your widget is **purely presentational** — no tool input, no server-computed props, just static HTML with URL params — register it with `exposeAsTool: true` and skip writing a custom tool. The widget becomes a callable tool whose arguments are the props.

```typescript
server.uiResource({
  type: "mcpApps",
  name: "greeting-card",
  htmlTemplate: `...`,
  metadata: { /* ... */ },
  exposeAsTool: true,  // becomes a tool named "greeting-card"
});
```

## When you need both a tool and a widget

This is the common case. Server fetches data, computes props, returns them through `widget()`:

```typescript
server.tool(
  {
    name: "search-products",
    schema: z.object({ query: z.string() }),
    widget: { name: "product-list" },
  },
  async ({ query }) => {
    const results = await db.search(query);
    return widget({
      props: { query, results },
      output: text(`Found ${results.length} products for "${query}"`),
    });
  }
);
```

The widget renders `results`. The model sees the `output` summary so it can reason about what just happened on the next turn.

## Always provide a text fallback

Hosts vary. `ctx.client.supportsApps()` lets you branch (see `05-host-capability-detection.md`), but at minimum populate `output` or `message` so text-only clients still get a useful answer.

## Anti-pattern: "everything is a widget"

Don't widget-ify a tool whose entire output is "Booked. Confirmation #ABC-123." That's a sentence — text wins on every axis: latency, transcript fidelity, client coverage, build complexity.

Don't widget-ify a tool whose result the model is expected to **paraphrase** to the user. Widgets are end-state UI; the model can't "summarize" props it can't see in plain text reliably.
