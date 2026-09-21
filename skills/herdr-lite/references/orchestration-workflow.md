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
BRANCH="fix/issue-${TASK_ID}"

# 1. Provision worktree and capture coordinates:
WORKTREE_JSON="$(herdr worktree create --cwd "$REPO_ROOT" --path "$WORKTREE_PATH" --branch "$BRANCH" --label "task-${TASK_ID}" --no-focus)"
WS_ID="$(echo "$WORKTREE_JSON" | jq -er '.result.workspace.workspace_id')"
IMPL_PANE_ID="$(echo "$WORKTREE_JSON" | jq -er '.result.root_pane.pane_id')"

# 2. Launch AGY Implementer in Pane 1:
herdr agent start "impl-${TASK_ID}" --kind agy --pane "$IMPL_PANE_ID" --timeout 45000 -- --model "gemini-3.8-flash-high" --dangerously-skip-permissions
```

### Slash Command Selection & Team Structure Rules:
1. **Zero-Space Prefix Syntax**: Slash commands must be placed at the **very start** of the prompt string with **strictly zero space** after the slash:
   - `/teamwork-preview` (NOT `/ teamwork-preview`)
   - `/boost` (NOT `/ boost`)
2. **Implementation Command Selection**:
   - **Standard Implementation Tasks**: Prefix with `/teamwork-preview /herdr`. The prompt **MUST** explicitly specify how the sub-team will be created, even for small teams (e.g. assigning explicit responsibilities across 2–3 roles).
   - **Simple Tasks**: For minor tweaks (e.g. 1-line typo fix, docs URL update, single config constant), skip `/teamwork-preview` and run directly.
   - **Deep / Extremely Hard Scenarios**: For high-complexity tasks (e.g. distributed consensus, complex DB migration locks, core algorithmic engines), prefix with `/boost /herdr` to engage deep reasoning and multi-perspective verification.

### Implementer Mission Brief Example:
When the Engineering Manager prompts the implementer, structure the prompt with explicit sub-team roles:

```bash
herdr agent prompt "$IMPL_PANE_ID" "/teamwork-preview /herdr
You are the Lead Implementer for Task #${TASK_ID}.
Assemble and guide a specialized sub-team to execute this task:
- Role 1 (Lead Developer): Implements core business logic, schema changes, and service interfaces.
- Role 2 (TDD Specialist): Authors behavioral test cases first (red), then verifies green state.
- Role 3 (QA Verifier): Enforces Fast Syntax Gate, edge-case assertions, and git commit cleanliness.

Workflow:
1. Implement behavioral tests first (TDD).
2. Fix the underlying issue with minimal surface changes.
3. Commit cleanly and push branch '$BRANCH'.
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

### Deep Review with Domain Skills & `/boost` Option:
The reviewer operates in Pane 2. For standard reviews, use default review instructions.
For **very deep reviews** on complex, high-risk, or security-sensitive PRs, prefix the prompt with `/boost /herdr` to invoke deep reasoning and adversarial verification:

```bash
herdr agent wait "$REV_PANE_ID" --until idle --timeout 60000

herdr agent prompt "$REV_PANE_ID" "/boost /herdr
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

### Non-Monolithic Streaming Wait Loop (Per-Task Wait, Zero Wave-Blocking):

> [!IMPORTANT]
> **The Streaming Review Rule**:
> Never wait for ALL implementers in a wave to finish before starting reviews!
> If a wave has multiple tasks, waiting for the whole wave to finish causes massive idle latency and starves reviewers.
> Instead, track active workers with per-task waits (`herdr agent wait "$IMPL_PANE_ID" --until done --until idle --timeout <MS>`).
> As soon as **any single worker** reports `DONE` or enters `idle` with an open PR, **immediately launch its reviewer in Pane 2 via `herdr pane split`**.
> While Reviewer 1 audits Task 1, Worker 2 and Worker 3 continue implementing.
> When Reviewer 1 approves Task 1, the CTO can begin serial rebase-and-merge of Task 1 immediately.
> The whole wave wait does not have to finish before individual task reviews and merges proceed.

```bash
# Streaming per-task wait and review launch pattern:
# For each running implementer, wait deterministically for task completion:
herdr agent wait "$IMPL_PANE_ID" --until done --until idle --timeout 180000

# Confirm PR is open before launching reviewer:
PR_URL="$(gh pr list --head "$BRANCH" --json url -q '.[0].url')"
test -n "$PR_URL" || { echo "No PR open on $BRANCH; awaiting completion"; exit 1; }

