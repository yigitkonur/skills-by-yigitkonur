---
name: copilot-review-init
description: "Use skill if you need GitHub Copilot review setup, copilot-instructions.md, or scoped *.instructions.md files for repo-specific PR review behavior."
---

# Copilot Review Init

Generate a complete set of GitHub Copilot code review instruction files tailored to a specific repository.

## What This Produces

GitHub Copilot code review reads instruction files from a PR's repository to guide its analysis. This skill generates:

1. **`.github/copilot-instructions.md`** — Repository-wide review standards applied to every file
2. **Multiple `.github/instructions/*.instructions.md`** — Focused micro-files, each scoped to specific file types via `applyTo` frontmatter

### Why Micro-Files

The micro-file architecture is the core design philosophy. Instead of cramming everything into one file:

- Each file stays within Copilot's **4,000-character processing window** (content beyond this is silently ignored)
- Language-specific rules never bleed into unrelated files
- Teams can own and iterate on their relevant instruction files independently
- Adding a new concern means adding a new file, not editing a monolith

A well-configured repository typically produces 5-12 instruction files.

## Workflow

### Phase 1: Explore the Repository

Before writing a single instruction, map the codebase.

**Structure**
- Monorepo vs single-service
- Directory layout, package boundaries
- Build output directories to ignore

**Tech Stack** — Scan config files:
- `package.json`, `tsconfig.json` → TypeScript/JavaScript ecosystem
- `requirements.txt`, `pyproject.toml` → Python ecosystem
- `Cargo.toml` → Rust; `tauri.conf.json` → Tauri desktop
- `go.mod` → Go; `*.csproj` → C#/.NET
- `docker-compose.yml`, `.github/workflows/` → Infrastructure/CI

**Existing Instruction Files** — Check for:
- `.github/copilot-instructions.md` and `.github/instructions/*.instructions.md`
- `.cursorrules`, `.windsurfrules`, `CLAUDE.md`, `AGENTS.md`, `REVIEW.md`
- `CONTRIBUTING.md`

If instruction files already exist, read them. The goal is to complement and improve, not overwrite blindly.

**Existing Linting & Formatting** — This is critical:
- ESLint, Prettier, Biome → Skip formatting and style rules
- Black, Ruff, isort → Skip Python formatting
- rustfmt, clippy → Skip Rust formatting
- golangci-lint → Skip Go style rules

Never write instructions for things linters already enforce. Copilot's value is in semantic rules that require understanding intent — not syntactic rules a linter handles better.

**Pain Points**
- Recent PRs and issues for recurring themes
- Git history for common bug patterns
- TODO/FIXME/HACK comments indicating tech debt

### Phase 2: Plan Instruction Architecture

Decide which files to generate based on what you found.

**Always generate:**

| File | Purpose |
|---|---|
| `.github/copilot-instructions.md` | Universal rules for all files: security, quality, cross-cutting concerns |

**Generate per language detected:**

| Stack | File | `applyTo` |
|---|---|---|
| TypeScript/JS | `typescript.instructions.md` | `**/*.{ts,tsx,js,jsx}` |
| Python | `python.instructions.md` | `**/*.py` |
| Rust | `rust.instructions.md` | `**/*.rs` |
| Go | `go.instructions.md` | `**/*.go` |
| C# | `csharp.instructions.md` | `**/*.cs` |

**Generate per framework/domain detected:**

| Concern | File | `applyTo` |
|---|---|---|
| React components | `react.instructions.md` | `**/*.{tsx,jsx}` |
| Next.js App Router | `nextjs.instructions.md` | `**/app/**/*.{ts,tsx}` |
| API routes | `api.instructions.md` | `**/api/**/*.{ts,js}` or `**/routes/**/*.py` |
| Database/ORM | `database.instructions.md` | Scoped to model/migration dirs |
| Tauri commands | `tauri.instructions.md` | `**/src-tauri/**/*.rs` |
| MCP server | `mcp.instructions.md` | `**/src/**/*.ts` |
| Tests | `testing.instructions.md` | `**/*.{test,spec}.{ts,tsx,js,jsx}` |
| Docker/infra | `docker.instructions.md` | `**/Dockerfile*` |
| CI/CD | `ci.instructions.md` | `**/.github/workflows/**/*.yml` |
| Security-critical paths | `security.instructions.md` | Scoped to auth/payment/admin dirs |
| Accessibility | `a11y.instructions.md` | `**/*.{tsx,jsx,html}` |

**Monorepo strategy:**
Create package-scoped files when packages have meaningfully different review needs:
- `packages-api.instructions.md` with `applyTo: "packages/api/**/*"`
- `packages-web.instructions.md` with `applyTo: "packages/web/**/*"`

