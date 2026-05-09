---
name: init-makefiles
description: Use skill if you are generating scenario-specific Makefile control planes, safely replacing old scaffolds, syncing Make targets, or optionally wiring deploy CI.
---

# init-makefiles

Make is the project's control plane. One generated Makefile (or up to four in monorepos), zero required arguments, scenario-appropriate targets only.

Run this skill when an agent must scaffold or refresh `make` targets in a project. The skill inspects the repo, classifies it into one of seven scenarios, snapshots and replaces approved prior scaffolding, generates the right Makefile(s), syncs the `AGENTS.md` `## Make targets` contract, and optionally wires GitHub Actions for push-to-main deploys.

## Compatibility note

`init-makefiles` is the consolidated successor to the older make-local, make-railway, and make-vercel direction. Do not recreate provider-specific Makefile skills; classify the project scenario here, then generate only scenario-appropriate targets.

## How to think about this

Three principles, applied without exception:

1. **Scenarios beat providers.** Don't ask "is this a Vercel project?" — ask "what is this project?" The provider stack (Vercel, Railway, Supabase, etc.) falls out of the scenario, never the other way around.
2. **Local = real dev builds, never toy builds.** Next.js / Turborepo / monorepo projects use the actual dev pipeline. No shortcuts that diverge from production behaviour.
3. **Exposure is opt-in.** `make local` binds `127.0.0.1`. `make local-lan` binds `0.0.0.0`. `make tunnel` runs Tailscale Serve (tailnet-only). `make funnel` is PUBLIC and gated behind explicit `PUBLIC_FUNNEL=1`. Funnel never enables as a side effect of any other command.

## Use this skill when

- The user asks to "set up make for this project", "wire deploy via make", "fix make local", "ship this Mac app to my macbook"
- An existing Makefile has bit-rotted (stale targets, no port hygiene, hardcoded provider commands)
- A monorepo has three Makefiles with three different banners and the user wants consistency
- A new project needs a control plane and the user wants `make` to be it
- The project's `AGENTS.md` / `CLAUDE.md` doesn't list its make targets and an agent needs to know what's available

## Do not use this skill when

- The user wants a one-off shell script — use bash, not make
- The project is purely a CI pipeline with no local control plane — use `.github/workflows/` directly
- Railway logs, scale, restart, env edits, or one-off CLI operations are the job — use `use-railway`
- AGENTS hierarchy, REVIEW.md, folder-scoped agent config, or broad repo governance is the job — use `init-agent-config`
- Hosted MCP architecture beyond a local MCP control target is the job — use `build-mcp-use-server`

## Workflow

### 1. Inspect (read-only)

Capture the project's state before writing anything:

```bash
# Package manager
ls bun.lockb pnpm-lock.yaml yarn.lock package-lock.json 2>/dev/null

# Framework signals (frontend)
ls next.config.* vite.config.* astro.config.* nuxt.config.* svelte.config.* remix.config.* 2>/dev/null

# Supabase
ls supabase/config.toml 2>/dev/null
jq -r '.dependencies | keys[]?' package.json 2>/dev/null | grep -i supabase

# Monorepo
ls turbo.json pnpm-workspace.yaml apps/ packages/ 2>/dev/null
jq -r '.workspaces' package.json 2>/dev/null

# Backend signals
find apps server services -maxdepth 2 -name "package.json" 2>/dev/null | head

# MCP server
jq -r '.dependencies | keys[]?' package.json 2>/dev/null | grep -E 'modelcontextprotocol|mcp-use'

# Mac signals
ls *.xcodeproj *.xcworkspace Package.swift Info.plist 2>/dev/null

# Existing Make scaffolding
ls Makefile *.mk scripts/dev.sh scripts/deploy.sh 2>/dev/null
find . -maxdepth 3 -name "Makefile" -not -path "./node_modules/*"

# AGENTS.md / CLAUDE.md state
ls -la AGENTS.md CLAUDE.md 2>/dev/null
```

Then run the bundled detector for a second, low-freedom signal pass. Resolve `scripts/scenario-detect.sh` relative to this skill directory and pass the downstream project root:

```bash
bash scripts/scenario-detect.sh /path/to/project
```

The detector is read-only and heuristic-only; it prints observed signals and candidate scenarios, not the final answer. Full detection cheat sheet in `references/scenario-detection.md`; detector implementation notes in `scripts/scenario-detect.md`.

