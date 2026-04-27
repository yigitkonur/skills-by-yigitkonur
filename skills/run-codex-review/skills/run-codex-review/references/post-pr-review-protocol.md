# Post-PR Review Protocol

Phases 6–8 of this skill. After a PR is opened (Phase 5), this protocol governs:
- Triggering Codex rescue as the last automated check.
- Waiting for external review bots (Copilot, Greptile, Devin, plus any humans).
- Adaptive end condition: 900s base + extension if comments still flowing + termination on quiet.
- Hand-off to Phase 7 evaluator sub-agent.
- Phase 8 main-agent direct apply.

## The two review streams

After PR creation, two streams produce feedback:

| Stream | Source | Trigger | Typical arrival |
|---|---|---|---|
| 1 | **Codex rescue** | We trigger via `trigger-codex-rescue.py` immediately after PR creation | 1–5 minutes |
| 2 | **External bots** (Copilot, Greptile, Devin) | Auto-triggered by GitHub on PR open | 1–10 minutes per bot |

Codex rescue is **Codex's own background sub-agent**, not a Claude sub-agent we dispatch. We hand off the PR link; Codex spawns its own infrastructure to review. We wait for the review to land on the PR like any other.

## Phase 6 — trigger codex rescue

```bash
python3 scripts/trigger-codex-rescue.py --pr <number> --branch <b>
```

The script:
1. Reads the manifest entry for `<branch>` to get `worktree_path`.
2. Inside that worktree, invokes the Codex rescue CLI form:
   ```
   codex review --rescue --background --fresh --model gpt-5.5 --effort xhigh --pr <number>
   ```
   (Adjustment point in the script; the actual CLI form depends on your Codex install.)
3. Captures the rescue job id from stdout.
4. Writes `rescue_review_id` and `rescue_started_at` to the branch's manifest entry.
5. Returns immediately (does not poll).

### Why "fresh" and "xhigh effort"

- **`--fresh`**: no prior session bias. Codex rescue evaluates the PR cold; it doesn't carry over the inner-loop's context.
- **`--model gpt-5.5`**: stronger reasoning than the inner-loop's default model. The rescue is a last check; it deserves the heavier model.
- **`--effort xhigh`**: Codex spends more compute. Acceptable here because rescue is one-shot per PR, not per round.
- **`--background`**: Codex queues the job; we don't block waiting for it.

## Phase 6 — adaptive review window

After codex rescue is triggered, the wait begins:

```bash
python3 scripts/await-pr-reviews.py --pr <number> \
  --base-wait 900 --quiet-window 180 --extension 300 --total-cap 1800
```

### The algorithm

```
trigger codex rescue
record start_time
wait base_wait seconds (900s = 15 minutes)

loop:
    fetch PR comments via gh api repos/<owner>/<repo>/pulls/<n>/comments + reviews
    measure age of newest comment
    if newest_comment_age > quiet_window (180s = 3 minutes):
        break  # all bots quiet for ≥ 3 min → assume done
    elif (now - start_time) >= total_cap (1800s = 30 minutes):
        break  # safety cap reached
    else:
        wait extension seconds (300s = 5 minutes)
        # then re-check

emit gathered reviews JSON
```

### Calibration values (defaults, override with flags)

| Knob | Default | Why |
|---|---|---|
| Base wait | **900 s** (15 min) | Most external bots finish within 15 min on typical PRs. |
| Quiet window | **180 s** (3 min) | "If no comment in last 3 min, all sub-agents have finished." (your spec) |
| Extension | **300 s** (5 min) | "If still receiving, wait additional 5 min." (your spec) |
| Total cap | **1800 s** (30 min) | Safety bound to prevent runaway. Override only with explicit reason. |

### Why these values, not others

- The 3-min quiet window is the "sub-agents are done" signal. Bots that are still working post comments every 1–2 min; 3 min of silence is a strong signal they're idle.
- The 5-min extension matches typical bot inter-comment intervals. If a bot is mid-stream, give it 5 min to finish; if no further comment after that, it's done.
- The 30-min total cap is the hard ceiling. Past 30 min, even if comments are still arriving, accept the state — the bots are running unusually slow OR they're stuck. Better to evaluate what we have than to wait forever.

## Phase 6 — gathering output

After the wait terminates, `await-pr-reviews.py` writes:

```
/tmp/codex-review-rounds/<branch-slug>.pr-reviews.json
```

Schema:

```json
{
  "pr_number": 42,
  "pr_url": "https://github.com/<fork-owner>/<repo>/pull/42",
  "branch": "feat/foo",
  "worktree_path": "/Users/.../wt-feat-foo",
  "fetched_at": "2026-04-26T11:30:00Z",
  "wait_terminated_by": "quiet" | "total_cap" | "interrupted",
  "wait_seconds": 1080,
  "sources": [
    {
      "source": "codex-rescue",
      "review_id": "cdx-rescue-abc123",
      "raw_text": "...",
      "items": [
        {"id": "...", "severity_raw": "...", "file": "...", "line": 42, "body": "..."}
      ]
    },
    {"source": "copilot", "items": [...]},
    {"source": "greptile", "items": [...]},
    {"source": "devin", "items": [...]},
    {"source": "human:<username>", "items": [...]}
  ]
}
```

`source` values:
- `codex-rescue` — the codex rescue review
- `copilot` — GitHub Copilot's review
- `greptile` — Greptile bot's review
- `devin` — Devin's review
- `human:<username>` — any human reviewer's items (rare in this flow)

Items are normalized across sources to the same JSON shape; source-specific metadata goes in the raw_text or extra fields.

## Phase 7 — evaluator sub-agent dispatch

After Phase 6 emits the gathered JSON, main agent dispatches **one evaluator sub-agent per PR**. The brief follows MISSION_PROTOCOL (see `parallel-subagent-protocol.md` for the template).

Key brief points:
- **Context**: PR number, URL, worktree, gathered reviews JSON path. Provide all known PR changes (commits, files).
- **Mission**: evaluate every item via `/do-review` skill. Return decisions per `references/review-evaluation-protocol.md` schema. **Do not modify the worktree.**
- **DoD**: every item has a decision; output JSON conforms to schema; cross-source contradictions flagged as ambiguous in BOTH affected items.
- **Verification**: `git status` in worktree returns empty (no drift); JSON has decisions for all items.
- **Failure**: missing decision → mark ambiguous; stale citation → reject; can't determine → ambiguous (never silently accept).

## Phase 8 — main-agent direct apply

After the evaluator sub-agent hands back, **main agent acts directly** (no further sub-agent). Use `/do-review` skill in main agent's context for sanity-checking each apply.

### Apply flow

```
Read evaluator's output JSON.
For each accepted item (deduplicated across sources):
    1. Read cited code (Read tool) at <worktree>/<file>:<line> ± context.
    2. Compose the fix per evaluator's rationale + Codex/source's suggested fix.
    3. Sanity-check via /do-review skill (in main agent's context):
       - Does the fix align with the evaluator's rationale?
       - Does the fix introduce regressions?
    4. Apply via Edit (with diff-walk discipline).
    5. git add <files>.
    6. git diff --cached (verify only intended hunks).
    7. git commit -m "<emoji> <type>(<scope>): apply <source>'s <item-id>"
       — or one commit per logical concern (better; matches inner-loop discipline).

If ambiguous[] non-empty:
    Mark PR BLOCKED in manifest with terminal_reason citing the items.
    Surface in deliverable.
    Do NOT merge.
    Optional: open a fresh PR with the patches applied (if changes are too divergent for an in-place amendment).

Else:
    git push origin <branch>
    Wait for CI green.
    gh pr merge <number> --repo <fork>/<repo> --squash | --merge | --rebase
       (per repo policy)
```

### Why main-agent direct, not sub-agent

The evaluator's structured output is already in main agent's context. Re-dispatching to a sub-agent for the apply step would:
- Pay a cold-start cost.
- Re-load the evaluator's JSON into a fresh agent.
- Risk drift between evaluator's rationale and applier's interpretation.

Main agent applying directly keeps the chain tight: evaluator decides → main agent applies. The user's stated principle: "do-review is healthier when answers come straight back".

### Optional: open a fresh PR

If the evaluator's accepted set is so large or divergent that amending the current PR would muddy its history, main agent has the option to:

1. Mark the current PR as "superseded by #<new>".
2. Branch from main again.
3. Cherry-pick the original branch's commits + apply the accepted items.
4. Open a new PR with `/ask-review` (Phase 5 redux for this branch).
5. Close the original PR.

This is the user's "we'll ask for a new PR if needed" path. Use sparingly — most of the time, in-place commits are simpler.

## Failure modes

### Codex rescue never returns

`audit-review-state.py` flags the `rescue_review_id` as in-flight past total_cap. Treat as missing source — proceed with whatever did arrive. Note in PR's manifest entry: `rescue_status: timeout`.

### No external bots installed in repo

`await-pr-reviews.py` waits the base 900s, sees no external sources. Quiet window triggers (no comments at all → 3 min quiet from t=900s = always quiet). Returns at t=1080s (900s + extension before quiet check) with only codex rescue in `sources[]` (or empty if rescue also failed).

