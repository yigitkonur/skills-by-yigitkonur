# Skybridge MIME Type

ChatGPT's legacy Apps SDK resource MIME is `text/html+skybridge`. With `type: "mcpApps"`, mcp-use builds Apps SDK metadata automatically; you do not set the MIME by hand or dual-register the widget.

## The two MIME variants

| Registration type | MIME | Resource shape |
|---|---|---|
| `mcpApps` | `text/html;profile=mcp-app` | UI resource with `_meta.ui.*` plus generated `openai/*` metadata for ChatGPT |
| `appsSdk` | `text/html+skybridge` | Legacy ChatGPT-only UI resource with `_meta["openai/*"]` metadata |

Both paths serve the same underlying HTML. Prefer `mcpApps` so the package can generate the portable metadata.

## How auto-emission works

When you register a widget with `type: "mcpApps"`:

```typescript
server.uiResource({
  type: "mcpApps",
  name: "weather-display",
  htmlTemplate: `...`,
  metadata: { /* unified */ },
});
```

mcp-use internally instantiates two adapters:

```typescript
import { McpAppsAdapter, AppsSdkAdapter } from "mcp-use/server";

const mcpAppsAdapter = new McpAppsAdapter();
const appsSdkAdapter = new AppsSdkAdapter();

const mcpAppsResource = mcpAppsAdapter.buildResourceMetadata(yourDefinition);
const appsSdkResource = appsSdkAdapter.buildResourceMetadata(yourDefinition);
const appsSdkToolMeta = appsSdkAdapter.buildToolMetadata(
  yourDefinition,
  "ui://widget/weather-display.html"
);
```

You don't construct these yourself; they run automatically when `type: "mcpApps"` is used.

The package uses both adapters to build protocol metadata, but normal code should still register one `type: "mcpApps"` widget.

## What `AppsSdkAdapter` does

For ChatGPT, the adapter:

1. Sets MIME type to `text/html+skybridge`.
2. Wraps metadata under `_meta["openai/*"]` keys.
3. Converts CSP camelCase to snake_case (`connectDomains` → `connect_domains`). See `04-csp-format-differences.md`.
4. Sets `openai/outputTemplate` to `ui://widget/<name>.html` so ChatGPT knows which template to render for tool results.
5. Maps invocation status: `invoking` → `openai/toolInvocation/invoking`, `invoked` → `openai/toolInvocation/invoked`.

Server-origin CSP enrichment is handled before registration for `type: "mcpApps"`; legacy `appsSdk` auto-registration has its own OpenAI-origin defaults.

## Side-by-side example

Source — what you write:

```typescript
server.uiResource({
  type: "mcpApps",
  name: "chart",
  htmlTemplate: `...`,
  metadata: {
    csp: { connectDomains: ["https://api.example.com"] },
    prefersBorder: true,
    invoking: "Generating chart...",
    invoked: "Chart generated",
    widgetDescription: "Displays chart data",
  },
});
```

What `McpAppsAdapter.buildResourceMetadata()` produces:

```json
{
  "mimeType": "text/html;profile=mcp-app",
  "_meta": {
    "ui": {
      "csp": { "connectDomains": ["https://api.example.com"] },
      "prefersBorder": true,
      "invoking": "Generating chart...",
      "invoked": "Chart generated"
    }
  }
}
```

What the Apps SDK adapter contributes across tool/resource metadata:

```json
{
  "mimeType": "text/html+skybridge",
  "_meta": {
    "openai/outputTemplate": "ui://widget/chart.html",
    "openai/toolInvocation/invoking": "Generating chart...",
    "openai/toolInvocation/invoked": "Chart generated",
    "openai/widgetPrefersBorder": true,
    "openai/widgetCSP": {
      "connect_domains": ["https://api.example.com"]
    },
    "openai/widgetDescription": "Displays chart data"
  }
}
```

Same source. Two correctly-shaped outputs.

## When you'd touch adapters directly

Almost never. The adapters are exposed for advanced custom registrations:

```typescript
import { McpAppsAdapter, AppsSdkAdapter } from "mcp-use/server";
```

Use them only if you're building a registration layer outside the standard `server.uiResource` API. For all normal cases, registration is sufficient.

## Related

- Why `mcpApps` is preferred over `appsSdk`: `05-dual-protocol-via-mcpapps.md`.
- CSP format details: `04-csp-format-differences.md`.
