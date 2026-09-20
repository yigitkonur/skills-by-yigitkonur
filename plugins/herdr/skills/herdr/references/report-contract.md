# Canonical Report Contract & Durable Mission Artifacts

Read this reference to understand the durable artifact contract, publication mechanics, consumption semantics, and native notification protocol for Herdr orchestration missions.

This document is the **single canonical source of truth** across all mission participants for:
1. Upfront role-first triage and authority boundaries (CTO, EM, implementer, reviewer, integrator, recovery executor).
2. Exactly two durable artifact kinds (mutable manager checkpoint `state.yaml`, immutable reports).
3. Canonical producer report schema (explicit `role`, runtime, verified terminal, optional session, mounted skill path/revision).
4. Atomic publication pipeline (write `.partial` → validate content → pre-flight collision check → atomic rename → native prompt notice).
5. Concise native notice format with strict 1:1 field parity.
6. Manager consumption semantics (registered identity matching, exact attempt matching, future attempt quarantine, obsolete attempt pruning, idempotent digest checks, mutation rejection, receipt vs. approval).
7. Reviewer Q/A protocol and explicit return coordinates using portable placeholders.

Other references (`event-monitoring.md`, `mission-briefs.md`, `parallel-capacity.md`, `stopped-agent-recovery.md`) route to this contract rather than duplicating its schemas.

---

## 1. Role-First Triage Matrix: Runtime Is Not Role

The same `SKILL.md` and reference graph are consumed by all participants. **Execution runtime (`agy`, `codex`, `claude`) is NOT role authority.**

Before executing any instructions, cold readers must locate their assigned role in the matrix below to determine their exact operational boundaries, required sections, and forbidden duties:

| Role | Runtime Host | Primary Authority | Permitted Sections | Strictly Out of Scope |
|---|---|---|---|---|
| **CTO** | Codex / Root PTY | Mission strategy, architectural boundaries, final candidate gate authority, CLI control of explicit targets, bounded native observation. | Sections 2, 6.5 (Receipt vs Approval Gate). | Daily task dispatch, worktree editing. |
| **Engineering Manager (EM)** | Codex | Global task graph dispatch, checkpointing, report intake, milestone publication, reviewer Q/A relay. | Sections 2, 3 (Schema), 4 (Publication), 5 (Notice Intake), 6 (Consumption Semantics). | Direct production code editing, unassigned task execution. |
| **Implementer** | AGY | Feature implementation, tests, local commits, report handback in assigned worktree. | Sections 2, 3 (Schema), 4 (Publication), 5 (Notice), 7, 8. | Modifying `state.yaml`, consuming peer reports, managing other workers. |
| **Fresh Reviewer** | AGY | Clean-context evaluation of spec, code, tests, and diffs on assigned branch/head. | Sections 2, 3 (Schema), 4 (Publication), 5 (Notice), 8 (Q/A). | Editing implementation files, approving own work, managing task graph. |
| **Integration Executor** | AGY | Serial Git/GitHub gating, draft PR lifecycle, packaging generation, cleanup. | Sections 2, 3 (Schema), 4 (Publication), 5 (Notice). | Parallel drafting, direct push to main without gate approval. |
| **Recovery Executor** | AGY | Bounded diagnostic probes, process reconciliation, orphaned resource audit. | Sections 2, 3 (Schema), 4 (Publication), 5 (Notice), 7. | Re-launching live TUIs, executing production tasks without brief. |

> [!IMPORTANT]
> **No Management Hierarchy Bootstrapping**: Assigned AGY executors and reviewers must **never** initialize a secondary manager, create sub-managers, or modify `state.yaml`. All coordination flows through the designated Engineering Manager.

> [!NOTE]
> **Non-Pane CTO Boundary**: When operating from a Root PTY outside Herdr, the CTO retains full CLI control over explicit known pane targets (`herdr agent read`, `herdr agent prompt`, etc.) and performs manual observation of shared run root artifacts. Because a non-pane CTO lacks a native Herdr callback pane, reports truthfully record `cto.pane_id: null` and `cto.tab_id: null`. Workers never fabricate CTO callback coordinates; all worker notices route to the Engineering Manager.

