# scripts/

Every script gets a paired `<name>.md` doc. Detailed docs live alongside each script. This file is the index — phase, mode, mutation status, gate.

## Conventions

- Every executable is `chmod +x` and has the proper shebang (`#!/usr/bin/env bash` / `#!/usr/bin/env python3` / `#!/usr/bin/env node`).
- Bash scripts target POSIX `bash` (no zsh-isms); Python scripts are 3.10+ stdlib-only; mjs scripts are Node 22+ ESM.
- Mutators (`*-update`, `cleanup-*`, `setup-worktree.sh`) default to dry-run for the user-facing Python variants and to silent-execute for the runner-internal bash variants. The Python rule is the spec; the bash variant is correct because runners never prompt.
- Read-only diagnostics (`audit-*`, `list-*`, `classify-*`, `apply-*`, `rescue-detect.py`) never modify state under any flag.
- Every script supports `--help` (or equivalent usage on missing args).
- Bash scripts source `codex-flags.sh` for `CODEX_FLAGS`. None hard-code the flag list.

## By role

| Group | Scripts |
|---|---|
| Source-of-truth | `codex-flags.sh` |
| Top-level dispatcher | `orchestrate-codex.mjs` |
| Pre-flight | `bootstrap.sh` |
| Per-mode runners | `run-fleet.sh`, `run-batch.sh`, `run-single.sh`, `run-review.sh` |
| Worktree lifecycle | `setup-worktree.sh`, `list-worktrees.py`, `cleanup-worktrees.py` |
| Manifest mutators | `manifest-update.sh` (bash), `manifest-update.py` (python) |
| Auditors | `audit-fleet-state.py`, `audit-sizes.sh` |
| Observability | `codex-monitor.sh`, `codex-json-filter.sh` |
| Templating | `render-prompts.sh` |
| Review helpers | `classify-review-feedback.py`, `apply-review-decisions.py` |
| Rescue | `rescue-detect.py` |
| Test | `test-monitor-integration.mjs` |
| Vendored | `codex-cc/codex-companion.mjs`, `codex-cc/app-server-broker.mjs`, `codex-cc/lib/*` (15 files) |

## By mode

| Mode | Pre-flight | Spawn | Observability | Manifest | Cleanup |
|---|---|---|---|---|---|
| exec | `bootstrap.sh` | `orchestrate-codex.mjs exec` → `run-fleet.sh` (uses `setup-worktree.sh` per task) | `codex-monitor.sh` | `manifest-update.sh` (per task), `audit-fleet-state.py` | `cleanup-worktrees.py` |
| batch | `bootstrap.sh` | `orchestrate-codex.mjs batch` → `render-prompts.sh` → `run-batch.sh` | `codex-monitor.sh --tail-runner-log` | `manifest-update.sh`, `audit-fleet-state.py`, `audit-sizes.sh` | (no worktrees to tidy; manifest deleted) |
| single | `bootstrap.sh` | `orchestrate-codex.mjs single` → `run-single.sh` (uses `codex-json-filter.sh`) | filter pipe is the monitor | `manifest-update.sh` | `cleanup-worktrees.py` (if a fresh worktree was created) |
| review | `bootstrap.sh` | `orchestrate-codex.mjs review` → `run-review.sh` (uses `setup-worktree.sh`, `classify-review-feedback.py`, `apply-review-decisions.py`) | `codex-monitor.sh --review` | `manifest-update.sh` | `cleanup-worktrees.py` |
| rescue | `bootstrap.sh` | `orchestrate-codex.mjs rescue` → `rescue-detect.py` (classify) → original mode's runner | inherits original mode | `manifest-update.sh` | inherits original mode |
| audit | n/a | `orchestrate-codex.mjs audit` → `audit-fleet-state.py` | n/a (read-only) | n/a | n/a |
| tidy | n/a | `orchestrate-codex.mjs tidy` → `cleanup-worktrees.py --execute` | n/a | manifest deleted post-tidy | n/a |

## By mutation

