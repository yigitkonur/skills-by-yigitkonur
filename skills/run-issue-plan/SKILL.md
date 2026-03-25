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
2. `command -v jq >/dev/null` — required by `scripts/read-tree.sh`
3. Resolve the helper-script path once:
   ```bash
   REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
   SKILL_DIR="/absolute/path/to/run-issue-plan"  # directory containing this SKILL.md
   [ -x "$SKILL_DIR/scripts/read-tree.sh" ] || {
     echo "Set SKILL_DIR to the absolute path of the directory that contains this SKILL.md before using helper scripts." >&2
     exit 1
   }
   ```
   `SKILL_DIR` is the local skill install path, not a path inside the target repository. After `REPO` is set, pass `--repo "$REPO"` to every later `gh` command.
4. This skill assumes the current runtime can dispatch subagents. If it cannot, stop after Phase 2 and hand back the ready-issue set plus dispatch prompts for manual execution.
5. User provides the root issue number, or detect it:
   ```bash
   gh issue list --repo "$REPO" -l "type:epic" -l "wave:0-foundation" --json number,title --jq '.[] | "#\(.number): \(.title)"'
   ```
   If this returns no epics and the user did not provide `ROOT_NUMBER`, stop and route to `plan-issue-tree`. If it returns multiple epics and the user did not provide `ROOT_NUMBER`, present the candidates and ask the user to choose. This skill does not create plans or guess roots.
6. Verify the tree:
   ```bash
   bash "$SKILL_DIR/scripts/read-tree.sh" "$REPO" ROOT_NUMBER
   ```

## Workflow

### Phase 1: Read the plan

```bash
FULL=1 bash "$SKILL_DIR/scripts/read-tree.sh" "$REPO" ROOT_NUMBER
```

Present the tree with open/closed counts per wave.

### Phase 2: Identify current wave

Read `references/wave-execution.md` for detailed wave management.

```bash
for wave in "wave:0-foundation" "wave:1" "wave:2" "wave:3" "wave:4" "wave:5"; do
  count=$(gh issue list --repo "$REPO" -l "$wave" --state open --json number --jq 'length')
  total=$(gh issue list --repo "$REPO" -l "$wave" --state all --json number --jq 'length')
  [ "$total" -gt 0 ] && echo "$wave: $((total - count))/$total closed ($count open)"
done
```

List ready leaf issues to dispatch — open `type:task` or `type:subtask` issues with no open children, all blockers closed, and no `status:in-progress`, `status:blocked`, `status:failed`, or `status:needs-review` label. Track parent issues separately: when all children close, verify the parent's own DoD and close it without dispatching a fresh implementation subagent.

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
Read `references/generic-prompt-patterns.md` for tool-agnostic prompt writing rules.

For each ready issue:

1. Read the issue fully:
   ```bash
   gh issue view NUMBER --repo "$REPO" --json title,body,labels,assignees,comments
   ```

2. Read sub-issues:
   ```bash
   gh api "repos/$REPO/issues/NUMBER/sub_issues" \
     --jq '.[] | "- #\(.number): \(.title) [\(.state)]"'
   ```

3. Read recent comments:
   ```bash
   gh issue view NUMBER --repo "$REPO" --json comments \
     --jq '.comments[-3:] | .[] | "[\(.author.login)]: \(.body)"'
   ```

