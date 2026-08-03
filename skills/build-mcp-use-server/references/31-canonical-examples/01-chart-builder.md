# Chart Builder Example

*Read this when you need a tool that generates structured output and renders an MCP App view.*

## Overview

Chart Builder is an **external template-gallery app** — a standalone repo outside the `mcp-use/mcp-use` monorepo, listed on the marketing site's Templates page. It is not one of the canonical in-repo examples under `libraries/typescript/packages/server/examples/`; see `references/31-canonical-examples/00-how-to-use-this-cluster.md` for that distinction. The metadata below (demo URL, GitHub repo, tool name) is verified against `docs/home/templates.mdx`. Its source is not part of the monorepo and was not available to verify line-for-line, so the code sample is illustrative of the pattern, not a quote from the repo — clone it and read the real source before copying anything from it.

**What it does:** Users describe a chart (`create-chart` tool), the server generates structured chart data, and an MCP App view renders it interactively.

## Live endpoints

| Resource | URL |
|----------|-----|
| **Demo endpoint** | `https://yellow-shadow-21833.run.mcp-use.com/mcp` |
| **GitHub source** | [mcp-use/mcp-chart-builder](https://github.com/mcp-use/mcp-chart-builder) |
| **One-click deploy** | [Deploy on Manufact](https://mcp-use.com/deploy/start?repository-url=https%3A%2F%2Fgithub.com%2Fmcp-use%2Fmcp-chart-builder&branch=main&project-name=mcp-chart-builder&port=3000&runtime=node) |

## Connect in Inspector

1. Open [Inspector](/inspector/index).
2. Click **Direct transport**.
3. Paste: `https://yellow-shadow-21833.run.mcp-use.com/mcp`
4. Open **Tools** tab → select `create-chart` → call with `{ "description": "bar chart showing monthly sales" }`
5. View renders in the Inspector UI.

## Pattern this illustrates (verified against real v2 API surface, not this repo's source)

A view-bound tool with a typed `outputSchema` follows the same shape documented in `references/04-tools/canonical-anchor.md` and `references/18-mcp-apps/server-surface/01-tool-view-field.md`:

```typescript
export const createChart = server.tool(
  {
    name: "create-chart",
    description: "Generate a chart from a natural language description",
    inputSchema: z.object({
      description: z.string().describe("Chart description, e.g. 'bar chart of sales by region'"),
    }),
    outputSchema: z.object({
      type: z.enum(["bar", "line", "pie"]),
      data: z.array(z.object({ label: z.string(), value: z.number() })),
      title: z.string(),
    }),
    view: { name: "chart-display", description: "Renders the chart visualization" },
  },
  async ({ description }, ctx) => {
    const chart = await generateChart(description);
    return {
      content: [{ type: "text", text: `Chart generated: ${chart.title}` }],
      structuredContent: chart,
    };
  }
);
```

The view side reads that data with the real `mcp-use/react` hook — `useToolContext`, not `useWidget` (`useWidget` is not exported by `mcp-use/react`; the shipped exports are enumerated in `references/18-mcp-apps/view-react/02-usetoolcontext.md`):

```tsx
import { useToolContext } from "mcp-use/react";

export default function ChartDisplay() {
  const view = useToolContext<"create-chart">();
  if (view.status !== "result") return null;
  const chart = view.toolOutput; // typed by outputSchema
  return <svg>{/* render chart.data */}</svg>;
}
```

## Clone and customize

```bash
git clone https://github.com/mcp-use/mcp-chart-builder
cd mcp-chart-builder
npm install
npm run dev  # Opens Inspector at http://localhost:3000/mcp/inspector
```

Edit `index.ts` to change tool inputs, or the view source for rendering — read the real files first; this page's snippet is a pattern reference, not a copy of that repo.

## Deploy

```bash
npm run deploy
# First run: authenticates with `mcp-use login`, then deploys.
# Prints a dashboard URL — copy the generated MCP endpoint from the
# dashboard rather than assuming a *.run.mcp-use.com slug.
```
