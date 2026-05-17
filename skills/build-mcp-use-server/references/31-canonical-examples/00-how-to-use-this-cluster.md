# Canonical Examples — How to Use This Cluster

The `mcp-use/*` GitHub organisation publishes 12 reference servers that exercise every notable feature of mcp-use. They are the load-bearing examples this whole skill distills from. When this skill teaches a pattern, one of these repos demonstrates it in production-quality form.

Read these directly when you want to see real code, real `package.json` deps, real widget builds, real CSP, and real hosted demos.

## Foundational order

Read these three first. Everything else assumes you understand them.

1. `01-mcp-widget-gallery.md` — every widget *type* in one place: React, raw HTML, Remote DOM, programmatic, client detection.
2. `02-mcp-recipe-finder.md` — complex Zod schemas, completable args, MCP middleware (`server.use("mcp:tools/call", ...)`), tool annotations, prompts, resources.
3. `03-mcp-chart-builder.md` — streaming-tool-props pattern: render the widget while the LLM is still typing the JSON.

## All 12 repos by purpose

| Doc | Repo | Purpose |
|---|---|---|
| `01-mcp-widget-gallery.md` | `mcp-use/mcp-widget-gallery` | Every widget type variant |
| `02-mcp-recipe-finder.md` | `mcp-use/mcp-recipe-finder` | Schemas, middleware, annotations |
| `03-mcp-chart-builder.md` | `mcp-use/mcp-chart-builder` | Streaming tool props |
| `04-mcp-media-mixer.md` | `mcp-use/mcp-media-mixer` | Every response helper (image, audio, binary, html, css, js, xml, ...) |
| `05-mcp-progress-demo.md` | `mcp-use/mcp-progress-demo` | Progress tokens, widget polling, annotations, `error()` |
| `06-mcp-resource-watcher.md` | `mcp-use/mcp-resource-watcher` | Resources, subscriptions, `notifyResourceUpdated`, `onRootsChanged` |
| `07-mcp-multi-server-hub.md` | `mcp-use/mcp-multi-server-hub` | `server.proxy()` + HTTP and MCP-operation middleware + audit |
| `08-mcp-i18n-adaptive.md` | `mcp-use/mcp-i18n-adaptive` | Client introspection, locale, timezone, safe area |
| `09-mcp-diagram-builder.md` | `mcp-use/mcp-diagram-builder` | Mermaid diagrams with streaming + edit-in-place |
| `10-mcp-slide-deck.md` | `mcp-use/mcp-slide-deck` | Rich presentation widget with asset upload route |
| `11-mcp-maps-explorer.md` | `mcp-use/mcp-maps-explorer` | Leaflet maps with markers and lookups |
| `12-mcp-huggingface-spaces.md` | `mcp-use/mcp-huggingface-spaces` | External REST API + iframe embedding |

## How each entry is structured

Every file in this cluster is a short anchor — not a tutorial. It contains:

- **Repo URL** at the top.
- **One-line description** of what the repo demonstrates.
- **Load-bearing files** — the small list of files that make the repo interesting.
- **Patterns demonstrated** — the named techniques the repo exercises.
- **Clusters this complements** — pointers back into this skill so you can study the underlying concept after seeing it applied.
- **When to study this repo** — concrete trigger conditions.

The full source is the reference; this cluster is a navigation index.

## Workflow / canonical-example overlap

Several `30-workflows/` files (notably 11 through 15) are derived from these canonical repos. The workflow file teaches the pattern in a self-contained way; the canonical-example file points you at the production repo for the full context. Use both.

## How to clone and study

```bash
gh repo clone mcp-use/mcp-widget-gallery
cd mcp-widget-gallery
npm install
npm run dev
# open http://localhost:3000/inspector
```

Widget repos follow the `create-mcp-use-app` scaffold layout — `index.ts` at the root, widgets under `resources/<name>/widget.tsx`. Utility-only repos such as `mcp-media-mixer` may have only `index.ts`.

## See also

- Templates that match these repos: `../29-templates/04-mcp-apps-widget.md`
- Workflows derived from these repos: `../30-workflows/11-streaming-chart-widget.md` … `../30-workflows/15-i18n-adaptive-widget.md`
