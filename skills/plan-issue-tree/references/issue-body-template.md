# Issue Body Template

Every issue created by plan-issue-tree uses this structure. The body doubles as a subagent prompt — run-issue-plan reads it directly to generate agent dispatches.

## Template

```markdown
## Context & Rationale

- **What problem this solves:** [specific problem or gap]
- **Why it matters:** [impact of not solving]
- **What completion unlocks:** [what becomes possible]
- **What non-completion breaks:** [what is blocked without this]
- **System fit:** [relation to adjacent issues and the larger project]

## Strategic Intent

- **End-state:** [observable outcome — what to verify when done]
- **Hard constraints:** [non-negotiable requirements]
- **Known risks:** [what could go wrong]
- **Tradeoffs accepted:** [what we chose not to do and why]

**Ownership:** You own this. Explore freely, trust your judgment, adapt as needed.

## Definition of Done

Every criterion is Binary (done or not), Specific (concrete), Verifiable (third party can confirm):

- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

> You must achieve 100% of every criterion before stopping. Partial = incomplete.

## Wave & Dependencies

- **Wave:** [N]
- **Type:** [epic | feature | task | subtask]
- **Priority:** [critical | high | medium | low]
- **Blocked by:** [#numbers or "none"]
- **Blocks:** [#numbers or "none"]
- **Parent:** [#number or "root"]

## Technical Notes

[Optional — file paths, architecture decisions, API specs. Keep brief.]
```

## By issue type

### Epics

DoD focuses on child completion:

```markdown
- [ ] All child feature issues are closed
- [ ] Integration between features verified
- [ ] [Epic-specific criterion]
```

### Tasks and subtasks

Most important type — these become subagent prompts. Write with maximum specificity:

```markdown
- [ ] File `src/auth/middleware.ts` exports `validateToken(token: string): Promise<boolean>`
- [ ] `npm test -- --testPathPattern=auth` passes with 0 failures
- [ ] POST /api/login with valid credentials returns 200 with `access_token` in body
```

## BSV criteria — good and bad

### Good

- `File src/auth/middleware.ts exports function validateToken`
- `Running npm test -- --testPathPattern=auth passes with 0 failures`
- `POST /api/login with valid credentials returns HTTP 200`
- `The users table has columns: id (uuid), email (varchar unique), created_at (timestamptz)`

### Bad

- `Code is clean` — not specific
- `Tests pass` — which tests? what command?
- `Works correctly` — not verifiable
- `Good performance` — no threshold
- `Follows best practices` — subjective

## Cross-referencing

Mention blocking/blocked issues in both the structured section and the narrative:

> "This task creates the auth middleware (#23) required by the login endpoint (#25) and API gateway (#27)."
