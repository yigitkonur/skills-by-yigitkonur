# Behavior Delta — v1 → v2.0-beta

Every observable change in the orchestrate-codex unification refactor (branch
`feat/orchestrate-codex-unification-263c3eec`). Backward-compat preserved
through 1 release; deprecated paths removed in v3.0.

## Renamed scripts (with 1-release shims; removed in v3.0)

Each shim logs `WARN deprecated_script` to the run ledger when invoked via the
old name. Internal callers (dispatcher + runners) use the new names directly so
the warning fires only for external callers.

| Old path | New path | Notes |
|---|---|---|
| `bootstrap.sh` | `preflight.sh` | rename clarifies "runs for every mode, not only review" |
| `manifest-update.sh` | `manifest-update.py --execute` | bash variant retired; Python is canonical |
| `audit-fleet-state.py` | `audit.py state` | subcommand of unified audit.py |
| `audit-sizes.sh` | `audit.py sizes` | Python port of bash math (count/mean/stdev) |
| `list-worktrees.py` | `audit.py worktrees` | subcommand |
| `render-prompts.sh` | `render.sh --mode template` | unified renderer |
| `render-task-prompts.sh` | `render.sh --mode wrap` | unified renderer |
| `test-monitor-integration.mjs` | `test.mjs --section pure-functions` | consolidated harness |
| `test-runner-contracts.mjs` | `test.mjs --section subprocess` | consolidated harness |

## New scripts

| Path | Purpose |
|---|---|
| `scripts/_lib.sh` | Sourced helpers (oc_load_constants, oc_source_codex_flags, oc_install_signal_trap, oc_manifest_set, oc_log_run_ledger, oc_concurrency_check, oc_compute_slug, oc_acquire_run_lock) |
| `scripts/_lib.py` | Python helpers (Manifest with `with_lock`, Constants, json_envelope, resolve_state_dir, log_ledger_line, STATUS_TERMINAL/NON_TERMINAL, coerce_value with allowlist) |
| `scripts/constants.json` | Single source of truth for numeric constants and policy defaults |
| `scripts/audit.py` | Unified read-only audit (state/sizes/worktrees) |
| `scripts/render.sh` | Unified prompt renderer (template/wrap) |
| `scripts/preflight.sh` | Renamed from bootstrap.sh |
| `scripts/build-docs.mjs` | Doc auto-generator (regenerates *.md from `--help` output + WHY block) |
| `scripts/test.mjs` | Consolidated test harness |
| `scripts/__fixtures__/` | Test fixture tree (baseline + golden + parity runner + codex-stub) |
| `BEHAVIOR-DELTA.md` | This file |

## Bug fixes (behavior changed to match documented intent)

### KB-001: `manifest-update.py` lock-timeout now exits 3

- **Was:** uncaught `SystemExit` from `acquire_lock` → exit code 1
- **Now:** typed `LockTimeout` exception caught in `main()`; exits 3 with `error.code="lock_timeout"`; matches bash sibling and documented contract
- **Detection in JSON mode:** `{"ok": false, "error": {"code": "lock_timeout", "message": "..."}}`

### KB-002: `audit.py state` exit-2 path removed

- **Was:** documented `exit 2` for "Manifest missing (still emits a report)" — never actually emitted
- **Now:** `audit.py state` exits 1 with `error.code="manifest_missing"` for missing manifest, `error.code="manifest_unreadable"` for corrupt; doc generated from `--help` reflects reality

### KB-003: `audit.py worktrees` JSON keys

- **Was:** doc claimed `dirty`, `ahead` keys; source emits real keys `dirty_count`, `commits_ahead_of_origin_main`, plus `upstream`, `unpushed`, `head`, `bare`, `detached`, `locked`, `prunable`
- **Now:** doc matches source; JSON consumers should use the real key names. Old `list-worktrees.py` shim continues to emit the same (correct) keys.

### KB-004: `render.sh --mode template` slug character class

- **Was:** doc claimed `[a-z0-9-]` (which would drop `.` and `_`); source kept them
- **Now:** doc and source agree on `[a-z0-9._-]`. Slugs like `foo.bar.md` and `01.config_v2.md` are preserved verbatim.

## New behaviors (additive; no breaking change)

### `WORKTREE_SETUP_HOOK` env var

- `setup-worktree.sh` invokes `$WORKTREE_SETUP_HOOK <wt-path>` after built-in setup steps when the env var points to an executable
- Non-zero exit produces new exit code **6** (`worktree_setup_hook_failed`)
- Useful for stacks the built-in symlink logic doesn't cover (Unity, Xcode, Gradle, Rust, embedded toolchains)
- Unset / non-executable → no-op (backward-compat for existing callers)

### Structured run ledger

- New env var `OC_RUN_LEDGER=<path>` enables structured logging
- Replaces the `2>/dev/null || true` resilience pattern (silenced lock contention, missing helpers, jq parse errors)
- Format: `<HH:MM:SSZ> [<LEVEL>] <source>: <msg> key=value ...`
- Consumers: `audit.py state` aggregates ERROR/WARN counts (future), Monitor surfaces them as flag (future), post-mortem grep
- Producers: `_lib.sh::oc_log_run_ledger` (bash), `_lib.py::log_ledger_line` (Python)
- Deprecation shims write to the ledger on every invocation (`WARN deprecated_script`)

