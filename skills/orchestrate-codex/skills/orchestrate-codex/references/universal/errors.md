# Error code catalog — `node orchestrate-codex.mjs`

One page, one row per `error.code` the dispatcher emits. Grep here first; jump to the deep-dive only when the row is not enough.

Source of truth: `scripts/orchestrate-codex.mjs` — every `errEnvelope(...)` call site plus the `EXIT_CODE_BY_ERROR` map (lines 134-178). Helper-internal codes (Python helpers, bash runners) are not catalogued here unless they bubble through the dispatcher envelope.

## Contents

- Catalog
- How to read an error envelope
- Common patterns
- See also

## Catalog

| `error.code` | What it means | Exit | First-line recovery | Deep-dive |
|---|---|---|---|---|
| `unknown_mode` | Subcommand is not one of `exec\|batch\|single\|review\|rescue\|audit\|tidy\|help`. | 2 | Re-run with a valid subcommand. `node orchestrate-codex.mjs help`. | SKILL.md "Detect the mode" |
| `unknown_option` | A `--flag` was passed that this subcommand does not accept. The first offender is in `error.message`; the full list is in `error.unknown_options`. | 2 | Drop the flag, or move it to the subcommand that owns it. The dispatcher uses long-form flags only. | SKILL.md "Step 2 — Universal pre-flight" |
| `missing_required_arg` | A required flag for the chosen mode is absent (e.g. `--tasks` for `exec`, `--inputs`+`--template` for `batch`, `--prompt`/`--prompt-file` for `single`, `--branches` for `review`). | 2 | Re-invoke with the named flag populated. | `modes/<mode>.md` |
| `bad_argument` | Flag is present but malformed — bad value type, bad combination, or invalid for the active mode (e.g. `--apply` outside `rescue`, unsupported `mode_state` for rescue redispatch). | 2 | Read `error.message` for the specific argument; fix it. | `modes/<mode>.md` |
| `bad_inputs_file` | `--inputs <file>` is missing, empty after stripping blanks, or has a duplicate row that would collide on slug. | 2 | Inspect the file. Disambiguate duplicates; ensure ≥1 non-blank row. | `modes/batch.md` |
| `bad_tasks_file` | `--tasks <tasks.json>` is missing, not a JSON array of `{id\|slug, prompt\|prompt_file}`, empty, or a row references a `prompt_file` path that does not exist. | 2 | Validate JSON shape; check every `prompt_file` exists. | `modes/exec.md` |
| `bad_template_file` | `--template <tmpl>` path does not exist. | 2 | Pass the right path; confirm `XXXXXXXXXXXXX` placeholder is in the file. | `modes/batch.md` |
| `bad_prompt_input` | `--prompt-file` (single mode) or per-task prompt file path does not exist on disk. | 2 | Fix the path, or use `--prompt "..."` inline. | `modes/single.md` |
| `bad_branches_input` | `review` mode got no resolvable branches — empty file, empty comma list, or no positionals. | 2 | Pass at least one branch via `--branches <file-or-comma-list>` or positional args. | `modes/review.md` |
| `bad_schema_file` | A schema file referenced by the subcommand is malformed JSON or wrong shape. | 2 | Validate the schema file; re-emit valid JSON. | `modes/<mode>.md` |
| `not_a_repo` | `review` (and any other git-required mode) was invoked outside a git working tree. | 2 | `cd` into the repo. `git rev-parse --is-inside-work-tree` must succeed. | SKILL.md preflight step 3 |
| `manifest_not_found` | `rescue` / `audit` / `tidy` got no manifest at the resolved path. The manifest may have been tidied, or `--manifest <path>` is wrong. | 3 | Pass an explicit `--manifest <abs-path>`, or enumerate siblings with `ls "$(orchestrate-codex --resolve-state-dir)/manifest"*.json`. | `idempotency.md#enumerating-manifest-siblings` |
| `manifest_corrupt` | The manifest file exists but is not valid JSON. | 3 | Inspect, repair (or delete) the file. **Never** force-overwrite a manifest with running entries. Use `audit-fleet-state.py` to triage; `manifest-update.py` to fix. | `manifest-contract.md` |
| `manifest_stale` | `rescue` refused a manifest older than 7 days (`started_at` field). Old manifests reference deleted branches and pruned codex-companion job records. | 3 | Re-run `rescue` with `--accept-stale` to override consciously. | `modes/rescue.md` |
| `schema_version_too_new` | Manifest's `schema_version` is greater than the skill's `SCHEMA_VERSION` constant. Forward-incompatible by design — newer manifests may carry semantically-required `mode_state.*` or `policy.*` fields the older code cannot reason about. The dispatcher refuses cleanly rather than silently downgrading. | 3 | **Upgrade the skill** (or its installed pack) to a version with `SCHEMA_VERSION >= manifest.schema_version`. Do NOT hand-edit the manifest's `schema_version` to coerce it; that strips the contract. **There is no dispatcher flag to bypass this check** — `--accept-stale` is freshness-only, `--force-new-run` writes a sibling but does not skip the gate, and no `--schema-ignore` / `--force-schema-downgrade` flag exists by design. The forward-incompatible refusal IS the contract. | `failure-modes.md`, `manifest-contract.md` |
| `concurrent_run_in_progress` | A manifest at the resolved path has ≥1 entry in `queued` or `running`. The dispatcher refuses to start a parallel run on the same manifest. `error.recovery_options` enumerates the three paths. | 3 | (1) wait for the live run to finish; (2) `rescue` to re-attach and redispatch; (3) `--force-new-run --run-id <custom>` for a sibling manifest. | `idempotency.md#dispatcher-refusal` |
| `manifest_inflight_race` | A second `seedManifest` race condition wrote to a manifest that flipped to in-flight between the concurrent-run gate and the actual seed write. Defense-in-depth — same shape as `concurrent_run_in_progress`. | 3 | Wait, then re-run. Or `rescue` to take over. | `idempotency.md` |
| `spawn_failed` | A subprocess (bootstrap.sh, runner script) could not be spawned, was missing on disk, or exited non-zero with no auth-specific signal. `error.stdout`/`error.stderr` carry the captured streams. | 4 | Read the captured stderr; verify `scripts/<runner>.sh` exists and is executable; check the working tree. | `failure-modes.md` |
| `python_helper_failed` | A Python helper (`rescue-detect.py`, `manifest-update.py`, `cleanup-worktrees.py`) exited non-zero or returned non-JSON. `error.stdout`/`error.stderr` carry the captured streams. | 4 | Inspect the captured stderr. The helper itself is read-only when called from the dispatcher; the most common cause is malformed manifest input. | `manifest-contract.md`, `modes/rescue.md` |
| `codex_unauthenticated` | `bootstrap.sh` saw `codex login status` exit non-zero (status 2 or 3 from the script). Codex spawns would fail immediately. | 5 | Run `codex login`; re-invoke. Bypass with `ORCHESTRATE_SKIP_CODEX_AUTH=1` only when using bearer-token / managed-companion / proxy auth where `login status` reports false-negative. | SKILL.md preflight step 2 |
| `codex_unavailable` | `command -v codex` returned nothing. The CLI is not on PATH; the detached runner would exit immediately and strand the manifest. | 5 | Install codex-cli (https://github.com/openai/codex). Verify with `codex --version`. | SKILL.md preflight step 1 |

Any unmapped error code falls back to **exit 1** (see `EXIT_CODE_BY_ERROR` default in `orchestrate-codex.mjs:178`).

## How to read an error envelope

Every dispatcher invocation prints exactly one JSON envelope on stdout, newline-terminated. On failure:

```json
{
  "ok": false,
  "schema_version": "<n>",
  "command": "<subcommand>",
  "error": {
    "code": "<one of the codes above>",
    "message": "<human-readable explanation>",
    "...extra": "<context fields specific to the code>"
  },
  "meta": { "...": "..." }
}
```

- `error.code` is the catalog key. Stable across versions.
- `error.message` is human-readable; never machine-grep this — grep `error.code`.
- Code-specific extras: `concurrent_run_in_progress` carries `manifest_path`, `inflight_count`, `inflight_ids`, `recovery_options[]`. `manifest_stale` carries `manifest_path`, `started_at`, `age_days`. `unknown_option` carries `unknown_options[]`. `spawn_failed` and `python_helper_failed` carry `stdout` and `stderr`. Inspect them before triage.
- Exit code maps from `error.code` via `EXIT_CODE_BY_ERROR` (see catalog table). 0 = success, 1 = unmapped, 2 = bad input, 3 = manifest state, 4 = subprocess, 5 = codex prerequisites.

## Common patterns

### `concurrent_run_in_progress`

The single most-hit envelope. Two recovery paths are roughly equivalent in operator effort; pick by intent.

```bash
# Resume the existing run (most common — preserves history, classifier-driven redispatch):
node scripts/orchestrate-codex.mjs rescue --manifest <path>

# Run in parallel without disturbing the live run (sibling manifest):
node scripts/orchestrate-codex.mjs <mode> --force-new-run --run-id <custom> ...
```

Envelope shape:

```json
{"ok": false, "command": "exec",
 "error": {"code": "concurrent_run_in_progress",
           "manifest_path": "...", "inflight_count": 3,
           "inflight_ids": ["01-foo","02-bar","03-baz"],
           "recovery_options": ["wait","rescue","--force-new-run --run-id <custom>"]}}
```

Discipline note: parallel siblings race undetected on overlapping slugs (same `answers/<slug>.md` file, same exec worktree path). Keep slug spaces disjoint. See `idempotency.md` "Disjoint-slug discipline".

### `manifest_stale`

Triggered only by `rescue` against a manifest older than 7 days.

```bash
# Override consciously after confirming the worktrees / branches still exist:
node scripts/orchestrate-codex.mjs rescue --manifest <path> --accept-stale
```

The manifest age is in `error.age_days`; `--accept-stale` downgrades the gate to a stderr WARN.

### `bad_argument`

Most often: `--apply` value not in `{failed-only, never-started-only, all-non-done, ids:s1,s2,...}`, or a flag passed to the wrong subcommand. Read `error.message`; the dispatcher names the offending argument.

```bash
# Wrong:    --apply failed
# Right:    --apply failed-only
# Wrong:    rescue --tasks tasks.json
# Right:    rescue --manifest <path> --apply <subset>
```

### `codex_unauthenticated`

Pre-flight gate from `bootstrap.sh`. Either fix the auth state or bypass deliberately.

```bash
# Normal fix:
codex login
node scripts/orchestrate-codex.mjs <mode> ...

# Bypass for bearer-token / managed / proxy auth:
ORCHESTRATE_SKIP_CODEX_AUTH=1 node scripts/orchestrate-codex.mjs <mode> ...
```

If you bypass, verify auth another way before declaring pre-flight green — a stranded manifest is the failure mode this gate exists to prevent.

## See also

- `failure-modes.md` — the 7-row failure taxonomy with per-row remediation. Errors above are dispatcher-time refusals; failure modes are runtime-time.
- `idempotency.md` — concurrent-run, force-new-run, sibling enumeration, force-redo.
- `manifest-contract.md` — schema, atomic writes, repair workflow when `manifest_corrupt` fires.
- `modes/rescue.md` — full rescue lifecycle and `--apply` semantics.
