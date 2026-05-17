# scripts/

The unification refactor (v2.0-beta; see `../BEHAVIOR-DELTA.md`) is in progress. This README reflects the v2.0-beta layout. Old script names continue to work via deprecation shims through v2.x and are removed in v3.0.

## Conventions

- Every executable is `chmod +x` and has the proper shebang (`#!/usr/bin/env bash` / `#!/usr/bin/env python3` / `#!/usr/bin/env node`).
- Bash scripts target POSIX `bash` (no zsh-isms); Python scripts are 3.10+ stdlib-only; mjs scripts are Node 22+ ESM.
- Mutators (`*-update`, `cleanup-*`, `render.sh`, `setup-worktree.sh`) default to dry-run for the user-facing Python variants and to silent-execute for the runner-internal bash variants. The Python rule is the spec; the bash variant is correct because runners never prompt.
- Read-only diagnostics (`audit.py`, `classify-review-feedback.py`, `apply-review-decisions.py`, `rescue-detect.py`) never modify state under any flag.
- Every script supports `--help` (or equivalent usage on missing args). `.md` docs are auto-generated from `--help` via `build-docs.mjs`.
- Bash scripts source `_lib.sh` (which sources `codex-flags.sh`) for `CODEX_FLAGS` and helpers. None hard-code the flag list.

## By role

| Group | Active | Deprecated shim |
|---|---|---|
| Constants & shared libs | `constants.json`, `_lib.sh`, `_lib.py` | — |
| Source-of-truth | `codex-flags.sh` | — |
| Top-level dispatcher | `run-codex-1.mjs` | — |
| Pre-flight | `preflight.sh` | `bootstrap.sh` |
| Per-mode runners | `run-fleet.sh`, `run-batch.sh`, `run-single.sh`, `run-review.sh` | — |
| Worktree lifecycle | `setup-worktree.sh`, `audit.py worktrees`, `cleanup-worktrees.py` | `list-worktrees.py` |
| Manifest mutators | `manifest-update.py` | `manifest-update.sh` |
| Auditors | `audit.py {state,sizes,worktrees}` | `audit-fleet-state.py`, `audit-sizes.sh`, `list-worktrees.py` |
| Observability | `codex-monitor.sh`, `codex-json-filter.sh` | — |
| Templating | `render.sh --mode {template,wrap}` | `render-prompts.sh`, `render-task-prompts.sh` |
| Review helpers | `classify-review-feedback.py` (incl. `--apply-queue`) | `apply-review-decisions.py` |
| Rescue | `rescue-detect.py` | — |
| Test | `test.mjs`, `__fixtures__/run-parity.mjs` | `test-monitor-integration.mjs`, `test-runner-contracts.mjs` |
| Maintenance | `build-docs.mjs` | — |
| Vendored | `codex-cc/codex-companion.mjs`, `codex-cc/app-server-broker.mjs`, `codex-cc/lib/*` | — |

## By mode

| Mode | Pre-flight | Spawn | Observability | Manifest | Cleanup |
|---|---|---|---|---|---|
| exec | `preflight.sh` (manual) | `run-codex-1.mjs exec` → `run-fleet.sh` (uses `setup-worktree.sh` per task) | `codex-monitor.sh` | runners call `python3 manifest-update.py --execute` (via `_lib.sh::oc_manifest_set`); audit via `audit.py state` | `cleanup-worktrees.py` |
| batch | `preflight.sh` (manual) | `run-codex-1.mjs batch` → `render.sh --mode template` → `run-batch.sh` | `codex-monitor.sh --tail-runner-log` | `audit.py {state,sizes}` | (no worktrees to tidy; manifest deleted) |
| single | `preflight.sh` (manual) | `run-codex-1.mjs single` → `run-single.sh` (uses `codex-json-filter.sh`) | filter pipe is the monitor | manifest writes through Python | `cleanup-worktrees.py` only when prior exec/review worktrees need cleanup |
| review | `preflight.sh` (auto) | `run-codex-1.mjs review` → `run-review.sh` (uses `setup-worktree.sh`, `classify-review-feedback.py`) | `codex-monitor.sh` | manifest writes through Python | `cleanup-worktrees.py` |
| rescue | n/a for classify; original mode on redispatch | `run-codex-1.mjs rescue` → `rescue-detect.py`; `--apply ...` → original mode's runner | inherits original mode | manifest writes through Python | inherits original mode |
| audit | n/a | `run-codex-1.mjs audit` → `audit.py state` | n/a (read-only) | n/a | n/a |
| tidy | n/a | `run-codex-1.mjs tidy` → `cleanup-worktrees.py --execute` | n/a | manifest deleted post-tidy | n/a |

## By mutation

