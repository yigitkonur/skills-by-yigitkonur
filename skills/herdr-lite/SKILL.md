---
name: herdr-lite
description: "Use if orchestrating coding agents via Herdr with native Git worktrees, PR-driven state, and side-by-side review-and-fix panes."
---
# Herdr-Lite

Herdr-Lite is a lightweight, self-contained orchestration control plane for AI coding agents. It provides a direct, agile workflow tailored for Antigravity (AGY) and developer orchestrators.

In Herdr-Lite, **Git worktrees**, **dedicated Herdr workspaces**, **GitHub PRs**, and **Herdr split panes** form the native state machine.

---

## 1. Dual-Agent Leadership Topology (CTO & Engineering Manager)

Herdr-Lite establishes an explicit, two-tier leadership division of responsibility in the primary control workspace:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Primary Control Workspace (e.g., zeo-geo-radar)                                  │
├────────────────────────────────────────┬────────────────────────────────────────┤
│ Pane 1: CTO Agent                      │ Pane 2: Engineering Manager (EM) Agent │
│ • Pair-programming with founder/user   │ • DEDICATED AGY AGENT (NOT a shell!)   │
│ • Strategic wave sequencing & DAG      │ • Operational supervisor of team pool  │
│ • Architectural invariants & gates     │ • Dispatches tasks with /teamwork-...  │
│ • Serial rebase & merge sign-off       │ • Central callback & report intake hub │
│ • Global escalation arbitration        │ • Live worktree, PR, & gate burndown   │
└────────────────────────────────────────┴────────────────────────────────────────┘
```

### Mandates & Invariants:
1. **The EM is an Authentic AGY Agent**: Never replace the Engineering Manager with a dumb bash terminal or passive status script. The EM must be an active AGY agent (`herdr agent start "eng-man" --kind agy --pane <PANE_ID> -- --model gemini-3.8-flash-high --dangerously-skip-permissions`).
2. **Central Callback Hub**: All implementer and reviewer agents report their status back to the Engineering Manager (`REPORT: task_id=<ID> pr_url=<URL> head_sha=<SHA> status=DONE`). The EM tracks progress, validates evidence, and coordinates with the CTO.
3. **Prompt Slash Commands & Team Assembly Mandate**:
   - **Prefix Syntax**: Slash commands MUST be placed at the **very beginning** of the prompt string with **strictly zero space** after the slash:
     - `/teamwork-preview` (NOT `/ teamwork-preview`)
     - `/boost` (NOT `/ boost`)
   - **Implementation Tasks**:
     - *Standard Implementation*: Prefix with `/teamwork-preview /herdr`. The prompt MUST explicitly instruct the lead implementer how to structure and assemble a specialized sub-team even for small tasks (e.g. 2–3 roles: Lead Implementer, Test/TDD Specialist, Domain Specialist, QA Verifier).
     - *Very Simple Tasks* (e.g. 1-line typo, doc link repair, single-value config update): Can skip `/teamwork-preview` and run directly.
     - *Deep / High-Complexity Scenarios* (e.g. distributed concurrency, database lock migrations, multi-system synchronization): Prefix with `/boost` to invoke deep reasoning, multi-perspective strategic planning, and rigorous verification loops.
   - **Review Tasks**:
     - *Standard Review*: Default review prompt in Pane 2 (or `/teamwork-preview /herdr` when multi-agent review decomposition is required).
     - *Very Deep Review*: For high-risk, security-critical, or complex PRs, prefix with `/boost` to trigger exhaustive adversarial scrutiny, edge-case generation, and deep verification.
4. **Unbounded Event-Driven Longevity (No Execution Limits)**: Neither the CTO nor the EM operates under arbitrary step or turn limits. Bounded execution is maintained via PR-driven state milestones, 2-strike review budgets, and reactive callbacks, enabling sustained multi-wave completion rallies without artificial execution caps.
5. **Mandatory CTO ➔ EM Active Supervision Contract (Zero Blindness Mandate)**:
   - **The Anti-Pattern**: The CTO must NEVER become a detached observer polling raw Git/GitHub state (`gh issue list`, `gh pr list`) while leaving the living EM agent in Pane 2 untracked. Tracking downstream code artifacts instead of upstream agent cognition produces tracking loss, stalls, and blind spots.
   - **Continuous Supervision Primitives**:
     - `herdr agent wait "$EM_PANE_ID" --until idle --timeout 60000`: The CTO MUST deterministically wait for the EM to complete its turn before deciding next actions. Never rely on loose unhooked timers or sleep polling.
     - `herdr pane read "$EM_PANE_ID" --lines 100`: The CTO MUST actively inspect the EM's live terminal buffer at every status boundary to capture lane dispatches, reviewer assignments, and blocker declarations.
     - `herdr agent prompt "$EM_PANE_ID" "<PROMPT>"`: The CTO MUST apply continuous pressure through active interrogation whenever the EM is idle, silent, or at a wave boundary:
       ```text
       CTO STATUS INTERROGATION:
       1. What is the current wave burndown and active lane progress?
       2. Which candidate PR URLs and verified commit SHAs are awaiting serial merge?
       3. Are there any concrete blockers, test failures, or 2-strike review escalations?
       4. What is the planned DAG and dispatch queue for the next wave?
       ```
   - **Structured Wave Handover Protocol (EM ➔ CTO)**:
     - When all lanes in a wave report `DONE`, the EM must NOT silently stop. It must output a formal, machine-readable handover block:
       ```text
       WAVE_COMPLETE: wave=<WAVE_ID> prs=[<PR1>, <PR2>] shas=[<SHA1>, <SHA2>] next_wave=<NEXT_WAVE_ID> next_issues=[<ISSUE1>, <ISSUE2>] status=AWAITING_SERIAL_MERGE
       ```
      - The CTO captures this block, verifies gates, performs the serial squash-merges onto `main`, and then explicitly prompts the EM to unlock and dispatch `NEXT_WAVE`.
6. **Post-Milestone Agent & Pane Retirement Mandate (Zero Background Bloat)**:
   - When all waves and milestones are 100% complete (zero open issues, zero open PRs), the CTO MUST cleanly retire the living Engineering Manager in Pane 2:
     ```bash
     herdr pane close "$EM_PANE_ID"
     ```
   - Close any remaining worker panes, review panes, or temporary tabs (`herdr tab close "$TAB_ID"`).
   - Never leave idle, zombie AI agents running in the background consuming memory, API context, and cluttering `herdr pane list`.

---

## 2. Antigravity Orchestration Lifecycle

Antigravity operates a continuous, multi-wave streaming orchestration loop:

1. **Automatic Ticket Intake**: When starting without GitHub issues, automatically decompose discussions or bugs into vertical tracer-bullet tickets and publish via `gh issue create`. See [references/ticket-decomposition-and-waves.md](references/ticket-decomposition-and-waves.md).
2. **Multi-Wave Dependency Graph (Waves 1 to 5)**: Arrange tickets into a DAG based on blocking edges; dispatch disjoint Wave 1 lanes concurrently.
3. **Dedicated Worktree Workspace Provisioning**: Execute `herdr worktree create` to provision an isolated workspace for each task with Pane 1 automatically anchored in the checkout.
4. **Streaming Side-by-Side Review Split**: Implementers report `status=DONE` to the EM. As soon as any worker reports done, **split the pane side-by-side** in the same tab (`herdr pane split --pane "$IMPL_PANE_ID" --direction right ...`) to launch the reviewer in Pane 2.
   > [!IMPORTANT]
   > **Implementation Pane Preservation**: Never close or kill the implementation pane when a review begins! The implementer pane holds vital execution logs, reasoning transcripts, and test traces needed for review and fix-and-verify loops. Both panes remain alive and visible side-by-side.
5. **Deep Review-and-Fix**: The reviewer audits exact commit SHAs with domain skills (`code-review`, `tdd`, `audit-completion`), authors test/bug patches directly in the worktree, and posts GitHub PR approval.
6. **EM Handover & CTO Serial Rebase-Merge**: Once all wave lanes report `DONE`, the EM outputs a structured handover (`WAVE_COMPLETE: wave=... prs=[...] shas=[...] next_wave=... next_issues=[...]`). The CTO actively captures this via `herdr pane read`, validates baseline gates, serially rebases candidate PRs onto `main`, and squash-merges.
7. **Full-Job Teardown, Worktree Removal & Milestone Retirement**:
   - *Merge Integrity Verification*: Confirm PR is MERGED on remote before touching checkouts (`gh pr view "$PR_URL" --json state -q .state`).
   - *Worktree Teardown*: Execute `herdr worktree remove --workspace "$WS_ID"` (removes disk checkout and unregisters workspace).
   - *Branch Cleanup*: Delete local branch post-removal (`git branch -D "$BRANCH"`) and prune remotes (`git remote prune origin`).
   - *Milestone Retirement*: When all waves/milestones conclude, retire the EM pane (`herdr pane close "$EM_PANE_ID"`).

---

## 3. Worktree Workspace Topology: Side-by-Side Pane Layout

Each task operates inside its own dedicated Herdr workspace, featuring a side-by-side implementer and reviewer layout in a single unified tab:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ Dedicated Worktree Workspace: task-182 (workspace_id: w1Y, Tab: task-182)     │
├───────────────────────────────────────┬───────────────────────────────────────┤
│ Pane 1: "impl" (Implementer)          │ Pane 2: "review" (Split on "DONE")    │
│ • Runs AGY Implementer                │ • Runs Gemini 3.8 Flash Reviewer      │
│ • Behavioral TDD implementation       │ • Audits exact candidate commit SHA   │
│ • Local commit & push branch          │ • Inspects implementer output directly│
│ • Opens PR (gh pr create)             │ • Directly patches tests & bug fixes  │
│ • Reports: "status=DONE pr_url=..."   │ • Posts PR review & approvals         │
│ • REMAINS OPEN throughout review      │ • Certifies final green state         │
├───────────────────────────────────────┴───────────────────────────────────────┤
│ Both panes remain open until COMPLETE FINISH; then workspace is closed.       │
└───────────────────────────────────────────────────────────────────────────────┘
```

