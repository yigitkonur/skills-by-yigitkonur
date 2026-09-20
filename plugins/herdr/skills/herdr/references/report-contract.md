# Canonical Report Contract & Durable Mission Artifacts

This is the **single canonical source of truth** for: durable artifact kinds, producer report schema, atomic publication pipeline, native notice format, manager consumption semantics, and reviewer Q/A protocol. Other references route here rather than duplicating schemas.

## 1. Exactly Two Durable Artifact Kinds

```
+------------------------------------------------------------------------------------+
| KIND 1: MUTABLE MANAGER CHECKPOINT (state.yaml alone)                              |
| Location: Absolute run root outside disposable worktrees (<REPORT_ROOT>).          |
| Owner: Codex Engineering Manager (EM) alone. Updated in place on state transitions. |
+------------------------------------------------------------------------------------+
| KIND 2: IMMUTABLE YAML REPORTS (<task>-a<attempt>-<purpose>.yaml)                  |
| Location: Absolute run root. Never modified or overwritten once published.          |
| Owners: Producer agents (implementer, reviewer, integrator) & Manager milestones.  |
+------------------------------------------------------------------------------------+
```

**Never** write mission reports inside Git worktrees. **Never** communicate mission state via untyped terminal chat.

## 2. When to Use an Immutable Report vs. a Native Message

- **Native message only** (no immutable report): Operational progress, routine check-ins, simple questions that carry no evidence, plain status that needs no durable record.
- **Immutable report required**: Handback of a work product, technical review decision, material blocker requiring a management decision, risky recovery result.

## 3. Canonical Producer Report Schema

```yaml
schema_version: 1
mission_id: <string>
task_id: <string>
attempt: <integer>
report_id: <string>      # Unique canonical ID: <task_id>-a<attempt>-<purpose>

producer:
  runtime: <string>      # agy | codex | claude
  model: <string>        # e.g. gemini-3.8-flash-high
  role: <string>         # implementer | reviewer | integrator | recovery_executor | manager
  pane_id: <string>
  tab_id: <string>
  terminal_id: <string>
  session_id: <string|null>
  skill_path: <string>
  skill_revision: <string>

manager:
  pane_id: <string>
  tab_id: <string>

cto:
  pane_id: <string|null>
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

### Illustrative Example (JSON-formatted YAML subset)

```yaml
{
  "schema_version": 1,
  "mission_id": "herdr-codex-first-20260920",
  "task_id": "simplification_writer",
  "attempt": 1,
  "report_id": "simplification_writer-a1-handback",
  "producer": {
    "runtime": "agy",
    "model": "gemini-3.1-pro-high",
    "role": "implementer",
    "pane_id": "<PRODUCER_PANE_ID>",
    "tab_id": "<PRODUCER_TAB_ID>",
    "terminal_id": "<PRODUCER_TERM_ID>",
    "session_id": null,
    "skill_path": "/Users/mac/docs/superpowers/worktrees/herdr-codex-first-20260920/integration/skills/herdr/SKILL.md",
    "skill_revision": "44bda65727e221b75c391330a59ce22bac48c9a1"
  },
  "manager": { "pane_id": "<MANAGER_PANE_ID>", "tab_id": "<MANAGER_TAB_ID>" },
  "cto": { "pane_id": null, "tab_id": null },
  "status": "completed",
  "summary": "Rewrote skills/herdr/SKILL.md and references. All checks pass.",
  "evidence": [
    { "command": "python3 scripts/validate-skills.py", "exit_code": 0, "result": "Validated 56 skills -- All validations passed" },
    { "command": "python3 scripts/gen-marketplace.py --check", "exit_code": 0, "result": "plugin metadata is up to date" },
    { "command": "git diff --check ce4dc732..HEAD", "exit_code": 0, "result": "" },
    { "command": "git rev-parse HEAD", "exit_code": 0, "result": "44bda65727e221b75c391330a59ce22bac48c9a1" }
  ],
  "git": {
    "base": "ce4dc7325241f8a3269047934c31131274019c7c",
    "head": "44bda65727e221b75c391330a59ce22bac48c9a1",
    "branch": "feat/herdr-codex-first",
    "worktree": "/Users/mac/docs/superpowers/worktrees/herdr-codex-first-20260920/integration",
    "pr": 88
  },
  "files": ["skills/herdr/SKILL.md", "skills/herdr/references/report-contract.md"],
  "unresolved_effects": [],
  "requested_action": "integrate"
}
```

## 4. Atomic Publication Pipeline (No-Clobber & Verified)

```
[ Step 1: Write .partial ]
       │  Producer generates report via apply_patch to:
       │  <REPORT_ROOT>/<report_id>.partial
       ▼
