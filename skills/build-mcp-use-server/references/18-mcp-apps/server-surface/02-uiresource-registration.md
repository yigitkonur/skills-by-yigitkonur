# Registering UI Resources

`server.uiResource(...)` registers a widget entry point with the server. The host fetches the resulting HTML and loads it into the iframe sandbox. mcp-use generates the protocol-specific metadata for both MCP Apps and ChatGPT Apps from a single registration.

## Signature

```typescript
server.uiResource({
  type: "mcpApps" | "rawHtml" | "remoteDom" | "appsSdk",  // appsSdk deprecated
  name: string,
  htmlTemplate?: string,  // mcpApps/appsSdk
  htmlContent?: string,   // rawHtml
  script?: string,        // remoteDom
  metadata?: Record<string, unknown>,
  appsSdkMetadata?: Record<string, unknown>,
  props?: WidgetProps,
  description?: string,
  title?: string,
  exposeAsTool?: boolean,
  toolOutput?: CallToolResult | ((params) => CallToolResult),
});
```

## Type variants

| Type | When to use | Status |
|---|---|---|
| `mcpApps` | Default for new widgets. Dual-protocol — works in MCP Apps clients **and** ChatGPT. | **Recommended** |
| `rawHtml` | Plain HTML you author yourself, no MCP Apps protocol — no `useWidget`, no postMessage RPC. | Niche |
| `remoteDom` | Remote DOM rendering (server-driven UI tree). | Advanced |
| `appsSdk` | ChatGPT Apps SDK only, snake_case CSP, `openai/*` keys. | **Deprecated** |

For new code, use `mcpApps`. See `../chatgpt-apps/06-deprecation-of-appssdk.md` for the deprecation rationale and `../../28-migration/04-appssdk-to-mcpapps.md` for migration steps.

## Common case — `type: "mcpApps"`

```typescript
import { MCPServer } from "mcp-use/server";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  baseUrl: process.env.MCP_URL || "http://localhost:3000",
});

server.uiResource({
  type: "mcpApps",
  name: "weather-display",
  htmlTemplate: `
    <!DOCTYPE html>
    <html>
      <head><meta charset="UTF-8"><title>Weather</title></head>
      <body>
        <div id="root"></div>
        <script type="module" src="/resources/weather-display.js"></script>
      </body>
    </html>
  `,
  metadata: {
    csp: {
      connectDomains: ["https://api.weather.com"],
      resourceDomains: ["https://cdn.weather.com"],
      scriptDirectives: ["'unsafe-eval'"],   // required for bundled React runtime
    },
    prefersBorder: true,
    autoResize: true,
    invoking: "Fetching weather...",
    invoked: "Weather loaded",
    widgetDescription: "Displays current weather conditions",  // ChatGPT-specific
  },
});
```

This single call generates:
- For MCP Apps clients — MIME `text/html;profile=mcp-app`, camelCase CSP, standard `_meta.ui.*` keys.
- For ChatGPT — MIME `text/html+skybridge`, snake_case CSP, `openai/*` keys.

## When to use `uiResource` directly vs auto-discovery

mcp-use auto-discovers widgets in `resources/<name>/widget.tsx`. For those, you do **not** call `server.uiResource()` — the framework registers them at startup using `widgetMetadata` from the file (see `06-widget-metadata-export.md` and `07-resources-folder-conventions.md`).

Call `server.uiResource()` directly when:
- You're shipping a non-React HTML widget (no `widget.tsx`).
- You need to override the auto-discovered registration (custom `htmlTemplate`).
- You're writing a `rawHtml` or `remoteDom` resource.
- You're scaffolding programmatically.

## `exposeAsTool: true` — auto-tool registration

When `exposeAsTool: true`, mcp-use registers the widget itself as a callable tool. The tool's input schema comes from `props`. Skip this and write a custom tool when you need server-side data fetching/transformation before rendering.

```typescript
server.uiResource({
  type: "mcpApps",
  name: "greeting-card",
  htmlTemplate: `...`,
  props: {
    name: { type: "string", required: true },
    greeting: { type: "string", required: true },
  },
  exposeAsTool: true,  // becomes a callable tool named "greeting-card"
});
```

## CSP and metadata details

Live in dedicated pages:
- CSP fields and the camelCase/snake_case mapping: `05-csp-metadata.md`.
- The full `metadata` object shape (when authoring widgets in `resources/`): `06-widget-metadata-export.md`.
- `baseUrl` injection into CSP: `04-baseurl-and-asset-serving.md`.

## Don't pass `appsSdkMetadata` for new code

`type: "appsSdk"` requires `appsSdkMetadata` with `openai/*` keys. `type: "mcpApps"` accepts unified `metadata`. You **may** pass `appsSdkMetadata` alongside `metadata` on `mcpApps` to override ChatGPT-specific keys, but prefer encoding everything in `metadata` so both protocols stay in sync.
