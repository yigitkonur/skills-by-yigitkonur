# Authentication

Complete reference for authentication — OAuth 2.1, bearer tokens, custom headers, and browser OAuth flows.

---

## Supported Methods

| Method | Best For | Transport |
|---|---|---|
| **OAuth 2.1** | Full OAuth flow with Dynamic Client Registration (DCR) | HTTP |
| **Bearer Tokens** | API keys and static tokens | HTTP |
| **Custom Headers** | Flexible header-based auth | HTTP |

---

## OAuth Authentication (Browser / React)

OAuth provides secure, token-based authentication with automatic token refresh and user consent flows. Use `useMcp` from `mcp-use/react`:

```typescript
import { useMcp } from "mcp-use/react";

function MyComponent() {
  const mcp = useMcp({
    url: "http://localhost:3000/mcp",
    callbackUrl: "http://localhost:3000/callback",
  });

  if (mcp.state === "pending_auth") {
    return <button onClick={mcp.authenticate}>Authenticate with OAuth</button>;
  }
  if (mcp.state === "authenticating") {
    return <div>Authenticating...</div>;
  }
  if (mcp.state === "ready") {
    return <div>Connected! {mcp.tools.length} tools available</div>;
  }
  return <div>Connecting...</div>;
}
```

### Custom OAuth Provider (Headless / Testing)

If you run in non-browser environments (tests, headless runners, custom redirects), inject your own OAuth provider via `authProvider`:

```typescript
import { useMcp } from "mcp-use/react";
import { MyOAuthClientProvider } from "./my-oauth-provider";

const mcp = useMcp({
  url: "http://localhost:3000/mcp",
  authProvider: new MyOAuthClientProvider(),
});
```

When `authProvider` is provided, `useMcp` uses that provider directly instead of creating the default browser OAuth provider internally.

---

## Bearer Token Authentication (Browser / React)

For servers requiring API keys or bearer tokens, pass `headers` directly to `useMcp`:

```typescript
import { useMcp } from "mcp-use/react";

function MyComponent() {
  const mcp = useMcp({
    url: "http://localhost:3000/mcp",
    headers: {
      Authorization: "Bearer sk-your-api-key-here",
    },
  });

  // Use mcp.tools, mcp.callTool, etc.
}
```

---

## Node.js Client Authentication

For server-side Node.js applications, use `MCPClient` with bearer tokens or custom headers. OAuth flows are browser-only and not available in Node.js environments.

### Bearer Token — `authToken` Field

The simplest way to authenticate with API-based MCP servers:

```typescript
import { MCPClient } from "mcp-use";

const config = {
  mcpServers: {
    "my-server": {
      url: "https://api.example.com/mcp",
      authToken: "sk-your-api-key-here",
    },
  },
};

const client = MCPClient.fromDict(config);
```

With environment variables:

```typescript
import { MCPClient } from "mcp-use";

const config = {
  mcpServers: {
    "my-server": {
      url: "https://api.example.com/mcp",
      authToken: process.env.MCP_API_KEY,
    },
  },
};

const client = MCPClient.fromDict(config);
```

### Custom Headers

For servers requiring custom authentication headers or additional metadata:

```typescript
import { MCPClient } from "mcp-use";

const config = {
  mcpServers: {
    "my-server": {
      url: "https://api.example.com/mcp",
      headers: {
        Authorization: "Bearer sk-your-api-key",
        "X-API-Version": "2024-01-01",
        "X-Custom-Header": "value",
      },
    },
  },
};

const client = MCPClient.fromDict(config);
```

> **Note:** When using custom headers, avoid exposing secrets in client-side bundles. Prefer server-side `MCPClient` for sensitive header values.

### Configuration File

Load authentication settings from a JSON configuration file by passing the file path directly to the constructor, or use `MCPClient.fromDict()` for an inline config object:

```typescript
import { MCPClient } from "mcp-use";

// Pass file path directly
const client = new MCPClient("./mcp-config.json");

// Or load from an inline dict/object
import config from "./mcp-config.json";
const client2 = MCPClient.fromDict(config);
```

**Best Practice**: Store sensitive tokens in environment variables and reference them in your configuration instead of hardcoding them in files.

---

## CLI Authentication

The mcp-use CLI client supports bearer token authentication for connecting to secured MCP servers:

