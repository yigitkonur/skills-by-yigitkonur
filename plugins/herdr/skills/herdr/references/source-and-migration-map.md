# Source & Migration Traceability Map

This document establishes the exhaustive provenance, mapping, and disposition of all rule groups from the upstream Herdr specification, the canonical Herdr skill, the retired Herdr-Lite skill, and field evaluation experience into the unified Herdr skill architecture.

---

## 1. Upstream & Source Provenance

- **Canonical Repository Base**: `yigitkonur/skills-by-yigitkonur` at commit `b7a8889716e825e590028665b3b8d4fe7bf85ba1`.
- **Upstream Herdr Specification**: `herdrdev/herdr` at commit `c34dd6b2acd432cb7acbe9de568b245853e3b8c7` (`sources/herdr-upstream-SKILL.md`).
- **Canonical Herdr Source**: `skills/herdr/SKILL.md` and 6 references (`report-contract.md`, `parallel-capacity.md`, `mission-briefs.md`, `serial-merge-and-conflicts.md`, `event-monitoring.md`, `stopped-agent-recovery.md`).
- **Canonical Herdr-Lite Source**: `skills/herdr-lite/SKILL.md` and 7 references (`herdr-primitives.md`, `orchestration-workflow.md`, `recovery-and-safeguards.md`, `review-and-fix-contract.md`, `serial-merge-and-conflicts.md`, `terminal-and-event-rules.md`, `ticket-decomposition-and-waves.md`).
- **Operational Experiences & Field Reports**:
  - Grounded operational findings from `/tmp/herdr-merge-experiences-20260926/` (notes 01 to 13).
  - Isolated AGY probe verification (`probe-agy-controller-verification.json`).
  - User-supplied evaluation across multi-repo reviews.

---

## 2. Rule Group Disposition Summary

| Disposition | Definition |
|---|---|
| **Retained** | Preserved with its original intent, updated for unified terminology and command accuracy. |
| **Merged** | Unified from duplicate definitions across Herdr and Herdr-Lite into a single authoritative source. |
| **Qualified** | Retained with specific operational bounds, edge-case conditions, or harness-specific caveats. |
| **Rejected** | Explicitly removed due to architectural friction, prompt bloat, or verified anti-patterns. |

---

## 3. Comprehensive Rule Group Mapping Ledger

### A. Upstream Herdr Rules (`sources/herdr-upstream-SKILL.md`)

| Source Section / Heading | Disposition | Destination Reference | Rationale & Acceptance Criteria |
|---|---|---|---|
| `## Learn the current CLI` (`HERDR_ENV=1` Check) | Retained | `SKILL.md`, `operating-modes.md` | Verification gate ensuring control commands execute only within Herdr-managed panes. |
| `## Learn the current CLI` (Installed Help Authority) | Retained | `SKILL.md`, `herdr-primitives.md` | Installed CLI binary is authoritative for flags and syntax; prohibits inventing flags. |
| `## Use IDs and caller context` (Opaque ID Handles) | Merged | `topology-and-worktrees.md`, `herdr-primitives.md` | Stable opaque IDs (`w1`, `w1:t1`, `w1:p1`); dynamic coordinates via `herdr pane current --current`. |
| `## Use IDs and caller context` (Saved SSH Machines `--machine`) | Retained | `herdr-primitives.md` §5 | Dedicated `--machine` forwarding rules, server-scoped IDs, absolute/tilde paths, no TUI required. |
| `## Start and coordinate an agent` (Geometry Split Rules) | Merged | `topology-and-worktrees.md` §2 | Inspect dimensions; split right for $\ge 120$ cols, down for tall/narrow; avoids unreadable 12-col trap. |
| `## Start and coordinate an agent` (Prompt Delivery & Paste) | Merged | `event-monitoring.md` §3 | DEC Mode 2004 bracketed paste timing, `--wait` lifecycle settlement, and no-wait worker notices. |
| `## Start and coordinate an agent` (Logical Keys `send-keys`) | Merged | `herdr-primitives.md` §1, `event-monitoring.md` §4 | Standardizes `esc`, `enter`, `ctrl+c`, `up`, `down`, `tab`. Canonical Escape token is `esc`. |
| `## Run an ordinary command in another pane` (Read Sources) | Merged | `event-monitoring.md` §1 | Maps `recent-unwrapped`, `visible`, `recent`, `detection` to logging, modal, and columnar tasks. |
| `## Safety and coordination rules` (Server Stop Prohibition) | Merged | `stopped-agent-recovery.md` §4 | Strictly prohibits `herdr server stop` or blanket kills from active sessions. |

