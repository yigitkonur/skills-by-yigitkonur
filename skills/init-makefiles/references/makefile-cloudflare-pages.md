# Cloudflare Pages — opt-in deploy variant of Scenario A

> **Read this reference only when the user has explicitly asked for Cloudflare Pages.** The Scenario A default is Vercel — see `makefile-frontend.md`. Cloudflare Pages flips that default only when the user names "Cloudflare", "Pages", "Wrangler", or similar. Disk signals alone (a stray `wrangler.toml`, a `_redirects` file) do **not** flip the default — projects routinely have `wrangler.toml` to drive R2 or Workers while shipping the frontend to Vercel.

When CF Pages is the chosen provider, everything in `makefile-frontend.md` about `local`, `local-lan`, `tunnel`, `stop`, `clean` still applies — only the deploy targets change. CF Pages and Vercel are mutually exclusive deploy paths in this skill; generate one set, not both.

## Target inventory (replaces Vercel section)

| Target | One-line description |
|---|---|
| `deploy` | Alias for `deploy-cloudflare` |
| `deploy-cloudflare` | `wrangler pages deploy $(DIST_DIR) --branch=main --commit-dirty=true` |
| `deploy-preview` | Same with `--branch=preview` for a non-production URL |
| `cf-project-init` | Idempotent: creates the Pages project on first run |
| `cf-list` | `wrangler pages deployment list --project-name=$(CF_PROJECT)` |
| `cf-tail` | `wrangler pages deployment tail --project-name=$(CF_PROJECT)` |
| `verify` | `curl -sI $(PROD_URL)` — expect 2xx/3xx |
| `build` | Framework build → `$(DIST_DIR)/` (no Pages-specific change) |
| `build-check` | Build + verify Pages limits (≤25 MiB/file, ≤20k files) |

Helpers (`_`-prefixed, hidden from `make help`): `_check-wrangler`, `_print-banner-deployed`. No `_check-vercel-tokens` — wrangler uses its own OAuth login, not env tokens by default.

## Variables

```makefile
CF_PROJECT  ?= $(notdir $(CURDIR))                # Cloudflare Pages project name
DIST_DIR    ?= dist                                # frameworks default; adjust per build output
PROD_URL    ?= https://$(CF_PROJECT).pages.dev    # default subdomain; override for custom domain
```

## `wrangler.toml` for Pages

Generate a minimal `wrangler.toml` at the repo root. Pages reads `pages_build_output_dir` to know where the static files live; `name` sets the Pages project; `compatibility_date` pins runtime behavior.

```toml
name = "your-pages-project"
compatibility_date = "YYYY-MM-DD"
pages_build_output_dir = "./dist"
```

That's the entire config for a static SPA. With it on disk, `wrangler pages deploy` without arguments picks up the directory and project name. Without it, every command needs `--project-name=…` and a positional dist directory — uglier but still works.

`wrangler.toml` is **safe to commit**. No secrets live here.

## `deploy-cloudflare` — canonical recipe

```makefile
.PHONY: deploy-cloudflare _check-wrangler

deploy-cloudflare: _check-wrangler build-check cf-project-init
	@printf "$(D)→ deploying $(DIST_DIR)/ to Cloudflare Pages project '$(CF_PROJECT)' (branch=main)$(Z)\n"
	@wrangler pages deploy $(DIST_DIR) \
	  --project-name=$(CF_PROJECT) \
	  --branch=main \
	  --commit-dirty=true
	@$(MAKE) --no-print-directory _print-banner-deployed

_check-wrangler:
	@command -v wrangler >/dev/null 2>&1 || { \
	  printf "$(R)wrangler CLI not found$(Z)  $(D)brew install cloudflare-wrangler  OR  npm i -g wrangler$(Z)\n"; exit 1; }
	@wrangler whoami >/dev/null 2>&1 || { \
	  printf "$(R)wrangler not authenticated$(Z)  $(D)run: wrangler login$(Z)\n"; exit 1; }
```

Why each flag:

- `--project-name=$(CF_PROJECT)` — mandatory when there's no `wrangler.toml` (or when it's missing the `name` field); harmless when redundant.
- `--branch=main` — production deploys go to the production branch. `--branch=preview` (or any other branch name) gets a per-branch preview URL of the form `<branch>.<project>.pages.dev`.
- `--commit-dirty=true` — wrangler refuses to deploy a dirty working tree by default. This flag accepts it. For CI use, drop it and let CI guarantee a clean tree.

