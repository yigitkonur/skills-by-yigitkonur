# Workflow: Streaming Chart Widget

**Goal:** ship a widget that renders an Apache ECharts visualisation while the LLM is still streaming the tool input. The widget reads `partialToolInput` and `isStreaming` from `useWidget` and re-renders the chart on every update — the user sees it draw progressively rather than waiting for the full JSON. Modeled on `mcp-use/mcp-chart-builder`.

## Prerequisites

- mcp-use 1.26.0 or newer.
- React 19, ECharts 5+.

## Layout

```
chart-mcp/
├── package.json
├── tsconfig.json
├── index.ts
└── resources/
    └── chart-display/
        ├── widget.tsx
        └── types.ts
```

## `package.json` (key deps)

```json
{
  "type": "module",
  "scripts": { "dev": "mcp-use dev", "build": "mcp-use build", "start": "mcp-use start" },
  "dependencies": {
    "mcp-use": "^1.26.0",
    "zod": "^4.0.0",
    "echarts": "^5.5.0",
    "react": "^19",
    "react-dom": "^19"
  }
}
```

## `index.ts`

```typescript
import { MCPServer, text, widget } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "chart-builder",
  version: "1.0.0",
  description: "ECharts visualizations that stream as the LLM writes them",
  baseUrl: process.env.MCP_URL || "http://localhost:3000",
});

server.tool(
  {
    name: "create-chart",
    description:
      "Create an interactive chart. Supports bar, line, pie, scatter, radar, " +
      "heatmap, and more. Pass a full ECharts option object as a JSON string. " +
      "The chart renders progressively as the JSON streams in.",
    schema: z.object({
      title: z.string().optional().describe("Chart title"),
      chartType: z
        .enum(["bar", "line", "pie", "scatter", "radar", "heatmap", "treemap", "sunburst", "gauge", "funnel"])
        .describe("Primary chart type"),
      option: z.string().describe(
        "Full ECharts option object as a JSON string. " +
          "Must include xAxis/yAxis/series for cartesian charts, or series for pie/radar/gauge."
      ),
    }),
    widget: {
      name: "chart-display",
      invoking: "Generating chart...",
      invoked: "Chart ready",
    },
  },
  async ({ title, chartType, option }) => {
    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(option);
    } catch {
      return text("Invalid ECharts option JSON.");
    }
    if (title && !parsed.title) parsed.title = { text: title };
    return widget({
      props: { chartType, option: parsed },
      output: text(`Created ${chartType} chart${title ? `: ${title}` : ""}`),
    });
  }
);

server.listen().then(() => console.log("Chart Builder running"));
```

## `resources/chart-display/types.ts`

```typescript
import { z } from "zod";

export const propSchema = z.object({
  chartType: z.string(),
  option: z.record(z.string(), z.unknown()),
});

export type ChartDisplayProps = z.infer<typeof propSchema>;
```

## `resources/chart-display/widget.tsx`

```tsx
import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";
import React, { useEffect, useRef } from "react";
import * as echarts from "echarts";
import { propSchema, type ChartDisplayProps } from "./types";

export const widgetMetadata: WidgetMetadata = {
  description: "Interactive chart powered by Apache ECharts",
  props: propSchema,
  exposeAsTool: false,
  metadata: {
    prefersBorder: true,
    invoking: "Generating chart...",
    invoked: "Chart ready",
  },
};

const ChartDisplay: React.FC = () => {
  const { props, isPending, isStreaming, partialToolInput, theme } =
    useWidget<ChartDisplayProps>();

  const elRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);

  // Pick the best option available: completed props if we have them,
  // otherwise the partial tool input as it streams.
  const getOption = (): Record<string, unknown> | null => {
    if (props?.option) return props.option as Record<string, unknown>;
    if (isStreaming && partialToolInput) {
      const partial = partialToolInput as Partial<ChartDisplayProps>;
      if (partial.option && typeof partial.option === "object") {
        return partial.option as Record<string, unknown>;
      }
    }
    return null;
  };

  // Initialise once, then setOption on every change. Try/catch swallows
  // the brief windows when the partial JSON is structurally invalid.
  useEffect(() => {
    if (!elRef.current) return;
    if (!chartRef.current) {
      chartRef.current = echarts.init(
        elRef.current,
        theme === "dark" ? "dark" : undefined,
        { renderer: "canvas" }
      );
    }
    const option = getOption();
    if (!option) return;
    try {
      chartRef.current.setOption(option, true);
    } catch {
      // Partial option mid-stream — ignore until next update.
    }
  }, [props, partialToolInput, theme]);

  // Resize on container changes.
  useEffect(() => {
    if (!chartRef.current) return;
    const ro = new ResizeObserver(() => chartRef.current?.resize());
    if (elRef.current) ro.observe(elRef.current);
    return () => ro.disconnect();
  }, []);

  // Re-init on theme change (echarts theme is set at construction).
  useEffect(() => {
    if (!chartRef.current || !elRef.current) return;
    chartRef.current.dispose();
    chartRef.current = echarts.init(
      elRef.current,
      theme === "dark" ? "dark" : undefined,
      { renderer: "canvas" }
    );
    const option = getOption();
    if (option) chartRef.current.setOption(option, true);
  }, [theme]);

  if (isPending && !isStreaming) {
    return <div className="p-6 h-96 bg-gray-100 dark:bg-gray-800 animate-pulse rounded" />;
  }

  return (
    <div className="p-4 bg-white dark:bg-gray-950 min-h-[200px]">
      {isStreaming && (
        <div className="flex items-center gap-1.5 mb-2 text-xs text-blue-500">
          <span className="h-2 w-2 rounded-full bg-blue-500 animate-pulse" />
          streaming
        </div>
      )}
      <div ref={elRef} style={{ width: "100%", height: 420 }} />
    </div>
  );
};

export default function Chart() {
  return (
    <McpUseProvider autoSize>
      <ChartDisplay />
    </McpUseProvider>
  );
}
```

## Run

```bash
npm install
npm run dev
# Inspector: http://localhost:3000/inspector
```

## Test

In the Inspector, call `create-chart`:

```json
{
  "title": "Quarterly Revenue",
  "chartType": "bar",
  "option": "{\"xAxis\":{\"data\":[\"Q1\",\"Q2\",\"Q3\",\"Q4\"]},\"yAxis\":{},\"series\":[{\"type\":\"bar\",\"data\":[120,200,150,180]}]}"
}
```

You'll see the chart render incrementally as the model streams the option JSON.

## Streaming-tool-props pattern

- `isStreaming` and `partialToolInput` are set while tool input is mid-stream.
- `props` is the final validated structured content after the tool returns.
- Render a skeleton while pending, best-effort render partial input while streaming, then render final props.
- Wrap partial rendering in `try/catch`; mid-stream JSON can be incomplete.

## See also

- Canonical: `../31-canonical-examples/03-mcp-chart-builder.md`
- Streaming props deep dive: `../18-mcp-apps/streaming-tool-props/`
- More widget types: `../31-canonical-examples/01-mcp-widget-gallery.md`
