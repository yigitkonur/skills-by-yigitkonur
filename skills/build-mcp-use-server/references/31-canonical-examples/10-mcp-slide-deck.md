# Canonical: `mcp-use/mcp-slide-deck`

**URL:** https://github.com/mcp-use/mcp-slide-deck
**Hosted demo:** https://solitary-block-r6m6x.run.mcp-use.com/mcp

The presentation-widget reference. `create-slides` builds a navigable deck that streams in slide-by-slide; `edit-slide` updates a single slide by index. The server also exposes a `/api/assets` POST/GET pair so the widget can store and reference uploaded images by id — a clean pattern for mixing widget UI with server-side asset storage.

## Load-bearing files

| File | What to read it for |
|---|---|
| `index.ts` (`slideSchema`) | A non-trivial nested schema — title, HTML content, optional layout, optional image URL |
| `index.ts` (asset routes: `server.post("/api/assets")`, `server.get("/api/assets/:id")`) | Custom Hono routes that take and serve base64-uploaded assets keyed by UUID |
| `index.ts` (`create-slides` tool) | Streaming tool input that the widget picks up slide-by-slide |
| `index.ts` (`edit-slide` tool) | Per-index mutation, same widget name |
| `resources/slide-viewer/widget.tsx` | Navigation, fullscreen mode, model-context (which slide is active) |

## Patterns demonstrated

| Pattern | Where |
|---|---|
| Custom `server.post` + `server.get` routes alongside MCP for asset I/O | Top of `index.ts` |
| In-memory asset store keyed by UUID, served at `/api/assets/:id` | `assets` Map |
| Nested-array streaming widget — slides arrive one by one as the model writes them | `create-slides` schema and widget |
| Per-index edit using the same widget — `edit-slide` updates `slides[index]` | `edit-slide` |
| Model-context ("you are now on slide 3") so the LLM can drive navigation | Widget exposes current index |
| Theme variants (`light` / `dark` / `gradient`) | `theme` schema field |

## Clusters this complements

- `../17-advanced/` — custom Hono routes alongside MCP (the asset endpoints)
- `../18-mcp-apps/streaming-tool-props/` — streaming a list of objects, not a single object
- `../05-responses/` — `widget()` response with rich props

## When to study this repo

- You need a widget that streams an array (not a single object) — slides, cards, list items.
- Your widget needs to upload or reference binary assets that the model cannot embed inline.
- You want a worked example of model-context — the AI knows which sub-element is currently focused.
- You want a per-index edit pattern (update one item without resending the whole list).

## Local run

```bash
gh repo clone mcp-use/mcp-slide-deck
cd mcp-slide-deck
npm install
npm run dev
```
