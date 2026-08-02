# CSP Metadata: Domains and Sandbox Permissions

*Read this when you need to declare which third-party domains your view uses, set sandbox permissions, or troubleshoot CSP violations.*

Views operate in isolated iframes with a strict Content Security Policy (CSP). You declare which domains the view needs to access via the tool's `view` field, environment variables, or auto-append defaults. The framework merges these three sources into a single CSP object sent to the host.

## CSP Structure

CSP has four domain categories:

```typescript
import type { McpUiResourceCsp } from "mcp-use";

const csp: McpUiResourceCsp = {
  connectDomains: ["https://api.example.com"],      // fetch, XHR, WebSocket
  resourceDomains: ["https://cdn.example.com"],     // CSS, scripts, images
  frameDomains: ["https://embed.example.com"],      // iframes, embeds
  baseUriDomains: ["https://myserver.example.com"],  // base URI (rarely used)
};
```

## Three-Tier Merge Order (High → Low Priority)

CSP is merged from three sources in this order (highest priority first):

### 1. Author Declaration (Tool `view.csp`)

Declared directly on the tool definition:

```typescript
server.tool(
  {
    name: "search-products",
    description: "Search products",
    inputSchema: z.object({ query: z.string() }),
    outputSchema: productSchema,
    view: {
      name: "product-search",
      csp: {
        connectDomains: ["https://api.example.com"],
        resourceDomains: ["https://cdn.example.com"],
      },
    },
  },
  handler
);
```

### 2. Environment Variables

Set at deployment time:

```bash
# Per-category
CSP_CONNECT_DOMAINS=https://api.example.com,https://analytics.example.com
CSP_RESOURCE_DOMAINS=https://cdn.example.com
CSP_FRAME_DOMAINS=https://embed.example.com
CSP_BASE_URI_DOMAINS=https://myserver.example.com

# Or shortcut (all four categories)
CSP_URLS=https://api.example.com,https://cdn.example.com,https://embed.example.com
```

**Precedence within env vars:** Category-specific vars override `CSP_URLS`.

### 3. Framework Auto-Append (Lowest Priority)

The framework automatically appends:
- `MCP_URL` → `connectDomains` (so views can reach the server)
- `MCP_ASSETS_URL` → `resourceDomains` (so views can load assets)

If `MCP_ASSETS_URL` is not set, the server origin is used instead.

## Typical Flow

```bash
# Production deployment

# Set server & asset origins
export MCP_URL=https://myserver.com
export MCP_ASSETS_URL=https://cdn.myserver.com

# Set third-party domains via env (or declare in tool.view.csp)
export CSP_CONNECT_DOMAINS=https://api.thirdparty.com
export CSP_RESOURCE_DOMAINS=https://images.thirdparty.com

# Server starts; CSP is merged at resource emission time
# Resulting CSP includes:
# - Author domains (from tool.view.csp) — highest priority
# - Env-set domains (CSP_* vars)
# - Auto-appended: https://myserver.com (connect), https://cdn.myserver.com (resource)
```

## Example: Multi-Domain View

```typescript
// index.ts
const chartResultsSchema = z.object({
  labels: z.array(z.string()),
  data: z.array(z.number()),
});

server.tool(
  {
    name: "create-chart",
    description: "Create an interactive chart",
    inputSchema: z.object({ type: z.enum(["bar", "line"]) }),
    outputSchema: chartResultsSchema,
    view: {
      name: "chart-builder",
      description: "Interactive chart editor",
      csp: {
        connectDomains: ["https://analytics.stripe.com"],  // Stripe analytics
        resourceDomains: ["https://fonts.googleapis.com"],  // Google Fonts
        frameDomains: ["https://charts.example.com"],       // Chart iframe
      },
    },
  },
  async ({ type }) => ({
    content: [{ type: "text", text: `Created ${type} chart` }],
    structuredContent: { labels: ["A", "B"], data: [10, 20] },
  })
);

export default server;
```

## Environment Variable Examples

### Basic Setup

```bash
mcp-use deploy --env MCP_URL=https://myapp.example.com
mcp-use deploy --env CSP_CONNECT_DOMAINS=https://api.example.com
```

### CDN + Multiple Third Parties

```bash
export MCP_URL=https://server.example.com
export MCP_ASSETS_URL=https://cdn.example.com
export CSP_CONNECT_DOMAINS=https://api.stripe.com,https://api.anthropic.com
export CSP_RESOURCE_DOMAINS=https://images.example.com,https://fonts.googleapis.com
export CSP_FRAME_DOMAINS=https://youtube.com,https://maps.google.com
```

### Using CSP_URLS Shortcut

```bash
# Adds to all four categories (rarely used; prefer category-specific)
export CSP_URLS=https://example.com,https://api.example.com
```

## Verifying Emitted CSP

The framework emits CSP on the view resource's `_meta.ui.csp` field. Inspect via:

```bash
# Using mcp-use client CLI
mcp-use client local resources read ui://views/chart-builder.html | jq '._meta.ui.csp'

# Or via direct HTTP
curl -s http://localhost:3000/mcp/resources/read -d '{"uri":"ui://views/chart-builder.html"}' | jq '.[0]._meta.ui.csp'
```

Expected output (merged from all three sources):

```json
{
  "_meta": {
    "ui": {
      "csp": {
        "connectDomains": [
          "https://api.example.com",     (from author)
          "https://analytics.stripe.com", (from author)
          "https://myserver.example.com"  (auto-appended MCP_URL)
        ],
        "resourceDomains": [
          "https://fonts.googleapis.com",  (from author)
          "https://cdn.example.com"        (auto-appended MCP_ASSETS_URL)
        ],
        "frameDomains": ["https://charts.example.com"]
      }
    }
  }
}
```

## Sandbox Permissions

Declare permissions alongside CSP:

```typescript
server.tool(
  {
    name: "editor",
    description: "Edit content",
    inputSchema: z.object({ content: z.string() }),
    outputSchema: z.object({ saved: z.boolean() }),
    view: {
      name: "editor",
      csp: { connectDomains: ["https://api.example.com"] },
      permissions: ["allow-same-origin", "allow-scripts", "allow-forms"],
    },
  },
  handler
);
```

Common permissions:
- `allow-same-origin` — Access cookies & localStorage
- `allow-scripts` — Execute JavaScript
- `allow-forms` — Submit forms
- `allow-modals` — Show dialogs
- `allow-popups` — Open windows

## Troubleshooting

See **references/27-troubleshooting/05-csp-violations.md** for diagnosing CSP block messages and resolver strategies.

## Cross-References

- **Canonical tool + view example:** references/18-mcp-apps/canonical-anchor.md
- **View folder conventions:** references/18-mcp-apps/server-surface/02-register-views-and-folder-conventions.md
- **Asset serving and MCP_URL/MCP_ASSETS_URL:** references/18-mcp-apps/server-surface/04-assets-mcp-url-and-serving.md
- **CSP violation debugging:** references/27-troubleshooting/05-csp-violations.md