---

## 2. Architectural Core: Exactly Two Durable Artifact Kinds

To eliminate split-brain state, race conditions, and unstructured log scraping, Herdr orchestration missions use **exactly two durable artifact kinds**:

```
+---------------------------------------------------------------------------------------+
| DURABLE MISSION ARTIFACT TOPOLOGY                                                     |
+---------------------------------------------------------------------------------------+
| KIND 1: MUTABLE MANAGER CHECKPOINT (state.yaml alone)                                 |
| - Location: Absolute mission run root outside disposable worktrees (<REPORT_ROOT>).   |
| - Owner: Codex Engineering Manager (EM) alone.                                        |
| - Invariant: Sole mutable checkpoint file. Updated in place on task state transitions.|
| - Contents: Global task graph, active assignments, registered identities, consumed    |
|   report IDs and SHA-256 digests, decisions log, action log, recovery instructions.   |
+---------------------------------------------------------------------------------------+
| KIND 2: IMMUTABLE YAML REPORTS (<task>-a<attempt>-<purpose>.yaml & manager-m<N>.yaml) |
| - Location: Absolute mission run root outside disposable worktrees (<REPORT_ROOT>).   |
| - Owners: Producer agents (implementer, reviewer, integrator) & Manager milestone logs.|
| - Invariant: Strictly immutable once published. Never modified or overwritten in place|
| - Contents: Strict YAML contract declaring task/attempt identity, assigned role,      |
|   truthful status, evidence commands/results/exits, Git base/head, blockers,          |
|   requested action, pending operations with unknown effects.                          |
+---------------------------------------------------------------------------------------+
```

### Run Root Invariant
Both artifact kinds reside in a single shared, absolute directory on the host filesystem (`<REPORT_ROOT>`, e.g., `<RUNS_DIR>/<mission_id>`).
- **Never write mission reports inside Git worktrees**: Worktrees are disposable ephemeral checkouts that may be reset, switched, or pruned upon task completion.
- **Never communicate mission state via untyped raw terminal chat**: State changes must be anchored to an immutable YAML report.
- **Manager Milestones are Kind 2**: Reports published by the manager (such as `manager-m1-bootstrap.yaml`) are immutable Kind 2 reports documenting checkpoints for the CTO; `state.yaml` alone is mutable.

---

## 3. Canonical Producer Report Schema

Every producer report must conform to this complete YAML schema:

```yaml
schema_version: 1                        # Integer contract version (currently 1)
mission_id: <string>                     # Unique mission identifier (e.g. herdr-codex-first-20260920)
task_id: <string>                        # Task identifier from manager task graph (e.g. report_contract)
attempt: <integer>                       # 1-indexed attempt counter assigned by EM (e.g. 1)
report_id: <string>                      # Unique canonical ID: <task_id>-a<attempt>-<purpose>
event_id: <string>                       # Optional fine-grained event tracker: <task_id>.<purpose>.<seq>

producer:
  runtime: <string>                      # Runtime binary: agy | codex | claude
  model: <string>                        # Specific model identifier: gemini-3.8-flash-high | gpt-6-astra
  role: <string>                         # Assigned role: implementer | reviewer | integrator | recovery_executor | manager
  pane_id: <string>                      # Herdr pane identifier: e.g. <PRODUCER_PANE_ID>
  tab_id: <string>                       # Herdr tab identifier: e.g. <PRODUCER_TAB_ID>
  terminal_id: <string>                  # Underlying PTY terminal ID: e.g. <PRODUCER_TERM_ID>
  session_id: <string|null>              # Agent session UUID; if unexposed/unavailable, record null or "unavailable"
  skill_path: <string>                   # Absolute path to mounted skill: e.g. /path/to/skills/herdr/SKILL.md
  skill_revision: <string>               # Git commit SHA or version of loaded skill

manager:
  pane_id: <string>                      # Manager return pane: e.g. <MANAGER_PANE_ID>
  tab_id: <string>                       # Manager return tab: e.g. <MANAGER_TAB_ID>

cto:
  pane_id: <string|null>                 # Root CTO return pane; null if CTO operates outside Herdr (Root PTY) without callback pane
  tab_id: <string|null>                  # Root CTO return tab; null if CTO has no Herdr tab

status: <string>                         # Enum: in_progress | completed | blocked | failed | milestone | registered
summary: <string>                        # Concise, truthful executive summary of progress or findings

evidence:                                # Structured log of every verification check executed
  - command: <string>                    # Exact shell command executed (e.g. git diff --check, pytest)
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

## 4. Atomic Publication Pipeline (No-Clobber & Verified)

To prevent the manager or automated observers from reading partially written, corrupted, or clobbered YAML files, all producers must adhere strictly to the **4-step publication pipeline**:

```
[ Step 1: Write .partial ]
       │  Producer generates report via apply_patch to:
       │  <REPORT_ROOT>/<report_id>.partial
       ▼
