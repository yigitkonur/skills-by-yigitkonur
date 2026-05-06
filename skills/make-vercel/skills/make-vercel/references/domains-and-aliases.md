# Domains and aliases on Vercel

Two distinct concepts:

- **Domains** — your owned domains (e.g., `acme.com`)
- **Aliases** — pointers from a domain to a specific deployment

## Adding a domain

```bash
vercel domains add acme.com
```

Vercel issues DNS instructions:

```
Configure your DNS:
  Type: A
  Name: @
  Value: 76.76.21.21

  Type: CNAME
  Name: www
  Value: cname.vercel-dns.com
```

Update your DNS provider; verify:

```bash
vercel domains inspect acme.com
```

Shows `Status: Verified` once DNS propagates (5min - 24h depending on TTL).

## Assigning to production

After domain is verified, link it to the project:

```bash
# Auto-aliases new production deploys to acme.com
vercel domains add acme.com
vercel alias acme.com my-project.vercel.app   # if not auto-assigned
```

Production deploys (`vercel --prod`) automatically alias to all domains assigned to the project. No manual aliasing per deploy.

## Preview domain aliasing

By default, preview deploys get unique URLs (`my-project-abc123.vercel.app`). To assign a stable preview URL (e.g., `staging.acme.com`):

```bash
# After a preview deploy
PREVIEW=$(vercel deploy --yes 2>&1 | grep -oE 'https://[^ ]+\.vercel\.app' | tail -1)
vercel alias $PREVIEW staging.acme.com
```

Or in CI for the staging branch:

```yaml
- run: |
    PREVIEW=$(vercel deploy --yes --token=$VERCEL_TOKEN | tail -1)
    vercel alias $PREVIEW staging.acme.com --token=$VERCEL_TOKEN
```

## Subdomain wildcards

Vercel supports `*.acme.com` for multi-tenant setups:

```bash
vercel domains add "*.acme.com"
```

Each subdomain (e.g., `customer1.acme.com`) routes to your project; the app reads `req.headers.get('host')` to differentiate tenants.

DNS:

```
Type: CNAME
Name: *
Value: cname.vercel-dns.com
```

## Removing

```bash
vercel domains rm acme.com
# or remove just an alias
vercel alias rm acme.com
```

## DNS providers

- **Cloudflare:** set the records, then DISABLE Cloudflare's proxying for these (orange cloud → grey). Vercel needs direct DNS to issue cert.
- **Route 53 / Cloudflare DNS / etc.:** Vercel works with all standard DNS providers. ALIAS records (Route 53 specific) work; CNAME at apex doesn't.
- **Apex CNAME workaround:** Vercel offers `CNAME` flattening via their nameservers (`ns1.vercel-dns.com`, `ns2.vercel-dns.com`). Switch your domain to use Vercel as DNS.

## SSL certificates

Auto-issued via Let's Encrypt within minutes of DNS verification. Renewed automatically. No manual cert management.

For wildcard certs, Vercel uses DNS-01 challenge — you may need to add a TXT record temporarily.

## Custom 404s and redirects

Use `vercel.json` for redirects:

```json
{
  "redirects": [
    { "source": "/old-page", "destination": "/new-page", "permanent": true },
    { "source": "/blog/:slug", "destination": "/posts/:slug", "permanent": true }
  ]
}
```

For Next.js, prefer `next.config.ts` `async redirects()`. Same effect; lives with the app.

## Inspecting

```bash
# Show all domains assigned to current project
vercel domains ls

# Inspect one
vercel domains inspect acme.com

# Show all aliases for the current project
vercel alias ls
```

## Removing a wrong assignment

If you accidentally aliased a preview to production:

```bash
# Unset
vercel alias rm acme.com

# Re-alias to production deploy
vercel alias <prod-deployment-url> acme.com
```

## Don't aliases break the deploy URL?

The unique `<project>-abc123.vercel.app` URL stays available alongside any aliases. So `acme.com` and `my-project-abc123.vercel.app` both point to the same deployment.
