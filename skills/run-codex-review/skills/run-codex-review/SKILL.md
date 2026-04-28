---
name: run-codex-review
description: "Use skill if you are running parallel per-branch /codex:review fix-rereview loops with /do-review evaluators, opening PRs via /ask-review, codex rescue, and adaptive multi-bot review evaluation."
---

# Prepare and Run Codex Review

The job: turn a messy repo into a clean per-branch decomposition; converge each branch through Codex's per-round review loop with `/do-review`-evaluated worker sub-agents; open a comprehensive PR per branch via a sub-agent that uses `/ask-review`; trigger `/codex:resc --background --fresh --model gpt-5.5 --effort xhigh` on each PR as a last check; wait adaptively (900s base + 5-min extensions if bots still talking + 3-min quiet to terminate, capped at 30 min) for external review bots (Copilot, Greptile, Devin); dispatch a `/do-review` evaluator sub-agent per PR over all gathered streams; have the main agent apply the evaluator's accepted subset directly using `/do-review` in its own context; merge foundation→leaf on the private fork only; tidy. End state: every branch DONE-merged or surfaced (CAP-REACHED / BLOCKED / FAILED), no stale worktrees, manifest deleted, `audit-review-state.py` exits 0.

This skill **layers on top of** `run-repo-cleanup`. Read that skill's `SKILL.md` first; its references and scripts are canonical for diff-walk, conventional commits, fork safety, worktrees, merge ordering. This skill adds: commit redistribution on committed history; the two-level coordinator+worker inner loop; `/ask-review`-based PR creation by sub-agent; `/codex:resc` orchestration with adaptive wait; multi-source review evaluation via `/do-review` sub-agents; main-agent direct apply; review-aware cleanup.

Every sub-agent in this skill is dispatched per **`~/MISSION_PROTOCOL.md`** — Context Block → Mission Objective → Research & Tool Guidance → BSV Definition of Done → Verification → Failure Protocol → Handback. See `references/mission-protocol-integration.md`. Brief discipline is the lever; without it, parallel sub-agents drift toward mediocre.

## Pinned Defaults

Fill these once per project. If any cell is blank, ask — do not guess.

| Key | Value |
|---|---|
| origin (private fork) | `git@github.com:<owner>/<repo>.git` |
| upstream (read-only) | `git@github.com:<upstream-owner>/<upstream-repo>.git` |
| default base branch | `main` |
| max rounds per branch (Phase 3) | `20` |
| 3-consecutive-all-rejected → DONE | yes |
| worktree path scheme | `../<repo>-wt-<branch-slug>` |
| manifest path | `/tmp/codex-review-manifest.json` |
| round-log dir | `/tmp/codex-review-rounds/` |
| PR body cap (Phase 5, hard) | **50,000 chars (max only; no min)** |
| Codex rescue invocation (Phase 6) | `/codex:resc --background --fresh --model gpt-5.5 --effort xhigh` |
| Wait base (Phase 6) | `900 s` (15 min) |
| Wait quiet window | `180 s` (3 min) |
| Wait extension | `300 s` (5 min) |
| Wait total cap | `1800 s` (30 min) |
| Mission protocol | `~/MISSION_PROTOCOL.md` |
| run-repo-cleanup root | `<install-path>/run-repo-cleanup/` |
| this skill root | `<install-path>/run-codex-review/` |

Repo-local `AGENTS.md` / `CLAUDE.md` / `CONTRIBUTING.md` wins over anything here.

## Non-Negotiable Invariants

1. `origin` = private fork. `upstream` = read-only. Every mutating `gh` call passes `--repo <fork-owner>/<fork-repo>` explicitly. (See `skills/run-repo-cleanup/references/fork-safety.md`.)
2. Read every diff before staging. No `git commit -am`. (See `skills/run-repo-cleanup/references/diff-walk-discipline.md`.)
3. Never `rm` an unknown file. Quarantine to `to-delete/` first. (See `skills/run-repo-cleanup/references/to-delete-folder.md`.)
4. **One worktree per branch. One coordinator per worktree. One fresh worker per round.** No two agents mutate the same branch concurrently.
5. **`/codex:review` always runs `--background`.** Never inline.
6. **20-round hard cap per branch.** Branches converge independently; one capping does not stop siblings.
7. **Never `--force` push** a branch under active review. Stack commits on top.
8. **Never push to upstream. Never touch `main` directly.**
9. **Subagents fix; main agent merges.** Main agent never opens PRs in this workflow either — the PR-Creator sub-agent does.
10. Granularity at the **concern boundary**, not arbitrary. Don't over-split a coherent commit; don't under-split a mixed one.
11. **Never apply review feedback as-is.** Every Codex inner-loop, codex-rescue, copilot, greptile, devin item passes through a `/do-review` evaluator (sub-agent in Phase 3 + Phase 7; main-agent direct in Phase 8). Direct-apply is forbidden. (See `references/review-evaluation-protocol.md`.)
12. **Every sub-agent brief follows MISSION_PROTOCOL Mission Brief Skeleton.** Soft language banned. BSV Definition of Done. Ceilings, not floors. (See `~/MISSION_PROTOCOL.md` and `references/mission-protocol-integration.md`.)
13. **PR creator MUST be a sub-agent.** Main agent never opens PRs in this skill's workflow. PR-Creator uses `/ask-review` skill (Skill tool) — hand-rolling the body is forbidden.
14. **PR body ≤ 50,000 chars (hard cap; max only, no min).** Comprehensive ≠ verbose. The body must contain at least 3 explicit reviewer questions.
15. **Codex rescue triggered immediately after PR creation.** Always `--background --fresh --model gpt-5.5 --effort xhigh`. It runs as Codex's own background sub-agent (not a Claude Agent we dispatch).
16. **Wait window is 900s base + adaptive end + 1800s total cap.** Don't merge before the window closes and the evaluator runs.

