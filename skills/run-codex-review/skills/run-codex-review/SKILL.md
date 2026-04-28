---
name: run-codex-review
description: "Use skill if you are running parallel per-branch /codex:review fix-rereview loops with /do-review evaluators, opening PRs via /ask-review, codex rescue, and adaptive multi-bot review evaluation."
---

# Prepare and Run Codex Review

The job: turn a messy repo into a clean per-branch decomposition; converge each branch through Codex's per-round review loop driven by **main agent as coordinator** (with per-round Applier sub-agents and main-agent `/do-review` evaluation); open a comprehensive PR per branch via a sub-agent that uses `/ask-review`; trigger codex rescue on each PR (`/codex:resc` slash for chat, or `scripts/trigger-codex-rescue.py` wrapping `codex-companion.mjs task --background` for programmatic loops); wait adaptively (900s base + 5-min extensions if bots still talking + 3-min quiet to terminate, capped at 30 min) for external review bots (Copilot, Greptile, Devin, cubic-dev-ai, copilot-pull-request-reviewer); dispatch a `/do-review` Evaluator sub-agent per PR over all gathered streams; have the main agent apply the evaluator's accepted subset directly via Edit + per-concern commits (Phase 8a); merge foundation→leaf with `git rebase --onto` mechanics for squash-merged stacks (Phase 8b); tidy. End state: every branch MERGED or surfaced (BLOCKED / CONVERGED-AT-CAP / CAP-REACHED / FAILED), no stale worktrees, no stale local/remote branches, manifest deleted, `audit-review-state.py` exits 0.

This skill **layers on top of** `run-repo-cleanup`. Read that skill's `SKILL.md` first; its references and scripts are canonical for diff-walk, conventional commits, fork safety, worktrees, merge ordering. This skill adds: commit redistribution on committed history; the **main-agent-coordinator + per-round Applier** inner loop with `/do-review` evaluation in main's context; `/ask-review`-based PR creation by sub-agent; codex-rescue orchestration with adaptive wait; multi-source review evaluation via Evaluator sub-agents; main-agent direct apply (Phase 8a) followed by foundation→leaf serial merge (Phase 8b); review-aware cleanup with hard exit gate.

Every sub-agent in this skill is dispatched per **`~/MISSION_PROTOCOL.md`** — Context Block → Mission Objective → Research & Tool Guidance → BSV Definition of Done → Verification → Failure Protocol → Handback. See `references/mission-protocol-integration.md`. Brief discipline is the lever; without it, parallel sub-agents drift toward mediocre.

## Slash commands vs shell commands — invocation matrix

This skill drives four slash commands. They are NOT shell programs. The codex plugin (`openai-codex/codex`) marks `/codex:review`, `/codex:status`, `/codex:result` as `disable-model-invocation: true` — **sub-agents physically cannot call them via `Skill(...)`**. `/codex:resc` requires the `Agent` tool which is not available to forked general-purpose sub-agents.

Read this matrix once and stop guessing.

