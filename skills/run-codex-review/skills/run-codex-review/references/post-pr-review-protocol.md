# Post-PR Review Protocol

Phases 6–8 of this skill. After a PR is opened (Phase 5), this protocol governs:
- Triggering Codex rescue as the last automated check.
- Waiting for external review bots (Copilot, copilot-pull-request-reviewer, Greptile, Devin, cubic-dev-ai, plus any humans). Bot list expands over time as new code-review bots are installed on the repo; the comment-poller works against the GitHub API and surfaces whatever lands, so adding a new bot does not require skill changes.
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

There are two valid invocation paths for Phase 6 rescue from main agent. Pick by context:

**A. Interactive context (chat directive):** Type `/codex:resc --fresh --model gpt-5.5 --effort xhigh --pr <number>` in the chat. The slash command dispatches a Codex sub-agent via the `Agent` tool internally. Use this when main agent has a few PRs and you're not in a parallel loop.

**B. Programmatic loop context (sanctioned for Phase 6 with N PRs):**

```bash
Bash(run_in_background=True):
  cd <worktree-path> && \
  node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" task \
       --write --fresh --effort xhigh \
       "<comprehensive review prompt for PR #<n>>"
```

This is the **same code path** the `/codex:resc` slash command runs internally — `/codex:resc`'s frontmatter dispatches a Codex sub-agent via `node codex-companion.mjs task`. In a programmatic loop where main agent dispatches N rescue jobs in parallel, the Bash invocation is cleaner than typing N slash-command directives. Both are sanctioned; the companion-script path is NOT a workaround.

The `task` subcommand is the public interface for "run a Codex sub-agent on this prompt". `--write` means "post the review back to the PR thread"; `--fresh` means "no prior session bias"; `--effort xhigh` is the heaviest reasoning budget for one-shot last-check rescues.

`scripts/trigger-codex-rescue.py` wraps this for batch use; it:
1. Reads the manifest entry for `<branch>` to get `worktree_path`.
2. Inside that worktree, dispatches `node codex-companion.mjs task --write --fresh --effort xhigh "<prompt>"` via Bash run_in_background.
3. Captures the resulting Codex job id.
4. Writes `rescue_review_id` and `rescue_started_at` to the branch's manifest entry.
5. Returns immediately (does not poll).

### Why "fresh" and "xhigh effort"

These are arguments passed to the `/codex:resc` slash command, not shell flags:

- **`--fresh`**: no prior session bias. Codex rescue evaluates the PR cold; it doesn't carry over the inner-loop's context.
- **`--model gpt-5.5`**: stronger reasoning than the inner-loop's default model. The rescue is a last check; it deserves the heavier model.
- **`--effort xhigh`**: Codex spends more compute. Acceptable here because rescue is one-shot per PR, not per round.
- Background execution is governed by the codex plugin itself (rescue runs out-of-band by default); there is no `--background` argument to set explicitly.

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

## Phase 8a — main-agent direct apply (per-PR sequential; cross-PR order irrelevant)

After the evaluator sub-agent hands back, **main agent acts directly** (no further sub-agent). The evaluator's JSON is the authority; main agent applies each accepted item mechanically. **`/do-review` re-eval per item is OPTIONAL and OFF by default** — the evaluator already used /do-review in Phase 7; double-eval is rarely worth the cost. Reserve for borderline-confidence cases.

### Apply flow (per PR)