[ Step 2: Validate Content, Shape, & Compute SHA-256 ]
       │  2a. Syntax validation — choose the path matching your environment:
       │    • PyYAML available: python3 -c "import yaml; yaml.safe_load(open('<REPORT_ROOT>/<report_id>.partial'))"
       │    • No PyYAML: Author reports as JSON-formatted YAML (a valid YAML 1.2 subset),
       │      then validate with: python3 -c "import json; json.load(open('<REPORT_ROOT>/<report_id>.partial'))"
       │  2b. Shape validation — verify required top-level keys exist and nested values
       │      are mappings (not strings that swallowed their sub-keys due to indentation):
       │      Required keys: schema_version, mission_id, task_id, attempt, report_id, producer, status.
       │      Required mappings: producer, manager, cto (each must be a dict, not a scalar).
       │      See stopped-agent-recovery.md for checkpoint shape recovery after indentation defects.
       │  2c. Compute SHA-256 digest of the .partial file for post-publication verification.
       ▼
[ Step 3: Collision Pre-Flight, Atomic Rename, & Verified Publication ]
       │  Producer verifies destination does NOT exist:
       │  test ! -e <REPORT_ROOT>/<report_id>.yaml || { echo 'Destination exists!'; exit 1; }
       │  Then POSIX atomic replace without clobber:
       │  mv -n <REPORT_ROOT>/<report_id>.partial <REPORT_ROOT>/<report_id>.yaml
       │  Verify all three post-rename conditions (any failure aborts notice):
       │    1. Source removed:  test ! -e <REPORT_ROOT>/<report_id>.partial
       │    2. Destination exists: test -f <REPORT_ROOT>/<report_id>.yaml
       │    3. Destination matches expected digest from Step 2c:
       │       shasum -a 256 <REPORT_ROOT>/<report_id>.yaml  (compare to Step 2c value)
       │  If .partial still exists after mv -n exits 0, a TOCTOU race occurred:
       │  another producer published the destination between pre-flight and rename.
       │  Abort the notice; do not report success for bytes that were not published.
       ▼
[ Step 4: Native Prompt Notice (No-Wait) ]
          Producer alerts manager via Herdr PTY prompt without blocking:
          herdr agent prompt "<MANAGER_PANE_ID>" "<NOTICE_TEXT>"
