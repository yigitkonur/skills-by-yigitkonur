---
name: herdr
description: Use if orchestrating coding agents, parallel worktrees, split panes, or session lifecycle via Herdr CLI across direct, task, or managed workflows.
---

# Herdr

Herdr is a terminal workspace manager for AI coding agents. It organizes execution surfaces into workspaces, tabs, and split panes, recognizes coding agents running inside panes, and exposes session control through the `herdr` CLI over a local socket API.

Before dispatching work, establish a visible Herdr pane and supervisory authority:

1. **In-Pane Agents (Default)**: Verify running inside a Herdr-managed pane:
   ```bash
   test "${HERDR_ENV:-}" = 1
   ```
   If verified, resolve live coordinates via `herdr pane current --current`.
2. **Outside-Herdr Bootstrap**: An explicitly authorized controller outside Herdr discovers or creates a workspace, then creates a visible control pane (or tab when a split is too small). Start the supervisor agent there and verify its live pane ID before dispatching work. Bootstrap commands target explicit IDs; subsequent prompts, scrollback inspection, and handbacks use the visible pane IDs. Do not infer UI focus from the external terminal.
3. **Fail-Closed Boundary**: If `HERDR_ENV != 1` and you lack explicit authority to bootstrap a Herdr pane, **stop**. Do not control another session by guessing a target.

When verified, the installed `herdr` CLI in `PATH` is the authority for syntax. Discover available commands with `herdr --help`, `herdr agent`, `herdr pane`, and `herdr worktree`. Read identifiers and state from structured JSON output instead of predicting them.

---

## 1. Operating Modes & Routing

Select the operating mode based on task scope and complexity:

| Operating Mode | When to Use | Topology & Authority | Coordination Ceremony |
|---|---|---|---|
| **Direct Operation (Mode 1)** | Quick inspection, 1 verification command, bug diagnosis, bounded fix | Current pane or 1 sibling pane; no EM | Zero: no issues, no PRs, no DAG, no YAML |
| **Task Execution (Mode 2)** | 1 cohesive delivery or up to 2 independent lanes | Direct parent supervision; writer + reviewer | Light: task brief, native reports, exact SHA |
| **Managed Mission (Mode 3)** | 3+ active implementation areas, coordinated cross-repo delivery, multi-wave DAG | Dedicated EM agent; write worktrees + read tabs | Full: `state.yaml`, immutable YAML, dynamic DAG |

- **Mode 1 (Direct Operation)**: Run commands directly in the caller's pane or a single sibling pane. Reserved for genuinely bounded, low-blast-radius work (e.g. self-contained doc/test/mechanical fixes without architectural or breaking interface shifts). Never force managerial overhead on trivial tasks.
- **Mode 2 (Task Execution)**: Parent agent manages workers directly. One whole-change writer owns coupled files; an independent reviewer verifies the candidate commit in a sibling pane or isolated checkout.
- **Mode 3 (Managed Mission)**: Exactly ONE Engineering Manager (EM) agent in the primary workspace manages active state, dynamic DAG waves, resource quotas, and worker handback reports. Triggered only for 3+ active implementation areas or coordinated cross-repo delivery (three independent read-only scouting or research lanes alone do NOT force an EM). Dedicated worktrees are used for write isolation; passive read-only lanes retain tab/pane routes in the existing checkout to prevent workspace sprawl.

For complete routing rules, authority limits, and upgrade procedures, see [references/operating-modes.md](references/operating-modes.md).

---

## 2. Topology, Worktrees & Geometry Rules

Organize terminal layout using Herdr's native hierarchy:
- **Sibling Pane in Same Tab**: Paired implementer and reviewer, or tightly coupled processes, where geometry permits readable splits.
- **Tab in Current Workspace**: Independent read-only inspection, research, or monitoring in the same repository.
- **Native Worktree Workspace**: Dirty or concurrent write isolation in the same repository (`herdr worktree create`).
- **Dedicated Workspace**: Independent repository only (`herdr workspace create`).

