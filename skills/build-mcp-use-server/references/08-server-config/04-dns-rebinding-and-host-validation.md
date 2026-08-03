# DNS Rebinding and Host Validation

*Read this to understand how localhost-class binds are protected, when to add allowedHosts, and how Host validation works on server.fetch.*

## DNS Rebinding Attack & Host-Header Validation

A DNS rebinding attack tricks a browser into requesting your localhost server on behalf of an attacker. The server trusts the request because it comes from localhost, but it was initiated by a hostile web page.

**Solution:** Validate the `Host` header. Accept only hostnames you expect to receive.

## Localhost-Class Automatic Protection

When you bind to `127.0.0.1`, `localhost`, or `::1`, **Host validation is automatically ON**.

```typescript
// Local development with automatic protection
await server.listen(3000);  // binds 127.0.0.1
// Valid Host headers: 127.0.0.1:3000, localhost:3000, [::1]:3000
// Invalid: attacker.com:3000, 192.168.1.100:3000 → 403 Forbidden
```

This automatic protection applies to `listen()` when it binds a localhost-class host. `server.fetch()` has no bind host, so Host validation is off unless `allowedHosts` is configured.

## Public Binds (0.0.0.0) and Edge Proxies

When you bind to `0.0.0.0` (public), **Host validation is OFF by default**. Platform edges (Railway, Cloudflare, Vercel) route only assigned hostnames, so you don't need to check.

```typescript
// Public deployment behind edge
await server.listen(3000, { host: "0.0.0.0" });
// Edge routes only traffic for api.example.com → Host: api.example.com
// Host validation OFF; trust the edge
```

`listen()` on a non-localhost host without `allowedHosts` logs a `console.warn`: `"[mcp-use] listen() is serving on <host> without Host validation. Behind a platform edge that only routes your own domains this is expected; if this process is reachable directly, set allowedHosts to restrict it."` This is a warning, not a startup failure — the server still binds and serves.

## allowedHosts: Extra Allowed Hostnames

Add extra hostnames for DNS-rebinding protection when localhost isn't enough (e.g., testing from a development machine on the network, or sandboxed views on different subdomains).

```typescript
new MCPServer({
  name: "api",
  version: "1.0.0",
  allowedHosts: ["api.dev.local", "dev-machine.local"],
});

// Valid Host headers:
// - 127.0.0.1:3000 (localhost-class, always allowed)
// - api.dev.local:3000 (in allowedHosts)
// - dev-machine.local:3000 (in allowedHosts)
// Invalid:
// - attacker.com:3000 (not in allowedHosts)
```

**Key points:**
- Port-agnostic: `api.dev.local` (any port) is valid; `api.dev.local:3000` also matches
- Additive: Localhost-class hosts are always allowed; `allowedHosts` adds to that list
- Enables Host validation on `server.fetch`: Setting `allowedHosts` also turns on Host validation for `server.fetch()`, which otherwise applies none

## hostValidationMiddleware

`hostValidationMiddleware()` is Fetch middleware, not Hono middleware. Do not pass it to `app.use()` or `server.use()`. For an `MCPServer`, prefer constructor configuration so every mounted route uses the same policy:

```typescript
import { MCPServer } from "mcp-use";

const server = new MCPServer({
  name: "api",
  version: "1.0.0",
  allowedHosts: ["api.example.com", "localhost"],
});

server.get("/health", (c) => c.json({ ok: true }));
```

When you own a Fetch boundary rather than an `MCPServer` configuration, wrap its terminal handler with `composeFetch`:

```typescript
import {
  composeFetch,
  hostValidationMiddleware,
  MCPServer,
} from "mcp-use";

const server = new MCPServer({
  name: "api",
  version: "1.0.0",
});

const validatedFetch = composeFetch(
  server.fetch,
  hostValidationMiddleware(["api.example.com", "localhost"]),
);

export default validatedFetch;
```

See `05-middleware.md` for middleware patterns.

## When to Use allowedHosts

**You need allowedHosts when:**
- Testing from a different machine on your network (set to machine hostname)
- View iframes on different subdomains (e.g., `views.dev.local`)
- Multi-tenant setup with different hostnames per tenant

**You don't need allowedHosts when:**
- Pure localhost development (127.0.0.1, localhost, ::1 auto-allowed)
- Public deployment behind an edge proxy (edge handles routing)

## Example: Local Network Testing

```typescript
const server = new MCPServer({
  name: "api",
  version: "1.0.0",
  host: "0.0.0.0",  // Listen on all interfaces
  allowedHosts: ["mydev.local"],  // Allow requests from dev machine
});

await server.listen(3000);
// Request with Host: mydev.local:3000 → allowed (in allowedHosts)
// Request with Host: attacker.com (DNS-rebound to this machine's IP) → rejected (403, not in allowedHosts)
```

## Host vs Origin Validation

| Header | Validated by | Purpose | When ON |
|--------|--------------|---------|---------|
| `Host` | `hostValidationMiddleware` or implicit localhost check | DNS rebinding protection | Localhost-class binds always; or when `allowedHosts` set |
| `Origin` | `originValidationMiddleware` or implicit check | CSRF & sandboxed iframe protection | When `allowedOrigins` set |

Both protect against different attacks. Use both for defense-in-depth on public servers.

See `03-cors-and-allowed-origins.md` for Origin validation details.