```

### Publication Rules
1. **Command-Capable AGY Requirement**: Google Antigravity CLI (AGY) workers have full tool execution capabilities (`apply_patch`, git, python). Never use non-atomic file writes, raw string redirection (`>`), or file-only fallbacks that weaken this publication sequence.
2. **No-Overwrite Invariant**: A published report is immutable. The pre-flight check in Step 3 ensures that if a destination file `<REPORT_ROOT>/<report_id>.yaml` already exists, publication aborts with an error rather than silently overwriting evidence.
3. **No Producer Attempt Increments**: The Engineering Manager alone owns incrementing `attempt` numbers. If a producer needs to publish corrections, progress updates, or revisions within an assigned attempt, it must generate a **new unique `report_id`** with a descriptive purpose suffix (e.g. `report_contract-a1-revision1.yaml`), leaving prior published reports untouched.
4. **No Undeclared Dependencies**: Validation in Step 2 uses available system tooling only. Two supported paths: (a) When PyYAML is installed, `yaml.safe_load` validates arbitrary YAML reports. (b) When PyYAML is absent, producers **author reports as JSON-formatted YAML** — a valid YAML 1.2 subset that Python's standard-library `json.load` can validate without additional packages. JSON-formatted YAML is an explicit authoring choice, not a claim that `json.load` parses arbitrary YAML. Shape validation (Step 2b: required keys exist, required values are mappings) applies regardless of parser. Do not implement a custom YAML parser or install packages not already present.

---

## 5. Concise Native Notice Contract

Immediately after renaming the report file, the producer notifies the manager using `herdr agent prompt` **without `--wait`**.

### Notice Fields (1:1 Parity)
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
For maximum terminal compatibility across agent runtimes, format the notification as a single structured line using discovered coordinates:

```text
REPORT NOTICE: mission_id=<MISSION_ID> task_id=<TASK_ID> attempt=<ATTEMPT> report_id=<REPORT_ID> pane_id=<ORIGIN_PANE_ID> tab_id=<ORIGIN_TAB_ID> report_path=<REPORT_PATH> status=<STATUS> requested_action=<REQUESTED_ACTION>
```

### Why `--wait` Is Prohibited in Worker Notices
- Invoking `herdr agent prompt <TARGET> "<TEXT>" --wait` causes the worker's tool call to block until the manager settles into `idle`, `done`, or `blocked`.
- If the manager is actively orchestrating other lanes or running long tasks, the worker remains frozen.
- Worse, if the manager prompts the worker back while the worker is waiting, a **callback deadlock** occurs.
- Therefore, all worker notices **must omit `--wait`**. Herdr injects the notice directly into the manager's PTY with bracketed paste and Enter.

---

## 6. Manager Consumption Semantics

When the Engineering Manager receives a report notification (or discovers an unconsumed report during state reconciliation), it executes the following strict consumption sequence:

```
                        [ Notice Received / Discovered ]
                                       │
                                       ▼
                         [ Read & Calculate SHA-256 ]
                                       │
                  Does report match registered assignment?
                (mission_id, task_id, pane_id, tab_id, terminal_id,
                 role, runtime; session_id if registered)
                                ├─── No ───► [ REJECT UNREGISTERED PRODUCER ]
                               Yes
                                │
                                ▼
              Does attempt match current_assigned_attempt?
                                ├─── attempt > current ──► [ QUARANTINE FUTURE ATTEMPT ]
                                ├─── attempt < current ──► [ REJECT OBSOLETE ATTEMPT ]
                                │                          (Record evidence; do not advance)
                     attempt == current
                                │
                                ▼
                        Does report_id already exist?
                                ├─── No ───► [ Record Evidence in state.yaml ]
                               Yes
                                │
                                ▼
                     Does digest match existing?
                        ├─── Yes ──► [ Idempotent Duplicate; No-Op ]
                        No
                        │
                        ▼
             [ REJECT MUTATED REPORT (MUTATED_REPORT_REJECTED) ]
