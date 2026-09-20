# Herdr-Lite Orchestration Workflow

This reference provides the complete, step-by-step lifecycle for dispatching tasks, managing parallel Git worktrees, supervising streaming implementer and reviewer tabs inside worktree workspaces, and executing serial integration.

---

## 1. Lifecycle & Streaming Architecture

```
[ Problem Input: Issue / Bug / Task Batch ]
                     │
                     ▼
[ Step 1: Parallelism Analysis & Wave Sizing ]
   • Classify tasks into Disjoint vs Coupled lanes
   • Maximize parallelism across independent write surfaces
                     │
                     ▼
[ Step 2: Native Worktree Provisioning ]
   • herdr worktree create provisions Git worktree + Workspace
   • Tab 1: impl (Implementer runs TDD, commits, opens PR)
                     │
                     ▼
[ Step 3: Event-Driven Streaming Review (No Lockstep Waiting) ]
   • When Worker i sends "I'm done: PR=<url>", Antigravity immediately:
   • Spawns Tab 2: review inside Worker i's Workspace
   • Reviewer (Gemini 3.8 Flash) runs in-depth audit with domain skills
   • Reviewer patches edge cases directly, commits, and approves PR
                     │
                     ▼
[ Step 4: Serial Merge & Conflict Resolution ]
   • Enqueue approved candidates into serial rebase-and-merge pipeline
   • Rebase cleanly onto moving main baseline (resolve conflicts if needed)
   • Merge to main, close workspace, remove worktree, notify user
```

---

## 2. Step 1: Parallelism Analysis & Wave Sizing

Before provisioning resources, the Antigravity orchestrator classifies incoming tasks based on write boundaries:

1. **Disjoint Parallelism (Maximized Concurrency)**:
   Tasks that touch non-overlapping directories, separate packages, or independent backend routes are assigned disjoint lanes. Launch all disjoint lanes concurrently in Wave 1.
2. **Coupled Work Rule**:
   Interdependent files, tightly coupled schema/service pairs, or shared utilities must be kept within a single writer lane to avoid cross-branch synchronization thrashing.

---

## 3. Step 2: Native Worktree & Workspace Provisioning

Use Herdr's native `worktree create` command. This creates the Git worktree, opens an isolated Herdr workspace, and launches a root pane in Tab 1:

```bash
TASK_ID="182"
REPO_ROOT="/root/dev/my-project"
WORKTREE_PATH="/root/dev/my-project-task-${TASK_ID}"
BRANCH_NAME="fix/issue-${TASK_ID}"

# 1. Provision worktree and capture coordinates:
WORKTREE_JSON="$(herdr worktree create "$REPO_ROOT" "$WORKTREE_PATH" --branch "$BRANCH_NAME")"
WORKSPACE_ID="$(echo "$WORKTREE_JSON" | jq -er '.result.workspace.workspace_id')"
IMPL_PANE_ID="$(echo "$WORKTREE_JSON" | jq -er '.result.root_pane.pane_id')"
IMPL_TAB_ID="$(echo "$WORKTREE_JSON" | jq -er '.result.root_pane.tab_id')"

# 2. Rename root tab to 'impl' for visual clarity:
herdr tab rename "$IMPL_TAB_ID" "impl"

# 3. Launch AGY Implementer:
herdr agent start "impl-${TASK_ID}" --kind agy --pane "$IMPL_PANE_ID" -- --model "$IMPL_MODEL"
```

### Implementer Mission Brief:
Instruct the implementer to follow TDD, commit, open a PR, and report completion:
```bash
herdr agent prompt "$IMPL_PANE_ID" "Execute Task #${TASK_ID}:
1. Implement behavioral tests first (TDD).
2. Fix the underlying issue with minimal surface changes.
3. Commit cleanly and push branch '$BRANCH_NAME'.
4. Open PR: gh pr create --title 'fix: issue #${TASK_ID}' --body 'Closes #${TASK_ID}'.
5. When complete, output notification:
   DONE: task_id=${TASK_ID} pr_url=<PR_URL> candidate_sha=$(git rev-parse HEAD)"
```

---

## 4. Step 3: Event-Driven Streaming Review (Inside Worktree Workspace)

> [!IMPORTANT]
> **No Lockstep Waiting**: When 7 worktrees are running in parallel, do not wait for all 7 to finish. As soon as Worker $i$ finishes and reports `DONE`, immediately open a dedicated review tab inside Worker $i$'s workspace!

### Spawning the Review Tab:
```bash
# Open Tab 2 for deep review inside the worktree's workspace:
REV_TAB_JSON="$(herdr tab create --workspace "$WORKSPACE_ID" --cwd "$WORKTREE_PATH" --label "review" --no-focus)"
REV_PANE_ID="$(echo "$REV_TAB_JSON" | jq -er '.result.root_pane.pane_id')"

# Launch independent reviewer:
herdr agent start "rev-${TASK_ID}" --kind agy --pane "$REV_PANE_ID" -- --model "gemini-3.8-flash-high"
```

### Deep Review with Domain Skills:
The reviewer operates with full terminal width in Tab 2 and applies specialized skills (`code-review`, `tdd`, `audit-completion`, `diagnosing-bugs`):

```bash
# Ensure reviewer is idle before prompting:
herdr agent wait "$REV_PANE_ID" --until idle --timeout 60000

herdr agent prompt "$REV_PANE_ID" "Deep Review & Hardening for PR #${TASK_ID}:
- PR URL: $PR_URL
- Candidate SHA: $CANDIDATE_SHA
- Worktree: $WORKTREE_PATH

Instructions:
1. Use skills (code-review, tdd, audit-completion) to verify specifications, edge cases, and test suites.
2. Review-and-Fix: If tests are missing or minor bugs are found, write the patches directly, run validation suites, commit, and push to the branch.
3. Post formal GitHub PR approval:
   gh pr review '$PR_URL' --approve -b 'LGTM: verified candidate commit $(git rev-parse HEAD)'
4. Send notification:
   APPROVED: task_id=${TASK_ID} pr_url=$PR_URL head_sha=$(git rev-parse HEAD)"
```

---

## 5. Step 4: Serial Merge & Safe Teardown

Once approved:
1. **Desktop / TUI Notification**:
   ```bash
   herdr notification show "Candidate Approved" \
     --body "Issue #${TASK_ID} approved and enqueued for merge." \
     --sound done
   ```
2. **Serial Integration**:
   Follow [references/serial-merge-and-conflicts.md](serial-merge-and-conflicts.md) to serially rebase onto `main`, resolve any conflicts, and land the PR.
3. **Safe Teardown**:
   - Close workspace: `herdr workspace close --workspace "$WORKSPACE_ID"`.
   - Verify `git status --porcelain` is clean in the worktree.
   - Remove worktree: `git worktree remove "$WORKTREE_PATH"`.