### Geometry & Coordinate Invariants:
- **Projected Usable Dimensions**: Inspect live layout first via `herdr pane layout --current`. Project child dimensions including separator columns before splitting; split horizontally or vertically only when both resulting panes maintain readable dimensions ($\ge 80$ columns, $\ge 20$ rows), or open a tab if constrained. Detailed calculation: [references/topology-and-worktrees.md](references/topology-and-worktrees.md).
- **Targeting**: Always pass `--no-focus` for background tasks to preserve user/caller focus. Discover coordinates dynamically via `herdr pane current --current`. Never rely on unverified startup environment variables (`$HERDR_PANE_ID`) when panes move, and never use bare commands that fall back to UI focus.
- **Worktree vs. Workspace**: Distinguish `herdr workspace close` (closes UI session only, leaving Git tracking intact) from `herdr worktree remove` (unlinks directory from disk and unregisters workspace).

For geometry decisions, dynamic coordinates, and workspace primitives, see [references/topology-and-worktrees.md](references/topology-and-worktrees.md) and [references/herdr-primitives.md](references/herdr-primitives.md).

### 2a. Cold Bootstrap Sequence (CTO First-Wave Handover & EM Autonomous Orchestration)

Herdr establishes an explicit, two-tier leadership pair in the primary control workspace: CTO on the LEFT (Pane 1), EM on the RIGHT (Pane 2). Workers and reviewers run in separate per-task worktree workspaces.

1. **CTO captures coordinates and launches the EM pane**:
   ```bash
   # Discover CTO own coordinates and leadership tab:
   CTO_PANE_ID="$(herdr pane current | jq -r .result.pane.pane_id)"
   LEADERSHIP_TAB_ID="$(herdr pane current | jq -r .result.pane.tab_id)"

   # Split right from CTO, capturing the returned EM pane ID:
   EM_PANE_ID="$(herdr pane split --pane "$CTO_PANE_ID" --direction right --cwd "$RUN_ROOT" --no-focus | jq -r .result.pane.pane_id)"

   # Launch EM into returned shell pane with chosen harness (defaults to ambient/agy):
   EM_KIND="${HERDR_AGENT_KIND:-agy}"
   herdr agent start "herdr-engineering-manager" --kind "$EM_KIND" --pane "$EM_PANE_ID" -- --model "$EM_MODEL" --dangerously-skip-permissions
   ```

2. **CTO orchestrates the First Wave**:
   The CTO initializes the environment, decomposes the initial tasks, and opens task environments:
   ```bash
   # CRITICAL LAW: Workspaces MUST be worktree-backed. NEVER create independent workspaces
   # via `herdr workspace create` or loose shell `git worktree add` tabs.
   # Always use Herdr's native worktree command:
   WORKTREE_JSON="$(herdr worktree create --cwd "$REPO_ROOT" --path "$WORKTREE_PATH" --branch "$BRANCH" --label "task-${TASK_ID}" --no-focus)"
   WS_ID="$(echo "$WORKTREE_JSON" | jq -er .result.workspace.workspace_id)"
   WORKER_PANE_ID="$(echo "$WORKTREE_JSON" | jq -er .result.root_pane.pane_id)"

   # Launch initial worker:
   herdr agent start "impl-${TASK_ID}" --kind "$WORKER_KIND" --pane "$WORKER_PANE_ID" -- --model "$WORKER_MODEL" --dangerously-skip-permissions

   # Wait for worker harness to initialize to idle before prompting:
   herdr agent wait "$WORKER_PANE_ID" --until idle --timeout 60000

   # Dispatch task brief with mandatory /teamwork-preview /herdr prefix and inject $EM_PANE_ID as the return route:
   herdr agent prompt "$WORKER_PANE_ID" "/teamwork-preview /herdr
   <TASK_BRIEF>
   When complete, WRITE BACK TO THE ENGINEERING MANAGER with:
   herdr agent prompt \"$EM_PANE_ID\" \"REPORT: task_id=$TASK_ID pr_url=<URL> head_sha=\$(git rev-parse HEAD) status=DONE\""
   ```

