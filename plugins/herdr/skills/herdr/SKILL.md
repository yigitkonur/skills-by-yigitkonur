---
name: herdr
description: "Use if orchestrating coding agents, parallel subagents, isolated Git worktrees, and clean-context PR reviews using the Herdr multiplexer."
---

# Herdr

Herdr is an external multiplexer and supervisor control plane for AI coding agents. It decouples topology (`workspace` → `tab` → `pane`), OS processes (`pty`), and cognitive agents (`agent`), enabling a single model or harness to orchestrate multiple subagents concurrently without trapping them in headless subshells or blinding human supervisors.

Orchestration follows an explicit chain: **CTO** → **Engineering Manager (EM)** → **Multi-Harness Executors (AGY, Codex, Claude Code)**.

---

## 1. Role Selection (Cold Reader Intake)

Every cold reader identifies its assigned role first. Read only the sections and references for your role.

| Assigned Role | Authority & Scope | Execute | Skip |
|---|---|---|---|
| **CTO** | Strategic governance, architectural gates, candidate evidence sign-off. | §1, §2 (CTO path) | §3–§7 execution (delegate to EM) |
| **Engineering Manager (EM)** | Central orchestration: `state.yaml`, task dispatch, report intake, reviewer scheduling, milestone publication, terminal retirement. | §1–§7 | Direct feature code authoring; pushing to `main` |
| **Implementer** | Feature implementation, local commits, atomic report publication in assigned worktree. | §1, §2, §4, references/report-contract.md | §3 (EM-only); editing `state.yaml` |
| **Fresh Reviewer** | Independent read-only audit of exact candidate commit SHA in clean context. | §1, §2, §5, references/report-contract.md | §3, §4, §6; editing production code |
| **Integration/Recovery**| Worktree integration or bounded diagnostic probes/recovery. | §1, §2, §6, §7, references/stopped-agent-recovery.md | §3–§5 |

> [!IMPORTANT]
> **No Management Bootstrapping**: Assigned executor roles select only execution and evidence paths. Never infer you are an orchestrator or spawn nested subagents.
> **Runtime Is Not Role (Harness-Agnostic Fleet)**: The execution engine (`agy`, `codex`, `claude`) does not define the organizational role. CTO, Engineering Manager, Implementers, and Reviewers can run under any supported harness. Codex is strictly optional; Antigravity (AGY) natively supports full-stack orchestration out of the box.
> **No Execution Limits on Autonomous Agents**: Agents do not have arbitrary step or turn limits. Longevity is sustained through disk-backed state checkpoints (`state.yaml`), event-driven push callbacks (token efficiency without polling), and finite failure budgets (2-strike review limit) rather than artificial execution caps.

---

## 2. Discover, Register, Verify

### 2a. Cold Bootstrap Sequence (CTO → EM → Workers)

Before workers exist, the CTO establishes the leadership pair. Leadership resides in **exactly two panes in ONE shared tab**: CTO on the LEFT, EM on the RIGHT. Workers and reviewers run in separate per-task tabs or worktree workspaces.

1. **CTO captures coordinates and creates the EM pane**:
   ```bash
   # Discover CTO own coordinates and leadership tab:
   CTO_PANE_ID="$(herdr pane current | jq -r .result.pane.pane_id)"
   LEADERSHIP_TAB_ID="$(herdr pane current | jq -r .result.pane.tab_id)"

   # Split right from CTO, capturing the returned EM pane ID:
   EM_PANE_ID="$(herdr pane split --pane "$CTO_PANE_ID" --direction right --cwd "$RUN_ROOT" --no-focus | jq -r .result.pane.pane_id)"

   # Launch EM into returned shell pane with chosen harness (defaults to ambient/agy):
   EM_KIND="${HERDR_AGENT_KIND:-agy}"
   herdr agent start "herdr-engineering-manager" --kind "$EM_KIND" --pane "$EM_PANE_ID" -- --model "$EM_MODEL"
   ```
