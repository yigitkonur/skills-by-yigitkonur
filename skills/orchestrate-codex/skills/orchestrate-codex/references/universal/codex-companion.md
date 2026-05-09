# codex-companion — the vendored OpenAI dispatcher

`scripts/codex-cc/codex-companion.mjs` is the vendored upstream dispatcher for `openai/codex-plugin-cc`. The skill keeps the subtree for install-independent state helpers and rescue forensics. **The skill does NOT use `codex-companion task --background` for any of its modes.** All four modes (exec / batch / single / review) call `codex exec` (or `codex exec review`) directly via the bash runners (`scripts/run-fleet.sh`, `run-batch.sh`, `run-single.sh`, `run-review.sh`). The hot path imports `lib/args.mjs`, `lib/state.mjs`, and `lib/workspace.mjs`; rescue reads the colocated `state.json` and `jobs/` records when present. The `task --background` surface exists in the vendored tree but is not on the skill's hot path.

The vendored `codex-companion.mjs` is invoked by the skill in exactly **one** place: `task-resume-candidate` for rescue-mode correlation with codex's app-server job records. (Even that path is partially wired: `rescue-detect.py` reads codex-companion job records, but the dispatcher's `handleRescue` does not yet drive `codex exec resume` based on them — see C1/C9 derailments and `references/universal/failure-modes.md`.)

The reason for routing exec/batch/single/review through `codex exec` directly rather than `codex-companion task`: we need the `codex exec --json` JSONL stream for Monitor-friendly observability. `codex-companion task --background` returns a `jobId` and requires `status` polling — that's the wrong primitive for a Monitor-driven skill.

## Subcommands and which we use

`codex-companion.mjs <subcommand> [args]`:

| Subcommand | Skill use? | Notes |
|---|---|---|
| `setup` | no | Plugin auth bootstrap; the user runs `codex login` directly. |
| `task [--background] [...]` | no | App-server RPC path. We use `codex exec` directly. |
| `task-worker` | no | Internal; spawned by `task --background`. Not invoked directly. |
| `task-resume-candidate` | no | Available in the vendored tool, but current rescue reads manifest/filesystem/job records directly. |
| `status [--wait] [--json]` | no | Polls the app-server for in-flight task status. We poll the manifest. |
| `result <jobId>` | no | Returns the result envelope of a completed task. We don't have task ids in our flow. |
| `cancel <jobId>` | no | Kills a background task. We use `kill -TERM <pid>` from the manifest. |
| `review` | no | App-server review surface. We use native `codex exec review`. |
| `adversarial-review` | no | Same; out of scope for this skill. |

## Rescue correlation

`rescue-detect.py` mirrors `state.mjs` in Python, locates the codex-companion state directory, and reads `jobs/*.json` directly when those records exist. If records are gone, rescue falls back to manifest status, logs, answers, worktrees, and exit codes.

For single-mode rescue, the forensic call is:

```bash
node <skill-root>/scripts/codex-cc/codex-companion.mjs task-resume-candidate --json --cwd <workspace-root>
```

Status: `rescue-detect.py` reads codex-companion job records under `<plugin-data>/state/<slug>-<hash>/jobs/<id>.json` for forensic correlation. The dispatcher's `handleRescue` does not yet invoke `task-resume-candidate` to drive a re-spawn (C1/C9 derailments verified rescue is half-implemented as of 2026-05-08). Until the gap is closed, `task-resume-candidate` is a forensic-only surface for the skill — operators who need a context-preserving resume must call `codex exec resume <id>` themselves.

Output is a JSON list of resumable thread descriptors:

```json
[
  {
    "thread_id": "019e0a7e-...",
    "started_at": "2026-05-08T18:21:01Z",
    "last_message_at": "2026-05-08T18:25:11Z",
    "summary": "<first agent_message text>"
  }
]
```