`wrangler whoami` is the auth gate. If it prints the user's account banner, OAuth login is live and the deploy will succeed. If it errors, the helper exits 1 with `wrangler login` as the fix.

## `cf-project-init` — idempotent project creation

`wrangler pages deploy` will prompt interactively on first run to create the project. In a Make recipe that's a hang. The init target creates the project ahead of time:

```makefile
.PHONY: cf-project-init
cf-project-init: _check-wrangler
	@out=$$(wrangler pages project list 2>/dev/null || true); \
	if ! echo "$$out" | grep -qw "$(CF_PROJECT)"; then \
	  printf "$(D)→ creating Pages project '$(CF_PROJECT)' (first-run)$(Z)\n"; \
	  wrangler pages project create $(CF_PROJECT) --production-branch=main >/dev/null 2>&1 || true; \
	fi
```

`grep -qw` matches the exact project name as a word (avoids false positives on shared prefixes). The `|| true` after the create allows re-runs to no-op cleanly when the project already exists (CF returns a 409-ish error which the bash silences).

## `cf-list` and `cf-tail`

```makefile
.PHONY: cf-list cf-tail
cf-list: _check-wrangler
	@wrangler pages deployment list --project-name=$(CF_PROJECT)

cf-tail: _check-wrangler
	@wrangler pages deployment tail --project-name=$(CF_PROJECT)
```

`cf-tail` streams live request logs from the **production** deployment by default. For a specific deployment use `wrangler pages deployment tail <deployment-id> --project-name=…`. The skill generates only the prod-tail form; users with a debugging need can run the deployment-id form ad hoc.

## `build-check` — Pages limits

Cloudflare Pages limits (verified May 2026):

| Limit | Value | Source |
|---|---|---|
| Max file size | 25 MiB unzipped | `developers.cloudflare.com/pages/platform/limits` |
| Max files per deployment | 20,000 | same |
| Max headers per request | varies | not enforced at build time |

Function size (Pages Functions / `_worker.js`) has its own 10 MB compressed limit — orthogonal to static asset limits.

```makefile
.PHONY: build-check
build-check: build
	@total=$$(find $(DIST_DIR) -type f 2>/dev/null | wc -l | tr -d ' '); \
	  size=$$(du -sh $(DIST_DIR) 2>/dev/null | awk '{print $$1}'); \
	  printf "$(D)→ $(DIST_DIR)/: %s files, %s total$(Z)\n" "$$total" "$$size"
	@over=$$(find $(DIST_DIR) -type f -size +25M 2>/dev/null || true); \
	  if [ -n "$$over" ]; then \
	    printf "$(R)FAIL: files exceed Cloudflare Pages 25 MiB per-file limit:$(Z)\n%s\n" "$$over"; \
	    exit 1; \
	  fi
	@total=$$(find $(DIST_DIR) -type f 2>/dev/null | wc -l | tr -d ' '); \
	  if [ "$$total" -gt 20000 ]; then \
	    printf "$(R)FAIL: %s files exceeds Cloudflare Pages 20,000 file limit$(Z)\n" "$$total"; \
	    exit 1; \
	  fi
	@printf "$(G)✓ $(DIST_DIR)/ fits Pages limits$(Z)\n"
```

The 25 MiB check is the common trip — large bundled WAV/video assets, .map files, full transformers.js packages. Mitigation order:
1. Move heavy assets out of `dist/` to R2 (see `makefile-r2-bulk.md`) and load via `/media/*` redirect
2. Code-split the framework bundle
3. Drop source maps from production builds

The 20,000 file check rarely hits unless you're bundling a per-file asset library (e.g., a typeface foundry catalog or a games framework's tilemap dir).

## `_redirects` — SPA routing and asset proxying

Cloudflare Pages reads `<dist>/_redirects` at deploy time. Each non-comment line: `<from> <to> [status]`. Same-domain redirects accept 200 (rewrite), 301, 302, 307, 308. Cross-domain redirects accept 301/302/303/307/308 only — 200 rewrites do not cross origins.

Two common rules:

```text
# Proxy archive media to an R2 bucket bound at a custom domain.
# Cross-domain: 302 with :splat preserved. Range requests survive.
/media/* https://files.example.com/:splat 302

# SPA history-API fallback: any non-asset path serves index.html.
# Same-domain: 200 rewrite (no client-visible redirect).
/* /index.html 200
```

