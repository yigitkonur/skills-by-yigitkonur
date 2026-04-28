# Branch Decomposition Ledger

The manifest is the durable cross-process state for the entire skill. Every sub-agent (coordinator, worker, PR-creator, evaluator) and the main agent communicate exclusively through atomic writes to this file. This file specifies the schema, the status states, the persistence rules, and the rendering to the final deliverable.

## File location

Default: `<repo-root>/.codex-review-manifest.json` (the wrappers compute this from the worktree's git common-dir and add `.codex-review-manifest.json` next to it). Override with `--manifest <path>` on every script. The repo-local default keeps concurrent skill sessions across different repos from clobbering each other (older skill versions defaulted to `/tmp/codex-review-manifest.json` and concurrent sessions caused lost-update bugs in production). Add `.codex-review-manifest.json{,.lock}` and `.codex-review-rounds/` to `.gitignore`.

## Schema (top-level)

```json
{
  "schema_version": 2,
  "repo_root": "/Users/yigitkonur/dev-test/myrepo",
  "base_branch": "main",
  "fork_owner_repo": "yigitkonur/myrepo",
  "upstream_owner_repo": "upstream-owner/myrepo",
  "created_at": "2026-04-26T10:00:00Z",
  "completed_at": null,
  "merge_order": null,
  "branches": [ /* per-branch entries */ ]
}
```

`merge_order` is filled in Phase 4 by the main agent after reading the manifest's terminal states.

`schema_version` is bumped to `2` from `1` in this revision (post-PR fields added).

## Schema (per-branch entry)

```json
{
  "branch": "feat/foo",
  "concern_one_liner": "Replace interests with marketing-set in onboarding",
  "worktree_path": "/Users/.../myrepo-wt-feat-foo",
  "remote": "origin",
  "head_sha_at_spawn": "deadbeef1234...",
  "head_sha_current": "feedface9876...",

  "status": "IN-LOOP",
  "rounds": 3,
  "last_review_id": "cdx-job-abc123",
  "last_review_at": "2026-04-26T10:14:32Z",
  "last_classifier_summary": {"total": 4, "major_n": 1, "minor_n": 3, "unclassified_n": 0},
  "subagent_started_at": "2026-04-26T10:01:00Z",
  "updated_at": "2026-04-26T10:15:00Z",
  "terminal_reason": null,
  "backup_ref": "backup/codex-review/feat-foo/2026-04-26T09-58-22Z",
  "cleaned_up": false,
  "all_rejected_streak": 0,

  "round_history": [
    {
      "round": 1,
      "review_id": "...",
      "major_n": 3, "minor_n": 2,
      "decisions": {"accepted": 2, "rejected": 1, "ambiguous": 0},
      "completed_at": "..."
    },
    {
      "round": 2,
      "review_id": "...",
      "major_n": 2, "minor_n": 4,
      "decisions": {"accepted": 1, "rejected": 0, "ambiguous": 1},
      "completed_at": "..."
    }
  ],

  /* Phase 5 — set by PR-creator */
  "pr_number": 42,
  "pr_url": "https://github.com/yigitkonur/myrepo/pull/42",
  "pr_title": "✨ feat(onboarding): replace interests with marketing-set",
  "pr_body_path": "/tmp/pr-body-feat-foo.md",
  "pr_opened_at": "2026-04-26T11:00:00Z",
  "pr_body_chars": 28412,
  "pr_explicit_questions": 5,

  /* Phase 6 — set by trigger-codex-rescue.py */
  "rescue_review_id": "cdx-rescue-abc123",
  "rescue_started_at": "2026-04-26T11:01:00Z",
  "rescue_status": "running",
  "rescue_pr_number": 42,
  "rescue_model": "gpt-5.5",
  "rescue_effort": "xhigh",

  /* Phase 6 — set by await-pr-reviews.py */
  "pr_reviews_path": "/tmp/codex-review-rounds/feat-foo.pr-reviews.json",
  "pr_reviews_terminated_by": "quiet",
  "pr_reviews_wait_seconds": 1080,

  /* Phase 7 — set by evaluator sub-agent */
  "pr_evaluation_path": "/tmp/codex-review-rounds/feat-foo.pr-evaluation.json",
  "pr_evaluation_summary": {
    "total": 28,
    "accepted": 9,
    "rejected": 17,
    "ambiguous": 2,
    "by_source": {
      "codex-rescue": {"accepted": 3, "rejected": 4, "ambiguous": 0},
      "copilot": {"accepted": 2, "rejected": 8, "ambiguous": 1},
      "greptile": {"accepted": 4, "rejected": 5, "ambiguous": 1},
      "devin": {"accepted": 0, "rejected": 0, "ambiguous": 0}
    }
  },
  "pr_evaluation_at": "2026-04-26T11:25:00Z",

  /* Phase 8 — set by main agent direct */
  "pr_apply_commits": ["abc123...", "def456..."],
  "pr_applied_at": "2026-04-26T11:35:00Z",
  "pr_merged": true,
  "pr_merged_at": "2026-04-26T11:40:00Z",
  "pr_merge_method": "squash"
}
```

Notes on fields:
- `head_sha_at_spawn` is fixed; `head_sha_current` updates after each push (worker, then Phase 8 main agent).
- `concern_one_liner` is filled by the human or main agent in Phase 1; **required** before Phase 2 spawn.
- `backup_ref` is set by `redistribute-commits.py --execute`; null otherwise.
- `round_history` is the source of truth for Phase 3's per-round breakdown. The new `decisions` field per round captures the worker evaluator's call.
- `all_rejected_streak` is the coordinator's counter for the 3-consecutive-rejected DONE rule.
- `subagent_started_at` is null until Phase 3 dispatch.
- Phase 5/6/7/8 fields are null until each phase touches the entry.
- `pr_merge_method` is one of `squash` / `merge` / `rebase` per repo policy.

## Status state machine

| State | Set by | Means |
|---|---|---|
| `SPAWNED` | `spawn-review-worktrees.py` | Worktree created, branch pushed to origin, no coordinator dispatched yet. |
| `IN-LOOP` | Main agent on Phase 3 dispatch | Coordinator owns this branch; rounds in progress. |
| `DONE` | Main agent (Phase 3 loop) | Last classifier output had `major == []`, OR 3 consecutive all-rejected rounds. Ready for Phase 5. |
| `CONVERGED-AT-CAP` | Main agent (Phase 3 loop) | Configured `max_rounds_per_branch` exhausted with at least one round of fixes pushed; remaining items captured for the PR body. Ready for Phase 5; PR body documents the deferred items. |
| `CAP-REACHED` | Main agent (Phase 3 loop) | 20 rounds reached with major items still present AND no successful round of pushed fixes (every round had failures). Surface for human; **no Phase 5**. |
| `BLOCKED` | Main agent (Phase 3) OR evaluator (Phase 7) | Persistent ambiguity, oscillation, or contradictions. Surface for human; **no merge**. |
| `FAILED` | Coordinator OR main agent OR any script | Tooling failure (codex, push, validation, evaluator) past retry budget. |
| `PR-OPEN` | PR-Creator (Phase 5) | PR has been opened on the fork; pending Phase 6 wait + Phase 7 evaluation. |
| `PR-EVALUATED` | Evaluator (Phase 7) | Evaluator's decisions JSON written; pending Phase 8 apply. |
| `PR-APPLIED` | Main agent (Phase 8) | Accepted items applied + pushed; pending merge. |
| `MERGED` | Main agent (Phase 8) | PR merged on fork. Ready for Phase 9 cleanup. |

Transitions:

```
                 (created)
                    │
                    ▼
                SPAWNED  ──(main agent enters Phase 3 loop, round 1)──▶  IN-LOOP
                                                                          │
            ┌────────────────────────────┬──────────────────────┬────────┼─────────┬──────────┐
            ▼                            ▼                      ▼        ▼         ▼          ▼
          DONE              CONVERGED-AT-CAP              CAP-REACHED  BLOCKED  FAILED
            │                                                 │      │                │
            │ (Phase 5: PR-Creator dispatched)                └──────┴────────────────┘
            ▼                                                       (no further phases;
        PR-OPEN                                                      surface in deliverable)
            │
            │ (Phase 6: rescue triggered + adaptive wait)
            ▼
        (still PR-OPEN; rescue + bots arrive)
            │
            │ (Phase 7: evaluator sub-agent dispatched)
            ▼
       PR-EVALUATED
            │
            │ (Phase 8: main agent applies)
            │
       ┌────┴─────┐
       ▼          ▼
  PR-APPLIED   BLOCKED  (ambiguous items present)
       │          │
       ▼          ▼
    MERGED   (surface in deliverable)
       │
       ▼
   (Phase 9 cleanup)
```

## Persistence rules

1. **Atomic writes only.** Every write is `tempfile + os.replace` with `flock`. Never `open(path, 'w')` directly. See `parallel-subagent-protocol.md` for the recipe.
2. **One writer per branch entry per phase.** Per branch:
   - `spawn-review-worktrees.py` writes the initial entry.
   - Main agent writes the `IN-LOOP` transition on coordinator dispatch.
   - Coordinator writes terminal status + round_history.
   - PR-Creator writes Phase 5 fields.
   - `trigger-codex-rescue.py` writes rescue_* fields.
   - `await-pr-reviews.py` writes pr_reviews_* fields.
   - Evaluator writes pr_evaluation_* fields.
   - Main agent writes Phase 8 + final fields.
3. **Always update `updated_at`.** Every write touches the entry's timestamp.
4. **Never delete entries during the run.** Mark `cleaned_up: true` in Phase 9; remove the file entirely only after the final tidy audit passes.
5. **schema_version bump on incompatible changes.** This revision uses `v2` (added Phase 5/6/7/8 fields). Older v1 manifests should be migrated or rejected.

## Rendering to the final deliverable

The summary table in the deliverable derives directly from the manifest:

| Manifest field | Table column |
|---|---|
| `branch` | Branch |
| `worktree_path` | Worktree |
| `concern_one_liner` | Concern |
| `rounds` | Rounds |
| `status` | Final status |
| `pr_number` | PR |
| `pr_evaluation_summary.{accepted,rejected,ambiguous}` | Reviews accepted/rejected/ambiguous |
| `pr_merged` | Merged |
| `terminal_reason` + last `round_history` entry | Notes |

The per-branch round-history appendix is rendered from each entry's `round_history` array. The per-PR review evaluation summary is rendered from `pr_evaluation_summary`.

## Recovery from a corrupt manifest

If `audit-review-state.py` reports the manifest is malformed:

1. Look for `<manifest-path>.bak` (atomic-replace leaves no `.bak`, but `redistribute-commits.py` does — check there too).
2. If no backup, reconstruct from round logs + PR review files: scan `<rounds-dir>/*.json`; group by branch slug; rebuild a minimal manifest with `status` inferred from the latest round's classifier output and any `pr-reviews.json` / `pr-evaluation.json` present.
3. As a last resort, abandon the run: `cleanup-worktrees.py --execute --force-abandon <every-branch>`, delete the manifest, restart from Phase 0.

## When to delete the manifest

Phase 9, after the fresh-subagent tidy audit reports TIDY. The manifest is no longer needed; round logs + pr-reviews + pr-evaluation files follow it into deletion.

If the same project re-enters this skill later, a new manifest is created fresh — never resume an old one across sessions.

## Worked example

After Phase 9 cleanup, a complete branch entry might look like:

```json
{
  "branch": "feat/onboarding",
  "concern_one_liner": "Replace interests with marketing-set",
  "worktree_path": "/Users/.../myrepo-wt-feat-onboarding",
  "remote": "origin",
  "head_sha_at_spawn": "abc123...",
  "head_sha_current": "feedface987...",
  "status": "MERGED",
  "rounds": 4,
  "all_rejected_streak": 0,
  "terminal_reason": "no major in round 4",
  "round_history": [
    {"round": 1, "major_n": 3, "decisions": {"accepted": 3, "rejected": 0, "ambiguous": 0}},
    {"round": 2, "major_n": 1, "decisions": {"accepted": 1, "rejected": 0, "ambiguous": 0}},
    {"round": 3, "major_n": 1, "decisions": {"accepted": 0, "rejected": 1, "ambiguous": 0}},
    {"round": 4, "major_n": 0, "decisions": {"accepted": 0, "rejected": 0, "ambiguous": 0}}
  ],
  "pr_number": 42,
  "pr_url": "https://github.com/you/myrepo/pull/42",
  "pr_body_chars": 28412,
  "pr_explicit_questions": 5,
  "rescue_review_id": "cdx-rescue-abc",
  "rescue_status": "completed",
  "pr_reviews_path": "/tmp/codex-review-rounds/feat-onboarding.pr-reviews.json",
  "pr_reviews_terminated_by": "quiet",
  "pr_reviews_wait_seconds": 1080,
  "pr_evaluation_summary": {"total": 28, "accepted": 9, "rejected": 17, "ambiguous": 2},
  "pr_apply_commits": ["abc123", "def456"],
  "pr_merged": true,
  "pr_merged_at": "2026-04-26T11:40:00Z",
  "pr_merge_method": "squash",
  "cleaned_up": true
}
```

Every phase's contribution is visible. The trace is complete: one round of work → one round of review → one round of decision → final merged state.

## Final Deliverable template

Render at end of Phase 9 from manifest state. Each section maps to specific manifest fields — the template below shows where each value comes from. Phase 9 cannot exit until every section is producible.

```markdown
## 🎉 Full skill flow complete — N PRs merged to main (or M surfaced as BLOCKED)

### Final state on <fork-owner>/<repo>
<output of: git log --oneline origin/main~N..origin/main>

E.g.:
a12dd4e fix(antigravity): protobuf sessions + RPC + cache (#51)
cf8d3cd feat(parsers/gemini): JSONL + rewind reconciliation (#52)
…
3f15720 feat(handoff): structured timeline + verbosity controls (#53)

### Per-branch summary
| Branch | Concern | Rounds | Phase 3 status | PR | Phase 7 (a/r/x) | Phase 8a apply | Merged at | Notes |
|---|---|---:|---|---|---|---|---|---|

### Per-PR review breakdown
| PR | codex-rescue (a/r/x) | Copilot (a/r/x) | copilot-pull-request-reviewer (a/r/x) | greptile (a/r/x) | devin-ai-integration (a/r/x) | cubic-dev-ai (a/r/x) | Total accepted | Total ambiguous |
|---|---|---|---|---|---|---|---:|---:|

### What ran across all 10 phases
| Phase | What happened |
|---|---|
| 0 | Pre-flight audit — all scripts present, MISSION_PROTOCOL loaded, /ask-review + /do-review available; manifest path repo-local. |
| 1 | Decomposed N-file dirty tree into M per-concern branches. |
| 2 | M worktrees spawned with `--prep-deps`, M branches pushed, manifest emitted. |
| 3 | K rounds × M codex reviews; main agent evaluated, dispatched M Appliers per round; J fixes applied across rounds. |
| 4 | Merge order computed: foundation, then leaves. |
| 5 | M PR-Creators (throttled ≤4) opened PRs via REST `gh api repos/.../pulls`. |
| 6 | M codex-rescue jobs + M Monitors armed; external bots landed reviews; adaptive 900s base + 3-min quiet windows closed cleanly per PR. |
| 7 | M Evaluator sub-agents used /do-review over gathered streams; produced decisions JSON (≈X items: A accepted, R rejected, U ambiguous). |
| 8a | Main agent direct-applied accepted decisions across M worktrees; validated build+tests; pushed N commits. |
| 8b | Captured `foundation_pre_merge_tip`; squash-merged foundation with `--delete-branch`; rebased leaves with `git rebase --onto`; retargeted leaves to main; merged sequentially with CI-wait. |
| 9 | M worktrees removed, M local branches deleted, M remote branches deleted (mostly via `--delete-branch` in 8b), manifest + round-logs + briefs cleaned; final audit: TIDY. |

### Loop tools that kept this autonomous
- **Monitor** (M instances): per-PR comment poller; emitted one event per new bot/human comment; terminated on `[PR-N-DONE quiet]` or `[PR-N-DONE cap]`.
- **ScheduleWakeup** (X fires): cache-aware 1200-1800s fallback tickers covering the 900s adaptive-wait floor.
- **Agent run_in_background=true** (~K dispatches): Appliers, PR-Creators, Evaluators — each fired a handback notification on completion.
- **Bash run_in_background=true** (~K launches): per-branch codex review jobs, codex-rescue invocations, CI-wait pollers.

### Lessons captured during execution
(Only include genuinely novel learnings — not boilerplate. Examples: rate-limit pivot to REST, squash-merge `--onto` mechanic, brief-templating discipline, `/do-review` decision-only failure mode.)

### Tidy audit
<output from `audit-state.py` + `audit-review-state.py` — both must show CLEAN>
- `git worktree list` → only main
- `git branch -vv` → only main + any BLOCKED branches
- `gh pr list` → only BLOCKED PRs (or empty)

### Per-branch round history (appendix)

#### feat/foo (DONE in 4 rounds, merged as #42)
- Round 1: 3 major (3 accepted) → committed + pushed
- Round 2: 1 major (1 accepted) → committed + pushed
- Round 3: 1 major (0 accepted, 1 rejected) → all-rejected round
- Round 4: no major → DONE
- Phase 8a fixes: abc123, def456 (merged as squash 2026-04-26T11:40:00Z)

#### feat/bar (CONVERGED-AT-CAP at 20 rounds, merged as #43 with deferred items in PR body)
- 20 rounds, 8 accepted, 14 rejected, 0 ambiguous
- Remaining major items in last round: <listed in PR body>

#### feat/baz (BLOCKED — surfaced for human; NOT merged)
- terminal_reason: "ambiguous: <item-id>: <evaluator's question>"
- Suggested human action: <e.g. split into 2 branches, re-run per concern>
```
