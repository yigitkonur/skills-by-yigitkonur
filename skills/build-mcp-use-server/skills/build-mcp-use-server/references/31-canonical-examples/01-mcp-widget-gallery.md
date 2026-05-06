# Canonical: `mcp-use/mcp-widget-gallery`

**URL:** https://github.com/mcp-use/mcp-widget-gallery
**Hosted demo:** https://wandering-lake-mmxhs.run.mcp-use.com/mcp

The widget-types reference. Demonstrates every UI resource shape mcp-use supports, in a single server, side by side. Use it as the answer to "which widget type should I use?".

## Foundational

This is one of the three repos to read first (with `02-mcp-recipe-finder.md` and `03-mcp-chart-builder.md`). Once you have seen the gallery, every other widget repo is a specialisation.

## Load-bearing files

| File | What to read it for |
|---|---|
| `index.ts` | Every `server.tool` and `server.uiResource` call — one per widget type |
| `resources/react-showcase/widget.tsx` | The React variant with state, hooks, `useCallTool`, theme |
| `index.ts` block calling `server.uiResource({ type: "rawHtml", ... })` | Raw HTML widget with `{{props}}` interpolation |
| `index.ts` block calling `server.uiResource({ type: "remoteDom", ... })` | Remote DOM widget using `ui-stack` / `ui-text` / `ui-button` |
| `index.ts` block registering programmatic widgets | Widgets without a file — defined entirely in code |

## Patterns demonstrated

| Pattern | Where |
|---|---|
| React widget auto-discovery from `resources/<name>/widget.tsx` | `show-react-widget` tool |
| Raw HTML widget with prop interpolation (`{{name}}`) | `html-greeting` uiResource |
| Remote DOM widget (MCP-UI components, postMessage events) | `mcp-ui-poll` uiResource |
| Programmatic widget definition (no file on disk) | Inline `server.uiResource` blocks |
| Client detection adapting widget output | Tool that branches on `ctx.client.info()?.name` |
| `exposeAsTool: true` on a uiResource | Surfacing a widget as its own callable tool |

## Clusters this complements

- `../18-mcp-apps/widget-react/` — React widget mechanics
- `../18-mcp-apps/widget-recipes/` — recipe variants
- `../18-mcp-apps/widget-anti-patterns/` — what not to do
- `../16-client-introspection/` — detecting ChatGPT vs Claude vs Inspector
- `../29-templates/04-mcp-apps-widget.md` — the scaffold this repo follows

## When to study this repo

- You are choosing between React, raw HTML, and Remote DOM and want to see all three in working form.
- You want a worked example of `exposeAsTool: true`.
- You need a reference for client-detection branching inside a single tool.
- You are unsure whether your widget should live in `resources/` or be defined programmatically.

## Local run

```bash
gh repo clone mcp-use/mcp-widget-gallery
cd mcp-widget-gallery
npm install
npm run dev
# Inspector: http://localhost:3000/inspector
```
