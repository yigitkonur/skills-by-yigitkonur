# Writing Effective Agent Instructions

How to write high-signal, low-noise configuration files that AI coding agents reliably follow. Applies to both AGENTS.md and CLAUDE.md.

## Context Window Economics

### Why Every Line Matters

LLMs reliably follow 150–200 instructions total. System prompts consume ~50 slots. This leaves **~100–150 slots** for your config file + conversation history combined.

**Token math:**

| Content | Tokens |
|---------|--------|
| Average config line | ~15 tokens |
| 100-line file | ~1,500 tokens |
| 300-line file | ~4,500 tokens |
| Conversation history | 2,000–10,000+ tokens |

Irrelevant context degrades **all** instruction-following. Agents de-prioritize instructions that seem like they may not be relevant.

**Slot budget rule:** Treat every line as spending a slot from a limited budget. A 200-line config file with 50% noise is worse than a 60-line file with 100% signal.

### Right-Sizing by Project Complexity

| Project Type | Target Lines | Pattern |
|-------------|--------------|---------|
| Simple script/CLI | 20–40 | Single file |
| Standard app | 60–100 | Single file + 1–2 imports |
| Complex monorepo | 60–80 root + nested files | Progressive disclosure |
| Enterprise codebase | 40–60 root + heavy imports | Hierarchical files |

**Litmus test:** If you cannot read your entire config file in under 30 seconds, it is too long.

## The WHAT/WHY/HOW Framework

Every instruction in your config file should answer one of three questions:

### WHAT: Technical Reality

Document only what the agent **cannot infer** from reading code.

**Include:**
- Non-obvious tech stack choices: `"Next.js App Router, NOT Pages"`
- Architecture boundaries: service ownership, data flow directions
- Non-standard file locations: `"Config in config/ not src/config/"`
- Build tool specifics: `"bun, not npm — bun workspaces required"`

**Exclude:**
- Obvious framework usage (React component → agent knows it is React)
- Standard directory structures (`src/`, `lib/`, `tests/`)
- Common patterns visible in code

**Example — good WHAT section:**
```markdown
## Stack
- Next.js 14 App Router (NOT Pages Router)
- Drizzle ORM + PostgreSQL (NOT Prisma — migration speed)
- pnpm workspaces (NOT npm — workspace protocol required)
```

### WHY: Context and Purpose

Explain reasoning behind non-obvious decisions. This prevents agents from "fixing" intentional choices.

```markdown
## Why Sessions Instead of JWT
Sessions (not JWT) because:
- SSR requires server-readable auth state
- No mobile clients planned
- Simpler revocation model
```

**WHY signals prevent:** re-architecture suggestions, "improvement" PRs that undo intentional trade-offs, repeated questions about design choices.

### HOW: Practical Workflows

Commands and procedures the agent must execute correctly. **Verify every command** against package.json, Makefile, or CI before documenting.

```markdown
## Commands
- Dev: `pnpm dev` (NOT npm — pnpm workspaces required)
- Test: `pnpm test --coverage` (required >80%)
- Deploy: `pnpm deploy:staging` then `pnpm deploy:prod`
- Single test: `pnpm test -- path/to/file.test.ts`
```

## Signal Quality Checks

For every line in the config file, ask:

| Question | Action |
|----------|--------|
| Would removing this cause the agent to make a mistake? | If no → **cut it** |
| Can the agent infer this from reading the code? | If yes → **cut it** |
| Is this enforced by a linter or formatter? | If yes → **cut it** |
| Is this universal or path-specific? | If path-specific → **move to scoped rules** |
| Is this needed every session or only sometimes? | If sometimes → **move to supplemental docs** |
| Is this a directive or a suggestion? | If suggestion → **rewrite as directive or remove** |

## Common Bloat Patterns

| Pattern | Problem | Fix |
|---------|---------|-----|
| Full directory tree listing | Agent can run `tree` itself | Remove, or keep only non-obvious parts |
| Copy of README.md | Duplicated context | Reference README, do not copy |
| Exhaustive API docs | Too much for context | Move to supplemental file |
| Linter rules repeated | Deterministic tools handle this | Remove entirely |
| Generic "best practices" | Vague and ignored | Replace with specific, measurable rules |
| Stale commands | Worse than no commands | Verify against package.json/Makefile |
| Obvious framework usage | Agent infers from code | Remove (e.g., "This is a React app") |
| Full dependency lists | Agent reads package.json | Only list non-obvious choices |
| Motivational statements | "Write clean code" helps no one | Replace with specific directives |
| Example code snippets | Gets stale quickly | Reference files by path instead |

## Progressive Disclosure

### When to Split

**Split when:**
- Config file exceeds 100 lines
- Project has 3+ distinct workflow areas
- Team members work on isolated areas
- Instructions are task-specific rather than universal

**Never split when:**
- Everything fits in 60 lines
- Splitting would create files under 20 lines each

### Trigger Tables Pattern

Use a trigger table at the top of your config to enable on-demand loading:

