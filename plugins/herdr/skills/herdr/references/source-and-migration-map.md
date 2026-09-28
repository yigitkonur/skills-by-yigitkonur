# Source & Migration Traceability Map

This document establishes the verified provenance, mapping, and disposition of all rule groups from the upstream Herdr specification, the canonical Herdr skill, the retired Herdr-Lite skill, and field evaluation experience into the unified Herdr skill architecture.

> [!NOTE]
> **Provenance & Evidence Scope**:
> - Pinned snapshots in `sources/` reflect repository state at base commit `b7a8889716e825e590028665b3b8d4fe7bf85ba1` and upstream commit `c34dd6b2acd432cb7acbe9de568b245853e3b8c7`.
> - Differences between remote repository files (`sources/remote-*`) and separately installed copies (`sources/installed-*`) are explicitly distinguished in this ledger.
> - Provenance files and field notes are historical evidence, not runtime dependencies.
> - User-supplied evaluation scores and claims remain explicitly unverified.

---

## 1. Source Inventory & Provenance

The unified deliverable accounts for all original source entry points and references:
1. **Upstream Herdr**: `sources/herdr-upstream-SKILL.md` (commit `c34dd6b2acd432cb7acbe9de568b245853e3b8c7`).
2. **Canonical Herdr Entry Point**: `sources/remote-herdr/SKILL.md` and `sources/installed-herdr/SKILL.md`.
3. **Canonical Herdr References (6 files)**:
   - `report-contract.md`
   - `parallel-capacity.md`
   - `mission-briefs.md`
   - `serial-merge-and-conflicts.md` (remote only)
   - `event-monitoring.md`
   - `stopped-agent-recovery.md`
4. **Retired Herdr-Lite Entry Point**: `sources/remote-herdr-lite/SKILL.md` and `sources/installed-herdr-lite/SKILL.md`.
5. **Retired Herdr-Lite References (7 files)**:
   - `herdr-primitives.md`
   - `orchestration-workflow.md`
   - `recovery-and-safeguards.md`
   - `review-and-fix-contract.md`
   - `serial-merge-and-conflicts.md`
   - `terminal-and-event-rules.md`
   - `ticket-decomposition-and-waves.md`

---

## 2. Rule Group Disposition Categories

- **Retained**: Preserved with its original intent, updated for unified terminology and command accuracy.
- **Merged**: Unified from duplicate definitions across Herdr and Herdr-Lite into a single authoritative source.
- **Qualified**: Retained with specific operational bounds, edge-case conditions, or harness-specific caveats.
- **Rejected**: Explicitly removed due to architectural friction, prompt bloat, or verified anti-patterns.

---

## 3. Comprehensive Rule Group Mapping Ledger

### A. Upstream Herdr Specification (`sources/herdr-upstream-SKILL.md`)

| Real Section Heading / Topic | Disposition | Target Reference | Rationale & Mapped Obligations |
|---|---|---|---|
| `## Learn the current CLI` (`HERDR_ENV=1` Check) | Retained | `SKILL.md`, `operating-modes.md` | Verification gate ensuring control commands execute only within Herdr-managed panes or under authorized external supervision. |
| `## Learn the current CLI` (Installed Help Authority) | Retained | `SKILL.md`, `herdr-primitives.md` | Installed CLI binary is authoritative for flags and syntax; prohibits inventing flags. |
| `## Use IDs and caller context` (Opaque ID Handles) | Merged | `topology-and-worktrees.md` §3, `herdr-primitives.md` | Stable opaque IDs (`w1`, `w1:t1`, `w1:p1`); dynamic coordinates via `herdr pane current --current`. |
| `## Use IDs and caller context` (Saved SSH Machines `--machine`) | Retained | `herdr-primitives.md` §6 | Dedicated `--machine` forwarding rules, server-scoped IDs, absolute/tilde paths, no TUI required. |
| `## Start and coordinate an agent` (Geometry Split Rules) | Merged | `topology-and-worktrees.md` §2 | Projected dimension calculation; split right for $\ge 161$ cols, down for $\ge 41$ lines; avoids 12-col trap. |
| `## Start and coordinate an agent` (Prompt Delivery & Paste) | Merged | `event-monitoring.md` §3 | DEC Mode 2004 bracketed paste timing, `--wait` lifecycle settlement, and no-wait worker notices. |
| `## Start and coordinate an agent` (Logical Keys `send-keys`) | Merged | `herdr-primitives.md` §1, `event-monitoring.md` §4 | Standardizes `esc`, `enter`, `ctrl+c`, `up`, `down`, `tab`. Canonical Escape token is `esc`. |
| `## Run an ordinary command in another pane` (Read Sources) | Merged | `event-monitoring.md` §1 | Maps `recent-unwrapped`, `visible`, `recent`, `detection` to logging, modal, and columnar tasks. |
| `## Safety and coordination rules` (Server Stop Prohibition) | Merged | `stopped-agent-recovery.md` §5 | Strictly prohibits `herdr server stop` or blanket kills from active sessions. |