```
Read <repo>/.codex-review-rounds/pr-<n>.evaluation.json.

# AMBIGUOUS GATE — read this FIRST, before any apply
If ambiguous[] non-empty:
    Mark PR BLOCKED in manifest:
      terminal_reason: "ambiguous: <item-id>: <evaluator's question>"
    DO NOT apply this PR's accepted items either —
      partial-apply ships unreviewed code with half-decided intent.
    Surface in deliverable. Do NOT merge.
    Move to next PR.

# ACCEPTED ITEMS — only reached when ambiguous[] is empty
For each accepted item (deduplicated across sources, first-seen rationale wins):
    1. Read cited code at <worktree>/<file>:<line> ± 25 lines (Read tool).
    2. Apply the evaluator's intended-shape fix via Edit.
       If it doesn't apply cleanly (file moved, line shifted, current shape mismatch):
         DO NOT improvise. Record `apply_failed_after_evaluation: <item-id>` in manifest.
         Continue with remaining items. Surface at end of Phase 8a.
    3. Stage by concern from the start:
         git -C <worktree> add <files-for-this-concern>
         (do NOT stage all then `git restore --staged .` to peek and restage)
    4. git -C <worktree> diff --cached  # verify only intended hunks
    5. git -C <worktree> commit -m "<emoji> <type>(<scope>): <subject> (#<pr>)"
       — Note the (#<pr>) suffix for traceability.
       — One concern per commit by default.
       — Multi-concern allowed IFF tightly coupled to same file AND
         message lists each concern as a bullet (the bullets are the
         accountability — they document the audit trail).

# OPTIONAL sanity-check
For borderline confidence items only (not by default):
    Skill(skill="do-review", args="--item <body> --code <cited_code>")
    If main agent disagrees with the evaluator's accept decision:
      Mark item ambiguous; revert; surface — do not push the disagreement.

# VALIDATE before push
pnpm run build && pnpm test  # or repo-equivalent per AGENTS.md/CONTRIBUTING.md
If validation fails:
    Revert the offending commit. Mark item ambiguous. Surface — do not retry blindly.

# PUSH (no merge yet)
git -C <worktree> push origin <branch>   # NEVER --force
```

Process PRs in any order in 8a. Foundation→leaf is enforced in 8b.

### Phase 8a apply recipe (one-shot helper)

A wrapper script encapsulates the repetitive bits:

```bash
python3 <this-skill>/scripts/apply-evaluator-decisions.py \
  --pr <n> \
  --worktree <worktree> \
  --eval <repo>/.codex-review-rounds/pr-<n>.evaluation.json \
  --print-queue
```

Output: ordered apply queue with ambiguous items at the top (BLOCKED warning), then accepted items each with `file:line:intended-shape:rationale`. Read-only — does NOT modify worktree, does NOT commit, does NOT push. Main agent walks the queue, applies via Edit, validates, commits, pushes — but the queue derivation is mechanical and offloaded to the script.

### Why main-agent direct, not sub-agent

The evaluator's structured output is already in main agent's context. Re-dispatching to a sub-agent for the apply step would:
- Pay a cold-start cost.
- Re-load the evaluator's JSON into a fresh agent.
- Risk drift between evaluator's rationale and applier's interpretation.

Main agent applying directly keeps the chain tight: evaluator decides → main agent applies. The user's stated principle: "do-review is healthier when answers come straight back".

## Phase 8b — merge in foundation→leaf strict serial

Apply is done; now merge in dependency order. Foundation merges first; each leaf rebases onto the new main between merges.

### Merge flow

```
Order PRs per manifest.merge_order (foundation first, then leaves).

For each PR in order:
    # CI-WAIT GATE
    Bash(run_in_background=True):
      until [ "$(gh pr checks <n> --json bucket --jq 'all(.[]; .bucket != "pending")')" = "true" ]; do
        sleep 30
      done
      gh pr checks <n>
    # Notification fires when all checks land terminal state.

    If any check is `failure` or `cancelled`:
        Mark PR BLOCKED with terminal_reason: "CI failure: <check-name>"
        Surface; do NOT merge; continue with next PR.
        Exception: if THIS is foundation, STOP — do not merge any leaves.

    Else:
        gh pr merge <n> --repo <fork>/<repo> --squash
          (or --merge / --rebase per repo policy from AGENTS.md)

    After merge:
        git fetch --all --prune
        For every leaf PR not yet merged:
            git -C <leaf-worktree> rebase origin/main
            git -C <leaf-worktree> push --force-with-lease origin <leaf-branch>
            (--force-with-lease, NOT --force; safe because no review is in flight
             and Phase 1's backup ref preserves the original commits.)
```

### Foundation must succeed first

Leaves are based on foundation. If foundation can't merge (CI fails, conflict): STOP — do not merge any leaves; surface foundation BLOCKED to the human. The human resolves foundation, then re-runs Phase 8b on the leaves.

### Optional: open a fresh PR for `apply_failed_after_evaluation`

