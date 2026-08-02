# CSP Differences: MCP Apps vs. ChatGPT

*Read this when declaring CSP for a tool that targets both MCP Apps and ChatGPT.*

CSP metadata is translated between MCP Apps and ChatGPT protocols, but the terminology and merge order differ slightly.

## Terminology Mapping

| MCP Apps | ChatGPT Apps SDK | Purpose |
|-|-|-|
| `connectDomains` | `connectSources` | Fetch, XHR, WebSocket |
| `resourceDomains` | `scriptSources` + `styleSources` | CSS, JavaScript, images |
| `frameDomains` | `frameSources` | iframes, embeds |
| `baseUriDomains` | `baseUriSources` | `<base>` tag URIs |

mcp-use automatically translates between these when emitting both protocols.

## CSP Merge Order (Both Platforms)

CSP metadata is merged in this priority order (highest first):

1. **Author `view.csp`** on the tool definition (highest priority)
2. **Environment variables** (`CSP_CONNECT_DOMAINS`, `CSP_RESOURCE_DOMAINS`, etc., or `CSP_URLS` shortcut)
3. **MCP auto-append** — server origin added to `connectDomains`; assets origin added to `resourceDomains` (lowest priority)

**Same merge order applies to both MCP Apps and ChatGPT.**

## Example: Multi-Origin Tool

Server tool with external API + CDN:

```typescript
export const getData = server.tool(
  {
    name: "get-data",
    description: "Fetch data from multiple origins",
    outputSchema: z.object({ /* ... */ }),
    view: {
      name: "data-view",
      csp: {
        // Author declares required domains (highest priority)
        connectDomains: ["https://api.example.com"],
        resourceDomains: ["https://cdn.example.com"],
      },
    },
  },
  async () => {
    // Fetches are allowed by CSP
    const data = await fetch("https://api.example.com/data");
    return {
      content: [{ type: "text", text: "Data loaded" }],
      structuredContent: { /* uses cdn.example.com for images */ },
    };
  }
);
```

**MCP Apps resource emitted:**

```json
{
  "type": "text",
  "uri": "ui://views/data-view.html",
  "mimeType": "text/html;profile=mcp-app",
  "_meta": {
    "ui": {
      "csp": {
        "connectDomains": ["https://api.example.com", "https://myserver.com"],
        "resourceDomains": ["https://cdn.example.com", "https://myserver.com"]
      }
    }
  }
}
```

(Author domains first, then auto-appended server/assets origin.)

**ChatGPT metadata emitted simultaneously:**

```json
{
  "toolId": "get-data",
  "appMetadata": {
    "sandbox": {
      "connectSources": ["https://api.example.com", "https://myserver.com"],
      "scriptSources": ["https://cdn.example.com", "https://myserver.com"],
      "styleSources": ["https://cdn.example.com", "https://myserver.com"]
    }
  }
}
```

(ChatGPT combines CSS and scripts into separate `scriptSources` / `styleSources`; mcp-use maps `resourceDomains` to both.)

## Environment Variable Overrides

You can override author CSP via environment variables:

```bash
# Override all four categories uniformly
CSP_URLS=https://api.example.com,https://cdn.example.com

# Or specify each category
CSP_CONNECT_DOMAINS=https://api.example.com
CSP_RESOURCE_DOMAINS=https://cdn.example.com
CSP_FRAME_DOMAINS=https://embed.example.com
CSP_BASE_URI_DOMAINS=https://myserver.com
```

**Precedence:** Author `view.csp` > env vars > auto-append.

Example: If tool declares `connectDomains: ["https://api.example.com"]` and you set `CSP_CONNECT_DOMAINS=https://override.com`, the author value wins and `https://override.com` is ignored.

## Detection in Views (ChatGPT-Specific)

You can optionally detect the runtime and adjust fetch behavior (though usually unnecessary):

```typescript
import { useHostContext } from "mcp-use/react";

export default function DataView() {
  const hostContext = useHostContext();
  
  // Optional: adjust behavior based on client
  if (hostContext.client?.name === "ChatGPT") {
    // ChatGPT-specific behavior (rarely needed)
  }
  
  // But CSP always applies regardless of detection
}
```

**Note:** `client.name` is a hint; CSP enforcement is the authoritative mechanism.

## CSP Violations

If your view tries to fetch from an origin not in CSP:

**Browser console error:**

```
Refused to connect to 'https://blocked.com' because it violates the following Content Security Policy directive: "connect-src 'self' https://api.example.com https://myserver.com"
```

**Fix:** Add the origin to `view.csp.connectDomains` in the tool definition.

## See Also

- `references/18-mcp-apps/server-surface/05-csp-metadata.md` — full CSP API and merge rules
- `references/18-mcp-apps/anti-patterns.md` — "Missing or Wrong CSP" anti-pattern
- `canonical-anchor.md` — end-to-end example with CSP
