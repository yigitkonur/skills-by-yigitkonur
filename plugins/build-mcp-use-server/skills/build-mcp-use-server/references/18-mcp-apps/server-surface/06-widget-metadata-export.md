# `widgetMetadata` Export

Every auto-discovered widget exports a named `widgetMetadata` constant from its `widget.tsx`. mcp-use reads this at startup to register the widget, generate types, and configure the host.

## Shape

```typescript
import type { WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

const propSchema = z.object({
  city: z.string().describe("City name"),
  temperature: z.number().describe("Temperature in Celsius"),
});

export const widgetMetadata: WidgetMetadata = {
  title: "Weather Display",
  description: "Displays current weather conditions",
  props: propSchema,
  exposeAsTool: false,
  metadata: {
    csp: { connectDomains: ["https://api.weather.com"] },
    prefersBorder: true,
    autoResize: true,
    invoking: "Loading weather...",
    invoked: "Weather loaded",
    widgetDescription: "Interactive weather card",
    domain: "https://weather.example.com",
  },
};
```

## Field reference

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | `string` | No | Human-readable widget title. |
| `description` | `string` | No | LLM-facing prose. Tells the model when to invoke this widget. Surfaces as the tool's description when `exposeAsTool: true`. |
| `props` | `ZodSchema` or `InputDefinition[]` | No | The shape of `useWidget().props`. Used for type generation, runtime validation, and tool-input schema if `exposeAsTool: true`. |
| `inputs` / `schema` | `ZodSchema` or `InputDefinition[]` | No | Deprecated aliases for `props`. |
| `toolOutput` | `CallToolResult` or `(params) => CallToolResult` | No | Model-visible output for auto-registered widgets. |
| `exposeAsTool` | `boolean` | No | When `true`, mcp-use auto-registers the widget as a callable tool with `props` as the input schema. When `false`, wire it through a custom tool's `widget` config. Set this explicitly. |
| `metadata` | `WidgetMetadata.metadata` | No | Host configuration — CSP, prefersBorder, autoResize, invoking/invoked, ChatGPT-specific overrides. |
| `appsSdkMetadata` | `AppsSdkMetadata` | No | Legacy ChatGPT-only metadata. Prefer unified `metadata` for new widgets. |

## The `metadata` object

```typescript
interface WidgetMetadataMetadata {
  csp?: {
    connectDomains?: string[];
    resourceDomains?: string[];
    baseUriDomains?: string[];
    frameDomains?: string[];
    redirectDomains?: string[];
    scriptDirectives?: string[];
    styleDirectives?: string[];
  };
  prefersBorder?: boolean;            // host draws a border/frame
  autoResize?: boolean;               // MCP Apps clients auto-size widget height
  widgetDescription?: string;         // ChatGPT-specific extra description
  domain?: string;                    // ChatGPT widget domain
  invoking?: string;                  // status text while tool runs
  invoked?: string;                   // status text after tool completes
}
```

| Field | Applies to | Notes |
|---|---|---|
| `csp` | Both | See `05-csp-metadata.md`. Always camelCase. |
| `prefersBorder` | Both | `true` for cards/panels; `false` for fullscreen/immersive. |
| `autoResize` | MCP Apps | Host auto-fits widget height. Pair with `<McpUseProvider autoSize />`. |
| `widgetDescription` | ChatGPT | Extra prose ChatGPT shows alongside the widget context. |
| `domain` | ChatGPT | Custom widget domain attribution. |
| `invoking` / `invoked` | Both | Status text. Auto-defaults to `"Loading {name}..."` and `"{name} ready"`. |

## Why `description` matters

The `description` field is the LLM's guidance for when to call the underlying tool — especially when `exposeAsTool: true`. Be specific:

- Bad: `"Display data"`.
- Good: `"Interactive product search results with filtering and sorting. Shows product cards with images, prices, and ratings. Use when the user wants to compare or filter products."`

## Type generation

When you run `mcp-use dev`, types are extracted from `widgetMetadata.props` into `.mcp-use/tool-registry.d.ts`. This gives `useCallTool("name")` IntelliSense for inputs and outputs generated from registered server tools.

If you skip `mcp-use dev`, run `npx mcp-use generate-types` after schema changes.

## What's NOT in `widgetMetadata`

- The widget component itself — that's the **default export**.
- The tool's name, schema, or handler — those live on the linked tool's `server.tool()` registration (see `03-tool-widget-config.md`).
- Server-side runtime config (port, baseUrl) — that's `MCPServer({ ... })`.

## Minimum viable export

```typescript
export const widgetMetadata: WidgetMetadata = {
  description: "...",
  props: z.object({}),
  exposeAsTool: false,
};
```

Everything else has sensible defaults. Fill in `metadata.csp` when you need external origins, and `metadata.prefersBorder` when the visual fits.
