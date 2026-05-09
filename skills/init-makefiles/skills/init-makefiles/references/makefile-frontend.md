# Frontend Makefile recipes

Canonical Makefile body for Scenarios A (frontend-only), C (frontend portion when paired with a custom backend), and D (frontend portion when paired with Supabase). Covers local dev, LAN exposure, Tailscale tunnel, Vercel deploy, Vercel env pull, and pre-deploy size guard. Tailscale logic is delegated to `tailscale-funnel-rules.md`; the kill-only-our-own port helper and LAN IP enumerator come from `port-hygiene.md`. The universal preamble (SHELL, ANSI palette, `.ONESHELL`) is in `makefile-base.md`.

## Target inventory

| Target | One-line description |
|---|---|
| `local` | Bind dev server to `127.0.0.1:$(PORT)` and start the framework's dev script |
| `local-lan` | Same as `local` but bind `0.0.0.0` and print every LAN URL |
| `tunnel` | Tailscale Serve on this node — tailnet-only HTTPS/HTTP |
| `tunnel-stop` | Disable our port from Tailscale Serve and Funnel; kill local dev on `$(TUNNEL_PORT)` |
| `funnel` | PUBLIC Tailscale Funnel — gated behind `PUBLIC_FUNNEL=1` |
| `stop` | Kill our own dev process on `$(PORT)` |
| `clean` | `stop` + wipe `.next/cache` (or framework-equivalent) |
| `deploy-vercel` | `vercel link --yes`, `vercel deploy --prod`, `vercel inspect --wait` |
| `verify` | `curl -sI` the prod URL; expect 2xx/3xx |
| `env-pull` | `vercel env pull .env.local` (NOT `vercel pull` — see trap below) |
| `build-check` | Pre-deploy `vercel build --prod` + per-function size sort + 250 MB guard |

Helper targets (prefixed with `_`, hidden from `make help`): `_free-port-%`, `_ensure-services`, `_print-banner-local`, `_print-banner-local-lan`, `_print-banner-tunnel`, `_check-vercel-tokens`. The first three live in `port-hygiene.md`. Tailscale-internal helpers come from `tailscale-funnel-rules.md`.

## Variables

```makefile
PROJECT_NAME ?= $(notdir $(CURDIR))
PORT         ?= 3456
HOST         ?= 127.0.0.1
TUNNEL_PORT  ?= 3457
TUNNEL_TLS   ?= 0
DEV_CMD      ?= npm run dev
VERCEL_PROJECT ?= $(PROJECT_NAME)
VERCEL_TELEMETRY_DISABLED := 1
export VERCEL_TELEMETRY_DISABLED
```

`DEV_CMD` is auto-detected from `package.json#scripts.dev` at scaffold time and inlined verbatim. `PORT` defaults to a non-squat port (3456 / 4321 / 5174 — see `port-hygiene.md`). `VERCEL_PROJECT` defaults to the directory name; override per-invocation if the Vercel project name diverges.

## `local` — localhost-bound dev

Binds the framework's dev server to `127.0.0.1:$(PORT)`. The default. Browser-only access on this machine. No LAN, no tunnel.

```makefile
.PHONY: local
local: _free-port-$(PORT) _ensure-services _print-banner-local
	@HOSTNAME=127.0.0.1 PORT=$(PORT) $(DEV_CMD)
```

Notes:
- `_free-port-$(PORT)` reclaims if the port is held by a `node|next-server|turbo|turbopack|next|bun|deno` process; refuses if held by anything else (suggests `+10` port). See `port-hygiene.md`.
- `_ensure-services` is best-effort `docker compose up -d` if a `docker-compose.yml` or `compose.yml` exists. No-op otherwise. Never fatal.
- `_print-banner-local` prints `http://localhost:$(PORT)` and the stop/clean hint.
- `HOSTNAME=127.0.0.1` forces Next/Vite/Astro to bind loopback even if their default is `0.0.0.0`. Belt and braces.
- Never use `--hostname 0.0.0.0` here. LAN exposure is `local-lan`'s job.

## `local-lan` — LAN-bound dev

Binds the dev server to `0.0.0.0:$(PORT)` so phones / laptops / tablets on the same Wi-Fi can reach it via the host's LAN IP. Use case: real-device mobile testing.