## The Ten Phases

```
                dirty tree / mixed-concern branches / N worktrees
                              │
       Phase 0 — Pre-flight audit (state + manifest + orphan worktrees)
                              │
       Phase 1 — Decompose & redistribute commits → per-concern branches
                              │
       Phase 2 — One worktree per branch + push to fork (manifest emitted)
                              │
       Phase 3 — Parallel inner loop (coordinator + per-round worker
                 sub-agents; worker uses /do-review on every Codex item;
                 20-round cap; 3 consecutive all-rejected → DONE)
                              │
       Phase 4 — Convergence report aggregation (main agent reads manifest)
                              │
       (Phases 5–8 sequential per PR, foundation → leaf)
                              │
       Phase 5 — PR-Creator sub-agent uses /ask-review to author
                 comprehensive body (≤ 50k chars, ≥ 3 reviewer questions),
                 opens PR with --repo explicit on the fork
                              │
       Phase 6 — Trigger /codex:resc --background --fresh --model gpt-5.5
                 --effort xhigh on the PR; adaptive wait (900s base +
                 +5min if comments in last 3min + terminate on 3min quiet,
                 30 min total cap); gather all review streams
                              │
       Phase 7 — Evaluator sub-agent uses /do-review on all streams
                 (codex-rescue, copilot, greptile, devin); returns
                 accepted / rejected / ambiguous decisions JSON
                              │
       Phase 8 — Main agent direct: read evaluator's JSON, apply accepted
                 items via /do-review skill in own context, push, merge
                 (or BLOCKED if ambiguous; surface for human)
                              │
       Phase 9 — Tidy & final audit (fresh subagent re-verifies)
                              │
              every branch DONE-merged or surfaced; nothing stale
```

Each phase has a checkpoint. Don't skip forward. If you find yourself tempted to skip — re-audit.

---

## Phase 0 — Pre-flight audit

**Think first**: *What state am I in? Are there orphan review worktrees from a prior session? Any background Codex jobs still running? Any branches mid-loop from a previous run?*

1. `python3 skills/run-repo-cleanup/scripts/audit-state.py` — base audit.
2. `python3 skills/run-repo-cleanup/scripts/list-worktrees.py` — enumerate.
3. `python3 <this-skill>/scripts/audit-review-state.py` — review-loop wrapper. Detects: orphan `*-wt-*` worktrees, stale `/tmp/codex-review-manifest.json`, in-flight Codex background jobs from prior runs, branches with stale round logs.
4. `python3 skills/run-repo-cleanup/scripts/init-to-delete.py` if `.gitignore` is missing the patterns.
5. Verify remotes per `skills/run-repo-cleanup/references/fork-safety.md`.
6. Verify `~/MISSION_PROTOCOL.md` is present and current. Every sub-agent dispatch depends on it.
7. Verify the `/ask-review` and `/do-review` skills are registered. Both are required.

**Gate**: enter Phase 1 only when (a) no in-progress git op, (b) `origin` verified as the fork, (c) `.gitignore` includes `to-delete/` + agent artifacts, (d) no orphan review state from a prior session, (e) MISSION_PROTOCOL + ask-review + do-review available.

**Red flags**:
- "I'll just start fresh and ignore the prior session's manifest." → No. Either resume or clean up explicitly.
- "audit-state.py is enough; skip audit-review-state." → No. Orphan review state is invisible to the base audit.
- "I'll skip the MISSION_PROTOCOL check; the briefs will work without it." → No. The protocol IS the brief discipline.

---

## Phase 1 — Decompose & redistribute commits

**Think first**: *What are the N concerns? For each existing commit on each existing branch, which concern does it serve? Are any commits mixing concerns?*