---

### B. Original Entry Points: `herdr/SKILL.md` vs. `herdr-lite/SKILL.md`

| Real Section Heading / Topic | Source File | Disposition | Target Reference | Rationale & Mapped Obligations |
|---|---|---|---|---|
| `## 1. Role Selection (Cold Reader Intake)` | `remote-herdr/SKILL.md` & `installed-herdr/SKILL.md` | Retained | `operating-modes.md` | Role selection based on task size; direct path defined as genuinely bounded work, not arbitrary single-file work. |
| `## 2. Discover, Register, Verify` | `remote-herdr/SKILL.md` & `installed-herdr/SKILL.md` | Merged | `topology-and-worktrees.md`, `event-monitoring.md` §7 | Cold bootstrap sequence, live coordinate verification via `--current`, model verification. |
| `## 3. Bound, Decompose, Assign (EM)` | `remote-herdr/SKILL.md` & `installed-herdr/SKILL.md` | Merged | `ticket-decomposition-and-waves.md`, `mission-briefs.md` | Task decomposition, vertical tracer bullets, plain-language briefs with authority block. |
| `## 4. Execute (Implementers)` | `remote-herdr/SKILL.md` & `installed-herdr/SKILL.md` | Merged | `parallel-capacity.md`, `mission-briefs.md` | Whole-change writer ownership; isolated worktree execution; prompt handback yield. |
| `## 5. Independent Review & Early Candidate Path` | `remote-herdr/SKILL.md` & `installed-herdr/SKILL.md` | Merged | `review-and-fix-contract.md`, `parallel-capacity.md` §3 | Fresh independent reviewer; full verified commit object ID binding; early coherent candidate path. |
| `## 6. Serial Integration & Delivery` | `remote-herdr/SKILL.md` & `installed-herdr/SKILL.md` | Merged | `serial-merge-and-conflicts.md` | Serial rebase on mission-authorized target branch; review delta on rebased SHA; conflict engine. |
| `## 7. Retrospective Lifecycle, Teardown & Handback` | `remote-herdr/SKILL.md` & `installed-herdr/SKILL.md` | Merged | `lifecycle-and-cleanup.md` | Decoupled 3-stage teardown: pane retirement, worktree removal gate, safe local branch deletion. |
| `## 1. Dual-Agent Leadership Topology (CTO & Engineering Manager)` | `remote-herdr-lite/SKILL.md` & `installed-herdr-lite/SKILL.md` | **Rejected** / Replaced | `operating-modes.md` | **Anti-Pattern**: Mandatory two-tier leadership for small tasks creates workspace sprawl. Replaced with task-size routing (Direct, Task, Managed). |
| `## 2. Antigravity Orchestration Lifecycle` | `remote-herdr-lite/SKILL.md` & `installed-herdr-lite/SKILL.md` | Merged | `operating-modes.md`, `harness-antigravity.md` | Lifecycle flow unified with queue prevention and pre-Escape safety gates. |
| `## 3. Worktree Workspace Topology: Side-by-Side Pane Layout` | `remote-herdr-lite/SKILL.md` & `installed-herdr-lite/SKILL.md` | Qualified / Merged | `topology-and-worktrees.md` §1, §2 | Side-by-side review panes retained where geometry allows ($\ge 161$ cols); review tabs used under constrained dimensions. |
| `## 4. Core Herdr CLI Primitives Quick Reference` | `remote-herdr-lite/SKILL.md` & `installed-herdr-lite/SKILL.md` | Merged | `herdr-primitives.md` | Command syntax consolidated with verified installed help flags (`--amount`). |
| `## 5. Preserved Invariant Safeguards` | `remote-herdr-lite/SKILL.md` & `installed-herdr-lite/SKILL.md` | Merged | `review-and-fix-contract.md`, `lifecycle-and-cleanup.md` | Exact SHA review, 2-round failure budget, clean tree verification, safe teardown gates. |