If a precondition fails (no `package.json`, no dev script, no SSH alias for Mac scenario), surface it before generating. Do not generate something that breaks on first run.

### 2. Classify

Pick exactly one scenario per deployable app. The seven:

| # | Scenario | Primary signal | What's in scope |
|---|---|---|---|
| **A** | Frontend-only | `next.config.*` / `vite.config.*` / etc.; no backend dir; no Supabase | Local, LAN, tunnel; Vercel deploy |
| **B** | MCP server | `@modelcontextprotocol/sdk` or `mcp-use` in deps | Local; no deploy; `inspect` target |
| **C** | Frontend + backend | A signals + `apps/api` (or similar) with Express/Hono/Fastify | Frontend + Vercel + Railway |
| **D** | Frontend + Supabase | A signals + `@supabase/supabase-js` + `supabase/` dir | Frontend + Vercel + Supabase CLI ops |
| **E** | Multi-service Railway | Multiple service dirs / `railway.toml` files | Railway only; parallel deploy where safe |
| **F** | Build-artifact | Cargo / Go / Swift / native CLI; no HTTP framework, no remote target | Build + run locally; no deploy |
| **G** | MacBook ship | `.xcodeproj` / `Package.swift` Mac target + remote-Mac SSH alias | Build + ship via `rsync` + atomic swap + verify |

For single-app projects, the final classification has one tag. For monorepos, each deployable app gets one tag and the root gets a dominant orchestration tag. For the rare frontend + backend + Supabase shape, use the supported combined tag **C+D** only when the custom backend deploys separately and Supabase is also in scope.

Before generating files, print this block:

```text
Scenario: <A-G, or C+D for supported combined shape>
Scope: <repo root or per-app paths>
Confidence: <high|medium>
Signals: <observed files/deps/commands>
Excluded scenarios: <why the near misses were rejected>
Provider scope: <Vercel/Railway/Supabase/MacBook/local-only>
Makefiles to generate: <root + app paths, max 4>
Ambiguity resolved: <none or the answered question>
```

If detection is ambiguous → **ask one targeted question, never guess**. Sample prompts in `references/scenario-detection.md`.

### 3. Preview and read existing scaffolding

Run the bundled wipe preview before touching files. Resolve `scripts/preview-makefile-wipe.sh` relative to this skill directory and pass the downstream project root:

```bash
bash scripts/preview-makefile-wipe.sh /path/to/project
bash scripts/preview-makefile-wipe.sh /path/to/project --paths-only > /tmp/init-makefiles-candidates.txt
```

The script is read-only. It prints exact paths, match reasons, tracked state, and uncommitted status; implementation notes live in `scripts/preview-makefile-wipe.md`.

For every candidate `Makefile`, `*.mk`, `make-*.sh`, `scripts/dev.sh`, and `scripts/deploy.sh`: read the file before classifying it as scaffold. Note useful patterns the user encoded (custom env handling, project-specific port choices, framework-specific dev commands) because those inform regenerated targets.

Write a deletion manifest containing only paths approved for replacement:

```bash
DELETION_MANIFEST=/tmp/init-makefiles-delete-manifest.txt
# write one approved path per line, exactly as printed by the preview
```

Refuse to continue if a candidate has uncommitted non-scaffold edits the agent cannot classify. If unrelated dirty files exist, leave them untouched and state that they were not snapshotted.

### 4. Snapshot and wipe from manifest

Create a targeted snapshot commit before deletion. Stage only manifest paths:

```bash
git status --porcelain
while IFS= read -r path; do
  [ -n "$path" ] || continue
  git add -- "$path"
done < "$DELETION_MANIFEST"
git commit -m "chore(make): snapshot existing scaffold before init-makefiles regen"
```

Never use `git add -A` for the snapshot. Never auto-commit unrelated work.

Print recovery before deleting:

```bash
SNAPSHOT_SHA=$(git rev-parse --short HEAD)
printf 'Recovery: git revert %s\n' "$SNAPSHOT_SHA"
printf 'Single file: git restore --source=%s -- path/to/Makefile\n' "$SNAPSHOT_SHA"
```

Delete only manifest paths:

```bash
while IFS= read -r path; do
  [ -n "$path" ] || continue
  rm -f -- "$path"
done < "$DELETION_MANIFEST"
```

### 5. Generate core Makefiles

