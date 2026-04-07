# Wave Execution

How to manage wave-by-wave execution of GitHub Issue plans.

Assumes `REPO` is already set and every `gh` command below uses `--repo "$REPO"`.

## Detecting the current wave

```bash
for wave in "wave:0-foundation" "wave:1" "wave:2" "wave:3" "wave:4" "wave:5"; do
  count=$(gh issue list --repo "$REPO" -l "$wave" --state open --json number --jq 'length')
  total=$(gh issue list --repo "$REPO" -l "$wave" --state all --json number --jq 'length')
  [ "$total" -gt 0 ] && echo "$wave: $((total - count))/$total closed ($count open)"
done
```

The current wave is the lowest-numbered wave with open issues.

## Dispatch queue vs closure queue

A leaf issue is ready to dispatch when:
1. Open
2. Labeled `type:task` or `type:subtask`
3. No open child issues
4. All issues in its "Blocked by" section are closed
5. Not labeled `status:in-progress`, `status:blocked`, `status:failed`, or `status:needs-review`

A parent issue is ready to close when:
1. It is still open
2. It has child issues
3. All child issues are closed
4. The parent's own Definition of Done can now be verified from the tree, comments, and resulting state

Do not dispatch parent issues as fresh implementation work just because their children are closed. Parent issues move into a closure-verification queue, not the ready-to-dispatch queue.

## Practical readiness audit

For each open issue in the current wave:

1. Read the issue body and labels:
   ```bash
   gh issue view NUMBER --repo "$REPO" --json body,labels,title
   ```
2. Read child state:
   ```bash
   gh api "repos/$REPO/issues/NUMBER/sub_issues" \
     --jq '.[] | "#\(.number) [\(.state)]"'
   ```
3. Classify it:
   - ready to dispatch: task/subtask, no open children, blockers closed, no active status label
   - ready to close: parent issue whose children are all closed
   - blocked/in-progress/failed/needs-review: keep out of the dispatch queue and present the reason to the user

If a wave still has open issues but zero ready leaf issues, stop and present the blockage summary. Do not guess the next action or silently advance to another wave.

## Dependency parsing

Treat the `## Wave & Dependencies` section as the source of truth for blockers:
1. Read the `**Blocked by:**` line from the issue body
2. If the line says `none`, the issue has no blockers
3. If the line lists `#` references, each referenced issue must be closed before the issue enters the ready queue
4. If the body is missing `## Wave & Dependencies` or `**Blocked by:**`, stop and treat the issue body as invalid for execution until the plan is corrected

## Status label management

```bash
# Starting work
gh issue edit NUMBER --repo "$REPO" --add-label "status:in-progress" --remove-label "status:ready"

# Needs review
gh issue edit NUMBER --repo "$REPO" --add-label "status:needs-review" --remove-label "status:in-progress"

# Failed attempt
gh issue edit NUMBER --repo "$REPO" --add-label "status:failed" --remove-label "status:in-progress" --remove-label "status:ready"

# Closing
gh issue edit NUMBER --repo "$REPO" --remove-label "status:in-progress" --remove-label "status:needs-review" --remove-label "status:blocked" --remove-label "status:failed" --remove-label "status:ready"
gh issue close NUMBER --repo "$REPO" --comment "Completed — all DoD criteria verified."
```

## Wave transition protocol

When all issues in a wave are closed:

1. Verify: `gh issue list --repo "$REPO" -l "wave:N" --state open --json number --jq 'length'` returns 0
2. Verify parent issues in wave `N` are closed, not just leaf issues
3. Read updated tree: `bash "$SKILL_DIR/scripts/read-tree.sh" "$REPO" ROOT_ISSUE`
4. Present completion summary
5. List next wave's ready leaf issues and any parents ready for closure
6. Ask user for confirmation before proceeding

## Progress reporting

```
## Wave N Progress

| Issue | Title | Status | DoD |
|---|---|---|---|
| #A | Setup auth | Completed | 5/5 |
| #B | Create schema | In Progress | - |
| #C | Add tests | Ready | - |
| #D | Deploy config | Blocked by #B | - |

**Wave:** 1/4 complete
**Overall:** 5/20 closed (25%)
```

## Handling blocked issues

```bash
gh issue edit NUMBER --repo "$REPO" --add-label "status:blocked"
gh issue comment NUMBER --repo "$REPO" --body "Blocked by #BLOCKER — waiting for completion."
```

Move to next ready issue. Check back after blocker resolves.

Failed issues are not ready issues. They stay labeled `status:failed` until the user chooses a recovery path.

## Reopening

If an issue needs rework after closing:
1. `gh issue reopen NUMBER --repo "$REPO"`
2. Comment with what needs fixing
3. Re-dispatch with failure context
4. Do not re-close dependents — they may need re-verification