Generate `_redirects` only when the project has a documented need. Don't blanket-add the SPA fallback — many frameworks (Astro static export, SvelteKit static adapter, Next static export) handle history-API routing themselves. Adding `/* /index.html 200` on top of a framework-built `_redirects` file causes the framework's deep-route handling to short-circuit.

If both `public/_redirects` and `dist/_redirects` (framework-generated) exist, the deploy uses the file in the **deployed dir**. The skill generates into `public/_redirects` (or whatever `pages_build_output_dir` parent is) — never into the build output.

## `verify`

```makefile
.PHONY: verify
verify:
	@code=$$(curl -s -L -o /dev/null -w "%{http_code}" --max-time 12 "$(PROD_URL)/" || echo ERR); \
	  case $$code in \
	    2*|3*) printf "  $(G)$$code$(Z) $(PROD_URL)\n" ;; \
	    *)     printf "  $(R)$$code$(Z) $(PROD_URL)\n"; exit 1 ;; \
	  esac
```

Same shape as the Vercel variant. The default `PROD_URL` is `https://$(CF_PROJECT).pages.dev`. Override with a custom domain at scaffold time: `PROD_URL=https://app.example.com`.

For Pages projects with multiple custom domains, `verify` only probes one. That's fine — if the project is healthy on its primary domain, ancillary domains are typically a Cloudflare DNS-level concern, not a Pages-level one.

## Post-deploy banner

```makefile
_print-banner-deployed:
	@printf "\n$(B)$(G)✓ deployed$(Z)  $(C)$(PROD_URL)$(Z)\n"
	@printf "  $(D)logs:    make cf-tail$(Z)\n"
	@printf "  $(D)list:    make cf-list$(Z)\n"
	@printf "  $(D)verify:  make verify     (rung 5 — this machine)$(Z)\n"
	@printf "  $(D)rung 6:  curl -sI $(PROD_URL)   (run from phone on cellular for true independent check)$(Z)\n\n"
```

Mirrors the verification ladder; rung 5 is what `make verify` claims, rung 6 is the user's manual cellular-side check.

## `env-pull` is NOT generated by default

Wrangler has `wrangler pages secret list` but no clean pull-to-`.env.local` equivalent. The Vercel `make env-pull` target has no exact Pages analog. If the user needs production env vars locally:

```bash
wrangler pages secret list --project-name=<name>     # list keys
# values must be re-fetched manually from the dashboard
```

Generate `env-pull` only if the user explicitly asks for it; otherwise skip. Most CF Pages workflows put `.env.local` under user control (gitignored) and use `wrangler pages secret put` to push to production.

## Authentication: OAuth vs API tokens

Wrangler authenticates two ways:

| Method | How | When to use |
|---|---|---|
| OAuth | `wrangler login` opens a browser, writes to `~/.config/.wrangler/config/default.toml` | Local dev, single-developer machines |
| API token | `CLOUDFLARE_API_TOKEN=cfat_…` (and `CLOUDFLARE_ACCOUNT_ID=…`) in env | CI, multi-user machines, headless servers |

The skill assumes OAuth for local — `_check-wrangler` runs `wrangler whoami` which exits 0 in either case. CI flows pass the API token via `${{ secrets.CLOUDFLARE_API_TOKEN }}` in GitHub Actions (`ci-cd-workflow.md`).

API token verify endpoint (sanity check from a script):

```bash
curl -s "https://api.cloudflare.com/client/v4/accounts/<account_id>/tokens/verify" \
     -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  | jq '.success, (.result | {id, status, expires_on, not_before})'
```

`success: true` with `status: "active"` confirms the token is alive. **Token validity is independent of token permissions** — a verified token can still 401 on every operation if its permission groups are empty. If `wrangler r2 bucket info <bucket>` returns `Authentication error [code: 10000]` the token is alive but missing the `Workers R2 Storage` group.

## Detection signals (evidence only — never auto-deciders)

`scenario-detection.md` prints these signals for the user's awareness; user intent decides the variant.

| Signal | What it tells you |
|---|---|
| `wrangler.toml` / `wrangler.jsonc` at repo root | Cloudflare tooling is in play. **Does NOT mean Pages** — may be R2-only or Workers-only. |
| `pages_build_output_dir` field in wrangler config | Strong evidence of an existing or planned Pages setup. Still confirm with the user before switching from Vercel default. |
| `public/_redirects` exists | Pages-specific routing file. Same rule: inform, don't auto-switch. |
| `.vercel/` directory present | Confirms the Vercel default. |
| `vercel.json` at repo root | Confirms the Vercel default. |
| User says "Cloudflare", "Pages", "Wrangler" in the request | **This** is the only trigger that flips the default to Cloudflare Pages. |