2. **Verify Leadership Topology**:
   Confirm SAME tab, exactly two panes, CTO left (x=0) and EM right (x>0):
   ```bash
   herdr tab get "$LEADERSHIP_TAB_ID"
   herdr pane layout --pane "$CTO_PANE_ID"
   ```
3. **CTO dispatches EM brief** with mission scope, run root path, CTO return address (`$CTO_PANE_ID`), and authorized model tiers.
4. **EM allocates workers/reviewers** into dedicated worktree tabs/workspaces, capturing returned IDs, and launches the executor agent:
   ```bash
   TAB_INFO="$(herdr tab create --workspace "$WS_ID" --cwd "$TASK_CWD" --label "$TASK_LABEL" --no-focus)"
   WORKER_TAB_ID="$(echo "$TAB_INFO" | jq -er '.result.tab.tab_id')"
   WORKER_PANE_ID="$(echo "$TAB_INFO" | jq -er '.result.root_pane.pane_id')"
   WORKER_KIND="${HERDR_AGENT_KIND:-agy}"
   herdr agent start "$AGENT_LABEL" --kind "$WORKER_KIND" --pane "$WORKER_PANE_ID" -- --model "$WORKER_MODEL"

   # Dispatch task brief with mandatory /teamwork-preview /herdr prefix:
   herdr agent prompt "$WORKER_PANE_ID" "/teamwork-preview /herdr
   <TASK_BRIEF>"
   ```
5. **Session Invariant**: Preserve existing healthy sessions; never run duplicate bootstrap or launch a new agent over a live TUI. Check installed `--help` for syntax rather than guessing.
6. **Non-Pane CTO Boundary**: When the CTO operates from a Root PTY outside Herdr, explicit-target CLI commands (`herdr agent read`, etc.) work, but native prompt callbacks targeting the CTO do not exist (`cto.pane_id: null`). The CTO reads reports and `state.yaml` directly from the shared run root on disk.

### 2b. Live Coordinates & Model Verification (All Panes)

Always resolve live coordinates via `herdr pane current`. Do NOT trust static startup environment variables (e.g. `HERDR_TAB_ID`) as panes may move:
```bash
SELF_PANE_ID="$(herdr pane current | jq -r .result.pane.pane_id)"
SELF_TAB_ID="$(herdr pane current | jq -r .result.pane.tab_id)"
SELF_TERM_ID="$(herdr pane current | jq -r .result.pane.terminal_id)"
SELF_CWD="$(herdr pane current | jq -r .result.pane.cwd)"
```

`herdr pane current` confirms physical coordinates, but does NOT prove active model or composer readiness. Verify active model and effort independently via native runtime indicators (e.g. TUI footer/menu).

### 2c. Registration & Acknowledgment

Register confirmed identity with the manager's return address without `--wait`:
- **Preflight match** (identity, model, and role verified as authorized): Proceed directly without waiting for explicit ACK.
- **Preflight mismatch, unclear authority, or restart/relaunch context**: Preserve explicit acknowledgment before proceeding.

---

## 3. Bound, Decompose, Assign (EM)

The EM runs a continuous loop: **report intake** → **strict identity/evidence decision** → **next ready dispatch or escalation** → **checkpoint & prompt retirement**.

- **Small Work Default**: Default to 1 writer and 1 independent reviewer for a cohesive coupled unit of work.
- **Parallel Capacity**: Dispatch all ready disjoint work in the same wave. Refill capacity as workers publish handbacks. True parallelism requires independent results; do not artificially spawn multiple workers for interdependent files.
- **Checkpointing & Dedupe**: Maintain `state.yaml` with active state, ownership, dedupe index, and pending effects. Do not copy historical transcripts. Read past reports from disk when needed.

---

## 4. Execute (Implementers)

- **Implementation**: Make minimal changes to satisfy the spec. If the task changes application code, use appropriate behavioral tests (TDD). Documentation changes are exempt from mandatory red/green TDD. Commit locally.
- **Handback**: Publish an immutable YAML report via the verified 4-step pipeline and send a concise notice to the manager (no `--wait`). See [references/report-contract.md](references/report-contract.md).
- **Communication**: Plain questions and routine progress use short native messages with Question ID, context, and return route. Enter is the default. Tab is optional and requires exclusive composer ownership. See [references/event-monitoring.md](references/event-monitoring.md).

