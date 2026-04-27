# trigger-codex-rescue.py

Phase 6 entry point. After `open-comprehensive-pr.py` (or the PR-Creator sub-agent) opens a PR, this script triggers Codex rescue against it. Codex rescue is **Codex's own background sub-agent**, not a Claude Agent we dispatch — we hand it the PR link, and Codex's infrastructure spawns the review job.

## Usage

```bash
python3 scripts/trigger-codex-rescue.py --pr 42 --branch feat/foo
python3 scripts/trigger-codex-rescue.py --pr 42 --branch feat/foo --model gpt-5.5 --effort xhigh
python3 scripts/trigger-codex-rescue.py --pr 42 --branch feat/foo --dry-run
```

## Behavior

1. Read the manifest entry for `<branch>` to get `worktree_path`.
2. Inside that worktree, invoke the codex rescue CLI:
   ```
   codex review --rescue --background --fresh --model <m> --effort <e> --pr <n>
   ```
3. Capture the rescue job id from stdout (regex patterns; fallback to synthetic).
4. Update the manifest entry with:
   - `rescue_review_id` — the job id
   - `rescue_started_at` — UTC ISO timestamp
   - `rescue_status` — `"running"` (later updated to `"completed"` / `"timeout"` / `"failed"` by `await-pr-reviews.py`)
   - `rescue_pr_number` — for cross-reference
   - `rescue_model` — for audit
   - `rescue_effort` — for audit
5. Return immediately. **Does not poll.** Phase 6's `await-pr-reviews.py` owns the wait.

## Flags

| Flag | Default | Effect |
|---|---|---|
| `--pr <n>` | required | PR number to review. |
| `--branch <b>` | required | Branch name (manifest entry key). |
| `--manifest <path>` | `/tmp/codex-review-manifest.json` | Manifest to update. |
| `--model <m>` | `gpt-5.5` | Codex model (per the user's spec). |
| `--effort <e>` | `xhigh` | Codex effort level (per the user's spec). |
| `--dry-run` | off | Print the plan; no invocation, no manifest write. |

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Rescue triggered; job id parsed; manifest updated. |
| `1` | Rescue triggered but no job id parseable from output; synthetic id used; manifest still updated. Caller may proceed but should be aware. |
| `2` | Codex CLI not found OR codex returned a hard error. Manifest marked `rescue_status: "failed"`. |

## Adjustment point — codex rescue CLI form

The script tries (in order) these forms:

```python
candidates = [
    ["codex", "review", "--rescue", "--background", "--fresh",
     "--model", model, "--effort", effort, "--pr", str(pr)],
    ["codex", "rescue", "--background", "--fresh",
     "--model", model, "--effort", effort, "--pr", str(pr)],
    ["codex", "resc", "--background", "--fresh",
     "--model", model, "--effort", effort, "--pr", str(pr)],
]
```

If your installation uses a different form (e.g. `claude codex resc`, `cdx-rescue`, etc.), edit `invoke_rescue()`'s `candidates` list. The script picks the first form that doesn't return rc=127 (command not found).

## Job-id parsing

The script tries these regex patterns on launch stdout (case-insensitive):

```
\brescue[- ]?job[- ]?id[:=]\s*([A-Za-z0-9_-]+)
\b(cdx[- ]?rescue[- ]?[A-Za-z0-9_-]+)
\bjob[- ]?id[:=]\s*([A-Za-z0-9_-]+)
\bbackground job[:=]\s*([A-Za-z0-9_-]+)
```

If none match, a synthetic id `cdx-rescue-unknown-<unix-ts>` is generated and a warning is printed (exit 1, not 0). The synthetic id is still recorded so subsequent scripts can correlate.

## Why these defaults

- **`--background`** is non-negotiable (per the skill's invariant). Inline mode would block the agent.
- **`--fresh`** clears prior session bias. The rescue is a last check; we want it cold.
- **`--model gpt-5.5`** is the strongest reasoning model available; appropriate for a one-shot rescue.
- **`--effort xhigh`** spends more compute. Acceptable here because rescue is one-shot per PR (not 20 rounds).

## When to run

- **Phase 6**, immediately after the PR-Creator sub-agent reports the PR number/URL.
- One invocation per PR; do not invoke twice for the same PR.

## Safety

- Read-only on git state (no commits, no pushes).
- Writes to manifest only — atomic write via `tempfile + os.replace`.
- Never invokes a Claude Agent — Codex rescue is Codex's own sub-agent, separate process.

## Sample output (success)

```
triggering codex rescue: PR #42 in /Users/.../wt-feat-foo (gpt-5.5, effort=xhigh)...
  ✓ rescue triggered: job id = cdx-rescue-7f8a9c12
  ✓ manifest updated: /tmp/codex-review-manifest.json
```

## Sample output (parse failure but trigger succeeded)

```
triggering codex rescue: PR #42 in /Users/.../wt-feat-foo (gpt-5.5, effort=xhigh)...
⚠  no recognizable rescue job id in launch output; using synthetic: cdx-rescue-unknown-1714138200
  ✓ rescue triggered: job id = cdx-rescue-unknown-1714138200
  ✓ manifest updated: /tmp/codex-review-manifest.json
```

(exit 1 — caller should treat the rescue as triggered but log the parse issue)

## Sample output (codex not installed)

```
✗ codex CLI not found: command not found: codex
```

(exit 2 — manifest marked `rescue_status: "failed"` with the error)

## Failure modes

| Failure | Wrapper behavior | Caller (Phase 6) action |
|---|---|---|
| codex CLI not on PATH | Exit 2; manifest `rescue_status: failed` | Skip rescue stream; await-pr-reviews.py will see no rescue items. |
| Codex hard error (network, auth) | Exit 2; manifest `rescue_status: failed` with error text | Same as above. |
| Job id parse failure | Exit 1; synthetic id; manifest `rescue_status: running` | Proceed; await-pr-reviews.py polls based on PR comments, not job id. |
| Worktree missing | Exit 2; manifest unchanged | Spawn-review-worktrees may have been bypassed; surface for human. |

## Read/write surface

- **Reads**: manifest (initial), worktree path (verifies dir exists), codex CLI stdout/stderr.
- **Writes**: manifest entry for `<branch>` (atomic).
- **Does NOT**: commit, push, modify the worktree, comment on the PR, or dispatch any Claude Agent.

## Extending

- Replace `invoke_rescue()`'s `candidates` with your codex CLI form.
- Replace `parse_rescue_job_id()`'s patterns with your codex output convention.
- Add a `--policy <path>` flag if your codex rescue accepts a policy file (e.g. severity tuning).
- Add a `--prompt <text>` flag to inject extra guidance into the rescue's prompt context (if codex supports it).