3. **CTO Dispatches Handover to the Engineering Manager**:
   The CTO instructs the EM to take over operational command of the running team:
   ```bash
   # Wait for EM harness to initialize to idle before prompting:
   herdr agent wait "$EM_PANE_ID" --until idle --timeout 60000

   herdr agent prompt "$EM_PANE_ID" "CTO HANDOVER & OPERATIONAL DIRECTIVE:
   First-wave tasks are provisioned and workers are running. They will report directly to you at $EM_PANE_ID.
   You now take full operational command:
   - Organize and direct workers using their specialized skills (tdd, code-review, audit-completion).
   - Manage streaming side-by-side reviews in their tabs (herdr pane split).
   - Provision subsequent waves (Waves 2-5) natively via herdr worktree create.
   - When all wave tasks pass review, emit:
     WAVE_COMPLETE: wave=<WAVE_ID> prs=[<PRS>] shas=[<SHAS>] next_wave=<NEXT> next_issues=[<ISSUES>] status=AWAITING_SERIAL_MERGE"
   ```

4. **EM Autonomous Operational Takeover**:
   - The Engineering Manager takes over all execution details: deciding review workflows, allocating reviewers via side-by-side splits (`herdr pane split --pane "$IMPL_PANE_ID" --direction right ...`), and assigning domain skills (`tdd`, `code-review`, `audit-completion`).
   - For subsequent waves (Waves 2–5), the EM natively provisions worktree workspaces (`herdr worktree create`). Independent workspaces are strictly forbidden.
   - Workers, reviewers, and EM orchestrate among themselves.

5. **CTO Sole-Follower Invariant & Asynchronous Wait Tracking**:
   - Once initialized, the **CTO tracks and follows ONLY the Engineering Manager**.
   - **Mandatory Bounded Timeouts on All Scripted Waits (Zero Infinite Waits)**:
     - EVERY scripted `herdr agent wait` and `herdr pane wait-output` command MUST specify an explicit bounded `--timeout <MS>` (recommended: 60000ms to 180000ms; maximum: 300000ms / 5m). Calling wait commands without an explicit `--timeout` in automated scripts or orchestration flows is strictly forbidden; relying on implicit CLI defaults is reserved strictly for interactive human terminal sessions.
     - When matching output patterns, never wait on an overly fragile narrow regex without handling generic errors or timeouts. If `--timeout` expires, the agent MUST NOT hang silently; it must immediately read the live pane buffer (`herdr pane read <PANE_ID> --lines 50`), inspect foreground processes (`herdr pane process-info`), diagnose the actual state, and yield an actionable status update to the user.
   - **Immediate Dispatch Acknowledgment & Conversational Cadence (Max 30–60s Silence Limit)**:
     - Leadership agents (CTO and EM) must NEVER execute lengthy (>4 tool calls) unbroken chains without providing visible progress updates to the user. Agents must maintain a conversational heartbeat (max 30–60s silence limit).
     - When dispatching a directive or advancing waves, immediately output a concise progress summary to the user before entering wait states.
     - **Synchronous Dependency Gates vs Supervisory Waits**:
       - *Dependency-gating waits* (such as waiting for an agent harness to initialize to `idle` before dispatching an initial prompt in steps 2 and 3 above) MUST run synchronously with a bounded timeout (`--timeout 30000` to `60000ms`), because the subsequent prompt depends directly on interactive readiness.
       - *Supervisory monitoring waits* (monitoring an EM or worker through multi-minute tasks): Never block the session for minutes without conversational status. Output an immediate progress summary to the user first. If waiting in an interactive agent turn, either use bounded wait slices (30–60s) or background the wait (`herdr agent wait "$EM_PANE_ID" --until idle --timeout 180000 & WAIT_PID=$!`), yield ongoing status, and join via `wait $WAIT_PID` so the user does not experience a frozen session.
   - **Automated Lifecycle Reaping & Workspace/Tab Cleanup**:
     - Completed tasks must be automatically reaped immediately upon remote PR merge verification (`gh pr view "$PR_URL" --json state -q .state | grep -iq "MERGED"`).
     - **Cleanliness Gate Before Pane Closure**: ALWAYS verify the worktree is clean (`test -z "$(git -C "$WORKTREE_PATH" status --porcelain)"`) BEFORE closing panes or tearing down checkouts. If uncommitted changes exist, DO NOT close panes or hard-exit; escalate by diagnosing uncommitted diffs (`git -C "$WORKTREE_PATH" status -s`) and alerting the operator.
     - Once cleanliness and PR merge are verified:
       1. Retire reviewer and implementer agent panes: `herdr pane close --pane "$IMPL_PANE_ID" 2>/dev/null || true` and `herdr pane close --pane "$REV_PANE_ID" 2>/dev/null || true`.
       2. Remove the worktree checkout and unregister workspace via Herdr: `herdr worktree remove --workspace "$WS_ID" || { echo "Worktree removal failed; diagnosing..."; exit 1; }`.
       3. Delete the local branch and prune remotes: `git -C "$REPO_ROOT" branch -D "$BRANCH"` and `git -C "$REPO_ROOT" remote prune origin`.
       4. Close any lingering standalone workspaces or tabs: `herdr workspace close "$WS_ID" 2>/dev/null || true`.
     - Never leave completed tasks or dead tabs/workspaces lingering open in Herdr.
   - **Context Window Hygiene**:
     - Do NOT run unbounded commands (e.g. `gh issue view <ID>` dumping >1,000 lines) that bloat context and cause inference lag. Rely on local `specs/*.md` files or targeted queries (`gh issue view <ID> --json title,number`).
   - **Deterministic Agent Wait Tracking**: Every running agent MUST be tracked with `herdr agent wait <TARGET_PANE> [--until <STATUS>] [--timeout <MS>]` or `herdr pane wait-output`. Unhooked `sleep` loops and detached polling without agent state checks are strictly prohibited.
   - When the EM emits `WAVE_COMPLETE`, the CTO verifies baseline gates, performs the serial squash-merges onto `main`, and signals the EM to proceed.

