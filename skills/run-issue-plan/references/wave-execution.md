# Wave Execution

How to manage wave-by-wave execution of GitHub Issue plans.

## Detecting the current wave

```bash
for wave in "wave:0-foundation" "wave:1" "wave:2" "wave:3" "wave:4" "wave:5"; do
  count=$(gh issue list -l "$wave" --state open --json number --jq 'length')
  total=$(gh issue list -l "$wave" --state all --json number --jq 'length')
  [ "$total" -gt 0 ] && echo "$wave: $((total - count))/$total closed ($count open)"
done
```

The current wave is the lowest-numbered wave with open issues.

## Ready issue detection

An issue is ready when:
1. Open
2. All issues in its "Blocked by" section are closed
3. Leaf node (type:task or type:subtask) or all children closed
4. Not labeled `status:in-progress`

## Status label management

```bash
# Starting work
gh issue edit NUMBER --add-label "status:in-progress" --remove-label "status:ready"

# Needs review
gh issue edit NUMBER --add-label "status:needs-review" --remove-label "status:in-progress"

# Closing
gh issue edit NUMBER --remove-label "status:in-progress" --remove-label "status:needs-review" --remove-label "status:blocked" --remove-label "status:ready"
gh issue close NUMBER --comment "Completed — all DoD criteria verified."
```

## Wave transition protocol

When all issues in a wave are closed:

1. Verify: `gh issue list -l "wave:N" --state open --json number --jq 'length'` returns 0
2. Read updated tree: `bash {baseDir}/scripts/read-tree.sh REPO ROOT_ISSUE`
3. Present completion summary
4. List next wave's ready issues
5. Ask user for confirmation before proceeding

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
gh issue edit NUMBER --add-label "status:blocked"
gh issue comment NUMBER --body "Blocked by #BLOCKER — waiting for completion."
```

Move to next ready issue. Check back after blocker resolves.

## Reopening

If an issue needs rework after closing:
1. `gh issue reopen NUMBER`
2. Comment with what needs fixing
3. Re-dispatch with failure context
4. Do not re-close dependents — they may need re-verification
