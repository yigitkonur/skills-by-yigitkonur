# Canonical Report Contract & Durable Mission Artifacts

## 1. Immutable Reports
Terminal PTY reads are lossy. All verifiable deliverables, test results, and status declarations must be published to durable, immutable YAML reports under `report_root` on disk.

## 2. Report Format
Reports are YAML files with the following fields:
- `mission_id`
- `task_id`
- `attempt`
- `role`
- `status` (e.g., `completed`, `blocked`, `rejected`, `approved`)
- `results` or `findings`
- `unresolved_effects`

## 3. Atomic Publication Pipeline
1. Write to `<path>.partial`
2. Validate content
3. Rename atomically: `mv <path>.partial <path>`
4. Notify the manager via `herdr agent prompt` (no `--wait`).

## 4. Manager Intake
The EM reads the report.
- Receipts are NOT approvals. The manager consumes the report to update `state.yaml` and advance the task graph.
- If the report indicates `rejected`, the EM schedules a new implementation attempt.
- If the report indicates `approved`, the EM schedules integration.
