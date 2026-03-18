---
name: run-issue-plan
description: Use skill if you are executing a project plan stored as GitHub Issues with sub-issues by reading the tree, dispatching subagents wave-by-wave, and tracking completion.
---

# Run Issue Plan

Execute wave-based project plans stored as GitHub Issue trees by reading the hierarchy, dispatching subagents per issue, and tracking completion wave-by-wave.

## Trigger boundary

Use when an existing GitHub Issue tree needs to be executed with subagent dispatches.

Do NOT use when:
- Creating a new plan (use `plan-issue-tree`)
- Reviewing code (use `review-pr`)
- No GitHub Issues exist yet

## Prerequisites

1. `gh auth status` — must be authenticated
2. User provides the root issue number, or detect it:
   ```bash
   gh issue list -l "type:epic" -l "wave:0-foundation" --json number,title --jq '.[] | "#\(.number): \(.title)"'
   ```
3. Verify the tree:
   ```bash
   bash {baseDir}/scripts/read-tree.sh "$REPO" ROOT_NUMBER
   ```

## Workflow

### Phase 1: Read the plan

```bash
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
FULL=1 bash {baseDir}/scripts/read-tree.sh "$REPO" ROOT_NUMBER
```

Present the tree with open/closed counts per wave.

### Phase 2: Identify current wave

Read `references/wave-execution.md` for detailed wave management.

```bash
for wave in "wave:0-foundation" "wave:1" "wave:2" "wave:3" "wave:4" "wave:5"; do
  count=$(gh issue list -l "$wave" --state open --json number --jq 'length')
  total=$(gh issue list -l "$wave" --state all --json number --jq 'length')
  [ "$total" -gt 0 ] && echo "$wave: $((total - count))/$total closed ($count open)"
done
```

List ready issues — open, leaf-level, all blockers closed, not in-progress.

Present to user:

```
**Current Wave: wave:1** (3/8 complete)

Ready:
- [ ] #12: Setup authentication (3 subtasks)
- [ ] #15: Create database schema

Blocked:
- [ ] #20: Integration tests — blocked by #12, #15

Completed:
- [x] #18: Configure CI/CD
```

### Phase 3: Dispatch subagents

Read `references/subagent-dispatch.md` for the prompt template.

For each ready issue:

1. Read the issue fully:
   ```bash
   gh issue view NUMBER --json title,body,labels,assignees,comments
   ```

2. Read sub-issues:
   ```bash
   gh api "repos/$REPO/issues/NUMBER/sub_issues" \
     --jq '.[] | "- #\(.number): \(.title) [\(.state)]"'
   ```

3. Read recent comments:
   ```bash
   gh issue view NUMBER --json comments \
     --jq '.comments[-3:] | .[] | "[\(.author.login)]: \(.body)"'
   ```

4. Mark in-progress:
   ```bash
   gh issue edit NUMBER --add-label "status:in-progress" --remove-label "status:ready"
   ```

5. Generate the subagent prompt from the issue body — extract Context & Rationale, Strategic Intent, and Definition of Done sections verbatim.

6. Dispatch:
   ```
   Agent(
     description: "Execute #NUMBER: SHORT_TITLE",
     prompt: [generated prompt],
     subagent_type: "general-purpose",
     mode: "auto",
     name: "issue-NUMBER"
   )
   ```

7. For independent issues in the same wave, dispatch **multiple Agent calls in a single message**.

### Phase 4: Completion verification

After each subagent returns:

1. Check every BSV criterion from the issue's Definition of Done
2. If ALL met — close the issue with evidence:
   ```bash
   gh issue close NUMBER --comment "Completed. All DoD verified: [evidence per criterion]."
   ```
3. If NOT met — comment and keep open:
   ```bash
   gh issue comment NUMBER --body "Incomplete. Unmet: [list]. Needs: [guidance]."
   ```
   Do NOT retry without user input.

### Phase 5: Wave transition

When all wave issues are closed:

1. Announce completion with summary
2. Read tree again: `bash {baseDir}/scripts/read-tree.sh "$REPO" ROOT_NUMBER`
3. Show next wave's ready issues
4. **Ask user for confirmation** before proceeding
5. Repeat from Phase 2

## Decision rules

- Execute leaf issues (task/subtask) first; parent issues close when all children close
- If an issue has sub-issues, dispatch each sub-issue separately
- If a subagent fails, comment on the issue and ask the user — do not auto-retry
- Independent issues within a wave dispatch in parallel
- Never modify issue bodies — only add comments
- Verify DoD with evidence before closing

## Reference routing

| File | When to read |
|---|---|
| `references/subagent-dispatch.md` | Before generating any subagent prompt |
| `references/wave-execution.md` | When managing wave transitions, status labels, or blocked issues |

## Guardrails

- Do NOT execute without showing the plan tree first
- Do NOT skip wave order — waves are sequential, issues within waves can be parallel
- Do NOT close an issue unless ALL BSV criteria are verifiably met
- Do NOT proceed to next wave without user confirmation
- Do NOT modify issue bodies — only add comments
- Do NOT retry failed issues without user input
- Always read full issue body, sub-issues, and comments before dispatching
- Use `gh` CLI for all GitHub operations
