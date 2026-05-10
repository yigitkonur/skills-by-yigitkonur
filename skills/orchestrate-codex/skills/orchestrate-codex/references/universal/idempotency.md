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

Sometimes the entry is `done` but the user wants a different output (different prompt, different model, codex non-determinism produced a worse result the first time). Today this is a manual three-step workflow:

```bash
# 1. Archive the existing answer.
mkdir -p answers/.prev
mv answers/<slug>.md answers/.prev/

# 2. Mark the entry queued for redispatch (note the --execute; default is dry-run).
python3 scripts/manifest-update.py entry --manifest <path> --entry <slug> \
    --set status=queued --set attempts=0 --execute

# 3. Re-run. The runner picks up the queued entry on its next pass.
node scripts/orchestrate-codex.mjs <mode> ...
```

**Implemented.** A dispatcher convenience flag `--force-redo <slug>[,<slug2>,...]` is wired in `orchestrate-codex.mjs` for `exec` and `batch` modes. It archives the existing answer file (batch) to `<answers>/.prev/<slug>-<ts>.md`, flips the entry's status back to `queued`, and re-spawns the runner.

```bash
# Force re-run of one entry (exec or batch):
node scripts/orchestrate-codex.mjs <mode> --force-redo <slug>

# Force re-run multiple entries (comma-separated; one --force-redo flag):
node scripts/orchestrate-codex.mjs <mode> --force-redo "slug-a,slug-b"

# Force re-run every entry:
node scripts/orchestrate-codex.mjs <mode> --force-redo-all
```

Each `--force-redo` cycle increments `attempts` by 2 (once on the queued-flip in `flipEntryToQueued` at `orchestrate-codex.mjs:1101`, once on runner START in `run-batch.sh:238`). This is a known artifact of the two-phase manifest write — the bookkeeping double-counts but does not affect skip-existing or rescue classification. When auditing `attempts` after one or more force-redos, divide by 2 to get the operator-visible cycle count.

Use `rescue --apply failed-only|never-started-only|all-non-done|ids:...` (canonical) — `rescue --redo {failed,never-started,all-non-done}` is accepted as a back-compat alias and normalized into `--apply` — for the rescue-driven path. The three-step manual workflow above remains valid as a defense-in-depth path when you don't trust the dispatcher to flip status atomically.

**Never delete `answers/.prev/`** until the new answer is verified. Codex non-determinism means a retry can produce a smaller (or larger but worse) output than the original.

## Redo all

**Implemented** for exec and batch modes:

```bash
node scripts/orchestrate-codex.mjs <mode> --force-redo-all
```

Archives every existing answer file (batch) to `<answers>/.prev/<slug>-<ts>.md`, flips every entry to `queued`, and re-spawns the runner. The audit cost is real — surface a confirmation prompt before the operator triggers this.

For non-done entries only, prefer `rescue --apply all-non-done` (canonical; `rescue --redo all-non-done` is the back-compat alias) — wired in the dispatcher and operates against the existing manifest without archiving any answer files.

The fully-manual workflow (still valid as a defense-in-depth path):

```bash
# Archive every answer to answers/.prev/.
mkdir -p answers/.prev && mv answers/*.md answers/.prev/ 2>/dev/null

# Flip every entry back to queued.
for slug in $(jq -r '.entries[].id' <manifest>); do
  python3 scripts/manifest-update.py entry --manifest <manifest> \
      --entry "$slug" --set status=queued --set attempts=0 --execute
done

# Re-run.
node scripts/orchestrate-codex.mjs <mode> ...
```

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
- Pass `--force-new-run --run-id <custom>` to write a sibling manifest (`manifest.<custom-run-id>.json` in the same state directory). **Implemented** in `orchestrate-codex.mjs` for exec/batch/single. The runners would still race on per-entry locks if both runs target overlapping entries; use this only when the new run touches a disjoint task set.

Starting a new run on an active manifest is intentionally gated; the runners would race on per-entry state without `--force-new-run`.

### Enumerating manifest siblings

`audit` and `rescue` resolve the canonical `manifest.json` from the cwd-derived state dir; they do **not** enumerate `manifest.<run-id>.json` siblings. To list every manifest in the active state dir (so an operator who forgot a custom `--run-id` can find it):

```bash
ls "$(node scripts/orchestrate-codex.mjs --resolve-state-dir)/manifest"*.json 2>/dev/null
```

Or, if `--resolve-state-dir` is unavailable, the same enumeration via the universal-fallback paths:

```bash
find "${CLAUDE_PLUGIN_DATA:-/nonexistent}/state" "${TMPDIR:-/tmp}/codex-companion" \
    -type f \( -name 'manifest.json' -o -name 'manifest.*.json' \) 2>/dev/null
```

Pass any chosen sibling to `--manifest <abs-path>` directly. The dispatcher's resolver bypasses cwd-derivation when `--manifest` is explicit.

### Disjoint-slug discipline across siblings

`--force-new-run --run-id <custom>` writes a sibling manifest, but **slug uniqueness is not enforced across siblings**. Two parallel runs with overlapping entry slugs share the same `answers/<slug>.md` and (for exec) the same `<repo>-wt-<mode>-<slug>` worktree path. Both runners then race undetected — the skip-existing guard reads only its own manifest, so each runner believes the entry is queued for it. Last writer wins on the answer file; the loser's commits orphan inside a worktree the surviving manifest no longer references.

The operator MUST keep slug spaces disjoint when running parallel siblings. Practical patterns:

- **Per-bucket prefixes.** `--run-id translate-en` writes entries `translate-en-row-001`, `--run-id translate-es` writes `translate-es-row-001`. The slugs do not collide.
- **Per-bucket `--answers-dir`.** Different output directories make the answer-file race impossible (batch mode); the worktree race remains a concern for exec mode and requires a slug-prefix anyway.
- **Sequential, not parallel.** When in doubt, run siblings back-to-back — the second run starts after the first reaches a terminal manifest state. No race surface.

This is operator discipline. The dispatcher cannot detect overlapping slugs across sibling manifests; it would have to read every manifest under the state dir on every dispatch, which is not how the contract is wired today.

## Anti-patterns

- Bypassing the skip guard by deleting the manifest. The answer files are still there; the new run will produce N more answers. Archive prior outputs (use `--force-redo` / `--force-redo-all`) and intentionally requeue instead.
- Hand-editing `manifest.json` to flip an entry's status. Use `manifest-update.py` so the history records the flip.
- Treating "done" as eternal. If the input changes, archive the prior output and intentionally requeue the entry — `--force-redo <slug>` does it atomically.
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
