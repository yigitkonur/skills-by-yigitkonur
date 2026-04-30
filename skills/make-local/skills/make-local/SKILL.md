---
name: make-local
description: Use skill if you are authoring a `make local` or `make tunnel` target for Next.js/Node projects, picking between Tailscale Serve, portless, and plain LAN binding.
---

# Make Local

Author the Makefile that gives a developer a stable, friendly URL for local dev — across reboots, across worktrees, across devices on their tailnet. Replaces `localhost:3000` with `https://<name>.localhost` (portless) or `http://<node>.ts.net` (Tailscale Serve).

## How to think about this

The default `next dev` flow has three real problems:
1. **Port memorization.** Devs end up with sticky-notes mapping projects to ports because OrbStack/Postgres/Redis/another dev server collide.
2. **Loopback isolation.** `localhost` and `*.localhost` are bound to `127.0.0.1` per RFC 6761 — phones, tablets, secondary laptops can't reach them.
3. **Cookie/storage pollution.** Multiple projects on `localhost` share cookies and IndexedDB, leaking auth state.

The fix is a per-project named URL backed by a real cert. Two paths:

- **portless** (single machine, daily driver) — installs a local CA, binds :443, gives you `https://<name>.localhost` with HTTP/2. First-run sudo prompt for cert trust + port bind, silent thereafter.
- **Tailscale Serve** (cross-device) — proxies `http://<node>.ts.net` to your local port, reachable from any device signed into your tailnet. Real Let's Encrypt cert if you opt into HTTPS.

The third path (`make local-lan`, plain `0.0.0.0:PORT`) is the universal fallback for headless CI, phones on the same Wi-Fi when MagicDNS isn't resolving, and tools that can't follow `.localhost` certs.

## Use this skill when

- The user asks for "make local", "local dev script", "tunnel for dev server", "share my dev server with phone/teammate", "stable URL for development".
- A Next.js / Node project needs cross-device dev access (mobile testing, remote pair, demo to a stakeholder on the same tailnet).
- Port conflicts or auth-cookie collisions are recurring pain.

## Do not use this skill when

- The user wants production deployment — route to `make-railway` or `make-vercel`.
- The user wants to set up Tailscale itself or troubleshoot tailnet connectivity — that's outside scope; this skill assumes Tailscale is signed in.
- The project is already shipping; this is a dev-experience skill, not a runtime change.

## Workflow

### 1. Detect what you're working with

Before writing a single Make target, capture the project's current state:

```bash
# Framework + dev script
cat package.json | jq -r '.scripts.dev'

# What port the app currently uses (default 3000 / 3107 / 3456 / etc.)
grep -rE '"dev":|--port|PORT' package.json next.config.* 2>/dev/null | head -5

# Auth library (matters for the dev-bypass section)
grep -E '"@clerk/nextjs"|"next-auth"|"@auth/" ' package.json | head

# Tailscale state
tailscale status --json 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); s=d['Self']; print(s.get('HostName'), '·', s.get('DNSName','').rstrip('.'))"

# Is portless installed
which portless || echo "(install: npm install -D portless)"
```

If any check fails, that's a precondition — surface it to the user before generating the Makefile, don't generate something that will break on first run.

### 2. Pick the path based on requirements

Use the decision tree in `references/path-decision.md`. Default ranking:

1. If user wants HTTPS + cross-device → **Tailscale Serve** (`make tunnel`)
2. If user wants stable name on this machine only → **portless** (`make local`)
3. If user wants raw LAN-IP access for phone-on-Wi-Fi → **plain bind** (`make local-lan`)

