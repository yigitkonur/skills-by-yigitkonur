# DNS rebinding protection

`allowedOrigins` is the defense. Configuration lives in `03-cors-and-allowed-origins.md`. This file explains *why* you need it.

## The attack

DNS rebinding lets a malicious website talk to your local MCP server through the user's browser. Steps:

1. User visits `evil.example.com`. The page's JS issues `fetch('http://attacker-controlled-host/mcp', ...)`.
2. The attacker's DNS server first answers with the attacker's IP, then quickly rebinds the hostname to `127.0.0.1`.
3. The browser, applying same-origin to the *hostname*, treats subsequent requests as same-origin — but they now hit your local MCP server.
4. The malicious page can call your tools, read resources, exfiltrate data — all from the user's machine, all bypassing CORS.

CORS does not stop this. CORS keys on the request's `Origin` header (the attacker's domain), but the *target* hostname has been rebound to localhost. The browser thinks it's making a same-origin call.

## The defense

`Host` header validation. Even after DNS rebinding, the browser still sends `Host: <attacker-controlled-host>` (the original hostname the page used). Your server checks that header against a known list and rejects mismatches.

```typescript
const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  allowedOrigins: ['https://app.example.com'],
})
```

The middleware extracts hostnames from the URLs in `allowedOrigins` and compares against the incoming `Host` header. Mismatch → `403 Forbidden`.

## When to enable

| Scenario | `allowedOrigins`? |
|---|---|
| Localhost server, browser-based client (Inspector, widget) | Required |
| Public HTTPS server reachable from a browser | Required |
| Server behind a reverse proxy that filters Host already | Required as defense in depth |
| stdio-only server | N/A — no HTTP attack surface |
| Server reachable only by a trusted CLI on the same host | Optional but recommended |

## Loading from env

```typescript
const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  allowedOrigins: process.env.ALLOWED_ORIGINS?.split(','),
})
```

Set `ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com` in your deployment platform.

## What `allowedOrigins` does not do

- Does not authenticate users — pair with OAuth (`11-auth/`).
- Does not validate per-route permissions — pair with route-scoped middleware (`05-middleware-and-custom-routes.md`).
- Does not make `cors: { origin: '*' }` safe.
- Does not replace TLS — terminate HTTPS at the edge.

## Reverse-proxy checklist

| Check | Why |
|---|---|
| Forward `Host` and `X-Forwarded-*` headers correctly | Avoid false rejections |
| Preserve the `/mcp` path | Discovery and OAuth callbacks depend on it |
| Set explicit trusted origins (not `*`) | Avoid accidental browser exposure |
| Terminate TLS at the edge | Keep browser flows secure |
