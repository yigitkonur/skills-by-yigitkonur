---
name: plan-issue-tree
description: Use skill if you are planning a project as GitHub Issues with sub-issues, wave-based execution order, labels, and dependency wiring via the gh CLI.
---

# Plan Issue Tree

Create maximalist, wave-based project plans as GitHub Issue trees with sub-issue nesting (up to 8 levels), labels, and agent-ready issue bodies that follow the subagent prompt protocol.

## Trigger boundary

Use when planning any project, feature, or complex task using GitHub Issues with sub-issues and wave labels.

Do NOT use when:
- Executing an existing issue plan (use `run-issue-plan`)
- Reviewing a PR (use `review-pr`)
- General planning without GitHub Issues

## Prerequisites

```bash
gh auth status
command -v jq >/dev/null
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
SKILL_DIR="/absolute/path/to/plan-issue-tree"  # directory containing this SKILL.md
[ -d "$SKILL_DIR/scripts" ] || {
  echo "Set SKILL_DIR to the absolute path of this skill directory before using helper scripts." >&2
  exit 1
}
EXISTING_LABELS=$(gh label list --repo "$REPO" --limit 200 --json name -q '.[].name')
printf '%s\n' "$EXISTING_LABELS" | grep -E '^(wave:|type:|priority:)' || true
```

`SKILL_DIR` must be the absolute path of the directory that contains this `SKILL.md`. Do **not** assume the target repository also contains the skill. After `REPO` is set, pass `--repo "$REPO"` to every later `gh` command so reads and mutations always target the planned repository.

If wave/type/priority labels are missing, record the missing label names in the draft plan. Do **not** mutate repository labels yet. If the approved plan needs Wave 6 or higher, note the highest wave number and pass it later as `MAX_WAVE=N` when creating labels.

Only after the user approves both the plan tree and the label mutation, run:

```bash
MAX_WAVE="${MAX_WAVE:-5}" bash "$SKILL_DIR/scripts/setup-labels.sh" "$REPO"
```

## Workflow

### Phase 1: Context discovery

1. Detect repo: `gh repo view --json nameWithOwner -q .nameWithOwner`
2. Scan existing issues: `gh issue list --repo "$REPO" --state open --limit 10 --json number,title,labels`
3. Brief codebase scan (README, package.json, entry points)

### Phase 2: Brainstorming questions

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

### Phase 3: Plan design

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

### Phase 4: Issue creation

Create issues **bottom-up** (leaves first) so child IDs exist when wiring parents.

If labels were missing earlier, ask for explicit approval to create them immediately before issue creation. Then run:

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

Read `references/body-size-validation.md` for the full validation sequence. If a body exceeds 60,000 characters, split into parent-stub + child-detail pattern per `references/body-size-validation.md`.

```bash
BODY="$(cat <<'BODY'
[body following subagent protocol]
BODY
)"

# Size check — hard rule
BODY_LENGTH=$(echo -n "$BODY" | wc -c)
if [ "$BODY_LENGTH" -gt 60000 ]; then
  echo "SPLIT REQUIRED: $BODY_LENGTH chars exceeds threshold"
  # Follow split protocol in body-size-validation.md
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

Because `run-issue-plan` reuses the body as the subagent prompt, keep issue bodies tool-agnostic. Put file paths and architecture hints in `Technical Notes`; do not hard-code editor, test-runner, or build-tool commands into the body.

### Phase 5: Sub-issue wiring and cross-linking

After creating all issues, wire relationships in two passes:

**Pass 1 — Sub-issue hierarchy (bottom-up):**

```bash
bash "$SKILL_DIR/scripts/link-sub-issue.sh" "$REPO" PARENT_NUMBER CHILD_NUMBER
```

**Pass 2 — Bidirectional cross-references:**

After all issues exist with real numbers, update bodies that used placeholders:

```bash
gh issue view "$ISSUE_NUM" --repo "$REPO" --json body -q .body | \
  sed "s/PLACEHOLDER_AUTH/#$AUTH_ISSUE_NUM/g" | \
  gh issue edit "$ISSUE_NUM" --repo "$REPO" --body-file -
```

Verify bidirectional linking — every "Blocks: #X" must have a corresponding "Blocked by: #Y" in issue #X. Read `references/cross-linking-patterns.md` for the full wiring protocol and verification commands.

### Phase 6: Verification

```bash
bash "$SKILL_DIR/scripts/read-tree.sh" "$REPO" ROOT_ISSUE_NUMBER
```

Verify all links, labels, and DoD sections. Present the final tree to the user.

## Decision rules

- If a task description exceeds 3 sentences, decompose it into subtasks
- If two tasks have no dependency, they belong in the same wave
- If a subtask would take more than one focused session, split further
- Use `priority:critical` sparingly — only for true blockers within a wave

## Reference routing

| File | When to read |
|---|---|
| `references/question-bank.md` | Before asking brainstorming questions |
| `references/issue-body-template.md` | Before writing any issue body |
| `references/label-schema.md` | When setting up or applying labels |
| `references/body-size-validation.md` | Before every `gh issue create` — validation checklist and split decision tree |
| `references/cross-linking-patterns.md` | During Phase 5 wiring — bidirectional linking, verification, scale patterns |

## Guardrails

- Do NOT create issues without user approval of the plan tree
- Do NOT skip the brainstorming questions phase
- Do NOT create issues with empty or vague bodies
- Do NOT forget sub-issue wiring after issue creation
- Do NOT create fewer than 3 nesting levels for non-trivial projects
- Every issue body MUST have a Definition of Done with BSV criteria
- Always create issues bottom-up (leaves first)
- Use GraphQL for sub-issue linking via `link-sub-issue.sh` — REST POST has known bugs