```makefile
.PHONY: local-lan
local-lan: _free-port-$(PORT) _ensure-services _print-banner-local-lan
	@HOSTNAME=0.0.0.0 PORT=$(PORT) $(DEV_CMD)
```

The banner enumerates every reachable IPv4:

```makefile
_print-banner-local-lan:
	@printf "\n$(B)$(G)$(PROJECT_NAME) dev$(Z)  $(D)0.0.0.0:$(PORT) (LAN)$(Z)\n"
	@printf "  $(C)→$(Z) http://localhost:$(PORT)\n"
	@ifconfig 2>/dev/null | awk '/inet / && $$2 != "127.0.0.1" {print $$2}' | head -6 \
	  | while read ip; do printf "  $(C)→$(Z) http://$$ip:$(PORT)  $(D)(LAN)$(Z)\n"; done
	@printf "  $(D)stop:  make stop      cache panic:  make clean$(Z)\n\n"
```

The IP enumerator picks up LAN, tailnet, USB-C ethernet, and virtual interfaces. The phone-on-Wi-Fi user picks the matching IP without thinking. Implementation rationale and squat list in `port-hygiene.md`.

## `tunnel`, `tunnel-stop`, `funnel`

These three targets are defined in full in `tailscale-funnel-rules.md`. Inline summary so this file is self-contained:

- `tunnel` — Tailscale Serve, tailnet-only, default HTTP (`*.ts.net` HSTS preload + Next.js EPROTO interaction means HTTP is the safe default for Next; opt-in `TUNNEL_TLS=1` for HTTPS).
- `tunnel-stop` — disables ONLY our port (`tailscale serve --https=443 $(TUNNEL_PORT) off` and `tailscale funnel $(TUNNEL_PORT) off`) and kills dev on `$(TUNNEL_PORT)`. NEVER runs `tailscale serve reset` or `tailscale funnel reset` — those wipe other projects' mappings.
- `funnel` — public, gated behind `PUBLIC_FUNNEL=1`, refuses any `TUNNEL_PORT` not in `443 | 8443 | 10000`.

Read `tailscale-funnel-rules.md` before generating these recipes.

## `stop` and `clean`

```makefile
.PHONY: stop clean
stop:
	@pid=$$(lsof -ti :$(PORT) 2>/dev/null || true); \
	if [ -n "$$pid" ]; then \
	  kill -TERM $$pid 2>/dev/null || true; sleep 0.4; \
	  if kill -0 $$pid 2>/dev/null; then kill -9 $$pid 2>/dev/null || true; fi; \
	  printf "$(Y)killed pid $$pid on :$(PORT)$(Z)\n"; \
	else \
	  printf "$(D)nothing on :$(PORT)$(Z)\n"; \
	fi

clean: stop
	@rm -rf .next/cache .turbo .vite .astro/cache 2>/dev/null || true
	@printf "$(G)wiped framework caches$(Z)\n"
```

`make clean` is the recovery-from-Turbopack-panic command. Print it in the help banner. The framework-cache list is conservative — only nuke directories the framework owns. Do NOT remove `node_modules` here; that's an explicit user opt-in (`make nuke` is intentionally NOT generated).

## `deploy-vercel` — canonical recipe

```makefile
.PHONY: deploy-vercel _check-vercel-tokens

deploy-vercel: _check-vercel-tokens
	@vercel link --yes --project=$(VERCEL_PROJECT) --token=$$VERCEL_TOKEN >/dev/null
	@URL=$$(vercel deploy --prod --yes --token=$$VERCEL_TOKEN --logs); \
	  printf "$(B)$(G)Deployed:$(Z) %s\n" "$$URL"; \
	  vercel inspect "$$URL" --wait --token=$$VERCEL_TOKEN; \
	  vercel curl /api/health --deployment "$$URL" --token=$$VERCEL_TOKEN || true

_check-vercel-tokens:
	@command -v vercel >/dev/null 2>&1 || { \
	  printf "$(R)vercel CLI not found$(Z)  $(D)npm i -g vercel$(Z)\n"; exit 1; }
	@if [ -z "$$VERCEL_TOKEN" ]; then \
	  printf "$(R)VERCEL_TOKEN not set$(Z)\n"; \
	  printf "  $(D)create:  https://vercel.com/account/tokens$(Z)\n"; \
	  printf "  $(D)export:  export VERCEL_TOKEN=...$(Z)\n"; \
	  exit 1; \
	fi
```

