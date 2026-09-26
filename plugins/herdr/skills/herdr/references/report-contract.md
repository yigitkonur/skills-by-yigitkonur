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
  - Routine progress check-ins, plain technical questions, or lightweight task handbacks.
  - Questions require only: Question ID, concise context, and sender's return route.
- **Immutable YAML report required** (Mode 3 Managed Missions):
  - Handback of completed work deliverables.
  - Formal technical review verdicts and hardening decisions.
  - Material blockers requiring managerial decisions.
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
  base: <string>             # 40-character base commit SHA
  head: <string>             # 40-character candidate commit SHA
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

To ensure no observer reads partially written or clobbered reports, producers strictly follow this 4-step pipeline:

```
[ Step 1: Write .partial ]
       │  Author report via editor/tool to:
       │  <RUN_ROOT>/<report_id>.partial
       ▼
[ Step 2: Validate Syntax, Shape, & Digest ]
       │  2a. Syntax Validation:
       │      • PyYAML available: python3 -c "import yaml; yaml.safe_load(open('<PATH>'))"
       │      • JSON-formatted YAML: python3 -c "import json; json.load(open('<PATH>'))"
       │  2b. Shape Validation:
       │      Required keys: schema_version, mission_id, task_id, attempt, report_id, producer, status.
       │      Required mappings: producer, manager, cto.
       │  2c. Compute SHA-256 Digest:
       │      EXPECTED_DIGEST=$(shasum -a 256 <PATH> | awk '{print $1}')
       ▼
[ Step 3: Collision Pre-Flight & Atomic Rename ]
       │  Verify destination does NOT exist:
       │  test ! -e <RUN_ROOT>/<report_id>.yaml || { echo 'Destination exists!'; exit 1; }
       │  POSIX atomic rename:
       │  mv -n <RUN_ROOT>/<report_id>.partial <RUN_ROOT>/<report_id>.yaml
       │  Verify all three post-rename conditions (abort notice on any failure):
       │    1. Source removed: test ! -e <RUN_ROOT>/<report_id>.partial
       │    2. Destination exists: test -f <RUN_ROOT>/<report_id>.yaml
       │    3. Destination matches expected digest from Step 2c:
       │       shasum -a 256 <RUN_ROOT>/<report_id>.yaml (matches EXPECTED_DIGEST)
       │  If .partial still exists after mv -n exits 0, a TOCTOU race occurred: abort notice!
       ▼
[ Step 4: Native Prompt Notice (No-Wait) ]
          herdr agent prompt "<MANAGER_PANE_ID>" "<NOTICE_TEXT>"
```

### Publication Rules:
1. **No Overwrites**: Once published, a report is permanently immutable.
2. **No Producer Attempt Increments**: The manager/supervisor alone increments `attempt`. Producer corrections within an assigned attempt produce a new unique file with a descriptive suffix (e.g. `<task_id>-a1-correction.yaml`), leaving prior reports untouched.

---

## 6. Concise Native Notice Format

Single-line notice format:
```text
REPORT NOTICE: mission_id=<MISSION_ID> task_id=<TASK_ID> attempt=<ATTEMPT> report_id=<REPORT_ID> pane_id=<ORIGIN_PANE_ID> tab_id=<ORIGIN_TAB_ID> report_path=<REPORT_PATH> status=<STATUS> requested_action=<REQUESTED_ACTION>
```

Producers **NEVER pass `--wait`** on notices.

---

## 7. Manager Consumption Semantics & Pending-Effects Reconciliation

When a report notice is received or discovered during state reconciliation:

1. **Identity Gate (before advancing graph)**:
   Verify `mission_id`, `task_id`, and `producer` fields (`pane_id`, `tab_id`, `terminal_id`, `role`, `runtime`) match the registered assignment in `state.yaml`. Unregistered, ambiguous, or mismatched reports are quarantined; explicit re-registration is required before evaluating evidence.
2. **Attempt Gate**:
   - `attempt == current`: process report.
   - `attempt > current`: quarantine future attempt.
   - `attempt < current`: reject obsolete attempt (log for historical audit; no graph advance).
3. **Idempotent Digest Check**:
   Compute SHA-256 of the report file.
   - If `report_id` was already recorded in `state.yaml` with an identical digest, consume as an **idempotent duplicate**: acknowledge receipt with no new task graph transitions, no second dispatch, and no Git or ACK chain effects.
   - If `report_id` exists with a different digest, flag `MUTATED_REPORT_REJECTED` and quarantine.
4. **Pending-Effect Reconciliation Gate**:
   Before dispatching dependent work or advancing a milestone, confirm that all prior tasks' `unresolved_effects` are either resolved or explicitly accepted and tracked in `state.yaml`. Never advance the graph over un-reconciled side effects.
5. **Receipt is NOT Approval**:
   Acknowledging receipt only records evidence in `state.yaml`. Advancing a task to `approved` or `integrated` requires independent technical verification (fresh review, check execution, or authorized sign-off).
