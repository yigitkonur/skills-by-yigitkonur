# Operational Observation, Events & Return Routing

Read this reference before submitting tasks, configuring callbacks, or supervising agent panes. This document defines the operational observation mechanics, screen buffer physics, prompt delivery protocols, and return routing across all Herdr orchestration roles.

For report schemas, publication mechanics, and manager consumption semantics, route to the canonical contract at [report-contract.md](report-contract.md).

---

## 1. Role Selection & Authority Gate (Cold Reader Intake)

Herdr's orchestration graph serves multiple roles from a single shared skill definition. **Runtime identity is not role identity.** Running inside `agy`, `codex`, or `claude` does not define your authority; your assigned mission brief defines your role.

Every cold reader must discover its assigned role before executing observation commands:

| Assigned Role | Authority & Observation Scope | Prohibited Actions |
|---|---|---|
| **Engineering Manager (EM)** | Central control plane: observes all worker panes, consumes immutable YAML reports, maintains `state.yaml`, handles wait timeouts, and relays peer inquiries. | Never author feature code directly in the management checkout; never push directly to `main`. |
| **Implementer / Worker** | Task execution in isolated worktree checkout: executes TDD cycle, publishes immutable reports to `report_root`, and dispatches no-wait notices to the manager return pane. | Never initialize a competing management hierarchy; never prompt or inspect peer worker panes. |
| **Reviewer** | Independent technical review: audits candidate diffs (`gh pr diff` or exact-SHA checkouts), conducts verification checks, and publishes review reports with structured verdicts. | Never edit production code under review; never mutate manager state; never spawn worker panes. |
| **Integration Executor** | Serial baseline reconciliation, worktree provisioning, branch rebase verification, and opening candidate draft PR or executing mission-authorized delivery. | Never merge without explicit candidate sign-off; never run concurrent conflicting rebases. |
| **Recovery Executor** | Targeted intervention for stopped, stalled, or crashed panes; reconciles native task inventories and active background processes. | Never perform blind kills (`kill -9` / `pkill`); never relaunch agents over live interactive TUIs. |
| **CTO** | Strategic governance, candidate evidence gates, and milestone reviews. If operating in a native Herdr pane, receives native PTY prompts without `--wait`; if on a non-pane host, observes via the manual-observation boundary without callback promises. | Does not manage fine-grained pane loops; operates outside native callback guarantees when hosted on a non-pane environment. |

### Stable Governance Invariants
- **Manager Alone Increments Attempts**: The Engineering Manager alone increments task `attempt` counters in `state.yaml`. Producers always match their assigned `attempt`; corrections use fresh `report_id`s within the assigned attempt.
- **Strict Ingestion Matching**: The manager matches exact assigned `mission_id`, `task_id`, `attempt`, and registered producer coordinates before acting on evidence; quarantines future attempts, and rejects obsolete attempts from advancing state.
- **Universal Report Immutability**: All published reports—including Codex manager reports—are strictly immutable. Only `state.yaml` serves as a mutable checkpoint.
- **Session Metadata**: Session UUID is optional and recorded as unavailable/null when unexposed by the runtime; verified terminal and pane coordinates remain load-bearing.
- **Portable Return Coordinates**: All reusable documentation and notice templates use dynamic discovered parameters (`$MANAGER_PANE_ID`, `$CALLER_PANE_ID`), never hardcoded host pane IDs.

