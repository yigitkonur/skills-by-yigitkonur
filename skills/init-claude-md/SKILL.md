---
name: init-claude-md
description: Use skill if you are creating, auditing, or maintaining CLAUDE.md files that configure Claude Code behavior for a repository.
---

# Init CLAUDE.md

Generate a focused CLAUDE.md file that configures Claude Code for a specific repository.

## What This Produces

A `CLAUDE.md` file at the project root that Claude Code reads at the start of every session. For complex projects, also generates `.claude/rules/` path-scoped rule files and an `agent_docs/` progressive-disclosure directory.

## Workflow

### Phase 1: Explore the Repository

Map the codebase before writing anything.

**Structure**
- Monorepo vs single-service
- Directory layout, package boundaries
- Build output directories

**Tech Stack** — Scan config files:
- `package.json`, `tsconfig.json` → TypeScript/JavaScript
- `pyproject.toml`, `requirements.txt` → Python
- `Cargo.toml` → Rust; `go.mod` → Go
- `docker-compose.yml`, `.github/workflows/` → Infrastructure/CI

**Existing Configuration** — Check for:
- `CLAUDE.md`, `CLAUDE.local.md`, `.claude/rules/`
- `AGENTS.md`, `.cursorrules`, `.windsurfrules`
- `CONTRIBUTING.md`, `README.md`

If files already exist, read them. Complement and improve, do not overwrite blindly.

**Existing Linting & Formatting** — Critical check:
- ESLint, Prettier, Biome → Skip formatting rules
- Black, Ruff → Skip Python formatting
- rustfmt, clippy → Skip Rust formatting

Never put instructions in CLAUDE.md for things linters already enforce. Claude's value is in semantic instructions that require understanding intent.

### Phase 2: Apply the WHAT/WHY/HOW Framework

Every CLAUDE.md answers three questions:

| Layer | Content | Example |
|-------|---------|---------|
| **WHAT** | Technical reality Claude cannot infer from code | "Next.js App Router, NOT Pages" |
| **WHY** | Reasoning behind non-obvious decisions | "Sessions not JWT because SSR needs server-readable auth" |
| **HOW** | Commands and procedures that must be exact | "`pnpm dev` (NOT npm — pnpm workspaces required)" |

**Key discipline:** Exclude anything Claude can infer by reading the code. If there is a React component, Claude knows it is React. If `package.json` has scripts, Claude can read them. Document only the non-obvious.

### Phase 3: Right-Size the File

Claude Code's system prompt uses ~50 instruction slots. Frontier LLMs reliably follow 150–200. That leaves ~100–150 for CLAUDE.md and conversation combined. Every line competes for attention.

| Target | Lines | When |
|--------|-------|------|
| Ideal | Under 60 | Simple apps, clear conventions |
| Good | Under 100 | Standard projects |
| Maximum | 300 | Refactor immediately if exceeded |

**Litmus test for every line:** "Would removing this cause Claude to make a mistake?" If no, cut it.

### Phase 4: Structure the File

Recommended sections for the root `CLAUDE.md`:

```markdown
# Project Name

Brief description (one line).

## Stack
- Language/Framework + version
- Key dependencies
- Package manager

## Structure
- `src/` — Application code
- `tests/` — Test suites

## Commands
- Dev: `pnpm dev`
- Test: `pnpm test`
- Build: `pnpm build`

## Conventions
- Critical convention 1
- Critical convention 2

## Git
- Branch naming pattern
- Commit format
```

Keep each section to the minimum that prevents mistakes. See `references/templates.md` for project-type-specific templates.

### Phase 5: Apply Progressive Disclosure (Complex Projects)

When the root file exceeds 100 lines or the project has 3+ distinct workflow areas, split:

1. Keep the root `CLAUDE.md` under 60–80 lines with universal instructions only
2. Create `agent_docs/` with task-specific markdown files
3. List those files in the root with one-line descriptions so Claude knows when to read them

```
agent_docs/
├── building.md
├── testing.md
├── code-conventions.md
├── service-architecture.md
└── database-schema.md
```

In `CLAUDE.md`, add a pointer section:

```markdown
## Supplemental Docs
- `agent_docs/building.md` — Build commands and dev server setup
- `agent_docs/testing.md` — Test runner, coverage, and CI
- `agent_docs/code-conventions.md` — Error handling, naming, patterns
```

Claude reads relevant files on demand instead of loading everything upfront.

### Phase 6: Use Path-Scoped Rules (Monorepos)

For monorepos or multi-module projects, use `.claude/rules/` for conditional instructions:

```yaml
---
paths:
  - "src/api/**/*.ts"
---

# API Rules
- Return consistent error shapes: `{ error: string, code: number }`
- Validate all inputs with Zod schemas
```

Rules without a `paths:` field load unconditionally. Rules with `paths:` load only when editing matching files.

```
.claude/rules/
├── code-style.md          # No paths → always loads
├── api.md                 # paths: ["src/api/**"]
├── testing.md             # paths: ["tests/**", "**/*.test.*"]
└── frontend/
    └── react.md           # paths: ["src/components/**"]
```

See `references/memory-hierarchy.md` for the complete placement guide.

### Phase 7: Validate

Run through this checklist before outputting:

- [ ] File is under 100 lines (under 60 preferred)
- [ ] No instructions for things linters already enforce
- [ ] No obvious facts Claude can infer from reading the code
- [ ] All documented commands verified against actual project config
- [ ] All directory references match actual structure
- [ ] No stale paths, dead links, or outdated dependency versions
- [ ] Instructions are specific and measurable, not vague
- [ ] Any `@import` paths resolve to real files
- [ ] Progressive disclosure files (if any) are referenced from root
- [ ] `.claude/rules/` files (if any) have valid `paths:` frontmatter

### Phase 8: Output

Present generated files as:

1. **File tree** showing all generated files
2. **Each file** in a fenced code block with path as heading
3. **Brief note** per file explaining what it targets and why

## Reference Files

| File | When to read |
|------|--------------|
| `references/best-practices.md` | Read when deciding what content belongs in CLAUDE.md vs elsewhere, or when optimizing an existing file for conciseness and signal quality. |
| `references/memory-hierarchy.md` | Read when deciding where to place instructions — project root, `.claude/rules/`, user-level, `CLAUDE.local.md`, hooks, or skills. |
| `references/templates.md` | Read when generating a new CLAUDE.md and need a starting template for the detected project type. |

## Anti-Patterns

- **Using CLAUDE.md as a linter** — Linters are deterministic, cheaper, and faster. Do not duplicate lint rules.
- **Auto-generating without review** — `/init` output needs manual curation. Auto-generated files are starting points, not final products.
- **Documenting the obvious** — If the code shows it, Claude already knows it.
- **Exceeding 300 lines** — Context degradation makes instructions unreliable.
- **Embedding code snippets** — Reference files by path instead of pasting stale snippets.
- **Mixing universal and path-specific rules** — Universal rules go in `CLAUDE.md`. Path-specific rules go in `.claude/rules/`.