Compose the new Makefile(s) from the scenario's references. Universal preamble in `references/makefile-base.md`. Scenario sections live in `references/makefile-frontend.md`, `references/makefile-backend.md`, `references/makefile-supabase.md`, and `references/makefile-macbook.md`. Monorepo delegation in `references/makefile-monorepo.md`.

**Hard rules baked into every generated Makefile:**

- **Max 4 Makefiles per project** — root + up to 3 app sub-Makefiles. If a monorepo has more apps, ask the user to pick three.
- **Every target works with zero arguments.** Env vars overridable (`make local PORT=4000`) but defaults must work. Sole exception: `make supabase-migrate-new name=<n>`.
- **Universal preamble** — `SHELL := bash`, `.SHELLFLAGS := -eu -o pipefail -c`, `.ONESHELL:`, `.DELETE_ON_ERROR:`, `MAKEFLAGS += --warn-undefined-variables --no-builtin-rules`, `.DEFAULT_GOAL := help`.
- **Port hygiene mandatory** — use `_free-port-%` from `references/port-hygiene.md`. Only kill our own dev processes (`node|next-server|turbo|turbopack|next|bun|deno`); refuse foreign holders, suggest `+10` port.
- **Localhost binding by default.** LAN binding via `make local-lan`. Tailscale Serve via `make tunnel` (tailnet-only). Tailscale Funnel via `make funnel` (PUBLIC, opt-in only).
- **Helper targets prefix with `_`** (`_check-vercel-tokens`, `_free-port-%`, `_print-banner-*`). They don't appear in `make help`.

### 6. Update AGENTS.md / CLAUDE.md

Apply the 5-state machine in `references/agents-md-update.md`. The contract:

- AGENTS.md is the source of truth
- CLAUDE.md is a symlink → AGENTS.md (or absent)
- Only the downstream project `## Make targets` section is written/updated, listing every generated target, env-var knob, and what the skill will and will not do
- Same-directory `CLAUDE.md → AGENTS.md` compatibility links are in scope
- Hand-written `## Make targets` sections require explicit replacement consent
- The rewrite is skipped if the existing section is already accurate (no churn)
- Broad AGENTS-first governance, nested folder instructions, and REVIEW.md remain the job of `init-agent-config`

### 7. Verify core generation

Run the verification ladder in `references/verification-ladder.md`. The skill claims at most rung 5 (external curl from this machine, no proxy). Rung 6 (independent client — phone on cellular) is a manual user step printed in the post-deploy banner.

Per scenario:
- A / C / D: `make local` opens browser; `make deploy` returns Ready URL; `make verify` HTTP-probes
- B: `make local` starts MCP on `127.0.0.1:<port>`; `make inspect` returns tool schema
- E: `make deploy-all` deploys services in parallel; `make verify` HTTP-probes each
- F: `make build` produces a binary; `./build/<name> --version` runs without error
- G: `make ship` rsyncs and `pgrep -x "$(APP_NAME)"` returns a PID after `sleep 2`

Core generation is complete when Makefiles, AGENTS.md sync, and verification are done. The skill remains useful and complete if CI/CD is declined.

### 8. Optional: CI/CD

Ask first: "Generate GitHub Actions deploy wiring locally? (y/n)". If yes, follow `references/ci-cd-workflow.md`:

1. Detect GitHub repo via `gh repo view --json nameWithOwner -q .nameWithOwner`
2. Generate `.github/workflows/deploy.yml` for the providers in scope only
3. Prompt user for ONLY the tokens needed (Vercel / Railway / Supabase)
4. `gh secret set <NAME> --body "$pasted"` for each required secret
5. Verify required secrets by name with `gh secret list`
6. Commit the workflow locally
7. Ask for explicit push authorization
8. Push only after that authorization; never force-push

If declined, leave `.github/workflows/` untouched. No half-baked YAML.

## Decision rules

- **Localhost-only by default.** `make local` binds `127.0.0.1`. LAN exposure must be explicit (`make local-lan`).
- **Funnel never auto-enables.** `make funnel` is the only target that uses Funnel, and only with `PUBLIC_FUNNEL=1`.
- **Backends don't run locally by default.** Local hosts the frontend or an MCP server. Backend stays remote in dev unless `LOCAL_BACKEND=1` is set explicitly.
- **Provider scope is conditional.** Vercel only if there's a frontend. Railway only if there's a custom backend. Supabase only if `supabase/` exists. MacBook only if a Mac project + remote-Mac target.
- **No improvised commands.** Inspect first; pick the canonical command from the relevant reference.
- **Replace before regenerating.** Preview, read, manifest, targeted snapshot, print recovery, then delete only manifest paths. Never edit Makefiles incrementally.
- **Max 4 Makefiles.** Ask if there are more apps than slots.
- **Detection ambiguous → ask one question, never guess.**

