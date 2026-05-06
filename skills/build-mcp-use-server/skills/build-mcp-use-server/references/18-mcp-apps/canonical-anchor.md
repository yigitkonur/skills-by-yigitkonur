# Canonical Anchor — `mcp-use/mcp-widget-gallery`

The foundational reference repo for everything in `18-mcp-apps/`. When in doubt about how a widget should be wired — server registration, `uiResource` variants, metadata, props streaming, follow-up messages — check this repo first.

## Repo

```
https://github.com/mcp-use/mcp-widget-gallery
```

It demonstrates the main widget registration paths:

| Path | What it loads | When to use |
|---|---|---|
| Auto-discovered React widget | `resources/react-showcase/widget.tsx` compiled at build time | Default for new widgets |
| `rawHtml` | A literal `htmlContent` string in `server.uiResource()` | Tiny static views, embedded charts |
| `remoteDom` | A `script` string in `server.uiResource()` | Custom RPC-driven UIs |
| `mcpApps` | An `htmlTemplate` string in `server.uiResource()` | ChatGPT + MCP Apps interop |

It also demonstrates **programmatic widget creation** via `server.uiResource(...)` outside of the `widget` config on `server.tool()`.

## Load-bearing files to read

When mining this repo for patterns, focus on these files first — they teach more than the rest combined.

| File | Why it matters |
|---|---|
| `index.ts` | Single-server registration of every variant; shows how `server.uiResource()` and `server.tool({ widget: ... })` co-exist |
| `resources/react-showcase/widget.tsx` | The reference React widget — `widgetMetadata` export, `useWidget`, theme handling, display-mode requests |
| `resources/react-showcase/types.ts` | Zod prop schema used by both the server and widget |
| `package.json` | Shows the expected `mcp-use` CLI scripts for dev, build, start, and type generation |

When adapting a recipe from `widget-recipes/`, cross-check the registration block in `index.ts` to make sure the server side matches what the recipe shows.

## Other widget-related canonical anchors

Different widget concerns live in sibling sub-clusters of `18-mcp-apps/`. Each has its own anchor file pointing at a different repo:

| Anchor | Repo | Concern |
|---|---|---|
| `streaming-tool-props/canonical-anchor.md` | `mcp-use/mcp-chart-builder` | Streaming `partialToolInput` into a chart widget while the LLM is still generating |
| `../14-notifications/canonical-anchor.md` | `mcp-use/mcp-progress-demo` | Server-pushed progress notifications and resource subscription updates |

If a question touches more than one of those concerns, walk both anchors before writing code — the repos use the same primitives but bias different defaults.

## When this anchor is the wrong one

| You actually want | Go to |
|---|---|
| Tool registration without a widget | `../04-tools/canonical-anchor.md` |
| Streamable HTTP transport patterns | `../09-transports/01-overview.md` |
| OAuth-protected widget endpoints | `../11-auth/01-overview-decision-matrix.md` |
| ChatGPT Apps-only interop | `chatgpt-apps/01-protocol-overview.md` |

## How to use this anchor

1. Read `index.ts` end to end before writing a new widget tool.
2. For auto-discovered React widgets, open the matching `resources/<name>/` folder and read the entry file in full.
3. Mirror the file layout (`resources/<widget-name>/widget.tsx`, `src/tools/<domain>.ts`) — the recipes in `widget-recipes/` already follow it.
4. Never copy a widget wholesale; lift the registration shape, the `widgetMetadata` block, and the `useWidget` access pattern, then write the body for your domain.
