# Workflow: MCP Apps View — Chart Widget

*Read this for an end-to-end workflow: scaffold, build a tool with a React chart view, test locally.*

## Prerequisites

- Node.js >= 22
- `npm` or `pnpm`
- Familiarity with React

## Steps

### 1. Scaffold

```bash
npx create-mcp-use-app@2.0.0-beta.14 my-charts --template mcp-apps --npm --install
cd my-charts
```

**Verify:** `package.json` has React 19, `zod@4.4.3`. Folder `views/my-view/` exists.

### 2. Replace the Tool

Edit `index.ts`:

```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({
  name: "chart-server",
  version: "1.0.0",
});

const chartDataSchema = z.object({
  labels: z.array(z.string()),
  values: z.array(z.number()),
  title: z.string(),
});

export const generateChart = server.tool(
  {
    name: "generate-chart",
    description: "Generate a bar chart from data",
    inputSchema: z.object({
      dataType: z.enum(["sales", "traffic"]).describe("Type of data"),
    }),
    outputSchema: chartDataSchema,
    view: {
      name: "chart-view",
      description: "Interactive chart visualization",
    },
  },
  async ({ dataType }) => {
    const data =
      dataType === "sales"
        ? { labels: ["Jan", "Feb", "Mar"], values: [100, 150, 120], title: "Monthly Sales" }
        : { labels: ["Mon", "Tue", "Wed"], values: [500, 600, 550], title: "Daily Traffic" };

    return {
      content: [{ type: "text", text: `Generated ${dataType} chart` }],
      structuredContent: data,
    };
  }
);

export default server;
```

Never call `server.listen()` here — the CLI (`mcp-use dev`/`mcp-use start`) owns the listener.

**Verify:** `npm run typecheck` passes.

### 3. Create the Chart View

Rename `views/my-view/` to `views/chart-view/`:

```bash
mv views/my-view views/chart-view
```

Replace `views/chart-view/view.tsx`:

```tsx
import { useToolContext, ThemeProvider, ModelContext } from "mcp-use/react";
import type { ViewConfig } from "mcp-use/react";

export const viewConfig: ViewConfig = {
  displayModes: ["inline", "fullscreen"],
  autoResize: true,
};

export default function ChartView() {
  const ctx = useToolContext<"generate-chart">();

  if (ctx.status === "pending") {
    return <ThemeProvider><p>Generating chart...</p></ThemeProvider>;
  }
  if (ctx.status === "error") {
    return <ThemeProvider><p>Error: {ctx.error?.message}</p></ThemeProvider>;
  }

  const { labels, values, title } = ctx.toolOutput;

  // Simple SVG bar chart
  const maxValue = Math.max(...values);
  const barWidth = 30;
  const barGap = 20;

  return (
    <ThemeProvider>
      <ModelContext content={`Chart: ${title} with ${labels.length} data points`}>
        <div style={{ padding: "20px" }}>
          <h2>{title}</h2>
          <svg width="300" height="200" style={{ border: "1px solid #ccc" }}>
            {labels.map((label, i) => {
              const barHeight = (values[i] / maxValue) * 150;
              const x = i * (barWidth + barGap) + 20;
              const y = 180 - barHeight;
              return (
                <g key={i}>
                  <rect x={x} y={y} width={barWidth} height={barHeight} fill="#007bff" />
                  <text x={x + barWidth / 2} y="195" textAnchor="middle" fontSize="12">
                    {label}
                  </text>
                  <text x={x + barWidth / 2} y={y - 5} textAnchor="middle" fontSize="10">
                    {values[i]}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
      </ModelContext>
    </ThemeProvider>
  );
}
```

**Verify:** No TypeScript errors: `npm run typecheck`.

### 4. Test Locally

```bash
npm run dev
# Inspector opens at http://127.0.0.1:3000/mcp/inspector
```

In Inspector:
1. Click **Tools** → **generate-chart**.
2. Choose **dataType**: `sales`.
3. Click **Call**.

**Verify:** View renders a bar chart with 3 bars and labels.

### 5. Hot-Reload

Edit `view.tsx` (e.g., change `fill="#007bff"` to `fill="#28a745"`). Save.

**Verify:** Chart color changes instantly in Inspector (no manual refresh).

## Common Issues

| Issue | Solution |
|-------|----------|
| View doesn't appear in Inspector | Check tool `view.name` exactly matches folder name (`views/chart-view/`) |
| TypeScript errors in `view.tsx` | Ensure `useToolContext` is imported from `mcp-use/react`, not `@mcp-use/react` |
| Chart renders but data is wrong | Check `structuredContent` matches `outputSchema`; mock data in tool callback |

## Next

- Add real data fetching (replace mock data with API call).
- Use CSS modules for styling (`view.css`).
- Add more views under `views/`.
- Deploy with `npm run deploy`.
- Read `../18-mcp-apps/01-what-are-mcp-apps.md` for comprehensive concepts.
