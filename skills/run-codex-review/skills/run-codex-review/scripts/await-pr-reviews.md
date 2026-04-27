# await-pr-reviews.py

Phase 6 wait + gather. After `trigger-codex-rescue.py` fires off the Codex rescue review, this script:

1. Waits for review streams (codex rescue + external bots) to land on the PR.
2. Adaptively decides when to stop waiting (quiet window vs. extension vs. total cap).
3. Gathers all reviews + comments from all sources via `gh api`.
4. Normalizes each item to a unified schema.
5. Writes the gathered JSON to `<rounds-dir>/<slug>.pr-reviews.json`.
6. Updates the manifest entry with the path + termination reason.

## Usage

```bash
# Default 900s base + adaptive end + 1800s total cap
python3 scripts/await-pr-reviews.py --pr 42 --branch feat/foo

# Override the timing
python3 scripts/await-pr-reviews.py --pr 42 --branch feat/foo \
  --base-wait 900 --quiet-window 180 --extension 300 --total-cap 1800

# Skip the wait entirely; just gather whatever's there now
python3 scripts/await-pr-reviews.py --pr 42 --branch feat/foo --no-wait
```

## Adaptive algorithm

```
record start_time
wait base_wait seconds (default 900)
   (poll every poll_interval to surface progress; doesn't shorten the wait)

loop:
    fetch all reviews + comments
    measure age of newest comment across all sources
    if age >= quiet_window (default 180s = 3 min):
        break  → "quiet"
    if (now - start_time) >= total_cap (default 1800s = 30 min):
        break  → "total_cap"
    wait min(extension, time_remaining_to_cap) seconds
    re-check
```

Termination reasons (recorded in the output JSON):

| `wait_terminated_by` | Meaning |
|---|---|
| `quiet` | Newest comment is at least `--quiet-window` old. Bots done. |
| `quiet_no_comments` | No comments arrived during the wait. Treat as done. |
| `total_cap` | Hit the safety cap with comments still flowing. Take what we have. |
| `no_wait` | `--no-wait` passed; immediate gather, no wait. |

## Calibration knobs

