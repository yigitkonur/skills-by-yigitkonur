# Observability

After deploy, you need to see what's happening. Railway provides logs + service status; for app-level observability, wire Sentry/Logtail/PostHog.

## `make logs` and friends

```makefile
logs:
	@railway logs --service $(firstword $(WEB_SERVICES)) --tail 50

logs-worker:
	@railway logs --service worker --tail 50

logs-tail:
	@railway logs --service $(firstword $(WEB_SERVICES))   # follows
```

`--tail N` shows last N lines. Without `--tail`, follows live (no exit). Press Ctrl+C to stop.

## Filtering logs

`railway logs` doesn't have grep built in. Pipe:

```bash
railway logs --service web --tail 1000 | grep -iE "error|throw|exception" | head
```

For structured logs (pino/winston JSON output):

```bash
railway logs --service web --tail 1000 | jq -c 'select(.level == "error")'
```

## Service status

```makefile
status:
	@railway service status --all
```

Output shape:

```
geo-tracker-redis    | 84f85c61-... | SUCCESS
zeo-radar-auth       | 3b2816d6-... | SUCCESS
zeo-radar-noauth     | fd132c0d-... | SUCCESS
geo-tracker-db       | 2ca0d760-... | SUCCESS
```

States: `SUCCESS`, `FAILED`, `BUILDING`, `DEPLOYING`, `INITIALIZING`, `QUEUED`, `REMOVING`, `WAITING`, `CRASHED`.

## Health checks

Configure in Railway dashboard → Service → Settings → Health Check:

| Field | Notes |
|---|---|
| Path | `/api/health` (or any 200-returning route that doesn't require auth) |
| Healthcheck timeout | 60s (default; raise for slow boots) |
| Restart policy | `ALWAYS` for production; `ON_FAILURE` for cron |

Implementing `/api/health`:

```ts
// app/api/health/route.ts
import { NextResponse } from 'next/server';

export async function GET() {
  // Optional: ping DB to verify it's reachable
  return NextResponse.json({ status: 'ok', uptime: process.uptime() });
}
```

Don't put auth on this route. Don't query DB unless cheap.

## Memory + CPU

Railway dashboard shows RSS/CPU per service. CLI:

```bash
railway service status --all --json | jq '.[] | {name, cpu, memory}'
```

If you see frequent OOM kills (memory > limit), either:

1. Optimize the app (Node memory leak, image processing without streaming)
2. Increase the service's memory limit in Railway dashboard

Default limits depend on your plan. Hobby tier: 512MB. Pro: configurable.

## Wire Sentry

For error tracking:

```bash
npm install @sentry/nextjs
npx @sentry/wizard@latest -i nextjs
```

Set `SENTRY_DSN` env in Railway. Sentry captures unhandled exceptions + custom `Sentry.captureException(err)` calls.

For dev-mode opt-out (skip Sentry overhead in `make local`), see the make-local skill's references/dev-bypass-recipes.md and the `next.config.ts` conditional `withSentryConfig` pattern.

## Wire Logtail / Better Stack / Axiom

For log aggregation outside Railway's web UI:

```bash
# Logtail/Better Stack: sink Railway logs via webhook
# Axiom: similar
```

Set up via Railway dashboard → Project Settings → Webhooks → add the log sink URL.

## Custom dashboards

Railway exposes minimal metrics. For dashboards, ship metrics to:

- **Grafana Cloud** — Prometheus-style, push from app via prom-client
- **Datadog** — agent or HTTP API, more enterprise
- **New Relic** — APM-style, agent-based

Add the agent/SDK to your Dockerfile + env. Out of scope for `make-railway` proper; mention in your project's runbook.

## Deploy webhooks

Railway can POST to a webhook on deploy events:

- Slack (deploy notifications)
- PagerDuty (failure alerts)
- Custom endpoint (analytics)

Configure: Project Settings → Webhooks → Add URL + event types.

For `make prod` to wait for the webhook before declaring done is overkill. Polling `railway service status --all` is sufficient and built into the Makefile template.

## Querying production DB safely

```bash
# Open a Postgres shell against production
railway connect postgres

# Or run a one-off query
railway run -- psql "$DATABASE_URL" -c "SELECT count(*) FROM users;"
```

`railway run` injects all env vars from the linked service into the local command. Useful for ad-hoc scripts:

```bash
railway run -- node scripts/backfill.js
```

Be careful — these are PRODUCTION env vars. Treat any output as production data.

## Quiet observability for `make local`

Local dev shouldn't ship to Sentry/Logtail. Gate the SDK init:

```ts
if (process.env.NODE_ENV === 'production' && process.env.SENTRY_DSN) {
  Sentry.init({ dsn: process.env.SENTRY_DSN });
}
```

Or skip the entire SDK in dev — see make-local's `dev-bypass-recipes.md`.