### Leadership Tab & Pane Topology
Herdr separates mission leadership from task execution:
- **One Leadership Tab, Exactly Two Panes**: The mission leadership tab hosts strictly two panes: CTO on the left and Engineering Manager (ENG-MAN) on the right.
- **Cold Bootstrap via Right Split**: During cold bootstrap, the EM pane is created via a horizontal split to the right from the CTO pane (`herdr pane split --direction right ...`). Bootstrap verification must confirm that both panes share the identical `tab_id` (`herdr tab get`) and verify the actual horizontal layout (CTO at x=0, EM to the right at x>0 via `herdr pane layout` and `herdr pane list`).
- **Task & Reviewer Isolation**: Task worker and reviewer panes operate in separate dedicated tabs to isolate screen buffers, tool noise, and PTY state from leadership observation.
- **Preserve Session Identities**: Existing session identities are preserved across leadership reorganizations; the CTO alone migrates live panes (such as moving live `p8`), and agents must never move, split, or restart live panes autonomously.

---

## 2. Native Identity Discovery & Return Address Registration

Every agent must discover its native coordinates immediately upon startup. These identifiers anchor all downstream return notifications and state transitions:

```bash
# Discover live caller coordinates
CALLER_PANE_ID="${HERDR_PANE_ID:-$(herdr pane current | jq -r .result.pane.pane_id)}"
CALLER_TAB_ID="${HERDR_TAB_ID:-$(herdr pane current | jq -r .result.pane.tab_id)}"
CALLER_TERM_ID="${HERDR_TERMINAL_ID:-$(herdr pane current | jq -r .result.pane.terminal_id)}"
CALLER_CWD="$(herdr pane current | jq -r .result.pane.cwd)"
```

### Worker Registration Protocol
Before executing engineering work, a newly started worker registers its confirmed identity with the manager return address (`$MANAGER_PANE_ID`) by dispatching a native notice without `--wait`:

```bash
herdr agent prompt "$MANAGER_PANE_ID"   "Registration notice: task=$TASK_ID attempt=$ATTEMPT mission=$MISSION_ID status=registered pane=$CALLER_PANE_ID tab=$CALLER_TAB_ID terminal=$CALLER_TERM_ID runtime=$RUNTIME model=$MODEL cwd=$CALLER_CWD. Ready and awaiting assignment acknowledgment."
```

---

## 3. The 3-Axis Decoupling Axiom

Multi-agent orchestration requires decoupling three distinct state dimensions:

```
+---------------------------------------------------------------------------------------+
| THE 3-AXIS DECOUPLING                                                                 |
+---------------------------------------------------------------------------------------+
| 1. WORKER STATE (PTY / Screen)       : idle | working | blocked | done | unknown      |
| 2. OBSERVER STATE (Host Wait Handle) : none | waiting | settled | timed_out           |
| 3. DELIVERY STATE (Engineering / Git): implementation -> draft_pr -> clean_review     |
|                                        -> ready_for_review -> integrated              |
|                                           (mission-authorized scope: unmerged / merge)|
+---------------------------------------------------------------------------------------+
```

### Critical Invariants:
1. **Observer Timeout $
eq$ Worker Failure**: When `herdr agent wait` hits a deadline, the worker is not broken; the observer simply reached its inspection boundary.
2. **Idle Worker $
eq$ Completed Task**: An agent resting at an idle prompt may have failed a test, crashed a subshell, or halted mid-turn. Settlement only grants permission to read evidence.
3. **Unknown Remains Unknown**: If an observer handle disconnects or an agent status reports `unknown`, the state is unverified. Never assume failure or success without reading screen and filesystem evidence.
4. **Quota Stalls Are Neither Dead Nor Idle**: Visible API rate limits or quota exhaustion (HTTP 429, `ResourceExhausted`) are neither dead worker processes nor successful idle completions. Observers must preserve owned pending effects, cease blind same-model retries, and route to the quota protocol in [stopped-agent-recovery.md](stopped-agent-recovery.md).

---

## 4. Terminal Screen Inspection: The 4 Buffers & Alt-Screen Physics

Full-screen interactive TUIs run on the terminal's **Alternate Screen Buffer** (`\x1b[?1049h`), where historical off-screen output is not preserved in PTY scrollback memory. Herdr provides four distinct read sources:

