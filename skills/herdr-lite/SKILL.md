---
name: herdr-lite
description: "Use if orchestrating coding agents via Herdr with native Git worktrees, PR-driven state, and side-by-side review-and-fix panes."
---
# Herdr-Lite

Herdr-Lite is a lightweight, self-contained orchestration control plane for AI coding agents. It provides a direct, agile workflow tailored for Antigravity (AGY) and developer orchestrators.

In Herdr-Lite, **Git worktrees**, **dedicated Herdr workspaces**, **GitHub PRs**, and **Herdr panes** form the native state machine.

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
3. **The `/teamwork-preview` Task Launch Rule**: When starting any implementation task in a worktree, the prompt **MUST** start with `/teamwork-preview` (strictly zero space after slash) and guide the implementer to assemble, coordinate, and lead a specialized sub-team (e.g., Schema Architect, API Specialist, QA Verifier) to execute the task.

---

## 2. Antigravity Orchestration Lifecycle

Antigravity operates a continuous, multi-wave streaming orchestration loop:

1. **Automatic Ticket Intake**: When starting without GitHub issues, automatically decompose discussions or bugs into vertical tracer-bullet tickets and publish via `gh issue create`. See [references/ticket-decomposition-and-waves.md](references/ticket-decomposition-and-waves.md).
2. **Multi-Wave Dependency Graph (Waves 1 to 5)**: Arrange tickets into a DAG based on blocking edges; dispatch disjoint Wave 1 lanes concurrently.
3. **Native Worktree Workspace Provisioning**: Execute `herdr worktree create` to provision an isolated workspace for each task with Tab 1 automatically anchored in the checkout and labeled `impl`.
4. **Streaming Review & Callback Loop**: Implementers write back `status=DONE` to the EM. As soon as any worker reports done, Tab 2 (`review`) is immediately opened inside that worktree workspace without waiting for other lanes.
5. **Deep Review-and-Fix**: The reviewer audits exact commit SHAs with domain skills (`code-review`, `tdd`, `audit-completion`), authors test/bug patches directly, and posts GitHub PR approval.
6. **Serial Integration & Wave Advancement**: Rebase approved candidates serially onto moving `main`, resolve any merge conflicts via `resolving-merge-conflicts` principles, merge to `main`, and advance to the next wave until all waves complete.

---

## 3. Worktree Workspace Topology: Golden Pattern vs. Anti-Pattern

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ Dedicated Worktree Workspace: task-182 (workspace_id: w1Y)                    │
├───────────────────────────────────────┬───────────────────────────────────────┤
│ Tab 1: "impl"                         │ Tab 2: "review" (Opened on "DONE")    │
│ • Runs AGY Implementer                │ • Runs Gemini 3.8 Flash Reviewer      │
│ • Behavioral TDD implementation       │ • Audits exact candidate commit SHA   │
│ • Local commit & push branch          │ • Uses code-review & tdd skills       │
│ • Opens PR (gh pr create)             │ • Directly patches tests & bug fixes  │
│ • Reports: "DONE: PR=<url> SHA=<sha>" │ • Approves PR (gh pr review --approve)│
└───────────────────────────────────────┴───────────────────────────────────────┘
```

> [!CAUTION]
> **Anti-Pattern (DO NOT DO)**: Running `git worktree add` in a shell and opening loose, independent tabs in the main workspace with `--cwd <path>`. This pollutes the control workspace, breaks Herdr's 1-to-1 workspace lifecycle tracking, and loses isolation.

> [!TIP]
> **Golden Pattern (ALWAYS DO)**: Run `herdr worktree create --cwd "$REPO_ROOT" --path "$WORKTREE_PATH" --branch "$BRANCH" --label "$LABEL" --no-focus`.
> Herdr automatically:
> 1. Creates the Git worktree at `$WORKTREE_PATH`.
> 2. Provisions an isolated Herdr workspace bound directly to the worktree.
> 3. Launches Tab 1 with its root pane already inside the checkout directory.
> 
> 1 Task = 1 Git Worktree = 1 Dedicated Herdr Workspace = Tab 1 (`impl`) + Tab 2 (`review`).

---

## 4. Core Herdr CLI Primitives Quick Reference

Herdr commands output native JSON. Use `jq` to extract identifiers:

```bash
# 1. Provision dedicated worktree workspace & capture coordinates:
WORKTREE_JSON="$(herdr worktree create --cwd "$REPO_ROOT" --path "$WORKTREE_PATH" --branch "$BRANCH" --label "task-${TASK_ID}" --no-focus)"
WS_ID="$(echo "$WORKTREE_JSON" | jq -er .result.workspace.workspace_id)"
IMPL_PANE_ID="$(echo "$WORKTREE_JSON" | jq -er .result.root_pane.pane_id)"
IMPL_TAB_ID="$(echo "$WORKTREE_JSON" | jq -er .result.root_pane.tab_id)"
herdr tab rename "$IMPL_TAB_ID" "impl"

