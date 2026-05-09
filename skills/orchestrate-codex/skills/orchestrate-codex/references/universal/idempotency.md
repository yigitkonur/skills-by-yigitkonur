# Idempotency

Re-running a runner against the same manifest skips entries that are already `done` and redoes only `queued` or `failed`. This makes every run safely re-runnable: rescue is cheap, partial runs are cheap, retries are cheap.

## Skip-existing guards by mode

| Mode | Guard | Where |
|---|---|---|
| exec | `manifest.entries[i].status == "done"` AND worktree has commits past baseline | `run-fleet.sh` `run_one()` |
| batch | `manifest.entries[i].status == "done"` AND `[ -s answers/<slug>.md ]` | `run-batch.sh` `run_one()` |
| single | one entry; `done` short-circuits | `run-single.sh` |
| review | `manifest.entries[i].mode_state.terminal_state` is set | `run-review.sh` |
| rescue | inherits original mode | dispatcher |

The guards short-circuit before any codex spawn. The runner emits `SKIP <slug>` and moves on.

## Why filesystem AND manifest

Two sources of truth seems redundant; it isn't. Each catches a different failure mode:

- **Manifest only**: if the manifest says `done` but the answer file is gone (user deleted it manually, disk full mid-write), the entry is silently lost. Re-running with a manifest-only check skips the lost entry.
- **Filesystem only**: if the file exists but is corrupt (e.g. `mv` interrupted mid-rename), the entry is silently broken. Re-running skips on file presence and the bad output stays.
- **Both**: the runner checks both. Discrepancy → audit. Manifest says `done` but file gone → rescue redispatch (no silent loss). File exists but manifest says `failed` → audit shows the drift.

## Atomic answer move (batch mode)

The pattern that makes batch mode robust:

```bash
tmp=$(mktemp -t answers-$slug.XXXXXX)
codex exec ... -o "$tmp" ...
if [ "$exit" = 0 ] && [ -s "$tmp" ]; then
    mv -f "$tmp" "answers/$slug.md"
else
    rm -f "$tmp"
fi
```

Properties:
- Crashed codex never leaves a half-written `answers/<slug>.md`. The temp file is in a separate path; only after success does it become the answer.
- Re-running over the same workdir picks up where it left off; the partially-written temp from the previous run is gone (rm at start of next attempt) or has been renamed (success).
- `mv -f` is atomic on the same filesystem (POSIX `rename(2)`).

## Force-redo per entry

Sometimes the entry is `done` but the user wants a different output (different prompt, different model, codex non-determinism produced a worse result the first time):

```bash
# Archive the existing answer.
mkdir -p answers/.prev
mv answers/<slug>.md answers/.prev/

# Mark the entry queued for redispatch.
python3 manifest-update.py --manifest <path> --entry <slug> --set 'status=queued' --set 'attempts=0'

# Re-run.
node orchestrate-codex.mjs <mode> ... # the runner picks up the queued entry
```

There is no mode-level `--force-redo` shortcut. Use rescue `--redo ...` for failed/never-started/non-done entries, or use the manifest helper intentionally after archiving prior answers.

**Never delete `answers/.prev/`** until the new answer is verified. Codex non-determinism means a retry can produce a smaller (or larger but worse) output than the original.

## Redo all

For completed entries, archive existing outputs, flip selected entries with `manifest-update`, and rerun the original mode. For non-done entries, prefer `rescue --redo all-non-done`.

## Idempotency under concurrent writes

Two runner workers should never operate on the same entry. The skip-existing guard reads the manifest at job-start; if entry status flips between two workers' reads, one of them does duplicate work — but the atomic answer move prevents corruption (only the first to write wins; the second's temp gets clobbered by `mv -f`).

The dispatcher guards against this at a higher level: it refuses concurrent runs against the same manifest (`error.code="concurrent_run_in_progress"`).

## Filesystem keying vs content hashing

The skill keys on filename (the slug), not content hash. Pros:
- Simple. Filename collisions are caught at render time, not runtime.
- Audit-friendly. `ls answers/` tells the whole story.
- No hash computation overhead.

Cons:
- A user who renames a slug between runs gets a duplicate answer. (Not an issue if slugs are deterministic from inputs.)
- A user who edits an existing answer file confuses the next run's skip-existing check (the file is non-empty so it's skipped, but it's not the "done" version codex produced).

For batch mode, the slug is derived deterministically from the input via `render-prompts.sh`. As long as the user doesn't hand-edit slug derivation, content-hash keying offers no real benefit.

For exec mode, the entry id is user-provided in `tasks.json`; collision avoidance is the user's responsibility.

## Dispatcher refusal

If a manifest exists with non-terminal entries (`queued | running`), the dispatcher refuses to start a new run:

```json
{"ok": false, "command": "exec", "error": {"code": "concurrent_run_in_progress", "inflight_count": 3, "inflight_ids": ["01-foo", "02-bar", "03-baz"]}}
```

Exit code 3. The user has options:
- Wait for the running run to finish.
- Run rescue mode (which is allowed against an active manifest — rescue's classification handles in-flight entries).
- Tidy the completed run, then start a new run.

Starting a new run on an active manifest is intentionally unsupported; the runners would race on per-entry state.

## Anti-patterns

- Bypassing the skip guard by deleting the manifest. The answer files are still there; the new run will produce N more answers. Archive prior outputs and intentionally requeue instead.
- Hand-editing `manifest.json` to flip an entry's status. Use `manifest-update.py` so the history records the flip.
- Treating "done" as eternal. If the input changes, archive the prior output and intentionally requeue the entry.
- Auto-retrying inside the runner. The runner does not retry. Rescue is operator-confirmed.
- Multiple runners over the same manifest. The dispatcher refuses concurrent runs; bypassing the dispatcher is unsafe.

## Forensics

If a re-run skipped entries that should have been redone:

```bash
# What does the manifest say?
jq '.entries[] | {id, status, attempts}' <manifest>

# Are the answer files matching the manifest?
for slug in $(jq -r '.entries[].slug' <manifest>); do
    if [ -s "answers/$slug.md" ]; then echo "FILE: $slug"; fi
done

# Compare manifest claim vs filesystem reality.
python3 audit-fleet-state.py --manifest <path> --json | jq '.drift'
```

Drift detected → use `manifest-update.py` to flip the affected entries to `failed`, then rescue.
