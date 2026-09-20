# Canonical Report Contract & Durable Mission Artifacts

Read this reference to understand the durable artifact contract, publication mechanics, consumption semantics, and native notification protocol for Herdr orchestration missions.

This document is the **single canonical source of truth** for:
1. Durable artifact kinds and schema definitions.
2. Atomic report publication pipeline (`.partial` → verify → atomic rename → native notice).
3. Concise native notice format and field parity.
4. Manager consumption semantics (idempotency, digest checking, obsolete attempt pruning, receipt vs. approval).
5. Reviewer Q/A and explicit return coordinate protocols.

Other references (`event-monitoring.md`, `mission-briefs.md`, `parallel-capacity.md`, `stopped-agent-recovery.md`) route to this contract rather than duplicating its schemas.

---

## 1. Architectural Core: Exactly Two Durable Artifact Kinds

To eliminate split-brain state, race conditions, and unstructured log scraping, Herdr orchestration missions use **exactly two durable artifact kinds**:

```
+---------------------------------------------------------------------------------------+
| DURABLE MISSION ARTIFACT TOPOLOGY                                                     |
+---------------------------------------------------------------------------------------+
| KIND 1: MANAGER-OWNED CHECKPOINT (state.yaml & manager-m<N>-<purpose>.yaml)          |
| - Location: Absolute mission run root outside disposable worktrees.                   |
| - Owner: Codex Engineering Manager (EM) alone.                                        |
| - Contents: Global task graph (dependencies, states, owners), active assignments,    |
|   consumed producer report IDs & SHA-256 digests, decisions log, action log,          |
|   pending unknown effects, recovery resume instructions.                              |
+---------------------------------------------------------------------------------------+
| KIND 2: PRODUCER-OWNED IMMUTABLE YAML REPORTS (<task>-a<attempt>-<purpose>.yaml)       |
| - Location: Absolute mission run root outside disposable worktrees.                   |
| - Owner: Individual producer agent (AGY implementer, fresh reviewer, integrator).     |
| - Contents: Strict YAML contract declaring identity, actual runtime/terminal, status, |
|   truthful summary, evidence commands & exit codes, exact Git base/head, blockers,    |
|   requested action, pending operations with unknown effects.                          |
| - Invariant: Immutable once published. Never edited or overwritten in place.          |
+---------------------------------------------------------------------------------------+
```

### Run Root Invariant
Both artifact kinds reside in a single shared, absolute directory on the host filesystem (`report_root`, e.g., `/Users/mac/docs/superpowers/runs/<mission_id>`).
- **Never write mission reports inside Git worktrees**: Worktrees are disposable ephemeral checkouts that may be reset, switched, or pruned upon task completion.
- **Never communicate mission state via untyped raw terminal chat**: State changes must be anchored to an immutable YAML report.

---

## 2. Canonical Producer Report Schema

Every producer report must conform to this complete YAML schema:

```yaml
schema_version: 1                        # Integer contract version (currently 1)
mission_id: <string>                     # Unique mission identifier (e.g. herdr-codex-first-20260920)
task_id: <string>                        # Task identifier from manager task graph (e.g. report_contract)
attempt: <integer>                       # 1-indexed attempt counter (e.g. 1)
report_id: <string>                      # Unique canonical ID: <task_id>-a<attempt>-<purpose>
event_id: <string>                       # Optional fine-grained event tracker: <task_id>.<purpose>.<seq>

producer:
  runtime: <string>                      # Runtime binary name: agy | codex | claude
  model: <string>                        # Specific model identifier: gemini-3.8-flash-high | gpt-6-astra
  pane_id: <string>                      # Herdr pane identifier: e.g. w3H:pA
  tab_id: <string>                       # Herdr tab identifier: e.g. w3H:t8
  terminal_id: <string>                  # Underlying PTY terminal ID: e.g. term_65beaae4006d89a
  session_id: <string>                   # Unique agent session UUID
  skill_revision: <string>               # Optional SHA or git revision of loaded skill

manager:
  pane_id: <string>                      # Manager return pane: e.g. w3H:p8
  tab_id: <string>                       # Manager return tab: e.g. w3H:t6

cto:
  pane_id: <string>                      # Root CTO return pane: e.g. w3H:p3
  tab_id: <string>                       # Root CTO return tab: e.g. w3H:t3

status: <string>                         # Enum: in_progress | completed | blocked | failed | milestone
summary: <string>                        # Concise, truthful executive summary of progress or findings

evidence:                                # Structured log of every verification check executed
  - command: <string>                    # Exact shell command executed
    exit_code: <integer>                 # Observed return code (0 = success)
    result: <string>                     # Observed output snippet, test counts, or error diagnostic

git:                                     # Candidate source code metadata (if task modifies files)
  base: <string>                         # 40-char SHA of commit checkout branched from
  head: <string>                         # 40-char SHA of commit holding produced changes
  branch: <string>                       # Local branch name: e.g. lane/report-contract
  worktree: <string>                     # Absolute path to isolated worktree checkout
  pr: <integer|string|null>              # GitHub PR number or URL if draft PR created; else null

files:                                   # List of files modified, added, or generated
  - <string>                             # Relative or absolute file path

blockers:                                # Active blocking issues requiring manager or CTO intervention
  - id: <string>                         # Unique blocker identifier: e.g. BLK-001
    description: <string>                # Concrete description of the failure or missing decision
    evidence: <string>                   # Reproduction command, error log, or diff reference
    options: [<string>]                  # Actionable choices considered
    recommendation: <string>             # Recommended course of action

requested_action: <string>               # Explicit action requested from manager:
                                         # acknowledge_baseline | review_candidate | integrate_lane |
                                         # unblock_decision | observe_milestone | None

pending_operations:                      # Operations initiated whose side effects remain unconfirmed
  - operation_id: <string>               # e.g. background_build_42
    command: <string>                    # Command that was dispatched
    status: <string>                     # pending | running | untracked
    risk: <string>                       # What happens if interrupted
```

---

## 3. Atomic Publication Pipeline

To prevent the manager or automated observers from reading partially written or corrupted YAML files, all producers must adhere strictly to the **4-step publication pipeline**:

```
[ Step 1: Write .partial ]
       │  Producer generates report via apply_patch to:
       │  <report_root>/<report_id>.partial
       ▼
[ Step 2: Validate Content ]
       │  Producer executes syntax and schema check:
       │  python3 -c "import yaml; yaml.safe_load(open('<report_id>.partial'))"
       │  and calculates SHA-256 digest.
       ▼
[ Step 3: Same-Filesystem Atomic Rename ]
       │  Producer executes POSIX atomic replace:
       │  mv <report_root>/<report_id>.partial <report_root>/<report_id>.yaml
       ▼
[ Step 4: Native Prompt Notice (No-Wait) ]
          Producer alerts manager via Herdr PTY prompt without blocking:
          herdr agent prompt "<MANAGER_PANE_ID>" "<NOTICE_TEXT>"
```

### Publication Rules
1. **Command-Capable AGY Requirement**: Google Antigravity CLI (AGY) workers have full tool execution capabilities (`run_command`, `apply_patch`, git, python). Never use non-atomic file writes, raw string redirection (`>`), or file-only fallbacks that weaken this publication sequence.
2. **Same-Filesystem Invariant**: The `.partial` file must be written in the same directory as the final `.yaml` destination so that `mv` executes a POSIX atomic rename (`rename(2)`), avoiding cross-device copy tearing.
3. **Immutable After Rename**: Once a report is renamed to `.yaml`, it is immutable. A producer must never edit an existing report. If additional progress occurs or corrections are needed, publish a new report with an incremented attempt number or distinct purpose suffix (e.g. `report_contract-a1-checkpoint2`).

---

## 4. Concise Native Notice Contract