6. **Proportional Worker Preflight**:
   - Workers (`impl-*`) must NOT run heavyweight full-repo verification suites (e.g. full `eslint` or full test matrices) upfront as a blind pre-flight ritual. Pre-flight is strictly lightweight: verify git status, read spec, and run targeted tests. Heavy multi-minute suites belong strictly at the Definition of Done (DoD) PR review gate.

7. **Session Invariant**: Preserve existing healthy sessions; never run duplicate bootstrap or launch a new agent over a live TUI. Check installed `--help` for syntax rather than guessing.
8. **Non-Pane CTO Boundary**: When the CTO operates from a Root PTY outside Herdr, explicit-target CLI commands (`herdr agent read`, etc.) work, but native prompt callbacks targeting the CTO do not exist (`cto.pane_id: null`). The CTO reads reports and `state.yaml` directly from the shared run root on disk.

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

## 3. Communication & Harness Physics

Distinguish published, submitted, consumed, and acted states. Successful CLI exit proves transport submission only. Durable reports carry unique IDs and SHA-256 hashes; short notices point to them.

### Harness Rules:
- **Antigravity (AGY)**:
  - **Queue Prevention**: Managers start each turn by sweeping queued notices and unconsumed reports in `report_root` first. Keep turns short (intake $\to$ decision $\to$ dispatch $\to$ checkpoint $\to$ yield). Delegate long builds/diagnostics to workers. Producers yield promptly after handback.
  - **Wakeup Ownership**: Root/controller owns EM wakeups; EM/parent owns worker wakeups. Never broadcast wakeups concurrently. No routine ACK cascades.
  - **Pre-Escape Safety Gates**: Never send Escape to an agent in `blocked` state or displaying a modal. Check visible screen before sending keys and select authorized choices. Never send Escape during active Git mutations, file writes, or package installations.
  - **Staged-After-Escape Recovery**: If a turn stalls with queued text, the single wakeup owner inspects screen state, sends targeted `esc`, and if message promoted to composer, submits EXISTING text with Enter once without duplicate paste.
  - **Resuming**: Reconcile surviving child processes vs. interrupted turns. Always use exact conversation ID (`agy --conversation "$ID"`), never `--continue`.
  - Detailed AGY procedures: [references/harness-antigravity.md](references/harness-antigravity.md).
- **OpenAI Codex**:
  - Start and steer Codex in a visible Herdr pane. Deliver a prompt once with `herdr agent prompt <PANE> <TEXT>`; inspect pane scrollback and agent state to verify receipt and action.
  - Enter steering can reach the next tool boundary. Avoid a second prompt while the first is pending. Do NOT apply AGY Escape mechanics to Codex; use plain language if its slash parser fails.
  - Detailed Codex procedures: [references/harness-codex.md](references/harness-codex.md).