1. **Dirty tree**: diff-walk every modified/untracked file (`skills/run-repo-cleanup/references/diff-walk-discipline.md`), commit per concern with conventional commits + gitmoji. Move uncertain files to `to-delete/`.
2. **Existing committed work**: for each non-base branch, `git log --oneline --no-merges <base>..HEAD` and `git diff --stat <base>...HEAD`. If commits mix concerns:
   ```bash
   python3 <this-skill>/scripts/redistribute-commits.py --branch <b> --base main           # dry-run plan
   python3 <this-skill>/scripts/redistribute-commits.py --branch <b> --base main --execute # split via interactive rebase + backup ref
   ```
   `--execute` only on **unpublished** commits. For published commits, use the cherry-pick-into-new-branch pattern in `references/commit-redistribution.md`. Never `--force`-push a rewritten published branch.
3. **One concern per branch.** If a single branch holds multiple reviewable topics, split into N branches.
4. **Don't over-split**: a coherent 200-line refactor is one commit, not five. Split only when a commit can't be described in one sentence.

**Gate**: every target branch holds one coherent concern, describable in one sentence. The branch ledger lives in the manifest emitted next phase.

**Red flags**:
- "These commits look fine even though they mix things." → No. Re-read.
- "I'll squash these together and let Codex sort it out." → No. Codex won't fix branch organization.
- "I'll rewrite this published branch's history real quick." → No. Cherry-pick into a new branch instead.

---

## Phase 2 — One worktree per branch + push to fork

**Think first**: *Each branch needs its own physical workspace before any review starts. Each must have a remote ref on `origin` for Codex to review against.*

```bash
python3 <this-skill>/scripts/spawn-review-worktrees.py --branches feat/a feat/b docs/c --execute
```

For each branch the script: creates `../<repo>-wt-<slug>` (or reuses if present and clean), pushes to `origin` with `-u` (refuses if remote != `origin`), appends an entry to the manifest. Verify with `python3 skills/run-repo-cleanup/scripts/list-worktrees.py`.

**Gate**: every branch has a worktree, every branch is at `origin/<branch>`, manifest written.

**Red flags**:
- "I'll review from the main worktree and switch branches." → No. Sub-agents will collide.
- "I'll push later, just before opening the PR." → No. Codex needs a remote ref now.

---

## Phase 3 — Parallel inner loop (coordinator + per-round worker)

**Think first**: *Each branch is independent. Each gets a coordinator sub-agent that drives the loop; per round it dispatches a fresh worker sub-agent that uses `/do-review` to evaluate Codex's items before applying. The main agent dispatches and watches; it does not edit during the loop.*

For each branch in the manifest, **main agent dispatches one coordinator sub-agent** (parallel across branches) per the brief in `references/parallel-subagent-protocol.md`. The coordinator runs the loop; per round it dispatches a fresh worker.

**Coordinator brief skeleton** (full template in `parallel-subagent-protocol.md`):
- Context: branch, worktree, manifest path, MISSION_PROTOCOL pointer, worker brief template location.
- Mission: drive `<branch>`'s manifest entry to a terminal state with full round history.
- DoD: status ∈ {DONE, CAP-REACHED, BLOCKED, FAILED}; rounds match round_history; terminal_reason set; remote tip matches manifest's head_sha_current.

**Coordinator's loop** (canonical pseudocode in `references/per-branch-fix-loop.md`):

```
round = 1
all_rejected_streak = 0

while round <= 20:
    run-codex-review.py → review JSON
    classify-review-feedback.py → exit 0 (≥1 major) or 1 (no major)

    if classifier exit 1:
        manifest.status = "DONE"; terminal_reason = "no major in round <N>"; break

    # Dispatch FRESH worker sub-agent for THIS round
    Agent(prompt=worker_brief_for_round, subagent_type="general-purpose")

    # Worker uses /do-review on every major item, applies accepted, pushes
    # Hands back: { accepted: N, rejected: M, ambiguous: K }

    if worker.failed:
        manifest.status = "FAILED"; break

    if worker.ambiguous and persistent_ambiguity:
        manifest.status = "BLOCKED"; break

    if worker.accepted == 0 and worker.rejected > 0:
        all_rejected_streak += 1
        if all_rejected_streak >= 3:
            manifest.status = "DONE"; terminal_reason = "3 consecutive all-rejected; Codex stuck"; break
    else:
        all_rejected_streak = 0

    round += 1

if round > 20:
    manifest.status = "CAP-REACHED"
```

**Worker brief skeleton** (full template in `parallel-subagent-protocol.md`):
- Context: branch, worktree, round number, round JSON path, classifier output, prior round summaries.
- Mission: every major item has a decision (accepted / rejected / ambiguous via `/do-review`); accepted items are committed (one concern per commit) and pushed; round log updated.
- DoD: every item has a decision; `git diff --cached` empty; validation exits 0; `git push origin <branch>` succeeded.

Main agent monitors with:

```bash
python3 <this-skill>/scripts/loop-status.py --watch
```

Live table: branch, rounds, last status, state. **No editing while sub-agents are running.**

