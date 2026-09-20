# Parallel Capacity, Clean Review & Serial PR Integration

Use this guide when coordinating multiple concurrent tasks, managing multi-worktree capacity, or running a multi-PR integration wave.

---

## 1. The Fundamental Law of Multi-Agent Swarms

> **Code synthesis is embarrassingly parallel ($O(1)$ scaling), but software integration is strictly serial ($O(N^2)$ interaction space).**

- **Parallelize Synthesis**: Multiple agents can plan, write unit tests, and draft feature code concurrently in isolated Git worktrees without interference.
- **Serialize Integration**: Merging multiple branches cannot be done in parallel without risking semantic interaction hazards. PRs must be audited in a clean context and integrated one by one into a moving, verified baseline.

---

## 2. Resource Allocation & Capacity Budget

Before launching parallel lanes, establish a capacity budget:

| Resource | Limits & Invariants |
|---|---|
| **Worktrees** | 1:1 mapping: each concurrent task gets exactly one dedicated worktree checkout under `.worktrees/<task>`. Never share working checkouts. |
| **Model Fleet** | Single-model strictness: orchestrator, workers, and reviewers all execute on the **same model** (`--model <model>`). |
| **Compiler / Test Leases** | Parallel native compilation (e.g. `xcodebuild`, heavy Rust builds) exhausts CPU and RAM, causing system freezes or OOM panics. Enforce a **Build Lease**: serialize heavy test runs and compilation passes while parallelizing text/code generation. |
| **Reviewers** | Reviewers run in clean context windows. They do not need dedicated write checkouts; they audit the pull request diff via GitHub CLI (`gh pr diff <PR_NUMBER>`). |

---

## 3. The 6-Stage PR Delivery Lifecycle

Every feature follows this progression:

```
[Worktree Isolated] 
       │
       ▼
[TDD Implementation (Red -> Green)]
       │
       ▼
[Open Draft PR (gh pr create --draft)]
       │
       ▼
[Worker Pushes Callback to Orchestrator Pane]
       │
       ▼
[Clean-Context Reviewer Audits Diff]
       ├── (Changes Requested) ──> [Worker Fixes in Worktree]
       └── (Approved)
               │
               ▼
[Promote to Ready (gh pr ready)]
       │
       ▼
[Serial Rebase on origin/main & Verification]
       │
       ▼
[Squash Merge & Container Cleanup]
```

### Stage 1: Dedicated Worktree Allocation
```bash
git worktree add -b feature/<task> .worktrees/<task> origin/main
herdr tab create --workspace "$CALLER_WS_ID" --cwd "$PWD/.worktrees/<task>" --label "<task>" --no-focus
```

### Stage 2: TDD & Implementation
The worker implements unit tests demonstrating the missing functionality (Red), writes the minimal code to satisfy the tests (Green), and commits changes.

### Stage 3: Draft Pull Request
The worker pushes its branch and opens a Draft PR:
```bash
git push origin feature/<task>
gh pr create --draft --title "feat: <task>" --body "$(cat .agent-runs/report.md)"
```

### Stage 4: Worker Callback Notification
The worker notifies the orchestrator pane directly:
```bash
herdr agent prompt "$CALLER_PANE_ID" \
  "I'm the herdr agent in pane $WORKER_PANE_ID. I've finished feature/<task>. PR #$PR_NUM is open in Draft. Tests pass. Read my report: herdr agent read $WORKER_PANE_ID --source recent-unwrapped --lines 100"
herdr notification show "Task Finished" --body "Draft PR #$PR_NUM open" --sound done
```

### Stage 5: Clean-Context PR Review
**Never review code in the implementer agent's pane.**
1. Spawn a clean reviewer agent on the same model in a new split pane:
   ```bash
   herdr pane split --pane "$CALLER_PANE_ID" --direction right --no-focus
   herdr agent start "reviewer-$PR_NUM" --kind codex --pane "$REVIEWER_PANE_ID" -- --model "$CURRENT_MODEL"
   ```
2. The reviewer inspects `gh pr diff $PR_NUM` and tests against specifications and quality standards.
3. If issues are found: reviewer submits comments (`gh pr review $PR_NUM --request-changes`). Orchestrator instructs worker to fix.
4. If approved: reviewer submits approval (`gh pr review $PR_NUM --approve`).

### Stage 6: Promotion & Serial Rebase Integration
1. Promote PR to ready:
   ```bash
   gh pr ready $PR_NUM
   ```
2. Rebase onto current `origin/main` to resolve any semantic or syntactic drift:
   ```bash
   git -C .worktrees/<task> fetch origin main
   git -C .worktrees/<task> rebase origin/main
   ```
3. Run verification tests on the rebased branch:
   ```bash
   npm test / pytest / cargo test
   ```
4. Push rebased commits:
   ```bash
   git -C .worktrees/<task> push --force-with-lease
   ```
5. Merge serially:
   ```bash
   gh pr merge $PR_NUM --squash --delete-branch
   ```
6. Cleanup:
   ```bash
   herdr tab close "$WORKER_TAB_ID"
   git worktree remove .worktrees/<task> --force
   ```

---

## 4. Handling Merge Conflicts with Ownership Mindset

When multiple PRs merge into `main`, downstream branches will inevitably encounter merge conflicts. Treat conflict resolution as standard engineering execution, not an escalation barrier:

1. **Detect Conflict Early**:
   `gh pr view $PR_NUM --json mergeable` reports `CONFLICTING`.
2. **Rebase in the Worker's Worktree**:
   ```bash
   git -C .worktrees/<task> fetch origin main
   git -C .worktrees/<task> rebase origin/main
   ```
3. **Resolve Conflict Markers**:
   - Inspect each conflicting file: `git status`.
   - Preserve both upstream bug fixes and branch feature logic.
   - Stage resolved files: `git add <file>`.
   - Continue rebase: `git rebase --continue`.
4. **Re-Verify with Tests**:
   Never assume a conflict resolution works simply because Git markers disappeared. Run the test suite:
   ```bash
   npm test / cargo test
   ```
5. **Force-Push with Lease**:
   ```bash
   git -C .worktrees/<task> push --force-with-lease
   ```
