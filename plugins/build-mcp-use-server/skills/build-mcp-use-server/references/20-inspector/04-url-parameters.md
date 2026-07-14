# URL Parameters

The Inspector reads URL query parameters to deep-link into a server, tab, or auto-connection. Use these for shareable debug links, embeds, and CLI handoffs.

## Parameters

| Parameter | Purpose | Values |
|---|---|---|
| `server` | Select connected server by ID, or open + connect to a URL | Connection ID (URL) or HTTP(S) URL |
| `autoConnect` | Open Inspector and connect to a server automatically | URL string or URL-encoded JSON config |
| `tab` | Open a specific tab on load | `tools` `prompts` `resources` `chat` `sampling` `elicitation` `notifications` `playground` |
| `tunnelUrl` | Tunnel subdomain or URL (preserved when navigating) | URL string — set by CLI, rarely manual |
| `embedded` | Run in embedded mode (reduced chrome, e.g. for iframes) | `true` |
| `embeddedConfig` | Embedded-mode styling | URL-encoded JSON |

## `server`

Select an already-connected server by its connection ID (the server URL). If the value is an HTTP(S) URL **and** no matching connection exists, the Inspector treats it as `autoConnect`: it connects, then selects.

```text
# Select existing connection by ID
/?server=https://mcp.example.com/mcp

# Open and connect to a new server (alias for autoConnect when not connected)
/?server=https://new-server.com/mcp
```

## `autoConnect`

Opens the Inspector and connects automatically. Two forms.

### Plain URL

```text
/?autoConnect=https://mcp.example.com/mcp
```

### JSON config (URL-encode the value)

```json
{
  "url": "https://mcp.example.com/mcp",
  "name": "My Server",
  "transportType": "sse"
}
```

Supported JSON fields:

| Field | Type | Notes |
|---|---|---|
| `url` | string | **Required** |
| `name` | string | Display alias |
| `transportType` | `"http"` \| `"sse"` | |
| `connectionType` | `"Direct"` \| `"Via Proxy"` | |
| `customHeaders` | object | `{ "Authorization": "Bearer …" }` |
| `auth` | object | OAuth tokens |
| `requestTimeout` | number | ms |
| `resetTimeoutOnProgress` | boolean | |
| `maxTotalTimeout` | number | ms |

## `tab`

Force a specific tab on load.

```text
/?tab=tools
```

Combine with `server` or `autoConnect`:

```text
/?server=https://mcp.example.com/mcp&tab=tools
```

The active tab is reflected back into the URL, so a refresh restores the same tab.

## `tunnelUrl`

Used with the CLI tunnel; stores the tunnel subdomain or URL and is preserved when navigating. Typically set by the Inspector or CLI; you rarely set it manually.

## `embedded`

Render the Inspector in embedded mode (iframe-friendly chrome).

```text
/?embedded=true
```

Pair with `MCP_INSPECTOR_FRAME_ANCESTORS` (env var) to whitelist the embedding origin.

## `embeddedConfig`

URL-encoded JSON for embedded-mode appearance.

```json
{ "backgroundColor": "#f5f5f5", "padding": "16px" }
```

## Example URLs

Auto-connect to a server:

```text
https://inspector.mcp-use.com/inspect?autoConnect=https://your-server.com/mcp
```

Auto-connect, open Tools tab:

```text
https://inspector.mcp-use.com/inspect?server=https://your-server.com/mcp&tab=tools
```

Embedded, auto-connect, Tools tab:

```text
https://inspector.mcp-use.com/inspect?embedded=true&autoConnect=https://your-server.com/mcp&tab=tools
```

## Tips

- Encode JSON values with `encodeURIComponent`. Browsers tolerate raw `:` and `,` but `&`, `+`, and `#` will break parsing.
- For internal docs and READMEs, prefer `autoConnect=<url>` over the JSON form for legibility.
- For embeds in dashboards, use `embedded=true` plus a server selector and a tab; let the parent app supply auth via `customHeaders`.