**Gate**: every branch in the manifest in a terminal state (`DONE` / `CAP-REACHED` / `BLOCKED` / `FAILED`).

**Red flags**:
- "Let me check progress mid-loop and skip --background once." → No.
- "Good enough after 3 rounds; ship it." → No (the classifier + worker decide).
- "Let me have one worker fix two rounds." → No (workers are fresh per round).
- "Let me have the coordinator do the work itself." → No (coordinator orchestrates; worker acts).
- "I'll skip /do-review for the obvious items." → No. Direct-apply violates invariant 11.
- "The classifier is being noisy, let me bypass it." → No — adjust `major-vs-minor-policy.md` if the policy is wrong.
- "I'll skip the validation step before re-review." → No. Codex can't tell your syntax error from a real bug.

---

## Phase 4 — Convergence report (main agent)

**Think first**: *What did each coordinator achieve? Which branches are mergeable; which need to surface?*

Once every branch is terminal, the main agent:

1. Reads `/tmp/codex-review-manifest.json`.
2. Builds the deliverable's first table (Branch | Worktree | Concern | Rounds | Final status).
3. Recomputes merge order with `python3 skills/run-repo-cleanup/scripts/suggest-merge-order.py --base main`. Override the heuristic for semantic dependencies; write the rationale into the manifest.
4. Surfaces non-`DONE` branches: each with its remaining major feedback and a suggested human action.

**Gate**: ordered list of mergeable (`DONE`) branches written into manifest.merge_order.

---

## Phase 5 — Comprehensive PR creation (sub-agent uses `/ask-review`)

**Think first**: *Each PR is opened by a fresh sub-agent dispatched by the main agent. The sub-agent uses the `/ask-review` skill to author a comprehensive body that explicitly asks the right reviewer questions. Body is capped at 50,000 chars (max only; no min). Main agent NEVER opens PRs in this workflow.*

Process branches sequentially in foundation→leaf order from manifest.merge_order.

For each `DONE` branch:

1. **Main agent dispatches a PR-Creator sub-agent** with the brief in `references/parallel-subagent-protocol.md`.
2. Brief includes: the branch's worktree, all known commits (subjects), all known files (paths), diff stats, round history with major/accepted/rejected/ambiguous counts, and any deferred-ambiguous items from Phase 3.
3. PR-Creator sub-agent:
   - Reads all known changes + the actual diff (to catch unknown changes).
   - Reads any AGENTS.md / CLAUDE.md / CONTRIBUTING.md inside the worktree.
   - Invokes `/ask-review` (Skill tool with `skill='ask-review'`).
   - Verifies body length ≤ 50,000 chars (`wc -c`).
   - Verifies body contains at least 3 explicit reviewer questions.
   - Saves body to `/tmp/pr-body-<branch-slug>.md`.
   - Opens PR: `gh pr create --repo <fork-owner>/<repo> --base <base> --head <branch> --title "..." --body-file <path>`.
   - Verifies URL is on fork: `gh pr view <number> --repo <fork>/<repo> --json url,baseRefName`.
   - Updates manifest entry: `pr_number`, `pr_url`, `pr_title`, `pr_body_path`, `pr_body_chars`, `pr_explicit_questions`, `pr_opened_at`.
   - Hands back to main agent.

**Gate**: PR exists on fork with `--repo` explicit; body ≤ 50k chars and has ≥ 3 explicit reviewer questions; manifest updated.

**Red flags**:
- "I'll just open the PR myself." → No. Invariant 13: PR creator MUST be a sub-agent.
- "I'll hand-roll the body — `/ask-review` is overhead." → No. Invariant 13: hand-rolling forbidden.
- "Body is over 50k, let me trim by removing the per-commit section." → No. Trim via `/ask-review`'s flags or split the PR.
- "Skip the explicit reviewer questions." → No. The user's spec says questions are critical.
- "Let me open this on upstream as a courtesy." → No. Fork-only invariant.

---

## Phase 6 — Codex rescue + adaptive review window

**Think first**: *Hand the PR link to Codex's own background sub-agent (`/codex:resc`). Then wait — adaptively — for codex-rescue + external bots (Copilot, Greptile, Devin) to land their reviews. The wait pattern: 900s base + 5-min extensions if bots are still talking + terminate on 3-min quiet + 30-min safety cap.*

For each PR opened in Phase 5, sequentially:

1. **Trigger codex rescue**:
   ```bash
   python3 <this-skill>/scripts/trigger-codex-rescue.py --pr <number> --branch <b>
   ```
   This invokes `codex review --rescue --background --fresh --model gpt-5.5 --effort xhigh --pr <number>` inside the branch's worktree. Codex rescue is **Codex's own background sub-agent** (not a Claude Agent); we hand it the PR link and Codex's infrastructure spawns the review job. Manifest gets `rescue_review_id`, `rescue_started_at`, `rescue_status: "running"`.

