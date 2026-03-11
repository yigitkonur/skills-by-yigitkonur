# Scoping and Targeting

Complete reference for `applyTo` glob syntax, `excludeAgent` property, instruction cascading and precedence, monorepo strategies, and overlapping scope management.

## Table of Contents

1. [applyTo Glob Syntax](#applyto-glob-syntax)
2. [Common Glob Patterns](#common-glob-patterns)
3. [excludeAgent Property](#excludeagent-property)
4. [Precedence and Cascading](#precedence-and-cascading)
5. [Scoping Strategies](#scoping-strategies)
6. [Monorepo Strategies](#monorepo-strategies)
7. [Overlapping Scopes](#overlapping-scopes)
8. [Subdirectory Organization](#subdirectory-organization)

---

## applyTo Glob Syntax

The `applyTo` value is a **single glob string** (not an array). It determines which changed files in a PR will have this instruction file applied.

### Frontmatter syntax

```yaml
---
applyTo: "**/*.{ts,tsx}"
---
```

Requirements:
- `---` must be on line 1 (no blank lines before it)
- Valid YAML between the two `---` delimiters
- `applyTo` value must be a quoted string
- Closing `---` must be present
- Glob is evaluated relative to the repository root

### Glob syntax reference

| Syntax | Meaning | Example |
|---|---|---|
| `*` | Match any characters except `/` | `*.ts` matches `index.ts` |
| `**` | Match any characters including `/` (recursive) | `**/*.ts` matches `src/lib/index.ts` |
| `?` | Match single character except `/` | `file?.ts` matches `file1.ts` |
| `{a,b,c}` | Match any of the alternatives | `*.{ts,tsx}` matches both extensions |
| `[abc]` | Match any character in the set | `file[123].ts` matches `file1.ts` |
| `[!abc]` | Match any character NOT in the set | `file[!0-9].ts` excludes numeric |
| `[a-z]` | Match character range | `version[0-9].js` matches `version3.js` |

**Note:** The glob follows GitHub's standard path globbing (same syntax as CODEOWNERS). Regular expressions are NOT supported.

---

## Common Glob Patterns

### By language

| Language | Pattern | Matches |
|---|---|---|
| TypeScript | `**/*.{ts,tsx}` | All TS/TSX files |
| JavaScript | `**/*.{js,jsx}` | All JS/JSX files |
| All JS/TS | `**/*.{ts,tsx,js,jsx}` | Combined JS and TS |
| Python | `**/*.py` | All Python files |
| Rust | `**/*.rs` | All Rust files |
| Go | `**/*.go` | All Go files |
| C# | `**/*.cs` | All C# files |
| Ruby | `**/*.{rb,erb}` | Ruby and ERB templates |
| Java | `**/*.java` | All Java files |
| Swift | `**/*.swift` | All Swift files |
| Kotlin | `**/*.{kt,kts}` | Kotlin files |
| YAML | `**/*.{yml,yaml}` | All YAML files |

### By framework/domain

| Scope | Pattern | Use case |
|---|---|---|
| React components | `src/components/**/*.{tsx,jsx}` | Component-specific rules |
| Next.js App Router | `**/app/**/*.{ts,tsx}` | App Router conventions |
| Next.js Pages Router | `**/pages/**/*.{ts,tsx}` | Pages Router conventions |
| API routes (TS) | `**/api/**/*.{ts,js}` | API endpoint rules |
| API routes (Python) | `**/routes/**/*.py` | Python API rules |
| Test files (JS/TS) | `**/*.{test,spec}.{ts,tsx,js,jsx}` | Test-specific rules |
| Test files (Python) | `**/test_*.py` | Python test rules |
| Tauri backend | `**/src-tauri/**/*.rs` | Tauri Rust rules |
| Database migrations | `**/migrations/**/*.{sql,py,ts}` | Migration-specific rules |
| GitHub Actions | `**/.github/workflows/**/*.yml` | CI workflow rules |
| Dockerfiles | `**/Dockerfile*` | Docker-specific rules |
| Monorepo package | `packages/api/**/*` | Package-scoped rules |
| GraphQL schemas | `**/*.{graphql,gql}` | Schema rules |
| Configuration | `**/*.{json,yaml,yml,toml}` | Config file rules |

### Pattern specificity examples

```yaml
# Broad — all TypeScript files everywhere
applyTo: "**/*.{ts,tsx}"

# Medium — only files in src directory tree
applyTo: "src/**/*.{ts,tsx}"

# Narrow — only component files
applyTo: "src/components/**/*.{tsx,jsx}"

# Very narrow — only auth-related files
applyTo: "**/auth/**/*.{ts,tsx}"
```

---

## excludeAgent Property

The optional `excludeAgent` frontmatter property prevents a specific Copilot agent from reading the file.

### Syntax

```yaml
---
applyTo: "**/*.ts"
excludeAgent: "coding-agent"
---
```

### Values

| Value | Effect |
|---|---|
| `"code-review"` | File is NOT read by Copilot code review; only the coding agent sees it |
| `"coding-agent"` | File is NOT read by the coding agent; only code review sees it |
| *(omitted)* | File is read by BOTH agents (default) |

### When to use excludeAgent

**Use `excludeAgent: "coding-agent"`** when:
- Rules are specific to review style (e.g., "flag this pattern for human attention")
- Instructions reference PR context that doesn't apply during coding
- Review-only architectural checks that would confuse code generation

**Use `excludeAgent: "code-review"`** when:
- Instructions describe how to generate or scaffold code
- Rules reference interactive workflows (e.g., "ask the user before proceeding")
- Build/test commands that only the coding agent should follow

**Omit excludeAgent** when:
- Rules apply equally to both review and generation (most common case)
- You want consistent standards across all Copilot interactions

---

## Precedence and Cascading

### Loading order

When a file in a PR is reviewed, Copilot loads instructions in this order:

1. **Organization-level** instructions (lowest priority)
2. **Repository-wide** `.github/copilot-instructions.md`
3. **All matching** `*.instructions.md` files (by `applyTo` pattern)
4. **Personal-level** instructions (highest priority)

### Multiple files applying to one file

A file at `src/components/Button.tsx` would receive instructions from:

| File | Why it matches |
|---|---|
| `copilot-instructions.md` | Applies to all files |
| `typescript.instructions.md` (`**/*.{ts,tsx}`) | Extension match |
| `react.instructions.md` (`**/*.{tsx,jsx}`) | Extension match |
| `components.instructions.md` (`src/components/**/*`) | Path match |

All matching instructions are combined. There is no "override" — instructions from all matching files are concatenated.

### Conflict resolution

When rules across files contradict each other, Copilot uses its judgment — there is no deterministic resolution. This is why avoiding contradictions is critical.

**Example conflict to avoid:**
```
typescript.instructions.md  → "Prefer interfaces over type aliases"
react.instructions.md       → "Prefer type aliases over interfaces for Props"
```

A `.tsx` file matches both patterns and receives contradictory guidance. Fix by making rules complementary:
```
typescript.instructions.md  → "Use interfaces for object shapes"
react.instructions.md       → "Use type aliases only for union types and utility types"
```

### Alphabetical ordering

When multiple scoped files match, they are concatenated in **alphabetical order by filename**. This matters when approaching the combined context limit — files processed first have more influence.

---

## Scoping Strategies

Choose the right scope width for each concern:

### Broad language scope

For general language rules that apply everywhere:
```yaml
applyTo: "**/*.{ts,tsx,js,jsx}"
```

Best for: Type safety, error handling patterns, import conventions.

### Framework-specific scope

For framework conventions that only apply to framework files:
```yaml
applyTo: "src/components/**/*.{tsx,jsx}"
```

Best for: Component patterns, hooks rules, rendering conventions.

### Directory-specific scope

For architecture rules tied to a directory's purpose:
```yaml
applyTo: "src/api/**/*"
```

Best for: API validation, database access rules, controller patterns.

### Critical path scope

For security-sensitive areas requiring extra scrutiny:
```yaml
applyTo: "**/auth/**/*.{ts,js}"
```

Best for: Authentication, payment processing, admin functionality.

### Cross-cutting narrow scope

For specific file types that need special handling:
```yaml
applyTo: "**/*.{test,spec}.{ts,tsx,js,jsx}"
```

Best for: Test conventions, fixture patterns, mocking standards.

---

## Monorepo Strategies

### Package-scoped files

When packages have meaningfully different review needs:

```
.github/
├── copilot-instructions.md                    # Universal rules
└── instructions/
    ├── typescript.instructions.md             # All TS files
    ├── packages-api.instructions.md           # API package only
    ├── packages-web.instructions.md           # Web package only
    ├── packages-shared.instructions.md        # Shared library only
    └── testing.instructions.md                # All test files
```

```yaml
# packages-api.instructions.md
---
applyTo: "packages/api/**/*"
---

# API Package Review Guidelines

## Endpoint Standards
- All routes must use the shared validation middleware
- Response format must follow ApiResponse<T> type
```

```yaml
# packages-web.instructions.md
---
applyTo: "packages/web/**/*"
---

# Web Package Review Guidelines

## Component Standards
- Use shared UI components from @company/ui-kit
- No direct API calls — use the shared API client from @company/api-client
```

### Rule deduplication in monorepos

**Root `copilot-instructions.md`** already applies to ALL files. Package-specific files should only contain rules UNIQUE to that package.

**Wrong** — repeating root rules:
```markdown
# packages-api.instructions.md
- No hardcoded secrets          ← already in copilot-instructions.md
- Use proper error handling     ← already in copilot-instructions.md
- Validate all API inputs       ← this is package-specific, keep it
```

**Right** — only package-specific rules:
```markdown
# packages-api.instructions.md
- Validate all API inputs using Zod schemas from packages/shared/schemas
- Use the shared database client — no direct Prisma imports
- Rate-limit all public endpoints using the shared middleware
```

### Service-oriented monorepo

For monorepos with independent services:

```yaml
# services-auth.instructions.md
---
applyTo: "services/auth/**/*"
---
```

```yaml
# services-payments.instructions.md
---
applyTo: "services/payments/**/*"
---
```

Each service file focuses on that service's unique domain rules.

---

## Overlapping Scopes

### Designing additive rules

When multiple files match one file, ensure rules are **additive** (complementary), not contradictory.

**Good overlap — rules complement each other:**
```
typescript.instructions.md (applyTo: "**/*.{ts,tsx}")
  → "Use strict TypeScript types"
  → "Handle null/undefined explicitly"

react.instructions.md (applyTo: "**/*.{tsx,jsx}")
  → "Use React.FC for component types"
  → "Memoize expensive computations"

api.instructions.md (applyTo: "**/api/**/*.ts")
  → "Validate request bodies with Zod"
  → "Return consistent response envelopes"
```

A file at `src/api/users.ts` gets all three sets — they don't conflict.

### Avoiding contradiction

If you need genuinely different rules for overlapping scopes, use non-overlapping patterns:

```yaml
# For non-React TypeScript
applyTo: "src/lib/**/*.ts"

# For React components
applyTo: "src/components/**/*.{tsx,jsx}"
```

### Optimal file count

| File count | Assessment |
|---|---|
| 1-3 | Too few — missing scoping benefits |
| 5-12 | Ideal range — good coverage without overhead |
| 13-20 | Acceptable for large monorepos |
| 20+ | Too many — maintenance burden, diminishing returns |

---

## Subdirectory Organization

Scoped instruction files can be placed in subdirectories under `.github/instructions/`:

```
.github/
└── instructions/
    ├── languages/
    │   ├── typescript.instructions.md
    │   ├── python.instructions.md
    │   └── rust.instructions.md
    ├── frameworks/
    │   ├── react.instructions.md
    │   └── nextjs.instructions.md
    └── domains/
        ├── security.instructions.md
        ├── api.instructions.md
        └── testing.instructions.md
```

Copilot reads `*.instructions.md` from `.github/instructions/` **and its subdirectories**. The directory structure is purely organizational — it does not affect which files are loaded or their precedence.

**Tradeoff:** Subdirectories add organizational clarity but make it harder to see all files at a glance. For repositories with 10+ instruction files, subdirectories can help. For 5-10 files, a flat structure is usually cleaner.