Why each flag:
- `vercel link --yes --project=NAME` is the find-or-create form: project exists → links and writes `.vercel/project.json`; doesn't exist → creates with that name. `--yes` auto-confirms in non-TTY.
- `--token=$$VERCEL_TOKEN` is mandatory in CI (no browser-prompt fallback). The double-dollar escapes Make's variable expansion so the shell sees `$VERCEL_TOKEN`.
- `vercel deploy --prod --yes` always production. For preview deploys use a different target (not generated by default).
- `--logs` streams build logs; capture the final URL via shell variable assignment.
- `vercel inspect "$$URL" --wait` blocks until the deployment is `READY` or `ERROR` — never declares done on a half-deployed build.
- `vercel curl /api/health --deployment "$$URL"` is a soft smoke test; `|| true` keeps the recipe green even if `/api/health` doesn't exist (most Next.js projects don't ship one out of the box).

The `.vercel/project.json` written by `vercel link` is **not secret**. Either commit it for deterministic CI, or rely on `vercel link --yes --project <name>` re-creating it every run. Pick one and stick with it.

## `env-pull` — and the `vercel pull` trap

```makefile
.PHONY: env-pull
env-pull: _check-vercel-tokens
	@vercel env pull .env.local --environment=development --token=$$VERCEL_TOKEN
	@printf "$(G)✓ .env.local updated (development scope)$(Z)\n"
```

**Trap: `vercel env pull` ≠ `vercel pull`.** They write different files (verified May 2026 against `https://vercel.com/docs/cli/env`, last_updated 2026-03-11):

| Command | Writes to | Used for |
|---|---|---|
| `vercel env pull .env.local` | `.env.local` (or path you pass) | The framework's dev server reads this — Next.js, Vite, etc. |
| `vercel pull` | `.vercel/.env.<target>.local` | `vercel build` and `vercel dev` only — the local CLI build pipeline |

Generate `vercel env pull .env.local`. The dev server reads `.env.local`, not anything under `.vercel/`. Confusing the two leads to "but my env vars aren't loading" debug spirals.

Sensitivity defaults (post-2025): `vercel env add` against `production` / `preview` defaults to **sensitive (write-only)** — values aren't visible after creation. Override with `--no-sensitive` if your team policy permits. The skill never blanket-imports `.env.local` to production envs (that would leak dev secrets); production secrets are managed via GitHub Actions `${{ secrets.* }}` per `ci-cd-workflow.md`.

## `verify`

```makefile
.PHONY: verify
verify:
	@if [ -z "$$PROD_URL" ] && [ -z "$(PROD_URL)" ]; then \
	  printf "$(R)PROD_URL not set$(Z)  $(D)export PROD_URL=https://your-app.vercel.app$(Z)\n"; \
	  exit 1; \
	fi
	@url=$${PROD_URL:-$(PROD_URL)}; \
	code=$$(curl -s -L -o /dev/null -w "%{http_code}" --max-time 12 "$$url/" || echo "ERR"); \
	case $$code in \
	  2*|3*) printf "  $(G)$$code$(Z) $$url\n" ;; \
	  *)     printf "  $(R)$$code$(Z) $$url\n"; exit 1 ;; \
	esac
```

`PROD_URL` is the live URL — either a custom domain (`https://app.example.com`) or the Vercel-issued fallback (`https://<project>.vercel.app`). Set as a Make variable at scaffold time, or pass per-invocation: `make verify PROD_URL=https://...`.

## `build-check` — function size guard

Vercel function size limits, verified May 2026 against `https://vercel.com/docs/limits` (last_updated 2026-03-02):

| Runtime | Unzipped | Compressed (~) |
|---|---|---|
| Node / Edge / Bun | 250 MB | ~50 MB |
| Python | 500 MB | ~100 MB (raised 2026-02-24 — see `https://vercel.com/changelog/python-vercel-functions-bundle-size-limit-increased-to-500mb`) |

The recipe runs an analyzer build, lists the ten largest functions, and fails if any exceeds 250 MB unzipped:

