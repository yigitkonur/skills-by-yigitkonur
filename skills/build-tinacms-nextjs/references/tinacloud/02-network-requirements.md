# Network Requirements

Domains that need to be reachable from editors' browsers and from your build/runtime environment.

## Editor browser

Editors loading `/admin/index.html` need to reach:

| Domain | Purpose |
|---|---|
| `app.tina.io` | Login / OAuth flow |
| `content.tinajs.io` | GraphQL API |
| `assets.tinajs.io` | Admin SPA static assets |
| `tina.io` | Documentation links |
| `*.tinajs.io` | Various subdomains |

## Build environment

CI builds (`tinacms build`) need:

| Domain | Purpose |
|---|---|
| `content.tinajs.io` | Schema validation |
| `registry.npmjs.org` | Package install |
| GitHub | Source repo access |

## Runtime (deployed app)

Server-side queries from your deployed app:

| Domain | Purpose |
|---|---|
| `content.tinajs.io` | GraphQL queries (server-side) |

## Corporate firewall allowlist

If editors are behind a corporate proxy/firewall:

```
Allow:
  *.tina.io
  *.tinajs.io
  app.tina.io
  content.tinajs.io
  assets.tinajs.io
```

Allow HTTPS (443) outbound to these domains.

## CORS

Your deployed app's domain doesn't need to be in any allowlist on TinaCloud's side — TinaCloud's GraphQL API accepts cross-origin requests from authenticated clients.

For self-hosted backends (`/api/tina/gql` on your own domain), CORS is automatically handled by the Next.js route — no extra config.

## SSL / TLS

All TinaCloud endpoints are HTTPS-only. Your deployed app should be HTTPS too — mixed-content errors block the admin from loading on insecure origins.

## Editor proxy testing

If editors report "admin won't load":

```bash
# From the editor's machine:
curl -I https://app.tina.io
curl -I https://content.tinajs.io
curl -I https://assets.tinajs.io
```

All should return 200/302, not connection-refused or 403.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Firewall blocks `*.tinajs.io` | Admin doesn't load | Allowlist domain |
| Mixed content (HTTP page, HTTPS admin) | Admin blocked by browser | Serve site over HTTPS |
| Corporate proxy strips authentication headers | Auth fails | Whitelist or bypass for TinaCloud |
| Different domain in dev (localhost) and prod | Cookies don't match | Expected — use Draft Mode flow per env |
