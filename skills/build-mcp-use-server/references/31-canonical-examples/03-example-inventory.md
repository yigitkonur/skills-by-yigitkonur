# Full Example Inventory

*Read this to find a specific example pattern or tool type.*

This is the complete inventory from `/tmp/mcp-use-beta/docs/typescript/server/examples.mdx`, verified 2026-08-02. Each row is grounded in the vendor docs.

## Canonical examples (with live endpoints)

| Example | Tools | Live endpoint | GitHub source | Deploy |
|---------|-------|---------------|---------------|--------|
| **Chart Builder** | `create-chart` | `https://yellow-shadow-21833.run.mcp-use.com/mcp` | [mcp-use/mcp-chart-builder](https://github.com/mcp-use/mcp-chart-builder) | Deploy link in repo |
| **Diagram Builder** | `create-diagram`, `edit-diagram` | `https://lucky-darkness-402ph.run.mcp-use.com/mcp` | [mcp-use/mcp-diagram-builder](https://github.com/mcp-use/mcp-diagram-builder) | Deploy link in repo |
| **Slide Deck** | `create-slides`, `edit-slide` | `https://solitary-block-r6m6x.run.mcp-use.com/mcp` | [mcp-use/mcp-slide-deck](https://github.com/mcp-use/mcp-slide-deck) | Deploy link in repo |
| **Maps Explorer** | `show-map`, `get-place-details`, `add-markers` | `https://super-night-ttde2.run.mcp-use.com/mcp` | [mcp-use/mcp-maps-explorer](https://github.com/mcp-use/mcp-maps-explorer) | Deploy link in repo |

**Source:** `/tmp/mcp-use-beta/docs/typescript/server/examples.mdx` lines 1–187

## How to use

1. **Copy a demo URL** and paste into [Inspector](/inspector/index) under **Direct transport**.
2. **Click Tools** to see registered tools.
3. **Call a tool** to test before cloning.
4. **Clone the GitHub repo** if you want to customize it.
5. **Deploy** using the repo's own deploy link or `npm run deploy` after customization.

## Patterns by tool type

### Structured output + views
- **Chart Builder** (`create-chart`) — structured JSON output with React view
- **Diagram Builder** (`create-diagram`, `edit-diagram`) — multi-tool workflow
- **Slide Deck** (`create-slides`, `edit-slide`) — similar pattern

### Location/geospatial
- **Maps Explorer** (`show-map`, `get-place-details`, `add-markers`) — Three related tools working with location data

## Testing without cloning

Use the Inspector to connect to any live endpoint and test tools. This is the fastest way to verify a tool's input/output before building on top of it.
