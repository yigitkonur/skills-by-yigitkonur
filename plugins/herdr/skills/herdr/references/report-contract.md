# Canonical Report Contract & Durable Mission Artifacts

This is the **single canonical source of truth** for durable artifact kinds, producer report schema, atomic publication pipeline, native notice format, manager consumption semantics, and reviewer Q/A protocol. Other references route here rather than duplicating schemas.

## 1. Exactly Two Durable Artifact Kinds

```
+------------------------------------------------------------------------------------+
| KIND 1: MUTABLE MANAGER CHECKPOINT (state.yaml alone)                              |
| Location: Absolute run root outside disposable worktrees (<REPORT_ROOT>).          |
| Owner: Engineering Manager (EM) alone. Updated in place on state transitions. |
+------------------------------------------------------------------------------------+
| KIND 2: IMMUTABLE YAML REPORTS (<task>-a<attempt>-<purpose>.yaml)                  |
| Location: Absolute run root. Never modified or overwritten once published.          |
| Owners: Producer agents (implementer, reviewer, integrator) & Manager milestones.  |
+------------------------------------------------------------------------------------+
```

**Never** write mission reports inside Git worktrees.

## 2. When to Use an Immutable Report vs. a Native Message

- **Native message only** (cheap communication, no immutable report): Routine progress updates, quick coordination check-ins, and plain technical questions. A plain question sent to the manager or a peer needs only a Question ID, concise context, and the sender's return route; options and recommendations are reserved for actual decisions or escalations.
- **Immutable report required** (durable evidence): Handback of a completed work product, technical review decisions, material blockers requiring management authorization, or risky recovery and authority changes.

## 3. Canonical Producer Report Schema

```yaml
schema_version: 1
mission_id: <string>
task_id: <string>
attempt: <integer>
report_id: <string>      # Unique canonical ID: <task_id>-a<attempt>-<purpose>

producer:
  runtime: <string>      # agy | codex | claude
  model: <string>        # e.g. <MODEL_IDENTIFIER>
  role: <string>         # implementer | reviewer | integrator | recovery_executor | manager
  pane_id: <string>      # e.g. <PRODUCER_PANE_ID>
  tab_id: <string>       # e.g. <PRODUCER_TAB_ID>
  terminal_id: <string>  # e.g. <PRODUCER_TERM_ID>
  session_id: <string|null>
  skill_path: <string>   # Absolute path to loaded skill
  skill_revision: <string>

manager:
  pane_id: <string>      # e.g. <MANAGER_PANE_ID>
  tab_id: <string>       # e.g. <MANAGER_TAB_ID>

cto:
  pane_id: <string|null> # null when CTO operates outside Herdr (Root PTY)
  tab_id: <string|null>

status: <string>         # in_progress | completed | blocked | failed | milestone | registered
summary: <string>

evidence:
  - command: <string>
    exit_code: <integer>
    result: <string>

git:
  base: <string>
  head: <string>
  branch: <string>
  worktree: <string>
  pr: <integer|string|null>

files:
  - <path>

unresolved_effects: []
requested_action: <string>
```

### Portable Illustrative Example (Synthetic Placeholders)

*Note: This example illustrates schema structure only. It uses synthetic placeholders and makes no claim that any command was executed or that any candidate passed. JSON-formatted YAML is an explicit authoring choice (a valid YAML 1.2 subset); it does not imply that standard `json.load` parses arbitrary YAML.*

```yaml
{
  "schema_version": 1,
  "mission_id": "example-mission-2026",
  "task_id": "feature_module",
  "attempt": 1,
  "report_id": "feature_module-a1-handback",
  "producer": {
    "runtime": "agy",
    "model": "model-id-placeholder",
    "role": "implementer",
    "pane_id": "<PRODUCER_PANE_ID>",
    "tab_id": "<PRODUCER_TAB_ID>",
    "terminal_id": "<PRODUCER_TERM_ID>",
    "session_id": null,
    "skill_path": "/path/to/repo/skills/herdr/SKILL.md",
    "skill_revision": "<CANDIDATE_SKILL_REVISION>"
  },
  "manager": { "pane_id": "<MANAGER_PANE_ID>", "tab_id": "<MANAGER_TAB_ID>" },
  "cto": { "pane_id": null, "tab_id": null },
  "status": "completed",
  "summary": "Illustrative handback summary demonstrating required schema fields.",
  "evidence": [
    { "command": "<VERIFICATION_COMMAND>", "exit_code": 0, "result": "<COMMAND_OUTPUT_PLACEHOLDER>" }
  ],
  "git": {
    "base": "<BASE_COMMIT_SHA>",
    "head": "<CANDIDATE_COMMIT_SHA>",
    "branch": "lane/feature-module",
    "worktree": "/path/to/worktree",
    "pr": null
  },
  "files": ["path/to/file.ext"],
  "unresolved_effects": [],
  "requested_action": "review"
}
```

## 4. Atomic Publication Pipeline (No-Clobber & Verified)

To prevent observers from reading partially written or clobbered YAML, all producers adhere strictly to the 4-step publication pipeline:

```
[ Step 1: Write .partial ]
       │  Producer authors report via apply_patch to:
       │  <REPORT_ROOT>/<report_id>.partial
       ▼
[ Step 2: Validate Content, Shape, & Compute SHA-256 ]
       │  2a. Syntax validation:
       │    • PyYAML available: python3 -c "import yaml; yaml.safe_load(open('<REPORT_ROOT>/<report_id>.partial'))"
       │    • No PyYAML: Author as JSON-formatted YAML (valid YAML 1.2 subset),
       │      then validate with: python3 -c "import json; json.load(open('<REPORT_ROOT>/<report_id>.partial'))"
       │  2b. Shape validation — verify required top-level keys and mappings exist and are not swallowed scalars:
       │      Required keys: schema_version, mission_id, task_id, attempt, report_id, producer, status.
       │      Required mappings: producer, manager, cto.
       │  2c. Compute SHA-256 digest of the .partial file:
       │      EXPECTED_DIGEST=$(shasum -a 256 <REPORT_ROOT>/<report_id>.partial | awk '{print $1}')
       ▼
[ Step 3: Collision Pre-Flight, Atomic Rename, & Verified Publication ]
       │  Verify destination does NOT exist:
       │  test ! -e <REPORT_ROOT>/<report_id>.yaml || { echo 'Destination exists!'; exit 1; }
       │  POSIX atomic no-clobber rename:
       │  mv -n <REPORT_ROOT>/<report_id>.partial <REPORT_ROOT>/<report_id>.yaml
       │  Verify all three post-rename conditions (any failure aborts notice):
       │    1. Source removed:  test ! -e <REPORT_ROOT>/<report_id>.partial
       │    2. Destination exists: test -f <REPORT_ROOT>/<report_id>.yaml
       │    3. Destination matches expected digest from Step 2c:
       │       shasum -a 256 <REPORT_ROOT>/<report_id>.yaml  (compare to EXPECTED_DIGEST)
       │  If .partial still exists after mv -n exits 0, a TOCTOU race occurred: abort notice.
       ▼
[ Step 4: Native Prompt Notice (No-Wait) ]
          herdr agent prompt "<MANAGER_PANE_ID>" "<NOTICE_TEXT>"
```

### Publication Rules
1. **No-Overwrite Invariant**: A published report is immutable. The pre-flight check in Step 3 ensures existing reports are never overwritten.
2. **No Producer Attempt Increments**: The EM alone increments `attempt`. Producer corrections within an assigned attempt generate a new unique `report_id` with a descriptive suffix (e.g. `<task_id>-a1-correction.yaml`), leaving prior reports untouched.

## 5. Concise Native Notice Format

Single-line format using discovered coordinates:
```text
REPORT NOTICE: mission_id=<MISSION_ID> task_id=<TASK_ID> attempt=<ATTEMPT> report_id=<REPORT_ID> pane_id=<ORIGIN_PANE_ID> tab_id=<ORIGIN_TAB_ID> report_path=<REPORT_PATH> status=<STATUS> requested_action=<REQUESTED_ACTION>
```

Workers **never** pass `--wait`. Passing `--wait` blocks the worker process and risks callback deadlocks.

## 6. Manager Consumption Semantics

When a report notice is received or discovered during state reconciliation:

1. **Identity Gate (before advancing graph)**: Verify `mission_id`, `task_id`, and `producer` fields (`pane_id`, `tab_id`, `terminal_id`, `role`, `runtime`) match the registered assignment in `state.yaml`. Unregistered, ambiguous, or mismatched reports are quarantined; explicit re-registration is required before evaluating evidence. The manager advances graph state only after identity validation succeeds.
2. **Attempt Gate**: `attempt == current` → process. `attempt > current` → quarantine future attempt. `attempt < current` → reject obsolete attempt (log for historical audit; no graph advance).
3. **Idempotent Digest Check**: Compute SHA-256 of report file. If `report_id` was already recorded in `state.yaml` with an identical digest, consume as an **idempotent duplicate**: acknowledge receipt with no new task graph transitions, no second dispatch, and no Git or ACK chain effects. If `report_id` exists with a different digest, flag `MUTATED_REPORT_REJECTED` and quarantine.
4. **Pending-Effect Reconciliation**: Before dispatching dependent work, confirm prior tasks' `unresolved_effects` are resolved or explicitly accepted.
5. **Receipt is NOT Approval**: Acknowledging receipt only records evidence in `state.yaml`. Advancing a task to `approved` or `integrated` requires independent technical verification (fresh review, check execution, or CTO sign-off).

## 7. Reviewer Communication & Q/A Protocol

- **Ordinary Questions**: Routine technical clarifications between reviewer and author/EM use short native prompt messages without `--wait` (e.g., `QUESTION [id=<Q_ID>]: <context> -> <question>; return_route=<PANE_ID>`). They do not require an immutable YAML report.
- **Material Blockers & Formal Escalations**: If clarification reveals an architectural conflict, scope ambiguity, or unresolvable technical contradiction requiring manager decision, publish a structured blocker report (`status: blocked`, `requested_action: unblock_decision`) containing structured blocker/options items.