| Source | CLI Syntax | Scope & Intended Use Case |
|---|---|---|
| **`recent-unwrapped`** | `herdr agent read <target> --source recent-unwrapped --lines <N>` | **Operational Context & Unwrapped Terminal Text**: Merges soft line wraps caused by narrow terminal columns. Used for inspecting recent agent output, error traces, and operational context. Does not constitute a complete or semantic transcript; formal verification evidence belongs in durable YAML reports on disk. |
| **`visible`** | `herdr agent read <target> --source visible --lines <N>` | **Modals & Spinners**: Captures the exact 2D rendered viewport. Mandatory for inspecting interactive menus (`ask_question`), confirmation prompts (`[y/N]`), live thinking spinners, and cursor focus. |
| **`recent`** | `herdr agent read <target> --source recent --lines <N>` | **Columnar Data**: Preserves fixed column alignments for ASCII diagrams, tabular terminal reports, and status grids. |
| **`detection`** | `herdr agent read <target> --source detection` | **Rule Introspection**: Plain text evaluated against Herdr's regex rules. Used strictly for heuristic diagnostic debugging (`herdr agent explain <target>`), never for verifying delivery evidence. |

### The Durable Report Evidence Rule
Terminal PTY reads provide operational management context, but are bounded, lossy, and subject to terminal column wrapping and alt-screen redrawing. Never treat terminal screen scrapes as complete transcripts or formal verification evidence. All verifiable deliverables, test results, and status declarations must be published to durable, immutable YAML reports under `report_root` on disk (see [report-contract.md](report-contract.md)).

---

## 5. Input Delivery & Prompting Protocols

### Default Operational Notification (Enter / Bracketed Paste)
To submit a prompt or notification to a recognized agent, use `herdr agent prompt`:

```bash
herdr agent prompt <TARGET> "<PROMPT_TEXT>"
```

- **Bracketed Paste Mechanics**: Wraps text in DEC Mode 2004 (`\x1b[200~...\x1b[201~`), signaling to terminal applications that incoming text is a paste block rather than interactive typing.
- **Staged Delay**: Enforces a configured pacing pause (`AGENT_PROMPT_SUBMIT_DELAY`, typically 300ms) before transmitting `\r` (Enter). This delay provides pacing for the terminal application's event loop to consume pasted input before newline submission; it does not guarantee prevention of character drops or eliminate all PTY race conditions under heavy load.
- **Receiver Disambiguation (Codex vs. AGY Writers)**:
  - **Busy Codex Operational Notices**: An idle Codex manager or worker consumes prompts immediately upon receipt. When Codex is executing a tool call or prompt turn, it buffers incoming operational text in its PTY input queue and reads it at the next turn boundary. However, busy delivery is not a guaranteed, loss-free synchronization mechanism under rapid PTY churn.
  - **Active AGY Writers**: In contrast, injecting prompt text into an active AGY writer while it is synthesizing code or generating tool calls can disrupt the agent's turn, corrupt active composer state, or collide with file writes. Active writers must never be interrupted with prompt injections while working; wait for idle settlement or use non-interrupting coordination.
- **Worker Notices Omit `--wait`**: Workers must NEVER pass `--wait` when notifying the manager. Passing `--wait` blocks the worker process and causes callback deadlocks if the manager attempts to prompt back.

