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

To prevent observers from reading partially written or clobbered YAML, all producers adhere strictly to the 4-step publication pipeline:

```
[ Step 1: Write to .partial File ]
  <REPORT_ROOT>/<report_id>.partial
             │
             ▼
[ Step 2: Validate Content, Shape, & Compute SHA-256 ]
  2a. Syntax validation:
    • PyYAML available: python3 -c "import yaml; yaml.safe_load(open('<REPORT_ROOT>/<report_id>.partial'))"
    • No PyYAML: Author as JSON-formatted YAML (valid YAML 1.2 subset),
      then validate with: python3 -c "import json; json.load(open('<REPORT_ROOT>/<report_id>.partial'))"
      (Note: json.load validates JSON-formatted YAML only, not arbitrary YAML).
  2b. Shape validation — verify required top-level keys and mappings exist and are not swallowed scalars:
      Required keys: schema_version, mission_id, task_id, attempt, report_id, producer, status.
      Required mappings: producer, manager, cto.
  2c. Compute SHA-256 digest of the .partial file:
      EXPECTED_DIGEST=$(shasum -a 256 <REPORT_ROOT>/<report_id>.partial | awk '{print $1}')
             │ (Validation passes)
             ▼
[ Step 3: Collision Pre-Flight, Atomic Rename, & Verified Publication ]
  Verify destination does NOT exist:
  test ! -e <REPORT_ROOT>/<report_id>.yaml || { echo 'Destination exists!'; exit 1; }
  Same-filesystem no-clobber rename:
  mv -n <REPORT_ROOT>/<report_id>.partial <REPORT_ROOT>/<report_id>.yaml
  Verify all three post-rename conditions (any failure aborts notice):
    1. Source removed:  test ! -e <REPORT_ROOT>/<report_id>.partial
    2. Destination exists: test -f <REPORT_ROOT>/<report_id>.yaml
    3. Destination matches expected digest from Step 2c:
       shasum -a 256 <REPORT_ROOT>/<report_id>.yaml (compare to EXPECTED_DIGEST)
  If .partial still exists after mv -n exits 0, destination already existed (TOCTOU race): abort notice.
  On error, preserve failed .partial file for diagnostic evidence; do NOT clobber.
             │
             ▼
[ Step 4: Native Prompt Notice (No-Wait) ]
  herdr agent prompt "<MANAGER_PANE_ID>" "<NOTICE_TEXT>"
  (Workers NEVER pass --wait to prevent sender deadlock)
```

### Publication Rules:
1. **No-Overwrite Invariant**: A published report is immutable. The collision pre-flight check in Step 3 ensures existing reports are never overwritten.
2. **No Producer Attempt Increments**: The supervisor/manager alone increments `attempt`. Producer corrections within an assigned attempt generate a new unique `report_id` with a descriptive suffix (e.g. `<task_id>-a1-correction.yaml`), leaving prior reports untouched.

---

## 6. Manager Consumption Semantics & Deduplication

When an Engineering Manager receives a report notice or discovers unconsumed reports during reconciliation:

1. **Identity Gate (Before Advancing Graph)**:
   A report digest alone cannot authenticate a notice. The manager verifies that `mission_id`, `task_id`, and `producer` fields (`pane_id`, `tab_id`, `terminal_id`, `role`, `runtime`, and `session` where registered) match the registered assignment in `state.yaml`. Unregistered, ambiguous, or mismatched reports are quarantined; explicit re-registration is required before evaluating evidence. The manager advances graph state only after identity validation succeeds.
2. **Attempt Gate**:
   - `attempt == current`: Process report.
   - `attempt > current`: Quarantine future attempt.
   - `attempt < current`: Reject obsolete attempt (log for historical audit; no graph advance).
3. **Idempotent Digest Check**:
   Compute `shasum -a 256 <REPORT_PATH>` (portable across macOS/Linux; do not assume `sha256sum` exists everywhere).
   - If `report_id` was already recorded in `state.yaml` with an **identical** digest: treat as an idempotent duplicate notice. Acknowledge receipt with no new task graph transitions, no second dispatch, and no Git or ACK chain effects.
   - If `report_id` was previously recorded with a **different** digest: flag `MUTATED_REPORT_REJECTED`, quarantine the file, and log a defect.
4. **Pending-Effect Reconciliation (`unresolved_effects`)**:
   Before dispatching dependent work, confirm prior tasks' `unresolved_effects` are resolved or explicitly accepted. If a report declares non-empty `unresolved_effects` (e.g. unlinked temp files, dangling background jobs, unmerged git locks), the manager **must NOT advance the dependent graph** until those side effects are explicitly reconciled.
5. **Receipt is NOT Technical Approval**:
   Acknowledging receipt only records evidence in `state.yaml`. Advancing a task to `approved` or `integrated` requires independent technical verification (fresh review, check execution, or supervisor sign-off).
