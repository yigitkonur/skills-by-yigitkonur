# Rescue mode — resume a partial run

Inspect an existing manifest, classify each entry's true state, then re-spawn an explicit subset through the original mode's runner.

## When rescue triggers

- A prior orchestrate-codex run ended with non-terminal entries.
- The user explicitly invokes rescue: `node orchestrate-codex.mjs rescue [--manifest <path>]`.
- The detection algorithm Q1 fires (manifest exists + resume keyword in prompt).

Rescue never auto-runs from classification. Redispatch requires an explicit `--redo` value.

## Inputs

```
node orchestrate-codex.mjs rescue [--manifest /abs/path/to/manifest.json]
node orchestrate-codex.mjs rescue --manifest /abs/path/to/manifest.json --redo failed
node orchestrate-codex.mjs rescue --manifest /abs/path/to/manifest.json --redo never-started
node orchestrate-codex.mjs rescue --manifest /abs/path/to/manifest.json --redo all-non-done --accept-stale
```

If `--manifest` omitted, the dispatcher resolves from cwd via the universal slug+hash function (matches codex-companion's `resolveStateDir`). If no manifest at the resolved path, rescue refuses with `error.code="no_manifest_found"` and stops.

## Pre-flight

1. Manifest path resolved and parses.
2. `manifest.schema_version <= skill_schema_version`. If newer, refuse with "skill upgrade needed."
3. `manifest.mode` field present and valid (`exec | batch | single | review`).
4. If redispatching `unknown` entries, user passes `--accept-stale`. Older manifests may reference deleted branches, removed files, or codex-companion job records that have aged out (MAX_JOBS=50 prune).
5. Original mode's runner preflight runs at redispatch time.

## Classification flow

`scripts/rescue-detect.py --manifest <path> --json` reads the manifest plus filesystem state plus codex-companion job records under `~/.../jobs/<id>.json`, and classifies each entry into one of:

| Class | Definition |
|---|---|
| `done` | `manifest.status=="done"` AND log file exists AND (answer file non-empty if applicable) AND (worktree committed past baseline if applicable) |
| `failed` | `manifest.status=="failed"` OR `exit_code != 0` OR worktree dirty + no commits + worker pid dead |
| `never_started` | `manifest.status=="queued"` AND no log file AND (no worktree if exec/review) |
| `in_flight` | `manifest.status=="running"` AND worker pid alive AND log file growing in last N ticks |
| `unknown` | Anything else (e.g. `running` but pid gone — codex-companion state pruned past MAX_JOBS=50) |

Output (JSON):
```json
{
  "manifest_path": "...",
  "run_id": "...",
  "mode": "exec",
  "counts": {
    "done": 2,
    "failed": 1,
    "never_started": 1,
    "in_flight": 0,
    "unknown": 0
  },
  "redispatch_options": {
    "failed_only": ["02-config-editor"],
    "never_started_only": ["04-alert-fsm"],
    "all_non_done": ["02-config-editor", "04-alert-fsm"]
  },
  "entries": []
}
```

## Redispatch decision

After classification, the dispatcher emits a JSON envelope with redispatch options embedded. To act, rerun with one explicit bucket:

```bash
node orchestrate-codex.mjs rescue --manifest <path> --redo failed
node orchestrate-codex.mjs rescue --manifest <path> --redo never-started
node orchestrate-codex.mjs rescue --manifest <path> --redo all-non-done --accept-stale
```

## Pre-rescue cleanup

For each entry the user chose to redo, the runner does:

1. **`in_flight` with stale pid.** `kill -TERM <pid>`; wait; `kill -KILL` if alive; mark entry `last_error="killed_by_rescue"`.
2. **Stale worktree (exec/review mode).** If `worktree_path` exists in manifest but `git worktree list` doesn't show it: `git worktree prune`; recreate via `setup-worktree.sh`.
3. **Dirty worktree (exec/review mode).** `git -C <wt> stash --include-untracked`; record stash ref into `manifest.entries[i].mode_state.pre_rescue_stash`. Do NOT abandon work silently.
4. **Stale partial answer (batch mode).** `rm -f answers/<slug>.partial` or any `<slug>.tmp`. Skip-existing guard reads `answers/<slug>.md` (the canonical path), so partials shouldn't matter, but clean for hygiene.
5. **Stale codex thread.** If `codex_thread_id` is present, the rescue can pass it to `codex exec resume <id>` for single-mode entries. For exec/batch/review, start fresh (no resume).

After cleanup, flip the entry to `queued`, clear `started_at` / `finished_at` / `exit_code` / `last_error`, and append a history row. The runner increments `attempts` when the new attempt starts.

## Re-spawn

Rescue does not re-implement the runners. It dispatches the original mode's runner with the chosen subset of entries marked `queued`. Skip-existing guards do the rest:

- exec mode: `bash run-fleet.sh --manifest <path> --only <ids>`.
- batch mode: `bash run-batch.sh --manifest <path> --only <ids>` with the manifest's prompt/answer/log dirs.
- single mode: re-spawns the one selected entry via `run-single.sh`.
- review mode: `bash run-review.sh --manifest <path> --only <ids>`.

The user's chosen subset's entries are flipped to `queued` first; everything else stays as-is.

## Edge cases

| Case | Handling |
|---|---|
| Manifest schema_version newer than skill | Refuse; surface "upgrade skill before resuming." |
| `manifest.mode == "rescue"` | Refuse; rescue-of-rescue is not a thing. The original mode is what we resume. |
| All entries are `done` | Print "nothing to rescue" and exit cleanly. Manifest can be tidied. |
| All entries are `unknown` | Surface; the codex-companion state aged out. Rescue can still try (filesystem signals only) but warn the user the context is limited. |
| Manifest references a worktree path that no longer exists AND no stash recorded | Treat as `never_started` for that entry; recreate via setup-worktree.sh on dispatch. |
| Manifest references a branch that no longer exists locally OR remotely | Surface; ask user to recreate the branch from `codex_thread_id` (if present) or to skip the entry. |
| Manifest is older than 7 days | Surface freshness warning; user passes `--accept-stale` to proceed. Old manifests may reference deleted branches, ignored issues, or aged-out codex-companion state. |
| User chose "redo all non-done" but `unknown` entries exist | Treat `unknown` as `failed` for redispatch purposes. Log the assumption in history. |
| The original mode is not implemented in this skill version | Refuse; surface the manifest's mode field and the supported modes. Skill upgrade or downgrade needed. |

## Success gate

Rescue inherits the original mode's success gate:
- exec / batch / single: every chosen entry reaches a terminal status (`done` or `failed`); the original cleanup runs.
- review: every chosen branch reaches a terminal state (`converged` / `cap_reached` / `blocked` / `failed`).

## Recovery

If rescue itself fails (the dispatcher crashes, the runner crashes mid-redispatch):
1. The manifest is preserved. Rescue is restartable.
2. `audit-fleet-state.py --manifest <path>` shows the current entry-by-entry truth.
3. Re-invoke rescue. The freshly-re-classified entries reflect any progress made before the crash.

Full failure taxonomy: `references/universal/failure-modes.md`.

## Anti-patterns

- Auto-rescue. Always confirm with the user.
- Silent overwrite of `done` entries. Skip-existing protects them; never bypass.
- Abandoning a dirty worktree without stashing. Stash and surface the stash ref so the user can `git stash pop` if they want to recover.
- Resuming a manifest from a different machine. Manifest paths are local; rescue is local-only by design.
- Hand-editing the manifest to "fix" rescue's classification. Use `manifest-update.py` if you must, but inspect with `audit-fleet-state.py` first.
