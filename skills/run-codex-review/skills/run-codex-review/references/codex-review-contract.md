# Codex Review Contract

`/codex:review --background` is the per-branch reviewer in this skill. This file is the **single pinned spec** for how the skill calls it, parses it, and decides "no major feedback".

## Invocation forms

Two forms exist; both must run **inside the branch's worktree** so Codex sees the right HEAD:

1. **Slash command** (interactive Claude Code session):
   ```
   /codex:review --background
   ```

2. **Underlying CLI** (programmatic; what scripts call):
   ```bash
   codex review --background [--branch <b>] [--base main]
   ```

`scripts/run-codex-review.py` calls the CLI form. If the CLI signature in your environment differs, adjust `run-codex-review.py`'s `invoke_codex()` function — keep the rest of this contract identical.

## Background-job lifecycle

```
launch  →  capture job id  →  poll  →  complete  →  fetch artifact  →  normalize JSON
```

1. Launch returns a job id on stdout (e.g. `cdx-job-abc123`). Capture it; persist in manifest as `last_review_id`.
2. Poll the job's status endpoint at `--poll-interval` (default 30s). Codex reports `running` / `completed` / `failed`.
3. On `completed`, fetch the artifact (file path / API call / `gh` PR comment — depends on your Codex install).
4. Normalize the artifact to the JSON schema below. Persist to `<rounds-dir>/<branch-slug>.<round>.json`.

If the job is still `running` after `--timeout` (default 1800s = 30 min), the wrapper marks the round `timeout` and returns exit 1; the subagent decides whether to retry the round (caps at 3 attempts).

## Normalized JSON schema

Every round emits one file. Schema:

```json
{
  "review_id": "cdx-job-abc123",
  "branch": "feat/foo",
  "head_sha": "deadbeef1234...",
  "started_at": "2026-04-26T10:00:00Z",
  "finished_at": "2026-04-26T10:04:32Z",
  "raw_text": "<full Codex output verbatim>",
  "items": [
    {
      "id": "cdx-1",
      "severity_raw": "high",
      "file": "src/foo.ts",
      "line": 42,
      "body": "Off-by-one in the slice — drops the last element."
    }
  ]
}
```

`severity_raw` is whatever Codex emits (`high|medium|low`, `error|warning|info`, etc.). The classifier (`classify-review-feedback.py`) maps it onto major/minor per `major-vs-minor-policy.md`. Don't pre-classify here — keep the wrapper's normalization mechanical.

If Codex's artifact is unstructured (free-text), `items` is `[]` and the classifier falls back to regex over `raw_text`. Mark `severity_raw: "unstructured"` in this case.

## Detecting "no major feedback"

The subagent decides DONE-vs-continue from the classifier's output, not from the raw artifact:

```bash
python3 scripts/classify-review-feedback.py --review-json <round-json>
```

Exit code:
- `0` = at least one major item → **continue the loop**.
- `1` = no major items (only minor / unclassified-but-no-major triggers) → **mark branch DONE**.
- `2` = parse failure → mark round `failed`, retry once (caps at 3).

Never decide DONE by eyeballing the raw text. The classifier is the single arbiter so the loop terminates the same way every time.

## Always `--background`

`--background` is non-negotiable. Inline mode blocks the subagent:

| Mode | Effect |
|---|---|
| `--background` | Codex runs out-of-band. Subagent polls; can do other work in between. Per-branch parallelism works. |
| inline | Subagent blocks until Codex returns. Other branches stall waiting. Defeats the whole skill. |

If the user/environment disables `--background` mode, this skill cannot run as designed — fall back to `run-repo-cleanup` for serial cleanup.

## Failure modes and what the wrapper does

| Failure | Wrapper behavior | Caller (subagent) action |
|---|---|---|
| codex CLI not installed | Exit 2 with stderr "codex not on PATH" | Cannot proceed; mark branch FAILED. |
| Network failure mid-launch | Exit 2 with raw error in stderr | Retry round (max 3); else FAILED. |
| Job stuck `running` past timeout | Exit 1; manifest marked `timeout` | Retry round (max 3); else FAILED. |
| Job `completed` but artifact missing | Exit 2 with stderr explaining where it looked | Cannot recover; mark FAILED. |
| Artifact present but malformed | Normalization writes `items: []`, `severity_raw: "unstructured"`; exit 0 | Classifier falls back to regex; loop continues normally. |
| Branch HEAD changed mid-review (someone else pushed) | Wrapper warns; review may be stale | Discard the round, retry from current HEAD. |

## Read-only invariants

`run-codex-review.py` itself is **mostly** read-only with respect to the repo — its only writes are the round-log file under `<rounds-dir>` and the manifest update. It does **not** push, commit, or modify the worktree. Pushing is the subagent's job after applying fixes.

## Adjusting the contract

If your Codex installation deviates from the schema above:

1. Edit `scripts/run-codex-review.py`'s `normalize_review()` function to match Codex's actual output.
2. Update this doc's Schema section in lock-step.
3. Run `scripts/classify-review-feedback.py` against a sample normalized JSON to confirm the classifier still partitions correctly.

Don't let the contract drift silently. The schema in this file is what the rest of the skill assumes.
