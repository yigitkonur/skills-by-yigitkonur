# CLAUDE.md Best Practices

Patterns for creating effective CLAUDE.md files based on Anthropic documentation, HumanLayer production patterns, and Abnormal Security enterprise insights.

## Context Window Economics

### Why Every Line Matters

Claude Code's system prompt contains ~50 baseline instructions. Frontier LLMs reliably follow 150–200 instructions total. This leaves ~100–150 slots for CLAUDE.md content and conversation history combined.

**Token cost:**
- Average CLAUDE.md line: ~15 tokens
- 100-line file: ~1,500 tokens
- 300-line file: ~4,500 tokens
- Conversation history: 2,000–10,000+ tokens

Irrelevant context degrades all instruction-following. Claude explicitly de-prioritizes instructions marked "may or may not be relevant."

### Right-Sizing by Project Complexity

| Project Type | Target Lines | Pattern |
|-------------|--------------|---------|
| Simple script/CLI | 20–40 | Single CLAUDE.md |
| Standard app | 60–100 | CLAUDE.md + 1–2 imports |
| Complex monorepo | 60–80 root + agent_docs/ | Progressive disclosure |
| Enterprise codebase | 40–60 root + heavy imports | Hierarchical files |

## The WHAT/WHY/HOW Framework

### WHAT: Technical Reality

Document only what Claude cannot infer from the code itself.

**Include:**
- Non-obvious tech stack choices ("Next.js App Router, NOT Pages")
- Architecture boundaries (service ownership, data flow)
- Non-standard file locations
- Build tool specifics (bun vs npm vs pnpm)

**Exclude:**
- Obvious framework usage (React component → Claude knows it is React)
- Standard directory structures
- Common patterns visible in code

### WHY: Context and Purpose

Explain reasoning behind non-obvious decisions:

```markdown
## Why Sessions Instead of JWT
Sessions (not JWT) because:
- SSR requires server-readable auth state
- No mobile clients planned
- Simpler revocation
```

### HOW: Practical Workflows

Commands and procedures Claude must execute correctly:

```markdown
## Commands
- Dev: `pnpm dev` (NOT npm — pnpm workspaces required)
- Test: `pnpm test --coverage` (required >80%)
- Deploy: `pnpm deploy:staging` then `pnpm deploy:prod`
```

## Progressive Disclosure

### When to Split

**Split when:**
- CLAUDE.md exceeds 100 lines
- The project has 3+ distinct workflow areas
- Team members work on isolated areas
- Instructions are task-specific rather than universal

**Never split when:**
- The project is simple and everything fits in 60 lines
- Splitting would create files under 20 lines each

### File Import Syntax

Claude Code supports importing external files:

```markdown
@docs/architecture.md
@agent_docs/testing.md
```

Or reference them as pointers in a "Supplemental Docs" section. Claude reads the files on demand when working in relevant areas.

### Example Directory Layout

```
project/
├── CLAUDE.md                 # Under 60 lines, universal only
├── CLAUDE.local.md           # Personal overrides (gitignored)
├── agent_docs/
│   ├── building.md
│   ├── testing.md
│   ├── code-conventions.md
│   ├── service-architecture.md
│   └── database-schema.md
└── .claude/
    └── rules/
        ├── api.md            # paths: ["src/api/**"]
        ├── frontend.md       # paths: ["src/components/**"]
        └── testing.md        # paths: ["tests/**"]
```

## Signal Quality Checks

### Litmus Test

For every line in CLAUDE.md, ask:

1. **Would removing this cause Claude to make a mistake?** If no → cut it.
2. **Can Claude infer this from reading the code?** If yes → cut it.
3. **Is this enforced by a linter or formatter?** If yes → cut it.
4. **Is this universal or path-specific?** If path-specific → move to `.claude/rules/`.
5. **Is this needed every session or only sometimes?** If sometimes → move to `agent_docs/`.

### Common Bloat Patterns

| Pattern | Problem | Fix |
|---------|---------|-----|
| Full directory tree listing | Claude can run `tree` itself | Remove, or keep only non-obvious parts |
| Copy of README.md | Duplicated context | Reference README, do not copy |
| Exhaustive API docs | Too much for context | Move to `agent_docs/api.md` |
| Linter rules repeated | Deterministic tools handle this | Remove entirely |
| Generic "best practices" | Vague and ignored | Replace with specific, measurable rules |
| Stale commands | Worse than no commands | Verify against package.json/Makefile |

## Measuring Effectiveness

### Iteration Cycle

1. Write CLAUDE.md
2. Use Claude Code for 2–3 sessions
3. Note where Claude ignores instructions or makes avoidable mistakes
4. Adjust: strengthen ignored rules, remove unused ones, add missing context
5. Repeat

### Signs of a Good File

- Claude follows conventions without reminders
- Claude asks fewer clarifying questions about project structure
- New team members can onboard with Claude immediately
- File rarely exceeds 80 lines

### Signs of a Bad File

- Claude ignores most instructions (file too long or too vague)
- Same correction given repeatedly across sessions
- File has not been updated in months but project has changed
- File contains style rules that linters should handle