### Canonical Notice Protocol & Schema Link
Worker and reviewer notices must adhere strictly to the canonical notice protocol and field parity requirements defined in [report-contract.md Section 5](report-contract.md#5-native-notification-protocol-prompt-staging-and-concise-notice-format). Do not duplicate or alter notice schemas; all notices route through the single canonical contract.

### Deferred Input (Tab)
Tab is an optional whole-turn-deferred input mode supported by specific agent composers:
- Requires **exclusive composer ownership**: the target agent must be sitting at a dedicated, empty interactive composer prompt.
- **Never use Tab for urgent alerts or operational fan-in notifications.** Enter is the universal, non-exclusive operational default.

### The Modal Bridge (`herdr agent send-keys`)
When an agent encounters a blocking modal prompt (`ask_question`, bash tool approval `[y/N]`), Herdr transitions the agent state to `blocked` and actively rejects `herdr agent prompt` with `error.code: agent_blocked` to protect the PTY from corrupted text.

Resolve blocked modals mechanically:
1. Read the visible viewport:
   ```bash
   herdr agent read <target> --source visible --lines 20
   ```
2. Send pre-validated keystrokes to select and submit:
   ```bash
   herdr agent send-keys <target> down enter
   ```
   *Valid key tokens: `up`, `down`, `enter`, `esc`, `tab`, `ctrl+c`.*

---

## 6. Degraded Mode: `herdr pane run` Fallback

In scenarios where an agent is active in an interactive terminal but Herdr's detection rules report `unknown` (e.g., custom wrappers or unmapped TUI headers):
1. First verify that foreground AGY is running and its composer is visible:
   ```bash
   herdr pane process-info --pane <PANE_ID>
   herdr pane read --source visible --lines 10 <PANE_ID>
   ```
2. If confirmed, use the verified native fallback command `herdr pane run`:
   ```bash
   herdr pane run <PANE_ID> <COMMAND>...
   ```
3. **Safety Invariants**:
   - `pane run` injects text followed by Enter into the target pane.
   - **Never use `pane run` on an unverified shell prompt or background task.**
   - **Never relaunch an agent over a live TUI session.**

---

## 7. Host Observer Mechanics & Supervision Patterns

Supervising managers track worker lanes using bounded event waits rather than tight loops:

```bash
herdr agent wait <TARGET> --until idle --until done --timeout 60000
```

### Supervisor Guidelines:
- **One Observation Handle Per Target/Attempt/Purpose**: Do not spawn competing background watchers on the same pane.
- **Distinguish Host Handles**: Distinguish `session_id` (the underlying execution process) from outer orchestration wait cells (`cell_id`).
- **The 10-Minute Silent Boundary Rule**: Multi-agent operations must never rely on fictional cron schedulers or unverified background wake promises. If an agent operates without state transitions for 10 minutes, it must record a checkpoint report at its next safe tool boundary.
- **CTO Routing & Non-Pane Boundary**: A CTO may operate inside a native Herdr pane (receiving native PTY prompts without `--wait`, e.g. `$CTO_PANE_ID`) or outside panes on a non-pane host. When the CTO is on a non-pane host, native PTY callbacks cannot be promised; the EM maintains an honest manual-observation boundary, checkpointing progress in `state.yaml` and publishing structured milestone reports.

---

## 8. Delivery & PR Integration Gates

1. **Mission-Specific Delivery Scope**:
   - Delivery authority and integration scope are mission-specific. Some missions (such as multi-agent coordination lanes with human-in-the-loop checkpoints) define delivery to conclude at an integrated, verified draft PR left unmerged for final sign-off. Other missions authorize full delivery, including serial squash-merging to `main`, cleanup, or release.
   - Individual lane writers commit to their isolated branch checkouts without opening competing individual PRs.
   - The assigned Integration Executor rebases verified commits serially and executes the integration actions authorized by the specific mission brief.
2. **General Authorized Delivery Sequence**:
   - Worker synthesizes tests and code in isolated worktree.
   - Rebase serially on `origin/main` and verify test suite passes (green).
   - **Exact-SHA Review Gate**: Independent Reviewer audits candidate diff and exact head in a clean context. Any rebase or code change produces a new commit SHA that invalidates prior reviews; delivery cannot proceed on a stale review.
   - Only after the exact candidate head is approved and checks pass: promote PR to ready (`gh pr ready <PR_NUM>`) if PR delivery is authorized.
   - Merge serially (squash-merge) into main when authorized by delivery brief.
   - Clean up worktree and pane containers.
