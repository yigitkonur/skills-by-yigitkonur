# Streaming State Machine

Four protocol moments exist, but `mcp-use@1.26.0` collapses "streaming args" and "executing tool" into the same visible hook state after a partial has arrived. Read `isPending`, `partialToolInput`, `toolInput`, and `props` together.

Source note: runtime at `mcp-use@1.26.0/package/dist/src/react/index.js` lines 2639-2643 and 2966-2977 keeps partials until `tool-result`; `widget-types.d.ts` lines 405-413 says `isStreaming` ends on `tool-input`, so follow runtime.

## The observable states

| Protocol moment | `isPending` | `isStreaming` | `partialToolInput` | `toolInput` | `props` |
|---|---|---|---|---|---|
| **Not started** | `true` | `false` | `null` | `{}` | `{}` or defaults |
| **Streaming args** | `true` | `true` | growing `Partial<TToolInput>` | `{}` until final args arrive | `{}` or defaults |
| **Executing tool** | `true` | `true` if any partial arrived; otherwise `false` | last partial value or `null` | complete args | merged from `toolInput` while waiting |
| **Complete** | `false` | `false` | `null` | complete args | `structuredContent` overlaid on `toolInput` |

## Timeline

```
LLM starts generating tool args, if host supports partials
  ↓ ui/notifications/tool-input-partial
  ↓ partialToolInput grows snapshot-by-snapshot
  ↓ isStreaming = true

LLM finishes generating args
  ↓ ui/notifications/tool-input
  ↓ toolInput = complete args
  ↓ partialToolInput remains set in mcp-use@1.26.0

Server tool handler executes
  ↓ isPending stays true

Server returns result
  ↓ ui/notifications/tool-result
  ↓ partialToolInput = null
  ↓ isStreaming = false
  ↓ isPending = false
  ↓ props = structuredContent overlaid on toolInput
```

## What's available in each state

### Not started / no partials

Nothing has arrived yet. Render a skeleton or spinner.

```tsx
if (isPending && !partialToolInput) return <Skeleton />;
```

This branch matches before streaming begins and remains the whole pending path on hosts that don't stream — see `04-fallback-for-non-streaming-hosts.md`.

### Streaming args

`partialToolInput` is a `Partial<TProps>` that gains fields as the LLM writes them. Field-arrival order follows generation order, not schema order. Always treat every field as possibly missing.

```tsx
const title = partialToolInput?.title;     // may be undefined
const code  = partialToolInput?.code ?? "";
```

### Executing tool

The LLM finished generating arguments; the server is now running. In `mcp-use@1.26.0`, receiving the final `tool-input` sets `toolInput` but does **not** clear `partialToolInput`. If a partial was received, `isStreaming` remains `true` until `tool-result`.

Do **not** key an executing branch on `isPending && !isStreaming && partialToolInput`; that predicate is not reachable in the current runtime. Use `isPending && partialToolInput` for the streaming/preview path, and `isPending && !partialToolInput` for the fallback path.

### Complete

Server returned. `isPending` is `false`, so `props` is narrowed to the full `TProps` shape. `output` and `metadata` are now set if your tool returned them.

## `toolInput` vs `partialToolInput` vs `props`

| Value | Available when | Contains |
|---|---|---|
| `partialToolInput` | While host has sent partial args and no result has arrived | Growing partial args from the LLM. Cleared on `tool-result`. |
| `toolInput` | Once final tool args arrive | Complete args the LLM sent. |
| `props` | Always, but typed partial while `isPending` | Defaults + `toolInput`, then server `structuredContent` after result. |

`toolInput` is the raw args the model emitted. Final `props` is what your tool handler decided to send back; `useWidget` overlays `structuredContent` on `toolInput`, so the shapes commonly match but do not have to.

## Field arrival order

For a schema like:

```typescript
z.object({ title: z.string(), description: z.string(), code: z.string() })
```

You might observe these snapshots in order:

1. `{ title: "Hello" }`
2. `{ title: "Hello World", description: "A" }`
3. `{ title: "Hello World", description: "A simple ex", code: "con" }`
4. `{ title: "Hello World", description: "A simple example", code: "console.log('hello')" }`

Plan your render so each successive snapshot looks coherent — the user sees all of them.