> [!CAUTION]
> **Anti-Pattern (DO NOT DO)**: 
> 1. Running `git worktree add` in a shell and opening loose, independent tabs in the main workspace with `--cwd <path>`.
> 2. Opening separate independent tabs for review instead of splitting side-by-side panes.
> 3. Prematurely terminating or closing the implementation pane when review starts, destroying the debug/context trail.

> [!TIP]
> **Golden Pattern (ALWAYS DO)**: 
> 1. Run `herdr worktree create --cwd "$REPO_ROOT" --path "$WORKTREE_PATH" --branch "$BRANCH" --label "task-${TASK_ID}" --no-focus`.
> 2. Run implementer in Pane 1.
> 3. When `status=DONE`, run `herdr pane split --pane "$IMPL_PANE_ID" --direction right --cwd "$WORKTREE_PATH" --no-focus` to launch reviewer in Pane 2.
> 4. Keep both panes open side-by-side until the entire task is certified and approved.

---

## 4. Core Herdr CLI Primitives Quick Reference

Herdr commands output native JSON. Use `jq` to extract identifiers:

```bash
# 0. CTO Active Supervision & Interrogation of EM in Pane 2 (Zero Blindness):
# Deterministically wait for EM to complete turn before making strategic moves:
herdr agent wait "$EM_PANE_ID" --until idle --timeout 60000

# Capture EM's screen buffer to inspect decisions, lane status, and blockers:
herdr pane read "$EM_PANE_ID" --lines 100

# Interrogate EM on progress or next wave DAG whenever EM goes quiet or finishes a wave:
herdr agent prompt "$EM_PANE_ID" "CTO STATUS INTERROGATION:
1. Report active lanes, PR URLs, and candidate SHAs.
2. Report any blockers, test failures, or escalations.
3. State the DAG and queue for the next wave."

# 1. Provision dedicated worktree workspace & capture coordinates:
WORKTREE_JSON="$(herdr worktree create --cwd "$REPO_ROOT" --path "$WORKTREE_PATH" --branch "$BRANCH" --label "task-${TASK_ID}" --no-focus)"
WS_ID="$(echo "$WORKTREE_JSON" | jq -er .result.workspace.workspace_id)"
IMPL_PANE_ID="$(echo "$WORKTREE_JSON" | jq -er .result.root_pane.pane_id)"

# 2. Launch Implementer with --dangerously-skip-permissions:
herdr agent start "impl-${TASK_ID}" --kind agy --pane "$IMPL_PANE_ID" --timeout 45000 -- --model "$IMPL_MODEL" --dangerously-skip-permissions

# 3. Prompt Implementer with mandatory /teamwork-preview /herdr prefix and explicit team structure:
herdr agent prompt "$IMPL_PANE_ID" "/teamwork-preview /herdr
You are the Lead Implementer for Task #${TASK_ID}...
Assemble and guide a specialized sub-team to complete this task:
- Role 1 (Lead Developer): Core logic, schemas, and API handlers.
- Role 2 (TDD Specialist): Behavioral red-to-green test suite.
- Role 3 (QA Verifier): Fast Syntax Gate, edge-case assertions, and PR packaging.
When done, report back with: REPORT: task_id=${TASK_ID} pr_url=<PR_URL> head_sha=\$(git rev-parse HEAD) status=DONE"

# Note: For extremely hard scenarios or deep implementation cases, substitute with /boost:
# herdr agent prompt "$IMPL_PANE_ID" "/boost /herdr ..."

# 4. Streaming Review: As soon as worker reports DONE, split pane side-by-side in SAME tab:
SPLIT_JSON="$(herdr pane split --pane "$IMPL_PANE_ID" --direction right --cwd "$WORKTREE_PATH" --no-focus)"
REV_PANE_ID="$(echo "$SPLIT_JSON" | jq -er .result.pane.pane_id)"
herdr agent start "rev-${TASK_ID}" --kind agy --pane "$REV_PANE_ID" --timeout 45000 -- --model "gemini-3.8-flash-high" --dangerously-skip-permissions

# 5. Prompt Reviewer (Implementer pane remains alive side-by-side):
# Use standard review or use /boost for very deep review on high-risk/complex PRs:
herdr agent prompt "$REV_PANE_ID" "/boost /herdr
Deep Review & Hardening for PR #${TASK_ID}...
Auditing candidate commit \$(git rev-parse HEAD) with adversarial rigor..."

# 6. Full-Job Teardown: ONLY once PR is confirmed MERGED to main:
# Verify PR is merged:
gh pr view "$PR_URL" --json state -q .state | grep -iq "MERGED"
# Remove worktree checkout and unregister workspace via Herdr:
herdr worktree remove --workspace "$WS_ID"
# Clean up preserved local branch and prune remotes:
git branch -D "$BRANCH"
git remote prune origin

# 7. Post-Milestone Retirement: When all issues/PRs are resolved, retire EM and lingering panes:
herdr pane close "$EM_PANE_ID"
```