The Phase 7 evaluator handles a single source (or no source) gracefully. If the gathered JSON has zero items, evaluator outputs an empty decisions array; main agent merges directly.

### External bot reviews are still arriving at total_cap

`await-pr-reviews.py` terminates with `wait_terminated_by: "total_cap"`. The current state is gathered. Phase 7 evaluates what we have. Late-arriving comments after evaluation are surfaced for human attention but don't block merge — the bot will still see them on the merged commit if it cares.

### Evaluator marks everything ambiguous

Surface for human triage. Do not merge. Likely cause: PR is too broad or too cross-cutting; consider splitting in a follow-up.

### Evaluator's accepted fix breaks CI

Phase 8 push fails CI. Revert the bad commit on the branch (don't force-push; commit a revert), mark the item ambiguous in the manifest with `terminal_reason: "post-apply CI failure: <details>"`, surface for human.

### Cross-source contradiction can't be resolved

Both sources' items go ambiguous. PR is BLOCKED. Human picks one source's recommendation, applies manually, then signals main agent to merge.

### Bot posts a non-actionable comment

Examples: "LGTM", "Looking good!", "Great work". The evaluator should treat these as **rejected with rationale "non-actionable approval"** — they don't drive a fix. The PR's GitHub state still shows the approval; the evaluator just doesn't generate work from it.

## "Ask for a new PR" semantics

Sometimes the evaluator's accepted items are so substantial that applying them in-place would:

- Bloat the PR's diff to where reviewers complain about scope creep.
- Mix the original change with the post-review fix in ways that hide which is which.
- Break the original PR's narrative (the body explains X, but now the PR is X + Y).

In these cases, Phase 8's "open a fresh PR" branch is the right answer. Decision rubric:

| Situation | Action |
|---|---|
| Accepted items are ≤ 3 small fixes (<50 lines total) | Apply in-place. |
| Accepted items overlap the original change's logic | Apply in-place. |
| Accepted items are a parallel concern (different files, different motivation) | New PR. |
| Original PR title would no longer match the resulting diff | New PR. |

Default: in-place. New PR is the escape hatch for unusual cases.

## Wait pattern alternatives

The user's design lists three wait mechanisms; the script implements the primary, but the others are valid choices:

| Mechanism | When |
|---|---|
| `await-pr-reviews.py --wait` | Default. Self-contained. |
| Bash `sleep 900` | Quick one-shot, no adaptive logic. Use only when external bots are absent. |
| `Monitor` tool with until-loop | If there's a streamable signal (e.g., `gh pr view --watch` doesn't exist, but a polling background process can be Monitor'd). |
| `ScheduleWakeup(delaySeconds=900)` | When the agent is in /loop dynamic mode and wants to release the runtime during the wait. Only available in /loop. |

The script is the default because the adaptive logic + gathering is bundled.

## Cache awareness

The 900s+ wait exceeds the 5-minute prompt cache TTL. After the wait, the next agent turn reads its full conversation context uncached. This is acceptable cost — the alternative is missing late-arriving bot reviews. If you're sensitive to cache miss cost, run the wait inside a script (`await-pr-reviews.py`); the script doesn't blow your context cache.

## Anti-patterns

| Anti-pattern | Why it fails |
|---|---|
| Skip Phase 6, merge fast | Loses the value of external review entirely. The whole skill exists to harvest reviewer feedback. |
| Trust copilot's items blindly | Copilot is a reviewer like any other. Evaluator first. |
| Run codex rescue inline (not `--background`) | Blocks the agent for 1–5 min. Defeats the parallel orchestration. |
| Wait less than 900s by default | Bots that arrive at minute 13 are missed; their feedback is lost. |
| Wait more than total_cap | Indefinite wait = dead session. Cap is the safety. |
| Auto-merge after Phase 8 even with ambiguous items | Ambiguous means human-in-the-loop. Auto-merge defeats the gate. |
| Re-run `/codex:review` after Phase 8 apply | Phase 8's commits are post-evaluator. Codex would re-flag items the evaluator already decided. Don't re-loop. |
| Apply rejected items "just to be safe" | Rejected means false positive. Applying them adds bad commits. |

## Bottom line

Open PR → trigger codex rescue → wait 900s with adaptive end → gather all streams → one evaluator sub-agent per PR uses `/do-review` → main agent applies accepted items directly using `/do-review` in own context → merge or surface BLOCKED. Two streams, one evaluator, direct apply, clean merge.
