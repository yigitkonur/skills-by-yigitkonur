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
