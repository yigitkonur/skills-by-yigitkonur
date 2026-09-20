# Mission Brief Templates

## 1. Implementer Brief

```markdown
# Mission Brief: Implementation

## 1. Role Authority
- **Assigned Role**: Implementer (AGY). Write code, run tests, and publish local commits.

## 2. Live Coordinates
Identify your live coordinates via `herdr pane current`. Do not rely on static environment variables.

## 3. Mandatory Return Route
- MANAGER_PANE_ID: "<MANAGER_PANE_ID>"
- RUN_ROOT: "<ABSOLUTE_RUN_ROOT>"
- RETURN_ROUTE: `herdr agent prompt "$MANAGER_PANE_ID" "<NOTICE>"` (no `--wait`)

## 4. Execution
1. Implement the requested feature via TDD.
2. Commit locally.
3. Publish `report_root/task_id-handback.yaml` and notify manager.
```

## 2. Reviewer Brief

```markdown
# Mission Brief: Review

## 1. Role Authority
- **Assigned Role**: Fresh Reviewer (AGY). Read-only audit of exact candidate SHA.

## 2. Live Coordinates
Identify your live coordinates via `herdr pane current`.

## 3. Mandatory Return Route
- MANAGER_PANE_ID: "<MANAGER_PANE_ID>"
- RUN_ROOT: "<ABSOLUTE_RUN_ROOT>"
- RETURN_ROUTE: `herdr agent prompt "$MANAGER_PANE_ID" "<NOTICE>"` (no `--wait`)

## 4. Execution
1. Checkout exact candidate SHA `$CANDIDATE_SHA`. (Do not unconditionally `git checkout` if in a shared worktree).
2. Audit diff and test execution.
3. Publish `report_root/task_id-review.yaml` and notify manager.
```

## 3. Safe Submission
Write brief with `apply_patch`. Submit via `herdr agent prompt "$TARGET_PANE_ID" "$(< brief.md)"`.
