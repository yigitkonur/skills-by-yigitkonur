---
name: herdr
description: Use if orchestrating coding agents, parallel worktrees, split panes, or session lifecycle via Herdr CLI across direct, task, or managed workflows.
---

# Herdr

Herdr is a terminal workspace manager for AI coding agents. It organizes execution surfaces into workspaces, tabs, and split panes, recognizes coding agents running inside panes, and exposes session control through the `herdr` CLI over a local socket API.

Before issuing control commands, verify that this agent runs inside a Herdr-managed pane:

```bash
test "${HERDR_ENV:-}" = 1
```

If the check fails, stop. Do not control Herdr from outside Herdr without explicit authority. When verified, the installed `herdr` CLI in `PATH` is the authority for syntax. Discover available commands with `herdr --help`, `herdr agent`, `herdr pane`, and `herdr worktree`. Read identifiers and state from JSON output instead of predicting them.

---

## 1. Operating Modes & Routing

Select the operating mode based on task scope and complexity:

| Operating Mode | When to Use | Topology & Authority | Coordination Ceremony |
|---|---|---|---|
| **Direct Operation (Mode 1)** | 1 command, quick inspection, bug diagnosis, 1-file fix | Current pane or 1 sibling pane; no EM | Zero: no issues, no PRs, no DAG, no YAML |
| **Task Execution (Mode 2)** | 1 cohesive delivery or up to 2 independent lanes | Direct parent supervision; writer + reviewer | Light: task brief, native reports, exact SHA |
| **Managed Mission (Mode 3)** | 3+ active lanes, cross-repo work, multi-wave DAG | Dedicated EM agent; worktree workspaces | Full: `state.yaml`, immutable YAML, DAG waves |

- **Mode 1 (Direct Operation)**: Run commands directly in the caller's pane or a sibling pane (`herdr pane split --current --direction right --no-focus`). Never force managerial overhead on trivial tasks.
- **Mode 2 (Task Execution)**: Parent agent manages workers directly. One whole-change writer owns coupled files; an independent reviewer verifies the candidate commit in a sibling pane.
- **Mode 3 (Managed Mission)**: Exactly ONE Engineering Manager (EM) agent in the primary workspace manages active state, DAG waves, resource quotas, and worker handback reports.

For complete routing rules and upgrade procedures, see [references/operating-modes.md](references/operating-modes.md).

---

## 2. Topology, Worktrees & Geometry Rules

Organize terminal layout using Herdr's native hierarchy:
- **Sibling Pane in Same Tab**: Paired implementer and reviewer, or tightly coupled processes.
- **Tab in Current Workspace**: Independent read-only inspection or monitoring in the same repository.
- **Native Worktree Workspace**: Dirty or concurrent write isolation in the same repository:
  ```bash
  herdr worktree create --cwd "$REPO_ROOT" --path "$WORKTREE_PATH" --branch "$BRANCH" --no-focus
  ```
- **Dedicated Workspace**: Independent repository only.

### Geometry & Coordinate Invariants:
- Inspect dimensions first (`herdr pane layout --pane "$HERDR_PANE_ID"`). Split wide panes ($\ge 120$ cols) `--direction right`; split narrow or tall panes `--direction down`. Avoid repeated right splits that create unreadable 12-column panes.
- Always pass `--no-focus` for background tasks to preserve user/caller focus.
- Discover coordinates dynamically via `herdr pane current` (returns JSON). Never trust static startup environment variables (`$HERDR_TAB_ID`) when panes move.
- Distinguish `herdr workspace close` (closes UI session only) from `herdr worktree remove` (deletes directory from disk and unregisters workspace).

For geometry decisions, dynamic coordinates, and workspace primitives, see [references/topology-and-worktrees.md](references/topology-and-worktrees.md) and [references/herdr-primitives.md](references/herdr-primitives.md).

---

## 3. Communication & Harness Physics

Distinguish published, submitted, consumed, and acted states. Successful CLI exit proves transport submission only. Durable reports carry unique IDs and SHA-256 hashes; short notices point to them.

