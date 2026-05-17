# The `widget()` Response Helper

The single canonical way to build a widget tool result. Imported from `mcp-use/server`. Returns a `CallToolResult` with three visibility channels populated correctly so the LLM, the host, and the widget each see what they should.

## Signature

```typescript
import { widget } from "mcp-use/server";

widget({
  props?: Record<string, any>,
  output?: CallToolResult,
  message?: string,
  metadata?: Record<string, unknown>,
}): CallToolResult
```

## Parameters

| Field | Type | Required | What it becomes |
|---|---|---|---|
| `props` | `Record<string, any>` | No | `structuredContent`. Reaches the widget as `useWidget().props`; not added to the model context. Defaults to `{}`. |
| `output` | `CallToolResult` | No | `content`. Use any response helper (`text(...)`, `object(...)`, etc.). What the LLM sees. |
| `message` | `string` | No | Shorthand for `output: text(message)`. Takes precedence over `output` when both are set. |
| `metadata` | `Record<string, unknown>` | No | `_meta`. Reaches the widget as `useWidget().metadata`. **Not** model-visible. Use for private UI hydration, not credentials. |

If neither `output` nor `message` is set, an empty text content block is emitted.

## Return shape

`widget()` only builds the runtime tool result: `content`, optional `structuredContent`, and optional `_meta`. MIME types and dual-protocol resource metadata come from the paired `server.tool({ widget })` registration and `server.uiResource()`/auto-discovered widget, not from `widget()`.

## Visibility table

| Field | LLM sees? | Widget sees? | Populated by |
|---|---|---|---|
| `content` | **Yes** | Yes (text fallback) | `output` or `message` |
| `structuredContent` | **No** | Yes (as `props`) | `props` |
| `_meta` | **No** | Yes (as `metadata`) | `metadata` |

This separates model-visible text from widget rendering data. `_meta` is not added to the model context, but the host/widget still receives it, so do not send credentials through `metadata`.

## Examples

### Minimal — props plus a text summary

```typescript
import { widget, text } from "mcp-use/server";

return widget({
  props: { city: "Paris", temperature: 22, conditions: "Sunny" },
  output: text("Weather in Paris: 22 degrees, Sunny"),
});
```

### `message` shorthand

```typescript
return widget({
  props: items,
  message: `Found ${items.length} items`,
});
```

Equivalent to `output: text(`Found ${items.length} items`)`.

### Structured `output` (rare — only when the model needs typed fields)

```typescript
import { widget, object } from "mcp-use/server";

return widget({
  props: items,
  output: object({ count: items.length, summary }),
});
```

### Private hydration via `metadata`

```typescript
return widget({
  props: { items: filteredItems },                    // model-safe
  metadata: { totalCount: 1000, nextCursor: "abc" },  // not model-visible
  output: text(`Showing ${filteredItems.length} of 1000 results`),
});
```

The widget reads via `useWidget()`:

```tsx
const { props, metadata } = useWidget();
// props    = { items: [...] }
// metadata = { totalCount, nextCursor }
```

## Always populate `output` (or `message`)

Even when widgets are supported, the `content` channel is what text-only clients and conversation transcripts see. A tool that returns a widget with empty `content` looks like a no-op to the model on its next turn. Cross-link: `../05-host-capability-detection.md`.

## Don't construct `CallToolResult` manually for widgets

Building `structuredContent` and `_meta` by hand is the largest source of "widget renders blank" bugs. The helper handles tool-result field placement; registration handles MIME and protocol metadata. Use both pieces together.

**Canonical doc:** https://manufact.com/docs/typescript/server/mcp-apps
