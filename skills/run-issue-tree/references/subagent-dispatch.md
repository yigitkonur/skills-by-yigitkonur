# Subagent Dispatch

How to generate worker prompts from GitHub Issue bodies and dispatch them through the current runtime's native subagent/task tool.

`gh` manages GitHub state only. It is not the worker dispatch mechanism.

## Dispatch Preparation

Use the script:

```bash
bash "$SKILL_DIR/scripts/dispatch-wave.sh" "$REPO" ROOT_ISSUE --limit CONCURRENCY
```

Add `--mark-in-progress` only when selected issues are actually being handed to runtime workers. Read `scripts/dispatch-wave.sh.md` for arguments and failure modes.

The script writes:

- `status.md` from `issue-tree-status.sh`
- `manifest.json`
- `prompts/issue-N.md`

## Manifest Schema

Each `manifest.json` entry has:

```json
{
  "issue_number": 123,
  "title": "Implement login endpoint",
  "wave": "wave:1",
  "labels": ["wave:1", "type:task", "priority:high"],
  "prompt_file": "/absolute/path/prompts/issue-123.md",
  "blockers": [],
  "parent": "122",
  "expected_completion_report_fields": [
    "issue_number",
    "files_changed",
    "commands_run",
    "dod_evidence",
    "deviations",
    "remaining_risk"
  ]
}
```

## Prompt Assembly Rules

Generated prompts must remain tool-agnostic. Use issue body content as the execution contract and preserve these lines exactly:

```markdown
You own this problem. Explore freely, trust your judgment, adapt as needed.
You must achieve 100% of every criterion above before stopping.
Partial completion = not complete. Do not hand back until every item is fully satisfied.
```

The prompt should include:

- repository and issue number
- issue title
- wave and dependency context
- parent issue
- recent comments if manually added by the orchestrator
- issue body sections
- expected completion report fields

## Runtime Dispatch Pattern

For each selected manifest entry, call the current runtime's native task/subagent tool:

- description/title: `Execute #NUMBER: SHORT_TITLE`
- prompt/body: contents of `prompt_file`
- stable name or id: `issue-NUMBER` if supported
- autonomous worker mode if the runtime exposes mode selection

Launch independent issues in the same wave in parallel up to the Q5 concurrency cap. Do not dispatch parent closure-queue issues as implementation workers.

If runtime-native dispatch is unavailable, return the manifest and prompt files for manual execution. Do not invent a shell-based worker launcher.

## Completion Handling

### Success

Close only after every DoD criterion has evidence:

```bash
gh issue edit NUMBER --repo "$REPO" --remove-label "status:in-progress" --remove-label "status:needs-review" --remove-label "status:blocked" --remove-label "status:failed" --remove-label "status:ready"
gh issue close NUMBER --repo "$REPO" --comment "$(cat <<'EOF'
## Completed
All DoD criteria verified:
- [x] Criterion 1 - evidence
- [x] Criterion 2 - evidence
EOF
)"
```

### Failure

```bash
gh issue edit NUMBER --repo "$REPO" --remove-label "status:in-progress" --remove-label "status:needs-review" --remove-label "status:ready" --add-label "status:failed"
gh issue comment NUMBER --repo "$REPO" --body "Attempt incomplete. Unmet: [list]. Needs: [guidance]."
```

Keep the issue open. Do not retry without user input.

## Reading Extra Context

Before dispatching, read:

```bash
FULL=1 bash "$SKILL_DIR/scripts/read-tree.sh" "$REPO" ISSUE_NUMBER
gh issue view NUMBER --repo "$REPO" --json comments --jq '.comments[-3:]'
```

Summarize comments and tree context into the prompt only when they change the worker's task. Avoid pasting stale file contents; list paths and let the worker read fresh code.