- **Universal Harnesses (Claude, Gemini, Cursor, etc.)**:
  - Verify interactive shell readiness (`$ `, `% `) before `agent start`.
  - Startup timeout does NOT prove launch failure; inspect process tree and visible output before retrying.
  - Quota errors: stop automated retries after 2 equivalent failures. Never downgrade models silently.
  - Detailed harness rules: [references/harness-other.md](references/harness-other.md).

For buffer read sources (`recent-unwrapped`, `visible`, `recent`), modal bridge, and PTY constraints, see [references/event-monitoring.md](references/event-monitoring.md). For unblocking hung sessions, manager recovery, and Git locks, see [references/stopped-agent-recovery.md](references/stopped-agent-recovery.md).

---

## 4. Candidate Review, Parallelism & Serial Integration

### Review & Capacity Invariants:
- **Streaming Reviews Law**: Never execute an unbounded blocking wait for a whole wave to finish. Decouple per-lane: reviews stream per-lane as soon as candidate code is ready, subject to available reviewer capacity (no whole-fleet barrier), using geometry-aware splits or review tabs.
- **Full Verified Object ID Binding**: Reviews bind strictly to a full verified commit object ID (`git rev-parse HEAD`) and clean working tree. If rebase or fixes change the commit SHA ($SHA_2 \neq SHA_1$), prior approval is invalidated, requiring an explicit review delta decision before landing.
- **Reviewer Boundary**: Reviewers are read-only hardening partners. Reviewers never self-approve.
- **Finite Review Bounds**: Two-round failure budget. If 2 consecutive review/fix rounds fail to resolve errors, stop automated retries and escalate. No material waivers.
- **Capacity & Model Fidelity**: Model and effort strictly follow user instructions. Concurrency is governed by measured host capacity and quota limits, counting internal subagents. Dynamic DAG waves advance when prerequisite dependency edges clear without an arbitrary 5-wave ceiling.

For capacity rules, see [references/parallel-capacity.md](references/parallel-capacity.md). For review contracts, see [references/review-and-fix-contract.md](references/review-and-fix-contract.md). For dynamic wave decomposition, see [references/ticket-decomposition-and-waves.md](references/ticket-decomposition-and-waves.md). For dispatch templates, see [references/mission-briefs.md](references/mission-briefs.md). For durable report schemas, see [references/report-contract.md](references/report-contract.md).

### Serial Integration Pipeline:
1. Rebase verified candidate commit onto mission-authorized target branch baseline (never hardcoded `main`). Compare resulting commit object ID: if changed, verify candidate and obtain required review delta decision before landing.
2. Run repository-authorized check and validation commands on integrated HEAD.
3. Push rebased commits: standard `git push` by default; use `--force-with-lease` only for authorized task branch rewrites with verified expected remote state.
4. Execute authorized delivery (PR merge or local fast-forward merge; never checkout target branch inside secondary worktree when target is checked out in primary).
5. Merge Conflict Resolution: use the 5-step engine (observe unmerged files with path-safe `git diff --name-only --diff-filter=U`, understand intent, reconcile hunks preserving upstream invariants, run checks, non-interactive continue with `GIT_EDITOR=true`). Safe rebase abort (`git rebase --abort`) is authorized if target baseline or scope is invalid.

For integration mechanics and conflict resolution, see [references/serial-merge-and-conflicts.md](references/serial-merge-and-conflicts.md).

---

## 5. Decoupled 3-Stage Teardown & Lifecycle

Execute cleanup across three separate, sequential engineering gates:

1. **Stage 1: Terminal & Pane Retirement**: Close worker panes promptly once handback report is verified durable on disk. Paired implementer panes are retained during review and closed after review completes. Leadership panes retire only when all coordination duties conclude.
2. **Stage 2: Worktree Removal Gate**: Delete worktree checkout directory only after candidate delivery (PR merged, local merge verified, or read-only/abandoned handback safely archived), tree is clean (`git status --porcelain`), and ignored build artifacts are verified safe or disposable. Dirty or ambiguous checkouts are preserved with a recorded reason; `--force` is prohibited. Unrelated worktrees remain untouched.
3. **Stage 3: Safe Branch Retirement**: Delete local Git branch strictly AFTER the worktree checkout is unlinked using safe deletion (`git branch -d`). If `-d` refuses, do NOT force deletion (`-D`). Retain the branch reference and record the retention reason. Never run global remote prunes (`git remote prune origin`).