Immediately after renaming the report file, the producer notifies the manager using `herdr agent prompt` **without `--wait`**.

### Notice Fields
The notice uses **identical field names** to the report identity to ensure mechanical, unambiguous parsing by the manager:

```text
mission_id: <mission_id>
task_id: <task_id>
attempt: <attempt>
report_id: <report_id>
pane_id: <origin_pane_id>
tab_id: <origin_tab_id>
report_path: <absolute_path_to_yaml>
status: <status>
requested_action: <requested_action>
```

### Standard Single-Line Format
For maximum terminal compatibility and conciseness across agent runtimes, format the notification as a single structured line:

```text
REPORT NOTICE: mission_id=herdr-codex-first-20260920 task_id=report_contract attempt=1 report_id=report_contract-a1-handback pane_id=w3H:pA tab_id=w3H:t8 report_path=/Users/mac/docs/superpowers/runs/herdr-codex-first-20260920/report_contract-a1-handback.yaml status=completed requested_action=review_candidate
```

### Why `--wait` Is Prohibited in Worker Notices
- Invoking `herdr agent prompt <TARGET> "<TEXT>" --wait` causes the worker's tool call to block until the manager settles into `idle`, `done`, or `blocked`.
- If the manager is actively orchestrating other lanes or running long tasks, the worker remains frozen.
- Worse, if the manager prompts the worker back while the worker is waiting, a **callback deadlock** occurs.
- Therefore, all worker notices **must omit `--wait`**. Herdr injects the notice directly into the manager's PTY with bracketed paste and Enter.

---

## 5. Manager Consumption Semantics

When the Engineering Manager receives a report notification (or discovers a report during state reconciliation), it applies the following consumption semantics:

```
                        [ Notice Received / Discovered ]
                                       │
                                       ▼
                         [ Read & Calculate SHA-256 ]
                                       │
                        Does report_id already exist?
                                ├─── No ───► [ Record Digest in state.yaml ]
                                │                        │
                               Yes                       ▼
                                │              Is attempt >= current?
                                ▼                        ├─── Yes ──► [ Consume & Advance Task ]
                     Does digest match existing?         │
                        ├─── Yes ──► [ Idempotent No-Op ] No
                        │                                │
                        No                               ▼
                        │                      [ Log Obsolete Attempt; Ignore ]
                        ▼
             [ REJECT MUTATED REPORT ]
```

### 1. Idempotent Digest Consumption
- The manager calculates the SHA-256 digest of the target report file.
- If the `report_id` has already been recorded in `state.yaml` with the identical SHA-256 digest, the notice is treated as an **idempotent duplicate**. The manager acknowledges receipt without re-executing task graph transitions.

### 2. Mutated Same-ID Rejection
- If an incoming report matches an existing `report_id` in `state.yaml` but has a **different SHA-256 digest**, the manager flags a critical protocol violation: `MUTATED_REPORT_REJECTED`.
- The modified file is rejected, and the manager alerts the producer to republish under a fresh `attempt` or `report_id`.

### 3. Obsolete-Attempt Pruning
- If a report arrives for an attempt lower than the currently recorded attempt (`attempt < current_task_attempt`), it is logged as historical evidence but **cannot advance or revert the task state**.

### 4. Report Receipt vs. Approval
- **Receipt is NOT Approval**: Acknowledging receipt of a producer report only confirms that evidence has been captured.
- **Approval Gate**: Advancing a task to `approved`, `ready_for_review`, or `integrated` requires independent technical verification (e.g. fresh AGY review, check execution, or CTO candidate sign-off).

---

## 6. Checkpoint Cadence & Timeouts

### Meaningful Transition Checkpoints
Producers and managers must publish checkpoints at meaningful state boundaries:
1. **Registration**: Discovery of actual pane/tab coordinates and runtime confirmation.
2. **Baseline Reconciliation**: Verification of remote base SHA, worktree provisioning, and tool check.
3. **Blocker Encountered**: Unresolvable dependency mismatch, tool failure, or architectural seam.
4. **Handback Candidate**: Feature implementation complete, tests passing, ready for review.
5. **Integration Milestone**: PR created, reviewed, or candidate branch reconciled.

