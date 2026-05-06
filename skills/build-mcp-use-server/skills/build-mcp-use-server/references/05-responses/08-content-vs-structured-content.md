# Content vs `structuredContent`

Use this file for the response-surface contract. Keep it grounded in `mcp-use@1.26.0`: helper behavior is defined by `dist/src/server/utils/response-helpers.d.ts` and the runtime in `dist/src/server/index.js`.

## Surfaces

| Field | What `mcp-use` puts there |
|---|---|
| `content[]` | MCP content blocks: text, image, audio, resource |
| `structuredContent` | Typed JSON from `object()`, `array()`, `widget({ props })`, or merged `mix()` inputs |
| `_meta` | MIME hints and helper metadata; widget metadata from `widget({ metadata })` |

## Helper behavior

| Helper | `content[]` | `structuredContent` | `_meta` |
|---|---|---|---|
| `text()` | text block | none | `mimeType: "text/plain"` |
| `markdown()` | text block | none | `mimeType: "text/markdown"` |
| `html()` / `css()` / `javascript()` / `xml()` | text block | none | matching text MIME |
| `image()` | image block | none | `mimeType`, `isImage: true` |
| `audio()` | audio block | none | `mimeType`, `isAudio: true` |
| `binary()` | text block containing base64 | none | `mimeType`, `isBinary: true` |
| `object(data)` | pretty-printed JSON text | `data` | `mimeType: "application/json"` |
| `array(items)` | pretty-printed JSON text | `{ data: items }` | none |
| `resource(...)` | resource block | none | none |
| `widget({ props, output, metadata })` | output content or message | output structured content, else `props` | `metadata` |
| `mix(...results)` | concatenated content arrays | shallow merge of structured objects | shallow merge of metadata objects |

## Ordinary tools

For non-widget tools, prefer helpers that fill the surfaces you need:

- Use `text()` or `markdown()` when the result is only conversational.
- Use `object()` for structured JSON objects; it also includes readable JSON text in `content`.
- Use `array()` for lists; it wraps the typed surface as `{ data: items }`.
- Use `mix(markdown(summary), object(data))` when the model needs prose and a typed consumer needs fields.

If a tool declares `outputSchema`, the returned `structuredContent` must match that schema. `object()`, `array()`, and `mix()` are the response helpers that populate `structuredContent`.

## Widget tools

`widget()` follows the widget visibility rules documented by mcp-use:

| Widget field | Result field | Visibility |
|---|---|---|
| `output` or `message` | `content` | LLM-visible summary |
| `props` | `structuredContent` | Widget props, not added to model context |
| `metadata` | `_meta` | Widget metadata, not added to model context |

Do not apply the ordinary-tool assumption to widget props. In widget docs, `structuredContent` is the widget data channel, while `content` is the model-facing summary.

## Rules

- Do not hand-write `structuredContent` when `object()` or `array()` can produce the correct shape.
- If you use `mix()`, avoid duplicate keys in structured objects unless later helpers intentionally override earlier helpers.
- Do not put secrets, bulky hydration data, or UI-only state in ordinary `object()` results. For widgets, use `widget({ metadata })` for client-only metadata and `widget({ props })` for render props.
- Do not rely on non-exported helpers such as `json()`, `video()`, `file()`, or `stream()` to create missing surfaces.

## Quick check

Before returning a response with both `content` and `structuredContent`, ask:

1. Does `content` give a readable answer?
2. Does `structuredContent` contain the typed body promised by `outputSchema` or by the widget props contract?
3. Is private widget-only data in `_meta`, not in ordinary model-facing text?
