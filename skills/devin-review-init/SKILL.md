---
name: devin-review-init
description: Use skill if you are setting up Devin Bug Catcher review behavior with REVIEW.md, AGENTS.md, or repo-specific pull request review instructions.
---

# Devin Review Init

Generate optimal `REVIEW.md` and optionally `AGENTS.md` files by analyzing the actual repository — its structure, tech stack, patterns, documentation, and team conventions — then producing tailored review instruction files that make Devin's Bug Catcher catch real issues.

## What Devin Review Is

Devin Review is an AI code review platform that hooks into GitHub PRs. It:

1. **Reads instruction files** in the repo (`REVIEW.md`, `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `.cursorrules`, `.windsurfrules`, `*.rules`, `*.mdc`)
2. **Analyzes diffs** with the Bug Catcher, classifying findings as **Bugs** (severe/non-severe) or **Flags** (investigate/informational)
3. **Posts reviews** with smart diff organization, copy/move detection, and inline comments synced to GitHub
4. **Supports auto-review** on PR open, push, and ready-for-review events

The critical insight: `REVIEW.md` is the primary mechanism for customizing what Devin's Bug Catcher looks for. Well-written review guidelines make the difference between noise and catching real bugs. Devin reads `REVIEW.md` at any directory level (`**/REVIEW.md`), so you can scope guidelines to subdirectories in monorepos.

## What Makes a Good REVIEW.md

Devin's Bug Catcher uses instruction files as context when analyzing PRs. The more specific and actionable your guidelines are, the more precise the Bug Catcher becomes. Key principles:

1. **Specific over vague** — "All API endpoints must validate request body with Zod" beats "validate inputs"
2. **Actionable** — The developer reading a flag should know exactly what to fix
3. **Prioritized** — Lead with critical areas (security, auth, data integrity) so the Bug Catcher weighs them higher
4. **Code examples help** — Good/bad patterns in fenced code blocks let the Bug Catcher match against actual anti-patterns
5. **Keep it under 500 lines** — Overly verbose files dilute signal and slow AI parsing
6. **Flat structure** — Use H2/H3 headers and bullet lists. Deep nesting reduces parsing accuracy

## Workflow

Follow these four phases in order.

### Phase 1: Explore the Repository

Before writing anything, map the territory. Use tools to answer:

1. **Structure** — Monorepo or single-service? What are the top-level directories?
   ```
   Run: ls -la at root, look for packages/, apps/, services/, src/
   ```
2. **Tech stack** — Languages, frameworks, ORMs, testing tools?
   ```
   Check: package.json, requirements.txt, go.mod, Cargo.toml, pyproject.toml
   Look at: tsconfig.json, .eslintrc, prettier config, Dockerfile
   ```
3. **Existing instruction files** — Does the repo already have REVIEW.md, AGENTS.md, CLAUDE.md, CONTRIBUTING.md, .cursorrules?
   ```
   Search for: REVIEW.md, AGENTS.md, CLAUDE.md, CONTRIBUTING.md, .cursorrules, .windsurfrules
   If they exist, read them — you'll extend rather than replace
   ```
4. **Documentation** — What context files exist?
   ```
   Search for: docs/, architecture.md, ADRs, openapi/, swagger/, prisma/schema.prisma
   ```
5. **Existing linting & CI** — What does the toolchain already catch?
   ```
   Check: .eslintrc, .prettierrc, CI configs, pre-commit hooks
   Don't duplicate what linters already enforce
   ```
6. **Pain points** — Look at recent PRs, issues, and git history for patterns
   ```
   Check: common bug patterns, frequently reverted commits, security incidents
   ```

### Phase 2: Decide File Strategy

**Which files to generate:**

| Situation | Files |
|---|---|
| Single-service repo | Root `REVIEW.md` |
| Monorepo with different review needs per package | Root `REVIEW.md` + scoped `REVIEW.md` in subdirectories |
| Team using Devin for task execution too | Root `REVIEW.md` + `AGENTS.md` |
| Repo already has CLAUDE.md or .cursorrules | Root `REVIEW.md` (complement, don't duplicate existing files) |

**REVIEW.md vs AGENTS.md:**

- `REVIEW.md` — Review-specific guidelines: what to check, what to flag, what to ignore. Read by Bug Catcher during PR analysis.
- `AGENTS.md` — Agent behavior instructions: coding style, architecture decisions, workflow patterns. Read by Devin during task execution (not just reviews).

If the user only mentions review/PR setup, generate `REVIEW.md` only. If they mention Devin task execution or agent behavior, also generate `AGENTS.md`.

### Phase 3: Write the REVIEW.md

Structure the file using these sections. Include only sections relevant to the repo — don't pad with generic filler.

**Recommended section order** (the Bug Catcher weighs content near the top higher):

#### 1. Critical Areas (always include)
What parts of the codebase need extra scrutiny. Be specific about paths and why.
```markdown
## Critical Areas
- All changes to `src/auth/` must be reviewed for security implications — this handles JWT validation and session management.
- Database migration files in `prisma/migrations/` should be checked for backward compatibility and data loss risk.
- Payment processing in `src/billing/` requires review for PCI compliance — no PII in logs, idempotent mutations.
```

#### 2. Conventions (always include)
Project-specific rules the Bug Catcher should enforce. These are the highest-value rules — make them specific and measurable.
```markdown
## Conventions
- API endpoints must validate request bodies using Zod schemas from `src/schemas/`.
- All public functions require explicit TypeScript return types — do not use `any` or implicit returns.
- React components must be functional components with hooks, not class components.
- Use `next/image` for all images — never raw `<img>` tags.
```

#### 3. Security (include if the repo handles auth, user data, or external APIs)
Security-specific rules that the Bug Catcher should flag as severe bugs.
```markdown
## Security
- Never interpolate user input into SQL queries. Use parameterized queries via Prisma.
- API keys and secrets must never appear in source code — use environment variables.
- All API routes must check authentication. Never rely on client-side auth alone.
- Sanitize HTML output to prevent XSS. Use DOMPurify for user-generated content.
```

#### 4. Performance (include if performance-sensitive)
Patterns to flag as investigate-level warnings.
```markdown
## Performance
- Flag any database queries inside loops — use batch operations instead.
- Watch for N+1 query patterns in API resolvers and serializers.
- Large datasets must be paginated server-side, not fetched all at once.
```

#### 5. Patterns (include code examples when the convention isn't obvious)
Good/bad code examples that the Bug Catcher can match against. Use fenced code blocks with clear labels.
```markdown
## Patterns

### Error Handling
Every async function must handle errors explicitly.

**Good:**
\`\`\`typescript
async function getUser(id: string): Promise<User> {
  try {
    return await db.user.findUniqueOrThrow({ where: { id } });
  } catch (error) {
    logger.error('getUser failed', { id, error });
    throw new AppError('USER_NOT_FOUND', { cause: error });
  }
}
\`\`\`

**Bad:**
\`\`\`typescript
async function getUser(id: string) {
  return await db.user.findUnique({ where: { id } }); // no error handling, implicit any return
}
\`\`\`
```

#### 6. Ignore (include to reduce noise)
Files the Bug Catcher should skip.
```markdown
## Ignore
- Auto-generated files in `src/generated/` do not need review.
- Lock files (package-lock.json, yarn.lock, pnpm-lock.yaml) can be skipped unless dependencies changed.
- Migration files in `prisma/migrations/` are auto-generated — only review the schema changes.
- Test snapshots in `__snapshots__/` don't need review.
```

#### 7. Testing (include if the repo has test requirements)
Testing conventions and coverage expectations.
```markdown
## Testing
- All new API endpoints must have integration tests.
- Utility functions must have unit tests with edge cases.
- Test files must be co-located with source files (e.g., `utils.test.ts` next to `utils.ts`).
```

### Phase 4: Validate and Output

**Before outputting, verify:**

- [ ] `REVIEW.md` is under 500 lines (ideally 100-300)
- [ ] No duplicate rules that existing linters already catch
- [ ] Rules are specific and measurable, not vague platitudes
- [ ] Critical/security sections are near the top
- [ ] Code examples use the repo's actual language and framework patterns
- [ ] Ignore patterns match the repo's actual generated/build directories
- [ ] If CLAUDE.md or .cursorrules exist, REVIEW.md doesn't repeat their content
- [ ] Monorepo subdirectory REVIEW.md files don't repeat root-level rules

**Output format:**

For every configuration you produce, include:

1. **File tree** showing exactly which files go where and what each is for
2. **Each file** as a complete markdown code block
3. **Reasoning annotations** after each file explaining WHY each major section was included, referencing specific repo context
4. **Verification step** — how to test the config works (open a test PR, use `@greptileai review` equivalent, or check the Devin Review dashboard)

## Reference Files

Read these when you need detailed specifications or examples:

- **`references/review-spec.md`** — Complete reference for REVIEW.md format, AGENTS.md format, all instruction files Devin reads, auto-review configuration, and Bug Catcher behavior. Read this when you need to check what Devin supports or how findings are classified.

- **`references/scenarios.md`** — Complete example REVIEW.md files for different stack types (TypeScript backend, Next.js, Python Django, Tauri, MCP server, monorepo). Read these for inspiration, but always adapt to the actual repository — never copy verbatim.

## Key Gotchas

- `REVIEW.md` is read from **any directory level** (`**/REVIEW.md`) — use this for monorepo scoping
- Devin also reads `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `.cursorrules`, `.windsurfrules`, `*.rules`, `*.mdc` — check for conflicts
- Auto-review triggers on PR open, push to PR, and when a draft is marked ready
- The Bug Catcher classifies findings as: **Bugs** (severe, non-severe) and **Flags** (investigate, informational)
- Keep REVIEW.md focused on review concerns — put coding/architecture standards in AGENTS.md or CLAUDE.md instead
- Custom review rule file paths can be configured in Settings > Review, but `**/REVIEW.md` is always read by default