### The 10-Minute Silent Boundary Rule
- Multi-agent operations must never rely on fictional cron schedulers, hidden background daemons, or unverified background wake promises.
- If an agent operates silently without an external notification or state transition for **ten minutes**, the agent must generate a checkpoint report at its **next safe tool boundary**.
- The checkpoint records current progress, active processes, and any pending operations with unknown effects, ensuring that if context compaction or interruption occurs, the mission can resume deterministically.

---

## 7. Reviewer Q/A Protocol & Return Coordinates

When an independent AGY reviewer or manager requires clarification on a candidate, communication must be structured to prevent informal, untracked chatter:

### Reviewer Question Schema
Every question submitted to a peer or manager must include:

```text
QUESTION NOTICE:
question_id: <task_id>-q<seq>
target_pane: <target_pane_id>
target_tab: <target_tab_id>
reply_pane: <origin_pane_id>
reply_tab: <origin_tab_id>
finding_evidence: <file_path_and_line_or_command_output>
options:
  1. <option_1>
  2. <option_2>
recommendation: <recommended_option>
```

### Manager Visibility Invariant
- Peer-to-peer inquiries must remain visible to the Engineering Manager.
- If the target agent's runtime does not support direct interactive prompt reception, the question is routed directly to the manager (`w3H:p8`), who logs the question in `state.yaml` and relays it to the appropriate worker.

---

## 8. Complete Concrete Example

### Valid Producer YAML Report (`report_contract-a1-handback.yaml`)

```yaml
schema_version: 1
mission_id: herdr-codex-first-20260920
task_id: report_contract
attempt: 1
report_id: report_contract-a1-handback
event_id: report_contract.handback.1
producer:
  runtime: agy
  model: gemini-3.8-flash-high
  pane_id: w3H:pA
  tab_id: w3H:t8
  terminal_id: term_65beaae4006d89a
  session_id: ccc084c9-608c-43da-9a12-660f17d888fd
  skill_revision: ce4dc7325241f8a3269047934c31131274019c7c
manager:
  pane_id: w3H:p8
  tab_id: w3H:t6
cto:
  pane_id: w3H:p3
  tab_id: w3H:t3
status: completed
summary: >-
  Implemented the single canonical report contract reference at skills/herdr/references/report-contract.md.
  Defines the two durable artifact kinds, atomic publication pipeline, concise notice format,
  idempotent manager consumption rules, reviewer Q/A protocol, and return coordinates.
evidence:
  - command: git diff --check
    exit_code: 0
    result: "Clean git diff check; no trailing whitespaces or syntax issues."
  - command: python3 -c "import yaml; yaml.safe_load(open('skills/herdr/references/report-contract.md'))"
    exit_code: 0
    result: "Embedded YAML schemas and examples verified valid."
git:
  base: ce4dc7325241f8a3269047934c31131274019c7c
  head: 8f9b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b
  branch: lane/report-contract
  worktree: /Users/mac/docs/superpowers/worktrees/herdr-codex-first-20260920/report-contract
  pr: null
files:
  - skills/herdr/references/report-contract.md
blockers: []
requested_action: review_candidate
pending_operations: []
```

### Matching Native Notice Prompt
The producer executes this shell command to notify the manager:

```bash
herdr agent prompt w3H:p8 'REPORT NOTICE: mission_id=herdr-codex-first-20260920 task_id=report_contract attempt=1 report_id=report_contract-a1-handback pane_id=w3H:pA tab_id=w3H:t8 report_path=/Users/mac/docs/superpowers/runs/herdr-codex-first-20260920/report_contract-a1-handback.yaml status=completed requested_action=review_candidate'
```

Notice that **every identity field matches identically** between the YAML report and the native notice string.
