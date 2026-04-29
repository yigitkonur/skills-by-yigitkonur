# trigger-codex-rescue.py

Phase 6 entry point. After the PR-Creator sub-agent opens a PR, this wrapper queues a Codex rescue review against it via `node codex-companion.mjs task --background --write --fresh --model gpt-5.5 --effort xhigh --prompt-file <path> --json` — the same code path the `/codex:resc` slash command runs internally. Codex's `task --background` returns `{ jobId, status: "queued", title, logFile }` immediately; the rescue review continues in a detached worker and lands on the PR like any other reviewer's comments.

This is the **programmatic-loop equivalent** of `/codex:resc` for cases where main agent is dispatching rescues across N PRs in parallel and typing N slash commands is awkward. Both paths are first-class.

## Usage

```bash
# Default: queue rescue, write rescue_review_id + rescue_started_at to manifest, return.
python3 scripts/trigger-codex-rescue.py \
    --pr 42 --branch feat/foo \
    --worktree /Users/.../wt-feat-foo \
    --prompt-file /tmp/rescue-prompt-pr-42.md

# Pipe the prompt on stdin instead of a file
cat prompt.md | python3 scripts/trigger-codex-rescue.py \
    --pr 42 --branch feat/foo --worktree /path/to/wt

# Block until the rescue job terminates (max 30 min)
python3 scripts/trigger-codex-rescue.py \
    --pr 42 --branch feat/foo --worktree /path \
    --prompt-file /tmp/p.md --wait --timeout-ms 1800000

# Dry-run prints the resolved codex-companion.mjs path + the planned invocation
python3 scripts/trigger-codex-rescue.py --pr 42 --branch feat/foo --worktree /path --dry-run
```

## Behavior

1. Read the rescue prompt (from `--prompt-file` or stdin). Persist to `/tmp/codex-rescue-prompt-pr-<n>.md`.
2. Discover `codex-companion.mjs` (env-var first, then `~/.claude/plugins/cache/openai-codex/codex/<latest>/`).
3. From inside `<worktree>`, invoke:
   ```bash
   node codex-companion.mjs task \
        --background --write --fresh \
        --model <m> --effort <e> \
        --prompt-file /tmp/codex-rescue-prompt-pr-<n>.md --json
   ```
   `task --background` honors the flag (unlike `review`, which always runs synchronously). Returns immediately with the queued-job descriptor.
4. Parse `{ jobId, status: "queued", title, logFile }` from stdout.
5. Update the manifest entry's `rescue_review_id`, `rescue_started_at`, `rescue_status: "running"`, plus audit fields (`rescue_pr_number`, `rescue_model`, `rescue_effort`, `rescue_title`, `rescue_log_file`).
6. If `--wait`: poll `node codex-companion.mjs status <job-id> --wait --timeout-ms <n> --json` until terminal. Update `rescue_status` (`completed | failed | cancelled`), `rescue_finished_at`, `rescue_phase`, `rescue_elapsed`.
7. Else: return immediately. Phase 6's `await-pr-reviews.py` (the comment-poller Monitor) handles the wait via PR comments.

## Flags

| Flag | Default | Effect |
|---|---|---|
| `--pr <n>` | required | PR number. |
| `--branch <b>` | required | Branch name (manifest entry key). |
| `--worktree <path>` | required | Worktree directory; codex runs from here. |
| `--prompt-file <path>` | (stdin) | Comprehensive review prompt for Codex. If absent, reads stdin. |
| `--manifest <path>` | `<repo-root>/.codex-review-manifest.json` | Manifest to update. Defaults repo-local. |
| `--model <m>` | `gpt-5.5` | Codex reasoning model. |
| `--effort <e>` | `xhigh` | Codex effort: `none\|minimal\|low\|medium\|high\|xhigh`. |
| `--wait` | off | Block on `status --wait` until terminal. |
| `--timeout-ms <n>` | `1800000` (30 min) | Total wall-clock cap when `--wait` is set. |
| `--dry-run` | off | Print the plan; no invocation, no manifest write. |

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Rescue queued (and completed if `--wait`); manifest updated. |
| `1` | `--wait` set but the job timed out before terminal status. |
| `2` | Queue failed (codex error, unparseable response, manifest error). |
| `127` | Codex plugin not installed. Surface to user. |

## Plugin discovery

Same logic as `run-codex-review.py`:

1. **`${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs`** if the env var is set.
2. **Latest semver-sorted version** under `~/.claude/plugins/cache/openai-codex/codex/<version>/scripts/codex-companion.mjs`.
3. Else exit 127 with install instructions pointing at https://github.com/openai/codex-plugin-cc.

