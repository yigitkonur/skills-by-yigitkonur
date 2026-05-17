# Security and CORS

For the positive setup of CORS and `allowedOrigins`, see `08-server-config/03-cors-and-allowed-origins.md` and `08-server-config/04-dns-rebinding-protection.md`. This file is the catalog of mistakes. For OAuth/Supabase-specific issues, see `27-troubleshooting/03-oauth-and-supabase-issues.md`. For Docker hardening, see `25-deploy/03-docker.md`.

## Don't skip `allowedOrigins` on HTTP servers

Without `allowedOrigins`, mcp-use accepts every `Host` header value — leaving you open to DNS rebinding attacks. An attacker's page resolves a hostname to your server's local IP, then loads the attacker page from that hostname, bypassing the same-origin policy in browser-initiated requests.

```typescript
// ❌ no host validation — accepts any Host header
const server = new MCPServer({ name: "api", version: "1.0.0" });
```

```typescript
// ✅ explicit allowlist
const server = new MCPServer({
  name: "api",
  version: "1.0.0",
  allowedOrigins: [
    "https://myapp.com",
    "https://app.myapp.com",
  ],
});
```

For dev, `localhost` and `127.0.0.1` are auto-allowed. In production, set the list explicitly — environment variable in `02-env-config.md`.

## Don't trust `X-Forwarded-*` blindly

`X-Forwarded-For`, `X-Forwarded-Host`, `X-Real-IP` are headers any client can set. Only trust them when you're behind a *known, controlled* proxy that overwrites them. Otherwise an attacker spoofs their source IP.

```typescript
// ❌ trusts whatever the client sent
const ip = c.req.header("x-forwarded-for") ?? "unknown";
```

```typescript
// ✅ honor the header your platform documents as authoritative,
//    and only when the immediate peer is a known proxy
//    Cloudflare → CF-Connecting-IP. Vercel → x-real-ip.
//    AWS ALB → first hop of X-Forwarded-For.
const ip = c.req.header("cf-connecting-ip")
  ?? c.req.header("x-real-ip")
  ?? "unknown";
```

Don't mix headers across platforms.

## Don't put credentials in source

Anything checked into git is leaked once a single contributor's machine is compromised, once the repo briefly goes public, or once a fork is published. Use env vars, validated at startup (`24-production/02-env-config.md`).

```typescript
// ❌ hardcoded secret
const STRIPE_KEY = "sk_live_4242424242";
```

```typescript
// ❌ default to a real value if env is missing
const STRIPE_KEY = process.env.STRIPE_KEY ?? "sk_live_REAL_FALLBACK";
```

```typescript
// ✅ require it; fail fast at startup
function requireEnv(key: string) {
  const v = process.env[key];
  if (!v) throw new Error(`Missing ${key}`);
  return v;
}
const STRIPE_KEY = requireEnv("STRIPE_KEY");
```

`.env` files belong in `.gitignore`. Use a secrets manager (Vault, AWS Secrets Manager, Doppler, Railway/Fly secrets) for production.

## Don't log full tokens

Bearer tokens, refresh tokens, API keys, and OAuth codes appearing in logs end up in your log aggregator's index, in shared dashboards, in alerts forwarded to chat — and from there in screenshots, error reports, and support tickets.

```typescript
// ❌ full token in log
logger.info("got token", { token: result.access_token });
```

```typescript
// ❌ full Authorization header
logger.info("incoming", { authorization: c.req.header("authorization") });
```

```typescript
// ✅ redact: prefix only, or boolean presence
function tokenPrefix(t: string | undefined) {
  return t ? `${t.slice(0, 8)}…` : "(none)";
}

logger.info("got token", { token: tokenPrefix(result.access_token) });
logger.info("incoming", { hasAuth: !!c.req.header("authorization") });
```

The same applies to `ctx.log()` — anything logged through `ctx.log()` is model-visible and may end up in transcripts. Redact there too.

## Don't override the default CORS without keeping `mcp-session-id`

The `cors` config **replaces** the default entirely. If you forget `mcp-session-id` in `allowHeaders` *and* `exposeHeaders`, sessions silently break in the browser — preflight passes but the client can't read the session header.

```typescript
// ❌ overrides default and drops the session header
cors: {
  origin: ["https://app.example.com"],
  allowHeaders: ["Content-Type", "Authorization"], // forgot mcp-session-id
}
```

```typescript
// ✅ keep mcp-session-id on both lists; keep mcp-protocol-version on allowHeaders
cors: {
  origin: ["https://app.example.com"],
  allowMethods: ["GET", "POST", "DELETE", "OPTIONS"],
  allowHeaders: ["Content-Type", "Authorization", "mcp-protocol-version", "mcp-session-id"],
  exposeHeaders: ["mcp-session-id"],
}
```

## Don't use `origin: "*"` in production

A wildcard origin lets any site embed your MCP endpoint and exfiltrate session-bearing responses. Even if your auth is sound, the wildcard widens the attack surface for free.

```typescript
// ❌ permissive — leftover from dev
cors: { origin: "*" }
```

```typescript
// ✅ explicit list, env-driven
cors: { origin: process.env.ALLOWED_ORIGINS?.split(",") ?? [] }
```

## Don't path-traverse on user input

User-controlled paths in `fs` calls let the caller read arbitrary files (`../../etc/passwd`).

```typescript
// ❌ reads anything the process can read
const content = await fs.promises.readFile(userPath, "utf-8");
```

```typescript
// ✅ resolve against an allowed root and verify
import { resolve, normalize } from "path";
const ALLOWED = resolve("./data");

const abs = resolve(ALLOWED, normalize(userPath));
if (!abs.startsWith(ALLOWED + "/")) {
  return error("Access denied: path outside allowed directory");
}
const content = await fs.promises.readFile(abs, "utf-8");
```

## Don't string-interpolate SQL

Parameterized queries are the only correct shape. Interpolation is SQL injection.

```typescript
// ❌
const rows = await db.query(`SELECT * FROM users WHERE name = '${name}'`);
```

```typescript
// ✅
const rows = await db.query(
  "SELECT id, name FROM users WHERE name LIKE $1",
  [`%${name}%`]
);
```

The same applies to Mongo `$where`, Redis `EVAL`, shell commands (`exec`), and any other string-built query.

## Don't disable TLS verification

```typescript
// ❌ "fixes" certificate errors by disabling them
process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";
```

This disables verification globally for the process — every fetch, every DB driver, every webhook call now accepts forged certificates. Fix the actual cert chain (add the right CA, renew expired certs).

## Quick checklist

| Don't | Do |
|---|---|
| Skip `allowedOrigins` | Set explicit allowlist (env-driven) |
| Trust `X-Forwarded-*` blindly | Verify peer is a trusted proxy first |
| Hardcode secrets | `requireEnv()` at startup |
| Log full tokens | Redact: prefix only or `hasToken: true` |
| Override CORS without `mcp-session-id` | Include in `allowHeaders` and `exposeHeaders` |
| `origin: "*"` in production | Explicit list |
| `fs` on raw user paths | Resolve under an allowed root, verify prefix |
| String-interpolated SQL | Parameterized queries |
| `NODE_TLS_REJECT_UNAUTHORIZED=0` | Fix the cert chain |
