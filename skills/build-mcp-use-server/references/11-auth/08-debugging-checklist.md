# OAuth Debugging Checklist

When OAuth fails, work top to bottom. The first failing item is almost always the cause.

## 1. Discovery

```bash
curl -sS https://your-server.example.com/.well-known/oauth-authorization-server | jq
curl -sS https://your-server.example.com/.well-known/oauth-protected-resource | jq
```

Check:
- Both endpoints return 200, valid JSON.
- DCR mode: `registration_endpoint` is present and points to upstream.
- Proxy mode: `authorization_endpoint` and `token_endpoint` point to **your** server.
- `issuer` matches what `verifyToken` expects.

If `.well-known` returns 404, OAuth is not configured — pass `oauth:` to `MCPServer`.

## 2. CORS on `.well-known`

Browser-based clients (Inspector, useMcp) need CORS headers:

```bash
curl -sS -i -H "Origin: http://localhost:5173" \
  https://your-server.example.com/.well-known/oauth-authorization-server | grep -i access-control
```

Expected: `access-control-allow-origin: *` (or your origin).
Fix: see `../26-anti-patterns/05-security-and-cors.md`.

## 3. Client redirect URI

The client's `redirect_uri` must be:
- Listed in the upstream provider dashboard (or proxy's allowlist).
- Exactly matching — including trailing slash, port, scheme.

| Symptom | Likely cause |
|---|---|
| `redirect_uri_mismatch` from upstream | Localhost port not allowed; add `http://localhost:*/**` for dev |
| Browser stuck after consent | Redirect URI scheme mismatch (http vs https) |
| Inspector "callback failed" | Inspector port differs from registered URI |

## 4. Scopes

```bash
# Decode the JWT (paste from Inspector or curl response)
echo "<jwt>" | cut -d. -f2 | base64 -d | jq
```

Check:
- `scope` claim contains what your tool expects.
- `permissions` (Auth0) or `realm_access.roles` (Keycloak) are populated.
- `offline_access` is present if you need refresh.

If a scope is missing: add it to `scopesSupported`, configure it upstream, and have the client re-authorize.

## 5. JWKS reachability

```bash
curl -sS <jwks_uri_from_metadata> | jq .keys[0].kid
```

Expected: returns at least one key with a `kid`.

| Symptom | Cause |
|---|---|
| `jwks fetch failed` | Network blocks egress to provider |
| `kid not found` | Provider rotated keys; mcp-use caches — restart the server |
| `signature verification failed` | Wrong JWKS URL in custom provider config |

## 6. Token expiry / clock skew

```bash
echo "<jwt>" | cut -d. -f2 | base64 -d | jq '{iat, exp, nbf}'
```

Check `exp` is in the future. mcp-use allows ~30s clock skew. If your server clock is off by minutes, all tokens fail.

```bash
date -u   # check server clock
```

Fix: enable NTP / chrony on the host.

## 7. Audience mismatch

Decode JWT, look at `aud`:

```bash
echo "<jwt>" | cut -d. -f2 | base64 -d | jq .aud
```

`aud` must match what your verifier expects:
- Auth0: matches `MCP_USE_OAUTH_AUTH0_AUDIENCE`.
- Keycloak: matches `audience` config (requires Audience mapper in Keycloak).
- Custom: matches `audience` in your `verifyToken` call.

| Symptom | Fix |
|---|---|
| `invalid audience` | Set provider audience config; for Keycloak, add Audience mapper |
| `aud` is a string but verifier expects array (or vice versa) | Both shapes are valid — bug if your verifier rejects |

## 8. Issuer mismatch

`iss` claim must match the configured issuer exactly. Common gotcha: trailing slash.

```
Configured: https://example.com/
Token iss:  https://example.com    # FAILS — missing slash
```

Fix in custom provider: match exactly. For built-ins, use the documented domain shape.

## 9. Token shape

| Provider | JWT or opaque |
|---|---|
| Auth0 | JWT (when API created with RS256) |
| WorkOS | JWT |
| Keycloak | JWT |
| Supabase | JWT (ES256 new, HS256 legacy) |
| Better Auth | JWT |
| Google | JWT (ID token) — but access token is opaque |
| GitHub | Opaque — needs custom `verifyToken` |
| Slack | Opaque |

If you wired `jwksVerifier` against an opaque-token provider, every request returns 401. Switch to a custom `verifyToken` that calls the provider's introspection or userinfo endpoint.

## 10. `Authorization` header reaches the server

```bash
# Reproduce the failing request directly
curl -sS -i -H "Authorization: Bearer <jwt>" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}' \
  https://your-server.example.com/mcp
```

If it works here but fails from the client, the problem is in the client (proxy, CORS, header stripping). If it fails here too, the problem is server-side.

## 11. Verify the verifier with `debug-auth` tool

Add temporarily:

```ts
server.tool({ name: 'debug-auth' }, async (_args, ctx) => ({
  content: [{ type: 'text', text: JSON.stringify({
    hasAuth: !!ctx.auth,
    userId: ctx.auth?.user?.userId ?? 'none',
    scopes: ctx.auth?.scopes ?? [],
    permissions: ctx.auth?.permissions ?? [],
    payloadKeys: ctx.auth ? Object.keys(ctx.auth.payload) : [],
  }, null, 2) }],
}))
```

Call it via Inspector. Remove before production.

## Cross-references

- Provider-specific failures: `../27-troubleshooting/03-oauth-and-supabase-issues.md`
- CORS configuration: `../26-anti-patterns/05-security-and-cors.md`
- Tunneling for HTTPS redirects: `../21-tunneling/`