# 2. Launch Implementer with --dangerously-skip-permissions:
herdr agent start "impl-${TASK_ID}" --kind agy --pane "$IMPL_PANE_ID" --timeout 45000 -- --model "$IMPL_MODEL" --dangerously-skip-permissions

# 3. Prompt Implementer with mandatory /teamwork-preview prefix:
herdr agent prompt "$IMPL_PANE_ID" "/teamwork-preview
You are the Lead Implementer for Task #${TASK_ID}...
Assemble and guide a specialized team to complete this task.
When done, report back with: REPORT: task_id=${TASK_ID} pr_url=<PR_URL> head_sha=\$(git rev-parse HEAD) status=DONE"

# 4. Streaming Review: As soon as worker reports DONE, spawn Tab 2 inside that workspace:
REV_TAB_JSON="$(herdr tab create --workspace "$WS_ID" --cwd "$WORKTREE_PATH" --label "review" --no-focus)"
REV_PANE_ID="$(echo "$REV_TAB_JSON" | jq -er .result.root_pane.pane_id)"
herdr agent start "rev-${TASK_ID}" --kind agy --pane "$REV_PANE_ID" --timeout 45000 -- --model "gemini-3.8-flash-high" --dangerously-skip-permissions

# 5. Notify User & EM of Milestones:
herdr notification show "Candidate Approved" --body "Issue #${TASK_ID} approved and queued for merge." --sound done

# 6. Retire Workspace, Remove Clean Worktree, and Clean Branches:
herdr workspace close "$WS_ID"
test -z "$(git -C "$WORKTREE_PATH" status --porcelain)" && git worktree remove "$WORKTREE_PATH"
git branch -d "$BRANCH" 2>/dev/null || git branch -D "$BRANCH"
git remote prune origin
```

See [references/herdr-primitives.md](references/herdr-primitives.md) for the complete CLI catalog.

---

## 5. Preserved Invariant Safeguards

Herdr-Lite strictly enforces core engineering physics:

1. **Wait for `idle` Before Prompting AGY**: Never inject prompt text into an active AGY writer while it is synthesizing code or executing tools (`herdr agent wait "$PANE_ID" --until idle`).
2. **Exact-SHA Review Binding**: Reviews bind strictly to an exact commit SHA. Any subsequent commit pushes HEAD to a new SHA ($SHA_2 \neq SHA_1$), invalidating prior approvals. A delta review is required for the new SHA.
3. **Two-Round Failure Budget**: If an implementer and reviewer do not converge within 2 review-and-fix rounds, **stop automated retries**. Escalate the concrete blocker to the user or supervisor.
4. **No Material Waivers**: Material findings cannot be reclassified as advisory to force an approval.
5. **Two-Stage Teardown**:
   - *Prompt Pane/Workspace Retirement*: Close reviewer and implementer resources once PR review is approved (`herdr workspace close <WS_ID>`).
   - *Worktree Removal Gate*: Only delete worktrees when `git status --porcelain` is strictly clean (`git worktree remove "$WORKTREE_PATH"`). Dirty checkouts are preserved with a recorded reason; `--force` is prohibited.

---

## Canonical References

| Reference | When to Read | Topics |
|---|---|---|
| [references/ticket-decomposition-and-waves.md](references/ticket-decomposition-and-waves.md) | Decomposing discussions/bugs into vertical tickets and scheduling up to 5 waves. | Tracer-bullet slices, gh issue create, DAG wave classification, callback protocol. |
| [references/orchestration-workflow.md](references/orchestration-workflow.md) | Setting up tasks, dispatching workers, streaming reviews, and safe teardown. | Parallelism analysis, workspace coordinate capture, streaming reviews, and deep audit. |
| [references/herdr-primitives.md](references/herdr-primitives.md) | Looking up CLI commands, syntax, flags, and `jq` coordinate extraction recipes. | Full command reference for worktree, workspace, tab, pane, agent, and notification. |
| [references/serial-merge-and-conflicts.md](references/serial-merge-and-conflicts.md) | Merging approved PRs onto main or resolving merge conflicts. | Serial rebase-and-merge pipeline, resolving-merge-conflicts protocol, force-push with lease. |
| [references/terminal-and-event-rules.md](references/terminal-and-event-rules.md) | Interacting with Herdr panes, sending prompts, and handling modals. | Live coordinates, PTY buffering, bracketed paste, modal bridge, degraded mode. |
| [references/review-and-fix-contract.md](references/review-and-fix-contract.md) | Auditing candidate PRs, writing test patches, or evaluating decisions. | Exact-SHA binding, direct patching, 2-round limits, delta reviews, PR commands. |
| [references/recovery-and-safeguards.md](references/recovery-and-safeguards.md) | Handling crashed agents, quota exhaustion, Git locks, or hung sessions. | No-kill-9, index.lock recovery, exact conversation resume, worktree safety. |
