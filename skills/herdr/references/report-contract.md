# Canonical Report Contract & Durable Mission Artifacts

This is the single canonical source of truth for durable artifact kinds, producer report schema v1, backward-compatible fields, atomic publication pipelines, native notice formats, manager consumption semantics, pending-effects reconciliation, and reviewer Q/A protocols.

---

## 1. Exactly Two Durable Artifact Kinds

```
+------------------------------------------------------------------------------------+
| KIND 1: MUTABLE MANAGER CHECKPOINT (state.yaml)                                    |
| Location: Absolute run root outside disposable worktrees (<RUN_ROOT>).             |
| Owner: Engineering Manager (EM) alone. Updated in place on state transitions.      |
+------------------------------------------------------------------------------------+
| KIND 2: IMMUTABLE YAML REPORTS (<task>-a<attempt>-<purpose>.yaml)                  |
| Location: Absolute run root. Never modified or overwritten once published.         |
| Owners: Producer agents (implementers, reviewers, integrators) & EM milestones.    |
+------------------------------------------------------------------------------------+
```

**Never write mission reports inside Git worktrees**. Worktrees are disposable and may be cleanly removed upon task completion.

---

## 2. Separation of Four States

Distinguish the four explicit states of a communication:

1. **Published**: The report artifact has been written to disk at the run root and its SHA-256 digest has been verified.
2. **Submitted**: A native prompt notice pointing to the report was sent to the recipient's pane via `herdr agent prompt`. CLI exit code $0$ proves transport submission ONLY.
3. **Consumed**: The recipient has discovered, read, and verified the report's identity and checksum from disk.
4. **Acted**: The recipient has executed state transitions, scheduled dependent work, or advanced the task graph based on the report.

---

## 3. When to Use Immutable Reports vs. Native Messages

- **Native message only** (Mode 1 / Mode 2 / routine coordination):
  - **Ordinary Technical Q/A**: Asking a clarifying question about interface shapes, checking if an endpoint is ready, or requesting non-blocking information.
  - Format: Concise question, brief context, and return route.
  - **Mode 2 Task Handbacks**: Summary of changes, commit SHA, and test outputs delivered directly in native text to the supervisor.
- **Immutable YAML report required** (Mode 3 Managed Missions):
  - Handback of completed work deliverables from workers.
  - Formal technical review verdicts and hardening decisions from reviewers.
  - **Formal Material Blockers**: Unresolvable specification collisions, missing external credentials, schema migration failures, or architectural choices requiring managerial decisions.
  - Risky recovery interventions and authority modifications.

---

## 4. Canonical Producer Report Schema (v1 Backward-Compatible)

```yaml
schema_version: 1
mission_id: <string>
task_id: <string>
attempt: <integer>
report_id: <string>          # Canonical format: <task_id>-a<attempt>-<purpose>

producer:
  runtime: <string>          # agy | codex | claude
  model: <string>            # Verified model identifier
  role: <string>             # implementer | reviewer | integrator | manager | recovery_executor
  pane_id: <string>          # e.g. w1:p1
  tab_id: <string>           # e.g. w1:t1
  terminal_id: <string>      # e.g. w1:term1
  session_id: <string|null>  # Conversation / session handle
  skill_path: <string>       # Absolute path to loaded skill
  skill_revision: <string>   # Loaded skill git revision / checksum

manager:
  pane_id: <string|null>     # e.g. w1:p2
  tab_id: <string|null>

cto:
  pane_id: <string|null>     # null when supervisor operates outside Herdr (Root PTY)
  tab_id: <string|null>

status: <string>             # in_progress | completed | blocked | failed | milestone | registered
summary: <string>

evidence:
  - command: <string>
    exit_code: <integer>
    result: <string>

git:
  base: <string>             # Full verified base commit object ID / SHA
  head: <string>             # Full verified candidate commit object ID / SHA
  branch: <string>
  worktree: <string>
  pr: <integer|string|null>

files:
  - <path>

unresolved_effects: []       # Explicit list of un-reconciled side effects
requested_action: <string>   # review | merge | unblock_decision | integrate | none
```

---

## 5. Atomic Publication Pipeline (No-Clobber & Verified)

Producers author reports through a strict 4-step atomic pipeline:

```
[ Step 1: Write to .partial File ]
  <RUN_ROOT>/reports/<REPORT_ID>.yaml.partial
             │
             ▼
[ Step 2: In-Process Validation Gate ]
  • YAML syntax parses cleanly
  • Required top-level keys & mappings present
  • Non-empty evidence & full commit object ID (git rev-parse HEAD)
  • Compute SHA-256 digest
             │ (Validation passes)
             ▼
[ Step 3: Atomic Rename ]
  mv -n <REPORT_ID>.yaml.partial <REPORT_ID>.yaml
             │
             ▼
[ Step 4: No-Wait Notice Delivery ]
  herdr agent prompt "$MGR_PANE" \
    "REPORT: report_id=<ID> path=<PATH> digest=<SHA256> status=completed"
  (Omit --wait to prevent sender deadlock)
```

---

## 6. Manager Consumption Semantics & Deduplication

When an Engineering Manager receives a report notice:
1. **Assignment & Identity Verification**:
   A report digest alone cannot independently authenticate a notice. The manager verifies that `task_id`, `attempt`, and `producer` match the active task assignment.
2. **Read Directly from Disk**:
   Read the target file from `<RUN_ROOT>/reports/<REPORT_ID>.yaml`. Never trust text transmitted through terminal argv alone.
3. **Deduplication Gate**:
   - Compute `sha256sum <PATH>`.
   - If `report_id` was already recorded with an **identical** digest: treat as a duplicate notice and consume idempotently (no-op).
   - If `report_id` was previously recorded with a **different** digest: flag `MUTATED_REPORT_REJECTED`, quarantine the file, and log a defect.
4. **Pending Effects Gate (`unresolved_effects`)**:
   If the report declares non-empty `unresolved_effects` (e.g. unlinked temp files, dangling background jobs, unmerged git locks), the manager **must NOT advance the dependent graph** until those side effects are explicitly reconciled.
5. **Update Checkpoint (`state.yaml`)**:
   Record receipt in `state.yaml` under the task entry. Receipt proves consumption; technical acceptance occurs only when required review gates pass.
