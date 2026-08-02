# Chart Builder Example

*Read this when you need a tool that generates structured output and renders an MCP App view.*

## Overview

The Chart Builder example shows how to take natural language input, validate and process it server-side, return structured JSON output, and render an interactive MCP App view.

**What it does:** Users describe a chart (`create-chart` tool), the server generates SVG or data structure, and a React view renders it interactively.

**Key files:**
- `index.ts` — Server entry with `create-chart` tool definition + outputSchema
- `views/chart-display/view.tsx` — React view receiving `structuredContent` props
- `.mcp-use/build/` — Compiled output after `mcp-use build`

## Live endpoints

| Resource | URL |
|----------|-----|
| **Demo endpoint** | `https://yellow-shadow-21833.run.mcp-use.com/mcp` |
| **GitHub source** | [mcp-use/mcp-chart-builder](https://github.com/mcp-use/mcp-chart-builder) |
| **Deploy your own** | Use source repo's deploy link |

## Connect in Inspector

1. Open [Inspector](/inspector/index).
2. Click **Direct transport**.
3. Paste: `https://yellow-shadow-21833.run.mcp-use.com/mcp`
4. Open **Tools** tab → select `create-chart` → call with `{ "description": "bar chart showing monthly sales" }`
5. View renders in the Inspector UI.

## Key patterns

**Tool definition with outputSchema:**
```typescript
export const createChart = server.tool(
  {
    name: "create-chart",
    description: "Generate a chart from natural language description",
    inputSchema: z.object({
      description: z.string().describe("Chart description, e.g. 'bar chart of sales by region'")
    }),
    outputSchema: z.object({
      type: z.enum(["bar", "line", "pie"]),
      data: z.array(z.object({
        label: z.string(),
        value: z.number()
      })),
      title: z.string()
    }),
    view: {
      name: "chart-display",
      description: "Renders chart visualization"
    }
  },
  async ({ description }, ctx) => {
    const chart = await generateChart(description);
    return {
      content: [{ type: "text", text: `Chart generated: ${chart.title}` }],
      structuredContent: chart
    };
  }
);
```

**React view receiving props:**
```tsx
import { useWidget } from "mcp-use/react";

export default function ChartDisplay() {
  const { props } = useWidget<ChartData>();
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

Edit `index.ts` to change tool inputs, or `views/chart-display/view.tsx` for rendering.

## Deploy

```bash
npm run deploy
# First run: logs into Manufact Cloud, then uploads
# Result: https://{your-slug}.run.mcp-use.com/mcp
```
