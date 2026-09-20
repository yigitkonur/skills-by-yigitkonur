# Herdr-Lite Orchestration Workflow

This reference provides the complete, step-by-step lifecycle for dispatching tasks, managing parallel Git worktrees, supervising streaming implementer and reviewer tabs inside worktree workspaces, executing serial integration, and advancing through multi-wave dependency graphs.

---

## 1. Lifecycle & Multi-Wave Streaming Architecture

```
[ Problem Input: Conversation / Sentry Bugs / PRD Spec ]
                           │
                           ▼
[ Step 0: Automatic Ticket Intake (if no issues exist) ]
   • Decompose into vertical tracer-bullet slices
   • Create GitHub issues automatically via gh issue create
                           │
                           ▼
[ Step 1: Multi-Wave Dependency Graph (Waves 1 to 5) ]
   • Build DAG based on "Blocked by:" edges and write surfaces
   • Maximize parallelism across disjoint lanes in Wave 1
                           │
                           ▼
[ Step 2: Native Worktree Provisioning (Current Wave) ]
   • herdr worktree create provisions Git worktree + Workspace
   • Tab 1: impl (Implementer runs TDD, commits, opens PR)
                           │
                           ▼
[ Step 3: Streaming Review & "Write Back to Me" Loop ]
   • Worker i sends "REPORT: status=DONE pr_url=<url>"
   • Antigravity immediately spawns Tab 2: review in Workspace i
   • Reviewer audits with domain skills, patches bugs, approves PR
                           │
                           ▼
[ Step 4: Serial Merge & Conflict Resolution ]
   • Rebase approved PRs serially onto main
   • Reconcile merge conflicts via resolving-merge-conflicts
   • Merge to main and retire worktree resources
                           │
                           ▼
[ Step 5: Wave Advancement ]
   • All Wave k tickets merged? Trigger Wave k+1
   • Continue until all waves converge
```

---

## 2. Step 0: Automatic Ticket Intake & GitHub Issue Creation

When invoked without pre-existing GitHub issues, Antigravity parses the discussion or problem statement and creates structured issues directly:

1. **Vertical Tracer-Bullet Slicing**:
   Each ticket cuts across all required layers (schema, services, UI, tests) and declaring explicit blocking dependencies (see [references/ticket-decomposition-and-waves.md](ticket-decomposition-and-waves.md)).
2. **Automated Publishing**:
   ```bash
   gh issue create --title "<TITLE>" --body "## What to build\n...\n## Acceptance criteria\n...\n## Blocked by\n<DEPENDENCIES>"
   ```

---

## 3. Step 1: Multi-Wave Dependency Graph & Parallelism Sizing

Antigravity organizes the issues into up to 5 sequential execution waves:
- **Wave 1 (Disjoint Frontier)**: All tickets with `Blocked by: None` that touch disjoint writable surfaces are launched concurrently.
- **Wave 2**: Tickets gated directly on Wave 1 deliverables.
- **Waves 3–5**: Multi-stage follow-ups or final integration sweeps.

---

## 4. Step 2: Native Worktree & Workspace Provisioning

For each ticket in the active wave, provision an isolated workspace:

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

### Implementer Mission Brief & Callback Mandate:
Instruct the implementer to write behavioral tests, commit, push, open a PR, and write back to the orchestrator:
```bash
herdr agent prompt "$IMPL_PANE_ID" "Execute Task #${TASK_ID}:
1. Implement behavioral tests first (TDD).
2. Fix the underlying issue with minimal surface changes.
3. Commit cleanly and push branch '$BRANCH_NAME'.
4. Open PR: gh pr create --title 'fix: issue #${TASK_ID}' --body 'Closes #${TASK_ID}'.
5. When complete, WRITE BACK TO ME with:
   REPORT: task_id=${TASK_ID} pr_url=<PR_URL> head_sha=$(git rev-parse HEAD) status=DONE"
```

---

## 5. Step 3: Event-Driven Streaming Review (Inside Worktree Workspace)

> [!IMPORTANT]
> **No Lockstep Waiting**: When multiple parallel worktrees run, do not wait for all of them to finish. As soon as Lane $i$ writes back `status=DONE`, immediately open Tab 2 (`review`) inside Workspace $i$!

### Spawning the Review Tab:
```bash
REV_TAB_JSON="$(herdr tab create --workspace "$WORKSPACE_ID" --cwd "$WORKTREE_PATH" --label "review" --no-focus)"
REV_PANE_ID="$(echo "$REV_TAB_JSON" | jq -er '.result.root_pane.pane_id')"
herdr agent start "rev-${TASK_ID}" --kind agy --pane "$REV_PANE_ID" -- --model "gemini-3.8-flash-high"
```

### Deep Review with Domain Skills:
The reviewer operates in Tab 2 and applies specialized skills (`code-review`, `tdd`, `audit-completion`, `diagnosing-bugs`):
```bash
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

## 6. Step 4: Serial Merge & Conflict Resolution

Follow [references/serial-merge-and-conflicts.md](serial-merge-and-conflicts.md):
1. Serially rebase approved candidate PRs onto moving `main`, using non-interactive continuation (`GIT_EDITOR=true git rebase --continue`).
2. If conflict markers occur, reconcile markers with semantic integrity—never blindly choosing `--ours` or `--theirs`—and push with lease (`git push --force-with-lease -u origin "$BRANCH_NAME"`).
3. Merge candidate into `main` (`gh pr merge "$PR_URL" --squash --delete-branch`). If reviewer and PR author share the same token, submit a review comment instead of self-approval before merging.
4. Execute clean teardown: verify clean worktree, close Herdr tabs and workspace (`herdr workspace close "$WORKSPACE_ID"`), remove worktree (`git worktree remove "$WORKTREE_PATH"`), delete local branch (`git branch -D "$BRANCH_NAME"`), and prune remotes (`git remote prune origin`).

---

## 7. Step 5: Continuous Wave Advancement

Once all PRs in Wave $k$ are merged:
1. Announce wave completion via Herdr desktop toast:
   ```bash
   herdr notification show "Wave ${CURRENT_WAVE} Completed" \
     --body "All PRs merged to main. Advancing to Wave $((CURRENT_WAVE + 1))." \
     --sound done
   ```
2. Automatically dispatch the next wave of newly unblocked tickets.
3. Repeat until all waves are complete.