The strongest Makefile gives all three — let the user pick per invocation. The zeo-radar Makefile (this skill's canonical example) ships all three side-by-side.

### 3. Generate the Makefile

Use the template in `references/makefile-template.md`. Replace these placeholders:

| Placeholder | What to replace with |
|---|---|
| `PROJECT_NAME` | The portless URL prefix → `<name>.localhost`. Use the npm package name without scope. |
| `PORT` | The dev port for `make local-lan`. Pick something far from 3000 (OrbStack squat zone). |
| `TUNNEL_PORT` | The dev port for `make tunnel`. Different from `PORT` so both can run. |
| `TS_HOSTNAME` | Output of `tailscale set --hostname=...` — defaults to current hostname. |
| `DEV_CMD` | Usually `npm run dev`. Adjust for `pnpm dev` / `bun dev`. |

### 4. Wire portless config

Create `portless.json` at repo root with the project name:

```json
{ "name": "PROJECT_NAME" }
```

That alone makes the URL `https://PROJECT_NAME.localhost`. Don't pass `--name` flags everywhere; the config is single-source-of-truth.

### 5. Wire `next.config.ts` allowedDevOrigins (Next 16+)

For tunnel hostnames to load HMR/_next assets, they MUST be listed verbatim in `next.config.ts`:

```ts
allowedDevOrigins: [
  "PROJECT_NAME",                       // portless short
  "PROJECT_NAME.localhost",             // portless FQDN
  "TS_HOSTNAME",                        // tailnet short MagicDNS
  "TS_HOSTNAME.<tailnet>.ts.net",       // tailnet FQDN
],
```

Next 16 does **exact-match** (not suffix-match), so list every form the agent might hit. Without this, the dev overlay flashes "Blocked cross-origin request to /_next/webpack-hmr" and HMR breaks silently.

### 6. Address auth gating if present

If the project uses Clerk or another auth wall, the Make targets must give the user a path to skip it for local work. See `references/dev-bypass-recipes.md` for Clerk's `AUTH_ENABLED=false` + `SOFT_GATE_PASSWORD` pattern.

### 7. Run detection + first-launch test

```bash
make local
# Should print all reachable URLs, start docker (postgres/redis) if compose exists, hand off to dev server
```

Verify each printed URL actually loads in the user's browser before declaring done.

## Decision rules

- Two paths is wrong; three paths is right. Always ship `local`, `tunnel`, `local-lan` together. Each one fails for situations the other two cover.
- Default `make local` to portless, not Tailscale. Reason: portless requires zero account/sign-in. Tailscale needs a signed-in tailnet. Beginner devs hit portless and it works; if they want cross-device, they discover `make tunnel` from the help screen.
- Default `make tunnel` to **HTTP**, not HTTPS. **`*.ts.net` is on Chrome's HSTS preload list** — Chrome will refuse plain HTTP and emit `ERR_BLOCKED_BY_CLIENT`. But TLS-fronted-HTTP-backend triggers Next.js EPROTO crashes on every middleware self-fetch. The right default depends on the framework — see `references/hsts-preload-trap.md` for the full decision matrix.
- Never blindly `kill -9` whatever's on a port. Only reclaim if the holder is `node`/`next`/`turbopack`/`next-server`. Anything else (OrbStack, postgres, browser tunnel, GitHub Actions runner) gets reported and refused. See `references/port-hygiene.md`.
- Print every URL up-front. Devs shouldn't have to `ifconfig` or `tailscale status`. The banner is part of the contract.

## Recovery paths

| Symptom | Cause | Fix |
|---|---|---|
| `make local` fails with "Cannot bind to :443" | portless first-run, sudo timed out | Re-run; the system dialog appears once per session |
| Browser shows `ERR_BLOCKED_BY_CLIENT` on tailnet URL | HSTS preload of `*.ts.net` rejects HTTP | Either switch tunnel to HTTPS (`tailscale serve --bg --https=443`) or fix the upstream proxy headers — see `references/hsts-preload-trap.md` |
| Dev server returns 500 with `EPROTO ... wrong version number` | TLS fronting an HTTP backend, middleware self-fetches `https://localhost:PORT` | Switch to `--http=80` mode, OR set `X-Forwarded-Proto: http` rewriting at proxy. See `references/eproto-tls-mismatch.md` |
| Dev overlay: `Blocked cross-origin request to /_next/webpack-hmr from "<host>"` | `allowedDevOrigins` doesn't list this exact host | Add the exact hostname (both short + FQDN forms) to `next.config.ts` |
| `make tunnel` says "tailscale not signed in" | Tailscale daemon up but account not linked | `tailscale up` interactively; this skill doesn't drive that flow |
| Page renders "Internal Server Error" through tunnel but works on `localhost:PORT` | Same crash on both — not a tunnel issue | `tail -f` the dev log; tunnel is innocent |
| Page renders blank with `<html id="__next_error__">` | Next.js error boundary served | Read dev log for the actual error — usually missing DB table, missing env var, mismatched auth keys |
| Port-conflict refusal: "port :PORT held by orbstack" | Something legit is squatting | Pick a different port (`make local PORT=4000`), don't kill OrbStack |

## Customizing the recipe

- **Non-Next frameworks (Express, Hono, Fastify, plain Node):** drop the `allowedDevOrigins` section entirely. The Makefile structure is identical.
- **Vite/SvelteKit/Remix:** Vite reads `--host` not `HOSTNAME`. Adjust the `make local-lan` recipe accordingly. Same banner pattern works.
- **Monorepo with multiple dev servers:** generate one Make target per app (`make local-web`, `make local-admin`). Pick distinct ports + portless names to avoid cookie collision.
- **Project has no Clerk/auth wall:** drop the dev-bypass section entirely.
- **Headless CI:** add a `make ci` that just binds plain `0.0.0.0:PORT`. No tunnel, no portless, no banner.

## Reference routing

| File | Read when |
|---|---|
| `references/path-decision.md` | Choosing between portless, Tailscale Serve, and plain LAN bind for a specific user need. |
| `references/makefile-template.md` | Generating the Make targets — the full template with every placeholder annotated. |
| `references/portless-setup.md` | Wiring portless: `portless.json`, first-run sudo, version pinning via package.json devDependency. |
| `references/tailscale-serve-setup.md` | Wiring Tailscale Serve: HTTP vs HTTPS, Funnel-off enforcement, hostname customization (`tailscale set --hostname=`), MagicDNS resolution. |
| `references/hsts-preload-trap.md` | Why `*.ts.net` HTTPS is mandatory for Chrome but breaks Next 16 middleware via EPROTO; the decision matrix. |
| `references/eproto-tls-mismatch.md` | The Next.js TLS-fronted-HTTP-backend crash, signature, and three workarounds. |
| `references/port-hygiene.md` | Stale-process detection, kill-only-our-own rule, banner conventions, multi-LAN-IP enumeration. |
| `references/dev-bypass-recipes.md` | Clerk soft-gate (`AUTH_ENABLED=false` + `SOFT_GATE_PASSWORD`), env precedence, "all-Next-pages-500" diagnostic. |
| `references/next-config-allowed-origins.md` | The exact-match Next 16 CORS rule, common forms to enumerate, hostname-rename procedure. |
| `references/cross-skill-handoffs.md` | When to hand off to `make-railway` (production), `make-vercel` (alt prod), `use-railway` (CLI commands). |

## Cross-skill handoffs

- After dev works, the user usually wants to deploy. Route to `make-railway` (long-running processes, BullMQ workers, SSE) or `make-vercel` (pure-static + serverless). See `references/cross-skill-handoffs.md` for the decision.
- For raw `railway` CLI questions, defer to `use-railway`.
- For tooling Railway operations beyond deploy (logs, scale, SSH), `use-railway`.

## Guardrails

- Don't write a Makefile that silently kills processes. Always classify the holder first.
- Don't promise HTTPS without checking HSTS implications for the chosen domain.
- Don't generate `next.config.ts` edits without preserving the user's existing `allowedDevOrigins` entries — append, never replace.
- Don't enable Tailscale Funnel by default. Funnel exposes the dev server to the public internet; it must be opt-in with explicit user consent.

## Final checks

Before declaring done:

- [ ] `make help` shows all three targets (`local`, `local-lan`, `tunnel`) with one-line descriptions
- [ ] `make local` actually starts the dev server and prints reachable URLs
- [ ] Every printed URL loads in a real browser (not just curl — Chrome's HSTS rules matter)
- [ ] If the project has auth: a documented path to bypass it for local dev (`/gate` or equivalent)
- [ ] `next.config.ts allowedDevOrigins` contains every tunnel hostname form used
- [ ] `make stop` and `make tunnel-stop` work and clean up serve/funnel config
- [ ] No process is killed unless it's our own (`node`/`next`/`turbopack`)