When both Vercel and Cloudflare signals are present, ask: the answer is the user's intent, not the disk state.

## Monorepo / multi-project case

Each Pages project in a monorepo gets its own `wrangler.toml` (per app). Multiple `make deploy-cloudflare` targets — one per app — share the same `_check-wrangler` helper.

```makefile
.PHONY: deploy deploy-web deploy-admin
deploy: deploy-web deploy-admin
deploy-web:
	@$(MAKE) -C apps/web deploy-cloudflare
deploy-admin:
	@$(MAKE) -C apps/admin deploy-cloudflare
```

The 4-Makefile ceiling still applies — root + up to three app Makefiles. See `makefile-monorepo.md`.

## Common failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `wrangler pages deploy` hangs on first run | Project doesn't exist yet; CLI prompts interactively | Run `cf-project-init` first (the Makefile target chains it as a prerequisite) |
| Deploy succeeds, `https://<project>.pages.dev` returns 404 on every path | First deploy hasn't fully propagated, or the production branch doesn't match `wrangler.toml` | Wait ~60 seconds; check `cf-list` for deployment status; ensure `--branch=main` matches the project's production branch |
| `Wrangler not authenticated` | OAuth expired or never ran | `wrangler login` (or set `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID`) |
| 25 MiB file rejected | Large asset bundled into dist | `make build-check`; move asset to R2; use `_redirects` to proxy |
| 20,000 file limit hit | Massive asset catalog in dist | Same — move to R2 or split into a separate Workers project |
| `_redirects` rule doesn't fire | Wrong file location (was in repo root, should be in `pages_build_output_dir`) | Move to `public/_redirects` (Vite/SvelteKit) or framework equivalent |
| Range request through `/media/*` returns 200, not 206 | Cross-origin 302 broke the Range header pass-through | Confirm browser follows the redirect; test directly against the R2 custom domain — if R2 returns 206, the browser-side flow works (most do correctly) |
| `output: 'standalone'` build fails on Pages | Standalone is for self-host targets (Railway, Docker), not Pages | Remove `output: 'standalone'` from `next.config.js` for Pages (same rule as Vercel) |
| `wrangler pages deploy` says "Could not find a project" | Project name in `--project-name` doesn't match a real CF project | Run `wrangler pages project list` to see real names; `cf-project-init` typically prevents this |

## DO-NOT list

- **DO NOT generate Vercel and Cloudflare deploy targets in the same Makefile.** Pick one; mixing both creates ambiguity about which `make deploy` does.
- **DO NOT generate `make funnel` / `make tunnel` differently for CF.** Tunnel/Funnel are dev-only patterns that don't care about production host. The `tailscale-funnel-rules.md` recipes work identically with Pages-deployed sites.
- **DO NOT commit `~/.wrangler/` state.** It contains OAuth session tokens. Add to `.gitignore` for the user (most projects already exclude all hidden state dirs).
- **DO NOT use `--keep-vars` on `wrangler pages deploy`.** That flag is for Workers, not Pages.
- **DO NOT add Pages-specific `vercel.json` or vice versa.** They are unrelated; one will be silently ignored, but it confuses future contributors.
- **DO NOT skip `cf-project-init` in CI.** The first CI run on a fresh CF account would otherwise hang waiting for the interactive create prompt.
- **DO NOT generate the `output: 'standalone'` flag for Next.js when targeting Pages.** Pages handles Next via its own adapter; standalone breaks Image Optimization just like on Vercel.
- **DO NOT confuse `wrangler.toml` and `wrangler.jsonc`.** Both are valid; pick one per project. Generate `wrangler.toml` by default — the TOML form is the older / more documented variant.

## Cross-references

- `makefile-base.md` — universal preamble, ANSI palette, help target, `.PHONY` rules
- `makefile-frontend.md` — `local`, `local-lan`, `tunnel`, `stop`, `clean` (provider-agnostic targets that still apply)
- `makefile-r2-bulk.md` — bulk media uploads to R2 (custom-domain reads, `_redirects` proxy, rclone tuning)
- `scenario-detection.md` — Cloudflare vs Vercel disambiguation for Scenario A
- `verification-ladder.md` — what `make verify` claims (rung 5 max); rung 6 is the manual cellular probe
- `ci-cd-workflow.md` — GitHub Actions wiring for CF deploys (`CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` secrets)
