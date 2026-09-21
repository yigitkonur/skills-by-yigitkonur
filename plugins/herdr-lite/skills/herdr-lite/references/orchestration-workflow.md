# Herdr-Lite Orchestration Workflow

This reference provides the complete, step-by-step lifecycle for dispatching tasks, managing parallel Git worktrees, supervising streaming implementer and reviewer panes side-by-side inside dedicated worktree workspaces, executing serial integration, and advancing through multi-wave dependency graphs.

---

## 1. Dual-Agent Leadership & Multi-Wave Streaming Architecture

Herdr-Lite operates a two-tier command structure in the primary control workspace:

- **CTO Agent (Pane 1, e.g. `wV:pH`)**: Focuses on strategic architecture, wave sequencing, DAG construction, serial merge decisions, and pair-programming with the user/founder.
- **Engineering Manager (EM) Agent (Pane 2, e.g. `wV:pJ`)**: A dedicated **AGY Agent** (NOT a simple bash terminal or shell script!) that actively manages the worker pool, receives implementer callbacks, monitors PRs, and coordinates reviews.

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
   • CTO builds DAG based on "Blocked by:" edges and write surfaces
   • Maximize parallelism across disjoint lanes in Wave 1
                           │
                           ▼
[ Step 2: Dedicated Worktree Workspace Provisioning (Current Wave) ]
   • herdr worktree create provisions Git worktree + dedicated Workspace
   • Pane 1: impl (Implementer runs TDD with /teamwork-preview, commits, opens PR)
                           │
                           ▼
[ Step 3: Streaming Side-by-Side Review Split & Callback Loop to EM Agent ]
   • Worker i reports to EM: "REPORT: status=DONE pr_url=<url>"
   • EM immediately splits the tab: herdr pane split --pane "$IMPL_PANE_ID" --direction right
   • Pane 2: review runs side-by-side; Implementer Pane 1 remains ALIVE and readable
   • Reviewer audits with domain skills, patches bugs, approves PR
                           │
                           ▼
[ Step 4: Full-Job Teardown & Serial Merge ]
   • Both review AND implementation finished? Close workspace
   • Rebase approved PRs serially onto main
   • Reconcile merge conflicts via resolving-merge-conflicts
   • Merge to main and remove clean worktree checkout
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

## 4. Step 2: Dedicated Worktree & Workspace Provisioning

> [!CAUTION]
> **Anti-Pattern (DO NOT DO)**: Running `git worktree add` in a shell and opening loose, independent tabs in the main workspace with `--cwd <path>`. This pollutes the control workspace, breaks Herdr's 1-to-1 workspace lifecycle tracking, and loses isolation.

> [!TIP]
> **Golden Pattern (ALWAYS DO)**: Run `herdr worktree create --cwd "$REPO_ROOT" --path "$WORKTREE_PATH" --branch "$BRANCH" --label "$LABEL" --no-focus`.
> Herdr automatically:
> 1. Creates the Git worktree at `$WORKTREE_PATH`.
> 2. Provisions an isolated Herdr workspace bound directly to the worktree.
> 3. Launches Pane 1 already inside the checkout directory.

For each ticket in the active wave, provision an isolated workspace:

```bash
TASK_ID="182"
REPO_ROOT="/root/dev/my-project"
WORKTREE_PATH="/root/dev/my-project-task-${TASK_ID}"
BRANCH_NAME="fix/issue-${TASK_ID}"

# 1. Provision worktree and capture coordinates:
WORKTREE_JSON="$(herdr worktree create --cwd "$REPO_ROOT" --path "$WORKTREE_PATH" --branch "$BRANCH_NAME" --label "task-${TASK_ID}" --no-focus)"
WORKSPACE_ID="$(echo "$WORKTREE_JSON" | jq -er '.result.workspace.workspace_id')"
IMPL_PANE_ID="$(echo "$WORKTREE_JSON" | jq -er '.result.root_pane.pane_id')"

# 2. Launch AGY Implementer in Pane 1:
herdr agent start "impl-${TASK_ID}" --kind agy --pane "$IMPL_PANE_ID" --timeout 45000 -- --model "gemini-3.8-flash-high" --dangerously-skip-permissions
```