| Script | Mutates? | Gate |
|---|---|---|
| `codex-flags.sh` | no (sourced) | n/a |
| `orchestrate-codex.mjs` | writes manifest | concurrent-run refusal |
| `bootstrap.sh` | creates state-dir | none (idempotent) |
| `setup-worktree.sh` | creates worktree | refuses if exists unless `ALLOW_REUSE=1` |
| `render-prompts.sh` | writes prompt files | none (skips collisions) |
| `run-fleet.sh` | spawns codex, auto-commits, writes manifest | `--dry-run` flag |
| `run-batch.sh` | spawns codex, writes answers, writes manifest | none (idempotent skip-existing) |
| `run-single.sh` | spawns codex, writes answer, writes manifest | none |
| `run-review.sh` | spawns codex review, writes findings, writes manifest | none |
| `codex-monitor.sh` | reads state | n/a (read-only loop) |
| `codex-json-filter.sh` | filters stdin | n/a |
| `audit-sizes.sh` | reads `answers/` | n/a (read-only) |
| `audit-fleet-state.py` | reads manifest + filesystem | n/a (read-only) |
| `list-worktrees.py` | reads git state | n/a |
| `cleanup-worktrees.py` | removes worktrees, deletes manifest | `--execute` flag |
| `manifest-update.sh` | writes manifest | none (silent execute by design — runner-internal) |
| `manifest-update.py` | writes manifest | `--execute` flag |
| `classify-review-feedback.py` | writes classified.json | n/a |
| `apply-review-decisions.py` | reads decisions.json | n/a (read-only — main agent applies) |
| `rescue-detect.py` | reads manifest + filesystem | n/a (read-only) |
| `test-monitor-integration.mjs` | writes /tmp test fixtures | n/a (test only) |

## Per-script paired docs

| Script | Doc |
|---|---|
| `codex-flags.sh` | `codex-flags.md` |
| `orchestrate-codex.mjs` | `orchestrate-codex.md` |
| `bootstrap.sh` | `bootstrap.md` |
| `setup-worktree.sh` | `setup-worktree.md` |
| `render-prompts.sh` | `render-prompts.md` |
| `run-fleet.sh` | `run-fleet.md` |
| `run-batch.sh` | `run-batch.md` |
| `run-single.sh` | `run-single.md` |
| `run-review.sh` | `run-review.md` |
| `codex-monitor.sh` | `codex-monitor.md` |
| `codex-json-filter.sh` | `codex-json-filter.md` |
| `audit-sizes.sh` | `audit-sizes.md` |
| `audit-fleet-state.py` | `audit-fleet-state.md` |
| `list-worktrees.py` | `list-worktrees.md` |
| `cleanup-worktrees.py` | `cleanup-worktrees.md` |
| `manifest-update.sh`, `manifest-update.py` | `manifest-update.md` (shared — both helpers documented in one file) |
| `classify-review-feedback.py` | `classify-review-feedback.md` |
| `apply-review-decisions.py` | `apply-review-decisions.md` |
| `rescue-detect.py` | `rescue-detect.md` |
| `test-monitor-integration.mjs` | `test-monitor-integration.md` |

## Vendored tree

`codex-cc/` is a vendored copy of `openai/codex-plugin-cc`'s `plugins/codex/scripts/` tree (minus the two hooks). See `codex-cc/UPSTREAM.md` for the pinned version, the patch (`codex.mjs.patch`), and the update procedure. Routing details for when the dispatcher / rescue uses these scripts: `references/universal/codex-companion.md`.

## Adding a new script

1. Author the script with the proper shebang and `chmod +x`.
2. Write the paired `<name>.md` doc following the format of the existing docs (Inputs / Outputs / Exit codes / Behavior / Notes).
3. Add a row to this README's "Per-script paired docs" table.
4. Reference the script in `SKILL.md`'s "Scripts" table OR in the appropriate `references/modes/<mode>.md`.
5. Run `python3 <repo-root>/scripts/validate-skills.py` to confirm references are linked.
