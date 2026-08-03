# URL Parameters

*Read this when you need to create shareable links that open the Inspector on a specific server, tab, or with auto-connect.*

URL parameters let you create deep links to the Inspector with a pre-selected server, tab, or auto-connect configuration.

## Parameter reference

| Parameter | Purpose | Values |
| --- | --- | --- |
| `server` | Select an existing connection by server ID or URL. If not saved, connects to the URL if it's HTTP(S). | Connection ID or URL string |
| `autoConnect` | Connect to a server when the Inspector loads. | URL string or URL-encoded JSON config |
| `tab` | Open a specific server tab. | `tools`, `prompts`, `resources`, `chat`, `sampling`, `elicitation`, `notifications`, `playground` |
| `tunnelUrl` | Preserve tunnel URL while navigating. Usually set by the CLI. | URL string |
| `embedded` | Use embedded mode with reduced page chrome. | `true` |
| `embeddedConfig` | Configure embedded styling. | URL-encoded JSON config |

## Auto-connect with URL only

```text
https://inspector.mcp-use.com/inspect?autoConnect=https://your-server.com/mcp
```

## Auto-connect with advanced options

Pass a URL-encoded JSON object to auto-connect with custom settings:

```json
{
  "url": "https://mcp.example.com/mcp",
  "name": "Example server",
  "transportType": "http",
  "connectionMode": "auto",
  "customHeaders": {
    "Authorization": "Bearer token"
  },
  "requestTimeout": 10000,
  "maxTotalTimeout": 60000
}
```

Supported JSON fields: `url` (required), `name`, `transportType` (`"http"` or `"sse"`), `connectionMode` (`"auto"`, `"direct"`, or `"proxy"`), `autoProxyFallback`, `connectionType` (`"Direct"` or `"Via Proxy"`, kept for older links), `customHeaders`, `auth`, `requestTimeout`, `resetTimeoutOnProgress`, `maxTotalTimeout`.

URL-encode the JSON before adding it to the query string.

## Open a specific tab

Combine parameters to open a tab directly:

```text
https://inspector.mcp-use.com/inspect?server=https://your-server.com/mcp&tab=tools
```

Available tabs: `tools`, `prompts`, `resources`, `chat`, `sampling`, `elicitation`, `notifications`, `playground`.

The Inspector also updates `tab` as you move between server tabs, so refreshes keep the current view.

## Embedded mode

Use `embedded=true` when the Inspector is hosted inside another UI (iframe):

```text
https://inspector.mcp-use.com/inspect?embedded=true
```

Use `embeddedConfig` with a URL-encoded JSON object when the embedded host needs styling overrides:

```json
{
  "backgroundColor": "#f5f5f5",
  "padding": "16px"
}
```

## Example links

Open hosted Inspector and connect to a server:

```text
https://inspector.mcp-use.com/inspect?autoConnect=https://your-server.com/mcp
```

Open hosted Inspector, connect, and show the Tools tab:

```text
https://inspector.mcp-use.com/inspect?server=https://your-server.com/mcp&tab=tools
```
