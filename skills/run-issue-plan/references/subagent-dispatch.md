# Subagent Dispatch

How to generate subagent prompts from GitHub Issue bodies and dispatch them via the Agent tool.

## Reading an issue for dispatch

```bash
gh issue view NUMBER --json title,body,labels,assignees,comments
gh api repos/OWNER/REPO/issues/NUMBER/sub_issues \
  --jq '.[] | "- #\(.number): \(.title) [\(.state)]"'
gh issue view NUMBER --json comments \
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
1. Run verification commands from the DoD
2. Confirm each criterion with evidence
3. Report completion listing evidence per criterion
```

## Dispatch via Agent tool

```
Agent(
  description: "Execute #NUMBER: SHORT_TITLE",
  prompt: [assembled prompt],
  subagent_type: "general-purpose",
  mode: "auto",
  name: "issue-NUMBER"
)
```

For independent issues in the same wave, dispatch multiple Agent calls in a single message.

## Dispatch patterns

**Sequential** — one issue at a time, verify between each. Use when issues have hidden dependencies.

**Parallel** — dispatch all ready issues simultaneously. Use for independent work within a wave.

**Wave-gated parallel** (recommended) — parallel within waves, sequential between waves with user confirmation.

## On completion

### Success

```bash
gh issue edit NUMBER --remove-label "status:in-progress"
gh issue close NUMBER --comment "$(cat <<'EOF'
## Completed
All DoD criteria verified:
- [x] Criterion 1 — [evidence]
- [x] Criterion 2 — [evidence]
EOF
)"
```

### Failure

```bash
gh issue edit NUMBER --remove-label "status:in-progress" --add-label "status:blocked"
gh issue comment NUMBER --body "Attempt incomplete. Unmet: [list]. Needs: [guidance]."
```

Keep the issue open. Do not retry without user input.

## Full tree context

For issues with sub-issues, read the full tree before dispatching:

```bash
FULL=1 bash {baseDir}/scripts/read-tree.sh OWNER/REPO ISSUE_NUMBER
```

Include the output in the subagent prompt's "Sub-issues in scope" section.