## Recovery paths

### Recovery from wipe

```bash
git log --oneline -- Makefile
git show --stat <snapshot-sha>
git revert <snapshot-sha>
# or restore a single file:
git restore --source=<snapshot-sha> -- path/to/Makefile
```

| Symptom | Cause | Fix |
|---|---|---|
| `make local` fails with "port :PORT held by orbstack" | Foreign port holder; refused per port-hygiene rule | Pick a different port (`make local PORT=4000`); don't kill OrbStack |
| `make tunnel` reports "tailscale not signed in" | Tailscale daemon up but account not linked | `tailscale up` interactively; this skill assumes Tailscale is signed in |
| `make deploy-vercel` fails with "Project not found" | `.vercel/project.json` missing or wrong project name | Re-run `vercel link --yes --project <name> --token=$VERCEL_TOKEN` |
| `make deploy-railway` returns 502 "Application Failed to Respond" | App listens on `localhost:3000` not `0.0.0.0:$PORT` | Fix app's bind address; redeploy |
| `make supabase-migrate-apply` no-ops with "no migrations to apply" | Migration files already in remote history | Run `make supabase-pull` to detect drift |
| `make ship` fails preflight with "ssh alias not found" | `Host macbook` not in `~/.ssh/config` | Add the Host block; `make ship` re-checks |
| AGENTS.md and CLAUDE.md both exist with different content | State 1 of the symlink machine | Skill prompts user; merges into AGENTS.md per `references/agents-md-update.md` |
| `gh secret set` fails with "auth required" | Not authenticated | `gh auth login`; CI/CD step re-runs |
| Vercel build fails with function over 250 MB | Heavy bundled deps | `make build-check` surfaces sizes; `references/makefile-frontend.md` lists mitigations |
| `make funnel` rejects port 3000 | Funnel allows only 443/8443/10000 | Use `make funnel TUNNEL_PORT=443` (and `PUBLIC_FUNNEL=1`) |
| `make tunnel` works but `host <node>.<tailnet>.ts.net` fails on macOS | macOS DNS quirk: `host`/`nslookup`/bare `dig` bypass system resolver | Use `tailscale dns query <fqdn>` or `dscacheutil -q host -a name <fqdn>` |

## Final report contract

Return this shape when the downstream project work is done:

```text
Scenario: <chosen scenario and confidence>
Generated files: <paths>
Deleted/replaced scaffold paths: <paths or none>
Snapshot: <sha and recovery command>
AGENTS.md / CLAUDE.md: <state>
CI/CD: <skipped | generated locally | secrets wired | pushed>
Verification: <rung actually reached per target>
Manual verification still required: <targets, especially rung 6>
```

## Reference routing

| File | Read when |
|---|---|
| `references/scenario-detection.md` | Classifying a project; resolving ambiguity; sample disambiguation prompts |
| `references/makefile-base.md` | Universal preamble, ANSI palette, helper conventions; every Makefile uses this |
| `references/makefile-frontend.md` | Generating Scenarios A / C / D frontend targets (`local`, `local-lan`, `tunnel`, `deploy-vercel`, `verify`, `env-pull`, `build-check`) |
| `references/makefile-backend.md` | Generating Scenarios C / E backend targets (Railway deploy, multi-service parallel, healthcheck rules, `railway.toml` baseline) |
| `references/makefile-supabase.md` | Generating Scenario D Supabase targets (`supabase-link`, `-migrate-*`, `-functions`, `-types`, `-secrets-*`) |
| `references/makefile-macbook.md` | Generating Scenario G ship pipeline (preflights, rsync, atomic swap, kill-then-launch, verify) |
| `references/makefile-monorepo.md` | Multi-Makefile delegation; 4-file ceiling; per-app namespacing; root-Makefile `$(MAKE) -C` pattern |
| `references/tailscale-funnel-rules.md` | Tunnel/Funnel target generation; macOS DNS quirks; Funnel port restrictions; ACL preflight |
| `references/port-hygiene.md` | The kill-only-our-own pattern; default-port squat list; SIGTERM-then-SIGKILL escalation; banner conventions |
| `references/agents-md-update.md` | The 5-state machine for AGENTS.md / CLAUDE.md; the `## Make targets` section template; idempotency rule |
| `references/ci-cd-workflow.md` | Wiring GitHub Actions; `gh secret set` sequence; concurrency rules; rotation hint |
| `references/env-vars-conventions.md` | Where envs live per scenario; `.env.local` vs `.env.railway`; Vercel sensitivity defaults; Railway built-in vars |
| `references/verification-ladder.md` | The 6 rungs; per-target verification; banner template for the user's manual rung-6 step |
| `scripts/scenario-detect.md` | Read-only heuristic detector script; use before final classification and ambiguity questions |
| `scripts/preview-makefile-wipe.md` | Read-only wipe preview script; use before manifest, targeted snapshot, and deletion |