# Immediately launch its reviewer in Pane 2 side-by-side:
SPLIT_JSON="$(herdr pane split --pane "$IMPL_PANE_ID" --direction right --cwd "$WORKTREE_PATH" --no-focus)"
REV_PANE_ID="$(echo "$SPLIT_JSON" | jq -er '.result.pane.pane_id')"
herdr agent start "rev-${TASK_ID}" --kind agy --pane "$REV_PANE_ID" --timeout 45000 -- --model "gemini-3.8-flash-high" --dangerously-skip-permissions

# Deliver the deep review prompt before entering wait state:
herdr agent prompt "$REV_PANE_ID" "/boost /herdr Review PR $PR_URL on branch $BRANCH. Audit against specs, run hermetic verification, and post approval or fix patches directly."
herdr agent wait "$REV_PANE_ID" --until idle --timeout 180000
```

---

## 6. Step 4: CTO Active Supervision & Engineering Manager Wave Handover

> [!IMPORTANT]
> **Zero Blindness Supervision Mandate**:
> The CTO must never poll downstream GitHub/Git status in a detached loop while leaving the Engineering Manager in Pane 2 untracked.
> The CTO must actively supervise and synchronize with the EM:
> 1. Deterministically block on EM turn completion:
>    `herdr agent wait "$EM_PANE_ID" --until idle --timeout 60000`
> 2. Read EM's live screen buffer to capture lane status and blockers:
>    `herdr pane read "$EM_PANE_ID" --lines 100`
> 3. Actively interrogate the EM if silent, stalled, or at wave boundaries:
>    `herdr agent prompt "$EM_PANE_ID" "CTO STATUS INTERROGATION: Report active lanes, PR URLs, candidate SHAs, blockers, and next wave DAG."`

### Structured Wave Handover Protocol:
When all lanes in active Wave $k$ reach completion and PRs are approved, the EM outputs a formal handover block:

```text
WAVE_COMPLETE: wave=WAVE_D prs=[#74, #75, #76, #77, #78] shas=[820caa1, 6e906fd, ...] next_wave=WAVE_E next_issues=[#39, #26, #30, #31, #6] status=AWAITING_SERIAL_MERGE
```

The CTO reads this block from the EM pane, runs baseline gates, serially rebases candidate PRs onto `main`, and executes squash merges.

---

## 7. Step 5: Full-Job Teardown & Worktree Retirement

> [!IMPORTANT]
> **Complete Job Closure Law**:
> A task is only closed when **both** the review and implementation phases are fully finished and confirmed merged to `main`.
> Prematurely killing the implementer when review begins is prohibited.
> Once candidate PR approval and serial squash-merge onto `main` are confirmed:
> 1. Confirm PR status is MERGED on remote (abort if not merged):
>    ```bash
>    gh pr view "$PR_URL" --json state -q .state | grep -iq "MERGED" || { echo "PR $PR_URL is not MERGED; aborting teardown"; exit 1; }
>    ```
> 2. Confirm clean working tree (abort if dirty):
>    ```bash
>    test -z "$(git -C "$WORKTREE_PATH" status --porcelain)" || { echo "Worktree $WORKTREE_PATH is dirty; aborting teardown"; exit 1; }
>    ```
> 3. Retire implementer and reviewer agent panes in the workspace:
>    ```bash
>    herdr pane close --pane "$IMPL_PANE_ID" 2>/dev/null || true
>    herdr pane close --pane "$REV_PANE_ID" 2>/dev/null || true
>    ```
> 4. Remove the worktree checkout and unregister the workspace via Herdr:
>    ```bash
>    herdr worktree remove --workspace "$WS_ID"
>    ```
> 5. Delete the local branch and prune remotes:
>    ```bash
>    git -C "$REPO_ROOT" branch -D "$BRANCH"
>    git -C "$REPO_ROOT" remote prune origin
>    ```
> 6. Verify zero lingering worktrees remain:
>    ```bash
>    git -C "$REPO_ROOT" worktree list
>    ```

---

## 8. Step 6: Continuous Wave Advancement

Once all PRs in Wave $k$ are merged and verified:
1. Announce wave completion via Herdr desktop toast:
   ```bash
   herdr notification show "Wave ${CURRENT_WAVE} Completed" \
     --body "All PRs merged to main. Advancing to Wave $((CURRENT_WAVE + 1))." \
     --sound done
   ```
2. The CTO prompts the EM to unlock and dispatch the next wave of tickets:
   ```bash
   herdr agent prompt "$EM_PANE_ID" "CTO DIRECTION: Wave ${CURRENT_WAVE} merged cleanly. Proceed with Wave $((CURRENT_WAVE + 1)) dispatch."
   ```
3. Repeat until all waves converge to zero open issues.
