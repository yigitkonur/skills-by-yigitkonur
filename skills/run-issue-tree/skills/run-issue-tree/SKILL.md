---
name: run-issue-tree
description: Use skill if you are planning or executing a project as GitHub Issues with sub-issues, wave-based execution, labels, and subagent dispatch via gh CLI.
---

# Run Issue Tree

Plan and execute wave-based project plans as GitHub Issue trees with sub-issue nesting (up to 8 levels), labels, and agent-ready issue bodies that follow the subagent prompt protocol.

## Trigger boundary

Use when planning any project, feature, or complex task using GitHub Issues with sub-issues and wave labels, OR executing an existing issue tree with subagent dispatches.

Do NOT use when:
- Reviewing a PR (use `do-review`)
- General planning without GitHub Issues

## Mode routing

This skill has two modes. Auto-detect based on context:

| Condition | Mode |
|---|---|
| No issue tree exists yet | **Plan Mode** (P1-P6) |
| Issue tree exists with open waves | **Execute Mode** (E1-E5) |
| User says "plan" explicitly | **Plan Mode** |
| User says "run" or "execute" explicitly | **Execute Mode** |

If Execute Mode detects no epics and the user did not provide a root issue number, switch to Plan Mode automatically.

## Prerequisites

```bash
gh auth status
command -v jq >/dev/null
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
SKILL_DIR="/absolute/path/to/run-issue-tree"  # directory containing this SKILL.md
[ -d "$SKILL_DIR/scripts" ] || {
  echo "Set SKILL_DIR to the absolute path of this skill directory before using helper scripts." >&2
  exit 1
}
```

`SKILL_DIR` must be the absolute path of the directory that contains this `SKILL.md`. Do **not** assume the target repository also contains the skill. After `REPO` is set, pass `--repo "$REPO"` to every later `gh` command so reads and mutations always target the planned repository.

For Execute Mode, verify the tree exists:
```bash
bash "$SKILL_DIR/scripts/read-tree.sh" "$REPO" ROOT_NUMBER
```

If this returns no epics and the user did not provide `ROOT_NUMBER`, switch to Plan Mode.

---

## Plan Mode

### P1: Context discovery

1. Detect repo: `gh repo view --json nameWithOwner -q .nameWithOwner`
2. Scan existing issues: `gh issue list --repo "$REPO" --state open --limit 10 --json number,title,labels`
3. Brief codebase scan (README, package.json, entry points)

### P2: Brainstorming questions

Ask the **5 required core questions** from `references/question-bank.md` (Q1-Q5). Add **0-2 optional follow-up questions** only when the task type demands more detail. Users answer in compact form: `1b,2d,3g,4a,5c`.

Required coverage is non-negotiable:
- Project scope and type
- Decomposition depth
- Wave count
- Success criteria (for BSV Definition of Done)
- Agent execution preference

Format each question as:

```
**Q1: What are you building?**
  a) Greenfield project from scratch
  b) Major new feature for existing project
  ...

**Answer format:** `1b,2c,3d,4a,5e` (one letter per question)
```

If the user answers in prose instead of compact codes, map each response back to Q1-Q5 explicitly before planning and ask follow-ups only for unanswered slots.

If the user does not answer the questions:
- stop after presenting the unanswered question set
- do **not** design the final tree or create issues
- tell the user you are blocked on planning inputs

If the user explicitly says to proceed with assumptions:
- create a **draft-only** tree with an `Assumptions` section up front
- tag every guessed answer explicitly
- still require explicit approval before any label mutation or issue creation

### P3: Plan design

Based on answers, design the full issue tree:

1. **Map waves** — group work into sequential waves. Wave 0 is always foundation. Q3 counts the waves after Wave 0.
2. **Decompose maximally** — every feature gets tasks, every task gets subtasks.
3. **Map dependencies** — which issues block others? These become sub-issue relationships.
4. **Assign labels** — wave, type, priority per issue. See `references/label-schema.md`.

Present the plan as an indented tree before creating issues:

```
Wave 0: Foundation
  Epic: Project Setup
    Task: Initialize repo structure
      Subtask: Create directory layout
      Subtask: Add configuration files
    Task: Set up CI/CD
      Subtask: Configure build pipeline

Wave 1: Core Features
  Epic: Feature A
    Task: Implement X
      Subtask: ...
```

**Maximalism targets:** 3-8 subtasks per task, 2-5 tasks per feature, 2-4 features per wave. Minimum totals: 20 issues (small), 50+ (medium), 100+ (large).