---

## 5. Independent Review & Early Candidate Path

- **Exact-SHA Review**: Reviews bind strictly to an exact commit SHA in clean context. The reviewer verifies the candidate SHA in a frozen read-only checkout. Unconditional `git checkout` is unsafe in a shared read-only worktree; allocate a separate exact-SHA checkout only if tests mutate state or the author must continue working simultaneously. Reviewers audit code, tests, and diffs; reviewers never author fixes or inherit EM dispatch authority.
- **Side-by-Side Review Split**: Alternatively, the EM may launch the reviewer by splitting the implementer's tab (`herdr pane split --pane "$IMPL_PANE_ID" --direction right --cwd "$WORKTREE_PATH" --no-focus`). In this pattern, the implementer pane is **preserved alive** throughout review to retain build logs, reasoning traces, and test transcripts.
- **Delta Review**: If the implementer modifies the branch and produces a new SHA, the old review is invalidated. The same independent reviewer can perform a delta review on the new HEAD, checking only the changed diff and impacted rules. The reviewer explicitly issues a new decision for the new HEAD.
- **Early Coherent Local Candidate Path**: Scoped work may be composed locally for whole-candidate checks and review without requiring redundant per-file lane approvals. Local composition is not release approval. One designated writer may sequentially prepare, write, generate/package, and execute authorized PR mechanics with explicit ownership, keeping independent review separate.
- **Review Loop Bounds & Failure Budget**: Two equivalent failed corrections or two review/fix rounds require a changed approach or concrete escalation, never a third blind retry or automatic approval. Read-only tool movement, changing error IDs, switching model tiers, or receiving new prompt iterations do NOT reset equivalent-failure budgets. Material findings cannot be reclassified as advisory to reach an approval. Cosmetic issues do not reopen a cycle.

---

## 6. Serial Integration & Delivery

Integration combines verified lane commits into a single integrated candidate:

1. **Rebase** onto current baseline.
2. **Run repository checks** (generation, validation, formatting).
3. **Verify** exact integrated HEAD.
4. **Deliver** as authorized by the mission brief (e.g. draft PR handed back unmerged, or authorized merge to main). General delivery follows actual mission authority and branch protections; draft/unmerged holds apply only when specified.

---

## 7. Retrospective Lifecycle, Teardown & Handback

Two distinct cleanup gates govern resource lifecycle:

### 7a. Prompt Terminal & Pane Retirement (EM Control & CTO Milestone Retirement)
- Once an owned worker's handback report is received, evidence is verified durable on disk, ownership is reconciled, and no assigned work or uncertain operations remain, the EM **promptly closes the owned worker pane** (`herdr pane close <PANE_ID>`). When using the side-by-side review pattern, closure occurs after both implementation and review are complete.
- Terminal release does NOT wait for PR merge or mission completion.
- If a session must be retained (e.g. for follow-up debugging), the EM records an explicit retention reason and release trigger in `state.yaml`. Conversation/resume identity and artifacts are preserved outside the process before closing.
- **Closure Invariants**: Verify live identity, foreground process, and owned effects before closing. **Never** close active user-owned panes or active sibling panes. Close a whole tab (`herdr tab close <TAB_ID>`) only if every contained pane is owned, completed, and eligible for closure.
- Verify pane disappearance (`herdr pane process-info` or read returns not found) and update the compact checkpoint in `state.yaml`.
- **Late/Duplicate Notices**: Late or duplicate notices from a retired worker do not respawn the terminal, repeat dispatch, or trigger Git actions.
- **Post-Milestone Zero-Bloat Retirement (CTO Obligation)**: When the entire mission or milestone is complete (zero open issues, zero unmerged PRs), the CTO orchestrator MUST cleanly retire the living Engineering Manager pane:
  ```bash
  herdr pane close "$EM_PANE_ID"
  ```
  Close any lingering worker, reviewer, or temporary execution tabs (`herdr tab close "$TAB_ID"`). Never leave idle zombie AI agents running in the background consuming memory and cluttering `herdr pane list`.