```makefile
.PHONY: build-check
build-check: _check-vercel-tokens
	@printf "$(D)→ analyzer build (may take 60-120s)$(Z)\n"
	@VERCEL_ANALYZE_BUILD_OUTPUT=1 vercel build --prod --token=$$VERCEL_TOKEN
	@printf "$(D)→ top 10 functions by unzipped size$(Z)\n"
	@du -sh .vercel/output/functions/*.func 2>/dev/null | sort -h | tail -10 || true
	@max_kb=$$(du -sk .vercel/output/functions/*.func 2>/dev/null | sort -n | tail -1 | awk '{print $$1}'); \
	  if [ -n "$$max_kb" ] && [ "$$max_kb" -gt $$((250*1024)) ]; then \
	    printf "$(R)FAIL: function over 250 MB unzipped (Node/Edge/Bun limit)$(Z)\n"; \
	    printf "$(D)Mitigation order:$(Z)\n"; \
	    printf "$(D)  1. vercel.json functions[].excludeFiles to drop bundled binaries$(Z)\n"; \
	    printf "$(D)  2. switch route to Edge runtime (no Node APIs)$(Z)\n"; \
	    printf "$(D)  3. split function — one route per func$(Z)\n"; \
	    printf "$(D)  4. move heavy work to Railway (Scenario C)$(Z)\n"; \
	    exit 1; \
	  fi; \
	  printf "$(G)✓ all functions under 250 MB unzipped$(Z)\n"
```

`VERCEL_ANALYZE_BUILD_OUTPUT=1` makes `vercel build` emit per-function size info into the build trace. `du -sk` returns kilobytes (POSIX-portable; `du -sb` is GNU-only). The 250 MB bound matches Node/Edge/Bun runtimes; raise to `500*1024` for Python-only projects (verify the runtime in `.vercel/output/config.json`).

Common offenders:
- Sharp / canvas / native binaries (~30-50 MB each)
- Puppeteer-full (~170 MB) / playwright (~250 MB) — almost always too big; move to Railway
- ffmpeg-static (~50 MB)
- @sentry/profiling-node (~5 MB) — usually fine but additive

Run `build-check` before `deploy-vercel` in CI; locally it's optional.

## Monorepo deploy delegation

In monorepos, the root Makefile delegates to per-app Makefiles:

```makefile
.PHONY: deploy-web deploy-admin deploy
deploy: deploy-web deploy-admin
deploy-web:
	@$(MAKE) -C apps/web deploy-vercel
deploy-admin:
	@$(MAKE) -C apps/admin deploy-vercel
```

Each app has its own Vercel project. The dashboard's "Root Directory" setting is **dashboard-only** (verified May 2026 against `https://vercel.com/docs/monorepos`) — there is no `vercel.json` field, no CLI flag for it. The skill instructs the user once via a printed banner during scaffold:

```
Set Root Directory in Vercel dashboard for each app project:
  https://vercel.com/<team>/<project>/settings → Build → Root Directory

The Make target won't fight you — `vercel link --yes --project <name>` finds
the project and Vercel respects the dashboard setting.
```

This banner prints once, during scaffold, NOT in the Makefile. Don't bake user-facing setup chatter into runtime targets. See `makefile-monorepo.md` for the full root + per-app pattern.

## Next.js `allowedDevOrigins` for tunnel hostnames

Next 16+ does **exact-match** (not suffix-match) on `allowedDevOrigins`. Every tunnel hostname form must be listed verbatim in `next.config.ts`:

```ts
export default {
  allowedDevOrigins: [
    "$(PROJECT_NAME)",                       // short MagicDNS
    "$(PROJECT_NAME).<tailnet>.ts.net",      // tailnet FQDN
    "$(PROJECT_NAME).localhost",             // portless FQDN (if used)
  ],
};
```

The scaffolder reads the user's `tailscale status --json | jq -r '.MagicDNSSuffix'` to fill in `<tailnet>` and reads `tailscale status --json | jq -r '.Self.HostName'` for the short MagicDNS form. **Append, never replace** the user's existing entries. Without this, the dev overlay flashes "Blocked cross-origin request to /_next/webpack-hmr" and HMR breaks silently.

If the user is on a non-`.ts.net` custom domain (Tailscale BYO domain), add that too. If the project doesn't use a tunnel, omit this section entirely.

## DO-NOT list (frontend / Vercel)

