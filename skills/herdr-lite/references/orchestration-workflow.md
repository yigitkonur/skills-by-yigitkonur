# Herdr-Lite Orchestration Workflow

This reference provides the complete, step-by-step lifecycle for dispatching tasks, managing parallel Git worktrees, supervising side-by-side implementer and reviewer panes, and safely retiring resources.

---

## 1. Lifecycle Overview

```
[ Problem Input: Issue / Bug / Task ]
                 │
                 ▼
[ Phase 1: Native Worktree Provisioning ]
   • Execute herdr worktree create
   • Capture workspace_id and root_pane.pane_id
                 │
                 ▼
[ Phase 2: AGY Implementer Execution ]
   • Launch AGY into root pane
   • Implement feature with behavioral tests (TDD)
   • Commit changes and open PR via gh pr create
                 │
                 ▼
[ Phase 3: Sibling Reviewer (Review-and-Fix) ]
   • Split tab right from implementer pane
   • Launch independent reviewer (gemini-3.8-flash-high)
   • Reviewer audits candidate SHA, authors test/bug patches, pushes
   • Reviewer posts approval on GitHub PR
                 │
                 ▼
[ Phase 4: Verification & Safe Teardown ]
   • Close worker panes promptly (herdr pane close)
   • Gate worktree removal on clean git status
   • Merge approved PR
```

---

## 2. Phase 1: Native Worktree & Pane Provisioning

Do not spawn detached tabs and then manually configure worktrees. Use Herdr's native `worktree create` command, which provisions the Git worktree, a dedicated Herdr workspace, and the root pane in a single atomic operation:

```bash
TASK_ID="182"
REPO_ROOT="/root/dev/my-project"
WORKTREE_PATH="/root/dev/my-project-task-${TASK_ID}"
BRANCH_NAME="fix/issue-${TASK_ID}"

# Provision worktree and capture coordinates:
WORKTREE_JSON="$(herdr worktree create "$REPO_ROOT" "$WORKTREE_PATH" --branch "$BRANCH_NAME")"
WORKSPACE_ID="$(echo "$WORKTREE_JSON" | jq -er '.result.workspace.workspace_id')"
IMPL_PANE_ID="$(echo "$WORKTREE_JSON" | jq -er '.result.root_pane.pane_id')"
```

---

## 3. Phase 2: Launching the Implementer

Start the Antigravity (AGY) implementer in the root pane:

```bash
herdr agent start "impl-${TASK_ID}" --kind agy --pane "$IMPL_PANE_ID" -- --model "$IMPL_MODEL"
```

### Implementer Mission Discipline:
1. **Behavioral Testing (TDD)**: Author a failing behavioral test verifying the bug or required feature before changing application logic.
2. **Atomic Commits**: Stage and commit only owned files with standard conventional commit headers:
   ```bash
   git add <owned_files>
   git commit -m "fix(core): resolve race condition in task coordinator (#${TASK_ID})"
   ```
3. **Open GitHub PR**: Push the branch and create a PR:
   ```bash
   git push -u origin "$BRANCH_NAME"
   PR_URL="$(gh pr create --title "fix(core): resolve task coordinator race" --body "Closes #${TASK_ID}")"
   ```

---

## 4. Phase 3: Spawning the Sibling Reviewer (Review-and-Fix)

To audit and harden the candidate without context switching, split the worktree tab to the right:

```bash
REV_PANE_ID="$(herdr pane split --pane "$IMPL_PANE_ID" --direction right --cwd "$WORKTREE_PATH" --no-focus | jq -er '.result.pane.pane_id')"
herdr agent start "rev-${TASK_ID}" --kind agy --pane "$REV_PANE_ID" -- --model "gemini-3.8-flash-high"
```

### Reviewer Mission Brief:
Deliver the candidate SHA and PR URL to the reviewer:
```bash
# Ensure reviewer composer is ready:
herdr agent wait "$REV_PANE_ID" --until idle --timeout 60000

herdr agent prompt "$REV_PANE_ID" "Review PR candidate:
- Branch: $BRANCH_NAME
- Worktree: $WORKTREE_PATH
- Candidate SHA: $(git -C "$WORKTREE_PATH" rev-parse HEAD)
- PR URL: $PR_URL

Instructions:
1. Audit the exact candidate commit SHA for correctness, edge cases, and test coverage.
2. If edge case tests or minor bug fixes are needed, patch them directly in this worktree, commit, and push to the branch.
3. Once all tests and linters pass, post an approval review comment via gh pr review."
```

---

## 5. Phase 4: Two-Stage Safe Teardown

Once the PR review is approved and CI passes:

1. **Terminal / Pane Retirement**: Close worker panes immediately:
   ```bash
   herdr pane close "$REV_PANE_ID"
   herdr pane close "$IMPL_PANE_ID"
   ```
2. **Worktree Removal Gate**:
   - Verify the worktree is completely clean:
     ```bash
     test -z "$(git -C "$WORKTREE_PATH" status --porcelain)" || { echo "DIRTY WORKTREE: Preserving for investigation"; exit 1; }
     ```
   - Delete the worktree cleanly:
     ```bash
     git worktree remove "$WORKTREE_PATH"
     ```
   - *Never* use `git worktree remove --force` on uncommitted or ambiguous checkouts.
