# Issue Size Management

How to handle GitHub's 65,536-character issue body limit when decomposing PRDs into issues.

## Hard limit

GitHub enforces a **65,536 character** limit on issue bodies. This applies identically across:
- REST API (`POST /repos/{owner}/{repo}/issues`)
- GraphQL API (`createIssue` mutation)
- Web UI (browser editor)

Exceeding the limit silently truncates content. There is no warning.

## Pre-creation size check

Before every `gh issue create`, measure the body:

```bash
BODY_LENGTH=$(echo -n "$BODY" | wc -c)
if [ "$BODY_LENGTH" -gt 60000 ]; then
  echo "WARNING: Body is $BODY_LENGTH chars (limit: 65536). Split required."
fi
```

Use **60,000** as the threshold (not 65,536) to leave buffer for cross-reference edits after creation.

## Split strategy: parent-stub + child-detail

When a body exceeds 60,000 characters, split into a lightweight parent stub and detail-carrying children.

### Parent stub pattern (< 2,000 chars)

```markdown
## Scope Summary

{2-3 sentence overview of this issue's scope}

## Children (full details)

- #CHILD_1: {title} — {one-line scope}
- #CHILD_2: {title} — {one-line scope}
- #CHILD_3: {title} — {one-line scope}

## Definition of Done

- [ ] All child issues closed
- [ ] Integration between children verified
- [ ] {Parent-level criterion if any}

## Wave & Dependencies

- **Wave:** {N}
- **Blocked by:** {#numbers or "none"}
- **Blocks:** {#numbers or "none"}
```

### Child detail pattern

Each child carries the full context for its portion:

```markdown
## Context & Rationale

- **Parent:** #{PARENT_NUMBER}: {parent title}
- **Scope boundary:** {what this child covers vs siblings}
- **What problem this solves:** {specific to this child}
...rest of standard issue body template...
```

### Split heuristics

Split along these boundaries (in priority order):

1. **By user story group** — each child covers 2-3 related user stories
2. **By vertical slice** — each child is one end-to-end flow
3. **By module boundary** — each child covers one module's changes
4. **By DoD section** — if DoD alone exceeds limits, split into verification phases

Never split mid-section. Always split at a semantic boundary.

## Character budget per section

Target budgets for a single issue body:

| Section | Target | Max |
|---|---|---|
| Context & Rationale | 2,000 | 5,000 |
| Strategic Intent | 1,000 | 3,000 |
| Definition of Done | 3,000 | 10,000 |
| Wave & Dependencies | 500 | 1,000 |
| Technical Notes | 2,000 | 5,000 |
| **Total** | **8,500** | **24,000** |

If any section exceeds its max, that section needs extraction into a child issue or a linked document.

## Cross-referencing after split

After creating all children, edit the parent to add real issue numbers:

```bash
PARENT_BODY=$(gh issue view $PARENT --json body -q .body)
UPDATED=$(echo "$PARENT_BODY" | sed "s/CHILD_1_PLACEHOLDER/#$CHILD_1_NUM/g")
gh issue edit $PARENT --body "$UPDATED"
```

## PRD-to-issue traceability at scale

For projects with 50+ issues, create a traceability issue:

```markdown
# PRD Traceability: {Feature Name}

| PRD Section | User Story | Issue | Wave | Status |
|---|---|---|---|---|
| 5.1 Authentication | US-1: Login flow | #101 | wave:1 | Open |
| 5.1 Authentication | US-2: OAuth | #102 | wave:1 | Open |
| 5.2 Dashboard | US-3: Overview | #110 | wave:2 | Open |
| 5.2 Dashboard | US-4: Filters | #111 | wave:2 | Open |
```

This issue is labeled `type:tracking` and is never closed until the project is complete.
