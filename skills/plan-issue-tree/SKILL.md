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
- General planning without GitHub Issues (use `plan-work`)

## Prerequisites

```bash
gh auth status
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
gh label list --limit 100 --json name -q '.[].name' | head -20
```

If wave/type/priority labels are missing:

```bash
bash {baseDir}/scripts/setup-labels.sh "$REPO"
```

## Workflow

### Phase 1: Context discovery

1. Detect repo: `gh repo view --json nameWithOwner -q .nameWithOwner`
2. Scan existing issues: `gh issue list --state open --limit 10 --json number,title,labels`
3. Brief codebase scan (README, package.json, entry points)

### Phase 2: Brainstorming questions

Ask **3-5 questions** with **multiple-choice options** (5-20 per question). Users answer in compact form: `1b,2d,3g,4a,5c`.

Read `references/question-bank.md` to select context-appropriate questions. Always cover:
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

### Phase 3: Plan design

Based on answers, design the full issue tree:

1. **Map waves** — group work into sequential waves. Wave 0 is always foundation.
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

Wait for user approval before creating issues.

### Phase 4: Issue creation

Create issues **bottom-up** (leaves first) so child IDs exist when wiring parents.

**Before every `gh issue create`**, validate the body:
1. Character count must be under 60,000 (GitHub limit: 65,536; buffer for post-creation edits)
2. All four required sections present (Context & Rationale, Strategic Intent, Definition of Done, Wave & Dependencies)
3. No vague DoD criteria ("tests pass", "works correctly", "code is clean")
4. All cross-referenced issue numbers exist

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

ISSUE_NUM=$(gh issue create \
  -t "Issue title" \
  -l "wave:1,type:task,priority:high" \
  -b "$BODY" --json number -q .number)
```

Read `references/issue-body-template.md` for the body format. Every body contains:
- **Context & Rationale** — what, why, what it unlocks
- **Strategic Intent** — end-state, constraints, risks, ownership grant
- **Definition of Done** — BSV checklist (Binary, Specific, Verifiable)
- **Wave & Dependencies** — wave number, blocks/blocked-by

### Phase 5: Sub-issue wiring and cross-linking

After creating all issues, wire relationships in two passes:

**Pass 1 — Sub-issue hierarchy (bottom-up):**

```bash
bash {baseDir}/scripts/link-sub-issue.sh "$REPO" PARENT_NUMBER CHILD_NUMBER
```

**Pass 2 — Bidirectional cross-references:**

After all issues exist with real numbers, update bodies that used placeholders:

```bash
gh issue view $ISSUE_NUM --json body -q .body | \
  sed "s/PLACEHOLDER_AUTH/#$AUTH_ISSUE_NUM/g" | \
  xargs -0 gh issue edit $ISSUE_NUM --body
```

Verify bidirectional linking — every "Blocks: #X" must have a corresponding "Blocked by: #Y" in issue #X. Read `references/cross-linking-patterns.md` for the full wiring protocol and verification commands.

### Phase 6: Verification

```bash
bash {baseDir}/scripts/read-tree.sh "$REPO" ROOT_ISSUE_NUMBER
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
