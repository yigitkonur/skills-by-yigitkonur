# Recovery, Quota & Worktree Safeguards

This reference provides recovery procedures for hung sessions, quota limits, stuck Git locks, and safe worktree cleanup in Herdr-Lite.

---

## 1. Process Reconciliation vs. Blind Kills

**Strictly Prohibited**: Executing `kill -9`, blanket `pkill -f`, or killing processes without inspecting state. Blind kills orphan Git locks (`index.lock`), corrupt shared PTY buffers, and destroy work in progress.

Before restarting or unblocking a pane:
1. **Query Active Processes**:
   ```bash
   herdr pane process-info --pane "$PANE_ID"
   ```
2. **Reconcile Git Locks**:
   If Git commands fail with `Another git process seems to be running`:
   - Discover the lock file path:
     ```bash
     LOCK_PATH="$(git -C "$WORKTREE_PATH" rev-parse --git-path index.lock)"
     ```
   - Check if an active process holds the lock:
     ```bash
     lsof "$LOCK_PATH"
     ```
   - Only remove `index.lock` if `lsof` shows no active process holding it and prior pane processes are confirmed terminated.

---

## 2. Quota & Hang Recovery Safeguards

When an agent encounters genuine quota exhaustion or a verified hard hang:

1. **Targeted Interruption**:
   Send a surgical `ctrl+c` to interrupt the stuck agent turn:
   ```bash
   herdr agent send-keys "$PANE_ID" ctrl+c
   ```
2. **State Inventory**:
   Capture the exact AGY conversation ID from Herdr session metadata:
   ```bash
   AGY_CONVERSATION_ID="$(herdr pane get --pane "$PANE_ID" | jq -r '.result.pane.agent_session.value')"
   ```
3. **Pre-Resume Verification**:
   Confirm the process has terminated and the pane rests at a clean shell prompt (`$`, `%`):
   ```bash
   herdr pane read --source visible --lines 5 "$PANE_ID"
   ```
4. **Exact Conversation Resume**:
   Reconnect to the exact conversation history using its explicit ID:
   ```bash
   agy --conversation "$AGY_CONVERSATION_ID"
   ```
   > [!CAUTION]
   > **Never use `--continue`**. `--continue` attaches to the globally most recent conversation and can cross-contaminate lane state across parallel worktrees.
5. **Single Continuation Prompt**:
   Verify the composer is input-ready, then transmit **exactly ONE** prompt message: `"continue"`.
6. **Quota Stop Rule**:
   If the quota failure returns immediately, **stop**. Do not loop or retry. Escalate to the developer or switch to an authorized alternative model tier.

---

## 3. Worktree Removal Gate & Pane Retirement

Resource cleanup follows two strict gates:

### Gate A: Pane & Workspace Retirement
- Close the reviewer and implementer resources as soon as PR review is approved:
  ```bash
  herdr tab close "$REV_TAB_ID"
  herdr workspace close "$WORKSPACE_ID"
  ```
- Alternatively, close individual panes:
  ```bash
  herdr pane close "$REV_PANE_ID"
  herdr pane close "$IMPL_PANE_ID"
  ```

### Gate B: Worktree Removal Gate (`git worktree remove`)
- Worktree cleanup is a separate engineering gate; closing panes or workspaces does not authorize deleting checkouts.
- **Mandatory PR Remote Merge Gate**:
  Never remove a worktree workspace or delete its branch until the PR has been verified as MERGED on GitHub remote:
  ```bash
  gh pr view "$PR_URL" --json state -q .state | grep -iq "MERGED" || {
    echo "ERROR: PR $PR_URL is not yet merged. Preserving worktree $WORKTREE_PATH"
    exit 1
  }
  ```
- **Cleanliness Check**:
  ```bash
  DIRTY_FILES="$(git -C "$WORKTREE_PATH" status --porcelain)"
  if [ -n "$DIRTY_FILES" ]; then
    echo "ERROR: Worktree is dirty. Preserving for review:"
    echo "$DIRTY_FILES"
    exit 1
  fi
  ```
- **Removal**:
  ```bash
  herdr worktree remove --workspace "$WORKSPACE_ID"
  # Or: git worktree remove "$WORKTREE_PATH"
  ```
- **Branch Retirement & Prune**:
  Once the worktree is unlinked, delete the local merged branch and prune remotes:
  ```bash
  git branch -D "$BRANCH_NAME"
  git remote prune origin
  ```
- *No Force Deletion*: `git worktree remove --force` is strictly prohibited without explicit human authorization.

---

## 4. Subagent Model Tiering & Concurrency Guard (429 Quota Exhaustion Prevention)

When running multi-agent swarms in parallel Herdr split panes or subagents:

1. **The Concurrency Anti-Pattern**:
   Launching 3+ subagents simultaneously using `Model: "inherit"` (defaulting to the heaviest multi-modal reasoning models like Gemini 3.8 Flash Pro/High) exhausts individual per-minute API quotas (`RESOURCE_EXHAUSTED (code 429)`) within ~60 tool invocations.

2. **Strict Two-Tier Model Policy**:
   - **Tier 1 (Heavy / Deep Reasoning)**: Reserved exclusively for CTO, strategic wave decomposition, deep architectural audits, and high-risk review (`--model gemini-3.8-flash-pro` / `inherit` / `/boost`).
   - **Tier 2 (High-Throughput / Fast Workers)**: Implementers, bugfix engineers, exploratory test scouts, linting, syntax gates, and TDD regression suites MUST specify high-throughput flash models (`--model gemini-3.8-flash` or `Model: "flash"`).

3. **Concurrency Throttling**:
   - Limit concurrent subagents to at most **2–3 active agents** per host.
   - If quota exhaustion (429) is observed on any agent, **immediately pause new lane dispatch**, downgrade worker tasks to `flash`, and sequence runs sequentially until rate counters reset.

---

## 5. Whole-Fleet Wait Obsession & Streaming Review Protocol

1. **The "Wait Obsession" Anti-Pattern**:
   Orchestrators often assume that because tasks are grouped into "Wave 1", "Wave 2", etc., they must execute a single blocking wait for every implementer in Wave 1 to complete before initiating any reviews or merges. This causes:
   - Starvation of reviewer capacity while fast tasks wait for the slowest task in the wave.
   - Delayed feedback loops where bugs in early tasks remain unreviewed for hours.
   - Sudden merge contention spikes at wave boundaries instead of smooth serial integration.

2. **Streaming Reviews Law**:
   - Reviews are decoupled per-lane. As soon as task $i$ completes and opens a PR, its reviewer starts immediately in a side-by-side pane.
   - The orchestrator maintains an active, non-blocking monitoring loop:
     - Query active lanes or use targeted short waits (`herdr agent wait <lane> --until idle --timeout 5000`).
     - The moment an implementer transitions to `done` or `idle` with an open PR, split the tab (`herdr pane split --direction right`), bypass the folder trust prompt (`herdr pane send-keys "$REV_PANE" enter`), and prompt the reviewer.
     - Never let finished tasks sit idle waiting for unfinished tasks in the same wave.
   - Approvals also stream: as each review is approved (`REVIEW_APPROVED`), it enters the serial merge pipeline immediately without waiting for sibling reviews.

3. **Recovery from Hung / Stalled Waits**:
   - If an orchestrator accidentally entered an unbounded blocking wait, interrupt it with `ctrl+c`.
   - Run `herdr agent list` to inspect the true live state across all panes.
   - Any lane with status `done` or `idle` with an open PR should be immediately split and transitioned to review.