| Script | Mutates? | Gate |
|---|---|---|
| `_lib.sh`, `_lib.py`, `constants.json`, `codex-flags.sh` | no (libs/data) | n/a |
| `run-codex-1.mjs` | writes manifest | concurrent-run refusal |
| `preflight.sh` | creates state-dir | none (idempotent) |
| `setup-worktree.sh` | creates worktree; runs `$WORKTREE_SETUP_HOOK` | refuses if exists unless `ALLOW_REUSE=1`; exit 6 on hook fail |
| `render.sh --mode template` | writes prompt files | hard-fails slug collisions unless `--force`; atomic write |
| `render.sh --mode wrap` | writes wrapped files | hard-fails collisions unless `--force`; atomic write |
| `run-fleet.sh` | spawns codex, auto-commits, writes manifest | `--dry-run` flag; `--only` subset |
| `run-batch.sh` | spawns codex, writes answers, writes manifest, writes audit report | `--dry-run` flag; idempotent skip when manifest status is `done` |
| `run-single.sh` | spawns codex, writes answer, writes manifest | `--dry-run` flag |
| `run-review.sh` | spawns codex review, writes findings, writes manifest | `--dry-run` flag; terminal states only |
| `codex-monitor.sh` | reads state, appends `monitor.log` | n/a (read-only loop) |
| `codex-json-filter.sh` | filters stdin | n/a |
| `audit.py {state,sizes,worktrees}` | reads manifest + filesystem | n/a (read-only) |
| `cleanup-worktrees.py` | removes worktrees, deletes manifest | `--execute` flag |
| `manifest-update.py` | writes manifest atomically (flock + tempfile + os.replace) | `--execute` flag; lock-timeout exits 3 |
| `classify-review-feedback.py` | reads review JSON; `--apply-queue` forwards to apply-review-decisions.py | n/a |
| `rescue-detect.py` | reads manifest + filesystem | n/a (read-only) |
| `build-docs.mjs` | rewrites `<script>.md` files | `--update` flag (default is `--check`) |
| `test.mjs` | writes test tmpdirs (cleaned up) | n/a (test only) |
| `__fixtures__/run-parity.mjs` | reads fixture set; `--update` rewrites | `--update` flag |
| **All deprecation shims** | forward to canonical script; append WARN to ledger | n/a |

## Per-script paired docs

Auto-generated from `--help` by `build-docs.mjs` (use `node build-docs.mjs --update` to regenerate; `--check` is the CI gate). Hand-written content lives inside `<!-- BEGIN WHY --> ... <!-- END WHY -->` blocks per file and is preserved across regenerations.

| Active script | Doc |
|---|---|
| `run-codex-1.mjs` | `run-codex-1.md` |
| `constants.json` | (data file; documented in `_lib.py` and `_lib.sh`) |
| `_lib.sh`, `_lib.py` | (library files; documented inline + in `architecture/01` of the unification strategy) |
| `codex-flags.sh` | `codex-flags.md` |
| `preflight.sh` | `preflight.md` (auto-generated) |
| `setup-worktree.sh` | `setup-worktree.md` |
| `render.sh` | `render.md` (auto-generated) |
| `run-fleet.sh` | `run-fleet.md` |
| `run-batch.sh` | `run-batch.md` |
| `run-single.sh` | `run-single.md` |
| `run-review.sh` | `run-review.md` |
| `codex-monitor.sh` | `codex-monitor.md` |
| `codex-json-filter.sh` | `codex-json-filter.md` |
| `audit.py` | `audit.md` (auto-generated) |
| `cleanup-worktrees.py` | `cleanup-worktrees.md` |
| `manifest-update.py` | `manifest-update.md` |
| `classify-review-feedback.py` | `classify-review-feedback.md` |
| `rescue-detect.py` | `rescue-detect.md` |
| `build-docs.mjs` | `build-docs.md` (auto-generated) |
| `test.mjs` | (documented inline + in `tasks/05` of the unification strategy) |

Deprecation shims keep their original `.md` files (`bootstrap.md`, `audit-fleet-state.md`, etc.) for one release as historical reference. v3.0 removes both script and doc.

## Vendored tree

`codex-cc/` is a vendored copy of `openai/codex-plugin-cc`'s `plugins/codex/scripts/` tree (minus the two hooks). The paired-doc rule does not apply inside this subtree; it is covered as one vendored unit by `codex-cc/UPSTREAM.md` and `references/maintenance/codex-companion.md` (with `references/maintenance/upstream-codex-cc.md` for the bump procedure). Route `codex-cc/lib/*` as a subtree, not as individual top-level scripts.

## Adding a new script

1. Author the script with the proper shebang and `chmod +x`. Bash scripts should `source "${OC_LIB_DIR}/_lib.sh"` early; Python scripts should `from _lib import ...`.
2. Add `--help` output that fully documents flags, env vars, and exit codes (this becomes the `.md` doc body).
3. Run `node build-docs.mjs --update --script <name>` to generate the paired `<name>.md` file with a stub WHY block.
4. Edit the `<!-- BEGIN WHY --> ... <!-- END WHY -->` block to add hand-written narrative (why this exists, when to use it, cross-references).
5. Reference the script in `SKILL.md`'s "Scripts" table or in the appropriate `references/modes/<mode>.md`.
6. Run `python3 ../../../../../../../scripts/validate-skills.py` to confirm references are linked, then `node build-docs.mjs --check` to confirm the doc matches `--help`.

## Test fixtures

`__fixtures__/` contains the pre-refactor baseline (`baseline/`) and cross-language golden fixtures (`golden/`). `run-parity.mjs` replays them against the current code. `bin/codex-stub` is a fake codex CLI for testing without real API calls. See `__fixtures__/README.md` for details.
