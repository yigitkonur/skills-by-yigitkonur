# REVIEW.md Format and Directives

Complete specification for writing effective `REVIEW.md` files that maximize Devin Bug Catcher accuracy.

---

## File Basics

- **Format**: Pure Markdown. No YAML frontmatter required.
- **Location**: Repository root, or any subdirectory (`**/REVIEW.md` glob)
- **Encoding**: UTF-8
- **Recommended length**: 100–300 lines (under 500 max — verbose files dilute signal)

Devin parses these Markdown elements:

| Element | Usage |
|---------|-------|
| `## H2` / `### H3` headers | Section boundaries — the Bug Catcher uses these to categorize rules |
| Bullet lists (`-` or `*`) | Individual rules within a section |
| Fenced code blocks (`` ``` ``) | Code examples with language tags — used for pattern matching |
| **Bold text** | Emphasis within rules — affects severity weighting |

---

## Recommended Section Order

The Bug Catcher treats content near the top of the file with **higher priority**. Recommended structure:

```
1. Critical Areas / Security    → severe bugs
2. Conventions                  → non-severe bugs
3. Performance                  → investigate flags
4. Patterns (code examples)     → pattern matching reference
5. Ignore                       → noise reduction
6. Testing                      → informational flags
```

### How Sections Map to Finding Classification

| REVIEW.md Section | Bug Catcher Classification | Typical Severity |
|-------------------|---------------------------|------------------|
| **Critical Areas** | Bug | Severe |
| **Security** | Bug | Severe |
| **Conventions** | Bug | Non-severe |
| **Performance** | Flag | Investigate |
| **Testing** | Flag | Informational |
| **Ignore** | Skipped | N/A |

> **Critical vs Security distinction:**
> Critical = repo-specific paths (migration safety, auth flows, payment processing).
> Security = general practices (input validation, secret handling, XSS prevention).
> Place both near the top, but separate them — Critical rules reference *your* codebase paths; Security rules apply universally.

---

## Section Reference

### Critical Areas

What parts of the codebase need extra scrutiny. Be specific about paths and reasoning.

```markdown
## Critical Areas
- All changes to `src/auth/` must be reviewed for security implications — this handles JWT validation and session management.
- Database migration files in `prisma/migrations/` should be checked for backward compatibility and data loss risk.
- Payment processing in `src/billing/` requires review for PCI compliance — no PII in logs, idempotent mutations.
```

**Writing tips:**
- Reference specific directory paths
- Explain **why** the area is critical (helps the Bug Catcher weigh findings)
- Use imperative language: "must be reviewed" over "should be checked"

### Security

Security-specific rules flagged as severe bugs. Place near the top for highest weighting.

```markdown
## Security
- Never interpolate user input into SQL queries. Use parameterized queries via Prisma.
- API keys and secrets must never appear in source code — use environment variables.
- All API routes must check authentication. Never rely on client-side auth alone.
- Sanitize HTML output to prevent XSS. Use DOMPurify for user-generated content.
- Error responses must not leak stack traces, internal paths, or database schema details.
```

**Writing tips:**
- Use absolute language: "never", "must", "always" — these trigger severe bug classification
- Reference specific libraries or patterns from your codebase
- Include the attack vector: "to prevent XSS", "to avoid SQL injection"

### Conventions

Project-specific rules enforced as non-severe bugs. These are the highest-value section — make rules specific and measurable.

```markdown
## Conventions
- API endpoints must validate request bodies using Zod schemas from `src/schemas/`.
- All public functions require explicit TypeScript return types — do not use `any` or implicit returns.
- React components must be functional components with hooks, not class components.
- Use `next/image` for all images — never raw `<img>` tags.
- Use the structured logger (`src/utils/logger`). Never use `console.log` in production code.
```

**Writing tips:**
- Each rule should be independently testable — "Can I look at a diff and determine if this rule is violated?"
- Reference actual paths, libraries, and patterns from your codebase
- Avoid vague rules like "write clean code" or "follow best practices"

### Performance

Patterns to flag as investigate-level warnings.

```markdown
## Performance
- Flag any database queries inside loops — use batch operations instead.
- Watch for N+1 query patterns in API resolvers and serializers.
- Large datasets must be paginated server-side, not fetched all at once.
- Images above the fold must set `priority={true}`. All others should lazy-load.
```

**Writing tips:**
- Describe the anti-pattern and the correct alternative
- Use quantifiable thresholds when possible: "responses over 1MB", "queries taking >100ms"

### Patterns

Good/bad code examples that the Bug Catcher can match against. Use fenced code blocks with language tags.

Use the repo's dominant language for code blocks. Match ecosystem idioms — if the project is Django, write Django examples, not generic Python. If the project is Go with `slog`, show `slog` patterns, not `log.Printf`.

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
  return await db.user.findUnique({ where: { id } }); // no error handling
}
\`\`\`
```

**Writing tips:**
- Always label examples as **Good:** and **Bad:**
- Use your project's actual language and frameworks in examples
- Keep examples focused on one concept — don't mix error handling with validation
- Tag code blocks with the correct language for syntax highlighting

#### Python Examples

**N+1 Queries:**

**Good:**
```python
# Use select_related / prefetch_related to batch queries
users = User.objects.select_related("profile").filter(active=True)
```

**Bad:**
```python
# Bare .all() in a loop causes N+1 queries
for user in User.objects.all():
    print(user.profile.name)  # hits DB every iteration
```

**Bare Except:**

**Good:**
```python
try:
    result = process(data)
except Exception as e:
    logger.error("processing failed", exc_info=e)
    raise
```

**Bad:**
```python
try:
    result = process(data)
except:  # catches KeyboardInterrupt, SystemExit — hides real bugs
    pass
```

**Type Hints:**

**Good:**
```python
def get_user(user_id: int) -> User | None:
    return User.objects.filter(id=user_id).first()
```

**Bad:**
```python
def get_user(user_id):  # no type hints — unclear contract
    return User.objects.filter(id=user_id).first()
```

#### Go Examples

**Error Handling:**

**Good:**
```go
val, err := doSomething()
if err != nil {
    return fmt.Errorf("doSomething context: %w", err)
}
```

**Bad:**
```go
val, _ := doSomething() // error silently ignored
```

**Goroutine Safety:**

**Good:**
```go
g, ctx := errgroup.WithContext(ctx)
for _, item := range items {
    g.Go(func() error {
        return process(ctx, item)
    })
}
if err := g.Wait(); err != nil {
    return err
}
```

**Bad:**
```go
for _, item := range items {
    go func() {
        process(item) // no error handling, no synchronization
    }()
}
```

**Structured Logging:**

**Good:**
```go
slog.Info("request handled", "method", r.Method, "path", r.URL.Path, "status", code)
```

**Bad:**
```go
log.Printf("handled %s %s %d", r.Method, r.URL.Path, code) // unstructured, hard to query
```

> **Steering note:** Focus Good/Bad examples on the top 2–3 risks in your codebase. Don't exhaustively example every rule. If a linter already enforces it, skip the example — the Bug Catcher adds more value on patterns linters can't catch.

### Ignore

Files and patterns the Bug Catcher should skip. Reduces noise from generated files, lock files, and test artifacts.

```markdown
## Ignore
- Auto-generated files in `src/generated/` do not need review.
- Lock files (package-lock.json, yarn.lock, pnpm-lock.yaml) can be skipped unless dependencies changed.
- Migration files in `prisma/migrations/` are auto-generated — only review schema changes.
- Test snapshots in `__snapshots__/` don't need review.
- Build output in `dist/` and `.next/` should never be committed.
```

#### Ignore Format

Patterns use **glob-style** syntax, one per line, relative to the repo root:

| Pattern | What it excludes |
|---------|------------------|
| `*.generated.*` | Generated files (e.g. `types.generated.ts`) |
| `**/migrations/` | Migration directories at any depth |
| `*_test.go` | Go test files |
| `**/__pycache__/` | Python bytecode cache directories |
| `vendor/`, `node_modules/` | Vendored dependencies |

**Writing tips:**
- List actual paths from your repo, not generic patterns
- Qualify when possible: "unless dependencies changed"
- Include generated code paths (ORM clients, GraphQL types, protocol buffers)

### Testing

Testing conventions and coverage expectations. Typically flagged as informational.

```markdown
## Testing
- All new API endpoints must have integration tests.
- Utility functions must have unit tests with edge cases.
- Test files must be co-located with source files (e.g., `utils.test.ts` next to `utils.ts`).
- Auth middleware must be tested: unauthenticated → redirect, unauthorized → 403.
```

---

## Phrasing and Severity

The language you use directly affects how the Bug Catcher classifies findings:

| Phrasing Style | Effect | Example |
|---------------|--------|---------|
| **Imperative + absolute** | Higher severity (severe bug) | "Must never", "Always required", "This MUST be fixed" |
| **Directive** | Medium severity (non-severe bug) | "Use X instead of Y", "Do not use" |
| **Suggestive** | Lower severity (investigate flag) | "Consider using", "Prefer X over Y" |
| **Descriptive** | Informational flag | "This pattern typically indicates", "For reference" |

### Examples of Effective vs Ineffective Rules

| ❌ Vague | ✅ Specific |
|----------|------------|
| "Validate inputs" | "All API endpoints must validate request bodies using Zod schemas from `src/schemas/`" |
| "Handle errors properly" | "Every async function must use try-catch with structured error logging via `src/utils/logger`" |
| "Write tests" | "All new API endpoints must have integration tests covering success, validation error, auth error, and not-found" |
| "Be careful with security" | "Never interpolate user input into SQL queries. Use Prisma's parameterized queries exclusively" |
| "Follow conventions" | "React components must be functional components with hooks, not class components" |

---

## Directory-Scoped REVIEW.md (Monorepos)

Place `REVIEW.md` in subdirectories to scope guidelines to specific packages or services:

```
repo/
├── REVIEW.md                    # Root: applies to all PRs
├── packages/
│   ├── api/
│   │   └── REVIEW.md            # API-specific: auth, validation, error handling
│   ├── payments/
│   │   └── REVIEW.md            # Payments: PCI compliance, idempotency
│   └── frontend/
│       └── REVIEW.md            # Frontend: accessibility, performance
```

### How Scoping Works

- Use the root `REVIEW.md` for cross-cutting concerns that stay true across the repo.
- Use a scoped `REVIEW.md` in `packages/api/` or a similar subtree only for local risks that would otherwise bloat or weaken the root file.
- Write each scoped file so it stands on its own for that subtree's local concerns.
- Devin's docs guarantee directory scoping, but they do not document a deterministic override model for overlapping `REVIEW.md` files. Avoid contradictions and do not rely on precedence to resolve them.
- Keep overlapping files complementary: trim the root if it overreaches, and keep scoped files tightly local.

### Scoping Best Practices

1. **Root file**: Cross-cutting concerns (security basics, general conventions, ignore patterns)
2. **Subdirectory files**: Domain-specific rules (API validation, frontend accessibility, payment compliance)
3. **Keep nesting shallow** — avoid placing `REVIEW.md` more than 3 levels deep
4. **Don't rely on overrides** — if two files would disagree, rewrite them so both can be read together without conflict

---

## Interaction with Other Instruction Files

Devin reads multiple instruction files. Avoid conflicts:

| If you have... | Then in REVIEW.md... |
|---------------|---------------------|
| `CLAUDE.md` | Don't repeat coding standards — focus on review-specific rules |
| `CONTRIBUTING.md` | Don't repeat workflow instructions — focus on what to check in diffs |
| `.cursorrules` or `.windsurfrules` | Don't repeat editor-specific rules — focus on review findings |
| `AGENTS.md` | Don't repeat agent behavior — `REVIEW.md` is for Bug Catcher criteria only |

---

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| 500+ line REVIEW.md | Dilutes signal, slows parsing | Keep under 300 lines; split into scoped files for monorepos |
| Duplicating linter rules | Bug Catcher flags things ESLint already catches | Check `.eslintrc` and CI configs first; only add rules linters miss |
| Generic platitudes | "Write clean code" gives zero signal | Every rule must be specific enough to test against a diff |
| Deep nesting (H4+) | Reduces parsing accuracy | Stick to H2 and H3 headers with flat bullet lists |
| Copy-pasting scenarios | Rules don't match your repo's actual patterns | Adapt every rule to reference real paths, libraries, and conventions |
| Missing Ignore section | Bug Catcher reviews generated files, lock files | Add Ignore section with your repo's actual generated/build paths |

---

## Complete Template

```markdown
# Review Guidelines

## Critical Areas
- [Path-specific areas needing extra scrutiny with reasoning]

## Security
- [Security rules — absolute language triggers severe bug classification]

## Conventions
- [Specific, measurable coding standards — reference actual paths and libraries]

## Performance
- [Anti-patterns to flag — describe the problem and the correct alternative]

## Patterns

### [Pattern Name]
[Description of the pattern]

**Good:**
\`\`\`language
// correct pattern
\`\`\`

**Bad:**
\`\`\`language
// anti-pattern
\`\`\`

## Ignore
- [Files and directories to skip — use actual repo paths]

## Testing
- [Test requirements and conventions]
```
