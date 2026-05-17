# Known bugs captured in baseline fixtures

Fixtures here capture CURRENT (pre-refactor) behavior. Some captures preserve documented bugs that the unification refactor intentionally fixes. Each `KB-NNN` entry below documents the bug, the fixture(s) that pin the buggy behavior, the decision driving the fix, and the expected post-refactor behavior.

When a phase fixes a bug, the corresponding fixture is updated atomically in the same PR.

## KB-001 — `manifest-update.py` lock-timeout exits 1 instead of 3

- **Fixture:** `baseline/manifest/lock-timeout-py.exit`
- **Current behavior:** uncaught `SystemExit` from `acquire_lock`; Python exits with code 1
- **Documented behavior:** doc claims exit 3 (matches bash sibling)
- **Decision:** `strategy/02 Decision 1` (consolidate to Python implementation; fix the exit code)
- **Phase:** `tasks/02` Phase 1
- **Post-refactor behavior:** exit 3 with `error.code="lock_timeout"`
- **Fixture update:** rewrite fixture `.exit` to `3` when Phase 1 ships

## KB-002 — `audit-fleet-state.py` exit code 2 documented but never emitted

- **Fixture:** `baseline/audit/audit-fleet-state-manifest-missing.exit`
- **Current behavior:** manifest-missing returns exit 1 (actionable path)
- **Documented behavior:** doc table claims exit 2 for "Manifest missing (still emits a report)"
- **Decision:** `strategy/02 Decision 2` (consolidate into `audit.py`; document real behavior)
- **Phase:** `tasks/03` Phase 2
- **Post-refactor behavior:** `audit.py state` exits 1 with `error.code="manifest_missing"`; doc reflects reality
- **Fixture update:** Phase 2 leaves the `.exit` unchanged (still 1); but updates the `.json` envelope to surface `error.code` instead of just being an actionable banner

## KB-003 — `list-worktrees.py` JSON keys are fictional in docs

