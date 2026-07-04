# Canonical: `mcp-use/mcp-diagram-builder`

**URL:** https://github.com/mcp-use/mcp-diagram-builder
**Hosted demo:** https://lucky-darkness-402ph.run.mcp-use.com/mcp

The Mermaid-diagram widget reference. Two tools — `create-diagram` and `edit-diagram` — emit Mermaid syntax that renders progressively in a streaming widget. The server keeps the latest diagram in memory so `edit-diagram` can replace it. Companion to `03-mcp-chart-builder.md`: same streaming pattern, different visualisation library.

## Load-bearing files

| File | What to read it for |
|---|---|
| `index.ts` (`diagramTypes` tuple) | The exact set of Mermaid diagram types the tool advertises |
| `index.ts` (`lastDiagram` module-scope ref) | Edit-in-place state — the simplest possible "current document" pattern |
| `index.ts` (`create-diagram` and `edit-diagram` tools) | Same widget name on both, different `invoking`/`invoked` messages |
| `resources/diagram-view/widget.tsx` | Reading `partialToolInput` to render Mermaid syntax mid-stream, calling `mermaid.render` defensively |

## Patterns demonstrated

| Pattern | Where |
|---|---|
| Two tools targeting the same widget name (create + edit, identical UI surface) | `widget: { name: "diagram-view" }` on both |
| `lastDiagram` as in-process current-document ref — no DB, no session map | Top of `index.ts` |
| Defensive render — Mermaid throws on partial syntax; widget swallows mid-stream errors | `widget.tsx` |
| Theme-aware Mermaid (`mermaid.initialize({ theme: theme === "dark" ? "dark" : "default" })`) | `widget.tsx` |
| Type hint via optional `diagramType` enum that disambiguates rendering when Mermaid auto-detection is wrong | Schemas |

## Clusters this complements

- `../31-canonical-examples/03-mcp-chart-builder.md` — the same streaming-tool-props pattern with ECharts
- `../18-mcp-apps/streaming-tool-props/` — deep dive
- `../30-workflows/11-streaming-chart-widget.md` — workflow derived from chart-builder; the same shape applies here

## When to study this repo

- You want a second worked example of streaming-tool-props beyond charts.
- You need an edit-in-place pattern (replace the previous render with a new one).
- You are integrating any rendering library that throws on partial input — Mermaid is a representative example.
- You want to see how `lastDiagram` (a single module-scope ref) substitutes for a session-keyed map when the document is global.

## Differences from `mcp-chart-builder`

| Concern | chart-builder | diagram-builder |
|---|---|---|
| Render lib | ECharts (canvas) | Mermaid (SVG via async `mermaid.render`) |
| Schema input | `option: z.string()` (JSON) | `diagram: z.string()` (Mermaid syntax) |
| Type hint | `chartType` enum, required | `diagramType` enum, optional |
| State | Stateless tools | Module-scope `lastDiagram` for `edit-diagram` |
| Theme | `echarts.init(el, "dark")` | `mermaid.initialize({ theme: "dark" })` |

## Local run

```bash
gh repo clone mcp-use/mcp-diagram-builder
cd mcp-diagram-builder
npm install
npm run dev
```
