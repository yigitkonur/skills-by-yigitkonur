# Canonical Anchor — `mcp-use/mcp-media-mixer`

Reference repo for the non-widget response-helper surface. Read it when you need a compact real server using the helpers exported by `mcp-use@1.26.0`.

**Repo:** [github.com/mcp-use/mcp-media-mixer](https://github.com/mcp-use/mcp-media-mixer)

## What it demonstrates

`index.ts` imports and uses:

- `text()`, `markdown()`, `html()`, `xml()`, `css()`, `javascript()` for text-family content.
- `object()` and `array()` for structured output.
- `image()`, `audio()`, and `binary()` for media and binary payloads.
- `resource()` for embedded resources.
- `mix()` for multi-part composition.
- `error()` for graceful tool failures.

It does **not** demonstrate `widget()`; use `../18-mcp-apps/server-surface/01-widget-helper.md` and the MCP Apps examples for widget-specific response behavior.

## Load-bearing files

| File | What to look at |
|---|---|
| `index.ts` | Tool registration and helper-by-helper examples. |
| `README.md` | Hosted URL, feature list, and local setup. |
| `dist/index.js` | Built server output if you need to compare runtime code. |
| `dist/mcp-use.json` | Generated server/widget metadata emitted by the build. |

The repo does not have `src/tools/*.ts`; all source examples currently live in root `index.ts`.

## Patterns it demonstrates

- **Exported-helper list in practice.** The import list matches `mcp-use/server` exports for response helpers except `widget()`.
- **Binary discipline.** PDF output uses `binary(base64, "application/pdf")`; there is no separate `file()` helper.
- **Composition.** `get-report` combines `text()`, `markdown()`, and `resource(...object(...))` with `mix()`.
- **Structured arrays.** `get-data-array` uses `array([...])`, producing `{ data: items }` in `structuredContent`.

## How to read it

1. Open `index.ts`.
2. Search for the helper name you are validating.
3. Compare the handler with `dist/src/server/utils/response-helpers.d.ts` from `mcp-use@1.26.0`.

Do not copy the repo wholesale. Use it as evidence for how the exported helpers compose into a real server.
