# Rescue mode — resume a partial run

Inspect an existing manifest, classify each entry's true state, then re-spawn an explicit subset through the original mode's runner.

## What rescue actually does today

Two distinct behaviors based on whether `--apply` is passed (`handleRescue` in `scripts/orchestrate-codex.mjs:1879-2120`):

- **Default (no `--apply`) — read-only classify.** Reads the manifest, runs `rescue-detect.py` (or a fallback bucket count), and emits an envelope whose `next_action` is a structured `ask_user_question` object describing the three redispatch buckets. It does NOT mutate the manifest, kill processes, stash worktrees, or spawn anything.
- **`rescue --apply <subset>` — redispatch.** After classify, runs pre-rescue cleanup (kill stale pids, stash dirty worktrees, prune temp partials), flips the chosen entries to `queued` (clearing `started_at`/`finished_at`/`exit_code`/`last_error`, incrementing `attempts`), then spawns the original mode's runner detached on the selected subset. The runner's skip-existing guards leave `done` entries alone; only the freshly-`queued` ones run.

Subsets accepted by `--apply`: `failed-only` | `never-started-only` | `all-non-done` | `ids:s1,s2,...`. The CLI also accepts `--redo {failed,never-started,all-non-done}` as an alias — it normalizes into `--apply` (`orchestrate-codex.mjs:1889-1906`). `--apply` is the canonical form (matches the envelope's `rerun_with` template).

`ids:s1,s2,s3` is by-name regardless of status. The status filters (`failed-only` / `never-started-only` / `all-non-done`) apply only to the named-subset variants. A `done` entry named in `ids:` will be flipped to `queued` and redispatched (operator-override semantics) — use this when you intentionally want to re-run an already-successful entry without archiving its answer through `--force-redo` first.

## When rescue triggers

- A prior orchestrate-codex run ended with non-terminal entries.
- The user explicitly invokes rescue: `node orchestrate-codex.mjs rescue [--manifest <path>]`.
- The detection algorithm Q1 fires (manifest exists + resume keyword in prompt).

Rescue never auto-runs redispatch from classification. Redispatch requires an explicit `--apply <subset>` (or its `--redo` alias).

## Inputs

```
node orchestrate-codex.mjs rescue [--manifest /abs/path/to/manifest.json]
node orchestrate-codex.mjs rescue --manifest /abs/path/to/manifest.json --apply failed-only
node orchestrate-codex.mjs rescue --manifest /abs/path/to/manifest.json --apply never-started-only
node orchestrate-codex.mjs rescue --manifest /abs/path/to/manifest.json --apply all-non-done --accept-stale
node orchestrate-codex.mjs rescue --manifest /abs/path/to/manifest.json --apply ids:02-config-editor,04-alert-fsm
```

If `--manifest` omitted, the dispatcher resolves from cwd via the universal slug+hash function (matches codex-companion's `resolveStateDir`). If no manifest at the resolved path, rescue refuses with `error.code="manifest_not_found"` and stops.

### Finding the manifest when you don't remember the cwd

The manifest path is derived from `realpath(cwd)` + sha256 — without the original cwd, the dispatcher cannot reconstruct it. To enumerate every manifest on disk under both fallback roots:

```bash
# Both possible roots (CLAUDE_PLUGIN_DATA env var wins if set; otherwise TMPDIR/codex-companion).
find "${CLAUDE_PLUGIN_DATA:-/nonexistent}/state" "${TMPDIR:-/tmp}/codex-companion" \
    -type f -name manifest.json 2>/dev/null
```

Each match lives at `<state-root>/<slug>-<sha256-prefix>/orchestrate-codex/manifest.json`. The `<slug>` is the basename of the original workspace root, so you can usually identify the project by reading the directory name. Pass the chosen path to `--manifest <abs-path>` directly — bypasses the cwd-based resolver.

Within a single state dir, `--force-new-run --run-id <custom>` writes `manifest.<custom>.json` siblings of the canonical `manifest.json`. Rescue and audit always resolve the canonical name; they do NOT enumerate siblings. Adjust the find above to `\( -name 'manifest.json' -o -name 'manifest.*.json' \)` to surface all sibling runs. See `references/universal/idempotency.md` (Enumerating manifest siblings) for the canonical recipe.

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

After classification (the no-`--apply` invocation), the dispatcher emits a JSON envelope with the classification and redispatch options embedded. The envelope's `next_action` is a structured `ask_user_question` object — the orchestrator should surface a 3-option `AskUserQuestion` to the user. To act on the user's choice, rerun with one explicit bucket:

```bash
node orchestrate-codex.mjs rescue --manifest <path> --apply failed-only
node orchestrate-codex.mjs rescue --manifest <path> --apply never-started-only
node orchestrate-codex.mjs rescue --manifest <path> --apply all-non-done --accept-stale
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

## Pre-rescue cleanup (wired today)

When invoked with `--apply`, `handleRescue` runs `preRescueCleanup` against the selected entries before flipping them to `queued`. The cleanup behavior:

1. **`in_flight` with stale pid.** `kill -TERM <pid>`; wait; `kill -KILL` if alive; mark entry `last_error="killed_by_rescue"`.
2. **Stale worktree (exec/review mode).** If `worktree_path` exists in manifest but `git worktree list` doesn't show it: `git worktree prune`; the runner recreates via `setup-worktree.sh` on the next round.
3. **Dirty worktree (exec/review mode).** `git -C <wt> stash --include-untracked`; record stash ref into `manifest.entries[i].mode_state.pre_rescue_stash`. Work is never abandoned silently.
4. **Stale partial answer (batch mode).** `rm -f answers/.<slug>.partial`. The runner writes its in-flight temp file at `answers/.<slug>.partial` (leading dot — see `run-batch.sh`); the canonical answer path is `answers/<slug>.md`. Partials are atomic-renamed away on success, so they only linger after a crash.
5. **Stale codex thread.** If `codex_thread_id` is present, rescue passes it to `codex exec resume <id>` for single-mode entries (default behavior; override with `mode_state.single.resume_thread`). For exec/batch/review, start fresh (no resume).

After cleanup, rescue flips each chosen entry to `queued`, increments `attempts`, clears `started_at` / `finished_at` / `exit_code` / `last_error`, and appends a history row for the cleanup + flip. The envelope's `cleanup` field reports what was done.

### Manual workaround (only if you really want to skip `--apply`)

If you have a reason to do the cleanup + flip + spawn yourself instead of relying on `--apply`:

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

# 6. Re-invoke the original mode's runner manually (see "Re-spawn" below).
```

In practice, `--apply <subset>` is the supported path; the manual sequence above is for emergencies (e.g. cleanup is failing and you want to do steps by hand to find out why).

## Re-spawn (wired today)

When invoked with `--apply`, after pre-rescue cleanup and the queued-flip, `handleRescue` spawns the original mode's runner detached, with mode-appropriate args/env (`orchestrate-codex.mjs:2038-2101`). The skip-existing guards in each runner leave `done` entries alone; only the freshly-`queued` ones run.

If you've taken the manual workaround above, you re-invoke the runner yourself:

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
| User chose `all-non-done` but `unknown` entries exist | Treat `unknown` as `failed` for redispatch purposes. Log the assumption in history. |
| The original mode is not implemented in this skill version | Refuse; surface the manifest's mode field and the supported modes. Skill upgrade or downgrade needed. |

## Success gate

Two gates depending on invocation:

- **Classify-only (no `--apply`).** Success = classifier exited 0 and the envelope was emitted with a structured `ask_user_question` next-action. The user's pick (or decline) closes the round.
- **Redispatch (`--apply <subset>`).** Rescue inherits the original mode's success gate after spawning the runner:
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
