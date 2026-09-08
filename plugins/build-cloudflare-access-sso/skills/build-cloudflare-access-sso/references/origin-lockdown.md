# Origin lockdown — making Access unbypassable

Cloudflare Access runs at Cloudflare's edge. A request that reaches your origin without passing
through Cloudflare never sees it. This file closes that hole.

## Prove the hole first

```bash
ORIGIN=<origin-ip>
curl -skI --resolve app.example.com:443:$ORIGIN https://app.example.com/ | head -1
curl -sI  --resolve app.example.com:80:$ORIGIN  http://app.example.com/  | head -1
```

`200` means anyone who knows the IP can use the app right now, fully unauthenticated. Record the
before/after — it is the only evidence that the lockdown did anything.

**The origin IP is not a secret.** It is discoverable through certificate-transparency logs,
historical DNS, `*.sslip.io` / `*.nip.io` hostnames pointing at the same box, mail headers,
misconfigured subdomains, and internet-wide scan databases. Any control that depends on the IP
staying unknown is not a control.

## Layer 1 — allow only Cloudflare's ranges

Fetch the ranges; never hardcode them.

```bash
curl -s https://api.cloudflare.com/client/v4/ips \
  | jq -r '.result.ipv4_cidrs[], .result.ipv6_cidrs[]' | paste -sd, -
```

Add your own admin path too (VPN CGNAT such as `100.64.0.0/10` for Tailscale, an office range, or
the host's own address) or you will lock yourself out of local debugging.

### Traefik v3 (Docker labels)

```yaml
labels:
  # v3 spells it `ipallowlist`; v2 called it `ipwhitelist`. Wrong spelling = silently no middleware.
  - traefik.http.middlewares.cf-only.ipallowlist.sourcerange=<comma-separated CIDRs>,100.64.0.0/10
  - traefik.http.routers.myapp-websecure.middlewares=cf-only@docker
  - traefik.http.routers.myapp-web.middlewares=redirect-to-https@file,cf-only@docker
```

Attach to **both** the `web` and `websecure` routers. Attaching only to `websecure` leaves plain
HTTP :80 answering before the redirect.

If Traefik sits behind another proxy, its idea of the client IP comes from
`entryPoints.*.forwardedHeaders.trustedIPs` — get that wrong and the allowlist matches the wrong
address.

### nginx

```nginx
# inside the server block for app.example.com
include /etc/nginx/cloudflare-ips.conf;   # generated: `allow <cidr>;` per line
allow 100.64.0.0/10;
deny  all;

# so logs and any app-side checks see the real client
real_ip_header CF-Connecting-IP;
# plus `set_real_ip_from <cidr>;` for each Cloudflare range
```

Regenerate `cloudflare-ips.conf` on a schedule and `nginx -t && nginx -s reload`.

### Caddy

```caddyfile
app.example.com {
    @not_cf not remote_ip <cidr> <cidr> … 100.64.0.0/10
    respond @not_cf 403
    reverse_proxy localhost:3000
}
```

### Cloud firewall / security group

Equivalent and often better: restrict :80 and :443 at the network layer to the Cloudflare ranges
plus your admin range. This survives application-layer misconfiguration. Use it *and* a proxy rule
if you can.

## Layer 2 — validate the Access JWT at the origin

IP allowlists fail open in one specific way: any *other* Cloudflare customer's traffic also
originates from those ranges. Token validation closes that.

Cloudflare injects `CF-Access-Jwt-Assertion` (and a `CF_Authorization` cookie) on requests it has
authorized. The origin verifies the JWT against the team's public keys:

```
https://<team-name>.cloudflareaccess.com/cdn-cgi/access/certs
```

Check, at minimum: signature against the JWKS, `aud` equals the application's AUD tag (Zero Trust →
the app's Overview), `iss` equals `https://<team-name>.cloudflareaccess.com`, and `exp`.

Cloudflare's own libraries and middleware exist for most stacks; `cloudflared` exposes this as
**Protect with Access** when you are tunnelling. If your app cannot be modified, an
auth-request/forward-auth step in the reverse proxy can do the verification instead.

## The PaaS split-brain hazard

Dokploy, Coolify, CapRover, Portainer stacks and similar control planes **regenerate** Traefik
router labels from their own database on every deploy, overwriting the
`traefik.http.routers.*.middlewares` value in your compose file.

Result:

- The middleware **definition** (`traefik.http.middlewares.cf-only.*`) lives in git and survives.
- The router **attachment** lives in the control plane's database and does not.

If a domain record is recreated or reset, the allowlist detaches with **no error anywhere** — the
container is healthy, the middleware still exists, nothing is attached to it, and the bypass is
open again.

Handle it by:

1. Re-attaching the middleware through the control plane's own API or UI (its domain/route record
   usually has a `middlewares` field), not only in the compose file. Many of these APIs reject
   partial updates — send the full record.
2. Writing the exact re-attach command into the repo's `AGENTS.md`, since it is not in git.
3. Adding check 2 from `verification-matrix.md` to post-deploy smoke tests, so a detach is caught
   by CI rather than by an incident.

## Keeping it fresh

- Cloudflare publishes new ranges occasionally. Re-fetch `/client/v4/ips` on a schedule and diff.
- Re-run the bypass check after every deploy, proxy upgrade, and DNS change.
- If you ever set the DNS record back to DNS-only for debugging, the origin allowlist is what stops
  it from becoming an outage-shaped security incident — leave it in place.