---

### B. Core Orchestration & Workflow Rules

| Source Section / Heading | Disposition | Destination Reference | Rationale & Acceptance Criteria |
|---|---|---|---|
| `herdr-lite/SKILL.md`: `## Two-Tier Leadership Architecture` | **Rejected** / Replaced | `operating-modes.md` | **Anti-Pattern**: Mandatory CTO/EM manager hierarchy for small tasks creates workspace sprawl. Replaced with 3 task-size modes: Direct (Mode 1), Task (Mode 2), Managed (Mode 3). |
| `herdr/SKILL.md`: `## 1. Operating Modes & Routing` | Retained | `operating-modes.md` | Direct path defined as genuinely small/bounded work (inspection, 1 command, bounded fix), not arbitrary single-file work. |
| `herdr-lite/references/ticket-decomposition-and-waves.md`: `## 1. Automatic Ticket Intake` | Retained | `ticket-decomposition-and-waves.md` §1 | Vertical tracer-bullet slicing across layers; context-bounded sizing; expand-contract for wide refactors. |
| `herdr-lite/references/ticket-decomposition-and-waves.md`: `## 2. Multi-Wave Parallelism Graph` | **Qualified** / Merged | `ticket-decomposition-and-waves.md` §2 | **Arbitrary 5-Wave Cap Rejected**: Dynamic DAG waves continue until dependency edges converge naturally without an artificial 5-wave ceiling. |
| `herdr-lite/references/orchestration-workflow.md`: `## 4. Step 2: Dedicated Worktree & Workspace Provisioning` | **Qualified** / Merged | `topology-and-worktrees.md`, `operating-modes.md` §3 | Dedicated worktrees (`herdr worktree create`) are reserved for dirty/concurrent write isolation. Read-only lanes retain tab/pane routes to prevent workspace sprawl. |
| `herdr-lite/references/orchestration-workflow.md`: `## 5. Step 3: Event-Driven Streaming Review` | Retained | `parallel-capacity.md` §5, `review-and-fix-contract.md` | **Streaming Reviews Law**: Reviews decouple per-lane; reviewer starts immediately upon worker completion. Whole-fleet blocking wait is rejected. |
| `herdr-lite/references/orchestration-workflow.md`: Side-by-Side Review Pane Split | Retained | `topology-and-worktrees.md` §1, `parallel-capacity.md` §5 | Splits tab right inside the task checkout, preserving live implementer output during review. |
| `herdr-lite/SKILL.md`: Mandatory Slash Prefixes (`/teamwork-preview /herdr`) | **Rejected** / Qualified | `mission-briefs.md` §2, `harness-codex.md` §3 | **Anti-Pattern**: Universal slash prefixes cause Codex parser failures. Plain-language briefs are fully valid; slash commands are reserved for tasks explicitly requiring them. |
| `herdr-lite/references/recovery-and-safeguards.md`: `## 4. Subagent Model Tiering` | **Rejected** / Replaced | `parallel-capacity.md` §2 | **Forced Flash Tiering Rejected**: Model and effort follow user instructions strictly; no speculative tier names or silent downgrades. Host capacity limits concurrency. |
| `herdr/references/parallel-capacity.md`: `## 2. Early Coherent Local Candidate Path` | Retained | `parallel-capacity.md` §3 | Single designated writer with whole-change ownership prepares and verifies candidate locally, avoiding redundant per-file approval bottlenecks. |

---

### C. Communication, Modals & Harness Physics

