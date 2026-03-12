# Writing Effective Instructions

How to write high-quality Copilot code review instructions that produce actionable, relevant review comments. Covers rule quality criteria, section ordering, formatting, character budgeting, and code examples.

## Table of Contents

1. [Rule Quality Criteria](#rule-quality-criteria)
2. [Section Ordering](#section-ordering)
3. [Formatting That Works](#formatting-that-works)
4. [Writing copilot-instructions.md](#writing-copilot-instructionsmd)
5. [Writing Scoped *.instructions.md](#writing-scoped-instructionsmd)
6. [Code Examples](#code-examples)
7. [Character Budget Strategy](#character-budget-strategy)
8. [Rule Categories](#rule-categories)
9. [What NOT to Write](#what-not-to-write)
10. [Iteration Workflow](#iteration-workflow)

---

## Rule Quality Criteria

Every rule must pass all four criteria:

### 1. Specific
State exactly what to check. Copilot cannot interpret vague guidance.

```
❌ "Handle errors properly"
✅ "All API handlers must wrap async operations in try-catch and return structured error responses using AppError class"
```

### 2. Measurable
A reviewer (human or AI) should be able to determine pass/fail unambiguously.

```
❌ "Write good tests"
✅ "New API endpoints must have at least one test covering the success path and one test covering the primary error path"
```

### 3. Actionable
The developer must know exactly what to fix if the rule is violated.

```
❌ "Follow best practices"
✅ "Use parameterized queries for all database operations — no string concatenation or template literals in SQL"
```

### 4. Semantic
The rule should require understanding intent, not just pattern matching. If a linter can catch it, the linter should handle it.

```
❌ "Use 2-space indentation" (linter rule)
✅ "Server Components must not import from @/lib/client-utils — use @/lib/server-utils instead" (architectural rule)
```

---

## Section Ordering

Content near the top of each file carries more weight with Copilot. Order sections by priority:

1. **Security-critical rules** — Injection, secrets, authentication
2. **Architecture/structural requirements** — Layer boundaries, import restrictions
3. **Error handling patterns** — Try-catch, error types, logging
4. **Code quality conventions** — Naming, function size, dead code
5. **Performance considerations** — N+1 queries, pagination, caching
6. **Testing expectations** — Coverage requirements, test patterns

### Template

````markdown
---
applyTo: "**/*.{ts,tsx}"
---

# [Technology/Domain] Review Guidelines

## Security

- [Highest priority rules first]

## Architecture

- [Structural requirements]

## Error Handling

- [Error patterns and conventions]

```code
// Example
```

## Code Quality

- [Conventions and standards]

## Performance

- [Performance considerations]

## Testing

- [Test expectations]
````

---

## Formatting That Works

### Effective formatting

| Format | Why it works |
|---|---|
| H2 headers (`##`) | Copilot uses these as section boundaries for context |
| Bullet points | Scannable, concise — more rules per character |
| Fenced code blocks | Copilot matches these against PR diffs |
| Bold text | Draws attention to key terms and emphasis |
| Short imperative directives | "Use X" is clearer than "Consider using X" |
| Simple 2-column tables | Good for pattern comparisons |

### Ineffective formatting

| Format | Why it fails |
|---|---|
| Deep nesting (H4, H5) | Reduces parsing accuracy |
| Long narrative paragraphs | Hard to parse, wastes characters |
| Tables with many columns | Complex tables confuse processing |
| HTML tags | Not processed meaningfully |
| Images or diagrams | Cannot be interpreted |
| Markdown links to external URLs | Copilot cannot follow links |

### Writing style

- **Imperative mood:** "Use", "Check", "Flag", "Require" — not "It would be good to consider"
- **One rule per bullet:** Each bullet should be a single, atomic directive
- **Front-load the action:** Start with what to do, then add context if needed
- **Avoid hedging:** "Must validate" not "Should try to validate when possible"

---

## Writing copilot-instructions.md

The repository-wide file should contain ONLY rules that genuinely apply to ALL code:

### Include

- Security fundamentals (no hardcoded secrets, input validation, no SQL injection)
- Cross-cutting error handling philosophy (structured logging, no swallowed errors)
- Universal naming conventions (only if consistent across all languages in repo)
- Performance red flags (N+1 queries, missing pagination, unbounded queries)
- Testing philosophy (new features need tests, test naming conventions)
- Documentation expectations (public API docs, changelog updates)

### Exclude

- Language-specific rules (TypeScript types, Python imports) → scoped files
- Framework-specific rules (React hooks, Next.js routing) → scoped files
- Path-specific rules (API validation, database migrations) → scoped files
- Style/formatting rules that linters enforce → linter config
- Build or CI commands → CI pipeline

### Example

```markdown
# Code Review Standards

## Security

- Check for hardcoded secrets, API keys, or credentials in any file
- Verify input validation on all external boundaries (API inputs, form data, URL params)
- Look for SQL injection via raw queries or string interpolation
- Review authentication checks on mutating endpoints

## Error Handling

- All async operations must have error handling (try-catch or propagation)
- Never expose internal error details or stack traces in responses
- Use structured logging: { error, requestId, userId, action }
- Never silently swallow errors with empty catch blocks

## Performance

- Flag N+1 database queries (queries inside loops)
- List endpoints must have pagination — no unbounded queries
- Flag synchronous operations that should be async

## Code Quality

- Functions should be focused and under 50 lines
- Remove dead code and unused imports
- No commented-out code in production
```

---

## Writing Scoped *.instructions.md

### Structure

1. YAML frontmatter with `applyTo` (and optionally `excludeAgent`)
2. H1 title describing the scope
3. Optional one-line purpose statement
4. H2 sections ordered by priority
5. 1-2 code examples per file
6. Total under 4,000 characters (aim for 2,500-3,500)

### Per-language files

Focus on language-specific idioms the linter doesn't catch:

````markdown
---
applyTo: "**/*.{ts,tsx}"
---

# TypeScript Review Guidelines

## Type Safety

- Avoid `any` — use `unknown`, generics, or specific types
- Define interfaces for all object shapes passed between functions
- Use strict null checks: handle `null`/`undefined` explicitly
- Prefer `as const` for literal types over type assertions

```typescript
// Avoid
function fetchUser(id: any): any {
  return db.query(`SELECT * FROM users WHERE id = ${id}`);
}

// Prefer
interface User { id: string; name: string; email: string; }
async function fetchUser(id: string): Promise<User | null> {
  return db.user.findUnique({ where: { id } });
}
```

## Error Handling

- Use typed error classes extending AppError, not raw Error
- Async functions must have try-catch or propagate errors explicitly
- Never silently swallow errors with empty catch blocks
````

### Per-framework files

Focus on framework-specific patterns and architectural rules:

````markdown
---
applyTo: "**/*.{tsx,jsx}"
---

# React Review Guidelines

## Component Architecture

- Prefer function components with hooks over class components
- Custom hooks must start with `use` and accept an options object as the last parameter
- Server Components must not import from client-only modules

## State Management

- Use `useState` for local state, context for cross-component state
- Avoid prop drilling beyond 2 levels — use context or composition
- Memoize expensive computations with `useMemo`, not inline calculations

```tsx
// Avoid
function Dashboard({ data }: Props) {
  const sorted = data.sort((a, b) => a.date - b.date); // sorts on every render

// Prefer
function Dashboard({ data }: Props) {
  const sorted = useMemo(() => [...data].sort((a, b) => a.date - b.date), [data]);
```
````

### Per-domain files

Focus on domain-specific requirements:

````markdown
---
applyTo: "**/api/**/*.{ts,js}"
---

# API Route Review Guidelines

## Request Validation

- All endpoints must validate request bodies before processing
- Use Zod schemas for validation — no manual type checking
- Return 400 with structured error messages for invalid input

## Authentication

- Every mutating endpoint must call `requireAuth()` before data access
- Check authorization (role/permission) after authentication
- Never trust client-supplied user IDs — use the authenticated session

## Response Format

- Return consistent response envelopes: { data, error, meta }
- Include pagination metadata for list endpoints: { page, pageSize, total }
- Use appropriate HTTP status codes (201 for creation, 204 for deletion)
````

---

## Code Examples

### When to include examples

- Rules involving specific patterns (show the pattern)
- Before/after comparisons (show what to flag vs what to suggest)
- Complex architectural rules (show the correct structure)

### Example format

Use fenced code blocks with the language identifier. Show "Avoid" and "Prefer" patterns:

````markdown
```typescript
// Avoid
const result = await db.query(userInput);

// Prefer
const result = await prisma.user.findUnique({ where: { id: validated.id } });
```
````

### Character-efficient examples

- Use the repo's actual patterns, not generic code
- Keep examples to 4-8 lines (avoid vs prefer combined)
- One example per concern — don't over-illustrate

---

## Character Budget Strategy

With 4,000 characters per file, budget carefully:

| Component | Approximate characters |
|---|---|
| Frontmatter | 30-50 |
| H1 title + purpose | 50-100 |
| H2 section headers (4-6) | 100-200 |
| Rules (15-20 bullets) | 1,200-1,800 |
| Code examples (1-2) | 400-800 |
| **Total** | **1,780-2,950** |

### If approaching 4,000 characters

1. Remove low-priority sections (usually testing or performance)
2. Shorten code examples (4 lines instead of 8)
3. Combine related rules into single bullets
4. Split into two files with narrower `applyTo` scopes
5. Move examples to a separate companion file if needed

---

## Rule Categories

Use this classification to ensure coverage without redundancy:

| Category | Belongs in | Examples |
|---|---|---|
| Security | copilot-instructions.md + security.instructions.md | Injection, secrets, auth checks |
| Architecture | Scoped files per layer | Layer boundaries, import restrictions |
| Error handling | copilot-instructions.md (universal) + scoped (patterns) | Try-catch, error types, logging |
| Naming | copilot-instructions.md (if universal) | Conventions, casing rules |
| Performance | copilot-instructions.md (universal flags) | N+1, pagination, caching |
| Testing | testing.instructions.md | Coverage, patterns, fixtures |
| Accessibility | a11y.instructions.md | ARIA, keyboard nav, contrast |
| Framework idioms | Per-framework scoped files | Hooks, routing, state management |

---

## What NOT to Write

### Rules linters already enforce

If ESLint, Prettier, Black, rustfmt, or similar tools are configured, skip:
- Indentation and spacing
- Semicolons and comma rules
- Import sorting
- Bracket placement
- Quote style

These waste your 4,000-character budget on rules that add no value.

### Copilot behavior modifications

These are silently ignored:
- "Use bold text for critical issues"
- "Add emoji severity indicators"
- "Rate code quality on a 1-10 scale"
- "Include a summary table"
- "Block merge if issues are found"

### Vague directives

These produce no actionable review comments:
- "Write clean code"
- "Follow best practices"
- "Be more careful"
- "Improve code quality"

### External references

Copilot cannot follow links. Instead of:
```
Follow our style guide at https://wiki.company.com/style
```

Copy the relevant rules directly into the instruction file.

---

## Iteration Workflow

Instructions are not write-once. Use this cycle:

### Step 1: Start minimal
Begin with 10-20 focused rules across 3-5 files. Resist the urge to cover everything.

### Step 2: Test with a real PR
Open a PR that touches files matching your `applyTo` patterns. Request Copilot review.

### Step 3: Evaluate results
- Which instructions produced relevant comments? Keep them.
- Which were ignored? Rewrite for specificity or move them higher in the file.
- Which produced false positives? Add nuance or remove.

### Step 4: Refine incrementally
Add 2-3 rules per iteration. This lets you attribute changes in review quality to specific rules.

### Step 5: Monitor over time
Review comments across 10+ PRs before declaring instructions "stable." Copilot is non-deterministic — single-PR results are not reliable.


---

## SMSA Quality Checklist

Use this checklist to evaluate every rule before including it in an instruction file. A rule must pass all four criteria.

### Specific

The rule names the exact pattern, function, or construct it applies to.

| Pass | Fail |
|---|---|
| Flag any `useEffect` that calls a fetch function without AbortController cleanup | Avoid side effects in components |
| When a Prisma `findMany` lacks a `take` or `where` clause, flag it as an unbounded query | Be careful with database queries |
| If a Go function returns an error, the caller must check it before proceeding | Handle errors properly |

### Measurable

Copilot can decide yes or no for each diff hunk without subjective judgment.

| Pass | Fail |
|---|---|
| Functions must not exceed 50 lines | Keep functions short |
| Every API endpoint must validate input with a Zod schema | Validate inputs |
| Test files must use `describe`/`it` blocks, not standalone `test()` calls | Write good tests |

### Actionable

The rule tells the reviewer what to do when the pattern is found.

| Pass | Fail |
|---|---|
| Flag as a security issue: any SQL query built with string concatenation | SQL injection is bad |
| Suggest wrapping with `ErrorBoundary` when a client component has no error handling | Components should handle errors |

### Semantic

The rule addresses architecture, security, correctness, or logic — not formatting or style.

| Pass | Fail |
|---|---|
| When a route handler accesses user data, verify the request includes authentication middleware | Use auth middleware |
| Never store secrets in environment variables prefixed with `NEXT_PUBLIC_` | Keep secrets safe |
| Flag any `console.log` left in production code paths | Use consistent logging (linter territory — drop this) |
| Use 2-space indentation | Formatting rule, not semantic (linter territory — drop this) |

---

## Recurring Theme Discovery Recipe

To find recurring review themes in a repository, use this systematic approach rather than guessing:

### Where to look

1. **Recent PRs** (most valuable): Look at the last 10–20 merged PRs for reviewer comments that repeat
2. **Open issues**: Search for labels like `bug`, `security`, `performance`, or `tech-debt`
3. **Code comments**: grep for `TODO`, `FIXME`, `HACK`, `XXX` for known pain points
4. **CONTRIBUTING.md**: Teams often document conventions they want enforced
5. **CI failures**: Repeated test failures or lint issues point to common mistakes

### Shell recipe for theme discovery

```bash
# Find TODO/FIXME/HACK comments as pain point signals
grep -rn "TODO\|FIXME\|HACK\|XXX" src/ --include="*.ts" | head -30

# Find error handling patterns (or lack thereof)
grep -rn "catch" src/ --include="*.ts" | head -20

# Find security-sensitive patterns
grep -rn "dangerouslySetInnerHTML\|eval(\|innerHTML" src/ --include="*.ts" | head -10
```

### When to stop

You have found enough themes when you can list 5–10 concrete patterns that a reviewer should flag. If you cannot find 5 after checking all sources above, the repository may not need many custom rules — keep the instruction set small.

---

## Concept Overlap vs Rule Duplication

Two instruction files may reference the same concept (e.g., error handling, authentication) without being duplicates. Use this test:

### It is additive overlap (acceptable)

- Root file says: "Always return structured error responses with a code, message, and optional details field"
- API file says: "Use the `ApiError` class from `src/errors.ts` for all API route error responses, with HTTP status codes matching the error type"
- These are complementary: the root sets the principle, the scoped file specifies the implementation

### It is duplication (fix it)

- Root file says: "Always validate request input with Zod schemas"
- API file says: "Validate all API inputs with Zod schemas before processing"
- These say the same thing. Keep it in whichever file has the narrower scope and remove from the other.

### It is a contradiction (fix immediately)

- Root file says: "Use try-catch for all async operations"
- Utility file says: "Prefer Result types over try-catch for error propagation"
- These conflict. Narrow the scopes so they do not overlap, or align the guidance.