The classifier uses this to enrich `unknown` entries (where the manifest's `codex_thread_id` field is missing or stale). For exec / batch / review, the manifest's own `codex_thread_id` is the source of truth — captured from the JSONL stream's `thread.started` event during the original run.

## Lib modules the dispatcher imports

The skill's `orchestrate-codex.mjs` (the top-level dispatcher) imports three modules from the vendored tree:

| Import | Purpose |
|---|---|
| `codex-cc/lib/args.mjs:parseArgs` | argv parser (kebab-case flags + positionals + `--`) |
| `codex-cc/lib/state.mjs:resolveStateDir(cwd)` | workspace slug+hash function (matches codex-companion's path layout) |
| `codex-cc/lib/workspace.mjs:resolveWorkspaceRoot(cwd)` | git-root finder, falls back to cwd |

Replicating these by hand would drift from upstream over time; importing keeps us aligned. See `references/universal/upstream-codex-cc.md` for update procedures.

## Lib modules the bash runners use indirectly

The bash runners do NOT import from `lib/*`. They:
- Source `codex-flags.sh` for the universal flag set.
- Call `codex exec` directly.
- Call `python3 manifest-update.py` for atomic manifest mutations (which is also stdlib-only and computes the slug+hash itself).

The `lib/*` modules exist in the vendored tree because (a) `codex-companion.mjs` needs them at runtime and (b) the dispatcher imports a few. We don't selectively-vendor.

## Correlating manifest entries with codex-companion job records

When `${CLAUDE_PLUGIN_DATA}` is set consistently (which `bootstrap.sh` ensures), our manifest sits at:

```
<plugin-data>/state/<slug>-<hash>/orchestrate-codex/manifest.json
```

And codex-companion's job records sit at:

```
<plugin-data>/state/<slug>-<hash>/state.json     # job index, MAX_JOBS=50
<plugin-data>/state/<slug>-<hash>/jobs/<id>.json # per-job records
```

Same `<slug>-<hash>` directory, different subpaths. Rescue's `rescue-detect.py` reads both:
- Per manifest entry, look up `mode_state.codex_companion_job_id` (or fall back to `codex_thread_id`).
- Find the matching `jobs/<id>.json` record.
- Read its `pid`, `status`, `updatedAt` to enrich the classification.

When the job record is gone (codex-companion pruned past `MAX_JOBS=50`), the entry is classified `unknown` with a "limited rescue context" note.

## Why we don't drive review through codex-companion

`codex-companion review` and `codex-companion adversarial-review` work via the codex app-server RPC. They produce structured findings via the upstream's review schema. They're powerful but:
- They require the app-server / broker lifecycle (spawn, register, teardown) — extra moving parts.
- They don't return JSONL events suitable for our Monitor filter.
- Native `codex exec review` (added in codex-cli 0.121+) covers our use case with simpler observability.

Review mode uses `codex exec review` directly via `run-review.sh`. The codex-companion review path is preserved in the vendored tree but not invoked by the skill's runners.

## Why we don't drive exec/batch through codex-companion `task`

`codex-companion task --background` enqueues a job, spawns a `task-worker` child, and returns a `jobId`. Status is polled via `status --wait`. It's the right primitive for "kick off a task and forget it" — but the skill needs Monitor-streamable JSONL events as they happen, which `codex exec --json` provides directly.

The skill's runners use `codex exec` and tee the JSONL stream to disk. Monitor tails the stream. The codex-companion task surface is preserved (and could be the right primitive for a future async-rescue mode), but isn't on the hot path today.

## Anti-patterns

- Calling `codex-companion task --background` from a runner. The skill expects JSONL streams; you'd lose them.
- Passing the bypass flag through `codex-companion`. The companion's defaults are now `danger-full-access` (per our patch), but downstream `codex exec` from the worker may not inherit it. The bash runners explicitly pass `CODEX_FLAGS` to every `codex exec`.
- Running `codex-companion review` and parsing its output instead of `codex exec review --json`. The structured output may differ between codex-cli versions; the JSONL stream is more stable.
- Modifying `lib/codex.mjs` outside `codex.mjs.patch`. Drift from upstream becomes invisible.

## Forensics

If rescue-detect.py is producing surprising classifications:

```bash
# What does codex-companion think is resumable?
node <skill-root>/scripts/codex-cc/codex-companion.mjs task-resume-candidate --json --cwd <workspace>

# What's in the codex-companion state?
cat <plugin-data>/state/<slug>-<hash>/state.json | jq '.jobs[]'

# Are there orphan job records?
ls <plugin-data>/state/<slug>-<hash>/jobs/
```

If the job records reference a thread that's no longer running but `state.json` still lists it as `running`, codex-companion's pruning didn't run. Manually update via:

```bash
# This is rare; usually the codex-companion lifecycle handles it.
node <skill-root>/scripts/codex-cc/codex-companion.mjs status --wait --json --jobId <stale-id>
```