For full teardown gates and preservation rules, see [references/lifecycle-and-cleanup.md](references/lifecycle-and-cleanup.md).

---

## 6. Reference Documentation Index

Every topic has an authoritative reference. Consult when the matching trigger occurs:

| Reference File | When to Read | Core Responsibilities |
|---|---|---|
| [references/operating-modes.md](references/operating-modes.md) | Selecting execution mode (Direct, Task, Managed) | Task-size routing, authority boundaries, upgrade transitions, no recursive managers. |
| [references/topology-and-worktrees.md](references/topology-and-worktrees.md) | Choosing layout, worktree, tab, or pane splits | 4-tier topology hierarchy, projected usable dimensions, dynamic coordinates, caller context. |
| [references/herdr-primitives.md](references/herdr-primitives.md) | Looking up CLI commands, syntax, or flags | Selected command reference for agent, pane, worktree, workspace, tab, notification, jq parsing. |
| [references/event-monitoring.md](references/event-monitoring.md) | Reading buffers, monitoring turns, handling modals | Read sources (unwrapped, visible, recent), settle-waits, modal bridge, 10-minute boundary. |
| [references/harness-antigravity.md](references/harness-antigravity.md) | Operating or unblocking Antigravity (AGY) sessions | Queue prevention, pre-Escape safety, staged-after-Escape single submit, exact resume. |
| [references/harness-codex.md](references/harness-codex.md) | Operating or steering OpenAI Codex agents | Pane-based prompt delivery, scrollback verification, and slash parser recovery. |
| [references/harness-other.md](references/harness-other.md) | Driving Claude Code, Gemini, Cursor, or other agents | Shell readiness gate, startup timeout vs live agent, bounded quota retries, model fidelity. |
| [references/mission-briefs.md](references/mission-briefs.md) | Dispatching tasks or formatting agent briefs | Authority block, plain-language briefs, role additions (impl/reviewer/integrator), pane-bound return routes. |
| [references/parallel-capacity.md](references/parallel-capacity.md) | Sizing concurrency or managing resource locks | Disjoint parallelism, measured capacity, model fidelity, internal subagent accounting, streaming reviews. |
| [references/ticket-decomposition-and-waves.md](references/ticket-decomposition-and-waves.md) | Decomposing tasks or scheduling multi-wave DAGs | Vertical tracer-bullet slicing, dynamic DAG waves, expand-contract refactors, edge-driven advance. |
| [references/report-contract.md](references/report-contract.md) | Authoring or consuming durable mission artifacts | Two artifact kinds (state.yaml vs YAML), 4-step atomic publication, no-wait notices, dedupe digest. |
| [references/review-and-fix-contract.md](references/review-and-fix-contract.md) | Conducting code reviews or handling review feedback | Full verified object ID binding, clean tree, read-only reviewer, delta decisions, 2-round budget. |
| [references/serial-merge-and-conflicts.md](references/serial-merge-and-conflicts.md) | Merging candidate code or resolving Git conflicts | Serial rebase on target branch, delta review on new SHA, 5-step conflict engine, safe abort. |
| [references/stopped-agent-recovery.md](references/stopped-agent-recovery.md) | Unblocking hung turns, Git locks, or crash recovery | Process inventory, target-bound absolute lock path, manager session recovery, exact resume. |
| [references/lifecycle-and-cleanup.md](references/lifecycle-and-cleanup.md) | Retiring panes, removing worktrees, deleting branches | Decoupled 3-stage teardown, worktree removal gate, dirty checkout preservation, safe branch deletion. |
| [references/source-and-migration-map.md](references/source-and-migration-map.md) | Verifying rule provenance or migration from herdr-lite | Complete mapping ledger with verified source headings from installed and remote sources. |
| [references/scenario-validation.md](references/scenario-validation.md) | Validating operational behaviors against specifications | 12 acceptance specifications with explicit live probe evidence vs. decision walkthrough labels. |
