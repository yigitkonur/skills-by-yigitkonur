# Wave Execution

How to manage wave-by-wave execution of GitHub Issue plans.

Assumes `REPO` and `SKILL_DIR` are already set.

## Canonical Status Command

Use the status script instead of hand-written wave loops:

```bash
bash "$SKILL_DIR/scripts/issue-tree-status.sh" "$REPO" ROOT_ISSUE
```

It discovers actual `wave:*` labels dynamically, so it supports wave 6+ and keeps `wave:0-foundation` first. Read `scripts/issue-tree-status.sh.md` for output fields and failure modes.

## State Machine

| From | To | Condition |
|---|---|---|
| `open/no-status` | `status:ready` | Dependencies and child issues are clear |
| `status:ready` | `status:in-progress` | Runtime-native dispatch starts |
| `status:in-progress` | `status:needs-review` | Human review is required before closure |
| `status:in-progress` | `closed` | Every DoD criterion is verified |
| `status:in-progress` | `status:failed` | Criteria remain unmet |
| `status:failed` | `status:ready` | User selects a recovery path |
| parent with closed children | closure-verification queue | Parent DoD must be verified; do not dispatch it as leaf work |

Re-runs must be idempotent. Re-read the tree and recompute readiness from issue bodies, child state, blocker state, and labels. Do not trust old session memory.

## Dispatch Queue vs Closure Queue

A leaf issue is ready to dispatch when:

1. It is open.
2. It is labeled `type:task` or `type:subtask`.
3. It has no open child issues.
4. All issues in its `Blocked by` line are closed.
5. It is not labeled `status:in-progress`, `status:blocked`, `status:failed`, or `status:needs-review`.

A parent issue is ready to close when:

1. It is still open.
2. It has child issues.
3. All child issues are closed.
4. The parent's own Definition of Done can now be verified from the tree, comments, and resulting state.

Parent issues move into a closure-verification queue, not the dispatch queue.

## Status Label Idempotency

Labels are state hints, not the source of truth. The source of truth is the current GitHub tree plus issue body dependencies.

Flag stale labels when:

- `status:ready` exists but a blocker is reopened or still open
- `status:ready` exists but the issue still has open children
- `status:blocked` exists but the `Blocked by` line has no open blockers
- an issue has multiple active status labels

`issue-tree-status.sh` reports stale label warnings. Resolve them before dispatching.

## Dependency Parsing

Treat the `## Wave & Dependencies` section as the source of truth for blockers:

1. Read the `**Blocked by:**` line from the issue body.
2. If the line says `none`, the issue has no blockers.
3. If the line lists `#` references, each referenced issue must be closed before the issue enters the ready queue.
4. If the body is missing `## Wave & Dependencies` or `**Blocked by:**`, treat the body as invalid for execution until corrected.

## Status Label Management

Starting work:

```bash
gh issue edit NUMBER --repo "$REPO" --add-label "status:in-progress" --remove-label "status:ready"
```

Needs review:

```bash
gh issue edit NUMBER --repo "$REPO" --add-label "status:needs-review" --remove-label "status:in-progress"
```

Failed attempt:

```bash
gh issue edit NUMBER --repo "$REPO" --add-label "status:failed" --remove-label "status:in-progress" --remove-label "status:ready"
```

Closing:

```bash
gh issue edit NUMBER --repo "$REPO" --remove-label "status:in-progress" --remove-label "status:needs-review" --remove-label "status:blocked" --remove-label "status:failed" --remove-label "status:ready"
gh issue close NUMBER --repo "$REPO" --comment "Completed - all DoD criteria verified."
```

## Wave Transition Protocol

When all issues in a wave are closed:

1. Run `issue-tree-status.sh`.
2. Confirm the wave has zero open issues.
3. Confirm parent issues in the wave are closed, not just leaf issues.
4. Present completion summary with DoD evidence.
5. List next wave ready leaf issues and parent closure queue.
6. Ask the user for confirmation before proceeding to the next wave.

## Handling Blocked And Failed Issues

Blocked issues stay open and out of the ready queue until blockers close. Failed issues stay labeled `status:failed` until the user chooses recovery. Do not auto-retry.

If an issue needs rework after closing:

1. Reopen it.
2. Comment with what needs fixing.
3. Re-dispatch with failure context.
4. Re-verify dependents that may have relied on the closed state.
