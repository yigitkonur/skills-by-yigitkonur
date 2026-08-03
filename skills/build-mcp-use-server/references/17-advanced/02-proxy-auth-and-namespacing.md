# Proxy Auth and Namespacing

*Read this when proxying sensitive upstreams, structuring multi-tenant gateways, or integrating auth-required servers.*

## Bearer token passthrough

Proxy config accepts bearer tokens that are forwarded to upstream servers:

```typescript
await server.proxy({
  userApi: {
    url: "https://users.example.com/mcp",
    authToken: process.env.USER_API_TOKEN,
  },
  adminApi: {
    url: "https://admin.example.com/mcp",
    authToken: process.env.ADMIN_API_TOKEN,
  },
});
```

Each upstream receives its token independently. Tokens are read from environment variables at proxy setup time, not per-request.

## Header-based auth

Use static headers for API key or custom auth schemes:

```typescript
await server.proxy({
  thirdparty: {
    url: "https://thirdparty.example.com/mcp",
    headers: {
      "x-api-key": process.env.THIRDPARTY_KEY,
      "x-client-id": process.env.THIRDPARTY_CLIENT_ID,
    },
  },
});
```

Headers are sent on every request to the upstream. Client who connects to your gateway does NOT see these headers or auth details — they are internal to the proxy.

## No OAuth bridge in proxy

v2 proxy does NOT bridge browser OAuth flows or token refresh. Obtain credentials upfront and pass them statically.

For gateways fronting OAuth-protected upstreams, refresh tokens in your application:

```typescript
// Resolve a fresh, unexpired token BEFORE the first proxy() call.
async function resolveUpstreamToken(): Promise<string> {
  const response = await fetch("https://auth.example.com/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token: process.env.REFRESH_TOKEN }),
  });
  const { access_token } = await response.json();
  return access_token;
}

const upstreamToken = await resolveUpstreamToken();

// proxy() must run before listen() / the first server.fetch() call — it
// throws once the server has started. It is not idempotent: calling it a
// second time opens a new upstream connection and does not update or
// replace the first; identically-named capabilities are skipped as
// collisions. Resolve long-lived or self-refreshing credentials up front
// instead of trying to re-proxy on a timer.
await server.proxy({
  api: {
    url: "https://api.example.com/mcp",
    authToken: upstreamToken,
  },
});
```

## Namespace collisions

Config keys become capability namespaces. If two upstreams export a tool with the same name, collisions are skipped (logged to diagnostics). Design upstream names to avoid overlap:

- `users_getUserById`, `payments_getUserById` (clear)
- `getUserById` upstream `a` and `getUserById` upstream `b` (collision if both named `a` and `b`)

Use semantic keys: `weather`, `database`, `analytics`, not `upstream1`, `upstream2`.

## Multi-tenant gateways

To proxy different upstreams per client, rebuild the proxy config at request time:

```typescript
server.post("/gateway/:tenant", async (c) => {
  const tenant = c.req.param("tenant");
  const config = await loadTenantUpstreams(tenant);
  
  // This is an escape hatch; mcp-use does not manage per-request proxies natively
  // Hand-roll with client + connection forwarding if multi-tenant proxying is critical
  return c.text("Multi-tenant proxy requires custom routing");
});
```

For true multi-tenant, use `@mcp-use/client` directly in custom routes to manage per-tenant connections, not `server.proxy()`.

## Resource URI mapping

Proxied static resources are exposed as `mcp-use-proxy:///<namespace>/<upstream-uri>`, where both `<namespace>` and the original `<upstream-uri>` are `encodeURIComponent`-escaped. The gateway resolves reads against the upstream connection it captured at mount time — clients never need to parse or reconstruct the upstream URI themselves.

## Best practices

1. **Set authToken or headers from env, never hardcode secrets.**
2. **Use semantic upstream names; avoid collisions by design.**
3. **Call proxy() before listen() or first fetch request.**
4. **For complex workflows, hand-write tools instead of proxying raw capability sets.**
5. **Multi-tenant scenarios: use @mcp-use/client directly in custom routes.**
