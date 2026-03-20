# Partial Wave Handling

How to manage waves where some issues succeed and others fail, and how to recover gracefully.

## Failure modes

### 1. Single issue failure in a wave

One issue fails while others in the same wave succeed.

**Detection:**
```bash
# Count open issues in the current wave
OPEN=$(gh issue list -l "wave:$WAVE" --state open --json number --jq 'length')
FAILED=$(gh issue list -l "wave:$WAVE" -l "status:failed" --json number --jq 'length')
DONE=$(gh issue list -l "wave:$WAVE" --state closed --json number --jq 'length')

echo "Wave $WAVE: $DONE closed, $OPEN open ($FAILED failed)"
```

**Response:**
1. Mark failed issue with `status:failed` label
2. Comment on the issue with failure details and unmet DoD criteria
3. Check if any wave N+1 issues are blocked ONLY by this failed issue
4. If yes — those N+1 issues stay blocked. Present to user.
5. If other N+1 issues are unblocked — they can proceed (with user confirmation)

### 2. Multiple failures in a wave

More than one issue fails in the same wave.

**Response:**
1. Mark each failed issue with `status:failed`
2. Present a failure summary table to the user:

```
## Wave N Failure Report

| Issue | Title | Status | Unmet DoD |
|---|---|---|---|
| #12 | Auth middleware | FAILED | Test suite fails |
| #15 | DB schema | FAILED | Migration errors |
| #18 | CI config | COMPLETED | — |
| #20 | Integration tests | BLOCKED | Waiting on #12, #15 |

**Options:**
1. Fix #12 and #15, then re-verify
2. Re-dispatch #12 and #15 with failure context
3. Skip and proceed to unblocked wave N+1 issues
4. Pause and investigate manually
```

3. Do NOT proceed without user choosing an option

### 3. Cascading block

A failed issue blocks multiple downstream issues across waves.

**Detection:**
```bash
# Find all issues that reference the failed issue in "Blocked by"
FAILED_NUM=12
gh issue list --state open --json number,body --jq \
  ".[] | select(.body | test(\"Blocked by:.*#$FAILED_NUM\")) | \"#\\(.number)\""
```

**Response:**
1. List the full cascade: failed issue → directly blocked → transitively blocked
2. Quantify impact: "Fixing #12 unblocks 3 issues in wave 2 and 5 issues in wave 3"
3. Present to user for decision

### 4. Same-wave circular dependency

Two issues in the same wave block each other (planning error).

**Detection:** During dispatch, if an issue lists a blocker that is in the same wave and that blocker lists the current issue as a blocker.

**Response:**
1. Flag the circular dependency
2. Suggest breaking the cycle: one issue becomes the prerequisite
3. Re-assign one to an earlier wave
4. Present to user for decision

## Recovery patterns

### Re-dispatch with failure context

When re-dispatching a failed issue, include the failure context from the previous attempt:

```markdown
## Previous Attempt Context

This issue was previously attempted and failed.

**Previous failure:** {description of what went wrong}
**Unmet DoD criteria:**
- [ ] {criterion 1} — failed because: {reason}
- [ ] {criterion 2} — failed because: {reason}

**Guidance for retry:**
- {specific guidance based on failure analysis}
- {what to do differently}
```

Add this to the subagent prompt BEFORE the standard issue body sections.

### Partial wave advancement

When most of a wave succeeds but one issue fails and doesn't block wave N+1:

```
Wave 1: 7/8 complete
  #12 FAILED — does not block any wave 2 issues
  All other wave 1 issues closed

Decision: Advance to wave 2 while re-attempting #12 in parallel?
```

If the user approves:
1. Dispatch wave 2 issues as normal
2. Re-dispatch #12 with failure context
3. Track #12 separately — it's now a "trailing" issue

### Wave rollback

When failures are severe enough to invalidate the wave:

1. Do NOT close any issues in the wave
2. Present the situation to the user
3. Options: fix and retry, re-plan the wave, or re-plan the entire project

## State tracking across sessions

All state is stored in GitHub labels and issue comments. If the orchestrator crashes and restarts, it can reconstruct state by:

```bash
# Reconstruct current state
echo "=== Project State ==="
for wave in "wave:0-foundation" "wave:1" "wave:2" "wave:3" "wave:4" "wave:5"; do
  TOTAL=$(gh issue list -l "$wave" --state all --json number --jq 'length')
  CLOSED=$(gh issue list -l "$wave" --state closed --json number --jq 'length')
  FAILED=$(gh issue list -l "$wave" -l "status:failed" --json number --jq 'length')
  IN_PROG=$(gh issue list -l "$wave" -l "status:in-progress" --json number --jq 'length')
  [ "$TOTAL" -gt 0 ] && echo "$wave: $CLOSED/$TOTAL closed, $FAILED failed, $IN_PROG in-progress"
done
```

This produces a complete snapshot without any external state storage.

## Decision matrix

| Scenario | Blocks next wave? | User action required? | Recovery |
|---|---|---|---|
| 1 issue fails, no downstream deps | No | Yes (confirm advance) | Re-dispatch in parallel with next wave |
| 1 issue fails, blocks N+1 issues | Yes (partially) | Yes (choose strategy) | Fix first, or advance unblocked issues |
| Multiple failures | Likely | Yes (review options) | Present failure table, let user decide |
| All issues fail | Yes | Yes | Re-plan the wave |
| Circular dependency | Wave stuck | Yes | Break cycle, re-assign waves |
| Orchestrator crash | No (state in labels) | No (auto-resume) | Re-read labels, resume from last state |