| Source Section / Heading | Disposition | Destination Reference | Rationale & Acceptance Criteria |
|---|---|---|---|
| `herdr-lite/references/terminal-and-event-rules.md`: `### 4.1 Worktree Project Trust Modal Bypass` | **Rejected** / Qualified | `harness-antigravity.md` §3 | **Anti-Pattern**: Blindly sending Enter after launch causes unintended turn submission if composer is reached. Replaced with visible buffer inspection before sending Enter. |
| `/tmp/01-agy-queued-pause.md` & `probe-agy-controller-verification.json`: AGY Queued Turn Dynamics | **Retained** (New) | `harness-antigravity.md` §1 | Input submitted during `working` state queues until turn finishes. Single wakeup owner invariant. |
| `/tmp/01` & `/tmp/03`: Staged-After-Escape Recovery | **Retained** (New) | `harness-antigravity.md` §2 | Pre-Escape inspection (modal and mutation checks). Targeted `esc` promotes message to composer; submit EXISTING text once with Enter without duplicate paste. |
| `probe-agy-controller-verification.json`: Child vs. Turn Disconnection | **Retained** (New) | `harness-antigravity.md` §2.3 | Distinguishes interrupted cognitive LLM turn from surviving child processes (exit 0). Reconciles process info and visible buffer. |
| `approved-plan.md` (Communication Contract): Consumed Evidence | **Retained** (New) | `harness-antigravity.md` §2.2, `report-contract.md` §2 | Empty queue or working state does not prove consumption. Recorded receipt IDs in `state.yaml` or disk artifacts provide proof. |
| `/tmp/02-codex-steering.md`: Codex Steering & Native Queue | **Retained** (New) | `harness-codex.md` §1, §2 | Enter delivers tool boundary steering; Tab enqueues deferred follow-up. Native `codex queue --thread --message` supported; AGY Escape mechanics prohibited on Codex. |
| `/tmp/05-startup-timeout.md`: Startup Timeout with Live Tools | Retained | `harness-other.md` §3 | Startup timeout does not prove launch failure. Check process tree and visible output before retrying. |
| `herdr/references/event-monitoring.md`: `### Runtime-Aware Notice Qualification` | Merged | `event-monitoring.md` §3 | Worker notices omit `--wait` to prevent callback deadlocks. |
| `herdr/references/event-monitoring.md`: `## 5. Degraded AGY Mode (herdr pane run)` | Merged | `event-monitoring.md` §5 | Verify foreground process and clean visible composer before fallback keystroke injection. |
| `herdr/references/event-monitoring.md`: `## 7. The 10-Minute Silent Boundary` | Merged | `event-monitoring.md` §6 | Single status read at safe tool boundary; prohibits tight polling loops and artificial heartbeat timers. |

---

### D. Durable Reports, Review & Integration

| Source Section / Heading | Disposition | Destination Reference | Rationale & Acceptance Criteria |
|---|---|---|---|
| `herdr/references/report-contract.md`: `## 1. Exactly Two Durable Artifact Kinds` | Retained | `report-contract.md` §1 | Mutable manager checkpoint (`state.yaml`) vs. immutable producer handbacks outside worktrees. |
| `approved-plan.md`: Separation of Published / Submitted / Consumed / Acted | Retained | `report-contract.md` §2 | Distinguishes disk write, transport submission, recipient receipt, and state graph execution. |
| `herdr/references/report-contract.md`: `## 3. Canonical Producer Report Schema` | Retained | `report-contract.md` §4 | Schema v1 backward compatibility: retains `producer.skill_revision`, `cto` routing, `in_progress` status. |
| `herdr/references/report-contract.md`: `## 4. Atomic Publication Pipeline` | Retained | `report-contract.md` §5 | Write `.partial`, validate syntax/shape/digest, atomic rename `mv -n`, post-rename 3-point check, TOCTOU check. |
| `herdr/references/report-contract.md`: `## 6. Manager Consumption Semantics` | Retained | `report-contract.md` §7 | Identity gate, attempt gate, idempotent digest check (`MUTATED_REPORT_REJECTED` on mismatch), receipt is NOT approval. |
| `herdr/references/report-contract.md`: Pending-Effects Reconciliation | Retained | `report-contract.md` §7 | Unresolved effects must be resolved or explicitly accepted before advancing the task graph. |
| `herdr-lite/references/review-and-fix-contract.md`: `## 1. Exact-SHA Review Invariant` | Merged | `review-and-fix-contract.md` §1 | Review binds strictly to verified 40-character commit SHA (`git rev-parse HEAD`). |
| `herdr/references/parallel-capacity.md`: `## 3. Review Invalidation & Delta Decisions` | Merged | `review-and-fix-contract.md` §1 | Any commit advance invalidates prior review ($SHA_2 \neq SHA_1$); delta decision on newly changed diff. |
| `herdr-lite/references/review-and-fix-contract.md`: `## 3. Finite Review Bounds & Failure Budget` | Merged | `review-and-fix-contract.md` §3 | Two-round failure budget halts retries; no artificial resets; no material waivers. |
| `herdr-lite/references/review-and-fix-contract.md`: Reviewer Self-Approval | **Rejected** / Qualified | `review-and-fix-contract.md` §2 | Reviewers are read-only hardening partners. Direct fixes transfer reviewer to author, requiring independent final review. |
| `herdr/references/serial-merge-and-conflicts.md`: `## 2. Step-by-Step Serial Landing Pipeline` | Merged | `serial-merge-and-conflicts.md` §2 | Serially rebase verified candidates onto mission-authorized branch with exact integrated checks. |
| `herdr-lite/references/serial-merge-and-conflicts.md`: Forced Merge to `main` | **Rejected** / Qualified | `serial-merge-and-conflicts.md` §1 | Target baseline is the mission-authorized branch (not hardcoded `main`). |
| `herdr/references/serial-merge-and-conflicts.md`: `## 3. Self-Contained Merge Conflict Resolution Engine` | Retained | `serial-merge-and-conflicts.md` §3 | 5-step engine: observe state, understand intent, reconcile hunks (preserve invariants), check, `GIT_EDITOR=true` continue. |
| `herdr-lite/references/serial-merge-and-conflicts.md`: Blanket Rebase No-Abort Rule | **Rejected** / Qualified | `serial-merge-and-conflicts.md` §4 | Safe abort (`git rebase --abort`) is authorized if target baseline or scope is structurally invalid. |

