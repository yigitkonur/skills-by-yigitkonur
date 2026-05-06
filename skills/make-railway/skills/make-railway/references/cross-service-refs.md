# Cross-service references

Services within a Railway project communicate via:

1. **Env templating** in the Railway dashboard (`${{Service.VAR}}`)
2. **Private domain** for in-cluster networking (`<svc>.railway.internal`)
3. **Public domain** for cross-environment / local dev (`<svc>.up.railway.app` or custom)

## The three hostnames

| Hostname | Resolves to | When to use |
|---|---|---|
| `<svc>.railway.internal` | Private IPv6 inside Railway's network | Inter-service calls within same project + environment |
| `<svc>.up.railway.app` | Public Railway edge | External traffic from anywhere |
| `<custom-domain>` | Public Railway edge | Production user-facing URL |

The DB equivalents:

| Var | Provided by | Form |
|---|---|---|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` | `postgresql://...@postgres.railway.internal:5432/railway` |
| `DATABASE_PUBLIC_URL` | `${{Postgres.DATABASE_PUBLIC_URL}}` | `postgresql://...@shortline.proxy.rlwy.net:NNNNN/railway` |

## Env templating syntax

In Railway dashboard → Service → Variables:

```
DATABASE_URL = ${{Postgres.DATABASE_URL}}
REDIS_URL    = ${{Redis.REDIS_URL}}
APP_URL      = ${{web.RAILWAY_PUBLIC_DOMAIN}}
```

Templates resolve at deploy time (not at runtime). Variables not in the same project return empty.

The CLI sees the resolved values:

```bash
railway variables --service web --kv | grep "^DATABASE_URL="
# DATABASE_URL=postgresql://...@postgres.railway.internal:5432/railway
```

## When private vs public matters

**Use private (`*.railway.internal`):**
- Web service → DB
- Web service → Redis
- Worker service → DB
- Inter-service HTTP within Railway

Why: faster (no Railway edge hop), free (no egress charges), more secure (not on public internet).

**Use public (`shortline.proxy.rlwy.net` / `*.up.railway.app`):**
- Local dev pointing at production data (`.env.local`)
- Migrations from a contributor's laptop (`prisma migrate deploy` against prod)
- External services that need to call your API
- CI/CD runners outside Railway

## Pulling public URL for local dev

```bash
# DB
railway variables --service postgres --kv | grep "^DATABASE_PUBLIC_URL=" | cut -d= -f2-

# Redis
railway variables --service redis --kv | grep "^REDIS_PUBLIC_URL=" | cut -d= -f2-
```

Save to `.env.local` for local-against-prod debugging:

```sh
# .env.local
# REMOTE-DB MODE — local dev hits Railway production data
DATABASE_URL=postgresql://...@shortline.proxy.rlwy.net:NNNNN/railway
REDIS_URL=redis://...@interchange.proxy.rlwy.net:NNNNN
```

⚠️ All mutations land on production. Mark this clearly in `.env.local`.

## Worker → Web HTTP (rare)

If `worker` needs to call `web`'s API directly (rare — usually they share Redis), use the private domain:

```ts
// In worker code
const webUrl = `http://${process.env.WEB_PRIVATE_HOST || 'web.railway.internal'}:${process.env.WEB_PRIVATE_PORT || 3000}`;
fetch(`${webUrl}/api/internal/something`);
```

Set `WEB_PRIVATE_HOST` and `WEB_PRIVATE_PORT` in Railway env via templating. Don't hard-code.

## DNS gotchas

- `*.railway.internal` resolves to **IPv6 only**. If your code uses Node's default DNS resolver, IPv6 should work. If you've forced IPv4 somewhere (`socket.connect({ family: 4 })`), it'll fail.
- DNS changes (new service, renamed) propagate within seconds inside Railway. Externally (custom domain), expect 60s-5m for new domains.

## When NOT to use cross-service refs

- One-off scripts (use the public URL or `railway run -- npm run script`)
- Local dev (always use public URL)
- Cross-environment (private domains don't span environments)

## Multi-project

Cross-project refs aren't supported. If `project-a` needs `project-b`'s DB, expose a public URL on `project-b` and configure `project-a` to consume it via plain env.