---

### C. Canonical Herdr References (6 Files)

| Source File & Real Section Heading | Remote vs. Installed Diff | Disposition | Target Reference | Rationale & Mapped Obligations |
|---|---|---|---|---|
| `report-contract.md`: `## 1. Exactly Two Durable Artifact Kinds` | Identical | Retained | `report-contract.md` §1 | Mutable `state.yaml` vs. immutable producer YAML reports outside worktrees. |
| `report-contract.md`: `## 2. When to Use an Immutable Report vs. a Native Message` | Identical | Qualified | `report-contract.md` §3 | Ordinary technical Q/A uses native text; formal blockers and handbacks use immutable YAML. |
| `report-contract.md`: `## 3. Canonical Producer Report Schema` | Identical | Retained | `report-contract.md` §4 | Schema v1 backward compatibility: `producer.skill_revision`, `cto` routing, `in_progress`. |
| `report-contract.md`: `## 4. Atomic Publication Pipeline (No-Clobber & Verified)` | Identical | Retained | `report-contract.md` §5 | Write `.partial`, validate syntax/shape/digest, atomic rename `mv -n`, no-wait notice. |
| `report-contract.md`: `## 5. Concise Native Notice Format` | Identical | Retained | `report-contract.md` §5 | One-line notice pointing to durable artifact path and SHA-256 digest. |
| `report-contract.md`: `## 6. Manager Consumption Semantics` | Identical | Retained | `report-contract.md` §6 | Identity gate, attempt gate, idempotent digest check (`MUTATED_REPORT_REJECTED` on mismatch). |
| `report-contract.md`: `## 7. Reviewer Communication & Q/A Protocol` | Identical | Retained | `report-contract.md` §3 | Non-blocking Q/A uses native prompt; formal blocking findings use review report. |
| `parallel-capacity.md`: `## 1. Disjoint Parallelism vs. Small Coupled Work` | Differ in text | Retained | `parallel-capacity.md` §1 | One whole-change writer for coupled files; parallelism only for disjoint surfaces. |
| `parallel-capacity.md`: `## 2. Early Coherent Local Candidate Path` | Differ in text | Retained | `parallel-capacity.md` §3 | Writer composes and validates whole candidate locally, bypassing redundant lane approvals. |
| `parallel-capacity.md`: `## 3. Review Invalidation & Delta Decisions` | Differ in text | Retained | `review-and-fix-contract.md` §1 | Commit advance invalidates approval ($SHA_2 \neq SHA_1$); delta review on changed diff. |
| `parallel-capacity.md`: `## 4. Finite Review Bounds & Failure Budget Rules` | Differ in text | Retained | `parallel-capacity.md` §6, `review-and-fix-contract.md` §3 | Two-round failure budget halts retries; no artificial resets; no material waivers. |
| `parallel-capacity.md`: `## 5. Retrospective Lifecycle & Teardown Gates` | Differ in text | Merged | `lifecycle-and-cleanup.md` | Subsections 5a (pane retirement) and 5b (worktree removal gate) consolidated into 3-stage lifecycle. |
| `parallel-capacity.md`: `## 6. Serial Integration & Delivery Lifecycle` | Present in both (differs in subsections) | Merged | `serial-merge-and-conflicts.md` | Remote has `### Merge Conflict Resolution Engine`, installed has `### Merge Conflict Ownership`. Rebase on moving baseline; self-contained conflict engine. |
| `mission-briefs.md`: `## 1. Common Authority Block (All Roles)` | Differ in text | Retained | `mission-briefs.md` §1 | Common authority block with identity, coordinates, objectives, checks, and pane-bound return route. |
| `mission-briefs.md`: `## 2. Implementer Additions` | Differ in text | Qualified | `mission-briefs.md` §3 | Worktree path, base SHA, owned files, exclusions; generic slash mandates rejected. |
| `mission-briefs.md`: `## 3. Fresh Reviewer Additions` | Differ in text | Qualified | `mission-briefs.md` §4 | Exact candidate commit ID; clean context; Mode 2 lightweight review notices. |
| `mission-briefs.md`: `## 4. Integration Executor Additions` | Differ in text | Retained | `mission-briefs.md` §5 | Target branch, serial pipeline, targeted repository checks. |
| `mission-briefs.md`: `## 5. Safe Submission Pattern` | Differ in text | Retained | `mission-briefs.md` §6 | Authoring briefs into temporary files at run root to prevent argv escaping errors. |
| `event-monitoring.md`: `## 1. Live Coordinates` | Identical | Retained | `event-monitoring.md`, `topology-and-worktrees.md` §3 | Coordinate discovery via `herdr pane current --current`. |
| `event-monitoring.md`: `## 2. Reading Pane State` | Identical | Retained | `event-monitoring.md` §1, §2 | Snapshot sources and settle-waits; server-side seen state vs. TUI badges. |
| `event-monitoring.md`: `## 3. Communication & Prompt Delivery` | Identical | Retained | `event-monitoring.md` §3 | Bracketed paste pacing delay; no-wait worker notices; avoiding whole-fleet blocking waits. |
| `event-monitoring.md`: `## 4. Modal Bridge` | Identical | Retained | `event-monitoring.md` §4 | Inspect visible buffer before sending targeted key tokens based on authorized choice. |
| `event-monitoring.md`: ``## 5. Degraded AGY Mode (`herdr pane run`)`` | Identical | Retained | `event-monitoring.md` §5 | Keystroke injection fallback; verifies foreground program and input-ready composer. |
| `event-monitoring.md`: `## 6. Targeted Intervention` | Identical | Retained | `event-monitoring.md` §6 | Targeted `esc` and `ctrl+c`; no blind kills; reconciles state before restart. |
| `event-monitoring.md`: `## 7. Discovery, Bootstrap & Model Verification` | Identical | Retained | `event-monitoring.md` §7 | Restored: live coordinates via `--current`, model verification via native TUI/session identity (process inspection proves launch intent only), 10-minute silent boundary. |
| `stopped-agent-recovery.md`: `## 1. Process Reconciliation vs. Blind Kills` | Identical | Retained | `stopped-agent-recovery.md` §1 | Process tree query; target-bound absolute lock path (`--path-format=absolute --git-path index.lock`). |
| `stopped-agent-recovery.md`: `## 2. Safe Restart of Crashed Agent Sessions` | Identical | Retained | `stopped-agent-recovery.md` §2 | Clean shell prompt check; confirm prior process dead; explicit configuration flags. |
| `stopped-agent-recovery.md`: `## 3. Quota & Hang Recovery Safeguards (§4.6)` | Identical | Retained | `stopped-agent-recovery.md` §3 | Inventory conversation ID first; targeted interruption; exact resume (`--conversation <UUID>`). |
| `stopped-agent-recovery.md`: `## 4. Manager Session Recovery & Selective Resume` | Identical | Retained | `stopped-agent-recovery.md` §4 | Restored: relinquishment proof, selective report intake, structural shape verification, worker adoption. |
| `stopped-agent-recovery.md`: `## 5. Bounded Recovery Rule & Blocker Escalation` | Identical | Retained | `stopped-agent-recovery.md` §3, §5 | Rule of two: halt retries after 2 equivalent failures; escalate concrete blocker; server stop prohibition. |
| `serial-merge-and-conflicts.md`: `## 1. Why Serial Integration?` | Remote-herdr only (absent in installed-herdr) | Retained | `serial-merge-and-conflicts.md` §1 | Serial landing sequence preventing semantic regressions and merge races. |
| `serial-merge-and-conflicts.md`: `## 2. Step-by-Step Serial Landing Pipeline` | Remote-herdr only (absent in installed-herdr) | Qualified | `serial-merge-and-conflicts.md` §2 | Rebase on authorized branch; delta review on changed SHA; standard push; no target checkout in worktree. |
| `serial-merge-and-conflicts.md`: `## 3. Self-Contained Merge Conflict Resolution Engine` | Remote-herdr only (absent in installed-herdr) | Retained | `serial-merge-and-conflicts.md` §3 | 5-step engine: path-safe NUL-delimited staging (`git diff -z --name-only --diff-filter=U \| xargs -0`), understand intent, reconcile, check, non-interactive continue. |
| `serial-merge-and-conflicts.md`: `## 4. Worktree Lifecycle, Herdr Defaults & Clean Teardown` | Remote-herdr only (absent in installed-herdr) | Qualified / Merged | `lifecycle-and-cleanup.md` | Understanding Herdr defaults; zero-bloat teardown protocol consolidated into decoupled 3-stage lifecycle. |

