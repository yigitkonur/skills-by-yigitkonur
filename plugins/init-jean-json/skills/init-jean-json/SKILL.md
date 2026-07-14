---
name: init-jean-json
description: "Use if onboarding a repo to Jean — jean.json and .worktreeinclude setup, run, teardown, ports."
---

# init-jean-json

Onboard a repository to **Jean** (coollabsio/jean — worktree-per-agent dev environment) by authoring its automation manifest **from evidence, then proving it in a real throwaway worktree before committing anything**. The deliverable is not a file — it is a *verified* worktree bootstrap: a fresh worktree that installs, runs, and tears down cleanly with zero manual steps.

Every schema claim here is verified against Jean source (`src-tauri/src/projects/{types,git,commands}.rs`) — exact contracts in `references/jean-json-spec.md`.

## Use this skill when

- a repo is being **onboarded to Jean** and needs `jean.json` created or fixed
- worktree creation is **slow or broken** (missing `.env`, reinstalling `node_modules` every time, orphaned containers) and you must optimize it
- authoring or repairing a **`.worktreeinclude`** manifest (which gitignored files travel into new worktrees)
- documenting the worktree bootstrap in **AGENTS.md** so non-Jean agents can replicate it

## Do NOT use this skill when

- the task is *"work on X in an isolated worktree"* — that is session isolation, not manifest authoring; use your native worktree tool
- operating the Jean desktop app (creating sessions, chatting) — this skill only authors repo-side config
- the repo will never use worktrees (single-checkout deploy repo) — say so and stop

## Hard rules

1. **Never claim done without the test-worktree proof.** A `jean.json` that was written but never executed in a fresh worktree is a draft, not a deliverable.
2. **Never leave test worktrees or test branches behind.** Finalize includes cleanup; verify with `git worktree list` + `git branch --list 'jean-test-*'` both empty of your artifacts.
3. **`jean.json` and `.worktreeinclude` must be committed (tracked).** Jean reads `jean.json` from the project root when creating worktrees — a gitignored manifest silently does nothing for teammates.
4. **Setup scripts must be idempotent and non-interactive.** They run in a background login shell with no TTY; a prompt = a silent hang.
5. **Guard every `rm`/destructive command with the env vars Jean validates** (`$JEAN_WORKSPACE_PATH`, `$JEAN_ROOT_PATH` are guaranteed non-empty absolute paths — plain relative `rm -rf` is not similarly guarded).

## Workflow

### Phase 1 — Explore (evidence before authoring)

Build a bootstrap inventory. Do not guess — read the repo:

```bash
git rev-parse --show-toplevel && git status --porcelain --ignored -- . | head -50
cat .gitignore 2>/dev/null
ls -d .env* .envrc .claude .agents .cursor .vscode config/secrets* 2>/dev/null
cat package.json 2>/dev/null | jq '{pm: .packageManager, scripts}'
ls pnpm-lock.yaml yarn.lock bun.lockb package-lock.json Cargo.toml pyproject.toml go.mod compose*.y*ml docker-compose*.y*ml Makefile 2>/dev/null
cat jean.json .worktreeinclude AGENTS.md CLAUDE.md 2>/dev/null
```

Answer these six questions (they map 1:1 onto the manifest):

| # | Question | Feeds |
|---|---|---|
| 1 | Which **gitignored-but-required** files exist? (`.env*`, `.claude/settings.local.json`, `.agents/`, secrets, local certs) | `.worktreeinclude` + setup copy lines |
| 2 | What is the **install command** and can it be made instant? (pnpm store, `cp -c` clone of `node_modules`, cargo target dir) | setup |
| 3 | What is the **dev run command**? Multiple processes? | `run` (string or array) |
| 4 | Which **ports** does the dev stack listen on? Do parallel worktrees collide? | `ports[]` + port strategy |
| 5 | What does a worktree **leave running** when abandoned? (containers, daemons, tunnels) | teardown |
| 6 | Does an existing `jean.json`/`.worktreeinclude`/AGENTS.md already cover part of this? | revise, don't duplicate |

If the repo has databases/containers per worktree, or parallel-port collisions, read `references/worktree-optimization.md` (port strategy, shared caches, COW copies) **before** drafting.

### Phase 2 — Draft both manifests

Author from `references/jean-json-spec.md` (exact schema, env vars, shell semantics) and `references/templates.md` (per-stack starting points: node/pnpm, bun, python, rust, go, docker-compose, monorepo).

Principles:

- **`.worktreeinclude` is the declaration; `jean.json` setup is the executor.** Jean does not read `.worktreeinclude` (verified against source) — so the setup script must perform the copies itself using `$JEAN_ROOT_PATH`. The `.worktreeinclude` file still ships for Claude Code WorktreeCreate hooks, other tools, and humans. Keep the two in sync; generate the setup copy-lines *from* the include list.
- Copy **small config** (`.env*`, `.claude/`, `.agents/`) with `cp`; clone **big artifacts** (`node_modules/`, `target/`, `.venv/`) with COW (`cp -Rc` on APFS — measured ~3ms for what a normal copy takes seconds on) or skip them for store-backed installs (`pnpm install --prefer-offline` is already near-instant).
- **Never symlink `node_modules`** across worktrees — parallel agents would mutate shared state and realpath-resolving tools break.
- Order setup: copies first (cheap, unblocks the agent), install second, slow warmups last or not at all.
- `run` uses the array form when there are independent processes (api + web + worker).
- teardown must be idempotent and safe to run twice (`docker compose down --remove-orphans || true`).

