# Network and Firewall Issues

For corporate networks, locked-down environments, or weird connection issues.

## Domains TinaCloud needs

Editors loading `/admin` need outbound HTTPS to:

| Domain | Purpose |
|---|---|
| `app.tina.io` | Login / OAuth flow |
| `content.tinajs.io` | GraphQL API |
| `assets.tinajs.io` | Admin SPA assets |
| `*.tinajs.io` | Various subdomains |

Build environment (CI) needs:

| Domain | Purpose |
|---|---|
| `content.tinajs.io` | Schema validation |
| `registry.npmjs.org` | Package install |
| `github.com` / `api.github.com` | Git operations |

## Corporate firewall allowlist

Allow HTTPS (443) outbound to:

```
*.tina.io
*.tinajs.io
app.tina.io
content.tinajs.io
assets.tinajs.io
```

Or just `*.tinajs.io` and `*.tina.io` if your firewall supports wildcards.

## Editor proxy testing

```bash
# From editor's machine
curl -I https://app.tina.io
curl -I https://content.tinajs.io
curl -I https://assets.tinajs.io

# All should return 200/302/3xx, not connection-refused
```

## Common firewall patterns

| Issue | Fix |
|---|---|
| Wildcard not supported | Allowlist specific domains |
| TLS inspection / MITM proxy strips auth | Add TinaCloud to bypass list |
| Port blocking | Ensure 443 outbound is open |

## Mixed content errors

**Symptom:** Admin doesn't load; browser console shows "Mixed Content" warnings.

**Cause:** Your site is over HTTPS but admin tries to load HTTP resources, or vice versa.

**Fix:**

- Always serve over HTTPS in production
- Check `NEXT_PUBLIC_SITE_URL` env var is `https://...`
- Vercel auto-provides SSL — don't override

## CORS errors

**Symptom:** `Access-Control-Allow-Origin` errors in browser.

**Cause:** TinaCloud's CORS policy rejects your origin (rare — TinaCloud generally allows authenticated cross-origin requests).

**Fix:**

- Use HTTPS
- Don't run admin on a totally different origin from your site (use subdomains, not separate domains)

## Self-hosted: CORS for the backend

For self-hosted projects, the `/api/tina/gql` route runs on your domain — same-origin, no CORS issue.

If you split admin and site to different origins:

```typescript
// app/api/tina/[...routes]/route.ts
const handler = async (req: Request) => {
  const response = await baseHandler(req)
  response.headers.set('Access-Control-Allow-Origin', 'https://admin.example.com')
  response.headers.set('Access-Control-Allow-Credentials', 'true')
  response.headers.set('Vary', 'Origin')
  return response
}
```

## Air-gapped environments

For environments with no outbound internet:

- TinaCloud doesn't work (requires reaching `content.tinajs.io`)
- Self-hosted partially works but admin SPA assets are CDN-served
- For full air-gap, you need to host the admin SPA assets on your own infrastructure

This is non-trivial. Consult TinaCMS Enterprise sales for air-gap options.

## SSH proxy / VPN

If editors access TinaCloud through a VPN or SSH proxy:

- VPN must allow TinaCloud egress
- DNS resolution should work for `*.tinajs.io`
- Some corporate VPNs do MITM TLS — exempt TinaCloud domains

## DNS issues

**Symptom:** Domain not resolving.

**Diagnostic:**

```bash
nslookup app.tina.io
dig content.tinajs.io
```

Should resolve to AWS/CloudFront IPs. If it fails, your DNS is filtered.

## Common mistakes

| Mistake | Fix |
|---|---|
| Firewall blocks `*.tinajs.io` | Allowlist explicitly |
| HTTP / HTTPS mismatch | Always HTTPS in production |
| Corporate proxy strips auth tokens | Bypass for TinaCloud |
| VPN doesn't include `*.tina.io` egress | Add to VPN routes |
| Air-gap deployment | Consult Enterprise sales |
