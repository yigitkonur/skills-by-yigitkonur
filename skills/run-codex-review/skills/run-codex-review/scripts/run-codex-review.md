# run-codex-review.py

Wrapper around `/codex:review --background` for one branch in one worktree. Launches the background review, polls to completion, fetches the artifact, normalizes to the JSON schema in `references/codex-review-contract.md`, writes the round log, and updates the manifest.

**This is the single entry point for "do one round of review on this branch".** Subagents call it once per round.

## Usage

```bash
python3 scripts/run-codex-review.py --branch feat/foo --worktree /Users/.../wt-feat-foo
python3 scripts/run-codex-review.py --branch feat/foo --worktree /path --base canary
python3 scripts/run-codex-review.py --branch feat/foo --worktree /path --timeout 600
python3 scripts/run-codex-review.py --branch feat/foo --worktree /path --dry-run
```

## Behavior

1. Pre-flight: verify `--worktree` exists and is on `--branch`.
2. `cd` into the worktree.
3. Invoke the codex CLI form (see "Adjustment point" below).
4. Parse the launch output for the background job id.
5. Poll the job status every `--poll-interval` seconds until completion or `--timeout`.
6. On completion: fetch the artifact, normalize to the schema, write `<rounds-dir>/<slug>.<round>.json`.
7. Update the manifest entry's `last_review_id`, `last_review_at`, `last_status`, `rounds`, `head_sha_current`, and append a `round_history` entry.

## Flags

| Flag | Default | Effect |
|---|---|---|
| `--branch <b>` | required | Branch under review. Must match the worktree's HEAD. |
| `--worktree <path>` | required | Worktree directory; codex runs from here. |
| `--base <ref>` | `main` | Base passed to the codex CLI (if it accepts one). |
| `--manifest <path>` | `/tmp/codex-review-manifest.json` | Manifest to update. |
| `--rounds-dir <path>` | `/tmp/codex-review-rounds/` | Round-log directory. |
| `--timeout <n>` | `1800` (30 min) | Seconds to wait for the background job to complete. |
| `--poll-interval <n>` | `30` | Seconds between status polls. |
| `--dry-run` | off | Print the plan; don't invoke codex. |

## Exit codes

| Code | Meaning | Caller (subagent) action |
|---|---|---|
| `0` | Review available; round log written | Run `classify-review-feedback.py` next. |
| `1` | Timeout (manifest marked `timeout`) | Retry the round (max 3); else mark FAILED. |
| `2` | Codex/CLI failed (manifest marked `failed`) | Retry the round (max 3); else mark FAILED. |

## Adjustment point — codex CLI form

The exact CLI form depends on your Codex installation. Edit `invoke_codex()` in the script to match.

Default attempts (in order):

```python
candidates = [
    ["codex", "review", "--background", "--branch", branch, "--base", base],
    ["codex", "review", "--background"],
]
```

If your install uses a different form (e.g. `claude codex review`, `cdx review`, `gh codex`), update the list. The script picks the first form that doesn't return `127` (command not found).

Same for the **status** poll (`codex review --status <id>`) and **fetch** (`codex review --fetch <id>`) — adjust if your install uses different subcommands.

## Schema of the round-log JSON

Per `references/codex-review-contract.md`:

```json
{
  "review_id": "cdx-job-abc123",
  "branch": "feat/foo",
  "head_sha": "deadbeef1234...",
  "started_at": "2026-04-26T10:00:00Z",
  "finished_at": "2026-04-26T10:04:32Z",
  "raw_text": "<full Codex output verbatim>",
  "items": [
    { "id": "...", "severity_raw": "...", "file": "...", "line": 42, "body": "..." }
  ]
}
```

`items` is populated when the artifact is structured JSON. When unstructured (free text), `items` is `[]` and the classifier scans `raw_text` instead.

## Job-id parsing

The script tries these patterns on launch stdout (case-insensitive):

```
\bjob[- ]?id[:=]\s*([A-Za-z0-9_-]+)
\b(cdx[- ]?job[- ]?[A-Za-z0-9_-]+)
\bbackground job[:=]\s*([A-Za-z0-9_-]+)
```

If none match, a synthetic id `cdx-job-unknown-<unix-ts>` is generated and a warning is printed. The synthetic id is still recorded in the manifest so the round-log filename is unique.

## Polling loop

```
status = "running"
while elapsed < timeout:
    rc, out, _ = sh(["codex", "review", "--status", job_id])
    if "completed" in out: status = "completed"; fetch; break
    if "failed" in out:    status = "failed"; break
    sleep(poll_interval)
```

If polling exceeds `--timeout`, the script returns exit 1 with `last_status: "timeout"` in the manifest. The subagent decides whether to retry (max 3 retries per round).

## Concurrency safety

`run-codex-review.py` is invoked **once per round per branch** by exactly **one subagent**. No file-locking is needed for the round-log write (each round-log filename is unique by `slug.round.json`). Manifest updates use `tempfile + os.replace` for atomicity, but the protocol assumes one subagent per branch — concurrent invocations on the same branch are an error.

## Sample output (success)

```
launching /codex:review --background in /Users/.../myrepo-wt-feat-foo ...
  job id: cdx-job-7f8a9c; polling every 30s up to 1800s...
  ✓ round log written: /tmp/codex-review-rounds/feat-foo.03.json
  ✓ manifest updated: rounds=3
```

## Sample output (timeout)

```
launching /codex:review --background in /Users/.../myrepo-wt-feat-foo ...
  job id: cdx-job-7f8a9c; polling every 30s up to 1800s...
✗ job cdx-job-7f8a9c timed out after 1800s
```

(exit 1; manifest `last_status: "timeout"`)

## Failure modes

| Failure | Wrapper behavior | Recovery |
|---|---|---|
| `codex` CLI not on PATH | Exit 2; `last_status: "failed"` | Install codex; resume. |
| Worktree not on the right branch | Exit 2 with stderr; no manifest update | `git -C <wt> checkout <branch>`; retry. |
| Network failure mid-launch | Exit 2; `last_status: "failed"` | Subagent retries (max 3). |
| Job stuck `running` past timeout | Exit 1; `last_status: "timeout"` | Subagent retries OR raises timeout. |
| Job `completed` but no artifact | Exit 2; `last_status: "failed"` | Investigate codex install; surface to human. |
| Artifact malformed JSON | Exit 0; `items: []`, `raw_text` populated | Classifier falls back to regex; loop continues. |
| Branch HEAD changed mid-review | Wrapper warns via raw_text comparison; review may be stale | Subagent discards round, retries from current HEAD. |

## When to run

- Per round, by exactly one subagent per branch.
- Never invoke twice in parallel on the same branch.
- Never invoke from outside the branch's worktree.

## Read/write surface

- **Reads**: `<worktree>/...`, manifest, codex CLI status/fetch endpoints.
- **Writes**: `<rounds-dir>/<slug>.<round>.json` (new each round), manifest entry for this branch.
- **Does NOT**: push, commit, modify the worktree, open PRs, edit other branches' entries.

## Extending

- Replace `invoke_codex()`'s body with your codex CLI form. Keep the return contract `(rc, stdout, stderr)`.
- Replace `parse_job_id()`'s patterns with your codex's launch-output convention.
- Replace `poll_job()`'s status/fetch with your codex's polling contract.
- Add a per-call `--policy <path>` flag if you want to override the classifier policy from this script (currently the classifier is invoked separately).