### Phase 3 — Test in a throwaway worktree (the gate)

Simulate exactly what Jean does, with the same env contract:

```bash
ROOT=$(git rev-parse --show-toplevel)
TB="jean-test-$(date +%s)"
WT="$(mktemp -d)/$TB"
git -C "$ROOT" worktree add -b "$TB" "$WT"

# replicate Jean's execution: login shell, cwd=worktree, three env vars
JEAN_WORKSPACE_PATH="$WT" JEAN_ROOT_PATH="$ROOT" JEAN_BRANCH="$TB" \
  zsh -l -c "cd '$WT' && <setup script verbatim from your draft jean.json>"
```

Verify each contract, not vibes:

1. **Setup exit code 0** and every declared copy landed (`ls "$WT"/.env*` etc.).
2. **Run works:** launch the run command in background from the worktree; poll the declared port(s) (`curl -fsS localhost:<port>` or `nc -z`) until up or a deadline; capture the failure output if not.
3. **Teardown works:** run it, confirm processes/containers/ports are actually released (`lsof -i :<port>` empty), then run it **again** to prove idempotence.
4. **Timing:** record wall-clock of setup. If install dominates, apply one optimization from `references/worktree-optimization.md` and re-test.

Any failure → fix the draft, re-run the phase. Do not weaken a check to pass it. Three distinct failed approaches on the same step → surface the evidence and ask.

### Phase 4 — Finalize

Only after Phase 3 is green:

1. Write final `jean.json` + `.worktreeinclude` at the repo root.
2. Ensure `.worktreeinclude`'s entries are actually gitignored (intersection rule: only ignored∩listed files copy) and that `jean.json` itself is **not** gitignored.
3. **AGENTS.md:** add/refresh a "Worktrees & jean.json" section so any agent — Jean or not — can bootstrap a worktree by hand. Use the block in `references/templates.md#agents-md-section`: what jean.json is, the manual equivalent (`git worktree add` + the same setup commands + the env vars), the ports table, and the teardown expectation. If AGENTS.md doesn't exist but CLAUDE.md does, put it there; if neither, create AGENTS.md.
4. Commit (`feat(dev-env): add jean.json worktree automation` or repo's convention).

### Phase 5 — Retire test artifacts

```bash
git -C "$ROOT" worktree remove --force "$WT"
git -C "$ROOT" branch -D "$TB"
git -C "$ROOT" worktree prune
git -C "$ROOT" worktree list && git -C "$ROOT" branch --list 'jean-test-*'   # both must show no test leftovers
```

Also kill anything the run test started (final `lsof -i :<port>` check). Report ends with: files committed, setup wall-clock time, proof summary, cleanup confirmation.

## Decision rules

- Existing `jean.json` present → diff-and-improve, never blind-overwrite; keep working script lines unless evidence says they're wrong.
- Secret files found (`.env` with real credentials) → copy them via setup/include as designed, but **never** print their contents into output or commit them; verify they remain gitignored.
- No dev server (library/CLI repo) → `run` = test or build watcher, `ports` omitted; don't invent a server.
- Setup would exceed ~60s even optimized → keep the slow step but move it to the *end* of the setup script (Jean runs setup in background; the agent can start typing immediately) and note the tradeoff.
- Repo already has a worktree bootstrap script (`scripts/setup-worktree.sh` etc.) → have `jean.json` call it instead of duplicating logic.
- Monorepo → one root `jean.json`; scope setup/run to the package(s) actually developed, per `references/templates.md`.
- Not on macOS/APFS → drop `cp -c`, fall back to store-backed installs (pnpm/uv/cargo already dedupe globally).

## Reference routing

| File | Read when |
|---|---|
| `references/jean-json-spec.md` | Writing any `jean.json` field — exact schema, `$JEAN_*` env contract, shell/exec semantics, failure behavior, and `.worktreeinclude` semantics (intersection rule, tool support matrix). |
| `references/worktree-optimization.md` | Setup is slow, ports collide across parallel worktrees, big dependency dirs, docker-compose per worktree, shared caches. |
| `references/templates.md` | Drafting — per-stack `jean.json` + `.worktreeinclude` starters and the AGENTS.md section template. |

## Red flags — stop and fix

- About to write `jean.json` without having read `.gitignore` and package scripts → back to Phase 1.
- About to report done without a fresh-worktree run → Phase 3 is the definition of done.
- `git worktree list` still shows a `jean-test-*` path in the final report → cleanup incomplete.
- Setup script contains an unguarded `rm -rf` on a variable path → rewrite using `$JEAN_WORKSPACE_PATH` prefix.
- `.worktreeinclude` lists a tracked file → it will never copy (intersection rule); remove it or untrack the file.