The discovery function is inlined in the script (one duplication is fine; not a shared module).

## Why these defaults

- **`--background`** is non-negotiable — `task --background` returns immediately with a job id; without it main agent would block for the entire rescue duration (1–5 minutes per PR × N PRs serially).
- **`--write`** lets Codex post the rescue review back to the PR as a comment.
- **`--fresh`** clears prior session bias. The rescue is a last check; we want Codex evaluating the PR cold.
- **`--model gpt-5.5`** is the strongest reasoning model available.
- **`--effort xhigh`** spends more compute. Acceptable because rescue is one-shot per PR (not 20 rounds).

## Polling pattern (`--wait` mode)

```bash
node codex-companion.mjs status <job-id> --wait --timeout-ms 1800000 --json
```

Returns `{ workspaceRoot, job: { id, status, phase, title, summary, logFile, startedAt, completedAt, updatedAt, elapsed, duration, progressPreview, kindLabel } }` when the job reaches a terminal status (`completed`, `failed`, `cancelled`) or when the timeout expires (job stays `running`/`queued`).

## When to run

- **Phase 6**, immediately after the PR-Creator sub-agent reports the PR number/URL.
- One invocation per PR; do not invoke twice for the same PR.
- Without `--wait`: returns in <2s; the comment-poller Monitor (`await-pr-reviews.py` or inlined Monitor command) catches the rescue review when it lands on the PR.
- With `--wait`: blocks for up to `--timeout-ms`. Use only when main agent has nothing else to do.

## Sample output (success, no `--wait`)

```
queueing codex rescue: PR #42 in /Users/.../wt-feat-foo (gpt-5.5, effort=xhigh)...
  ✓ queued: jobId=task-1714138200-abc123 status=queued
    logFile: /Users/.../codex-companion/state/jobs/task-1714138200-abc123.log
  ✓ manifest updated: /Users/.../repo/.codex-review-manifest.json
```

## Sample output (success, with `--wait`)

```
queueing codex rescue: PR #42 in /Users/.../wt-feat-foo (gpt-5.5, effort=xhigh)...
  ✓ queued: jobId=task-1714138200-abc123 status=queued
    logFile: /Users/.../codex-companion/state/jobs/task-1714138200-abc123.log
  ✓ manifest updated: /Users/.../repo/.codex-review-manifest.json
  waiting up to 1800s for rescue to finish...
  ✓ rescue completed (jobId=task-1714138200-abc123)
```

## Sample output (plugin missing)

```
codex-companion.mjs not found. Install the OpenAI Codex Claude Code plugin
(https://github.com/openai/codex-plugin-cc) — expected at ...
```

(exit 127; manifest `rescue_status: "failed"`, `rescue_error: "codex plugin unavailable"`)

## Failure modes

| Failure | Wrapper behavior | Caller (Phase 6) action |
|---|---|---|
| Plugin not installed | Exit 127; `rescue_status: "failed"`, `rescue_error: "codex plugin unavailable"` | Surface to user; install plugin. |
| `task --background` rejected by Codex (auth, network) | Exit 2; `rescue_status: "failed"`, error in manifest | Skip rescue stream; await-pr-reviews.py sees no rescue items. |
| Queue response unparseable | Exit 2; `rescue_status: "failed"`, `rescue_error: "unparseable queue response"` | Same. |
| `--wait` timeout (job still running) | Exit 1; manifest `rescue_status` reflects current state (likely `queued` or `running`) | Caller polls `status` later, or treats rescue as in-flight and proceeds. |
| Worktree missing | Exit 2 with stderr; no manifest update | Spawn-review-worktrees may have been bypassed; surface for human. |
| Rescue completes with `failed` or `cancelled` | Exit 2; manifest reflects status | Surface for human. |

## Read/write surface

- **Reads**: rescue prompt (file or stdin), manifest (initial), worktree directory, codex-companion stdout/stderr.
- **Writes**: `/tmp/codex-rescue-prompt-pr-<n>.md` (the prompt persistance), manifest entry for `<branch>` (atomic via `tempfile + os.replace`).
- **Does NOT**: commit, push, modify the worktree, comment on the PR (Codex itself does that via `--write`), or dispatch any Claude Agent.

## See also

- `scripts/run-codex-review.py` — the Phase 3 sibling that wraps `codex-companion.mjs review` (synchronous; for per-round inner-loop reviews).
- `scripts/await-pr-reviews.py` — the Phase 6 sibling that polls PR comments and waits for the rescue review (and external bots) to land.
- `references/post-pr-review-protocol.md` — full Phase 6 / 7 / 8 flow.
