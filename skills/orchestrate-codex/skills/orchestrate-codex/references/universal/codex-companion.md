# codex-companion — runtime correlation surface

> See `references/maintenance/codex-companion.md` for the vendored subtree's library tour, dispatcher rationale, and "why we don't drive review/exec/batch through codex-companion".

`scripts/codex-cc/codex-companion.mjs` is the vendored upstream dispatcher for `openai/codex-plugin-cc`. The skill keeps the subtree primarily for install-independent state helpers and rescue forensics. **The skill does NOT use `codex-companion task --background` for any of its modes** — every runtime path (exec / batch / single / review) calls `codex exec` directly via the bash runners. Rescue is the one runtime mode that touches codex-companion at all, and only for **forensic correlation** with codex's app-server job records.

This document covers the runtime correlation surface. If you are running rescue mode, this is what you need.

## Contents

- Rescue correlation
- Correlating manifest entries with codex-companion job records
- Forensics

## Rescue correlation

`rescue-detect.py` mirrors `state.mjs` in Python, locates the codex-companion state directory, and reads `jobs/*.json` directly when those records exist. If records are gone, rescue falls back to manifest status, logs, answers, worktrees, and exit codes.

For single-mode rescue, the forensic call is:

```bash
node <skill-root>/scripts/codex-cc/codex-companion.mjs task-resume-candidate --json --cwd <workspace-root>
```

Status: `rescue-detect.py` reads codex-companion job records under `<plugin-data>/state/<slug>-<hash>/jobs/<id>.json` for forensic correlation. For single-mode rescue, the dispatcher reads `entry.codex_thread_id` directly from the manifest and threads it into `run-single.sh` as `--resume-thread <id>` (orchestrate-codex.mjs:2210-2218; run-single.sh resume case). The runner translates this into `codex exec resume <id>` — context preserved without going through `task-resume-candidate`. The companion's `task-resume-candidate` surface remains forensic-only: read it via `node <skill-root>/scripts/codex-cc/codex-companion.mjs task-resume-candidate --json --cwd <workspace-root>` to enumerate resumable threads when the manifest lacks a `codex_thread_id` (e.g. hand-rolled manifests, runner crashed before capturing thread.started).

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
