# Cross-Linking Patterns

Bidirectional dependency wiring between issues. Every dependency must be documented in BOTH directions. Assumes `REPO` is already set and every `gh` command uses `--repo "$REPO"`.

## Core principle

Issue numbers in GitHub are immutable once created. The number `#42` will always refer to the same issue. Cross-references survive renames, label changes, and body edits. Use this immutability as the foundation for all linking.

## Linking types

### 1. Blocked-by / Blocks (dependency)

The blocked issue cannot start until the blocker is closed.

**In the blocked issue body:**
```markdown
## Wave & Dependencies
- **Blocked by:** #23 (auth middleware), #25 (database schema)
- **Blocks:** #30 (integration tests)
```

**In the blocker issue body:**
```markdown
## Wave & Dependencies
- **Blocked by:** none
- **Blocks:** #28 (login endpoint), #29 (API gateway)
```

### 2. Parent / Child (hierarchy)

Sub-issue relationship. Parent closes when all children close.

**In the parent body:**
```markdown
## Children
- #31: Create user model
- #32: Add validation rules
- #33: Write migration
```

**In the child body:**
```markdown
## Wave & Dependencies
- **Parent:** #30 (User management feature)
```

Additionally wire via GraphQL sub-issue API:
```bash
bash "$SKILL_DIR/scripts/link-sub-issue.sh" "$REPO" PARENT_NUM CHILD_NUM
```

### 3. Related (informational)

Issues that share context but have no dependency.

```markdown
## Technical Notes
See also: #45 (similar pattern in payments module), #12 (design decision)
```

### 4. PRD traceability

Link every implementation issue back to its source requirement.

```markdown
## Context & Rationale
- **PRD:** #100 (Feature X PRD)
- **User stories:** US-3, US-7, US-12 from the PRD
```

## Wiring protocol

### Bottom-up creation order

Always create leaf issues first, then wire upward:

```
Step 1: Create all subtasks         → get issue numbers
Step 2: Create tasks (ref subtasks) → get issue numbers
Step 3: Create features (ref tasks) → get issue numbers
Step 4: Create epics (ref features) → get issue numbers
Step 5: Wire sub-issue relationships via GraphQL
Step 6: Edit parent bodies to add real child numbers
```

### Post-creation cross-reference update

After all issues are created, update references that couldn't be set during creation (because the referenced issue didn't exist yet):

```bash
# Pattern: replace placeholder with real number
gh issue view "$ISSUE_NUM" --repo "$REPO" --json body -q .body | \
  sed "s/PLACEHOLDER_AUTH_MIDDLEWARE/#$AUTH_ISSUE/g" | \
  gh issue edit "$ISSUE_NUM" --repo "$REPO" --body-file -
```

### Bidirectional verification

After all wiring, verify every link is bidirectional:

```bash
# For each issue, check that every "Blocks" reference
# has a corresponding "Blocked by" in the target
gh issue view "$NUM" --repo "$REPO" --json body -q .body | \
  awk '/\*\*Blocks:\*\*/ {print}' | \
  grep -oE '#[0-9]+' | tr -d '#' | while read -r target; do
  BLOCKED_BY=$(gh issue view "$target" --repo "$REPO" --json body -q .body | awk '/\*\*Blocked by:\*\*/ {print}')
  if ! echo "$BLOCKED_BY" | grep -q "#$NUM"; then
    echo "MISSING BACKLINK: #$target does not list #$NUM as blocker"
  fi
done
```

## Cross-linking in narrative sections

In addition to the structured Wave & Dependencies section, mention dependencies in the Context & Rationale narrative:

```markdown
## Context & Rationale
- **What problem this solves:** Creates the authentication middleware that the login endpoint (#25) and API gateway (#27) depend on. Without this, no protected routes can function.
- **What completion unlocks:** Unblocks #25 (login), #27 (gateway), and transitively #30 (integration tests).
```

This provides context for WHY the dependency exists, not just THAT it exists.

## Dependency labels

In addition to body references, add dependency information via labels for machine-readable filtering:

```bash
# Mark issue as blocked
gh issue edit "$NUM" --repo "$REPO" --add-label "status:blocked"

# After blocker closes, update status
gh issue edit "$NUM" --repo "$REPO" --remove-label "status:blocked" --add-label "status:ready"
```

## Scale patterns (50+ issues)

For large issue trees, maintain a dependency matrix as a tracking issue:

```markdown
# Dependency Matrix

| Issue | Blocked By | Blocks | Wave | Status |
|---|---|---|---|---|
| #101 | — | #105, #106 | 0 | Open |
| #102 | — | #107 | 0 | Open |
| #105 | #101 | #110 | 1 | Blocked |
| #106 | #101 | #111 | 1 | Blocked |
| #107 | #102 | #112 | 1 | Blocked |
| #110 | #105 | — | 2 | Blocked |
```

Update this matrix as issues close. Label it `type:tracking`.
