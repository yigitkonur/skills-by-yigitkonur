# Rescue mode — resume a partial run

Inspect an existing manifest, classify each entry's true state, then re-spawn an explicit subset through the original mode's runner.

> **Status: read-only classification today.** `handleRescue` (`scripts/orchestrate-codex.mjs`) reads the manifest, runs `rescue-detect.py` (or a fallback bucket count), and emits an envelope describing what's redo-able. It **does not currently re-spawn**, **does not flip entries to `queued`**, and **does not perform pre-rescue cleanup.** The "Pre-rescue cleanup" and "Re-spawn" sections below describe **Planned** behavior; each section also shows the working manual sequence for today.

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
4. Manifest freshness ≤ 7 days OR user passes `--accept-stale`. Older manifests may reference deleted branches, removed files, or codex-companion job records that have aged out (MAX_JOBS=50 prune). Redispatching any `unknown` entry also requires `--accept-stale` regardless of manifest age.
5. Original mode's pre-flight runs at redispatch time. For modes that surface a `codex login status` check (single, batch, review pre-flights describe one), treat it as a soft warning — warn unless `~/.codex/config.toml` declares no `model_provider`, then proceed.

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

After classification, the dispatcher emits a JSON envelope with the classification and redispatch options embedded. The envelope's `next_action` is a structured `ask_user_question` object — the orchestrator should surface a 3-option `AskUserQuestion` to the user. To act on the user's choice, rerun with one explicit bucket:

```bash
node orchestrate-codex.mjs rescue --manifest <path> --redo failed
node orchestrate-codex.mjs rescue --manifest <path> --redo never-started
node orchestrate-codex.mjs rescue --manifest <path> --redo all-non-done --accept-stale
```

Sample question shape:

```
Which subset do you want to redo?
  - Redo failures only (1 entry: 02-config-editor)
  - Redo never-started only (1 entry: 04-alert-fsm)
  - Redo all non-done (2 entries: 02-config-editor, 04-alert-fsm)
```

The orchestrator should always offer a fourth implicit option: **decline** the AskUserQuestion (the user cancels). Don't add a literal "Stop" option to the question itself — the envelope only describes three. If the user wants to stop, they cancel.

Never auto-pick. Rescue is operator-confirmed.

## Pre-rescue cleanup

**Planned — not yet wired.** The current `handleRescue` is read-only and does none of the steps below. They describe the intended future behavior.

1. **`in_flight` with stale pid.** `kill -TERM <pid>`; wait; `kill -KILL` if alive; mark entry `last_error="killed_by_rescue"`.
2. **Stale worktree (exec/review mode).** If `worktree_path` exists in manifest but `git worktree list` doesn't show it: `git worktree prune`; recreate via `setup-worktree.sh`.
3. **Dirty worktree (exec/review mode).** `git -C <wt> stash --include-untracked`; record stash ref into `manifest.entries[i].mode_state.pre_rescue_stash`. Do NOT abandon work silently.
4. **Stale partial answer (batch mode).** `rm -f answers/.<slug>.partial`. The runner writes its in-flight temp file at `answers/.<slug>.partial` (leading dot — see `run-batch.sh`); the canonical answer path is `answers/<slug>.md`. Partials are atomic-renamed away on success, so they only linger after a crash.
5. **Stale codex thread.** If `codex_thread_id` is present, future rescue may pass it to `codex exec resume <id>` for single-mode entries. For exec/batch/review, start fresh (no resume).

After cleanup, the planned behavior is to flip the chosen entries to `queued`, increment `attempts`, clear `started_at` / `finished_at` / `exit_code` / `last_error`, and append a history row for the cleanup + flip. None of this is wired today.

### Manual workaround (today)

```bash
# 1. Inspect what classifier saw.
node orchestrate-codex.mjs rescue --manifest /abs/path/to/manifest.json
# (read the envelope; note which entries are failed / never-started / in-flight.)

# 2. For in-flight with stale pid:
kill -TERM <pid> 2>/dev/null; sleep 2; kill -KILL <pid> 2>/dev/null || true

# 3. For dirty worktrees:
git -C <worktree-path> stash push --include-untracked -m "pre-rescue stash <id>"
bash scripts/manifest-update.sh entry <manifest> <id> \
    "mode_state.pre_rescue_stash=$(git -C <worktree-path> rev-parse stash@{0})"

# 4. For batch-mode partials:
rm -f answers/.<slug>.partial

# 5. Flip chosen entries back to queued so the runner picks them up.
bash scripts/manifest-update.sh entry <manifest> <id> \
    status=queued exit_code= finished_at= last_error=

# 6. Re-invoke the original mode's runner manually.
```

## Re-spawn

**Planned — not yet wired.** The intended behavior is for rescue to dispatch the original mode's runner with the chosen subset of entries marked `queued`, letting the skip-existing guards take care of everything else. Today, after manually flipping entries to `queued`, you re-invoke the runner yourself:

```bash
# exec mode (positional manifest, runner reads JOBS / etc. from env):
bash scripts/run-fleet.sh /abs/path/to/manifest.json

# batch mode (env-var invocation; see batch.md "Standalone runner"):
JOBS=10 PROMPTS=./prompts ANSWERS=./answers LOGS=./logs \
    ORCHESTRATE_MANIFEST=/abs/path/to/manifest.json \
    bash scripts/run-batch.sh

# single mode:
bash scripts/run-single.sh \
    --manifest /abs/path/to/manifest.json \
    --entry-id single \
    --prompt-file <prompt> \
    --cwd <cwd> \
    --out <answer-path>

# review mode (one round at a time; see review.md):
bash scripts/run-review.sh /abs/path/to/manifest.json <round-number>
```

The skip-existing guards in each runner mean entries already at `done` are passed over; only the freshly-`queued` ones run.

## Edge cases

| Case | Handling |
|---|---|
| Manifest schema_version newer than skill | Refuse; surface "upgrade skill before resuming." |
| `manifest.mode == "rescue"` | Refuse; rescue-of-rescue is not a thing. The original mode is what we resume. |
| All entries are `done` | Print "nothing to rescue" and exit cleanly. Manifest can be tidied. |
| All entries are `unknown` | Surface; the codex-companion state aged out. Rescue can still try (filesystem signals only) but warn the user the context is limited. |
| Manifest references a worktree path that no longer exists AND no stash recorded | Treat as `never_started` for that entry; recreate via setup-worktree.sh on dispatch. |
| Manifest references a branch that no longer exists locally OR remotely | Surface; ask user to recreate the branch (from local reflog, from a teammate's fork, from scratch) or to skip the entry. The `codex_thread_id` field is recorded for diagnostic purposes; it does **not** today reconstruct branch state — `codex exec resume` replays the thread but does not regenerate git refs. |
| Manifest is older than 7 days | Surface freshness warning; user passes `--accept-stale` to proceed. Old manifests may reference deleted branches, ignored issues, or aged-out codex-companion state. |
| User chose "redo all non-done" but `unknown` entries exist | Treat `unknown` as `failed` for redispatch purposes. Log the assumption in history. |
| The original mode is not implemented in this skill version | Refuse; surface the manifest's mode field and the supported modes. Skill upgrade or downgrade needed. |

## Success gate

For today's read-only rescue, the success gate is just: classifier exited 0, envelope was emitted, and the user picked a subset (or declined). The actual redispatch — and the inherited per-mode terminal gates below — kick in once you've manually flipped entries and re-invoked the original runner.

Once redispatch is wired (or after manual redispatch), rescue inherits the original mode's success gate:
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
