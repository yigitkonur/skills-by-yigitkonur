# Security and CORS

*Read this when configuring public binds, browser origins, host validation, CORS, OAuth, or View CSP.*

## Confusing hosts with origins

`allowedHosts` validates the HTTP `Host` header. `allowedOrigins` validates browser `Origin` headers on non-GET/HEAD requests. Do not use one as a substitute for the other:

```typescript
const server = new MCPServer({
  name: "api",
  version: "1.0.0",
  allowedOrigins: ["api.example.com"], // Not Host-header protection
});
```

Configure each boundary independently. See `references/08-server-config/03-cors-and-allowed-origins.md` and `references/08-server-config/04-dns-rebinding-and-host-validation.md`.

## Assuming a public bind is automatic

The default host is loopback. A container may start successfully but remain unreachable if it binds only to `127.0.0.1`.

Do not change to `0.0.0.0` without also reviewing host validation, origin validation, OAuth resource URLs, and the platform proxy. For CLI startup, pass `--host 0.0.0.0`; for direct `listen()`, set `host: "0.0.0.0"` in server config or `HOST` in the environment.

## Assuming CORS is enabled

CORS is off when `cors` is omitted. Do not diagnose a browser preflight failure by changing `allowedOrigins` alone; origin validation and CORS headers are separate controls.

Use the v2 nested field names:

```typescript
cors: {
  origin: ["https://app.example.com"],
  methods: ["GET", "POST", "DELETE", "OPTIONS"],
  allowedHeaders: ["content-type", "authorization", "mcp-protocol-version"],
}
```

Do not use the v1-style `allowMethods` or `allowHeaders` keys.

## Using wildcard browser origins with credentials

Do not combine a permissive origin with bearer-authenticated browser traffic. Use an explicit origin list and enable credentials only when the browser client requires them.

## Using `allowedOrigins` for View CSP

Server CORS does not authorize a View iframe to call an external API. Declare external View destinations in the tool's `view.csp`:

```typescript
view: {
  name: "dashboard",
  csp: {
    connectDomains: ["https://api.example.com"],
    resourceDomains: ["https://cdn.example.com"],
  },
}
```

See `references/18-mcp-apps/server-surface/05-csp-metadata.md`.

## Logging bearer tokens

Do not log `ctx.auth.accessToken`, complete Authorization headers, authorization codes, or full token payloads. Debug using issuer, audience, expiration, scope names, and a correlation ID. Keep trace logging restricted because it can include full headers and bodies.

## Using client hints as authorization

`ctx.client.user()` is client-reported metadata, not a verified identity. Do not authorize access with its `subject`, organization, locale, or location. Use the verified provider identity at `ctx.auth.user` and provider-normalized permissions. See `references/11-auth/03-ctx-auth-and-user-context.md`.

## Hardcoding credentials

Do not place client secrets, JWT secrets, API keys, or database URLs in source. Read them from environment or a secret manager, fail fast when required values are absent, and never return them in tool results.

## Correct v2 pattern

```typescript
import { MCPServer } from "mcp-use";

const server = new MCPServer({
  name: "public-api",
  version: "1.0.0",
  host: "0.0.0.0",
  allowedHosts: ["mcp.example.com"],
  allowedOrigins: ["https://app.example.com"],
  cors: {
    origin: ["https://app.example.com"],
    methods: ["GET", "POST", "DELETE", "OPTIONS"],
    allowedHeaders: [
      "content-type",
      "authorization",
      "mcp-protocol-version",
    ],
  },
});

server.get("/health", (c) => c.json({ ok: true }));
await server.listen();
```