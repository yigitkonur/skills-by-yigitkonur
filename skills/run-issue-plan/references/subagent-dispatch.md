# Subagent Dispatch

How to generate subagent prompts from GitHub Issue bodies and dispatch them through the current runtime's subagent/task tool.

Assumes `REPO` and `SKILL_DIR` are already set.

## Reading an issue for dispatch

```bash
gh issue view NUMBER --repo "$REPO" --json title,body,labels,assignees,comments
gh api "repos/$REPO/issues/NUMBER/sub_issues" \
  --jq '.[] | "- #\(.number): \(.title) [\(.state)]"'
gh issue view NUMBER --repo "$REPO" --json comments \
  --jq '.comments[-3:] | .[] | "[\(.author.login)]: \(.body)"'
```

## Prompt template

Extract the three protocol sections from the issue body and assemble:

```
## Context & Rationale

You are working on issue #{NUMBER}: "{TITLE}" in the {REPO} repository.

{CONTEXT_AND_RATIONALE_FROM_ISSUE_BODY}

### Sub-issues in scope
{LIST_OF_SUB_ISSUES}

### Wave & dependency context
{WAVE_AND_DEPENDENCIES_SUMMARY}

### Additional context
{RECENT_COMMENTS_IF_ANY}

## Strategic Intent

{STRATEGIC_INTENT_FROM_ISSUE_BODY}

You own this problem. Explore freely, trust your judgment, adapt as needed.
Read relevant files by exploring the codebase before implementing.

## Definition of Done

{DOD_FROM_ISSUE_BODY_VERBATIM}

> You must achieve 100% of every criterion above before stopping.
> Partial completion = not complete. Do not hand back until every
> item is fully satisfied.

## Completion Protocol

When all DoD criteria are met:
1. Discover and run the project-native verification commands needed to prove the DoD
2. Confirm each criterion with evidence
3. Report completion listing evidence per criterion
```

## Dispatch via the runtime-native subagent tool

Dispatch the assembled prompt using whatever task/subagent mechanism the current runtime provides. Keep the prompt body intact and adapt only the wrapper fields:

- description/title: `Execute #NUMBER: SHORT_TITLE`
- prompt/body: the assembled prompt
- stable name or id: `issue-NUMBER` if supported
- autonomous worker mode if the runtime exposes mode selection

For independent issues in the same wave, launch multiple subagent/task invocations in the same turn when the runtime supports parallel dispatch.

## Dispatch patterns

**Sequential** — one issue at a time, verify between each. Use when issues have hidden dependencies.

**Parallel** — dispatch all ready issues simultaneously. Use for independent work within a wave.

**Wave-gated parallel** (recommended) — parallel within waves, sequential between waves with user confirmation.

## On completion

### Success

```bash
gh issue edit NUMBER --repo "$REPO" --remove-label "status:in-progress" --remove-label "status:needs-review" --remove-label "status:blocked" --remove-label "status:failed" --remove-label "status:ready"
gh issue close NUMBER --repo "$REPO" --comment "$(cat <<'EOF'
## Completed
All DoD criteria verified:
- [x] Criterion 1 — [evidence]
- [x] Criterion 2 — [evidence]
EOF
)"
```

### Failure

```bash
gh issue edit NUMBER --repo "$REPO" --remove-label "status:in-progress" --remove-label "status:needs-review" --remove-label "status:ready" --add-label "status:failed"
gh issue comment NUMBER --repo "$REPO" --body "Attempt incomplete. Unmet: [list]. Needs: [guidance]."
```

Keep the issue open. Do not retry without user input.

## Full tree context

For issues with sub-issues, read the full tree before dispatching:

```bash
FULL=1 bash "$SKILL_DIR/scripts/read-tree.sh" "$REPO" ISSUE_NUMBER
```

Include the output in the subagent prompt's "Sub-issues in scope" section. Summarize the `## Wave & Dependencies` section into the prompt's dependency context so the executing subagent sees blockers, dependents, and parent ownership boundaries.
