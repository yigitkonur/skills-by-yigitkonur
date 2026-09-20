---
name: herdr-lite
description: "Use if orchestrating coding agents via Herdr with native Git worktrees, PR-driven state, and side-by-side review-and-fix panes."
---
# Herdr-Lite

Herdr-Lite is a lightweight, self-contained orchestration control plane for AI coding agents. It provides a direct, agile workflow tailored for Antigravity (AGY) and developer orchestrators.

In Herdr-Lite, **Git worktrees**, **dedicated Herdr workspaces**, **GitHub PRs**, and **Herdr panes** form the native state machine.

---

## 1. Antigravity Orchestration Lifecycle

Antigravity operates a continuous, multi-wave streaming orchestration loop:

1. **Automatic Ticket Intake**: When starting without GitHub issues, automatically decompose discussions or bugs into vertical tracer-bullet tickets and publish via `gh issue create`. See [references/ticket-decomposition-and-waves.md](references/ticket-decomposition-and-waves.md).
2. **Multi-Wave Dependency Graph (Waves 1 to 5)**: Arrange tickets into a DAG based on blocking edges; dispatch disjoint Wave 1 lanes concurrently.
3. **Worktree & Workspace Provisioning**: Execute `herdr worktree create` to spin up a dedicated workspace for each task with Tab 1 labeled `impl`.
4. **Streaming Review & Callback Loop**: Implementers write back `status=DONE`. As soon as any worker reports done, Antigravity immediately opens Tab 2 (`review`) inside that worktree workspace without waiting for other lanes.
5. **Deep Review-and-Fix**: The reviewer audits exact commit SHAs with domain skills (`code-review`, `tdd`, `audit-completion`), authors test/bug patches directly, and posts GitHub PR approval.
6. **Serial Integration & Wave Advancement**: Rebase approved candidates serially onto moving `main`, resolve any merge conflicts via `resolving-merge-conflicts` principles, merge to `main`, and advance to the next wave until all waves complete.

---

## 2. Worktree Workspace Topology

Each task operates inside its own dedicated Herdr workspace:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ Worktree Workspace: task-182 (workspace_id: w1Y)                               │
├───────────────────────────────────────┬───────────────────────────────────────┤
│ Tab 1: "impl"                         │ Tab 2: "review" (Opened on "DONE")    │
│ • Runs AGY Implementer                │ • Runs Gemini 3.8 Flash Reviewer      │
│ • Behavioral TDD implementation       │ • Audits exact candidate commit SHA   │
│ • Local commit & push branch          │ • Uses code-review & tdd skills       │
│ • Opens PR (gh pr create)             │ • Directly patches tests & bug fixes  │
│ • Reports: "DONE: PR=<url> SHA=<sha>" │ • Approves PR (gh pr review --approve)│
└───────────────────────────────────────┴───────────────────────────────────────┘
```

---

## 3. Core Herdr CLI Primitives Quick Reference

Herdr commands output native JSON. Use `jq` to extract identifiers:

```bash
# 1. Provision worktree & capture workspace/pane/tab IDs:
WORKTREE_JSON="$(herdr worktree create "$REPO_ROOT" "$WORKTREE_PATH" --branch "$BRANCH")"
WS_ID="$(echo "$WORKTREE_JSON" | jq -er .result.workspace.workspace_id)"
IMPL_PANE_ID="$(echo "$WORKTREE_JSON" | jq -er .result.root_pane.pane_id)"
IMPL_TAB_ID="$(echo "$WORKTREE_JSON" | jq -er .result.root_pane.tab_id)"
herdr tab rename "$IMPL_TAB_ID" "impl"

# 2. Launch Implementer:
herdr agent start "impl-${TASK_ID}" --kind agy --pane "$IMPL_PANE_ID" -- --model "$IMPL_MODEL"

# 3. Streaming Review: As soon as worker reports DONE, spawn Tab 2:
REV_TAB_JSON="$(herdr tab create --workspace "$WS_ID" --cwd "$WORKTREE_PATH" --label "review" --no-focus)"
REV_PANE_ID="$(echo "$REV_TAB_JSON" | jq -er .result.root_pane.pane_id)"
herdr agent start "rev-${TASK_ID}" --kind agy --pane "$REV_PANE_ID" -- --model "gemini-3.8-flash-high"

# 4. Notify User of Milestones:
herdr notification show "Candidate Approved" --body "Issue #${TASK_ID} approved and queued for merge." --sound done

# 5. Retire Workspace, Remove Clean Worktree, and Clean Branches:
herdr workspace close "$WS_ID"
test -z "$(git -C "$WORKTREE_PATH" status --porcelain)" && git worktree remove "$WORKTREE_PATH"
git branch -d "$BRANCH" 2>/dev/null || git branch -D "$BRANCH"
git remote prune origin
```

See [references/herdr-primitives.md](references/herdr-primitives.md) for the complete CLI catalog.

---

## 4. Preserved Invariant Safeguards

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
