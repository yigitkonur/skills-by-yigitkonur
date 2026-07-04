# `baseUrl` and Asset Serving

Widgets are HTML/JS that the host loads from a URL. Telling mcp-use the canonical public URL of your server is the difference between "works locally" and "works in production".

## What `baseUrl` controls

| Concern | Why it needs `baseUrl` |
|---|---|
| Widget HTML asset URLs | The `htmlTemplate` references bundled JS like `/resources/foo.js`. The host needs absolute URLs to load these. |
| CSP auto-injection | `baseUrl` origin is auto-added to `connectDomains`, `resourceDomains`, and `baseUriDomains` so the widget can call back to the server. |
| `<Image src="/..." />` resolution | The component prepends `baseUrl` to `/`-rooted paths so relative assets work in deployed builds. |
| Public files (`public/`) | Served at `${baseUrl}/mcp-use/public/...`. |

## Precedence

mcp-use resolves the base URL in this order:

1. `MCPServer({ baseUrl })` — explicit constructor arg.
2. `MCP_URL` env var — picked up automatically.
3. Falls back to `http://localhost:<port>` for local dev only.

```typescript
import { MCPServer } from "mcp-use/server";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  baseUrl: process.env.MCP_URL || "http://localhost:3000",
});
```

## Env vars

| Var | Purpose |
|---|---|
| `MCP_URL` | Public base URL for widget assets and the server itself. Required for production. |
| `CSP_URLS` | Comma-separated list of additional origins to whitelist in widget CSP. Required when widget assets and API live on different domains. |

```sh
MCP_URL=https://my-server.example.com
CSP_URLS=https://api.example.com,https://cdn.example.com
```

## Separate asset/API origins

`mcp-use@1.26.0` does not define an `MCP_SERVER_URL` env var. If a widget must call APIs on another origin, keep `MCP_URL` pointed at the public MCP server URL and add extra asset/API origins to `CSP_URLS` or `metadata.csp.connectDomains` / `resourceDomains`.

```sh
MCP_URL=https://mcp-api.example.com
CSP_URLS=https://cdn.example.com,https://api.example.com
```

The widget's `mcp_url` comes from `window.__mcpPublicUrl`, which is derived from the configured server base URL.

## Common deploy pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| Widget renders empty / 404 in network tab | `baseUrl` is `localhost` in production | Set `MCP_URL` to public origin |
| Widget loads but `fetch` calls fail with CSP errors | API origin not in `connectDomains` | Add to `CSP_URLS` env or `metadata.csp.connectDomains` |
| Images load locally but break in deploy | Hardcoded `http://localhost:3000` in `<img src>` | Use `<Image src="/..." />` from `mcp-use/react` |
| Widget JS loads but `useWidget().callTool()` fails | Public server origin missing or blocked by CSP | Set `MCP_URL` to the public server origin and allow required domains |
| Mixed-content warning in ChatGPT | `baseUrl` is `http://` | ChatGPT requires HTTPS — see `../chatgpt-apps/01-protocol-overview.md` |

## Don't hardcode origins inside widgets

Widget code should never reference `http://localhost:3000` or a production URL directly. Use:

- `useWidget().mcp_url` for API calls.
- `<Image src="/foo.png" />` for assets in `public/`.

Both honor the deployment configuration automatically.

## Related

- CSP fields and how `baseUrl` is auto-injected: `05-csp-metadata.md`.
- The `<Image />` component: `../widget-react/05-image-component.md`.
- Production deployment checklist: `../../25-deploy/`.