| Flag | Default | Why |
|---|---|---|
| `--base-wait <s>` | `900` (15 min) | "Most agents finish within 15 minutes" (per the user's spec). |
| `--quiet-window <s>` | `180` (3 min) | "If no review in last 3 minutes, all sub-agents have finished" (user's spec). |
| `--extension <s>` | `300` (5 min) | "If still receiving, wait additional 5 min" (user's spec). |
| `--total-cap <s>` | `1800` (30 min) | Safety bound. Past this, accept the state. |
| `--poll-interval <s>` | `60` (1 min) | How often to print progress during the base wait. Doesn't shorten anything. |

These match the user's specified semantics. Override only with explicit reason.

## Source classification

Each review or comment is mapped to one of:

| Source | Author logins matched (case-insensitive) |
|---|---|
| `codex-rescue` | `codex[bot]`, `codex-rescue[bot]`, `openai-codex[bot]` |
| `copilot` | `copilot`, `copilot[bot]`, `github-copilot[bot]`, `github-actions[bot]` |
| `greptile` | `greptile-apps[bot]`, `greptile[bot]`, `greptileai[bot]` |
| `devin` | `devin-ai-integration[bot]`, `devin[bot]`, `devin-ai[bot]` |
| `human:<login>` | anything else |

Adjust the `BOT_LOGINS` dict in the script if your repo's bots use different login names.

## Item schema

Each gathered item:

```json
{
  "id": "codex-rescue-review-12345",
  "severity_raw": "COMMENTED" | "APPROVED" | "CHANGES_REQUESTED" | "comment",
  "file": "src/foo.ts" | null,
  "line": 42 | null,
  "body": "Off-by-one in slice() — drops the last element.",
  "submitted_at": "2026-04-26T11:34:22Z",
  "author": "codex[bot]"
}
```

Inline review comments have `file` + `line`. Top-level review summaries and PR-level comments have `file: null` + `line: null`.

## Output JSON schema

```json
{
  "pr_number": 42,
  "pr_url": "https://github.com/<fork>/<repo>/pull/42",
  "branch": "feat/foo",
  "fetched_at": "2026-04-26T11:30:00Z",
  "wait_terminated_by": "quiet",
  "wait_seconds": 1080,
  "sources": [
    {"source": "codex-rescue", "raw_count": 5, "items": [...]},
    {"source": "copilot",      "raw_count": 8, "items": [...]},
    {"source": "greptile",     "raw_count": 12, "items": [...]},
    {"source": "devin",        "raw_count": 3, "items": [...]}
  ]
}
```

Path: `<rounds-dir>/<branch-slug>.pr-reviews.json`. Phase 7's evaluator subagent reads this directly.

## Flags

| Flag | Default | Effect |
|---|---|---|
| `--pr <n>` | required | PR number. |
| `--branch <b>` | required | Branch name (manifest entry key). |
| `--manifest <path>` | `/tmp/codex-review-manifest.json` | Manifest to read fork_owner_repo from + update. |
| `--rounds-dir <path>` | `/tmp/codex-review-rounds/` | Output directory. |
| `--base-wait <s>` | `900` | Initial wait before adaptive checks. |
| `--quiet-window <s>` | `180` | Threshold for "newest comment too old → done". |
| `--extension <s>` | `300` | How much to extend if comments still flowing. |
| `--total-cap <s>` | `1800` | Safety bound for total wait. |
| `--poll-interval <s>` | `60` | Progress probe cadence during base wait. |
| `--no-wait` | off | Skip wait; gather immediately. |

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Reviews gathered (terminated by `quiet` / `quiet_no_comments` / `no_wait`). |
| `1` | Wait terminated by `total_cap` (still gathered what we have; surface in deliverable). |
| `2` | Manifest absent or fork_owner_repo missing; fatal. |
| `3` | gh CLI couldn't fetch PR / API failure. |

## When to run

- **Phase 6**, immediately after `trigger-codex-rescue.py`.
- One invocation per PR.
- If you re-run, the gathered JSON is overwritten — old version is lost.

## Safety

- Read-only on git state.
- Read-only on PR state (only fetches; never comments, never approves, never closes).
- Writes to `<rounds-dir>/<slug>.pr-reviews.json` (atomic).
- Updates manifest entry (atomic).
- Does NOT push, commit, merge, or modify the worktree.

## API endpoints used

| Endpoint | Purpose |
|---|---|
| `gh pr view <n> --repo <r> --json ...` | Verify PR exists, get URL, base, head. |
| `gh api repos/<r>/pulls/<n>/reviews --paginate` | Top-level reviews (with summary body). |
| `gh api repos/<r>/pulls/<n>/comments --paginate` | Inline review comments (file/line). |
| `gh api repos/<r>/issues/<n>/comments --paginate` | Top-level PR comments (PRs use the issues endpoint). |

All read-only. All paginated. Rate-limit-friendly (~6 calls per gather).

## Sample output (success — quiet termination)

```
PR:     #42  https://github.com/you/myrepo/pull/42
branch: feat/foo
repo:   you/myrepo
mode:   adaptive wait + gather
  base_wait=900s  quiet_window=180s  extension=300s  total_cap=1800s

  base wait: 900s (15 min)...
    [60s] 0 sources, 0 items so far
    [120s] 1 sources, 1 items so far
    [180s] 2 sources, 4 items so far
    [240s] 3 sources, 7 items so far
    ...
    [900s] 4 sources, 28 items so far
    [960s] newest comment 240s old (≥ 180s quiet); proceeding

  ✓ gathered 28 items across 4 sources
  ✓ written: /tmp/codex-review-rounds/feat-foo.pr-reviews.json
```

## Sample output (extension)

```
    [900s] 4 sources, 19 items so far
    [960s] newest comment 70s old (< 180s); waiting +300s
    [1260s] newest comment 90s old (< 180s); waiting +300s
    [1560s] newest comment 250s old (≥ 180s quiet); proceeding

  ✓ gathered 23 items across 4 sources
```

## Sample output (total cap reached)

```
    [1800s] total cap reached; stopping

  ✓ gathered 31 items across 4 sources
  ✓ written: /tmp/codex-review-rounds/feat-foo.pr-reviews.json
```

(exit 1 — caller should note `wait_terminated_by: total_cap` in the deliverable)

## Failure modes

| Failure | Behavior |
|---|---|
| `gh` CLI not installed | Exit 2 with stderr; manifest unchanged. |
| Repo not findable in manifest | Exit 2 with stderr; manifest unchanged. |
| PR doesn't exist | Exit 3; manifest unchanged. |
| GitHub API rate-limited | gh's automatic backoff handles transient limits; sustained limits cause empty arrays + the script proceeds (might miss data). |
| User Ctrl-C during wait | Python KeyboardInterrupt; partial gather not written; exit non-zero. |

## Cache awareness

The base wait of 900s exceeds the agent's prompt-cache TTL (5 min). Running this script as a subprocess **does not** consume the agent's cache during the wait — the agent's context is idle. After the script returns, the agent reads its full conversation context once (cache miss). This is acceptable cost for the value of waiting for external bot reviews.

Alternatives if you want to release the runtime entirely during the wait:

- `ScheduleWakeup(delaySeconds=900, ...)` if you're in `/loop` dynamic mode.
- `Monitor` tool watching a polling background command.

For most cases, this script is the cleanest path.

## Read/write surface

- **Reads**: manifest, gh API (read-only).
- **Writes**: `<rounds-dir>/<slug>.pr-reviews.json` (atomic), manifest entry (atomic).
- **Does NOT**: push, commit, modify the worktree, comment on the PR, dispatch any Claude Agent.

## Extending

- Add a per-source filter (`--only-sources codex-rescue,copilot`) if you want to ignore Greptile/Devin temporarily.
- Add a `--watch` mode that streams progress without ending — useful for human monitoring.
- Add review-state filtering (e.g., skip approvals, only gather `CHANGES_REQUESTED`).
- Add a CSV / TSV output mode for spreadsheet ingestion.