```

### 1. Registered Producer Matching & Provenance Verification
The manager verifies that the incoming report's top-level `mission_id` and `task_id` match the current mission and assigned task, and that the `producer` identity fields match the active registered assignment in `state.yaml`:
- **Required registered matches**: `pane_id`, `tab_id`, `terminal_id`, `role`, `runtime`.
- **Exposed session metadata**: When `session_id` (or session kind/source/value) is exposed by the runtime and recorded during registration, it must match. When unexposed or unavailable, it is recorded honestly as `null` or `"unavailable"`.
- **Identity semantics and limitations**:
  - PTY `terminal_id` may persist across agent process/CLI restarts in the same pane; it is not a guaranteed unique runtime generation identifier.
  - Native `session_id` may be resumed or compacted across restarts; it is not a universal guarantee of per-instance uniqueness.
  - No identity field or combination thereof cryptographically proves author identity; Herdr does not invent a synthetic identity generation service.
- **Manager-owned attempts and ambiguous report quarantine**:
  - Disambiguation and lifecycle governance are strictly owned by the Engineering Manager via `state.yaml` assignment records and explicit attempt progression.
  - If an unexpected report arrives with ambiguous provenance (e.g. after a crash, unannounced restart, or mismatched attempt), the manager **quarantines the report** and requires explicit re-registration before evaluating evidence.
- **Verified native pane move**:
  - When the CTO or EM moves a pane across tabs via `herdr pane move` (e.g. moving a manager pane to a new tab), the `tab_id` updates while `pane_id`, `terminal_id`, and `session_id` remain stable.
  - The manager records legitimate old and new `tab_id` history in `state.yaml` and updates peer return coordinates.
  - Historical published reports retain their original `tab_id` at the time of publication without retroactive modification.
  - Unexplained identity drift (e.g. unregistered tab or pane changes) is rejected.

### 2. Strict Attempt Matching & Future Quarantine
- **Exact Match (`attempt == current`)**: Normal processing path.
- **Future Attempt (`attempt > current`)**: **Quarantined**. An unassigned future attempt cannot advance the task graph without prior manager dispatch.
- **Obsolete Attempt (`attempt < current`)**: **Rejected from advancing state**. Logged as historical audit evidence only.

### 3. Idempotent Digest Consumption
- The manager calculates the SHA-256 digest of the target report file.
- If the `report_id` has already been recorded in `state.yaml` with an **identical SHA-256 digest**, the notice is consumed as an **idempotent duplicate**. The manager acknowledges receipt without re-executing task graph transitions.

### 4. Mutated Same-ID Rejection
- If an incoming report matches an existing `report_id` in `state.yaml` but has a **different SHA-256 digest**, the manager flags a critical protocol violation: `MUTATED_REPORT_REJECTED`.
- The file is rejected, and the manager alerts the producer to publish under a fresh `report_id`.

### 5. Report Receipt vs. Candidate Approval
- **Receipt is NOT Approval**: Acknowledging receipt of a producer report only registers evidence in `state.yaml`.
- **Approval Gate**: Advancing a task to `approved`, `ready_for_review`, or `integrated` requires independent technical verification (fresh AGY review, check execution, or CTO candidate sign-off).

---

## 7. Checkpoint Cadence & Timeouts

### Meaningful Transition Checkpoints
Producers and managers publish checkpoints at meaningful state boundaries:
1. **Registration**: Discovery of actual pane/tab coordinates and runtime confirmation.
2. **Baseline Reconciliation**: Verification of remote base SHA, worktree provisioning, and tool check.
3. **Blocker Encountered**: Unresolvable dependency mismatch, tool failure, or architectural seam.
4. **Handback Candidate**: Feature implementation complete, tests passing, ready for review.
5. **Integration Milestone**: PR created, reviewed, or candidate branch reconciled.

### The 10-Minute Silent Boundary Rule
- Multi-agent operations must never rely on fictional cron schedulers, hidden background daemons, or unverified background wake promises.
- If an agent operates silently without an external notification or state transition for **ten minutes**, the agent must generate a checkpoint report at its **next safe tool boundary**.
- The checkpoint records current progress, active processes, and any pending operations with unknown effects.

---

## 8. Reviewer Q/A Protocol & Return Coordinates

When an independent AGY reviewer or manager requires clarification on a candidate, communication must be structured to prevent informal, untracked chatter:

### Reviewer Question Schema
Every question submitted to a peer or manager must include:

```text
QUESTION NOTICE:
question_id: <task_id>-q<seq>
target_pane: <TARGET_PANE_ID>
target_tab: <TARGET_TAB_ID>
reply_pane: <ORIGIN_PANE_ID>
reply_tab: <ORIGIN_TAB_ID>
finding_evidence: <file_path_and_line_or_command_output>
options:
  1. <option_1>
  2. <option_2>
