# Generic Prompt Patterns

How to write subagent prompts that work regardless of which AI coding tool executes them. Prompts must be completely tool-agnostic — no mentions of specific editors, IDEs, CLI tools, or agent frameworks.

## Core principle

The issue body IS the prompt. A well-written issue body should be executable by any competent AI coding agent without modification. The agent reading it might be Claude Code, Cursor, Codex, Devin, Windsurf, or a custom droid. The prompt must not assume any specific tool.

## Self-contained prompt requirements

Every prompt must include enough context to execute without additional information:

### 1. Codebase orientation

```markdown
## Context & Rationale

Repository: {owner/repo}
Branch: {branch-name or "main"}

Key files for this task:
- `src/auth/middleware.ts` — authentication middleware (modify)
- `src/routes/login.ts` — login endpoint (create)
- `src/types/auth.ts` — type definitions (read for reference)
- `tests/auth/` — test directory (add tests here)
```

Name specific files but don't paste their contents (they may change between planning and execution). Let the agent read them fresh.

### 2. Bounded scope

Each prompt covers exactly one responsibility. The agent should know:
- What to create or modify
- What NOT to touch
- Where the boundary is

```markdown
## Strategic Intent

- **End-state:** Login endpoint accepts email/password, validates against the users table, returns JWT
- **Hard constraints:** Do not modify the existing registration flow. Do not change the JWT secret configuration. Use the existing database connection pool.
- **Scope boundary:** Only files in `src/auth/` and `src/routes/login.ts`. Do not modify middleware used by other routes.
```

### 3. Generic verification commands

Never specify a test runner, build tool, or linter by name in the DoD. Instead, describe WHAT to verify:

```markdown
## Definition of Done

- [ ] The project's test suite passes with zero failures
- [ ] The project's linter reports zero errors
- [ ] The project's type checker reports zero errors
- [ ] POST /api/login with valid credentials returns HTTP 200 with `access_token` in JSON body
- [ ] POST /api/login with invalid credentials returns HTTP 401 with error message
- [ ] POST /api/login with missing fields returns HTTP 422 with field-level validation errors
```

The agent should discover the correct commands by reading `package.json`, `Makefile`, `pyproject.toml`, or equivalent.

**Anti-pattern — tool-specific:**
```markdown
# BAD — assumes npm + jest
- [ ] `npm test -- --testPathPattern=auth` passes
- [ ] `npx eslint src/auth/` shows no errors
```

**Correct — tool-agnostic:**
```markdown
# GOOD — describes what, not how
- [ ] All tests covering authentication pass without failures
- [ ] No linting errors in modified files
```

### 4. Anti-staleness markers

Prompts are written during planning but executed later. Protect against codebase drift:

```markdown
## Context & Rationale

- **Planned against:** commit {hash} on {date}
- **If the following have changed, halt and report:** `src/auth/middleware.ts` signature, `UserModel` schema, JWT configuration in environment
- **Adaptation guidance:** If the auth module has been refactored since planning, follow the new patterns rather than fighting them. The DoD criteria remain valid regardless of implementation approach.
```

### 5. Completion protocol

Tell the agent exactly how to report completion:

```markdown
## Completion Protocol

When all DoD criteria are met:
1. Verify the project builds without errors
2. Verify all tests pass
3. Verify no linting or type errors in modified files
4. List each DoD criterion with evidence of completion
5. List all files created or modified with a one-line summary of changes
6. Report any deviations from the original plan with rationale
```

## Context injection tiers

Control how much context the prompt provides based on task complexity:

| Tier | Context size | When to use |
|---|---|---|
| Minimal | File paths + scope boundary | Simple, well-isolated tasks |
| Standard | File paths + scope + architectural context | Most tasks |
| Full | File paths + scope + architecture + related issue context | Complex tasks with cross-cutting concerns |

### Standard context template

```markdown
## Context & Rationale

- **Repository:** {owner/repo}
- **What problem this solves:** {specific problem}
- **Why it matters:** {impact}
- **What completion unlocks:** {downstream dependencies}
- **System fit:** This is part of the {feature} feature. Related issues: #{N} (parent), #{M} (sibling). Once complete, #{K} becomes unblocked.

### Architecture context
- The project uses {pattern} for {concern} (see `{file}` for existing example)
- Data models are defined in `{path}` using {approach}
- Tests follow the pattern in `{path}` — co-located with source files
```

## Prompt anti-patterns

| Anti-pattern | Problem | Fix |
|---|---|---|
| Pasting file contents into the prompt | Stale by execution time | List file paths; let agent read fresh |
| Mentioning specific tools | Breaks portability | Describe verification outcomes, not commands |
| Overly broad scope | Agent does too much or too little | Bound explicitly with file paths and "do not touch" list |
| No completion protocol | Agent stops ambiguously | Add explicit completion steps |
| No anti-staleness marker | Prompt assumes state that changed | Add "planned against commit" and "halt if changed" clauses |
| Assuming agent has memory | Different agent may execute | Make every prompt fully self-contained |
| Embedding decisions in DoD | DoD should verify, not prescribe | Put design decisions in Strategic Intent, verification in DoD |