2. **Wait + gather**:
   ```bash
   python3 <this-skill>/scripts/await-pr-reviews.py --pr <number> --branch <b> \
     --base-wait 900 --quiet-window 180 --extension 300 --total-cap 1800
   ```

   The script waits 900s base, then loops:
   - Fetch all reviews/comments from PR via `gh api`.
   - If newest comment is older than 180s → terminate ("quiet").
   - If total elapsed ≥ 1800s → terminate ("total_cap").
   - Else wait min(extension, time_remaining_to_cap), re-check.

   Output: `<rounds-dir>/<slug>.pr-reviews.json` with sources unified across `codex-rescue`, `copilot`, `greptile`, `devin`, plus any human reviewers.

**Gate**: gathered JSON written; manifest entry has `pr_reviews_path`, `pr_reviews_terminated_by`, `pr_reviews_wait_seconds`.

**Red flags**:
- "Skip the wait, merge fast." → No. The wait is the value.
- "Wait less than 900s by default." → No. Bots arriving at minute 13 would be missed.
- "Run codex rescue inline (not --background)." → No. Blocks the agent for 1–5 min.
- "Trigger codex rescue twice for extra coverage." → No. One per PR.

---

## Phase 7 — Per-PR evaluator sub-agent (uses `/do-review`)

**Think first**: *One evaluator sub-agent per PR reads all gathered review streams and decides accepted / rejected / ambiguous for every item using the `/do-review` skill. The evaluator is read-only on the worktree — it produces decisions; main agent applies in Phase 8.*

For each PR:

1. **Main agent dispatches an Evaluator sub-agent** with the brief in `references/parallel-subagent-protocol.md`.
2. Brief includes: PR number, URL, branch, worktree path, gathered reviews JSON path, the evaluation taxonomy (`references/review-evaluation-protocol.md`).
3. Evaluator sub-agent:
   - Reads the gathered JSON.
   - For each item across all sources:
     - Reads cited code in the worktree.
     - Uses `/do-review` skill (Skill tool with `skill='do-review'`).
     - Decides accepted / rejected / ambiguous per the rubric in `review-evaluation-protocol.md`.
   - Cross-checks for cross-source contradictions (e.g., "extract" vs "inline" on the same line) → both items go ambiguous.
   - Writes decisions JSON to `<rounds-dir>/<slug>.pr-evaluation.json` per the schema.
   - **Does NOT modify the worktree, comment on the PR, or merge.**
   - Hands back: counts, summary by source, contradictions.

**Gate**: every item has a decision; JSON conforms to schema; cross-source contradictions flagged in BOTH affected items; `git status` in worktree returns empty (no drift).

**Red flags**:
- "Trust copilot's items blindly." → No. Evaluator first.
- "Auto-resolve cross-source contradictions." → No. Mark both ambiguous; surface for human.
- "Dispatch a second evaluator for sanity-check." → No. One evaluator per PR.
- "Skip items the evaluator marked rejected." → No. The evaluator decided.

---

## Phase 8 — Main-agent direct apply + merge

**Think first**: *The evaluator's structured output is in main agent's context. Re-dispatching to a sub-agent for apply would re-load context unnecessarily. Main agent applies directly using `/do-review` in own context — the user's principle: "do-review is healthier when answers come straight back".*

For each PR:

1. **Main agent reads** `<rounds-dir>/<slug>.pr-evaluation.json`.
2. **For each accepted item** (deduplicated across sources):
   - Read cited code (Read tool).
   - Compose the fix per evaluator's rationale.
   - Sanity-check via `/do-review` skill in main agent's context (Skill tool with `skill='do-review'`).
   - Apply via Edit (with diff-walk discipline).
   - `git diff --cached` (verify only intended hunks).
   - `git commit -m "<emoji> <type>(<scope>): apply <source>'s <item-id>"`.
3. **For each ambiguous item**: do NOT apply. Record in BLOCKED list for the PR.
4. **After all accepted items applied**:
   ```bash
   git -C <worktree> push origin <branch>
   ```
   Wait for CI green.