recommendation: <recommended_option>
```

### Manager Visibility Invariant
- Peer-to-peer inquiries must remain visible to the Engineering Manager.
- If the target agent's runtime does not support direct interactive prompt reception, the question is routed directly to the manager (`<MANAGER_PANE_ID>`), who logs the question in `state.yaml` and relays it to the appropriate worker.

---

## 9. Concrete Portable Example (Synthetic Example Labeled)

*The following is a synthetic example demonstrating valid field relationships, portable placeholders, and executable evidence check commands.*

### Synthetic Producer YAML Report (`<task_id>-a1-handback.yaml`)

```yaml
{
  "schema_version": 1,
  "mission_id": "sample-mission-20260920",
  "task_id": "sample_feature",
  "attempt": 1,
  "report_id": "sample_feature-a1-handback",
  "event_id": "sample_feature.handback.1",
  "producer": {
    "runtime": "agy",
    "model": "gemini-3.8-flash-high",
    "role": "implementer",
    "pane_id": "<PRODUCER_PANE_ID>",
    "tab_id": "<PRODUCER_TAB_ID>",
    "terminal_id": "<PRODUCER_TERM_ID>",
    "session_id": null,
    "skill_path": "/path/to/skills/herdr/SKILL.md",
    "skill_revision": "ce4dc7325241f8a3269047934c31131274019c7c"
  },
  "manager": {
    "pane_id": "<MANAGER_PANE_ID>",
    "tab_id": "<MANAGER_TAB_ID>"
  },
  "cto": {
    "pane_id": "<CTO_PANE_ID>",
    "tab_id": "<CTO_TAB_ID>"
  },
  "status": "completed",
  "summary": "Implemented feature logic in assigned worktree. Verified all unit tests, error telemetry checks, and diff checks pass. Report published following atomic 4-step pipeline.",
  "evidence": [
    {
      "command": "git diff --check",
      "exit_code": 0,
      "result": "Clean diff check; zero whitespace or formatting defects."
    },
    {
      "command": "python3 -c \"import json; data = json.load(open('<REPORT_ROOT>/sample_feature-a1-handback.yaml')); assert data['status'] == 'completed'\"",
      "exit_code": 0,
      "result": "JSON-formatted YAML report validated via stdlib json.load."
    },
    {
      "command": "shasum -a 256 <REPORT_ROOT>/sample_feature-a1-handback.yaml",
      "exit_code": 0,
      "result": "<EXPECTED_DIGEST>  <REPORT_ROOT>/sample_feature-a1-handback.yaml (matches Step 2c digest)"
    }
  ],
  "git": {
    "base": "ce4dc7325241f8a3269047934c31131274019c7c",
    "head": "8f9b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b",
    "branch": "lane/sample-feature",
    "worktree": "<WORKTREE_ROOT>/sample-feature",
    "pr": null
  },
  "files": [
    "src/feature.ts"
  ],
  "blockers": [],
  "requested_action": "review_candidate",
  "pending_operations": []
}
```

### Matching Native Notice Prompt
The producer executes this shell command to notify the manager:

```bash
herdr agent prompt <MANAGER_PANE_ID> 'REPORT NOTICE: mission_id=sample-mission-20260920 task_id=sample_feature attempt=1 report_id=sample_feature-a1-handback pane_id=<PRODUCER_PANE_ID> tab_id=<PRODUCER_TAB_ID> report_path=<REPORT_ROOT>/sample_feature-a1-handback.yaml status=completed requested_action=review_candidate'
```

All identity fields match identically between the YAML report and the native notice string.