### Implementer Mission Brief & `/teamwork-preview /herdr` Mandate:
When the Engineering Manager prompts the implementer, the prompt **MUST** start with `/teamwork-preview /herdr` (zero space after slash) and instruct the worker to assemble a specialized team:

```bash
herdr agent prompt "$IMPL_PANE_ID" "/teamwork-preview /herdr
You are the Lead Implementer for Task #${TASK_ID}.
Assemble and guide a specialized sub-team (e.g. Architect, Specialist, QA Verifier) to execute this task:

1. Implement behavioral tests first (TDD).
2. Fix the underlying issue with minimal surface changes.
3. Commit cleanly and push branch '$BRANCH_NAME'.
4. Open PR: gh pr create --title 'fix: issue #${TASK_ID}' --body 'Closes #${TASK_ID}'.
5. When complete, WRITE BACK TO THE ENGINEERING MANAGER with:
   REPORT: task_id=${TASK_ID} pr_url=<PR_URL> head_sha=\$(git rev-parse HEAD) status=DONE"
```

---

## 5. Step 3: Event-Driven Streaming Review (Side-by-Side Split Pane)

> [!IMPORTANT]
> **Side-by-Side Split & Implementation Preservation**:
> When a worker reports `status=DONE`, do NOT create a separate tab, and **NEVER** terminate the implementer pane!
> The implementer pane holds critical context: build logs, test failure traces, and agent transcripts.
> Instead, split the pane side-by-side in the **same tab** so both agents are co-located:

### Splitting the Pane Side-by-Side:
```bash
SPLIT_JSON="$(herdr pane split --pane "$IMPL_PANE_ID" --direction right --cwd "$WORKTREE_PATH" --no-focus)"
REV_PANE_ID="$(echo "$SPLIT_JSON" | jq -er '.result.pane.pane_id')"
herdr agent start "rev-${TASK_ID}" --kind agy --pane "$REV_PANE_ID" --timeout 45000 -- --model "gemini-3.8-flash-high" --dangerously-skip-permissions
```

### Deep Review with Domain Skills:
The reviewer operates in Pane 2 and applies specialized skills (`code-review`, `tdd`, `audit-completion`, `diagnosing-bugs`):
```bash
herdr agent wait "$REV_PANE_ID" --until idle --timeout 60000

herdr agent prompt "$REV_PANE_ID" "/teamwork-preview /herdr
Deep Review & Hardening for PR #${TASK_ID}:
- PR URL: $PR_URL
- Candidate SHA: $CANDIDATE_SHA
- Worktree: $WORKTREE_PATH

Instructions:
1. Use skills (code-review, tdd, audit-completion) to verify specifications, edge cases, and test suites.
2. Inspect the implementer's left pane output directly if troubleshooting test failures.
3. Review-and-Fix: If tests are missing or minor bugs are found, write the patches directly, run validation suites, commit, and push to the branch.
4. Post formal GitHub PR approval:
   gh pr review '$PR_URL' --approve -b 'LGTM: verified candidate commit $(git rev-parse HEAD)'
5. Send notification:
   APPROVED: task_id=${TASK_ID} pr_url=$PR_URL head_sha=$(git rev-parse HEAD)"
```

---

## 6. Step 4: Full-Job Teardown & Serial Merge

> [!IMPORTANT]
> **Complete Job Closure Law**:
> A task is only closed when **both** the review and implementation phases are fully finished.
> Prematurely killing the implementer when review begins is prohibited.
> Once PR approval is confirmed:
> 1. Close the dedicated workspace (terminating both implementer and reviewer panes cleanly):
>    `herdr workspace close "$WORKSPACE_ID"`
> 2. Gate worktree deletion strictly on `git status --porcelain`:
>    `test -z "$(git -C "$WORKTREE_PATH" status --porcelain)" && git worktree remove "$WORKTREE_PATH"`
> 3. Serially rebase approved candidate PR onto `main` and squash-merge:
>    `gh pr merge "$PR_URL" --squash --delete-branch`
> 4. Prune local branch and remotes (`git branch -D "$BRANCH_NAME"`, `git remote prune origin`).

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