```markdown
## Supplemental Docs
| Area | File | Load When |
|------|------|-----------|
| API development | `docs/api-guide.md` | Editing `src/api/**` |
| Database schema | `docs/db-schema.md` | Editing `src/db/**` or migrations |
| Auth flow | `docs/auth-flow.md` | Editing `src/auth/**` |
| Deployment | `docs/deploy.md` | Running deploy commands |
```

### Multi-Entry Indexing

Reference the same resource from multiple points so the agent finds it regardless of when it scans:

1. **Start** — Trigger table (as above)
2. **Mid-doc** — Inline reference where contextually relevant:
   ```markdown
   ## Database
   - ORM: Drizzle (see `docs/db-schema.md` for migration patterns)
   ```
3. **End** — Complete reference list:
   ```markdown
   ## References
   - `docs/api-guide.md` — API design patterns and error shapes
   - `docs/db-schema.md` — Schema, migrations, seed data
   ```

### File Import Syntax (CLAUDE.md Only)

```markdown
@docs/architecture.md
@agent_docs/testing.md
```

**Warning:** Imports exceeding ~300 lines risk context bloat. For AGENTS.md, use pointer references instead (agents read the file on demand).

## Safety Gates

### Command Verification

- **Never invent commands.** Every command must be verified against `package.json` scripts, `Makefile` targets, CI config, or `pyproject.toml` scripts
- If uncertain: `"Known commands: see package.json scripts"`
- If no test command exists, state: `"Test: [not configured]"`

### Rule Deduplication

- **Never document linter-enforced rules.** If ESLint, Ruff, Clippy, or golangci-lint enforces a rule, do not repeat it
- Exception: Document only if the agent might disable it (e.g., `"Never disable ESLint rules inline without justification"`)

### Warning Preservation

When updating existing config files:
- Scan for: `Never`, `WARNING`, `CRITICAL`, `DO NOT`, `IMPORTANT` markers
- Carry forward all existing boundary rules unless user explicitly requests removal

## Dual-File Strategy

For teams using Claude Code alongside other agents:

### AGENTS.md as Single Source of Truth

Write all universal instructions in AGENTS.md. This file is read by 20+ agents.

### CLAUDE.md as Thin Wrapper

```markdown
@AGENTS.md

## Claude-Specific

### Memory
- Use `/compact` when context grows large
- CLAUDE.md survives compaction — re-read after `/compact`

### Path-Scoped Rules
- See `.claude/rules/` for file-specific instructions

### Imports
- `@docs/architecture.md` — loaded on demand
```

### When to Use Standalone CLAUDE.md

Use standalone CLAUDE.md (not wrapping AGENTS.md) when:
- Team uses only Claude Code — no other agents
- Heavy use of `@import`, `.claude/rules/`, hooks, or agents
- AGENTS.md would be a subset of what Claude needs

### Context Bloat Warning

If AGENTS.md exceeds ~300 lines, a CLAUDE.md that does `@AGENTS.md` plus adds Claude-specific content risks exceeding the effective context budget. In this case:
- Trim AGENTS.md to essential universal content
- Move detailed instructions to supplemental files
- Use trigger tables for on-demand loading

## Writing Style Guide

### Do

- Use imperative voice: "Use Zod for input validation"
- Be specific: "Named exports only, no default exports"
- Include the WHY when non-obvious: "Sessions not JWT because SSR needs server-readable auth"
- Use negative examples for common mistakes: "NOT Pages Router"

### Do Not

- Use passive voice: "Zod should be used" → "Use Zod"
- Be vague: "Write clean code" → "No `any` types without justification comment"
- Include opinions without project context: "React is better than Vue"
- Use conditional language: "You might want to consider..." → "Always run tests before committing"

### Formatting Rules

- Use markdown headers (`##`) for sections
- Use bullet lists for instructions (not paragraphs)
- Use code fences for commands and file paths
- Use tables for structured data (boundaries, commands, conventions)
- Keep lines under 100 characters when possible
- No emojis, no decorative formatting

## Canonical Thin Wrapper Note

When writing a CLAUDE.md thin wrapper, always use the template from **Step 3 of SKILL.md** as the authoritative source. Other reference files (project-templates.md, this file) may show project-type-specific thin wrapper variations, but those are customizations on top of the canonical template -- not replacements.

If you see conflicting thin wrapper examples across files, Step 3 of SKILL.md wins. See steering experience S-13 for details.

## Common Drafting Mistakes

| Mistake | Why it fails | Fix |
|---------|-------------|-----|
| Writing a "project overview" section | Duplicates README, wastes context slots | Reference README instead: `"See README.md for project overview"` |
| Listing every file in the project tree | Agents can read the filesystem themselves | Only document non-obvious directory purposes |
| Documenting linter-enforced rules | The linter already catches these | Only document if agents might disable the rule |
| Writing "write clean code" or "follow best practices" | Too vague to act on -- agents ignore it | Use specific, measurable rules: `"No any types without justification"` |
| Using passive voice throughout | Less clear, less followable | Use imperative: `"Use Zod"` not `"Zod should be used"` |
| Including conditional language | Agents treat `"consider"` as optional | Use direct commands: `"Always"`, `"Never"`, `"Use"` |
| Copying stack info from package.json | Agent can read package.json directly | Only document non-obvious stack choices or WHY context |

## Section Ordering Guidance

For AGENTS.md, order sections by decreasing importance to the agent:

1. **Commands** -- most frequently needed, most likely to cause errors if wrong
2. **Architecture** -- non-obvious structural decisions
3. **Conventions** -- coding patterns specific to this project
4. **Boundaries** -- Always/Ask/Never rules
5. **Dependencies/Stack** -- only non-obvious choices

For CLAUDE.md thin wrapper, the order is fixed:

1. `@AGENTS.md` import (always first)
2. `## Claude-Specific` header
3. Claude-only features (rules, memory, imports)