### 7b. Worktree Removal Gate & Herdr Defaults (Integration Authority)
- Worktree cleanup is a separate engineering gate; terminal closure does NOT authorize deleting checkouts.
- **Understanding Herdr's Default Worktree Behavior**:
  - `herdr worktree remove --workspace <WS_ID>` deletes the checkout directory on disk and unregisters the workspace from Herdr.
  - **Invariant 1: Never Deletes the Branch**: Neither Herdr nor Git deletes the local branch upon checkout removal.
  - **Invariant 2: Refuses Dirty Trees**: Removal fails if uncommitted changes exist (never pass `--force` without verifying changes are disposable).
  - **Invariant 3: `workspace close` vs `worktree remove`**: Running `herdr workspace close <WS_ID>` alone closes *only* Herdr UI/session state, leaving the physical directory and Git worktree tracking orphaned on disk. Always use `herdr worktree remove --workspace <WS_ID>`.
  - **Invariant 4: Branch Deletion Block**: `gh pr merge --delete-branch` cannot delete a local branch while it is checked out in an active worktree. Local branch deletion must occur post-worktree removal.
- **Mandatory Merge Integrity Gate**: NEVER remove a worktree until the PR is confirmed merged into `main` (`gh pr view "$PR_URL" --json state -q .state | grep -iq "MERGED"`). Removing a worktree with unmerged commits permanently destroys work.
- **Clean Teardown Sequence**:
  1. Confirm clean tree: `test -z "$(git -C "$WORKTREE_PATH" status --porcelain)"`.
  2. Remove checkout and workspace: `herdr worktree remove --workspace "$WORKSPACE_ID"` (or `git worktree remove "$WORKTREE_PATH"` + `herdr workspace close "$WORKSPACE_ID"`).
  3. Delete local branch: `git -C "$REPO_ROOT" branch -D "$BRANCH_NAME"`.
  4. Prune remote references: `git -C "$REPO_ROOT" remote prune origin`.
  5. Verify zero lingering worktrees: `git -C "$REPO_ROOT" worktree list` (only primary root remains).

### 7c. Mission Handback
Publish final immutable YAML report to the run root with exact HEAD, check results, and unresolved effects.

---

## Canonical References

| Reference | When to Read | Topics |
|---|---|---|
| [references/report-contract.md](references/report-contract.md) | Authoring, publishing, validating, or consuming reports. | YAML schema, atomic publication pipeline, notice format, consumption semantics, digest checks, reviewer Q/A. |
| [references/event-monitoring.md](references/event-monitoring.md) | Supervising terminals, reading Alt-Screen, delivering prompts, diagnosing unknown states. | Screen inspection buffers, bracketed paste, no-wait constraints, Tab input, modal bridge, degraded mode, model verification. |
| [references/stopped-agent-recovery.md](references/stopped-agent-recovery.md) | Unblocking stalled, modal-blocked, hung, or crashed sessions. | Diagnosis matrix, modal resolution, targeted `esc`/`ctrl+c`, Git lock reconciliation, safe TUI restart, quota recovery (§4.6). |
| [references/mission-briefs.md](references/mission-briefs.md) | Dispatching tasks or receiving assignments. | Common authority block, role additions (implementer/reviewer/integrator), coordinate discovery, callback mandate. |
| [references/parallel-capacity.md](references/parallel-capacity.md) | Planning concurrency waves or managing worktrees. | Disjoint parallelism, early candidate path, finite review bounds, failure budget rules, retrospective pane retirement, worktree cleanup gate. |
| [references/serial-merge-and-conflicts.md](references/serial-merge-and-conflicts.md) | Merging candidate PRs onto main or resolving merge conflicts. | Serial rebase-and-merge pipeline, self-contained 5-step conflict engine, Herdr default worktree behavior, PR merge gate, post-milestone teardown. |
