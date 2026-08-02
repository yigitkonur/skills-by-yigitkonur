# Connection Settings

*Read this when configuring how the Inspector connects to a server (Direct, Auto, Via Proxy, OAuth, timeouts).*

## Connection mode: Auto, Direct, or Via Proxy

Most servers work with just a transport type and URL. Choose a connection mode when the browser cannot reach the server directly or when you want to test specific connection paths.

### Auto (default)

The Inspector tries a direct browser connection first, then falls back to the configured Inspector proxy if direct access fails because of CORS or network policy.

**Use Auto when:** You want the Inspector to handle connection failures gracefully.

### Direct

The browser reaches the server directly without a proxy.

**Use Direct when:** The server is local, public, or reachable from your browser.

**Avoid Direct when:** The browser is blocked by CORS or network policy.

### Via Proxy

All requests go through the Inspector's built-in proxy.

**Use Via Proxy when:** The browser cannot reach the server directly because of CORS, network policy, or firewall rules.

**Avoid Via Proxy when:** The server works directly; proxying adds complexity.

## Name saved servers

Set a display name for each saved server. Changing only the name updates labels in the dashboard, server list, header, and command palette without reconnecting the server or clearing auth tokens.

## Custom headers

Add custom headers only when the server requires them (bearer tokens, API keys, version headers).

**Important:** Header values are runtime-only and are intentionally not saved after a reload. Supply them again at runtime. Prefer OAuth when the server supports it.

## Configure OAuth

By default, the Inspector uses Dynamic Client Registration (DCR), so no credentials are needed. Use the Authentication dialog when:

- The upstream auth server doesn't expose `registration_endpoint` (common for proxy-mode servers fronting Slack, WorkOS, or GitHub).
- You want to use a pre-registered OAuth client instead of DCR.

| Field | When to set it |
| --- | --- |
| Client ID | Use a pre-registered OAuth client instead of DCR. |
| Client Secret | Use a confidential client (switches token endpoint auth away from `none`). |
| Scope | Request a provider-specific space-separated scope list. |

When a server requires OAuth, the connection enters `pending_auth`. Click **Authenticate**, complete the provider flow, and return to the Inspector.

**Security:** Browser OAuth session values are encrypted at rest with AES-256-GCM. The non-extractable origin key is kept in IndexedDB, and versioned ciphertext remains in localStorage.

## Copy and paste configuration

Use **Copy Config** to export the current connection form as JSON. Paste JSON into the URL field of another Inspector instance to populate the form.

Example configuration:

```json
{
  "url": "https://mcp.example.com/mcp",
  "transportType": "http",
  "connectionMode": "auto",
  "headers": {
    "Authorization": "Bearer token123"
  },
  "requestTimeout": 10000,
  "resetTimeoutOnProgress": true,
  "maxTotalTimeout": 60000,
  "oauth": {
    "clientId": "your-client-id",
    "clientSecret": "your-client-secret",
    "scope": "read write"
  }
}
```

**Warning:** Remove secrets (OAuth tokens, API keys) before sharing exported configurations.

## Tune timeouts for long-running tools

Use timeout settings only when a valid tool call or resource read needs more time than the defaults.

| Setting | Default | Use when |
| --- | --- | --- |
| Request timeout | 10000 ms | A tool call takes longer than 10 seconds. |
| Maximum total timeout | 60000 ms | Retries or progress updates might extend beyond 60 seconds. |

If a request times out, first confirm the server eventually responds. Then raise the timeout to match the expected tool runtime.
