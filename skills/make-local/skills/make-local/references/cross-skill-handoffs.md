# Cross-skill handoffs

Where to route the user after `make local` works.

## "I want to deploy this somewhere"

Decision tree:

| Project shape | Skill |
|---|---|
| Pure-static + serverless Next.js, Edge runtime, marketing sites | **make-vercel** |
| Next.js with BullMQ workers, SSE keep-alives, long-running jobs | **make-railway** |
| Backend service (Express/Hono/Fastify), background workers | **make-railway** |
| Worker + web split (zeo-radar pattern) | **make-railway** |
| Mixed: Vercel for web + Railway for workers | both — see `make-vercel` for the split-pattern caveat |

Detail:

- **make-railway** — long-running processes, BullMQ workers, SSE that exceeds Vercel's serverless time limits, Docker-based deploys, Postgres/Redis sidecars
- **make-vercel** — Next.js with Edge runtime, serverless functions, automatic preview deploys per-PR, custom domains via DNS

## "How do I run a Railway CLI command I forgot"

Route to **use-railway**. That skill is the canonical CLI reference (deploy, logs, environments, linking, scaling, SSH, database access). `make-railway` covers the *workflow* of authoring deploy targets; `use-railway` covers the *CLI* itself.

## "My phone can't reach my dev server"

Stay in **make-local**:

- Phone on tailnet → `make tunnel` (HTTPS via Let's Encrypt, real cert)
- Phone on Wi-Fi only → `make local-lan` then open `http://<lan-ip>:PORT/`

## "I want to share dev with a stakeholder outside my tailnet"

Tailscale Funnel exposes `tailscale serve` to the public internet:

```bash
tailscale funnel --bg PORT
```

⚠️ Requires explicit user consent — never default to this. The dev server is now on the open internet with whatever security the app provides. Reset before exiting:

```bash
tailscale funnel reset
```

`make tunnel-stop` already resets both serve and funnel. Use it religiously.

## "I want a stable URL for browser-based AI agents to test"

`make tunnel` (with `TUNNEL_TLS=1` if the agent uses Chrome — HSTS preload of `*.ts.net` requires HTTPS). The URL is stable across reboots, so the agent doesn't need to re-discover it each session.

## "I want CI/CD via git hooks instead of GitHub Actions"

That's in **make-railway**'s scope (`make install-hooks`). The pattern works for Vercel too but Vercel's auto-deploy from GitHub is usually preferred there.
