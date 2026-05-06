# Canonical: `mcp-use/mcp-chart-builder`

**URL:** https://github.com/mcp-use/mcp-chart-builder
**Hosted demo:** https://yellow-shadow-21833.run.mcp-use.com/mcp

The streaming-tool-props reference. A single tool — `create-chart` — produces an Apache ECharts visualisation that renders progressively as the LLM streams the option JSON. The widget reads `partialToolInput` and `isStreaming` from `useWidget` and re-paints on every update.

## Foundational

One of the three repos to read first. Where `01-mcp-widget-gallery.md` shows widget *shapes* and `02-mcp-recipe-finder.md` shows server *mechanics*, this shows the streaming-render pattern that makes long-output widgets feel responsive.

## Load-bearing files

| File | What to read it for |
|---|---|
| `index.ts` | Single `create-chart` tool — JSON-string `option` schema, `widget()` response |
| `resources/chart-display/widget.tsx` | The streaming render: read `partialToolInput`, attempt `setOption`, swallow mid-stream errors |
| `resources/chart-display/types.ts` | `propSchema` shape — `chartType`, free-form `option` object |
| `resources/styles.css` | Shared widget styles |

## Patterns demonstrated

| Pattern | Where |
|---|---|
| `option: z.string()` (JSON-as-string) — keeps schemas simple while letting the model emit free-form ECharts config | `create-chart` schema |
| `widget({ props, output })` returning structured props plus an LLM-visible message | `create-chart` handler |
| `useWidget` exposing `isStreaming` and `partialToolInput` | `widget.tsx` |
| Best-effort `echarts.setOption(option, true)` inside a `try/catch` while streaming | `widget.tsx` |
| ECharts theme switch (`echarts.init(el, "dark")`) on theme change | `widget.tsx` `useEffect` |
| `ResizeObserver` driving `instance.resize()` | `widget.tsx` |
| `displayMode === "fullscreen"` + `requestDisplayMode` for an immersive view | `widget.tsx` |

## Clusters this complements

- `../18-mcp-apps/streaming-tool-props/` — the deep dive
- `../18-mcp-apps/widget-react/` — useWidget, McpUseProvider
- `../30-workflows/11-streaming-chart-widget.md` — workflow derived from this repo
- `../05-responses/` — `widget()` response helper

## When to study this repo

- You are building any widget whose props are large/structured and arrive over many tokens.
- You want to see how to deal with mid-stream invalid JSON without breaking the UI.
- You need a worked example of the `requestDisplayMode("fullscreen")` UX.
- You want a real-world precedent for `option: z.string()` schemas.

## Local run

```bash
gh repo clone mcp-use/mcp-chart-builder
cd mcp-chart-builder
npm install
npm run dev
```