Wait for user approval before creating issues or mutating labels.

### P4: Issue creation

Create issues **bottom-up** (leaves first) so child IDs exist when wiring parents.

If wave/type/priority labels are missing, ask for explicit approval to create them. Then run:

```bash
MAX_WAVE="${MAX_WAVE:-5}" bash "$SKILL_DIR/scripts/setup-labels.sh" "$REPO"
```

**Before every `gh issue create`**, validate the body:
1. Character count must be under 60,000 (GitHub limit: 65,536; buffer for post-creation edits)
2. All four required sections present (Context & Rationale, Strategic Intent, Definition of Done, Wave & Dependencies)
3. Ownership line and DoD closing text match the subagent prompt protocol verbatim
4. No vague DoD criteria ("tests pass", "works correctly", "code is clean")
5. DoD stays tool-agnostic — describe outcomes, not specific editors, test runners, or build tools
6. All cross-referenced issue numbers exist

Read `references/body-size-validation.md` for the full validation sequence. If a body exceeds 60,000 characters, split into parent-stub + child-detail pattern.

```bash
BODY="$(cat <<'BODY'
[body following subagent protocol]
BODY
)"

BODY_LENGTH=$(echo -n "$BODY" | wc -c)
if [ "$BODY_LENGTH" -gt 60000 ]; then
  echo "SPLIT REQUIRED: $BODY_LENGTH chars exceeds threshold"
  exit 1
fi

ISSUE_URL=$(gh issue create \
  --repo "$REPO" \
  -t "Issue title" \
  -l "wave:1" \
  -l "type:task" \
  -l "priority:high" \
  -b "$BODY")
ISSUE_NUM=${ISSUE_URL##*/}
```

Read `references/issue-body-template.md` for the body format. Every body contains:
- **Context & Rationale** — what, why, what it unlocks
- **Strategic Intent** — end-state, constraints, risks, ownership grant
- **Definition of Done** — BSV checklist (Binary, Specific, Verifiable)
- **Protocol wording** — ownership line and DoD closing sentence copied exactly
- **Wave & Dependencies** — wave number, blocks/blocked-by

Keep issue bodies tool-agnostic. Put file paths and architecture hints in `Technical Notes`; do not hard-code editor, test-runner, or build-tool commands into the body.

### P5: Sub-issue wiring and cross-linking

After creating all issues, wire relationships in two passes:

**Pass 1 — Sub-issue hierarchy (bottom-up):**

```bash
bash "$SKILL_DIR/scripts/link-sub-issue.sh" "$REPO" PARENT_NUMBER CHILD_NUMBER
```

**Pass 2 — Bidirectional cross-references:**

```bash
gh issue view "$ISSUE_NUM" --repo "$REPO" --json body -q .body | \
  sed "s/PLACEHOLDER_AUTH/#$AUTH_ISSUE_NUM/g" | \
  gh issue edit "$ISSUE_NUM" --repo "$REPO" --body-file -
```

Verify bidirectional linking — every "Blocks: #X" must have a corresponding "Blocked by: #Y" in issue #X. Read `references/cross-linking-patterns.md` for the full wiring protocol.

### P6: Verification

```bash
bash "$SKILL_DIR/scripts/read-tree.sh" "$REPO" ROOT_ISSUE_NUMBER
```

Verify all links, labels, and DoD sections. Present the final tree to the user.

---

## Execute Mode

### E1: Read the plan

```bash
FULL=1 bash "$SKILL_DIR/scripts/read-tree.sh" "$REPO" ROOT_NUMBER
```

Present the tree with open/closed counts per wave.

### E2: Identify current wave

Read `references/wave-execution.md` for detailed wave management.

```bash
for wave in "wave:0-foundation" "wave:1" "wave:2" "wave:3" "wave:4" "wave:5"; do
  count=$(gh issue list --repo "$REPO" -l "$wave" --state open --json number --jq 'length')
  total=$(gh issue list --repo "$REPO" -l "$wave" --state all --json number --jq 'length')
  [ "$total" -gt 0 ] && echo "$wave: $((total - count))/$total closed ($count open)"
done
```

List ready leaf issues — open `type:task` or `type:subtask` issues with no open children, all blockers closed, and no `status:in-progress`, `status:blocked`, `status:failed`, or `status:needs-review` label. Track parent issues separately: when all children close, verify the parent's own DoD and close it.

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