- **Fixture:** `baseline/audit/list-worktrees-typical.json`
- **Current behavior:** real keys `dirty_count`, `commits_ahead_of_origin_main` (plus `head`, `bare`, `detached`, `locked`, `prunable`, `upstream`, `unpushed`)
- **Documented behavior:** doc claims `dirty`, `ahead` (which don't exist)
- **Decision:** `strategy/02 Decision 2`
- **Phase:** `tasks/03` Phase 2
- **Post-refactor behavior:** `audit.py worktrees --json` emits the real keys; doc generated from `--help` reflects them
- **Fixture update:** Phase 2 leaves the captured JSON unchanged (it's always been correct); only the `.md` doc changes

## KB-004 — `render-prompts.sh` slug character class drops `.` and `_`

- **Fixture:** `baseline/runners/render-prompts-with-dots-and-underscores.stdout`
- **Current source:** `tr -c 'a-z0-9._-' '-'` — keeps dots and underscores
- **Documented behavior:** doc claims `[a-z0-9-]` (which would drop them)
- **Decision:** `strategy/02 Decision 3` (consolidate into `render.sh`; doc the real char class)
- **Phase:** `tasks/03` Phase 2
- **Post-refactor behavior:** `render.sh --mode template` keeps `[a-z0-9._-]`; doc matches
- **Fixture update:** Phase 2 leaves the captured stdout unchanged (source was always correct); only the doc changes

## KB-005 — `manifest-update.sh` accepts `--reason`/`--actor` flags in any position before key=value list

- **Fixture:** `baseline/manifest/sh-flags-trailing.exit`
- **Current behavior:** flags must come BEFORE positional `key=value` pairs; trailing flags cause "bad pair" exit 2
- **Documented behavior:** doc usage line shows flags AFTER positional pairs
- **Decision:** `strategy/02 Decision 1` (Python is canonical; bash deprecated)
- **Phase:** `tasks/02` Phase 1 (shim absorbs the difference)
- **Post-refactor behavior:** `manifest-update.py` accepts flags in any position (argparse handles this); shim translates old positional invocations
- **Fixture update:** Phase 1 leaves the bash fixture unchanged (deprecation path); adds a Python fixture showing position-independent flags

## KB-006 — `run-fleet.sh` `COMMIT_LEVEL` default is 3, doc says 2

- **Fixture:** `baseline/runners/run-fleet-default-commit-level.stdout`
- **Current behavior:** source defaults `COMMIT_LEVEL=3` (level-3 subject + body + diffstat)
- **Documented behavior:** doc table claims default 2
- **Decision:** doc regeneration (`tasks/05` Phase 4)
- **Phase:** Phase 4
- **Post-refactor behavior:** doc generated from `--help` reflects the real default of 3
- **Fixture update:** none; fixture was always correct

## KB-007 — Three runners falsely document signal trap as `trap 'kill 0' TERM INT EXIT`

- **Fixture:** `baseline/runners/run-fleet-sigterm.exit`, `baseline/runners/run-batch-sigterm.exit`, `baseline/runners/run-review-sigterm.exit`
- **Current behavior:** every runner uses a named handler (`_run_<mode>_signal`) on TERM/INT only; EXIT handles only worklist cleanup; `pkill -TERM -g $$` then `pkill -KILL -g $$` then exit 143
- **Documented behavior:** all three docs claim `trap 'kill 0' TERM INT EXIT`
- **Decision:** doc regeneration; `strategy/02 Decision 7` extracts named handler to `_lib.sh::oc_install_signal_trap`
- **Phase:** Phase 1 extracts; Phase 4 regenerates docs
- **Post-refactor behavior:** one shared handler; doc reflects reality
- **Fixture update:** unchanged (exit code 143 is correct in source); doc changes

## KB-008 — Runner DONE/FAIL/SKIP lines have TWO spaces, docs show one

- **Fixture:** `baseline/runners/*-done-line-spacing.stdout`
- **Current behavior:** `printf "DONE  %s ..."` (two spaces)
- **Documented behavior:** every doc shows one space
- **Decision:** doc regeneration
- **Phase:** Phase 4
- **Post-refactor behavior:** docs reflect two-space format; Monitor regex anchors on this
- **Fixture update:** unchanged; doc changes only

## KB-009 — `run-single.sh --reuse-worktree` flag has no observable effect

- **Fixture:** `baseline/runners/run-single-reuse-worktree.exit`
- **Current behavior:** flag is parsed; sets `REUSE_WORKTREE=1` env var; never read further in the script
- **Documented behavior:** doc claims it "records that the selected cwd is an existing worktree; no new worktree is created"
- **Decision:** `strategy/02 Decision 16` notes single-mode runner unchanged
- **Phase:** Phase 4 (doc only)
- **Post-refactor behavior:** flag accepted for backward compatibility with a deprecation warning to the run ledger; doc states "vestigial flag, accepted but no effect; will be removed in v3.0"
- **Fixture update:** unchanged; add ledger-warn fixture in Phase 1

## KB-010 — `run-single.sh` claims `LEVEL=verbose` env var enables verbose filter; real var is `CODEX_FILTER_LEVEL`

- **Fixture:** `baseline/runners/run-single-level-env-no-effect.stdout`
- **Current behavior:** `LEVEL` env is ignored; `CODEX_FILTER_LEVEL` is exported by run-single before piping to `codex-json-filter.sh`; the flag `--filter-level minimal|normal|verbose` is the user-facing knob
- **Documented behavior:** doc claims "Use `LEVEL=verbose` env" — this is fictional
- **Decision:** doc regeneration
- **Phase:** Phase 4 (with Phase 1 adding the ledger-warn shim that flags `LEVEL` if set)
- **Post-refactor behavior:** doc reflects `--filter-level` flag and `CODEX_FILTER_LEVEL` env; setting `LEVEL` produces a ledger warn
- **Fixture update:** unchanged; new ledger-warn fixture added in Phase 1
