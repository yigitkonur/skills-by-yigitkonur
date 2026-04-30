# Service topology — pick the shape

Pick the service shape based on the project's runtime needs. The Makefile's `WEB_SERVICES :=` line follows from this decision.

## Shape decision tree

| Project shape | `WEB_SERVICES` | Why |
|---|---|---|
| Stateless Next.js, no background jobs | `web` | One process, one URL |
| Next.js + BullMQ workers / SSE keep-alives | `web worker` | Workers need long-running process; web tier shouldn't run them |
| Next.js + workers + scheduled jobs | `web worker cron` | Cron is a separate service in Railway (no `--cron` flag) |
| Multi-tenant: auth + noauth deploys from same image | `web web-noauth` | Different env per service, same Dockerfile |
| Microservices: web + api + worker | `web api worker` | Each service has its own URL, env, logs |

## The web + worker pattern (zeo-radar canonical)

Two services from the **same image**, distinguished by an env var:

```Dockerfile
# Single Dockerfile builds both
FROM node:24-alpine
# ... build steps ...
CMD ["./scripts/start.sh", "&&", "npm", "start"]
```

Service config:

| Service | Env | Custom Start Command (Railway UI) |
|---|---|---|
| `web` | `ZEO_ROLE=web` | (default) `./scripts/start.sh && npm start` |
| `worker` | `ZEO_ROLE=worker` | `sh -c "./scripts/start.sh && ZEO_ROLE=worker npm run worker"` |

The app code branches on `ZEO_ROLE` to decide which queue consumers to attach. The web tier short-circuits worker registration via:

```ts
function shouldRunWorkers(): boolean {
  if (process.env.ZEO_ROLE === "worker") return true;
  if (process.env.ZEO_ROLE === "web") return false;
  // Legacy fallback for unset env
  return process.env.RAILWAY_SERVICE_NAME?.includes("worker") ?? false;
}
```

Deploy order: **worker first, then web**. BullMQ dedup + outbox patterns make the crossover safe.

## Multi-tenant: auth + noauth

Two services, same image, different `AUTH_ENABLED`:

| Service | `AUTH_ENABLED` | `SOFT_GATE_PASSWORD` | Use case |
|---|---|---|---|
| `web` | `true` | (unset) | Production users, Clerk-gated |
| `web-noauth` | `false` | `<password>` | Internal demos, staging, QA |

Both use the same `WEB_SERVICES := web web-noauth` and deploy in parallel.

## When NOT to add a worker service

- The job is idempotent and < 1 second → run inline in the request handler.
- The job runs on a cron schedule with no event triggers → use Railway Cron service, not a long-running worker.
- The job is truly one-off (data backfill) → `railway run -- npm run backfill` from the CLI, no service needed.

## Cron service shape

Railway Cron is a service type that runs your container on a schedule (instead of as a long-running process). Setup:

1. Create the service via Railway UI (CLI doesn't manage cron schedule).
2. Set the start command to your cron entrypoint.
3. Set the schedule in Railway UI → Service Settings → Cron.

The Makefile pattern is the same — just include the cron service in `WEB_SERVICES`. It deploys identically; Railway invokes it on schedule, not continuously.

See `references/cron-services.md` for setup details.

## Naming conventions

- Lowercase, dash-separated (`zeo-radar-auth`, `web-noauth`)
- Avoid generic names (`app`, `api`) in shared organizations — they collide
- Suffix the role (`web`, `worker`, `cron`, `noauth`) for clarity in `railway service status`
- For multi-tenant: prefix with the tenant (`acme-web`, `acme-worker`)

## Inter-service references

When `web` needs to reach `worker` directly (rare — usually they communicate via shared Redis), use the Railway-internal hostname:

```
http://worker.railway.internal:PORT
```

For `web` → DB, use the env var Railway injects:

```
${{Postgres.DATABASE_URL}}    # in Railway env config
```

See `references/cross-service-refs.md` for the full reference syntax and when to use private vs public URLs.
