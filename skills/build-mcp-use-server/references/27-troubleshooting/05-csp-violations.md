# CSP Violations

*Read this when a View iframe reports a blocked connection, asset, frame, or base URL.*

View CSP is declared on the tool's `view` field. Do not configure it through v1 `widgetMetadata` or a manually registered UI resource.

## Read the browser error literally

Extract the blocked URL and directive:

```text
Refused to connect to 'https://api.example.com/data' because it violates
"connect-src 'self' https://mcp.example.com".
```

The blocked origin is `https://api.example.com`; the relevant category is `connectDomains`.

## Map directives to v2 fields

| Browser directive or activity | v2 `view.csp` field |
|---|---|
| `fetch`, XHR, EventSource, WebSocket; `connect-src` | `connectDomains` |
| scripts, styles, images, fonts; related resource directives | `resourceDomains` |
| iframes and embeds; `frame-src` | `frameDomains` |
| `<base href>`; `base-uri` | `baseUriDomains` |

Add origins, not full request paths, unless the host/spec explicitly permits a more specific source expression.

## Declare CSP on the tool

```typescript
export const dashboard = server.tool(
  {
    name: "show-dashboard",
    description: "Load and display the account dashboard.",
    outputSchema: DashboardSchema,
    view: {
      name: "dashboard",
      csp: {
        connectDomains: ["https://api.example.com"],
        resourceDomains: ["https://cdn.example.com"],
        frameDomains: ["https://embed.example.com"],
      },
    },
  },
  callback,
);
```

See `references/18-mcp-apps/server-surface/05-csp-metadata.md`.

## Use environment policy when appropriate

The runtime merges author policy with CSP environment variables and auto-appended MCP origins:

```bash
CSP_CONNECT_DOMAINS=https://api.example.com
CSP_RESOURCE_DOMAINS=https://cdn.example.com
CSP_FRAME_DOMAINS=https://embed.example.com
CSP_BASE_URI_DOMAINS=https://app.example.com
```

`CSP_URLS` adds listed origins to all four categories and is therefore broader. Prefer category-specific variables when the requirement is known.

## Understand the merge

The effective policy combines:

1. author `view.csp`;
2. `CSP_*_DOMAINS` or `CSP_URLS`; and
3. automatically added MCP and asset origins.

`MCP_URL` contributes the MCP origin to `connectDomains`. The assets origin contributes to `resourceDomains`. An incorrect public `MCP_URL` or `MCP_ASSETS_URL` can therefore produce a production-only violation.

## Separate CSP from server CORS

A successful CSP check does not mean the external API will accept the request. The destination may still reject it with CORS. Conversely, permissive server CORS does not allow the View iframe to reach an origin absent from View CSP.

Debug in order:

1. CSP must allow the browser to send the request.
2. Destination CORS must allow the View origin to read the response.
3. Authentication and application authorization must accept it.

## Development-only failures

`mcp-use dev` uses Vite and HMR. The framework adds the serving origin and WebSocket variant needed for HMR. If development CSP still blocks HMR, verify that the View is served through the normal dev command and that the public/tunnel origin is correct; do not add arbitrary wildcard WebSocket origins.

## Production-only failures

Check:

- the deployed MCP origin in `MCP_URL`;
- the CDN/assets origin in `MCP_ASSETS_URL`;
- redirects to a different origin;
- fonts, CSS, images, and scripts loaded by third-party packages; and
- iframe providers that use more than one origin.

Use `mcp-use screenshot` or the Inspector with production-like CSP enforcement after deployment. See `references/23-debug/03-view-debugging.md`.

## Do not weaken policy to hide the error

Do not add every origin to `CSP_URLS`, declare broad wildcards, or attempt to enable `unsafe-inline` just to make a blank View render. Add the smallest exact origins required by the View's behavior.

## Verification loop

1. Reproduce the violation in the Inspector or target host.
2. Record directive and blocked origin.
3. Add it to the narrow matching category.
4. Restart `mcp-use dev` or rebuild/redeploy.
5. Hard-refresh the host iframe.
6. Confirm the original console violation is gone and no new violation replaces it.

For non-CSP rendering failures, return to `references/27-troubleshooting/04-view-rendering-issues.md`.