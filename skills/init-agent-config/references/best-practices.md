# Best Practices for Agent Configuration Files

Universal best practices for AGENTS.md and CLAUDE.md. Applies to any AI coding agent configuration.

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

Irrelevant context degrades **all** instruction-following. Agents de-prioritize instructions that "may or may not be relevant."

**Slot budget rule:** Treat every line as spending a slot from a limited budget. A 200-line config file with 50% noise is worse than a 60-line file with 100% signal.

### Right-Sizing by Project Complexity

| Project Type | Target Lines | Pattern |
|-------------|--------------|---------|
| Simple script/CLI | 20–40 | Single file |
| Standard app | 60–100 | Single file + 1–2 imports |
| Complex monorepo | 60–80 root + nested files | Progressive disclosure |
| Enterprise codebase | 40–60 root + heavy imports | Hierarchical files |

**Litmus test:** If you cannot read your entire config file in under 30 seconds, it is too long.

**Common bloat patterns:**

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

## WHAT/WHY/HOW Framework

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

Use a trigger table at the top of your config to enable on-demand loading. The agent reads the table, then loads the relevant supplemental file only when working in that area.

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

Reference the same resource from multiple points in the config so the agent finds it regardless of when it scans:

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

Claude Code supports importing external files:

```markdown
@docs/architecture.md
@agent_docs/testing.md
```

**Warning:** Imports exceeding ~300 lines risk context bloat. If the imported file is large, link to it as a reference instead of importing.

For AGENTS.md, use pointer references instead (agents read the file on demand when working in relevant areas).

## Quality Scoring Rubric

Rate any agent config file on these dimensions:

| Dimension | Points | Criteria |
|-----------|--------|----------|
| **Commands accuracy** | 20 | All documented commands verified against package.json / Makefile / CI. No invented commands. |
| **Architecture documentation** | 20 | Non-obvious boundaries, data flow, service ownership documented. Not duplicating README. |
| **Non-obvious patterns** | 15 | Documents what agents cannot infer: why decisions were made, hidden gotchas, non-standard paths. |
| **Conciseness** | 15 | No bloat, no filler, no linter-enforced rules. Every line passes the litmus test. |
| **Currency** | 15 | Commands, paths, and conventions match the current state of the codebase. No stale references. |
| **Actionability** | 15 | Instructions are directives, not suggestions. Agent can execute without ambiguity. |

**Grade thresholds:**

| Grade | Score | Meaning |
|-------|-------|---------|
| A | 90–100 | Production-ready, minimal iteration needed |
| B | 75–89 | Good, 1–2 areas to tighten |
| C | 60–74 | Functional but noisy or missing key sections |
| D | 45–59 | Significant gaps or stale content |
| F | < 45 | Actively harmful — incorrect commands, misleading architecture |

## Safety Gates

Rules that prevent agent config files from causing harm:

### Command Verification
- **Never invent commands.** Every command in the file must be verified against `package.json` scripts, `Makefile` targets, CI config, or `pyproject.toml` scripts.
- If uncertain about a command: `"Known commands: see package.json scripts"`
- If the project has no test command, do not fabricate one. State: `"Test: [not configured]"`

### Rule Deduplication
- **Never document linter-enforced rules.** If ESLint, Ruff, Clippy, or golangci-lint enforces a rule, the config file should not repeat it. Agents follow linter output.
- Exception: Document the rule only if the agent might disable it (e.g., `"Never disable ESLint rules inline without justification"`).

### Warning Preservation
- **Preserve critical warnings** found in existing config files during regeneration or updates.
- Scan for: `Never`, `WARNING`, `CRITICAL`, `DO NOT`, `IMPORTANT` markers.
- If updating a config file, carry forward all existing boundary rules unless the user explicitly requests removal.

### Verification Checklist
Before committing any agent config file:
1. Run every documented command and confirm it succeeds
2. Confirm documented paths exist (`ls src/api/` etc.)
3. Confirm conventions match actual code patterns (grep for counter-examples)
4. Confirm no linter-enforced rules are repeated

## Signal Quality Checks

For every line in the config file, ask:

1. **Would removing this cause the agent to make a mistake?** If no → cut it.
2. **Can the agent infer this from reading the code?** If yes → cut it.
3. **Is this enforced by a linter or formatter?** If yes → cut it.
4. **Is this universal or path-specific?** If path-specific → move to scoped rules.
5. **Is this needed every session or only sometimes?** If sometimes → move to supplemental docs.
6. **Is this a directive or a suggestion?** If suggestion → rewrite as directive or remove.

## Dual-File Strategy

For teams using Claude Code alongside other agents:

### AGENTS.md as Single Source of Truth

Write all universal instructions in `AGENTS.md`. This file is read by 20+ agents.

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

Use a standalone `CLAUDE.md` (not wrapping AGENTS.md) when:
- Team uses only Claude Code — no other agents
- Heavy use of `@import`, `.claude/rules/`, hooks, or agents
- AGENTS.md would be a subset of what Claude needs

### Context Bloat Warning

If `AGENTS.md` exceeds ~300 lines, a CLAUDE.md that does `@AGENTS.md` plus adds Claude-specific content risks exceeding the effective context budget. In this case:
- Trim AGENTS.md to essential universal content
- Move detailed instructions to supplemental files
- Use trigger tables for on-demand loading
