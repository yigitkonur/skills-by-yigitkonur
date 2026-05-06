# Connection Settings

Each Inspector connection is configured from the dashboard's **Connect** form. Most fields persist to `localStorage` and survive reloads.

## Connection types

| Type | Behavior | Use when |
|---|---|---|
| **Direct** | Browser → server, no intermediary. Default. | Local dev, public endpoints, anywhere CORS is open. |
| **Via Proxy** | Browser → `/inspector/api/proxy` → server. | Corporate proxies, CORS-blocked endpoints, network policy requires intermediary. |
| **Auto-Switch** | Try Direct, fall back to Via Proxy on failure. | Unsure which works; multi-environment setups. |

Toggle Auto-Switch from the **Connection Type** dropdown in the form.

## Transport

The inspector negotiates transport automatically from the URL scheme but exposes an explicit override in the form:

| Transport | URL scheme | Notes |
|---|---|---|
| `http` (Streamable HTTP) | `http://` / `https://` | Default for HTTP endpoints. |
| `sse` | `http://` / `https://` | Older SSE-only servers. |

Saved as `transportType` in the connection JSON.

## Server display name

Each saved connection has an editable **display name** (alias) shown in the dashboard, server list, header, command palette, and server picker. Edit from the connection form.

Changing **only** the display name updates labels everywhere **without** disconnecting or clearing tokens. Connection-affecting fields (URL, headers, OAuth, transport) trigger a reconnect on save.

## Advanced timeouts

| Field | Default | Meaning |
|---|---|---|
| Request Timeout | `10000` ms | Max time for a single RPC. |
| Maximum Total Timeout | `60000` ms | Max time for a full operation including retries and progress. |
| Reset Timeout on Progress | `true` | Resets request timer when the server sends a progress notification. |
| Inspector Proxy Address | `${origin}/inspector/api/proxy` | Endpoint for Via Proxy mode. Override only if mounted at a non-default path. |

## OAuth 2.0

For servers that require OAuth, click **Authentication** in the connection form.

### Setup

1. Enter **Client ID**.
2. Enter **Scope** (space-separated).
3. **Save**.

### Flow

The inspector enters states in this order:

| State | What it means |
|---|---|
| Connecting | Initial connection attempt |
| Pending Auth | Server returned 401 + auth URL; waiting for user to start flow |
| Authenticating | OAuth flow in progress (popup or redirect) |
| Ready | Authenticated, connected |
| Failed | Auth or connection failed; surfaced as toast with error reason |

When state hits **Pending Auth**, click **Authenticate** on the server card. The flow opens in the **current tab** (single-tab redirect; v3.0.1+) and returns to the inspector with `sessionStorage`-restored config so auto-reconnect works without `?autoConnect`. If a popup blocker bites, use the **open auth page** fallback link.

Tokens persist to `localStorage` keyed by server ID.

## Custom headers

Add HTTP headers attached to every request to the MCP server.

1. Click **Custom Headers** in the connection form.
2. **Add** → enter name + value.
3. **Save**.

Common headers:

| Header | Use |
|---|---|
| `Authorization: Bearer <token>` | API tokens |
| `X-API-Key: <key>` | Custom auth |
| `X-API-Version: v2` | Versioning |
| `X-Request-ID: <uuid>` | Tracing |

Values are masked behind a dot pattern by default; click the eye icon to reveal.

## Configuration import / export

### Copy Config

Export the current connection as JSON to clipboard. Schema:

```json
{
  "url": "https://mcp.example.com/mcp",
  "transportType": "http",
  "connectionType": "Direct",
  "headers": {
    "Authorization": "Bearer token123"
  },
  "requestTimeout": 10000,
  "resetTimeoutOnProgress": true,
  "maxTotalTimeout": 60000,
  "oauth": {
    "clientId": "your-client-id",
    "scope": "read write"
  }
}
```

### Paste Config

Paste a copied JSON config into the **URL** field. The form auto-populates every setting. Use this to share configs across teammates or instances; pair with secure-channel handoff for tokens.

## Connection status indicators

| Indicator | Meaning |
|---|---|
| Green | Connected, ready |
| Yellow | Connecting or authenticating |
| Red | Connection failed |
| Gray | Disconnected |

Hover for detailed status.

## See also

- `02-cli.md` — passing connection settings via CLI flags.
- `04-url-parameters.md` — driving connection state via URL.
- `11-protocol-toggle-and-csp-mode.md` — widget-specific debug toggles.