### E3: Dispatch subagents

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
   - DoD is tool-agnostic — no specific editors, test runners, or build tools
   - Body is under 60,000 characters
   - All cross-references (#numbers) point to existing issues

5. Mark in-progress:
   ```bash
   gh issue edit NUMBER --repo "$REPO" --add-label "status:in-progress" --remove-label "status:ready"
   ```

6. Generate the subagent prompt from the issue body — extract Context & Rationale, Strategic Intent, and Definition of Done sections verbatim, then carry Wave & Dependencies as execution context. The prompt must remain tool-agnostic. See `references/generic-prompt-patterns.md`.

7. Dispatch the assembled prompt through the current runtime's native subagent/task tool. Use:
   - description/title: `Execute #NUMBER: SHORT_TITLE`
   - prompt/body: the assembled prompt
   - autonomous worker mode if the runtime exposes mode selection

8. For independent issues in the same wave, dispatch multiple subagents in parallel.

If subagent dispatch is unavailable, stop and return the ready issue list, generated prompts, and label changes for manual execution.

### E4: Completion verification

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

### E5: Wave transition

When all wave issues are closed:

1. Announce completion with summary
2. Read tree again: `bash "$SKILL_DIR/scripts/read-tree.sh" "$REPO" ROOT_NUMBER`
3. Show next wave's ready leaf issues plus any parent issues now eligible for closure
4. **Ask user for confirmation** before proceeding
5. Repeat from E2

**If the wave has partial failures**, read `references/partial-wave-handling.md` for recovery patterns:
- Single failure with no downstream blocks — offer to advance while re-dispatching in parallel
- Single failure blocking next wave — present options (fix, re-dispatch with context, manual investigation)
- Multiple failures — present failure summary table, let user choose strategy
- Never auto-advance past a failed wave without user confirmation

**State recovery:** If the orchestrator session is interrupted, all state is recoverable from GitHub labels and issue states. Re-read the tree and reconstruct from `wave:*` and `status:*` labels.

---

## Decision rules

### Planning
- If a task description exceeds 3 sentences, decompose it into subtasks
- If two tasks have no dependency, they belong in the same wave
- If a subtask would take more than one focused session, split further
- Use `priority:critical` sparingly — only for true blockers within a wave

### Execution
- Dispatch only ready leaf issues (`type:task` or `type:subtask`); parent issues close after their children close and their own DoD is verified
- If an issue has sub-issues, dispatch the child issues separately
- If a subagent fails, comment on the issue and ask the user — do not auto-retry
- Independent issues within a wave dispatch in parallel
- Never modify issue bodies — only add comments
- Verify DoD with evidence before closing

## Reference routing

| File | When to read |
|---|---|
| `references/question-bank.md` | Plan Mode P2 — before asking brainstorming questions |
| `references/issue-body-template.md` | Plan Mode P4 — before writing any issue body |
| `references/label-schema.md` | Plan Mode P3/P4 — when setting up or applying labels |
| `references/body-size-validation.md` | Plan Mode P4 — before every `gh issue create` |
| `references/cross-linking-patterns.md` | Plan Mode P5 — bidirectional linking and verification |
| `references/wave-execution.md` | Execute Mode E2 — detecting ready issues, managing wave transitions |
| `references/subagent-dispatch.md` | Execute Mode E3 — subagent prompt template |
| `references/generic-prompt-patterns.md` | Execute Mode E3 — tool-agnostic prompt writing |
| `references/partial-wave-handling.md` | Execute Mode E5 — recovery patterns for partial failures |

## Guardrails

### Planning
- Do NOT create issues without user approval of the plan tree
- Do NOT skip the brainstorming questions phase
- Do NOT create issues with empty or vague bodies
- Do NOT forget sub-issue wiring after issue creation
- Do NOT create fewer than 3 nesting levels for non-trivial projects
- Every issue body MUST have a Definition of Done with BSV criteria
- Always create issues bottom-up (leaves first)
- Use GraphQL for sub-issue linking via `link-sub-issue.sh`

### Execution
- Do NOT execute without showing the plan tree first
- Do NOT skip wave order — waves are sequential, issues within waves can be parallel
- Do NOT close an issue unless ALL BSV criteria are verifiably met
- Do NOT proceed to next wave without user confirmation
- Do NOT modify issue bodies — only add comments
- Do NOT retry failed issues without user input
- Always read full issue body, sub-issues, and comments before dispatching
- Use `gh` CLI for all GitHub operations, always with `--repo "$REPO"`