See [references/herdr-primitives.md](references/herdr-primitives.md) for the complete CLI catalog.

---

## 5. Preserved Invariant Safeguards

Herdr-Lite strictly enforces core engineering physics:

1. **Wait for `idle` Before Prompting AGY**: Never inject prompt text into an active AGY writer while it is synthesizing code or executing tools (`herdr agent wait "$PANE_ID" --until idle`).
2. **Exact-SHA Review Binding**: Reviews bind strictly to an exact commit SHA. Any subsequent commit pushes HEAD to a new SHA ($SHA_2 \neq SHA_1$), invalidating prior approvals. A delta review is required for the new SHA.
3. **Two-Round Failure Budget**: If an implementer and reviewer do not converge within 2 review-and-fix rounds, **stop automated retries**. Escalate the concrete blocker to the user or supervisor.
4. **No Material Waivers**: Material findings cannot be reclassified as advisory to force an approval.
5. **Two-Stage Teardown on Full Completion**:
   - *Workspace Retirement*: Close reviewer and implementer panes together **only after** PR review is approved and merged (`herdr workspace close <WS_ID>`). Never terminate implementation prematurely.
   - *Worktree Removal Gate*: Only delete worktrees when `git status --porcelain` is strictly clean (`herdr worktree remove --workspace "$WS_ID"` or `git worktree remove "$WORKTREE_PATH"`). Dirty checkouts are preserved with a recorded reason; `--force` is prohibited.