---

### E. Teardown, Cleanup & Lifecycle

| Source Section / Heading | Disposition | Destination Reference | Rationale & Acceptance Criteria |
|---|---|---|---|
| `approved-plan.md` & `herdr/references/parallel-capacity.md`: Decoupled 3-Stage Teardown | Retained | `lifecycle-and-cleanup.md` | Decouples terminal retirement, worktree checkout removal, and local branch retirement. |
| `herdr/references/parallel-capacity.md`: `### 5a. Prompt Terminal & Pane Retirement` | Merged | `lifecycle-and-cleanup.md` §1 | Close worker pane once report is verified on disk; implementer pane preserved during active review. |
| `herdr/references/parallel-capacity.md`: `### 5b. Worktree Removal Gate` | Merged | `lifecycle-and-cleanup.md` §2 | Gate on clean tree (`git status --porcelain`) and verified remote merge; preserves dirty checkouts. |
| `herdr-lite/references/serial-merge-and-conflicts.md`: Automatic `branch -D` and Zero-Worktree Goal | **Rejected** / Qualified | `lifecycle-and-cleanup.md` §2, §3 | Local branch deletion happens only after worktree checkout is unlinked. No global zero-worktree prune goal; unrelated worktrees untouched. |
| `approved-plan.md`: Leadership Retirement Invariant | Qualified | `lifecycle-and-cleanup.md` §1 | Leadership panes retire only when all coordination duties conclude, not at arbitrary waves. |

---

### F. Field Experience & User-Supplied Evaluation

| Source Topic / Evaluation Insight | Disposition | Destination Reference | Rationale & Acceptance Criteria |
|---|---|---|---|
| Multi-repository ownership & coordinated delivery | Retained | `operating-modes.md` §3, `mission-briefs.md` | Retained as bounded capability for complex cross-repo managed missions. |
| Native internal subagent coordination | Retained | `parallel-capacity.md` §2 | Native subagents permitted where runtime supports them; counted in total host capacity. |
| Audit-before-uncertain-changes | Retained | `review-and-fix-contract.md` §2 | Pre-flight inspection of baseline diff and tests before making modifications. |
| Safe long-prompt handling | Retained | `mission-briefs.md` §6 | Submitting prompts via files/heredocs to avoid argument overflow or escaping issues. |
| Universal audit-plan-user-approval gates | **Rejected** | `operating-modes.md` §1, §2 | Low-ceremony paths proceed without halting for unnecessary human approval gates. |
| Mandatory subteams & 5000-line plans | **Rejected** | `operating-modes.md`, `mission-briefs.md` | Sized to task scope; no forced subteams for small tasks; concise operational briefs. |
| Perpetual status pressure & polling | **Rejected** | `event-monitoring.md` §6 | 10-minute boundary; push callbacks over continuous status polling. |