5. **If ambiguous list non-empty**: mark PR `BLOCKED` in manifest with `terminal_reason` citing the items. Surface in deliverable. Do NOT merge.
6. **Else**: `gh pr merge <number> --repo <fork>/<repo> --squash` (or per repo policy).
7. **Optional — fresh PR**: if accepted items are too divergent for in-place application (per `post-pr-review-protocol.md`'s rubric), open a new PR via Phase 5 redux for that branch.

After merge: `git fetch --all --prune`. If a sibling DONE branch overlaps the just-merged base, rebase it onto the new `main` (only safe because sibling has no review in flight at this point).

**Gate**: PR is `MERGED` (manifest field set), or `BLOCKED` with surfaced items.

**Red flags**:
- "Let me dispatch a sub-agent for apply too." → No. Phase 8 is main-agent direct.
- "Apply ambiguous items just in case." → No. Ambiguous = human-in-the-loop.
- "Re-trigger Codex review after apply." → No. Phase 8's commits are post-evaluator.
- "Merge the BLOCKED PR anyway." → No. The classifier said major, the evaluator said ambiguous. Human decides.

---

## Phase 9 — Tidy & final audit

**Think first**: *What state did I start in? Have I returned to it, plus the intended delta — nothing more, nothing less?*

1. Cleanup worktrees:
   ```bash
   python3 <this-skill>/scripts/cleanup-worktrees.py --base main --execute
   ```
   Refuses worktrees whose branch is not merged unless `--force-abandon <branch>` is passed.
2. Retire merged branches:
   ```bash
   python3 skills/run-repo-cleanup/scripts/retire-merged-branches.py --base main --execute
   ```
3. **Dispatch a fresh subagent** for an independent re-audit (per `skills/run-repo-cleanup/references/post-pr-verification.md`). The subagent runs read-only:
   - `python3 skills/run-repo-cleanup/scripts/audit-state.py` — must exit 0.
   - `python3 <this-skill>/scripts/audit-review-state.py` — must exit 0.
   - `git worktree list` — only main.
   - `git branch -vv` — only `main` and any open-PR (BLOCKED) branches.
   - `gh pr list --repo <fork>/<repo>` — matches expected.
   - `gh pr list --repo <upstream>/<upstream-repo> --author @me` — empty.
4. Delete `/tmp/codex-review-manifest.json` and `/tmp/codex-review-rounds/`.

**Gate**: subagent reports TIDY. `audit-review-state.py` exits 0.

**Red flags**:
- "I'll clean up next time." → No. Tidy is binary.
- "I'll keep the worktrees in case." → No. Stale worktrees are debris.

---

## Major vs Minor Feedback Policy

The classifier's `major[]` is a **candidate list for evaluation**, not an "apply-immediately" list. The Phase 3 worker (and Phase 7 evaluator) run `/do-review` on each candidate to decide accepted / rejected / ambiguous.

Loop on (major candidates):
- correctness bugs, runtime stability, data integrity, security, regressions, hygiene that hides bugs, review-blocking branch structure.

Do not loop on (minor):
- formatting, naming, style preferences, doc-only polish, speculative perf, scope creep.

Default-when-ambiguous (classifier): **major** (conservative).
Default-when-ambiguous (evaluator): **ambiguous** (surface for human).

Repo-local `CONTRIBUTING.md` / `AGENTS.md` may **tighten** the policy. Override is in repo policy, never per-branch judgement calls.

Full policy + worked examples + the classifier-vs-evaluator role split: `references/major-vs-minor-policy.md` and `references/review-evaluation-protocol.md`.

## Failure Modes & Recovery

| Failure | Recovery |
|---|---|
| `CAP-REACHED` (Phase 3) | Log remaining major feedback; surface for human. Don't auto-merge. |
| `BLOCKED` (Phase 3 oscillation / contradictions) | Halt branch; human decides split vs override vs accept-as-known. |
| `FAILED` (Phase 3 tooling) | Retry once at wrapper, 3× at sub-agent, else surface. |
| Coordinator/worker crash | Heartbeat detection via manifest mtime; redispatch up to 2x. |
| Lost worktree | `git worktree prune` + recreate from manifest; resume from `rounds + 1`. |
| `/ask-review` unavailable (Phase 5) | FAIL the PR-Creator dispatch. Do NOT hand-roll. Surface for human. |
| PR body > 50k chars (Phase 5) | Trim via `/ask-review` flags; if still too long, split the branch. Never delete reviewer questions. |
| Accidental upstream PR | Stop everything; recover per `skills/run-repo-cleanup/references/fork-safety.md`; rotate any leaked secrets. |
| Codex rescue invocation fails (Phase 6) | Manifest marks `rescue_status: "failed"`; `await-pr-reviews.py` proceeds; codex-rescue stream just empty. |
| External bots missing in repo | Wait window terminates fast (no comments → quiet); evaluator handles single source / no source gracefully. |
| Wait still receiving comments at total_cap | Terminate; gather what we have; surface late-arrivers in deliverable. |
| Evaluator marks everything ambiguous (Phase 7) | PR is BLOCKED. Surface for human (likely PR is too broad; consider split). |
| Evaluator's accepted fix breaks CI (Phase 8) | Revert; mark item ambiguous; surface. Don't auto-retry the same fix. |
| Cross-source contradiction can't be resolved | Both items ambiguous; PR BLOCKED; human picks. |
| Brief defect (sub-agent produces garbage) | Read brief; apply discipline checklist (`parallel-subagent-protocol.md`); revise; redispatch. The brief is the lever. |

Full recipes: `references/failure-recovery.md`.

## Final Deliverable

```markdown
## Per-branch summary
| Branch | Worktree | Concern | Rounds | Phase 3 status | PR | Phase 7 (a/r/x) | Merged | Notes |
|---|---|---|---:|---|---|---|---|---|

## Per-PR review breakdown
| PR | codex-rescue (a/r/x) | copilot (a/r/x) | greptile (a/r/x) | devin (a/r/x) | Total accepted | Total ambiguous |
|---|---|---|---|---|---:|---:|

## Tidy audit
<output from audit-state.py + audit-review-state.py — both must show CLEAN>

## Per-branch round history (appendix)
### feat/foo (DONE in 4 rounds)
- Round 1: 3 major (3 accepted) → committed + pushed
- Round 2: 1 major (1 accepted) → committed + pushed
- Round 3: 1 major (0 accepted, 1 rejected) → all-rejected round
- Round 4: no major → DONE

### feat/foo PR #42 — MERGED
- codex-rescue:  5 items (3 accepted, 2 rejected)
- copilot:       8 items (1 accepted, 6 rejected, 1 ambiguous)
- greptile:     12 items (4 accepted, 7 rejected, 1 ambiguous)
- devin:         3 items (1 accepted, 2 rejected)
- Cross-source contradictions: 0
- Phase 8 commits: abc123, def456
- Merged via squash at 2026-04-26T11:40:00Z

### feat/bar (CAP-REACHED at 20 rounds)
- 20 rounds, 8 accepted, 14 rejected, 0 ambiguous
- Remaining major items in last round: <description>
- Recommendation: split into 2 branches, re-run per concern.
```

The format is rendered from manifest entries; see `references/branch-decomposition-ledger.md`.

## Smell Test — forbidden internal thoughts

If any of these fires, stop and re-run `python3 <this-skill>/scripts/audit-review-state.py`:

**Phase 3:**
- "I'll just squash these reviews into one round."
- "Good enough after 3 rounds, ship it."
- "I'll skip /do-review for the obvious items."
- "Let me have one worker fix two rounds."
- "Let me have the coordinator do the work itself."
- "I'll skip the validation step before re-review."

**Phase 5:**
- "I'll just open the PR myself."
- "I'll hand-roll the body — /ask-review is overhead."
- "Skip the explicit reviewer questions."
- "The body is over 50k, let me trim by removing the per-commit section."

**Phase 6:**
- "Skip the wait, merge fast."
- "Run codex rescue inline."
- "Wait less than 900s — the bots are fast."

**Phase 7:**
- "Trust copilot blindly because it's usually right."
- "The evaluator is overhead; just apply what the bots say."
- "Auto-resolve the cross-source contradiction."

**Phase 8:**
- "Let me dispatch a sub-agent for the apply step too."
- "Apply the ambiguous items just in case."
- "Re-trigger Codex review after apply."
- "Merge the BLOCKED PR anyway."

**Cross-phase:**
- "I'll start fresh and ignore the prior session's manifest."
- "I'll write the brief later — this dispatch is simple."
- "Soft DoD ('clean code') — agents understand."
- "I can skip the failure protocol — the agent will figure it out."

## How to Think — meta-cognition per phase

- **Phase 0**: *What surprises me? Are MISSION_PROTOCOL + ask-review + do-review available?*
- **Phase 1**: *Can each branch be described in one sentence?*
- **Phase 2**: *Worktree AND remote ref on origin for each branch?*
- **Phase 3**: *Coordinator dispatched per branch; per round it dispatches a fresh worker that uses /do-review. Have I stepped back?*
- **Phase 4**: *Which branches are mergeable? What's the merge order rationale?*
- **Phase 5**: *PR opened by sub-agent using /ask-review? Body ≤ 50k? ≥ 3 reviewer questions?*
- **Phase 6**: *Codex rescue triggered? Wait window in progress with adaptive end?*
- **Phase 7**: *Evaluator decided every item via /do-review? Cross-source contradictions flagged?*
- **Phase 8**: *Applying directly via /do-review? Ambiguous items surfaced (BLOCKED), not silently merged?*
- **Phase 9**: *Returned to clean state plus the intended delta?*

See `references/thinking-steering.md` for full red-flag list. See `skills/run-repo-cleanup/references/agent-thinking-steering.md` for the general decompose/order/verify pattern. See `references/mission-protocol-integration.md` for brief-writing doctrine.

## Scripts

| Phase | Script | Type | One-liner |
|---|---|---|---|
| 0 | `scripts/audit-review-state.py` | new | Wrapper over `audit-state.py`; adds review-loop checks. |
| 0 | `skills/run-repo-cleanup/scripts/audit-state.py` | reused | Base audit. |
| 0 | `skills/run-repo-cleanup/scripts/list-worktrees.py` | reused | Enumerate worktrees. |
| 0 | `skills/run-repo-cleanup/scripts/init-to-delete.py` | reused | Idempotent `to-delete/` setup. |
| 1 | `scripts/redistribute-commits.py` | new | Split mixed-concern commits via interactive rebase + backup ref. |
| 2 | `scripts/spawn-review-worktrees.py` | new | Create worktrees, push to fork, emit manifest. |
| 3 | `scripts/run-codex-review.py` | new | Wrap `/codex:review --background`; normalize output to JSON. |
| 3 | `scripts/classify-review-feedback.py` | new | Apply major/minor policy; produce `{major[], minor[]}`. |
| 3 | `scripts/loop-status.py` | new | Live table of branch round status (read-only). |
| 4 | `skills/run-repo-cleanup/scripts/suggest-merge-order.py` | reused | Foundation→leaf heuristic. |
| 5 | `/ask-review` skill (Skill tool) | external | Author comprehensive PR body. |
| 6 | `scripts/trigger-codex-rescue.py` | new | Trigger `/codex:resc --background --fresh --model gpt-5.5 --effort xhigh`. |
| 6 | `scripts/await-pr-reviews.py` | new | Adaptive 900s wait + gather all review streams. |
| 7 | `/do-review` skill (Skill tool) | external | Evaluator's primary instrument. |
| 8 | `/do-review` skill (Skill tool) | external | Main agent's apply-time instrument. |
| 9 | `scripts/cleanup-worktrees.py` | new | Remove review worktrees; refuses unmerged unless `--force-abandon`. |
| 9 | `skills/run-repo-cleanup/scripts/retire-merged-branches.py` | reused | Delete merged local + remote branches. |

All new scripts: Python 3 stdlib only, dry-run by default where mutating, paired `.md` doc.

## References

| File | Type | One-liner |
|---|---|---|
| `references/mission-protocol-integration.md` | new | How every sub-agent dispatch in this skill complies with `~/MISSION_PROTOCOL.md`. |
| `references/codex-review-contract.md` | new | What `/codex:review --background` returns; how to invoke; how to read. |
| `references/per-branch-fix-loop.md` | new | Phase 3 coordinator + worker pattern; round counter; 20-cap; state machine. |
| `references/parallel-subagent-protocol.md` | new | The 4 sub-agent mission brief templates: coordinator, worker, PR-creator, evaluator. |
| `references/review-evaluation-protocol.md` | new | The "never apply review as-is" rule; accepted/rejected/ambiguous taxonomy + JSON schema. |
| `references/post-pr-review-protocol.md` | new | Phase 6 codex rescue + adaptive wait + gather. |
| `references/commit-redistribution.md` | new | Split mixed-concern commits with backup ref; published vs unpublished. |
| `references/branch-decomposition-ledger.md` | new | Manifest schema (v2) with Phase 5/6/7/8 fields. |
| `references/major-vs-minor-policy.md` | new | Classifier triggers + worked examples + role split with evaluator. |
| `references/failure-recovery.md` | new | All 10 phases' failure modes + recovery recipes. |
| `references/thinking-steering.md` | new | Red-flag thoughts per phase + decompose-step-back-watch reflex. |
| `references/reuse-from-run-repo-cleanup.md` | new | Index of which run-repo-cleanup files cover which concerns. |

Reused references (NOT duplicated):
- `skills/run-repo-cleanup/references/pre-flight-audit.md`
- `skills/run-repo-cleanup/references/diff-walk-discipline.md`
- `skills/run-repo-cleanup/references/conventional-commits.md`
- `skills/run-repo-cleanup/references/fork-safety.md`
- `skills/run-repo-cleanup/references/to-delete-folder.md`
- `skills/run-repo-cleanup/references/worktree-and-stash.md`
- `skills/run-repo-cleanup/references/multi-worktree-merge-order.md`
- `skills/run-repo-cleanup/references/pr-body-template.md`
- `skills/run-repo-cleanup/references/post-pr-verification.md`
- `skills/run-repo-cleanup/references/receiving-review-patterns.md`
- `skills/run-repo-cleanup/references/agent-thinking-steering.md`
- `skills/run-repo-cleanup/references/scripts-and-docs-layout.md`

External: `~/MISSION_PROTOCOL.md` (the brief-writing doctrine).

## Bottom Line

Audit → decompose → worktree-per-branch → push to fork → parallel inner loop with coordinator + per-round `/do-review`-evaluating worker (cap 20) → main agent dispatches PR-Creator sub-agent that uses `/ask-review` to author body (≤ 50k, ≥ 3 reviewer questions) → trigger `/codex:resc` and adaptive 900s wait for external bots → evaluator sub-agent uses `/do-review` on all gathered streams → main agent applies accepted items directly via `/do-review` in own context → merge or BLOCKED → tidy. Every sub-agent brief follows MISSION_PROTOCOL. Every review item passes through `/do-review`. Direct-apply forbidden. PR creation is sub-agent-only. Fork-only, ever. One discipline, sixteen invariants, zero exceptions.
