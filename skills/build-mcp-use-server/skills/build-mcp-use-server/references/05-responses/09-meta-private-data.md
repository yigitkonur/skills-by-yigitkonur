# `_meta` — Metadata and Widget-Only Data

`_meta` is the response metadata surface. In `mcp-use@1.26.0`, helpers use it for MIME hints and widget metadata:

- `text()`, `markdown()`, `html()`, `css()`, `javascript()`, `xml()`, `object()` set `_meta.mimeType`.
- `image()`, `audio()`, and `binary()` add type flags such as `isImage`, `isAudio`, or `isBinary`.
- `widget({ metadata })` copies `metadata` to `_meta`.
- `mix()` shallow-merges `_meta` objects from every helper passed in.

## Widget visibility recap

For widget tool results:

| Surface | Field | LLM sees it? | Widget sees it? |
|---|---|---|---|
| Content | `content[]` | Yes | Yes |
| Props | `structuredContent` | No | Yes (`useWidget().props`) |
| Metadata | `_meta` | No | Yes (`useWidget().metadata`) |

This visibility table is specific to widget responses. For ordinary non-widget tools, use `object()` or `array()` when the typed result itself is part of the tool answer.

## When to use `_meta`

| Data | Surface |
|---|---|
| The answer the model should reason over | `content` and/or ordinary `structuredContent` |
| Widget render props | `widget({ props })` |
| Widget cursors, timestamps, trace IDs, and other client-only metadata | `widget({ metadata })` |
| MIME hints for helper results | helper `_meta.mimeType` |
| OpenAI Apps SDK wiring keys | tool `_meta` at registration time |

Do not use `_meta` to deliver the actual answer. The model-facing summary belongs in `content`, usually via `text()` or `markdown()`.

## Setting `_meta` with `widget()`

The `widget()` helper takes `metadata` and routes it to `_meta`:

```typescript
import { widget, text } from "mcp-use/server";

return widget({
  props: { city, temperature, conditions },              // structuredContent
  output: text(`Weather in ${city}: ${temperature}°C`),  // content
  metadata: {                                            // _meta
    refreshSeconds: 60,
    nextCursor,
    traceId,
  },
});
```

For non-widget responses, set `_meta` directly only when you need metadata not already provided by a helper:

```typescript
return {
  ...markdown("Done."),
  _meta: {
    diagnosticTraceId: traceId,
    cacheTtlSeconds: 60,
  },
};
```

`mix()` merges `_meta` from every helper passed in, so later helpers can overwrite earlier keys with the same name.

## OpenAI Apps SDK wiring

The raw Apps SDK metadata pattern is supported, but it is lower-level than `widget: { ... }` plus `widget()`:

```typescript
server.tool(
  {
    name: "show_chart",
    description: "Display a chart",
    schema: z.object({ data: z.array(z.any()).describe("The chart data") }),
    _meta: {
      "openai/outputTemplate": "ui://widgets/chart",
      "openai/toolInvocation/invoking": "Generating chart...",
      "openai/toolInvocation/invoked": "Chart generated",
      "openai/widgetAccessible": true,
    },
  },
  async ({ data }) => ({
    _meta: { "openai/outputTemplate": "ui://widgets/chart" },
    content: [{ type: "text", text: "Chart displayed" }],
    structuredContent: { data },
  })
);
```

Prefer the `widget()` helper and registration-time `widget` config for new mcp-use widgets — see `../18-mcp-apps/server-surface/01-widget-helper.md`.

## Anti-patterns

| Bad | Good |
|---|---|
| Put widget-only cursors in `content` | Put them in `widget({ metadata })` |
| Use `_meta` as the only place containing the answer | Put the answer in `content` or ordinary `structuredContent` |
| Put large render-only lookup maps in ordinary `object()` output | Move render-only data to widget `props` or `metadata` |
| Assume `_meta` persists across calls | Treat `_meta` as per-response metadata only |
| Hand-write OpenAI `_meta` for every widget | Use `widget: { name, invoking, invoked }` and `widget()` where possible |