## Cross-skill handoffs

- **`use-railway`** — for ad-hoc Railway CLI operations not covered by deploy targets (logs, scale, restart, env management beyond what the Makefile exposes)
- **`build-mcp-use-server`** — for hosted-MCP scenarios beyond local-only MCP servers (Scenario B is for local-facing MCP only)
- **`build-macos-app`** — for Mac-app development standards (this skill only does Make scaffolding; framework choice and SwiftUI patterns belong there)
- **`init-agent-config`** — for AGENTS hierarchy, REVIEW.md, folder-scoped agent config, and broad repo governance

## Guardrails

- **Never enable Funnel as a side effect.** Funnel is never in `make tunnel`. Funnel only in `make funnel` with `PUBLIC_FUNNEL=1` ack.
- **Never run `tailscale serve reset` / `tailscale funnel reset` without explicit user consent.** They wipe ALL mappings on this node — other projects' included. Use targeted disable (`tailscale serve --https=443 <port> off`) instead.
- **Never `kill -9` foreign processes on a port.** Port hygiene refuses, suggests `+10`.
- **Never generate Railway config in projects without a custom backend.** Skip Scenarios A / B / D / F / G.
- **Never generate Vercel config in projects without a frontend.** Skip Scenarios E / F / G.
- **Never generate Supabase migrations in projects without `supabase/`.** Skip Scenarios A / B / C / E / F / G.
- **Never write tokens to disk except as `gh secret set` payloads.** Never echo tokens back to the user.
- **Never edit a Makefile in place.** Manifest, snapshot, delete, and regenerate. The targeted snapshot commit is the safety net.
- **Never delete scaffold paths that were not printed in the preview and copied into the deletion manifest.**
- **Never push CI/CD workflow commits without explicit push authorization after local generation and secret verification.**
- **Never set `output: 'standalone'`** in `next.config.js` for Vercel-hosted Next.js. Standalone is for self-host (Railway/Docker) only.
- **Never use `host` / `nslookup` / bare `dig`** to verify MagicDNS names on macOS — they bypass the system resolver. Use `tailscale dns query <fqdn>` or `dscacheutil -q host -a name <fqdn>`.
- **Never use `RAILWAY_API_TOKEN` (account scope)** when a project token would do. CI uses project tokens.
- **Never blanket-import `.env.local` into Vercel production.** Dev secrets leak that way.

## Final checks

Before declaring done:

- [ ] `make help` lists every generated target with one-line descriptions
- [ ] Every target works with zero arguments (`make X` runs cleanly)
- [ ] `AGENTS.md` `## Make targets` section accurately reflects the generated Makefile
- [ ] `CLAUDE.md` is a symlink → AGENTS.md (or absent)
- [ ] No more than 4 Makefiles in the project tree
- [ ] Snapshot commit exists in `git log` before the regen commit
- [ ] Deletion manifest paths match the deleted/replaced scaffold paths
- [ ] If CI/CD opted in: `.github/workflows/deploy.yml` exists; `gh secret list` shows the wired secrets; push was separately authorized
- [ ] No Funnel mapping was created without explicit `PUBLIC_FUNNEL=1`
- [ ] The Makefile preamble matches `references/makefile-base.md`
- [ ] Port hygiene helper is present in any Makefile that opens a port
- [ ] Cross-references in `references/*.md` use correct relative paths