### Harness Rules:
- **Antigravity (AGY)**:
  - Enter while working queues input until the active turn ends. Single wakeup owner per target.
  - Staged-After-Escape Recovery: exactly one wakeup owner sends targeted `esc` (`herdr agent send-keys <pane> esc`), reads visible buffer, and if the message was promoted to the composer, submits EXISTING text with Enter once (`herdr agent send-keys <pane> enter`) without duplicate paste.
  - Project Trust Modal: inspect visible buffer before sending keys; never send blind Enter.
  - Resuming: always use exact conversation ID (`agy --conversation "$ID"`), never `--continue`.
  - Detailed AGY procedures: [references/harness-antigravity.md](references/harness-antigravity.md).
- **OpenAI Codex**:
  - Enter delivers steering at the next tool boundary; Tab enqueues deferred follow-up.
  - Native queue: use `codex queue --thread <THREAD> --message <TEXT>` when thread UUID is known.
  - Do NOT apply AGY Escape mechanics to Codex. Fallback to plain language if slash parser fails.
  - Detailed Codex procedures: [references/harness-codex.md](references/harness-codex.md).
- **Universal Harnesses (Claude, Gemini, Cursor, etc.)**:
  - Verify interactive shell readiness (`$ `, `% `) before `agent start`.
  - Startup timeout does NOT prove launch failure; inspect process tree and visible output before retrying.
  - Quota errors: stop automated retries after 2 equivalent failures. Never downgrade models silently.
  - Detailed harness rules: [references/harness-other.md](references/harness-other.md).

For buffer read sources (`recent-unwrapped`, `visible`, `recent`), modal bridge, and PTY constraints, see [references/event-monitoring.md](references/event-monitoring.md). For unblocking hung sessions and Git locks, see [references/stopped-agent-recovery.md](references/stopped-agent-recovery.md).

---

## 4. Candidate Review, Parallelism & Serial Integration

### Review & Capacity Invariants:
- **Streaming Reviews Law**: Never execute an unbounded blocking wait for a whole wave to finish. Decouple per-lane: review starts immediately as soon as a lane reports done or submits candidate code.
- **Exact-SHA Review Binding**: Reviews bind strictly to an exact 40-character commit SHA (`git rev-parse HEAD`). Any subsequent commit automatically invalidates prior approval ($SHA_2 \neq SHA_1$), requiring a delta review.
- **Reviewer Boundary**: Reviewers are read-only hardening partners. Reviewers never self-approve.
- **Finite Review Bounds**: Two-round failure budget. If 2 consecutive review/fix rounds fail to resolve errors, stop automated retries and escalate. No material waivers.
- **Concurrency & Model Tiering**: Limit concurrency to 2–3 active heavy agents per host to prevent 429 quota exhaustion. Use flash models for exploratory workers.

For capacity rules, see [references/parallel-capacity.md](references/parallel-capacity.md). For review contracts, see [references/review-and-fix-contract.md](references/review-and-fix-contract.md). For wave decomposition (up to 5 waves), see [references/ticket-decomposition-and-waves.md](references/ticket-decomposition-and-waves.md). For dispatch templates, see [references/mission-briefs.md](references/mission-briefs.md). For durable report schemas, see [references/report-contract.md](references/report-contract.md).

### Serial Integration Pipeline:
1. Rebase verified candidate commit onto mission-authorized target branch baseline (never hardcoded `main`).
2. Run project validation suites (syntax, types, tests) on integrated HEAD.
3. Push verified HEAD with lease (`git push --force-with-lease`).
4. Execute authorized delivery (squash-merge PR or local fast-forward merge).
5. Merge Conflict Resolution: use the self-contained 5-step engine (observe state, understand intent, reconcile hunks preserving upstream invariants, run checks, non-interactive continue with `GIT_EDITOR=true`). Rebase abort (`git rebase --abort`) is authorized if target baseline or scope is invalid.

For integration mechanics and conflict resolution, see [references/serial-merge-and-conflicts.md](references/serial-merge-and-conflicts.md).

---

## 5. Decoupled 3-Stage Teardown & Lifecycle

Execute cleanup across three separate, sequential engineering gates:

1. **Stage 1: Terminal & Pane Retirement**: Close worker panes promptly once handback report is verified durable on disk:
   ```bash
   herdr pane close "$PANE_ID"
   ```
   Paired implementer panes are retained during review and closed after review completes. Leadership panes retire only when all responsibilities are finished.
2. **Stage 2: Worktree Removal Gate**: Delete worktree checkout directory only after PR merge is confirmed on remote (`gh pr view`) and tree is clean (`git status --porcelain`):
   ```bash
   herdr worktree remove --workspace "$WORKSPACE_ID"
   ```
   Dirty checkouts are preserved with a recorded reason; `--force` is prohibited. Unrelated worktrees remain untouched.
