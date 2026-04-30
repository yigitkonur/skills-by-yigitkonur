# EPROTO TLS-fronted-HTTP mismatch

Distinct from the HSTS trap, but adjacent. Triggers when TLS terminates upstream but the local server is HTTP.

## Symptom

Page returns 500. Dev server log shows:

```
Failed to proxy https://localhost:3001/sign-in
Error: write EPROTO C09841F801000000:error:0A00010B:SSL routines:tls_validate_record_header:wrong version number:ssl/record/methods/tlsany_meth.c:78:
    errno: -100,
    code: 'EPROTO',
    syscall: 'write'
```

## Cause

Tailscale Serve / nginx / Cloudflare Tunnel terminate TLS at :443, then forward the request to your local Next.js dev server on :PORT (HTTP). The forwarded request carries:

- `X-Forwarded-Proto: https`
- `X-Forwarded-Host: <tunnel-host>`
- `Host: localhost:<PORT>` (the proxy rewrites Host)

When Next.js middleware (Clerk, custom proxy.ts, etc.) does an internal self-fetch — for example to validate a session — it constructs the URL as `<X-Forwarded-Proto>://<Host>/<path>`:

```
https://localhost:3001/sign-in
```

But your local server speaks plain HTTP on :3001. The `https://` connection attempt sends a TLS Client Hello to an HTTP server → "wrong version number" → EPROTO.

## Three fixes

### 1. Use HTTP all the way (simplest)

Configure the upstream proxy to NOT terminate TLS. For Tailscale Serve:

```bash
tailscale serve --bg --http=80 PORT   # HTTP-only mode
```

WireGuard already encrypts the link end-to-end; the HTTPS layer is belt-on-belt. **Caveat:** browsers will reject this for `.ts.net` (HSTS preload — see `hsts-preload-trap.md`).

### 2. Use HTTPS all the way

Run the local dev server with TLS:

```bash
# Next.js doesn't natively support HTTPS dev. Use a local HTTPS proxy:
npx local-ssl-proxy --source 3443 --target 3001
# Then point Tailscale Serve at :3443
```

Heavyweight but bulletproof.

### 3. Make middleware respect X-Forwarded-Proto correctly

The cleanest fix: tell Next.js middleware that internal self-fetches should use the *protocol of the inbound request*, not blindly `https://`. Patch the proxy/middleware:

```ts
// proxy.ts
export default clerkMiddleware((auth, req) => {
  // Force internal self-fetches to use HTTP locally
  if (req.headers.get("x-forwarded-host")?.includes(".ts.net")) {
    req.headers.set("x-forwarded-proto", "http");
  }
  // ... rest of middleware
});
```

This is project-specific and brittle; recommend (1) or (2) first.

## Why this is Next-specific

Most frameworks (Express, Hono, Fastify) don't internally self-fetch. The middleware just runs synchronously against the inbound request. Next.js does this because of its server-component → server-action protocol — internal RSC streaming sometimes does an internal HTTP call to the same server.

## Diagnostic test

Probe via curl on the host:

```bash
# Should both return 200/307 (or whatever the route returns)
curl -sLk -o /dev/null -w "%{http_code}\n" http://localhost:3001/
curl -sLk -o /dev/null -w "%{http_code}\n" https://<tunnel-host>/
```

If localhost works but tunnel returns 500 + EPROTO in dev log → you've hit this.

## When to mention this in user-facing output

Bake the explanation into your commit message and the Makefile's `make tunnel` doc-comment. Devs hit this once and lose hours; documenting it is a force multiplier.
