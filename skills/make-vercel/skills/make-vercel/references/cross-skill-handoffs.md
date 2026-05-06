# Cross-skill handoffs

## "I want a friendly local URL"

Route to **`make-local`**. Tailscale Serve / portless / plain LAN bind.

For `vercel dev` (Vercel's local-emulation server) — that's a different tool, not part of these skills. It runs the Vercel runtime locally; useful for testing edge functions before deploy. Not a substitute for `make local`.

## "I have BullMQ workers / SSE / WebSocket — Vercel feels wrong"

Route to **`make-railway`**. The decision matrix in `references/vercel-vs-railway.md` covers when. Short answer: anything with a long-running process, anything that consumes from a queue, anything that holds connection state.

Hybrid: `make-vercel` for the web tier + `make-railway` for the worker tier. See the "split" pattern in `vercel-vs-railway.md`.

## "How do I run a `vercel` CLI command I forgot?"

No first-party `use-vercel` skill exists yet (as of this writing). Defer to:

- `vercel --help` (built-in)
- https://vercel.com/docs/cli (canonical)

If a `use-vercel` skill is added later, route there for CLI questions and keep this skill focused on the Makefile workflow.

## "I want CI/CD via GitHub Actions for Vercel"

Vercel's Git integration handles this automatically — push to your linked Git provider, Vercel deploys. Per-PR previews + production from main. No GitHub Actions needed for the deploy.

If you want pre-push checks (typecheck, lint, test) before Vercel sees the push, use the **`make-railway`** skill's git-hook installer (the hooks are deploy-target-agnostic).

## "I want to deploy from CI to Vercel (skip the auto-deploy)"

Disable Vercel's git auto-deploy in dashboard, then in your CI:

```bash
npm install -g vercel
vercel deploy --prod --token=$VERCEL_TOKEN --yes
```

Use `VERCEL_TOKEN` from https://vercel.com/account/tokens. Same pattern as Railway's CI deploy.

## "I want to migrate Vercel → Railway (or vice versa)"

Out of scope. The destination is the same Make target shape; the source decommission is per-platform.

Quick notes:
- Vercel → Railway: lose preview deploys (build them yourself in CI), gain long-running processes
- Railway → Vercel: lose Docker, lose workers (move to a separate Railway/Render instance), gain edge + free preview deploys

## "Should I use Cloudflare Workers / Netlify / Render instead?"

These skills don't cover those. Quick orientation:

- **Cloudflare Workers** — like Vercel Edge Functions but Cloudflare's whole ecosystem. Good if you're already in Cloudflare-land (R2, KV, D1, Durable Objects).
- **Netlify** — Vercel competitor. Mature, less Next.js-optimized. Pick if you have a strong Netlify reason; otherwise Vercel.
- **Render** — Railway competitor. Different pricing model. Mostly equivalent feature set.

For these, build a custom Makefile from scratch. The shape (pre-flight, deploy, verify, env management) is the same; the CLI commands differ.