- **DO NOT set `output: 'standalone'` in `next.config.js` for Vercel.** Standalone mode breaks Image Optimization, ISR, and Middleware integration on Vercel. Standalone is for self-host targets only — Railway, Fly.io, Docker. Use vanilla `next.config.js` (no `output` field) for Vercel.
- **DO NOT generate `vercel.json` unless overriding a specific build setting.** Vercel auto-detects Next.js, Vite, Astro, Nuxt, Remix, SvelteKit. Generating `vercel.json` to "be explicit" creates drift between dashboard auto-detect and the file, and dashboard wins silently.
- **DO NOT blanket-import `.env.local` into Vercel production envs.** That leaks dev secrets. Production envs are set via `vercel env add KEY production` (one at a time) or via GitHub Actions `${{ secrets.* }}` for CI-driven deploys.
- **DO NOT forget `--yes` and `--token`.** CI hangs without `--yes` waiting on a Y/n prompt. Auth fails without `--token` in non-TTY. Both are mandatory.
- **DO NOT use `vercel pull` to write `.env.local`.** That writes to `.vercel/.env.<target>.local`, not `.env.local`. The dev server reads `.env.local`. See the `env-pull` section above.
- **DO NOT set Root Directory in `vercel.json`.** It's not a `vercel.json` field. It's dashboard-only for monorepos. Print the dashboard URL once during scaffold; never re-print at runtime.
- **DO NOT generate the `make deploy-vercel` target if there is no frontend.** Skip Scenarios B / E / F / G. Vercel is a frontend-host; backends and CLIs go elsewhere.
- **DO NOT enable `VERCEL_TELEMETRY` for CI runs.** The preamble exports `VERCEL_TELEMETRY_DISABLED=1` so first-time CLI runs don't pause for the telemetry-opt-in prompt.

## Common failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `Error! No existing credentials found` | `VERCEL_TOKEN` not exported, `vercel login` not run | `_check-vercel-tokens` catches this; export `VERCEL_TOKEN` (https://vercel.com/account/tokens) |
| `Error! Project not found` | `.vercel/project.json` missing or wrong project name | `vercel link --yes --project <name> --token=$VERCEL_TOKEN` re-creates |
| `Error! Function exceeds 250 MB unzipped` | Heavy native deps in serverless route | Run `make build-check`; mitigations in priority order in the recipe |
| Deploy hangs at `Vercel CLI` prompt | Missing `--yes` in non-TTY | Always use `--yes` |
| `.env.local` empty after `make env-pull` | Wrong env scope or no dev env vars | Check Vercel dashboard → Settings → Environment Variables → Development scope is populated |
| `vercel pull` was used instead of `vercel env pull` | Wrong command — see trap above | Use `vercel env pull .env.local` |
| Dev server starts but env vars missing | Framework reads `.env.local` not `.vercel/.env.development.local` | Same as above; use `vercel env pull` |
| Build fails with `output: 'standalone'` errors on Vercel | Standalone mode incompatible with Vercel's Image Optimization | Remove `output: 'standalone'` from `next.config.js` |
| `make deploy-vercel` succeeds but `verify` returns 404 | Custom domain not yet aliased | `vercel alias <deployment-url> <custom-domain>` (one-time) or set `PROD_URL=<vercel-url>` |
| Telemetry prompt blocks first CI run | Vercel CLI prompts for telemetry consent | `export VERCEL_TELEMETRY_DISABLED=1` (already in the preamble) |
| Production env scope picked up dev secrets | `.env.local` was uploaded via dashboard "import" button | Re-set production secrets via `vercel env add KEY production` or via GitHub Actions secrets; dev secrets stay in `.env.local` only |
| `vercel inspect --wait` returns `ERROR` | Build failed at runtime checks | `vercel logs <deployment-url>` for the actual error; iterate locally with `vercel build --prod` |

## Cross-references

- `makefile-base.md` — universal preamble (SHELL, ANSI, `.ONESHELL`, `.DELETE_ON_ERROR`, `.DEFAULT_GOAL`)
- `port-hygiene.md` — `_free-port-%` helper and the LAN IP enumerator used by `_print-banner-local-lan`
- `tailscale-funnel-rules.md` — full bodies for `tunnel`, `tunnel-stop`, `funnel`
- `makefile-monorepo.md` — root Makefile delegation pattern for multi-app repos
- `env-vars-conventions.md` — where envs live per scenario; sensitivity defaults
- `verification-ladder.md` — what `make verify` claims (rung 5 max)
- `ci-cd-workflow.md` — GitHub Actions scaffolding that reuses `deploy-vercel` semantics