```bash
# Connect with bearer token
npx mcp-use client connect https://api.example.com/mcp \
  --name my-server \
  --auth sk-your-api-key

# List tools (uses saved authentication)
npx mcp-use client tools list

# Call a tool
npx mcp-use client tools call send_email '{"to":"[email protected]"}'

# Disconnect
npx mcp-use client disconnect my-server
```

The CLI automatically saves authentication tokens in `~/.mcp-use/cli-sessions.json` for future sessions.

---

## OAuth Flow Modes

mcp-use supports two OAuth flow modes for client applications:

### Popup Flow (Default)

Opens OAuth authorization in a popup window. Best for desktop and web applications.

**Advantages:**
- User stays on the same page
- Better UX for web applications
- No navigation interruption

```typescript
const mcp = useMcp({
  url: "http://localhost:3000/mcp",
  callbackUrl: "http://localhost:3000/callback",
  // Popup flow is the default
});
```

### Redirect Flow

Redirects the current window to the OAuth provider, then back to your app.

**Advantages:**
- Works in all browsers (popup blockers won't interfere)
- Better for mobile browsers
- More reliable across different environments

```typescript
const mcp = useMcp({
  url: "http://localhost:3000/mcp",
  callbackUrl: "http://localhost:3000/callback",
  useRedirectFlow: true, // Enable redirect flow
});
```

**Setup for Redirect Flow:**

1. Create a callback page in your app:

```typescript
// pages/callback.tsx or app/callback/page.tsx
import { onMcpAuthorization } from "mcp-use/auth";
import { useEffect, useState } from "react";

export default function OAuthCallback() {
  const [status, setStatus] = useState<"processing" | "success" | "error">("processing");

  useEffect(() => {
    onMcpAuthorization()
      .then(() => setStatus("success"))
      .catch((err) => {
        console.error("Auth failed:", err);
        setStatus("error");
      });
  }, []);

  return status === "processing"
    ? <div>Completing authentication...</div>
    : status === "success"
      ? <div>Success! Redirecting...</div>
      : <div>Authentication failed</div>;
}
```

2. Configure your callback URL to match this route:

```typescript
const mcp = useMcp({
  url: "http://localhost:3000/mcp",
  callbackUrl: "http://localhost:3000/callback", // Your callback page
  useRedirectFlow: true,
});
```

---

## Manual Authentication Control

By default, mcp-use requires explicit user action to trigger OAuth authentication. When a server requires authentication, the connection enters `pending_auth` state and you must call the `authenticate()` method:

```typescript
const mcp = useMcp({
  url: "http://localhost:3000/mcp",
  // preventAutoAuth: true is the default
});

// Manually trigger authentication when ready
if (mcp.state === "pending_auth") {
  return <button onClick={mcp.authenticate}>Sign in to continue</button>;
}
```

If the popup is blocked by the browser, `useMcp` exposes an `authUrl` property with the URL that should have been opened. Present this as a fallback link:

```typescript
const mcp = useMcp({
  url: "http://localhost:3000/mcp",
});

if (mcp.state === "pending_auth" || mcp.state === "authenticating") {
  return (
    <div>
      <button onClick={mcp.authenticate}>Authenticate</button>
      {mcp.authUrl && (
        <p>
          Popup blocked? <a href={mcp.authUrl} target="_blank" rel="noopener noreferrer">
            Open authentication page manually
          </a>
        </p>
      )}
    </div>
  );
}
```

To enable automatic OAuth flow (legacy behavior), set `preventAutoAuth: false`:

```typescript
const mcp = useMcp({
  url: "http://localhost:3000/mcp",
  preventAutoAuth: false, // Auto-trigger OAuth popup
});
```

| Setting | Behavior |
|---|---|
| `preventAutoAuth: true` (default) | User must call `authenticate()` explicitly |
| `preventAutoAuth: false` | OAuth starts automatically when server requires it |

---

## Custom OAuthClientProvider

Implement a custom provider for headless or testing scenarios:

```typescript
interface OAuthClientProvider {
  authorize: (options: { callbackUrl: string }) => Promise<string>;
  // optional: refreshToken, revoke, etc.
}
```

When supplied via `authProvider`, `useMcp` bypasses the built-in browser provider and delegates the full OAuth flow to your implementation.

---

## Configuration Options

### `useMcp` Hook Parameters (Browser / React)

| Parameter | Type | Required | Description |
|---|---|---|---|
| `url` | `string` | Yes | MCP server endpoint URL |
| `callbackUrl` | `string` | No (OAuth) | URL the OAuth provider redirects to after consent. Defaults to `/oauth/callback` on the current origin |
| `authProvider` | `OAuthClientProvider` | No | Custom provider instance for headless/testing environments |
| `useRedirectFlow` | `boolean` | No (default `false`) | Switch to redirect flow instead of popup |
| `preventAutoAuth` | `boolean` | No (default `true`) | If `false`, OAuth popup opens automatically on connection |
| `headers` | `Record<string, string>` | No | Additional HTTP headers for the MCP connection |
| `enabled` | `boolean` | No (default `true`) | When `false`, no connection is attempted (similar to TanStack Query's `enabled`) |

### Node.js `MCPClient` Server Configuration Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `url` | `string` | Yes | MCP server endpoint URL |
| `authToken` | `string` | No | Bearer token (added to Authorization header) |
| `auth_token` | `string` | No | Snake_case alias for `authToken` (Python config compatibility) |
| `headers` | `Record<string, string>` | No | Custom HTTP headers including authentication headers |

**Configuration Compatibility**: Both `authToken` (camelCase) and `auth_token` (snake_case) are accepted for token-based authentication. Use `authToken` for TypeScript conventions; `auth_token` is supported for compatibility with Python-style configurations.

---

## Example Servers

### OAuth with Dynamic Client Registration (DCR) — Linear

Linear supports DCR, so no `clientId` is needed:

```typescript
import { useMcp } from "mcp-use/react";

const mcp = useMcp({
  url: "https://mcp.linear.app/mcp",
  callbackUrl: "http://localhost:3000/callback",
  // No clientId needed — Linear supports DCR
});
```

### OAuth with Manual Registration — GitHub

GitHub requires manual app registration:

```typescript
import { useMcp } from "mcp-use/react";

const mcp = useMcp({
  url: "https://api.githubcopilot.com/mcp/",
  callbackUrl: "http://localhost:3000/callback",
  // clientId and other OAuth params configured via authProvider or server metadata
});
```

### Bearer Token — API-Based Servers

```typescript
import { MCPClient } from "mcp-use";

const client = MCPClient.fromDict({
  mcpServers: {
    apiServer: {
      url: "https://api.example.com/mcp",
      authToken: process.env.API_KEY,
    },
  },
});
```

---

## Security Best Practices

| Practice | Why |
|---|---|
| Use environment variables for tokens | Never hardcode secrets in source |
| Prefer OAuth over static tokens | Tokens can be rotated, scoped, and revoked |
| Use HTTPS for all connections | Prevents token interception in transit |
| Set `preventAutoAuth: true` | User controls when auth starts |
| Implement token refresh | Avoid expired token failures |
| Scope tokens minimally | Limit blast radius of token compromise |
| Use DCR when available | Automatic client registration, no manual setup |
| Avoid custom headers in client-side bundles | Secrets in browser bundles can be extracted; use server-side `MCPClient` instead |
| Prefer popup flow over redirect flow | Redirect flow puts the token in the callback URL query string; popup flow keeps tokens out of the URL |

**BAD** — Hardcoded credentials in source:

```typescript
const client = MCPClient.fromDict({
  mcpServers: {
    myServer: {
      url: "https://api.example.com/mcp",
      authToken: "sk-live-abc123def456ghi789",
    },
  },
});
```

**GOOD** — Environment variables or OAuth:

```typescript
// Option 1: Environment variables
const client = MCPClient.fromDict({
  mcpServers: {
    myServer: {
      url: "https://api.example.com/mcp",
      authToken: process.env.MCP_API_KEY,
    },
  },
});

// Option 2: OAuth (browser)
const mcp = useMcp({
  url: "https://api.example.com/mcp",
  callbackUrl: "/callback",
});
```

---

## Available Imports

```typescript
// Node.js client
import { MCPClient } from "mcp-use";

// React hook
import { useMcp } from "mcp-use/react";

// OAuth callback handler (redirect flow callback page)
import { onMcpAuthorization } from "mcp-use/auth";
```