3. **Stage 3: Branch Retirement**: Delete local Git branch and prune remote tracking references strictly AFTER the worktree checkout is unlinked:
   ```bash
   git branch -d "$BRANCH_NAME" 2>/dev/null || git branch -D "$BRANCH_NAME"
   git remote prune origin
   ```

For full teardown gates and preservation rules, see [references/lifecycle-and-cleanup.md](references/lifecycle-and-cleanup.md).

---

## 6. Reference Documentation Index

Every topic has an authoritative reference. Consult when the matching trigger occurs:

| Reference File | When to Read | Core Responsibilities |
|---|---|---|
| [references/operating-modes.md](references/operating-modes.md) | Selecting execution mode (Direct, Task, Managed) | Task-size routing, authority boundaries, upgrade transitions, no recursive managers. |
| [references/topology-and-worktrees.md](references/topology-and-worktrees.md) | Choosing layout, worktree, tab, or pane splits | 4-tier topology hierarchy, width/height split geometry, dynamic coordinates, caller context. |
| [references/herdr-primitives.md](references/herdr-primitives.md) | Looking up CLI commands, syntax, or flags | Full command reference for agent, pane, worktree, workspace, tab, notification, jq parsing. |
| [references/event-monitoring.md](references/event-monitoring.md) | Reading buffers, monitoring turns, handling modals | Read sources (unwrapped, visible, recent), settle-waits, modal bridge, 10-minute boundary. |
| [references/harness-antigravity.md](references/harness-antigravity.md) | Operating or unblocking Antigravity (AGY) sessions | Turn queue mechanics, staged-after-Escape recovery, trust modal inspection, exact resume. |
| [references/harness-codex.md](references/harness-codex.md) | Operating or steering OpenAI Codex agents | Enter steering at tool boundary, Tab enqueue, native codex queue CLI, slash parser recovery. |
| [references/harness-other.md](references/harness-other.md) | Driving Claude Code, Gemini, Cursor, or other agents | Shell readiness gate, startup timeout vs live agent, bounded quota retries, model fidelity. |
| [references/mission-briefs.md](references/mission-briefs.md) | Dispatching tasks or formatting agent briefs | Authority block, plain-language briefs, role additions (impl/reviewer/integrator), safe submission. |
| [references/parallel-capacity.md](references/parallel-capacity.md) | Sizing concurrency or managing resource locks | Disjoint parallelism, 2-3 worker limit, 429 quota prevention, reservation vs grant, streaming reviews. |
| [references/ticket-decomposition-and-waves.md](references/ticket-decomposition-and-waves.md) | Decomposing tasks or scheduling multi-wave DAGs | Vertical tracer-bullet slicing, up to 5 waves, expand-contract refactors, wave transitions. |
| [references/report-contract.md](references/report-contract.md) | Authoring or consuming durable mission artifacts | Two artifact kinds (state.yaml vs YAML), 4-step atomic publication, no-wait notices, dedupe digest. |
| [references/review-and-fix-contract.md](references/review-and-fix-contract.md) | Conducting code reviews or handling review feedback | Exact 40-char SHA binding, read-only reviewer, delta decisions, 2-round failure budget. |
| [references/serial-merge-and-conflicts.md](references/serial-merge-and-conflicts.md) | Merging candidate code or resolving Git conflicts | Serial rebase on target branch, 5-step conflict resolution engine, safe rebase abort, PR merge. |
| [references/stopped-agent-recovery.md](references/stopped-agent-recovery.md) | Unblocking hung turns, Git locks, or quota errors | Process tree inspection, dynamic index.lock removal, exact conversation resume, server daemon safety. |
| [references/lifecycle-and-cleanup.md](references/lifecycle-and-cleanup.md) | Retiring panes, removing worktrees, deleting branches | Decoupled 3-stage teardown, worktree removal gate, dirty checkout preservation, branch prune. |
| [references/source-and-migration-map.md](references/source-and-migration-map.md) | Verifying rule provenance or migration from herdr-lite | Complete mapping ledger: upstream Herdr, canonical Herdr, retired Herdr-Lite rule groups. |
| [references/scenario-validation.md](references/scenario-validation.md) | Validating operational behaviors against test cases | 12 acceptance scenarios: direct task, paired review, AGY Escape staging, Codex queue, clean teardown. |