---

### D. Retired Herdr-Lite References (7 Files)

| Source File & Real Section Heading | Remote vs. Installed Diff | Disposition | Target Reference | Rationale & Mapped Obligations |
|---|---|---|---|---|
| `herdr-primitives.md`: ``## 1. Worktree Primitives (`herdr worktree`)`` | Differ in text | Retained | `herdr-primitives.md` §3, `topology-and-worktrees.md` | Socket API worktree commands; atomic workspace creation; side-by-side pairing. |
| `herdr-primitives.md`: ``## 2. Workspace Primitives (`herdr workspace`)`` | Differ in text | Retained | `herdr-primitives.md` §4 | Workspace list, create, close commands. |
| `herdr-primitives.md`: ``## 3. Tab Primitives (`herdr tab`)`` | Differ in text | Retained | `herdr-primitives.md` §4 | Tab create, close commands; review tabs inside existing workspaces. |
| `herdr-primitives.md`: ``## 4. Pane Primitives (`herdr pane`)`` | Differ in text | Qualified | `herdr-primitives.md` §2 | Corrected `--amount <FLOAT>` for `resize` (disproving `--cells`); mandate `--current`. |
| `herdr-primitives.md`: ``## 5. Agent Primitives (`herdr agent`)`` | Differ in text | Retained | `herdr-primitives.md` §1 | Agent start, prompt, wait, read, send-keys, list, get. `agent get` qualified as metadata only. |
| `herdr-primitives.md`: ``## 6. Notification Primitives (`herdr notification`)`` | Differ in text | Retained | `herdr-primitives.md` §5 | Desktop toast alerts on task or wave completion. |
| `orchestration-workflow.md`: `## 1. Dual-Agent Leadership & Multi-Wave Streaming Architecture` | Differ in text | **Rejected** / Replaced | `operating-modes.md`, `ticket-decomposition-and-waves.md` | Mandatory two-tier leadership replaced with task-size routing; arbitrary wave ceilings removed. |
| `orchestration-workflow.md`: `## 2. Step 0: Automatic Ticket Intake & GitHub Issue Creation` | Differ in text | Qualified | `ticket-decomposition-and-waves.md` §1 | Vertical tracer-bullet slicing; GitHub issue creation qualified as optional mechanism. |
| `orchestration-workflow.md`: `## 3. Step 1: Multi-Wave Dependency Graph & Parallelism Sizing` | Differ in text | Qualified | `ticket-decomposition-and-waves.md` §2 | Dynamic DAG waves; prerequisite-driven advance; whole-wave merge barriers rejected. |
| `orchestration-workflow.md`: `## 4. Step 2: Dedicated Worktree & Workspace Provisioning` | Differ in text | Qualified | `topology-and-worktrees.md`, `mission-briefs.md` | Dedicated worktrees reserved for write isolation; read-only lanes retain tabs; plain-language briefs. |
| `orchestration-workflow.md`: `## 5. Step 3: Event-Driven Streaming Review (Side-by-Side Split Pane)` | Differ in text | Retained | `parallel-capacity.md` §5, `topology-and-worktrees.md` §2 | Streaming review law: initiate review immediately upon worker completion; projected geometry splits. |
| `orchestration-workflow.md`: `## 6. Step 4: Full-Job Teardown & Serial Merge` | Installed only | Merged | `lifecycle-and-cleanup.md`, `serial-merge-and-conflicts.md` | Replaced rigid teardown with decoupled 3-stage lifecycle and serial rebase pipeline. |
| `orchestration-workflow.md`: `## 6. Step 4: CTO Active Supervision & Engineering Manager Wave Handover` | Remote only | **Rejected** / Replaced | `operating-modes.md` §3, `ticket-decomposition-and-waves.md` §3 | Mandatory CTO/EM dual-agent leadership rejected; single supervisor with task-size routing; structured wave handover only when Mode 3 is authorized. |
| `orchestration-workflow.md`: `## 7. Step 5: Full-Job Teardown & Workspace Retirement` | Remote only | Merged | `lifecycle-and-cleanup.md` | Merged into decoupled 3-stage lifecycle (pane retirement, worktree removal gate, safe branch deletion). |
| `orchestration-workflow.md`: `## 7. Step 5: Continuous Wave Advancement` | Installed only | Merged | `ticket-decomposition-and-waves.md` §3 | Dynamic DAG advancement as prerequisites clear. |
| `orchestration-workflow.md`: `## 8. Step 6: Continuous Wave Advancement` | Remote only | Merged | `ticket-decomposition-and-waves.md` §3 | Dynamic DAG advancement as prerequisites clear. |
| `recovery-and-safeguards.md`: `## 1. Process Reconciliation vs. Blind Kills` | Differ in text | Merged | `stopped-agent-recovery.md` §1 | Query process tree before kill; target-bound lock reconciliation. |
| `recovery-and-safeguards.md`: `## 2. Quota & Hang Recovery Safeguards` | Differ in text | Merged | `stopped-agent-recovery.md` §3 | Inventory conversation ID; targeted interruption; exact resume (`--conversation <UUID>`). |
| `recovery-and-safeguards.md`: `## 3. Worktree Removal Gate & Pane Retirement` | Differ in text | Merged | `lifecycle-and-cleanup.md` | Gate A (pane retirement) and Gate B (worktree removal) merged into decoupled 3-stage lifecycle. |
| `recovery-and-safeguards.md`: `## 4. Subagent Model Tiering & Concurrency Guard (429 Quota Exhaustion Prevention)` | Remote only | **Rejected** / Replaced | `parallel-capacity.md` §2 | **Forced Flash Tiering Rejected**: Model and effort follow user instructions strictly; no speculative downgrades or concurrency caps. |
| `recovery-and-safeguards.md`: `## 5. Whole-Fleet Wait Obsession & Streaming Review Protocol` | Remote only | **Rejected** / Replaced | `parallel-capacity.md` §5, `event-monitoring.md` §3 | Whole-fleet wait loops prohibited; streaming reviews initiated immediately subject to capacity. |
| `review-and-fix-contract.md`: `## 1. Exact-SHA Review Invariant` | Differ in text | Merged | `review-and-fix-contract.md` §1 | Full verified commit object ID binding; clean working tree required; commit advance invalidates approval. |
| `review-and-fix-contract.md`: `## 2. Review-and-Fix Protocol` | Differ in text | Merged | `review-and-fix-contract.md` §2 | Read-only reviewer boundary; no self-approval; same-account PR comment handling. |
| `review-and-fix-contract.md`: `## 3. Finite Review Bounds & Failure Budget` | Differ in text | Merged | `review-and-fix-contract.md` §3 | Two-round failure budget halts retries; no artificial resets; no material waivers. |
| `serial-merge-and-conflicts.md`: `## 1. Why Serial Integration?` | Differ in text | Merged | `serial-merge-and-conflicts.md` §1 | Serial landing sequence prevents silent regressions and merge races. |
| `serial-merge-and-conflicts.md`: `## 2. Step-by-Step Serial Landing Pipeline` | Differ in text | Qualified | `serial-merge-and-conflicts.md` §2 | Rebase candidate; delta review on changed SHA; standard push; no target checkout in secondary worktree. |
| `serial-merge-and-conflicts.md`: `## 3. Merge Conflict Resolution Protocol` | Installed only | Merged | `serial-merge-and-conflicts.md` §3 | 5-step conflict resolution engine: path-safe `git diff --name-only --diff-filter=U`, understand intent, reconcile hunks. |
| `serial-merge-and-conflicts.md`: `## 3. Self-Contained Merge Conflict Resolution Engine` | Remote only | Merged | `serial-merge-and-conflicts.md` §3 | 5-step conflict resolution engine: path-safe `git diff --name-only --diff-filter=U`, understand intent, reconcile hunks. |
| `serial-merge-and-conflicts.md`: `## 4. Post-Merge Teardown & Resource Cleanup` | Installed only | **Rejected** / Replaced | `lifecycle-and-cleanup.md` | **Anti-Patterns Rejected**: `branch -D` fallback, global remote prune, zero-worktree prune goal replaced with safe decoupled 3-stage lifecycle. |
| `serial-merge-and-conflicts.md`: `## 4. Worktree Lifecycle, Herdr Defaults & Clean Teardown` | Remote only | **Rejected** / Replaced | `lifecycle-and-cleanup.md` | **Anti-Patterns Rejected**: `branch -D` fallback, global remote prune, zero-worktree prune goal replaced with safe decoupled 3-stage lifecycle. |
| `terminal-and-event-rules.md`: `## 1. Live Coordinates` | Differ in text | Merged | `topology-and-worktrees.md` §3, `event-monitoring.md` | Coordinate query via `herdr pane current --current`. |
| `terminal-and-event-rules.md`: `## 2. Reading Pane State` | Differ in text | Merged | `event-monitoring.md` §1 | Snapshot sources (`recent-unwrapped`, `visible`, `recent`, `detection`). |
| `terminal-and-event-rules.md`: `## 3. Communication & PTY Delivery Rules` | Differ in text | Merged | `event-monitoring.md` §3 | Bracketed paste pacing delay; no-wait worker notices. |
| `terminal-and-event-rules.md`: `## 4. Modal Bridge` | Differ in text | Qualified | `event-monitoring.md` §4, `harness-antigravity.md` §4 | Blind Enter on launch rejected; inspect screen and resolve based on visible authorized choice. |
| `terminal-and-event-rules.md`: ``## 5. Degraded AGY Mode (`herdr pane run`)`` | Differ in text | Merged | `event-monitoring.md` §5 | Keystroke injection fallback; verifies foreground program and input-ready composer. |
| `terminal-and-event-rules.md`: `## 6. The 10-Minute Silent Boundary` | Differ in text | Merged | `event-monitoring.md` §7 | Restored under Section 7: single read check at tool boundary; no tight polling loops or heartbeats. |
| `ticket-decomposition-and-waves.md`: `## 1. Automatic Ticket Intake & GitHub Issue Creation` | Identical | Qualified | `ticket-decomposition-and-waves.md` §1 | Vertical tracer-bullet slicing; context-bounded sizing; expand-contract; optional issue creation. |
| `ticket-decomposition-and-waves.md`: `## 2. Multi-Wave Parallelism Graph (Waves 1 to 5)` | Identical | Qualified | `ticket-decomposition-and-waves.md` §2 | **Arbitrary 5-Wave Cap Rejected**: Dynamic DAG waves; prerequisite-driven advance; whole-wave merge barriers rejected. |
| `ticket-decomposition-and-waves.md`: `## 3. "Write Back to Me" Continuous Feedback Loop` | Identical | Merged | `ticket-decomposition-and-waves.md` §3 | Worker handback callback, streaming review dispatch, serial integration and dynamic unblocking. |
