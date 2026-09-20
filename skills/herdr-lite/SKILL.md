---
name: herdr-lite
description: "Use if orchestrating coding agents via Herdr with native Git worktrees, PR-driven state, and side-by-side review-and-fix panes."
---

# Herdr-Lite

Herdr-Lite is a lightweight, self-contained orchestration control plane for AI coding agents. While the primary `herdr` skill governs enterprise multi-agent hierarchies (CTO $\to$ Codex EM with `state.yaml` and disk YAML reporting), **Herdr-Lite** provides a direct, agile workflow tailored for Antigravity (AGY) and developer orchestrators.

In Herdr-Lite, **Git worktrees**, **GitHub PRs**, **commit SHAs**, and **Herdr panes** form the native state machine.

---

## 1. Role Selection

Every cold reader identifies its assigned role first. Read only the sections and references relevant to your role.

| Assigned Role | Authority & Scope | Focus Sections & References | Out of Scope |
|---|---|---|---|
| **Lite Orchestrator** | Worktree provisioning, agent dispatch, PR tracking, safe retirement. | §2, §4, [references/orchestration-workflow.md](references/orchestration-workflow.md) | Authoring feature code directly |
| **Implementer (AGY)** | Feature implementation, behavioral tests (TDD), atomic commits, PR creation. | §3, [references/orchestration-workflow.md](references/orchestration-workflow.md) | Spawning sibling reviewers |
| **Sibling Reviewer** | Exact-SHA audit, direct test/code patching (review-and-fix), PR approval. | §3, [references/review-and-fix-contract.md](references/review-and-fix-contract.md) | Arbitrary task reassignment |

> [!IMPORTANT]
> **No Management Bootstrapping**: Implementers and Reviewers focus strictly on code, tests, and diffs. Never spawn nested subagents or assume supervisor authority.

---

## 2. Worktree & Pane Provisioning

Provision an isolated workspace and root pane in a single atomic step using `herdr worktree create`. Do not spawn redundant tabs with `herdr tab create`:

```bash
# 1. Provision worktree, workspace, and root pane in one call:
WORKTREE_OUTPUT="$(herdr worktree create "$REPO_ROOT" "$WORKTREE_PATH" --branch "$BRANCH_NAME")"
WORKSPACE_ID="$(echo "$WORKTREE_OUTPUT" | jq -er .result.workspace.workspace_id)"
IMPL_PANE_ID="$(echo "$WORKTREE_OUTPUT" | jq -er .result.root_pane.pane_id)"

# 2. Launch AGY Implementer into root pane:
herdr agent start "impl-${TASK_ID}" --kind agy --pane "$IMPL_PANE_ID" -- --model "$IMPL_MODEL"
```

---

## 3. Review-and-Fix Loop (Side-by-Side Panes)

The core unit of delivery in Herdr-Lite is a coupled **Implementer + Sibling Reviewer** pair operating in a shared worktree tab:

```
┌───────────────────────────────────────┬───────────────────────────────────────┐
│ Implementer Pane (Left)               │ Sibling Reviewer Pane (Right)         │
│ • Runs AGY implementer                │ • Runs Gemini 3.8 Flash / Reviewer    │
│ • Authors code with TDD               │ • Audits exact candidate commit SHA   │
│ • Opens PR (gh pr create)             │ • Patches tests/edge cases directly   │
│                                       │ • Posts formal approval on PR         │
└───────────────────────────────────────┴───────────────────────────────────────┘
```

1. **Split Right for Sibling Reviewer**:
   ```bash
   REV_PANE_ID="$(herdr pane split --pane "$IMPL_PANE_ID" --direction right --cwd "$WORKTREE_PATH" --no-focus | jq -er .result.pane.pane_id)"
   herdr agent start "rev-${TASK_ID}" --kind agy --pane "$REV_PANE_ID" -- --model "gemini-3.8-flash-high"
   ```
2. **Review-and-Fix Discipline**:
   - The reviewer audits the candidate HEAD, runs test suites, and inspects diffs.
   - For minor defects or missing test coverage, the reviewer **directly commits fixes** to the PR branch and pushes.
   - Once all criteria pass, the reviewer approves the PR:
     ```bash
     gh pr review "$PR_URL" --approve -b "LGTM: verified candidate commit $(git rev-parse HEAD)"
     ```

---

## 4. Preserved Invariant Safeguards

Herdr-Lite enforces rigorous engineering physics to prevent common multi-agent failure modes:

1. **Wait for `idle` Before Prompting AGY**: Never inject prompt text into an active AGY writer while it is synthesizing code or executing tools. Always wait for idle:
   ```bash
   herdr agent wait "$TARGET_PANE_ID" --until idle --timeout 60000
   ```
2. **Exact-SHA Review Binding**: Reviews bind strictly to an exact commit SHA. Any subsequent commit pushes HEAD to a new SHA ($SHA_2 \neq SHA_1$), invalidating prior approvals. A delta review is required for the new SHA.
3. **Two-Round Failure Budget**: If an implementer and reviewer do not converge within 2 review-and-fix rounds, **stop automated retries**. Escalate the concrete blocker to the user or supervisor.
4. **No Material Waivers**: Material findings cannot be reclassified as advisory to force an approval.
5. **Two-Stage Teardown**:
   - *Prompt Pane Retirement*: Close worker panes as soon as PR review is approved (`herdr pane close <PANE_ID>`). Do not leave orphaned idle panes running.
   - *Worktree Removal Gate*: Only delete worktree checkouts when `git status --porcelain` is strictly clean (`git worktree remove "$WORKTREE_PATH"`). Dirty checkouts are preserved with a recorded reason; `--force` is prohibited.

---

## Canonical References

| Reference | When to Read | Topics |
|---|---|---|
| [references/orchestration-workflow.md](references/orchestration-workflow.md) | Setting up tasks, dispatching workers, tracking PRs, and tearing down. | Step-by-step lifecycle, coordinate capture, PR creation, and integration. |
| [references/terminal-and-event-rules.md](references/terminal-and-event-rules.md) | Interacting with Herdr panes, sending prompts, and handling modals. | Live coordinates, PTY buffering, bracketed paste, modal bridge, degraded mode. |
| [references/review-and-fix-contract.md](references/review-and-fix-contract.md) | Auditing candidate PRs, writing test patches, or evaluating decisions. | Exact-SHA binding, direct patching, 2-round limits, delta reviews, PR commands. |
| [references/recovery-and-safeguards.md](references/recovery-and-safeguards.md) | Handling crashed agents, quota exhaustion, Git locks, or hung sessions. | No-kill-9, index.lock recovery, exact conversation resume, worktree safety. |
