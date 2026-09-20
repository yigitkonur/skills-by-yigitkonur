# Lite Execution & Review-and-Fix (AGY-First)

This reference outlines the lightweight, direct orchestration pattern for scenarios where an Antigravity (AGY) agent or developer coordinates tasks directly without the full Enterprise Codex CTO/EM hierarchy, `state.yaml` checkpointing, or 4-step disk YAML reports.

In Lite Execution, the **GitHub PR / Issue**, **commit SHA**, and **Herdr pane status** act as the native state machine.

---

## 1. When to Choose Lite Execution

| Factor | Enterprise Orchestration (Default) | Lite Execution (AGY-First) |
|---|---|---|
| **Leadership** | Shared tab: CTO left ($x=0$), Codex EM right ($x>0$) | Single AGY supervisor or developer orchestrator |
| **State Tracking** | Mutable `state.yaml` at run root | GitHub Issues, PRs, and Herdr pane inventory |
| **Artifacts** | Immutable YAML reports via 4-step pipeline | Git commit SHAs, PR review comments, CI checks |
| **Ideal For** | Large multi-agent teams (5+), async milestones, complex graph dependencies | Vertical slices, Sentry/issue batches, direct feature development |

---

## 2. Direct Worktree & Pane Provisioning

Use `herdr worktree create` to provision an isolated workspace and root pane in a single atomic step. Do not call redundant `herdr tab create` commands:

```bash
# Provision worktree, workspace, and root pane in one call:
WORKTREE_OUTPUT="$(herdr worktree create "$REPO_ROOT" "$WORKTREE_PATH" --branch "$BRANCH_NAME")"
WORKSPACE_ID="$(echo "$WORKTREE_OUTPUT" | jq -er .result.workspace.workspace_id)"
IMPL_PANE_ID="$(echo "$WORKTREE_OUTPUT" | jq -er .result.root_pane.pane_id)"

# Launch AGY Implementer into root pane:
herdr agent start "impl-${TASK_ID}" --kind agy --pane "$IMPL_PANE_ID" -- --model "$IMPL_MODEL"
```

---

## 3. Implementer Execution & PR Creation

The implementer operates within its assigned worktree:
1. **Behavioral Implementation**: Follow test-driven development (TDD) for application code.
2. **Local Commit**: Commit verified changes with clear conventional commit messages.
3. **Open PR**: Push branch to remote and open a draft or ready PR:
   ```bash
   git push -u origin "$BRANCH_NAME"
   PR_URL="$(gh pr create --title "$PR_TITLE" --body "$PR_BODY")"
   ```

---

## 4. Sibling Reviewer (Review-and-Fix)

To audit and patch the candidate without losing context, split the worktree tab to spawn a sibling reviewer side-by-side:

```bash
# Split right from implementer pane:
REV_PANE_ID="$(herdr pane split --pane "$IMPL_PANE_ID" --direction right --cwd "$WORKTREE_PATH" --no-focus | jq -er .result.pane.pane_id)"

# Launch reviewer (e.g. gemini-3.8-flash-high or authorized review model):
herdr agent start "rev-${TASK_ID}" --kind agy --pane "$REV_PANE_ID" -- --model "$REV_MODEL"
```

### Review-and-Fix Protocol:
1. **Exact-SHA Audit**: The reviewer inspects the candidate HEAD commit, runs local test suites, and audits diffs against acceptance criteria.
2. **Direct Patching**: If minor edge cases, missing test coverage, or lint/type issues are detected, the reviewer directly authors the fix, commits, and pushes to the PR branch:
   ```bash
   git commit -am "fix(test): add edge case coverage and tighten validation"
   git push
   ```
3. **Formal Approval**: Once the final commit SHA passes all checks, the reviewer posts a formal approval comment:
   ```bash
   gh pr review "$PR_URL" --approve -b "LGTM: verified candidate commit $(git rev-parse HEAD)"
   ```

---

## 5. Invariant Safeguards (PR #88 Core Rules)

Even in Lite Execution, the core engineering physics from PR #88 strictly apply:

- **Wait for `idle` Before Prompting AGY**: Never inject prompt text into an active AGY writer while it is synthesizing code or executing tools. Always wait for idle:
  ```bash
  herdr agent wait "$TARGET_PANE_ID" --until idle --timeout 60000
  ```
- **Exact-SHA Binding**: A PR approval is valid ONLY for the exact SHA reviewed. Pushing a new commit immediately invalidates previous approvals and requires a delta check.
- **Two-Round Limit**: If a reviewer and implementer exchange 2 rounds without achieving clean approval, **stop automated retries**. Escalate the concrete blocker to the user or supervisor.
- **Material Findings Cannot Be Waived**: Never downgrade functional bugs to advisory comments to force a merge.
- **Two-Stage Teardown**:
  1. *Prompt Pane Retirement*: Close reviewer and implementer paneles once work is approved:
     ```bash
     herdr pane close "$REV_PANE_ID"
     herdr pane close "$IMPL_PANE_ID"
     ```
  2. *Worktree Removal Gate*: Only delete the worktree after verifying `git status --porcelain` is clean:
     ```bash
     test -z "$(git -C "$WORKTREE_PATH" status --porcelain)" && git worktree remove "$WORKTREE_PATH"
     ```
     Never use `git worktree remove --force` on dirty or ambiguous worktrees.