[ Step 2: Validate Content, Shape, & Compute SHA-256 ]
       │  2a. Syntax validation:
       │    • PyYAML available: python3 -c "import yaml; yaml.safe_load(open('<REPORT_ROOT>/<report_id>.partial'))"
       │    • No PyYAML: Author as JSON-formatted YAML (valid YAML 1.2 subset),
       │      then validate with: python3 -c "import json; json.load(open('<REPORT_ROOT>/<report_id>.partial'))"
       │      JSON-formatted YAML is an authoring choice, not a claim json.load parses arbitrary YAML.
       │  2b. Shape validation — verify required top-level keys and mappings are not swallowed scalars.
       │      Required keys: schema_version, mission_id, task_id, attempt, report_id, producer, status.
       │      Required mappings: producer, manager, cto (each must be a dict, not a scalar).
       │  2c. Compute SHA-256 digest of the .partial file.
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
       │       shasum -a 256 <REPORT_ROOT>/<report_id>.yaml  (compare to Step 2c value)
       │  If .partial still exists after mv -n exits 0, a TOCTOU race occurred.
       │  Abort the notice. Do not report success for bytes not published.
       ▼
[ Step 4: Native Prompt Notice (No-Wait) ]
          herdr agent prompt "<MANAGER_PANE_ID>" "<NOTICE_TEXT>"
```

### Publication Rules
1. **No-Overwrite Invariant**: A published report is immutable. Pre-flight check ensures no silent clobber.
2. **No Producer Attempt Increments**: The EM alone increments `attempt`. Corrections within an attempt use a new unique `report_id` with a descriptive suffix (e.g. `task-a1-revision1.yaml`).

## 5. Concise Native Notice Format

Single-line format using discovered coordinates:
```text
REPORT NOTICE: mission_id=<MISSION_ID> task_id=<TASK_ID> attempt=<ATTEMPT> report_id=<REPORT_ID> pane_id=<ORIGIN_PANE_ID> tab_id=<ORIGIN_TAB_ID> report_path=<REPORT_PATH> status=<STATUS> requested_action=<REQUESTED_ACTION>
```

Workers **never** pass `--wait`. Passing `--wait` blocks the worker and risks deadlock.

## 6. Manager Consumption Semantics

When a report notice is received or discovered during state reconciliation:

1. **Identity Gate (before advancing graph)**: Verify `mission_id`, `task_id`, and `producer` fields (`pane_id`, `tab_id`, `terminal_id`, `role`, `runtime`) match registered assignment in `state.yaml`. Mismatch → quarantine. Manager advances graph only after identity passes.
2. **Attempt Gate**: `attempt == current` → process. `attempt > current` → quarantine. `attempt < current` → reject (log only).
3. **Idempotent Digest Check**: Compute SHA-256 of report. If `report_id` already recorded with identical digest → idempotent duplicate, no-op. If different digest → `MUTATED_REPORT_REJECTED`.
4. **Pending-Effect Reconciliation**: Before dispatching new work, confirm prior tasks' `unresolved_effects` are resolved or explicitly accepted.
5. **Receipt is NOT Approval**: Acknowledging receipt only records evidence. Advancing task to `approved` or `integrated` requires independent technical verification.
6. **Duplicate receipt creates no dispatch, Git, or ACK chain effects.**

## 7. Reviewer Q/A Protocol

When a reviewer needs clarification, publish a structured review report with `status: blocked` and `requested_action: qa_required`. Include `questions` as a YAML list with `id`, `context`, and `question` fields. Never resolve Q/A informally.