### `classify-review-feedback.py --apply-queue <path>`

- New flag accepts a path to an evaluation/decisions JSON
- Forwards to `apply-review-decisions.py --eval <path>` (preserves all existing behavior; passes through `--json` and `--branch`)
- The fold is the v3.0 trajectory; for v2.0-beta, both invocations work

### Cross-language fixture parity

- `__fixtures__/golden/` contains shared JSON fixtures consumed by both `_lib.py` and `_lib.sh`
- Slug derivation, state-dir resolution, manifest atomic write, monitor tick rule engine — verified to produce identical results across languages
- Run via `python3 _lib.py --verify-fixtures` and `bash _lib.sh --verify-fixtures`

## Unchanged

- All dispatcher subcommand names: `exec`, `batch`, `single`, `review`, `rescue`, `audit`, `tidy`
- Manifest schema (`schema_version: 1`)
- Monitor `tool_hint` envelope shape (JS-object literal, `new Function(...)` evaluable)
- Sentinel lines: `--- all jobs finished ---`, `--- single done (...) ---`, `--- fleet quiet ---`
- Status enum: `queued | running | done | failed | skipped | converged | blocked | cap_reached`
- Per-mode concurrency defaults: exec=5, batch=10, single=1, review=4
- Concurrency soft cap (20) and hard cap (100) policies
- Codex spawn flag set (`--dangerously-bypass-approvals-and-sandbox`, `gpt-5.5`, `xhigh`)
- Detached spawn semantics (`result.runner_pid` ≠ `meta.pid`)
- `ORCHESTRATE_SKIP_CODEX_AUTH` / `ORCHESTRATE_SKIP_CODEX_PREFLIGHT` / `ORCHESTRATE_RUNNER_FOREGROUND` test hatches

## Deferred to follow-up (post v2.0-beta)

These items from the strategy are scoped for future commits, not v2.0-beta:

- **Dispatcher multi-round review loop** (Decision 11): the dispatcher currently invokes `run-review.sh <manifest> 1` and returns. The orchestrator (main agent) drives the multi-round loop manually. The loop's design is in `tasks/04`; wiring it into `handleReview` is the largest remaining Phase 3 item.
- **Runner internals migration** to use `_lib.sh`: the four runners still have their own `_run_<mode>_signal` handlers and call `manifest-update.sh` directly. The shared helpers are in place; mechanical migration is tracked as Phase 3.5.
- **Full doc regeneration**: `build-docs.mjs --update` was run for the new scripts only. Regenerating every existing script's `.md` is a separate commit so the WHY block additions can be reviewed atomically.
- **Test fixture coverage expansion**: Phase 0 captured `--help` fixtures for 22 current scripts. Runner stdout, monitor ticks, JSONL filter output, and audit/manifest state-transition fixtures are designed in `tasks/01` but not yet captured.

## CI gates added

- `git grep '2>/dev/null \\|\\| true' scripts/` — must return 0 lines (Phase 1 + runner migration)
- `python3 _lib.py --verify-fixtures` — golden fixtures pass
- `bash _lib.sh --verify-fixtures` — cross-language slug parity OK
- `node __fixtures__/run-parity.mjs --target current` — 22/22 help fixtures pass
- `node build-docs.mjs --check` — committed `.md` matches `--help` output (after full regen)

## Migration guide for downstream consumers

Most consumers see no change. If you:

- **Invoke `bash bootstrap.sh`** → keeps working; consider switching to `bash preflight.sh`
- **Invoke `bash manifest-update.sh`** → keeps working; consider switching to `python3 manifest-update.py --execute` or `oc_manifest_set` (via `source _lib.sh`)
- **Parse `audit-fleet-state.py --json` output** → keep working with the shim; new key set is a superset (no removed keys)
- **Parse `list-worktrees.py --json` output** → keep working; key names were always `dirty_count` / `commits_ahead_of_origin_main` (the doc was lying)
- **Invoke `bash audit-sizes.sh`** → keeps working; new `--json` flag now actually produces JSON (was a doc lie before)
- **Branch on `manifest-update.py` exit codes** → review handling of exit 3 (lock timeout, was 1); the bash sibling already used 3

## Source of strategy

`/Users/yigitkonur/dev/unification-strategy/` is the authoritative design spec.
- `inventory/02-preserved-functionality-checklist.md` — every behavior preserved
- `strategy/02-consolidation-decisions.md` — every merge/delete rationale
- `tasks/0X-*.md` — per-phase acceptance criteria

The pre-refactor audit baseline is at `scripts/__fixtures__/baseline/audit-pass-v1.md` (copy of `/tmp/orchestrate-codex-audit/MASTER-REPORT.md`, 87 CRITICAL findings). Re-running the same 22-agent audit pass against the refactored docs should reduce this toward 0; that's the v2.0-final acceptance bar.