6. **Mandatory Merge Verification Before Worktree Removal**: Never unlink or delete a worktree checkout until the candidate PR is confirmed merged into `main`. Removing a worktree with unmerged commits causes permanent data loss.
7. **Post-Milestone Zero-Bloat Retirement**: When all waves and milestones conclude (zero open issues, zero unmerged PRs), the CTO must immediately close the EM agent pane (`herdr pane close "$EM_PANE_ID"`) and all completed panes/tabs. Zero idle agents in the background.

---

## Canonical References

| Reference | When to Read | Topics |
|---|---|---|
| [references/ticket-decomposition-and-waves.md](references/ticket-decomposition-and-waves.md) | Decomposing discussions/bugs into vertical tickets and scheduling up to 5 waves. | Tracer-bullet slices, gh issue create, DAG wave classification, callback protocol. |
| [references/orchestration-workflow.md](references/orchestration-workflow.md) | Setting up tasks, dispatching workers, streaming reviews, and safe teardown. | Parallelism analysis, workspace coordinate capture, streaming reviews, and deep audit. |
| [references/herdr-primitives.md](references/herdr-primitives.md) | Looking up CLI commands, syntax, flags, and `jq` coordinate extraction recipes. | Full command reference for worktree, workspace, tab, pane, agent, and notification. |
| [references/serial-merge-and-conflicts.md](references/serial-merge-and-conflicts.md) | Merging approved PRs onto main or resolving merge conflicts. | Self-contained 5-step conflict engine, Herdr default worktree behavior, PR merge gate, post-milestone teardown. |
| [references/terminal-and-event-rules.md](references/terminal-and-event-rules.md) | Interacting with Herdr panes, sending prompts, and handling modals. | Live coordinates, PTY buffering, bracketed paste, modal bridge, degraded mode. |
| [references/review-and-fix-contract.md](references/review-and-fix-contract.md) | Auditing candidate PRs, writing test patches, or evaluating decisions. | Exact-SHA binding, direct patching, 2-round limits, delta reviews, PR commands. |
| [references/recovery-and-safeguards.md](references/recovery-and-safeguards.md) | Handling crashed agents, quota exhaustion, Git locks, or hung sessions. | No-kill-9, index.lock recovery, exact conversation resume, worktree safety. |