| Command | Main agent | Worker / PR-Creator / Evaluator sub-agent |
|---|---|---|
| `/codex:review` | User-typed slash in chat for ad-hoc reviews. **For Phase 3 programmatic loops, dispatch the wrapper instead** (see worker row). | **`scripts/run-codex-review.py --branch X --base Y --worktree Z`**. The wrapper discovers `codex-companion.mjs` automatically (env-var first, then version-glob fallback), invokes it, normalizes the JSON output, and writes the round log. Sub-agents call the wrapper; the wrapper calls the companion script. |
| `/codex:resc` | (a) `/codex:resc --fresh --model gpt-5.5 --effort xhigh --pr <n>` typed as slash for 1-2 PRs. (b) **`scripts/trigger-codex-rescue.py --pr <n> --branch <b> --worktree <wt> --prompt-file <p>`** for programmatic loops with N PRs. Both paths run `codex-companion.mjs task --background` internally. | Not available. Phase 6 trigger is main-agent-only (the slash uses the `Agent` tool; the wrapper queues a Codex worker that forked sub-agents can't see). |
| `/ask-review` | `Skill(skill="ask-review", args="…")` | `Skill(skill="ask-review", args="…")` — used by PR-Creator sub-agents in Phase 5. |
| `/do-review` | `Skill(skill="do-review", args="…")` — Phase 8 main-agent direct apply. | **Not used in Phase 3 worker briefs.** Decisions are pre-made before worker dispatch (see invariant 11 + Phase 3 worker brief). Workers are appliers, not evaluators. |

**Forbidden in every context:**

- `codex review …` from Bash — there is no such CLI surface; the underlying `codex` binary has no `--background` flag.
- Any "shim" wrapping the codex binary because a flag is "missing".
- `node …/codex-companion.mjs review …` invoked DIRECTLY from a sub-agent brief or main-agent loop — that's what the wrapper is for. The wrapper does discovery, normalization, manifest-update, and round-log path computation. Calling the companion script directly bypasses all of that.
- Reading `scripts/run-codex-review.py` thinking it's a stub — **it isn't**. It's the canonical wrapper. Production traces of agents writing `/tmp/codex-review-runner.py` parallel implementations were a workaround for an earlier broken version; that version has been rewritten.

**Plugin discovery (handled inside the wrapper, documented for transparency):**

1. `${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs` — set by Claude Code when the plugin is loaded.
2. Latest semver-sorted version under `~/.claude/plugins/cache/openai-codex/codex/<version>/scripts/codex-companion.mjs` — fallback for environments without the env var.
3. If neither resolves: wrapper exits 127 with install instructions (https://github.com/openai/codex-plugin-cc).

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
| manifest path | `<repo-root>/.codex-review-manifest.json` (gitignored). **Never `/tmp/...`** — concurrent skill sessions in different repos clobber each other when both default to `/tmp/codex-review-manifest.json`. |
| round-log dir | `<repo-root>/.codex-review-rounds/` (gitignored). Same reasoning. |
| PR body cap (Phase 5, hard) | **50,000 chars (max only; no min)** |
| Codex rescue invocation (Phase 6) | Two first-class paths: (a) `/codex:resc --fresh --model gpt-5.5 --effort xhigh --pr <n>` typed as slash directive in chat, OR (b) `scripts/trigger-codex-rescue.py --pr <n> --branch <b> --worktree <wt> --prompt-file <p>` for programmatic loops (wraps `codex-companion.mjs task --background --write --fresh --effort xhigh`). |
| Single-owner repo mode | If `git remote -v` shows only `origin` and no `upstream`, treat origin as both source and target. Fork-safety invariant becomes vacuous. **Auto-detect in Phase 0; do not ask the user.** |
| Manifest path collision | Default is repo-local; collisions across sessions are structurally impossible. If a stale `/tmp/codex-review-manifest.json` exists from an older skill version, ignore it. |
| Wait base (Phase 6) | `900 s` (15 min) |
| Wait quiet window | `180 s` (3 min) |
| Wait extension | `300 s` (5 min) |
| Wait total cap | `1800 s` (30 min) |
| Codex review wall-clock cap (Phase 3 per-round) | `1500 s` (25 min). Codex can hang on remote tools (codebase-search APIs, etc.); the wrapper enforces this and exits non-zero with `terminal_reason: "review-hang past wall-clock cap"`. Main agent retries once, then marks the round FAILED. |
| Phase 5 PR-Creator parallelism cap | `4 simultaneous`. GitHub's GraphQL budget is shared with `gh pr create` body uploads; opening 9+ in parallel exhausts it. Throttle batches; PR-Creator brief MUST instruct the sub-agent to use REST (`gh api repos/<owner>/<repo>/pulls -f title=… -f body=@<file> -f base=… -f head=…`) not `gh pr create` (which uses GraphQL). |
| Mission protocol | `~/MISSION_PROTOCOL.md` |
| run-repo-cleanup root | `<install-path>/run-repo-cleanup/` |
| this skill root | `<install-path>/run-codex-review/` |

Repo-local `AGENTS.md` / `CLAUDE.md` / `CONTRIBUTING.md` wins over anything here.

## Authorization rule (read this once, do not re-litigate)

If the user's prompt named the full flow ("execute full skill flow", "run all phases", "do the whole pipeline", "full rigor", or invoked `/run-codex-review` without scoping), authorization is **persistent across all 10 phases**. Proceed phase-to-phase **without checkpoint, without option menus, without cost-warning prefaces, without asking "how would you like to proceed"**.

Exception — pause **only** if:
- A genuinely destructive operation requires confirmation that local context cannot resolve (e.g., a force-push the user did not authorize, a non-fast-forward push to a branch with prior history main agent did not write).
- A skill invariant has been violated and there is no clean recovery (e.g., codex plugin unavailable; manifest collision that auto-namespacing did not catch).
- The user typed a stop signal (`stop`, `pause`, `wait`, etc.) since the last action.

Never pause to:
- Estimate cost or wall-time ("this will take 4-7 hours and burn many tokens"). The user already authorized.
- Present an option menu (Full / Phase-N-only / Foundation-only / Pause). The flow is already chosen.
- Ask "would you like me to proceed?" The answer was given when the skill was invoked.
- Justify a deviation. Either follow the skill or hand back BLOCKED with `terminal_reason` and one sentence on what you'd do differently.

End-of-phase reports must be **one sentence**: "Phase X complete; entering X+1." Verbose state tables, per-branch summaries, and decision menus belong only in the **Final Deliverable** at the end of Phase 9.

## Non-Negotiable Invariants

1. **Repo-mode auto-detected, not asked.** Two modes:
    - **Two-remote** (origin = private fork, upstream = canonical): every mutating `gh` call passes `--repo <fork-owner>/<fork-repo>` explicitly; never push to upstream. (See `skills/run-repo-cleanup/references/fork-safety.md`.)
    - **Single-owner** (only `origin`, no upstream): origin is the target; `gh` calls still pass `--repo <owner>/<repo>` for explicitness, but the "never touch upstream" rule is vacuously satisfied.
    Detect from `git remote -v` in Phase 0. **Do not present options or ask the user when the detection is unambiguous.**
2. Read every diff before staging. No `git commit -am`. (See `skills/run-repo-cleanup/references/diff-walk-discipline.md`.)
3. Never `rm` an unknown file. Quarantine to `to-delete/` first. (See `skills/run-repo-cleanup/references/to-delete-folder.md`.)
4. **One worktree per branch. Main agent is the only coordinator (across all branches). One fresh Applier sub-agent per round per branch.** No two agents mutate the same branch concurrently. (The older "Coordinator sub-agent per worktree" pattern was dropped — long-lived sub-agents drift past harness session limits; main-agent-as-coordinator is empirically reliable. See `references/parallel-subagent-protocol.md` "Coordinator role".)
5. **Codex review runs synchronously per round.** `codex-companion.mjs review` ignores `--background`; per-branch parallelism comes from concurrent subprocess invocations across branches, not from a background flag. (`task --background` IS honored — that's how Phase 6 codex rescue works; see Phase 6.)
6. **20-round hard cap per branch.** Branches converge independently; one capping does not stop siblings.
7. **Never `--force` push** a branch under active review. Stack commits on top.
8. **Never push to upstream. Never touch `main` directly.**
9. **Subagents fix; main agent merges.** Main agent never opens PRs in this workflow either — the PR-Creator sub-agent does.
10. Granularity at the **concern boundary**, not arbitrary. Don't over-split a coherent commit; don't under-split a mixed one.
11. **Never apply review feedback as-is — but the evaluator is NOT the worker.** Every Codex/copilot/greptile/devin item passes through `/do-review` evaluation. The role split:
    - **Phase 3**: main agent runs the classifier on the round-log JSON, then evaluates each major item using `Skill(do-review)` in main's own context (one decision per item). Workers receive PRE-DECIDED accepted-fix specs and apply them mechanically. **Worker briefs do not mention `/do-review`** — that framing causes decision-only failure (workers produce excellent decision JSON but never apply or push).
    - **Phase 7**: dedicated Evaluator sub-agent runs `/do-review` on every PR review item from all sources.
    - **Phase 8**: main agent applies the evaluator's accepted subset directly using `/do-review` in own context.
    Direct-apply without prior `/do-review` evaluation is forbidden in every phase. But pushing eval onto Phase 3 workers is also forbidden — workers are appliers, not evaluators.
12. **Every sub-agent brief follows MISSION_PROTOCOL Mission Brief Skeleton.** Soft language banned. BSV Definition of Done. Ceilings, not floors. (See `~/MISSION_PROTOCOL.md` and `references/mission-protocol-integration.md`.)
13. **PR creator MUST be a sub-agent.** Main agent never opens PRs in this skill's workflow. PR-Creator uses `/ask-review` skill (Skill tool) — hand-rolling the body is forbidden.
14. **PR body ≤ 50,000 chars (hard cap; max only, no min).** Comprehensive ≠ verbose. The body must contain at least 3 explicit reviewer questions.
15. **Codex rescue triggered immediately after PR creation.** Always `--background --fresh --model gpt-5.5 --effort xhigh`. It runs as Codex's own background sub-agent (not a Claude Agent we dispatch).
16. **Wait window is 900s base + adaptive end + 1800s total cap.** Don't merge before the window closes and the evaluator runs.
17. **Use the right invocation surface per context.** Each command has explicit valid paths; do not guess.
   - **Phase 3 codex review** (per round, per branch): call `scripts/run-codex-review.py --branch X --base Y --worktree Z`. The wrapper discovers `codex-companion.mjs` (env-var first, then version-glob), invokes it synchronously, normalizes output, writes the round log. `/codex:review` is `disable-model-invocation: true` so sub-agents cannot dispatch the slash command — the wrapper IS their path. Main agent uses the wrapper too in programmatic loops.
   - **Phase 6 codex rescue** (per PR): two first-class paths from main agent — (a) `/codex:resc --fresh --model gpt-5.5 --effort xhigh --pr <n>` typed as slash directive for 1-2 PRs, OR (b) `scripts/trigger-codex-rescue.py --pr <n> --branch <b> --worktree <wt> --prompt-file <p>` for programmatic loops with N PRs. The wrapper internally calls `codex-companion.mjs task --background --write --fresh --effort xhigh` — same code path the slash command runs. Sub-agents cannot trigger rescue (no `Agent` tool in forked context).
   - `/ask-review`, `/do-review` are model-invocable → both main and sub-agents call via `Skill(...)`.
   - **Never** invoke `codex` directly from Bash (no `--background` CLI flag exists). **Never** invoke `node …/codex-companion.mjs …` directly from a brief — the wrappers do that, plus discovery, normalization, manifest update, and round-log path computation. **Never** write a parallel `/tmp/codex-review-runner.py` — that's what the production wrapper now does. **Never** invent a slash-command path that contradicts this matrix.

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
                 (codex-rescue, copilot, copilot-pull-request-reviewer, greptile, devin, cubic-dev-ai); returns
                 accepted / rejected / ambiguous decisions JSON
                              │
       Phase 8a — Main agent direct: read evaluator's JSON, apply accepted
                 items, validate, push (or BLOCKED if ambiguous; surface).
                 Apply order across PRs is irrelevant. /do-review re-eval
                 is opt-in; the evaluator's JSON is the authority.
                              │
       Phase 8b — Foundation→leaf strict serial merge: wait CI green per PR;
                 merge; rebase remaining leaves onto new main with
                 --force-with-lease. Foundation must succeed first.
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
4. **Auto-detect repo mode** from `git remote -v`:
   - Only `origin` exists → **single-owner mode**. Set `manifest.repo_mode = "single-owner"`. Skip the fork-safety options dialog. Do NOT ask the user about fork semantics.
   - Both `origin` and `upstream` exist → **two-remote mode**. Verify per `skills/run-repo-cleanup/references/fork-safety.md`.
5. **Pin manifest path repo-local.** This session's manifest is `<repo-root>/.codex-review-manifest.json`; round-log dir is `<repo-root>/.codex-review-rounds/`. Add both to `.gitignore` if not already there. **Do NOT use `/tmp/...`** — concurrent skill sessions across repos clobber each other when both default to /tmp. Pass `--manifest <repo-root>/.codex-review-manifest.json` to every script invocation. If a stale `/tmp/codex-review-manifest.json` exists from an older skill version, leave it alone — do not delete, do not edit.
6. `python3 skills/run-repo-cleanup/scripts/init-to-delete.py` if `.gitignore` is missing the patterns.
7. Verify `~/MISSION_PROTOCOL.md` is present and current. Every sub-agent dispatch depends on it.
8. Verify the `codex:review`, `codex:resc`, `ask-review`, and `do-review` skills are registered (`Skill(...)` callable). All four are required. If any is missing, surface to the user and stop — do not invent a shim.

**Gate**: enter Phase 1 only when (a) no in-progress git op, (b) repo mode auto-detected (single-owner or two-remote), (c) manifest path resolved (namespaced if a collision was detected), (d) `.gitignore` includes `to-delete/` + agent artifacts, (e) no orphan review state from a prior session, (f) MISSION_PROTOCOL + the four required skills available.

**Red flags**:
- "I'll just start fresh and ignore the prior session's manifest." → No. Either resume or namespace this session's manifest. Do not delete the other session's state.
- "I'll rebuild the manifest by hand because it has stale entries." → No. Auto-namespace and proceed.
- "audit-state.py is enough; skip audit-review-state." → No. Orphan review state is invisible to the base audit.
- "I'll skip the MISSION_PROTOCOL check; the briefs will work without it." → No. The protocol IS the brief discipline.
- "There's no upstream — let me ask the user how to set up fork semantics." → No. Single-owner mode is auto-detected. Proceed.
- "Let me run `codex --help` to confirm the CLI is ready." → No. Slash commands are not shell programs. The dispatch surface for sub-agents is `node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs"` (existence check is enough); for main agent the dispatch surface is the user-typed slash. Do not probe the underlying CLI.

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
python3 <this-skill>/scripts/spawn-review-worktrees.py --branches feat/a feat/b docs/c --execute --prep-deps
```

For each branch the script: creates `../<repo>-wt-<slug>` (or reuses if present and clean), pushes to `origin` with `-u` (refuses if remote != `origin`), appends an entry to the manifest. Verify with `python3 skills/run-repo-cleanup/scripts/list-worktrees.py`.

**Pre-flight worktree dependencies (`--prep-deps`).** If the project requires installed deps (`node_modules`, `.venv`, etc.) for the build/test that Phases 3 and 8 will run, install them in each worktree NOW — not lazily mid-Phase-3 or mid-Phase-8. The flag detects the package manager from repo files (`pnpm-lock.yaml` → `pnpm install`; `package-lock.json` → `npm ci`; `bun.lockb` → `bun install`; `requirements.txt` → `pip install -r requirements.txt`; `Cargo.toml` → no-op, cargo handles it; etc.) and runs the corresponding install in every newly-created worktree. Default is OFF; flip to ON for any repo whose validate command needs an install step. Production trace showed a worktree throwing `error TS2307: Cannot find module 'fs'` on first build because deps were never installed — `--prep-deps` makes that moment unreachable.

**Gate**: every branch has a worktree, every branch is at `origin/<branch>`, manifest written, deps installed (when `--prep-deps` was used).

**Red flags**:
- "I'll review from the main worktree and switch branches." → No. Sub-agents will collide.
- "I'll push later, just before opening the PR." → No. Codex needs a remote ref now.
- "Skip `--prep-deps`; workers will install lazily as needed." → Acceptable for repos where the validate command works without an install step (Rust, Go, plain-Python). Forbidden for npm/pnpm/bun/pip projects that the validate command needs `node_modules`/`.venv` for — Phase 8 surprise costs more than upfront install.

---

## Phase 3 — Parallel inner loop (main agent coordinates; appliers apply)

**Think first**: *Main agent IS the coordinator across all branches. It dispatches per-round APPLIER sub-agents in parallel — one per branch, fresh each round. Decisions about each Codex item are made by main agent BEFORE worker dispatch, using `Skill(do-review)` in main's own context. Workers receive pre-decided fix specs and execute mechanically. They do not evaluate.*

The coordinator-as-subagent pattern in older versions of this skill is dropped: in practice, sub-agents that need to live for hours (one per branch × convergence loop) are unreliable in Claude Code. Main agent owns the round-cadence directly and dispatches short-lived, single-purpose appliers.

**Per-round flow main agent runs** (parallel across all branches in flight):

```
round = 1
per branch: all_rejected_streak = 0

while any branch has round <= 20 and not in terminal state:

    # 1. Launch codex review for every active branch in parallel.
    #    Sub-agents cannot Skill(codex:review) — disable-model-invocation.
    #    Use the wrapper script (it bridges to codex-companion.mjs review --json).
    for branch in active_branches:
        bg: python3 <this-skill>/scripts/run-codex-review.py \
              --branch <b> --base <base> --worktree <wt> \
              --output <rounds-dir>/<slug>.<round>.json

    # 2. As each review completes:
    classify-review-feedback.py → exit 0 (≥1 major) or 1 (no major)

    if classifier exit 1:
        manifest.status = "DONE"; terminal_reason = "no major in round <N>"; continue

    # 3. Main agent EVALUATES each major item with Skill(do-review)
    #    in own context. Produces decisions JSON: per item, accepted/rejected/ambiguous.
    decisions = []
    for item in major_items:
        cited_code = read(<worktree>/<file>, around <line>, ±25 lines)
        decision = Skill(do-review, args="--item <body> --code <cited_code>")
        decisions.append(decision)

    # 4. Per branch: dispatch ONE applier sub-agent with the decisions baked in.
    #    Worker brief is in references/parallel-subagent-protocol.md.
    #    Worker DoD is BINARY: commits pushed to origin/<branch>; tests pass.
    #    Worker brief NEVER mentions /do-review (decisions are pre-made).
    Agent(prompt=applier_brief_with_decisions, subagent_type="general-purpose")

    # 5. Worker hands back: { applied: N, pushed: bool, validation: pass/fail }.
    if not worker.pushed:
        manifest.status = "FAILED"; terminal_reason = "applier failed to push"
        continue

    if all decisions were rejected (worker.applied == 0, worker.rejected > 0):
        all_rejected_streak += 1
        if all_rejected_streak >= 3:
            manifest.status = "DONE"; terminal_reason = "3 consecutive all-rejected; Codex stuck"
            continue
    else:
        all_rejected_streak = 0

    round += 1  # for this branch

per branch: if round > 20:
    manifest.status = "CAP-REACHED"
```

**Why the role split (read this once, do not re-litigate):**

If the worker brief says "evaluate via `/do-review`, then apply", workers stop at the evaluation step ~100% of the time. The /do-review framing pulls them into evaluator-mode and "Verdict: apply" feels like the deliverable. Splitting evaluation (main agent) from application (worker, with explicit fix specs and binary push DoD) makes workers reliably push. This is empirically verified across multiple runs.

**Applier brief skeleton** (full template in `parallel-subagent-protocol.md`):
- Context: branch, worktree, round number, base ref, prior rounds' commit SHAs.
- Mission: apply N pre-decided fixes (each spelled out with file:line + intended code shape), one concern per commit, validate, push.
- Hard constraints: NEVER invoke `/do-review`. NEVER propose alternative fixes. NEVER stop at "Verdict: apply" — apply is the deliverable.
- DoD (binary, verifiable): N new commits on `origin/<branch>`; `git -C <wt> rev-parse origin/<branch>` matches local HEAD; validation passes; `git -C <wt> log <base>..HEAD --oneline` shows the new commits.

Main agent monitors with:

```bash
python3 <this-skill>/scripts/loop-status.py --watch
```

Live table: branch, rounds, last status, state. **No editing while sub-agents are running.**

**Gate**: every branch in the manifest in a terminal state.

### Convergence taxonomy (the only valid terminal states)

| State | Meaning | When set | PR? |
|---|---|---|---|
| `DONE` | No major items in the latest round (classifier exit 1). | Round N classifier returned no major. | Yes — open PR. |
| `CONVERGED-AT-CAP` | Configured `max_rounds_per_branch` exhausted **with at least one round of fixes pushed**. Remaining items go in PR body as known-deferred. | Round counter ≥ cap; `len(round_history) ≥ 1`; latest classifier still exit 0 but Applier ran successfully. | Yes — open PR with deferred items in body. |
| `CAP-REACHED` | 20-round hard cap (or configured cap) hit with **no convergence at all** (every round still has major items, no progress). | Round counter ≥ 20; same classifier outcome round-after-round. | No — surface for human (likely needs branch split). |
| `BLOCKED` | Persistent ambiguous items, oscillation, contradictions; safe automated convergence not possible. | 3+ rounds of all-rejected (Codex stuck) reclassifies as `DONE`; persistent ambiguous reclassifies as `BLOCKED`. | No — surface. |
| `FAILED` | Tooling crash past retry budget, codex plugin unavailable, Applier failed to push. | Any infrastructure gate that the retries did not recover. | No — surface. |

**Do not invent additional states.** If a situation does not fit any of the five above, the skill is wrong (file an issue) — do NOT invent `DONE-PRAGMATIC`, `READY-ENOUGH`, or similar. Pick `BLOCKED` if you genuinely cannot pick from the taxonomy, with a `terminal_reason` describing the mismatch.

**Red flags**:
- "Let me check progress mid-loop." → No. Workers update the manifest atomically; read it.
- "Good enough after 3 rounds; ship it." → No (the classifier decides DONE).
- "Let me have one worker fix two rounds." → No (workers are fresh per round).
- "Let me write the worker brief telling it to `/do-review` each item itself." → **No.** The /do-review framing causes systematic decision-only failure (verified across runs). Main agent evaluates; worker applies.
- "I'll dispatch a coordinator subagent per branch like the older docs said." → No. Main agent IS the coordinator. The coordinator subagent role was dropped; sub-agents that live for hours are unreliable.
- "I'll skip /do-review evaluation for the obvious items." → No. Direct-apply (without prior decision) violates invariant 11.
- "The classifier is being noisy, let me bypass it." → No — adjust `major-vs-minor-policy.md` if the policy is wrong.
- "I'll skip the worker's validation step before push." → No. Codex can't tell your syntax error from a real bug.
- "Round-2 found new items but I'm tired; let me invent DONE-PRAGMATIC and ship." → No. Apply round-2 fixes; if budget is binding, set `CONVERGED-AT-CAP` per the convergence taxonomy and proceed to PR — do not invent off-spec terminal states.

---

## Phase 4 — Convergence report (main agent)

**Think first**: *What did each coordinator achieve? Which branches are mergeable; which need to surface?*

Once every branch is terminal, the main agent:

1. Reads `<repo-root>/.codex-review-manifest.json` (the repo-local default; pass `--manifest <path>` if a custom location was used).
2. Builds the deliverable's first table (Branch | Worktree | Concern | Rounds | Final status).
3. Recomputes merge order with `python3 skills/run-repo-cleanup/scripts/suggest-merge-order.py --base main`. Override the heuristic for semantic dependencies; write the rationale into the manifest.
4. Surfaces non-`DONE` branches: each with its remaining major feedback and a suggested human action.

**Gate**: ordered list of mergeable (`DONE`) branches written into manifest.merge_order.

---

## Phase 5 — Comprehensive PR creation (sub-agent uses `/ask-review`)

**Think first**: *Each PR is opened by a fresh sub-agent dispatched by the main agent. The sub-agent uses the `/ask-review` skill to author a comprehensive body that explicitly asks the right reviewer questions. Body is capped at 50,000 chars (max only; no min). Main agent NEVER opens PRs in this workflow.*

**Throttling**: dispatch ≤4 PR-Creators in parallel. Opening 9+ in parallel exhausts GitHub's GraphQL budget (verified in production traces). The PR-Creator brief MUST instruct the sub-agent to use **REST endpoints for body uploads** (`gh api repos/<owner>/<repo>/pulls -f title=… -f body=@<file> -f base=… -f head=…`), NOT `gh pr create` (which uses GraphQL). When a handback says "rate-limited", check `gh api rate_limit --jq '.resources.graphql.reset'` for the Unix-timestamp reset; if main agent is in `/loop` dynamic mode, `ScheduleWakeup(delaySeconds=<reset_in - now + 60>, ...)`; otherwise queue that branch's redispatch behind the next batch.

Process branches sequentially in foundation→leaf order from manifest.merge_order, but dispatch the PR-Creators in parallel batches of 4.

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
   - **Opens PR via REST endpoint** (avoids GraphQL rate-limit blast in parallel dispatches):
     ```bash
     gh api -X POST repos/<fork-owner>/<repo>/pulls \
            -f title="<title>" \
            -f head="<branch>" \
            -f base="<base>" \
            -F body=@/tmp/pr-body-<branch-slug>.md
     ```
     **Do NOT use `gh pr create`** — it uses GraphQL by default, which has a separate ~5000/hour budget that's quickly exhausted by parallel PR creation (verified in production: 9 parallel `gh pr create` saturates GraphQL while REST core is barely touched). The REST endpoint above uses the core budget. Both produce equivalent PRs.
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

**Think first**: *Hand the PR link to Codex's own background sub-agent (`/codex:resc`). Then wait — adaptively — for codex-rescue + external bots (Copilot, Greptile, Devin, cubic-dev-ai) to land their reviews. The wait pattern: 900s base + 5-min extensions if bots are still talking + terminate on 3-min quiet + 30-min safety cap.*

For each PR opened in Phase 5, sequentially:

1. **Trigger codex rescue.** Two sanctioned paths (pick by context):

   **A. Interactive (1-2 PRs):** type `/codex:resc --fresh --model gpt-5.5 --effort xhigh --pr <number>` in chat.

   **B. Programmatic loop (N PRs in parallel — Phase 6 default):**
   ```bash
   Bash(run_in_background=True):
     cd <worktree-path> && \
     node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" task \
          --write --fresh --effort xhigh \
          "<comprehensive prompt for PR #<n>>"
   ```
   This is the **same code path** `/codex:resc` runs internally; both invoke `codex-companion.mjs task`. In a programmatic loop, calling it directly is cleaner than typing N slash-command directives.

   Codex rescue is **Codex's own background sub-agent** (not a Claude Agent we dispatch). Manifest gets `rescue_review_id`, `rescue_started_at`, `rescue_status: "running"`. NEVER invoke `codex review --rescue …` from Bash (no such CLI surface). NEVER write a "shim" — both invocation paths are first-class.

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

## Phase 8a — Main-agent direct apply (per-PR sequential; cross-PR order irrelevant)

**Think first**: *The evaluator's structured output is in main agent's context. Apply one PR at a time; main agent reads the evaluation JSON, applies each accepted item, validates, pushes. Apply order across PRs doesn't matter — each branch is its own worktree. Merge order is enforced in 8b.*

For each PR with `<repo>/.codex-review-rounds/pr-<n>.evaluation.json`:

1. **Main agent reads** the evaluation JSON. Confirm:
   - `accepted` count > 0 (else mark `apply_status: "skipped-no-accepted"` and proceed to next PR).
   - `ambiguous` count > 0 → mark PR `BLOCKED` in manifest with `terminal_reason: "ambiguous: <item-id>: <evaluator's question>"`. **Skip apply for this PR's accepted items too** — partial-apply ships unreviewed code with a half-decided intent. Surface in deliverable, move to next PR.
2. **For each accepted item** (deduplicated across sources, preserving the first-seen rationale):
   - Read cited code at `<worktree>/<file>` around `<line>` (Read tool, ±25 lines for context).
   - Apply the fix per evaluator's intended-shape via Edit.
   - **If the intended-shape doesn't apply cleanly** (file moved, line shifted, current shape mismatch): DO NOT improvise. Record `apply_failed_after_evaluation: <item-id>` in manifest. Continue with remaining items. Surface at end of Phase 8a — the human decides re-evaluate or accept-as-known.
   - **Stage by concern from the start**: `git -C <worktree> add <files-for-this-concern>`. Do NOT stage everything then `git restore --staged .` to peek and restage — that's wasted overhead per PR. Diff-walk per concern from the first add.
   - `git -C <worktree> diff --cached` (verify only intended hunks).
   - `git -C <worktree> commit -m "<emoji> <type>(<scope>): <subject> (#<pr>)"`. Note the `(#<pr>)` suffix for traceability.
3. **Commit-grouping rule**: tightly-coupled small fixes to the same file may share one commit IF the message lists each concern as a bullet. Example:
   ```
   🐛 fix(parsers/copilot): hardening pass (#47)

   - Distinct sourceIds for inline tool requests
   - toolName carry-through on execution_complete
   - Dedup statSync in extractLastEventTimestamp
   ```
   For unrelated concerns, split into separate commits. **One concern per commit is the default**; combining is an exception that requires the bullets-in-message accountability.
4. **Validate** before push: `pnpm run build && pnpm test` (or repo-equivalent per `AGENTS.md`/`CONTRIBUTING.md`). Three failure modes:
   - **Build fails** (compile error, type error, syntax error from your edit) → revert the offending commit, mark item `apply_failed_validation`, surface — do not retry blindly with a different fix.
   - **Test fails on a NEW assertion that the fix should pass** (real regression) → revert, mark item ambiguous, surface.
   - **Test fails on an EXISTING assertion that asserts the OLD behavior the fix is intended to change** → this is a legitimate test-fixture update. Update the test (or fixture data) to match the new intended behavior in the SAME commit (or amend). Re-run validate. Do NOT revert. Example from production: a fix changed legacy session id format from `legacy:<basename>` to `legacy:<rel-path>` to disambiguate basename collisions across subdirectories. The existing test asserted the old format; updating the test fixture to match the new format was the correct response, not a revert.

   When in doubt between "real regression" and "legitimate test-fixture update": **read the test's intent**. If the test was protecting against the regression the evaluator's accepted fix introduces, it's a real regression — revert. If the test was asserting an arbitrary detail of the OLD behavior that the evaluator explicitly intended to change (and the evaluator's rationale documents the change), it's a fixture update — update it.
5. **Push**: `git -C <worktree> push origin <branch>` (no `--force`).
6. **`/do-review` sanity-check is OPTIONAL and OFF by default.** The Evaluator already used `/do-review` in Phase 7; re-running per item in Phase 8 is double-eval. Reserve for the rare case where main agent's reading of the cited code disagrees with the evaluator's rationale — when borderline, sanity-check before push; otherwise skip.

Process PRs in any order in 8a (foundation-first OR leaves-first OR interleaved are all fine). Phase 8b enforces merge order.

**Phase 8a gate**: every non-BLOCKED PR has new commits pushed; manifest has `apply_status: "applied"` per branch; ambiguous-flagged items recorded; `apply_failed_after_evaluation` items recorded for human surface.

**Red flags (8a)**:
- "Let me dispatch a sub-agent for apply too." → No. Phase 8 is main-agent direct.
- "Apply ambiguous items just in case." → No. Ambiguous = human-in-the-loop. The whole PR is BLOCKED.
- "Apply some accepted items even though others are ambiguous on the same PR." → No. Defer the entire PR.
- "Re-trigger Codex review after apply." → No. Phase 8's commits are post-evaluator.
- "Phase 8 evaluator's intended-shape doesn't apply cleanly; let me improvise." → No. Mark `apply_failed_after_evaluation`, surface for human.
- "Stage all files, peek with `git diff --cached`, then `git restore --staged .` to re-stage by concern." → No. Diff-walk per concern from the start.
- "Re-do `/do-review` per item even when evaluator already accepted with high confidence." → No. Default-skip; the evaluator's JSON is the authority.

---

## Phase 8b — Merge in foundation→leaf strict serial

**Think first**: *Apply is done. Now merge in dependency order with squash-merge-aware leaf rebases.*

The full merge recipe (foundation pre-merge tip capture, `git rebase --onto` for leaves, retargeting via `gh pr edit --base main`, sequential merge with CI-wait between, `--delete-branch` on merge) is documented in detail in **`references/post-pr-review-protocol.md` "Phase 8b — merge in foundation→leaf strict serial"**. Follow that recipe verbatim. Key points to keep in this skill body:

- **Capture foundation's pre-merge tip BEFORE merging foundation** (`foundation_tip=$(git -C <foundation-worktree> rev-parse HEAD)`). Required for the `git rebase --onto origin/main <foundation_tip> <leaf>` math below.
- **Foundation must succeed first.** If foundation CI fails, STOP — leaves are based on foundation; do not merge any of them. Surface foundation BLOCKED.
- **Squash-merging foundation collapses N foundation commits into 1 commit on main with a different SHA.** Plain `git rebase origin/main` on leaves conflicts on every foundation hunk. Use `git rebase --onto origin/main <foundation_tip> <leaf-branch>` to skip the duplicated history.
- **Retarget each leaf** (`gh pr edit <leaf-pr> --base main`) before merging — leaves were originally based on foundation.
- **`gh pr merge --squash --delete-branch`** (the `--delete-branch` flag halves Phase 9 cleanup).
- **`gh pr merge --auto` works for foundation, unreliable for leaves on divergent stacks.** Use sequential explicit merge with CI-wait between.
- **`--force-with-lease`, NOT `--force`** when pushing rebased leaves.

### Phase 8b hard exit gate

**Phase 8b does NOT exit until every non-BLOCKED PR is MERGED.** `gh pr list --repo <fork>/<repo>` should show ONLY BLOCKED or `apply_failed_after_evaluation` branches. If a PR is neither and isn't merged, 8b is incomplete — re-attempt the merge (in `/loop` mode, `ScheduleWakeup(delaySeconds=600)` and re-check). Do NOT proceed to Phase 9 with un-resolved PRs.

### Red flags (8b)

- "Merge foundation before CI green." → No. CI-wait is mandatory.
- "Foundation CI failed — merge the leaves anyway." → No. Halt all leaf merges; surface foundation BLOCKED.
- "Plain `git rebase origin/main` the leaves." → No. `--onto <foundation_tip>` is non-negotiable for squash-merged stacks.
- "Skip capturing `foundation_pre_merge_tip`." → No. Capture BEFORE merging foundation; the local HEAD may move after.
- "Skip retargeting leaves to main." → No. PR `--base` is independent of the rebased branch.
- "Use `gh pr merge --auto` to chain leaf merges." → No. Sequential explicit merge with CI-wait between.
- "Force-push leaves with `--force` instead of `--force-with-lease`." → No. `--force-with-lease` is the safety mechanism.
- "Merge the BLOCKED PR anyway." → No. Human decides.
- "Open a fresh PR for the apply_failed_after_evaluation items." → Acceptable but optional; surface for human first. Don't auto-cycle.

---

## Phase 9 — Tidy & final audit

**Think first**: *What state did I start in? Have I returned to it, plus the intended delta — nothing more, nothing less? No stale worktree, no stale local branch, no stale remote branch, no stale temp file.*

### Cleanup checklist (do ALL four; the hard gate fails if any is skipped)

1. **Worktrees** — `python3 <this-skill>/scripts/cleanup-worktrees.py --base main --execute`. Removes every `<repo>-wt-*` worktree whose branch is merged. Refuses unmerged worktrees unless `--force-abandon <branch>`.
2. **Local branches** — `python3 skills/run-repo-cleanup/scripts/retire-merged-branches.py --base main --execute`. `git branch -d <name>` for each fully-merged branch; leaves BLOCKED / `apply_failed_after_evaluation` alone.
3. **Remote branches** — only for branches that survived 8b without `--delete-branch`. Same script with `--remote --execute`.
4. **Temp files** — `rm -f <repo>/.codex-review-manifest.json{,.lock} && rm -rf <repo>/.codex-review-rounds/ && rm -f /tmp/applier-brief-*.md /tmp/evaluator-brief-*.md /tmp/pr-creator-brief-*.md /tmp/*-brief-template*.md`. (Legacy `/tmp/codex-review-manifest.json{,.lock}` from older runs: remove only if its `repo_root` matches the current session's; leave alone if pointing elsewhere.)

### Independent re-audit (mandatory)

Dispatch a fresh sub-agent for read-only re-audit (per `skills/run-repo-cleanup/references/post-pr-verification.md`). The audit runs `audit-state.py` + `audit-review-state.py` + verifies: `git worktree list` shows only main; `git branch -vv` shows only main + BLOCKED branches; `gh pr list` shows only BLOCKED PRs; `gh api repos/<fork>/branches` shows only main + BLOCKED; `.codex-review-*` files absent; `/tmp/*-brief-*.md` absent.

### Phase 9 hard exit gate (the "no stale anything" condition)

Phase 9 does NOT exit until ALL six are true:

1. Every non-BLOCKED branch is **MERGED** to main.
2. Every review **worktree** is removed.
3. Every merged **local branch** is deleted.
4. Every merged **remote branch** is deleted.
5. Every **temp brief / manifest / round-log** is cleaned.
6. Independent re-audit sub-agent reports **TIDY**.

If any fails, Phase 9 is incomplete. In `/loop` dynamic mode, `ScheduleWakeup(delaySeconds=600)` and re-check on transient failures (CI still pending, rate-limit blocking branch deletion). On structural failures (BLOCKED PRs), surface the exact list and stop — human takes over.

### Red flags (Phase 9)

- "I'll clean up next time." → No. Tidy is binary.
- "Local branches deleted; remote branches don't matter." → No. Stale remote branches accumulate; future runs see them as "in-flight" and refuse to spawn worktrees with the same name.
- "`git worktree remove --force <path>` everything." → No. `cleanup-worktrees.py` refuses unmerged worktrees by default to protect un-pushed work; use `--force-abandon <branch>` only when explicitly intended.
- "Skip the independent re-audit." → No. Fresh-context audit catches state drift main agent's own context can mask.
- "Skip cleaning `/tmp/*-brief-*.md`." → No. Future runs may create briefs with the same names and read stale data.

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

The wrap-up at end of Phase 9. **Phase 9 cannot exit until every section below is producible from manifest state** — this is the "all merged or surfaced" hard exit gate.

The full Final Deliverable template (per-branch summary, per-PR review breakdown across 6 bot sources, what-ran-across-all-10-phases table, loop-tools used, per-branch round-history appendix) lives in `references/branch-decomposition-ledger.md` "Final Deliverable template" — render it from manifest entries at end of Phase 9.

### "All merged or surfaced" hard exit gate

The Final Deliverable can be produced ONLY when every branch in the manifest reaches a terminal state:

| Terminal state | Acceptable for clean exit? |
|---|---|
| `MERGED` (with `merged_at` timestamp) | ✅ happy path |
| `BLOCKED` (with `terminal_reason` set) | ✅ surfaced for human; clean exit |
| `apply_failed_after_evaluation` (with item list) | ✅ surfaced for human |
| `CONVERGED-AT-CAP` (round budget hit; fixes pushed; deferred items in PR body) | ✅ surfaced; clean exit if PR is merged or BLOCKED |
| `CAP-REACHED` (round budget hit; no fixes pushed) | ✅ surfaced for human |
| `FAILED` (tooling crash past retry budget) | ✅ surfaced for human |
| `IN-LOOP` / `SPAWNED` / unset / `applying` | ❌ incomplete; re-attempt or surface the specific blocker |

If any branch is in an incomplete state when Phase 9 audit runs, **the audit fails**. Re-attempt the merge for that branch (in `/loop` mode, `ScheduleWakeup(delaySeconds=600)` and re-check). Do NOT produce the Final Deliverable until every branch is terminal.

## Smell Test — forbidden internal thoughts

If any of these fires, stop and re-run `python3 <this-skill>/scripts/audit-review-state.py`. The full annotated list lives in `references/thinking-steering.md` "Forbidden inventions"; the highest-leverage entries are below.

**Phase 3 (loop discipline)**:
- "Squash these reviews into one round" / "Good enough after 3 rounds, ship it" → no; classifier + main-agent decisions are the arbiters of DONE.
- "Let me dispatch a Coordinator sub-agent per branch like the older docs said" → main agent IS the coordinator. Long-lived sub-agents drift past harness session limits.
- "Let me write the worker brief asking it to `/do-review` then apply" → highest-leverage failure pattern. Workers stop at decision-only. Decisions stay with main agent; workers are appliers.
- "Let me have one worker fix two rounds" → workers are fresh per round.

**Phase 5-7 (PR + bots + evaluator)**:
- "I'll open the PR myself" / "Hand-roll the body — `/ask-review` is overhead" → invariant 13: PR creator MUST be a sub-agent using `/ask-review`.
- "Skip the wait" / "Wait less than 900s" → 900s base + adaptive end is the contract.
- "Trust copilot blindly" / "The evaluator is overhead" → every item passes through `/do-review` evaluation.

**Phase 7-8 (apply + merge)**:
- "Apply the ambiguous items just in case" / "Half-apply: ship the accepted items, defer the ambiguous ones" → ambiguous = the WHOLE PR is BLOCKED.
- "Skip CI-wait" → CI-wait is mandatory in 8b before any merge.
- "Foundation CI failed — merge the leaves anyway" → foundation is their base; halt all leaf merges.
- "Plain `git rebase origin/main` the leaves after foundation squash-merged" → no; `git rebase --onto origin/main <foundation_pre_merge_tip> <leaf>` is non-negotiable for squash-merged stacks.
- "Skip retargeting leaves to main" / "Use `gh pr merge --auto` to chain leaf merges" → retarget via `gh pr edit --base main`; sequential explicit merge with CI-wait between.
- "Stage everything, peek with `git diff --cached`, then `git restore --staged .`" → diff-walk per concern from the first `git add`.
- "Phase 8a evaluator's intended-shape doesn't apply cleanly; let me improvise" → mark `apply_failed_after_evaluation`, continue, surface.
- "Force-push leaves with `--force` instead of `--force-with-lease`" → use `--force-with-lease`.

**Phase 9 (cleanup)**:
- "I'll clean up next time" / "I'll keep the worktrees in case" → tidy is binary.
- "Local branches deleted; remote branches don't matter" → stale remote branches accumulate; future runs see them as "in-flight".
- "Skip the independent re-audit" → fresh-context audit catches state drift.

**Cross-phase (anti-stalls)**:
- "Decision point: how would you like to proceed? Option A / B / C / D" → if user authorized full flow, this is a stall. Proceed.
- "Before dispatching N parallel coordinators, let me do one smoke test first" → smoke tests are not in the workflow; Phase 0 already validates the dispatch surface.
- "Let me run `codex --help` / `codex login status` / `codex doctor`" → never probe the underlying CLI; users with custom providers/auth see misleading "not logged in" probes while the real flow works.
- "Let me `ls <worktree>/node_modules` before dispatching" → workers own their worktree setup.
- "I'll write a shim that wraps `node codex-companion.mjs review`" → that's what `scripts/run-codex-review.py` is. Use it.
- "I'll write 7 separate applier briefs via 7 `Write` calls" → mandatory: ONE template + render N from JSON in ONE Python invocation.
- "Phase 3 is taking forever; let me invent `DONE-PRAGMATIC`" → taxonomy is fixed (`DONE`, `CONVERGED-AT-CAP`, `CAP-REACHED`, `BLOCKED`, `FAILED`). Use `CONVERGED-AT-CAP` for round-budget exhausted.
- "I'll start fresh and ignore the prior session's manifest" / "I'll rebuild the manifest by hand" → Phase 0 auto-namespaces; do not delete or hand-edit other sessions' state.

## How to Think — meta-cognition per phase

- **Phase 0**: *What surprises me? Are MISSION_PROTOCOL + ask-review + do-review available?*
- **Phase 1**: *Can each branch be described in one sentence?*
- **Phase 2**: *Worktree AND remote ref on origin for each branch?*
- **Phase 3**: *I am the coordinator across all branches. Per round per branch: codex review wrapper → classifier → /do-review per major item in my own context → dispatch fresh Applier with pre-decided fix specs. Have I stepped back from the worktrees while Appliers run?*
- **Phase 4**: *Which branches are mergeable? What's the merge order rationale?*
- **Phase 5**: *PR opened by sub-agent using /ask-review? Body ≤ 50k? ≥ 3 reviewer questions? Throttled to ≤4 parallel?*
- **Phase 6**: *Codex rescue triggered (wrapper or slash)? Wait window in progress with adaptive end?*
- **Phase 7**: *Evaluator decided every item via /do-review? Cross-source contradictions flagged as ambiguous?*
- **Phase 8a**: *Reading evaluator decisions; applying accepted items directly via Edit; ambiguous → BLOCKED for the whole PR?*
- **Phase 8b**: *Captured `foundation_pre_merge_tip` BEFORE merging foundation? Using `git rebase --onto` for leaves? Sequential merge with CI-wait between?*
- **Phase 9**: *Returned to clean state plus the intended delta? 0 stale worktrees / local branches / remote branches / temp files? Independent audit said TIDY?*

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
| 3 | `scripts/run-codex-review.py` | rewritten | Spawns `node codex-companion.mjs review --json` (or `adversarial-review --json`) synchronously; auto-discovers the codex plugin path version-agnostic; normalizes output to the round-log JSON schema; writes `<rounds-dir>/<slug>.<round>.json`; updates manifest. `--mode review\|adversarial` flag. |
| 3 | `scripts/classify-review-feedback.py` | new | Apply major/minor policy; produce `{major[], minor[]}`. |
| 3 | `scripts/loop-status.py` | new | Live table of branch round status (read-only). |
| 4 | `skills/run-repo-cleanup/scripts/suggest-merge-order.py` | reused | Foundation→leaf heuristic. |
| 5 | `/ask-review` skill (Skill tool) | external | Author comprehensive PR body. |
| 6 | `scripts/trigger-codex-rescue.py` | rewritten | Spawns `node codex-companion.mjs task --background --write --fresh --model gpt-5.5 --effort xhigh --prompt-file <p> --json`; auto-discovers the plugin path; captures `jobId` + `logFile` to manifest. Optional `--wait` blocks on `status --wait` until terminal. |
| 6 | `scripts/await-pr-reviews.py` | new | Adaptive 900s wait + gather all review streams. |
| 7 | `/do-review` skill (Skill tool) | external | Evaluator's primary instrument. |
| 8a | `scripts/apply-evaluator-decisions.py` | new | Reads `<repo>/.codex-review-rounds/pr-<n>.evaluation.json`; prints ordered apply queue (ambiguous items at top with BLOCKED warning, then accepted items with `file:line:intended-shape:rationale`). Read-only; does NOT modify worktree, commit, or push. Reduces Phase 8a main-agent overhead from ~10 tool calls to ~5 per PR. |
| 8a | `/do-review` skill (Skill tool) | external | OPTIONAL Phase 8a sanity-check (off by default; opt-in for borderline confidence items). |
| 8b | `gh pr merge` (gh CLI) | external | Merge in foundation→leaf order with CI-wait gate. |
| 9 | `scripts/cleanup-worktrees.py` | new | Remove review worktrees; refuses unmerged unless `--force-abandon`. |
| 9 | `skills/run-repo-cleanup/scripts/retire-merged-branches.py` | reused | Delete merged local + remote branches. |

All new scripts: Python 3 stdlib only, dry-run by default where mutating, paired `.md` doc.

## References

| File | Type | One-liner |
|---|---|---|
| `references/event-driven-orchestration.md` | new | Pinned spec for Monitor / ScheduleWakeup / Bash run_in_background / Agent run_in_background usage in Phases 3-8. Read before any parallel dispatch. |
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

Audit → decompose → worktree-per-branch → push to fork → parallel inner loop with coordinator + per-round `/do-review`-evaluating worker (cap 20) → main agent dispatches PR-Creator sub-agent that uses `/ask-review` to author body (≤ 50k, ≥ 3 reviewer questions) → trigger `/codex:resc` and adaptive 900s wait for external bots → evaluator sub-agent uses `/do-review` on all gathered streams → main agent applies accepted items directly via `/do-review` in own context → merge or BLOCKED → tidy. Every sub-agent brief follows MISSION_PROTOCOL. Every review item passes through `/do-review`. Direct-apply forbidden. PR creation is sub-agent-only. Fork-only, ever. One discipline, seventeen invariants, zero exceptions.
