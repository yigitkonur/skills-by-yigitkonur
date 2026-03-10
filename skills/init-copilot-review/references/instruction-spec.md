# Copilot Code Review Instruction Specification

Complete reference for GitHub Copilot code review instruction file formats, capabilities, and constraints.

## Table of Contents

1. [File Types and Locations](#file-types-and-locations)
2. [copilot-instructions.md Format](#copilot-instructionsmd-format)
3. [*.instructions.md Format](#instructionsmd-format)
4. [applyTo Frontmatter and Glob Syntax](#applyto-frontmatter-and-glob-syntax)
5. [Character Limit](#character-limit)
6. [Section Structure Best Practices](#section-structure-best-practices)
7. [Supported vs Unsupported Features](#supported-vs-unsupported-features)
8. [Precedence and Cascading](#precedence-and-cascading)

---

## File Types and Locations

Copilot code review reads two types of instruction files:

| File | Location | Scope | Requires Frontmatter |
|---|---|---|---|
| `copilot-instructions.md` | `.github/copilot-instructions.md` | All files in repository | No |
| `*.instructions.md` | `.github/instructions/*.instructions.md` | Files matching `applyTo` pattern | Yes — `applyTo` required |

**Directory structure:**
```
.github/
├── copilot-instructions.md              # Repository-wide (applied to all files)
└── instructions/
    ├── typescript.instructions.md        # Scoped to TS files
    ├── python.instructions.md            # Scoped to Python files
    ├── react.instructions.md             # Scoped to React components
    ├── api.instructions.md               # Scoped to API routes
    ├── security.instructions.md          # Scoped to auth/payment paths
    └── testing.instructions.md           # Scoped to test files
```

**Important:** `*.instructions.md` files MUST be in `.github/instructions/` directory. Files in other locations are ignored by Copilot code review.

---

## copilot-instructions.md Format

Plain markdown. No frontmatter required. Applied to every file in the repository.

```markdown
# General Code Review Standards

## Security Critical Issues

- Check for hardcoded secrets, API keys, or credentials
- Look for SQL injection and XSS vulnerabilities
- Verify proper input validation and sanitization

## Code Quality

- Functions should be focused and under 50 lines
- Use descriptive naming conventions
- Ensure proper error handling

## Performance

- Identify N+1 database query problems
- Check for memory leaks and resource cleanup
```

**Best practice:** Only include rules that genuinely apply to ALL code. Language-specific, framework-specific, and path-specific rules belong in `*.instructions.md` files.

---

## *.instructions.md Format

Requires YAML frontmatter with `applyTo` property. Applied only to files matching the glob pattern.

````markdown
---
applyTo: "**/*.{ts,tsx}"
---

# TypeScript Standards

## Type Safety

- Avoid `any` type — use `unknown` or specific types
- Define interfaces for all object shapes
- Use strict null checks

```typescript
// Avoid
function process(data: any) { return data.value; }

// Prefer
interface DataShape { value: string; }
function process(data: DataShape): string { return data.value; }
```
````

**File naming convention:** `kebab-case.instructions.md`
- `typescript.instructions.md` (language)
- `react-components.instructions.md` (framework)
- `api-routes.instructions.md` (domain)
- `packages-api.instructions.md` (monorepo package)

---

## applyTo Frontmatter and Glob Syntax

The `applyTo` value is a **single glob string** (not an array). It determines which changed files in a PR will have this instruction file applied.

### Frontmatter syntax

```yaml
---
applyTo: "**/*.{ts,tsx}"
---
```

The YAML must be:
- At the very top of the file (no blank lines before `---`)
- Valid YAML between the two `---` delimiters
- The `applyTo` value must be a quoted string

### Common glob patterns

| Pattern | Matches |
|---|---|
| `**/*.ts` | All TypeScript files |
| `**/*.{ts,tsx}` | TypeScript and TSX files |
| `**/*.{ts,tsx,js,jsx}` | All JS/TS files |
| `**/*.py` | All Python files |
| `**/*.rs` | All Rust files |
| `**/*.go` | All Go files |
| `**/*.cs` | All C# files |
| `**/*.{rb,erb}` | Ruby and ERB template files |
| `**/*.java` | All Java files |
| `**/*.{yml,yaml}` | All YAML files |
| `src/components/**/*.{tsx,jsx}` | Components directory only |
| `**/api/**/*.{ts,js}` | API directories anywhere in tree |
| `**/app/**/*.{ts,tsx}` | Next.js App Router files |
| `**/src-tauri/**/*.rs` | Tauri Rust backend |
| `**/*.{test,spec}.{ts,tsx,js,jsx}` | Test files |
| `**/test_*.py` | Python test files |
| `**/.github/workflows/**/*.yml` | GitHub Actions workflows |
| `**/Dockerfile*` | Dockerfiles |
| `packages/api/**/*` | Specific monorepo package |
| `**/migrations/**/*.{sql,py,ts}` | Database migration files |

### Glob syntax reference

| Syntax | Meaning |
|---|---|
| `*` | Match any characters except `/` |
| `**` | Match any characters including `/` (recursive) |
| `?` | Match single character except `/` |
| `{a,b,c}` | Match any of the alternatives |
| `[abc]` | Match any character in the set |
| `[!abc]` | Match any character NOT in the set |

### Scoping strategies

**Broad language scope** — For general language rules:
```yaml
applyTo: "**/*.{ts,tsx,js,jsx}"
```

**Framework-specific scope** — For framework conventions:
```yaml
applyTo: "src/components/**/*.{tsx,jsx}"
```

**Directory-specific scope** — For architecture rules:
```yaml
applyTo: "packages/api/**/*"
```

**Critical path scope** — For security-sensitive areas:
```yaml
applyTo: "**/auth/**/*.{ts,js}"
```

---

## Character Limit

**Copilot code review reads only the first 4,000 characters of any instruction file.** Content beyond this limit is silently ignored — there is no warning.

This limit applies to:
- `copilot-instructions.md`
- Every individual `*.instructions.md` file

This limit does NOT apply to:
- Copilot Chat
- Copilot coding agent

### Practical implications

- Aim for **2,500–3,500 characters** per file to leave safety margin
- Put highest-priority rules at the top of each file
- If a concern needs more space, split into two files with narrower `applyTo` scopes
- Code examples consume characters quickly — keep them concise
- Prefer bullet points over prose paragraphs (more rules per character)

### Measuring characters

Count characters including markdown formatting, whitespace, and frontmatter:
```bash
wc -c .github/instructions/typescript.instructions.md
```

The frontmatter (`---\napplyTo: "..."\n---\n`) counts toward the 4,000-character limit.

---

## Section Structure Best Practices

### Recommended template

````markdown
---
applyTo: "**/*.{ts,tsx}"
---

# [Technology/Domain] Review Guidelines

## Purpose

One-line statement of what this file covers.

## [Highest Priority Concern]

- Rule 1
- Rule 2

```code
// Example
```

## [Second Priority Concern]

- Rule 1
- Rule 2

## [Third Priority Concern]

- Rule 1
- Rule 2
````

### Formatting that works well

- **H2 headers** (`##`) to separate topics — Copilot uses these as section boundaries
- **Bullet points** for individual rules — scannable and concise
- **Fenced code blocks** for examples — Copilot matches these against PR diffs
- **Bold text** for emphasis on key terms — draws attention to important concepts
- **Short imperative directives** — "Use X" not "It would be good to consider using X"

### Formatting that doesn't help

- Deep nesting (H4, H5 headers reduce parsing accuracy)
- Long narrative paragraphs
- Tables with many columns (simple 2-column tables are fine)
- HTML tags
- Images or diagrams

---

## Supported vs Unsupported Features

### What Copilot code review CAN do with instructions

| Capability | Example |
|---|---|
| Check for specific code patterns | "All API endpoints must validate with Zod" |
| Enforce naming conventions | "Use PascalCase for React components" |
| Flag security concerns | "Check for SQL injection in raw queries" |
| Catch architectural violations | "No direct database access from controller layer" |
| Require specific patterns | "All async functions must have try-catch" |
| Provide code examples | Before/after patterns in fenced blocks |
| Scope rules to file types | Via `applyTo` frontmatter |

### What Copilot code review CANNOT do

| Unsupported | Example |
|---|---|
| Change comment formatting | "Use bold text for critical issues" |
| Modify PR overview comment | "Add a security summary to the overview" |
| Block PR merges | "Block merge if issues are found" |
| Follow external links | "Review per standards at https://..." |
| Generate changelogs | "Create a changelog entry" |
| Count lines deterministically | "Functions must be exactly 50 lines" |
| Enforce build/test passing | "Ensure all tests pass" |
| Run code or linters | "Run ESLint and report results" |

### Workarounds

- **External links:** Copy relevant content directly into the instruction file
- **Build/test enforcement:** Use CI/CD checks instead
- **Deterministic counting:** Phrase as guidelines ("keep functions concise, under ~50 lines") not hard rules
- **Linting rules:** Let the linter enforce them; tell Copilot to focus on semantic rules instead

---

## Precedence and Cascading

When a file in a PR is reviewed, Copilot loads:

1. `.github/copilot-instructions.md` (always loaded for every file)
2. All `*.instructions.md` files whose `applyTo` pattern matches the file being reviewed

**Multiple files can apply to the same file.** For example, a file at `src/components/Button.tsx` would receive instructions from:
- `copilot-instructions.md` (applies to all)
- `typescript.instructions.md` with `applyTo: "**/*.{ts,tsx}"` (matches extension)
- `react.instructions.md` with `applyTo: "**/*.{tsx,jsx}"` (matches extension)
- `components.instructions.md` with `applyTo: "src/components/**/*"` (matches path)

All matching instructions are combined. If rules conflict across files, Copilot uses its judgment — which is why avoiding contradictions is important.

**Monorepo note:** A file at `packages/api/src/routes/users.ts` would receive:
- `copilot-instructions.md` (universal)
- `typescript.instructions.md` (language match)
- `api.instructions.md` (API route match)
- `packages-api.instructions.md` (package match)

Design your file set so rules are additive, not contradictory.