If Phase 8a recorded items as `apply_failed_after_evaluation` (intended-shape didn't apply because file/line drifted), surface them at end of 8a. The human decides:

1. Re-run Phase 7 evaluator with current code (preferred), OR
2. Branch from main again, cherry-pick the original branch's commits + apply the failed items by hand, open a new PR (Phase 5 redux), close the original PR.

Don't auto-cycle — surface and let the human pick.

## Failure modes

### Codex rescue never returns

`audit-review-state.py` flags the `rescue_review_id` as in-flight past total_cap. Treat as missing source — proceed with whatever did arrive. Note in PR's manifest entry: `rescue_status: timeout`.

### No external bots installed in repo

`await-pr-reviews.py` waits the base 900s, sees no external sources. Quiet window triggers (no comments at all → 3 min quiet from t=900s = always quiet). Returns at t=1080s (900s + extension before quiet check) with only codex rescue in `sources[]` (or empty if rescue also failed).

The Phase 7 evaluator handles a single source (or no source) gracefully. If the gathered JSON has zero items, evaluator outputs an empty decisions array; main agent merges directly.

### External bot reviews are still arriving at total_cap

`await-pr-reviews.py` terminates with `wait_terminated_by: "total_cap"`. The current state is gathered. Phase 7 evaluates what we have. Late-arriving comments after evaluation are surfaced for human attention but don't block merge — the bot will still see them on the merged commit if it cares.

### Evaluator marks anything ambiguous (the BLOCKED gate)

**An item marked `ambiguous` by the evaluator means**: real issue OR false positive can't be determined without human input.

**Rule**: a single ambiguous item BLOCKS the entire PR. Do NOT half-apply (don't ship the accepted items and defer the ambiguous ones — that ships unreviewed code with a half-decided intent). Defer the entire PR.

Per ambiguous item, main agent records:
1. `manifest.pr.terminal_reason: "ambiguous: <item-id>: <evaluator's exact question>"`.
2. Skip apply for that PR's accepted items too.
3. Surface in final deliverable with the evaluator's exact question.
4. Do NOT merge.

If the evaluator marks **everything** ambiguous, surface the whole PR for human triage. Likely cause: PR is too broad or too cross-cutting; consider splitting in a follow-up.

### Evaluator's accepted fix breaks CI

Phase 8a push fails CI in 8b. Revert the bad commit on the branch (don't force-push; commit a revert), mark the item `apply_failed_validation` in the manifest with `terminal_reason: "post-apply CI failure: <details>"`, surface for human.

### Phase 8a intended-shape doesn't apply cleanly (`apply_failed_after_evaluation`)

The evaluator's `intended-shape` references a file:line that has drifted (file moved, line shifted, surrounding code refactored between Phase 7 and Phase 8a). DO NOT improvise a fix.

Record `apply_failed_after_evaluation: <item-id>` in manifest. Continue with remaining items. Surface at end of Phase 8a. Human decides:
1. Re-run Phase 7 evaluator with current code (preferred), OR
2. Apply by hand and open a fresh PR (Phase 5 redux for that branch).

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
| Invoke codex rescue from Bash (`codex review --rescue …`) | There is no such CLI surface. Use `Skill(codex:resc, …)` — slash command, not shell. |
| `node …/codex-companion.mjs task …` directly from a sub-agent brief | The wrapper does that, plus discovery + manifest update + (optional) status polling. Use the wrapper. |
| Wait less than 900s by default | Bots that arrive at minute 13 are missed; their feedback is lost. |
| Wait more than total_cap | Indefinite wait = dead session. Cap is the safety. |
| Auto-merge after Phase 8 even with ambiguous items | Ambiguous means human-in-the-loop. Auto-merge defeats the gate. |
| Re-run `/codex:review` after Phase 8 apply | Phase 8's commits are post-evaluator. Codex would re-flag items the evaluator already decided. Don't re-loop. |
| Apply rejected items "just to be safe" | Rejected means false positive. Applying them adds bad commits. |

## Bottom line

Open PR → trigger codex rescue → wait 900s with adaptive end → gather all streams → one evaluator sub-agent per PR uses `/do-review` → main agent applies accepted items directly using `/do-review` in own context → merge or surface BLOCKED. Two streams, one evaluator, direct apply, clean merge.