4. **Pre-dispatch validation:**
   - Body contains all 4 protocol sections (Context & Rationale, Strategic Intent, Definition of Done, Wave & Dependencies)
   - DoD criteria are BSV (Binary, Specific, Verifiable) — no vague language
   - DoD is tool-agnostic — no specific editors, test runners, or build tools named in the prompt body
   - Body is under 60,000 characters
   - All cross-references (#numbers) point to existing issues

5. Mark in-progress:
   ```bash
   gh issue edit NUMBER --repo "$REPO" --add-label "status:in-progress" --remove-label "status:ready"
   ```

6. Generate the subagent prompt from the issue body — extract Context & Rationale, Strategic Intent, and Definition of Done sections verbatim, then carry the Wave & Dependencies section into the prompt as execution context so blockers, parent/child relationships, and downstream issues are visible. The prompt must remain tool-agnostic: no mentions of specific editors, test runners, or build tools. See `references/generic-prompt-patterns.md`.

7. Dispatch the assembled prompt through the current runtime's native subagent/task tool. Preserve the prompt body unchanged. Use:
   - description/title: `Execute #NUMBER: SHORT_TITLE`
   - prompt/body: the assembled prompt
   - stable issue-based name/id if the runtime supports one
   - autonomous worker mode if the runtime exposes mode selection

8. For independent issues in the same wave, dispatch multiple subagent/task invocations in the same turn when the runtime supports parallel launches.

If subagent dispatch is unavailable in the current runtime, stop here and return:
- the ready issue list
- the generated dispatch prompt per issue
- the label/status changes the user must apply manually

### Phase 4: Completion verification

After each subagent returns:

1. Check every BSV criterion from the issue's Definition of Done
2. If ALL met — close the issue with evidence:
   ```bash
   gh issue edit NUMBER --repo "$REPO" --remove-label "status:in-progress" --remove-label "status:needs-review" --remove-label "status:blocked" --remove-label "status:failed" --remove-label "status:ready"
   gh issue close NUMBER --repo "$REPO" --comment "Completed. All DoD verified: [evidence per criterion]."
   ```
3. If NOT met — comment and keep open:
   ```bash
   gh issue edit NUMBER --repo "$REPO" --remove-label "status:in-progress" --add-label "status:failed"
   gh issue comment NUMBER --repo "$REPO" --body "Incomplete. Unmet: [list]. Needs: [guidance]."
   ```
   Do NOT retry without user input.

### Phase 5: Wave transition

When all wave issues are closed:

1. Announce completion with summary
2. Read tree again: `bash "$SKILL_DIR/scripts/read-tree.sh" "$REPO" ROOT_NUMBER`
3. Show next wave's ready leaf issues plus any parent issues now eligible for closure
4. **Ask user for confirmation** before proceeding
5. Repeat from Phase 2

**If the wave has partial failures** (some issues closed, some failed), read `references/partial-wave-handling.md` for recovery patterns:
- Single failure with no downstream blocks → offer to advance while re-dispatching in parallel
- Single failure blocking next wave → present options (fix, re-dispatch with context, manual investigation)
- Multiple failures → present failure summary table, let user choose strategy
- Never auto-advance past a failed wave without user confirmation

**State recovery:** If the orchestrator session is interrupted, all state is recoverable from GitHub labels and issue states. Re-read the tree and reconstruct from `wave:*` and `status:*` labels. See `references/partial-wave-handling.md`.

## Decision rules

- Dispatch only ready leaf issues (`type:task` or `type:subtask`); parent issues close after their children close and their own DoD is verified
- If an issue has sub-issues, dispatch the child issues separately and keep the parent out of the implementation queue
- If a subagent fails, comment on the issue and ask the user — do not auto-retry
- Independent issues within a wave dispatch in parallel
- Never modify issue bodies — only add comments
- Verify DoD with evidence before closing

## Reference routing

| File | When to read |
|---|---|
| `references/subagent-dispatch.md` | Before generating any subagent prompt or mapping it onto the current runtime's subagent tool |
| `references/wave-execution.md` | When detecting ready leaf issues, closing parent issues, or managing wave transitions/status labels |
| `references/generic-prompt-patterns.md` | When writing or reviewing subagent prompts for tool-agnosticism |
| `references/partial-wave-handling.md` | When a wave has failures — recovery patterns, re-dispatch with context, state reconstruction |

## Guardrails

- Do NOT execute without showing the plan tree first
- Do NOT skip wave order — waves are sequential, issues within waves can be parallel
- Do NOT close an issue unless ALL BSV criteria are verifiably met
- Do NOT proceed to next wave without user confirmation
- Do NOT modify issue bodies — only add comments
- Do NOT retry failed issues without user input
- Always read full issue body, sub-issues, and comments before dispatching
- Use `gh` CLI for all GitHub operations, always with `--repo "$REPO"` once `REPO` is known
