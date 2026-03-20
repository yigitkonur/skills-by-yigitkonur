# PRD Decomposition Guide

How to break a finalized PRD into independently-implementable vertical slices for AI agent execution.

## Core principle: vertical slices, not horizontal layers

Break the PRD into **tracer bullet** issues. Each issue is a thin vertical slice that cuts through ALL integration layers end-to-end:

```
GOOD (vertical slice):
  Schema -> API endpoint -> UI component -> Tests
  One thin feature working end-to-end

BAD (horizontal layer):
  "Build all the database models"
  "Build all the API endpoints"
  "Build all the UI components"
  Layers that only work when assembled
```

Each slice should produce a deployable, testable increment. A user (or test) should be able to verify the slice works without any other slices being complete.

## Slice classification

Classify each slice as:

| Type | Meaning | Example |
|---|---|---|
| **AFK** | Can be implemented and merged without human interaction | "Add validation to email field" |
| **HITL** | Requires a human decision, design review, or approval | "Choose authentication provider" |

Prefer AFK over HITL. The more slices that can be autonomously implemented, the faster the project moves.

## Decomposition process

### Step 1: Identify the end-to-end flows
From the PRD's user stories, identify the distinct user flows. Each flow is a candidate for one or more slices.

### Step 2: Find the thinnest possible first slice
The first slice should be the simplest possible end-to-end path:
- Minimal data model (1-2 fields, not the full schema)
- One API endpoint
- Simplest possible UI
- One test proving it works

This establishes the architectural skeleton that subsequent slices flesh out.

### Step 3: Layer complexity incrementally
Each subsequent slice adds one dimension of complexity:
- More data fields
- Error handling for a specific case
- A new user role or permission
- A performance optimization
- An edge case from the PRD

### Step 4: Map dependencies
Some slices depend on others. Create a dependency graph:
```
Slice 1: Basic CRUD (no dependencies)
Slice 2: Validation rules (depends on Slice 1)
Slice 3: Search/filtering (depends on Slice 1)
Slice 4: Permissions (depends on Slice 1)
Slice 5: Bulk operations (depends on Slice 1, 2)
```

### Step 5: Validate with the user
Present the breakdown as a numbered list. For each slice:
- **Title**: Short descriptive name
- **Type**: HITL / AFK
- **Blocked by**: Which slices must complete first
- **User stories covered**: Which user story numbers from the PRD

Ask the user:
1. Does the granularity feel right? (Too coarse → split. Too fine → merge.)
2. Are the dependency relationships correct?
3. Should any slices be merged or split further?
4. Are the correct slices marked as HITL vs AFK?

Iterate until approved.

### Step 6: Create GitHub issues
Create issues in dependency order (blockers first) so you can reference real issue numbers.

**Issue template:**

```markdown
## What to build
{Concise description of this vertical slice. Describe end-to-end behavior, not layer-by-layer implementation. Reference specific sections of the parent PRD rather than duplicating content.}

## Acceptance criteria
- [ ] {Criterion 1}
- [ ] {Criterion 2}
- [ ] {Criterion 3}

## Blocked by
- #{issue-number} {title} (if any)
Or: "None — can start immediately"

## User stories addressed
Reference by number from the parent PRD:
- User story 3
- User story 7

## Parent PRD
#{parent-prd-issue-number}
```

Do NOT close or modify the parent PRD issue.

## Sizing guidance

| Slice size | Signal |
|---|---|
| Too small | "Add field X to the model" (no end-to-end behavior) |
| Just right | "Users can search by name and see results with pagination" (one flow, end-to-end) |
| Too large | "Implement the entire dashboard" (multiple flows, too much to review) |

Target: each AFK slice should represent roughly 5-15 minutes of focused AI agent work, ending with a runnable, testable outcome. If a slice would take longer, split it.

## Phased execution blocks

For complex features, group slices into phases:

**Phase 1: Foundation** (architectural skeleton)
- Slice 1: Basic data model + one endpoint + smoke test
- Slice 2: Core UI shell with routing

**Phase 2: Core functionality**
- Slice 3-6: Individual feature flows

**Phase 3: Polish and edge cases**
- Slice 7-9: Error handling, validation, edge cases

**Phase 4: Non-functional**
- Slice 10-11: Performance, security, accessibility

Each phase should end with a testable checkpoint. Include "DO NOT CHANGE" notes for code that earlier phases established and later phases should not modify.
