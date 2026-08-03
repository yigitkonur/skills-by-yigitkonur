# CSP Metadata: Domains and Sandbox Permissions

*Read this when a View loads remote content, embeds frames, or requests browser capabilities.*

View security facts are declared on the bound tool's `view` field and emitted on the generated resource under `_meta.ui`. They apply to browser code in the sandboxed View, not to server-side tool callback traffic.

## Public Types in beta.66

The package root exports `ToolViewConfig` and `UiPermissions`. It does **not** export `McpUiResourceCsp` or `McpUiResourcePermissions`.

```typescript
import type { ToolViewConfig, UiPermissions } from "mcp-use";

type ViewCsp = ToolViewConfig["csp"];

const csp: ViewCsp = {
  connectDomains: ["https://api.example.com"],
  resourceDomains: ["https://cdn.example.com"],
  frameDomains: ["https://embed.example.com"],
  baseUriDomains: ["https://views.example.com"],
};

const permissions: UiPermissions = {
  camera: {},
  microphone: {},
  geolocation: {},
  clipboardWrite: {},
};
```

Inline `view.csp` and `view.permissions` objects are also inferred without standalone type aliases.

## CSP Categories

| Key | Browser activity |
|-|-|
| `connectDomains` | `fetch`, XHR, EventSource, WebSocket |
| `resourceDomains` | Scripts, styles, images, fonts, and other loaded assets |
| `frameDomains` | Nested frames and embeds |
| `baseUriDomains` | Allowed document base URI origins |

Declare only origins the View itself needs:

```typescript
server.tool(
  {
    name: "create-chart",
    inputSchema: z.object({ type: z.enum(["bar", "line"]) }),
    outputSchema: z.object({
      labels: z.array(z.string()),
      data: z.array(z.number()),
    }),
    view: {
      name: "chart-builder",
      csp: {
        connectDomains: ["https://api.example.com"],
        resourceDomains: ["https://cdn.example.com"],
        frameDomains: ["https://embed.example.com"],
      },
    },
  },
  handler
);
```

A server callback fetching `https://api.example.com` does not require View CSP. A `fetch()` executed by `view.tsx` does.

## Additive Merge

The framework builds every CSP category by concatenating three segments and removing duplicates in first-seen order:

1. Author values from `view.csp`
2. Environment values
3. Framework auto-appended origins

"Earlier wins" only determines duplicate ordering. Later sources are still added; author values do not replace the environment or automatic values.

### Environment Sources

```bash
CSP_CONNECT_DOMAINS=https://api.example.com,https://events.example.com
CSP_RESOURCE_DOMAINS=https://cdn.example.com
CSP_FRAME_DOMAINS=https://embed.example.com
CSP_BASE_URI_DOMAINS=https://views.example.com
```

`CSP_URLS` is a shortcut fallback for all four categories:

```bash
CSP_URLS=https://shared.example.com
```

For each category, a non-empty category-specific variable replaces `CSP_URLS` as that category's **environment segment**. It does not replace author or automatic entries.

### Automatic Origins

- Server origin from `MCP_URL` or the request → `connectDomains`
- WebSocket variant of the server origin in dev → `connectDomains`
- Explicit `MCP_ASSETS_URL` origin → `resourceDomains`
- Otherwise the server origin → `resourceDomains`

The emitted CSP always contains all four arrays, even when some are empty.

## Example Merge

Given:

```typescript
view: {
  name: "chart-builder",
  csp: {
    connectDomains: ["https://api.example.com"],
    resourceDomains: ["https://cdn.example.com"],
  },
}
```

```bash
MCP_URL=https://mcp.example.com
MCP_ASSETS_URL=https://assets.example.com/static
CSP_CONNECT_DOMAINS=https://events.example.com
CSP_RESOURCE_DOMAINS=https://fonts.example.com
```

The resource metadata includes:

```json
{
  "ui": {
    "csp": {
      "connectDomains": [
        "https://api.example.com",
        "https://events.example.com",
        "https://mcp.example.com"
      ],
      "resourceDomains": [
        "https://cdn.example.com",
        "https://fonts.example.com",
        "https://assets.example.com"
      ],
      "frameDomains": [],
      "baseUriDomains": []
    }
  }
}
```

This object appears under the resource's `_meta`; the snippet shows only its `ui` value.

## Sandbox Permissions

`permissions` is an object whose key presence requests a capability. Values are empty objects, not booleans and not iframe `sandbox` tokens.

```typescript
import type { UiPermissions } from "mcp-use";

const permissions: UiPermissions = {
  camera: {},
  microphone: {},
  geolocation: {},
  clipboardWrite: {},
};
```

Only these four standard keys exist in beta.66. A host may deny a request, so feature-detect and handle denial in the View.

```typescript
server.tool(
  {
    name: "scan-qr-code",
    inputSchema: z.object({}),
    outputSchema: z.object({ decoded: z.string() }),
    view: {
      name: "qr-scanner",
      permissions: { camera: {} },
    },
  },
  handler
);
```

## Domain and Border Metadata

```typescript
view: {
  name: "oauth-view",
  domain: "host-approved-sandbox-name",
  prefersBorder: true,
}
```

- `domain` is a dedicated sandbox-origin hint. Its format and validation are host-dependent; it may not be a URL. If omitted, the host chooses its default sandbox origin.
- `prefersBorder` is a request, not a guarantee. Set an explicit boolean when the visual boundary matters.

For ChatGPT-specific submission and compatibility requirements, follow `../chatgpt-apps/01-dual-protocol.md` and `../chatgpt-apps/03-csp-differences.md`. Do not add ChatGPT-only resource extensions to standard `ToolViewConfig` snippets.

## Inspect the Emitted Resource

Read `ui://views/<name>.html` and inspect the content item's `_meta.ui`. The same resource metadata is also advertised on the resource listing.

```bash
npx mcp-use client connect dev http://localhost:3000/mcp
npx mcp-use client dev resources read "ui://views/chart-builder.html" --json
```

Expected location:

```text
result.contents[0]._meta.ui.csp
result.contents[0]._meta.ui.permissions
result.contents[0]._meta.ui.domain
result.contents[0]._meta.ui.prefersBorder
```

## Cross-References

- Tool binding and wire metadata: `01-tool-view-field.md`
- Manifest and validation: `02-register-views-and-folder-conventions.md`
- Asset origins and synthesized HTML: `04-assets-mcp-url-and-serving.md`
- CSP troubleshooting: `../../27-troubleshooting/05-csp-violations.md`
