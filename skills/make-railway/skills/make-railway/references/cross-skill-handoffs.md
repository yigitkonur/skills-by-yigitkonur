# Cross-skill handoffs

## "I want to run a `railway` CLI command"

Defer to **`use-railway`**. That skill is the canonical CLI reference (deploys, logs, environments, linking, scaling, SSH, database access). `make-railway` covers the *workflow* of authoring deploy targets; `use-railway` covers the *CLI* itself.

Examples that route to use-railway:
- "How do I `railway link` to a project?"
- "What does `railway run` do?"
- "How do I open a Postgres shell?"
- "Difference between `railway service status` and `railway status`?"

## "I want a friendly local URL"

Route to **`make-local`**. Tailscale Serve / portless / plain LAN bind, with the HSTS-preload trap, port-conflict detection, and dev-bypass recipes.

## "Should this go on Vercel instead?"

Route to **`make-vercel`** — the decision matrix lives there. Quick rule:

| Workload | Pick |
|---|---|
| Pure-static + serverless Next.js, Edge runtime | Vercel |
| Long-running process (BullMQ, SSE keep-alive > 5min, WebSocket) | Railway |
| Background queue consumer | Railway |
| Cron jobs | Railway Cron (no Vercel equivalent that's free) |
| Marketing/blog Next.js | Vercel (preview deploys per PR are killer) |
| Mixed: web + workers | Both — web on Vercel, workers on Railway |

## "I want CI/CD via GitHub Actions instead of git hooks"

Out of scope here. The git-hook approach is documented because it's the zero-CI-vendor-lock-in alternative. Actions has its own conventions.

If you're adding both: have hooks call the same scripts Actions calls (`scripts/test.sh`, `scripts/lint.sh`). Don't drift.

## "I want to deploy from CI to Railway"

Use `RAILWAY_TOKEN` (project token) in CI:

```yaml
# .github/workflows/deploy.yml (sketched)
- run: railway up --service web --detach
  env:
    RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

The `make prod` Makefile works in CI too — no different from local invocation. CI just exports `RAILWAY_TOKEN` instead of using `railway login`.

## "I need to migrate from Heroku / Render / Fly to Railway"

Out of scope. The destination is the same (Makefile + `railway up`), the source decommission is per-platform.