**Character budget:**
Aim for 2,500–3,500 characters per file. If a concern needs more, split into two files with narrower scopes rather than exceeding 4,000 characters.

### Phase 3: Write Instruction Files

**Rule Quality — Every rule must be:**
1. **Specific** — "All API endpoints must validate request bodies with Zod" not "validate inputs"
2. **Measurable** — Unambiguous pass/fail when reviewing code
3. **Actionable** — Developer knows exactly what to fix
4. **Semantic** — Requires understanding intent, not just pattern matching

**Section Ordering** — Content near the top of each file carries more weight:
1. Security-critical rules
2. Architecture/structural requirements
3. Error handling patterns
4. Code quality conventions
5. Performance considerations
6. Testing expectations

**Code Examples** — Include before/after using the repo's actual patterns:
````markdown
```typescript
// Avoid
const result = await db.query(userInput);

// Prefer
const result = await prisma.user.findUnique({ where: { id: validated.id } });
```
````

**Writing `copilot-instructions.md`:**
Include ONLY rules that genuinely apply to ALL code:
- Security fundamentals (no hardcoded secrets, input validation)
- Cross-cutting quality (error handling philosophy, logging conventions)
- Universal naming conventions (if consistent across languages)
- Performance red flags (N+1 queries, missing pagination)
- Testing philosophy

Do NOT put language-specific rules here.

**Writing `*.instructions.md` micro-files:**
- Valid YAML frontmatter with `applyTo` glob string (required)
- Under 4,000 characters (aim for 2,500–3,500)
- H2 headers for sections, bullet points for rules
- 1-2 code examples per file
- Highest-priority rules first

**Frontmatter format:**
```yaml
---
applyTo: "**/*.{ts,tsx}"
---
```

### Phase 4: Validate

Run through this checklist before outputting:

- [ ] Every `*.instructions.md` has valid YAML frontmatter with `applyTo`
- [ ] No file exceeds 4,000 characters (verify with character count)
- [ ] `applyTo` glob patterns are syntactically valid
- [ ] No rule overlap between `copilot-instructions.md` and micro-files
- [ ] No rules duplicating what existing linters enforce
- [ ] Rules are specific and measurable, not vague
- [ ] Code examples use the repo's actual patterns
- [ ] Security rules near top of each relevant file
- [ ] No attempts to modify Copilot UX, formatting, or PR overview
- [ ] No external links (Copilot cannot follow them)
- [ ] File naming: `kebab-case.instructions.md`
- [ ] Monorepo files don't repeat rules already in more-general files
- [ ] `copilot-instructions.md` is in `.github/` root, micro-files in `.github/instructions/`

### Phase 5: Output

Present generated files as:

1. **File tree** — Complete `.github/` structure
2. **Each file** — Full content in fenced code block with path as heading
3. **Reasoning** — Brief note per micro-file explaining what it targets and why

```
.github/
├── copilot-instructions.md
└── instructions/
    ├── typescript.instructions.md
    ├── react.instructions.md
    ├── api.instructions.md
    ├── database.instructions.md
    ├── security.instructions.md
    └── testing.instructions.md
```

## Reference Files

- **`references/instruction-spec.md`** — Complete format specification: frontmatter syntax, glob patterns, character limits, what Copilot supports and doesn't. Read when you need format details.

- **`references/anti-patterns.md`** — Common mistakes and how to avoid them. Includes a debugging sequence for when rules aren't followed. Read before validation.

- **`references/scenarios.md`** — 8 complete example instruction sets for different tech stacks (TS API, Next.js Dashboard, Django, Go, Tauri, MCP Server, Monorepo, Marketing site). Each shows the full file tree and all generated files. Read the relevant scenario when working with a matching stack.

- **`references/micro-library.md`** — Comprehensive library of 20+ individual `*.instructions.md` files organized by language, framework, and domain. Use as adaptation references — match to the actual codebase, don't copy verbatim.

## Key Gotchas

- Copilot reads only the first **4,000 characters** of any instruction file — the rest is silently ignored
- `*.instructions.md` files must live in `.github/instructions/` directory
- `copilot-instructions.md` must be in `.github/` root
- `applyTo` is a **single glob string**, not an array — use `{ts,tsx}` syntax for multiple extensions
- Copilot **cannot follow external links** — inline all content
- Instructions **cannot** change comment format, PR overview, or merge behavior
- Non-deterministic behavior is normal — Copilot won't follow every instruction every time
- Missing or empty `applyTo` on a `*.instructions.md` means the file applies to **nothing**
- Start with 10–20 focused rules across files and iterate based on real PR results
