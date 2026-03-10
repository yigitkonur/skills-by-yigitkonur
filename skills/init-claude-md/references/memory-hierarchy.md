# Memory Hierarchy

Where an instruction lives determines who sees it and when it loads. Use this reference to decide placement for any instruction.

## Placement Decision Table

| Instruction applies to… | Place it in… |
|--------------------------|--------------|
| All developers on this project | `./CLAUDE.md` (project root) |
| Only when editing specific file paths | `.claude/rules/` with `paths:` frontmatter |
| All sessions across all projects | `~/.claude/CLAUDE.md` (user memory) |
| Personal project preferences (not committed) | `CLAUDE.local.md` (gitignored) |
| Deterministic enforcement (not advisory) | `.claude/hooks/` — not memory |
| Domain knowledge relevant only sometimes | `.claude/skills/` |
| Agent-specific behavior | `.claude/agents/` |

All memory tiers are **advisory** — Claude reads them as guidance but may deviate under context pressure. For deterministic enforcement, use hooks.

## Tier Details

### Project Memory: `./CLAUDE.md`

The primary instruction file. Claude reads it at the start of every session.

- Committed to version control
- Shared across all team members
- Target: under 100 lines (60 preferred)

### Path-Scoped Rules: `.claude/rules/`

Modular, conditionally-loaded instructions. Each `.md` file supports optional YAML frontmatter with `paths:` glob patterns.

**Frontmatter format:**
```yaml
---
paths:
  - "src/api/**/*.ts"
  - "src/routes/**"
---

# API Development Rules
- Return consistent error shapes: `{ error: string, code: number }`
- Validate all inputs with Zod schemas
```

Rules without `paths:` load unconditionally (same priority as `CLAUDE.md`).

**Glob syntax:**
- `**/*.ts` — all TypeScript files
- `src/**/*` — everything under src/
- `src/**/*.{ts,tsx}` — TypeScript and TSX
- `tests/**` — everything under tests/

**Organization example:**
```
.claude/rules/
├── code-style.md        # No paths → always loads
├── api.md               # paths: ["src/api/**"]
├── testing.md           # paths: ["tests/**", "**/*.test.*"]
├── frontend/
│   └── react.md         # paths: ["src/components/**"]
└── backend/
    └── database.md      # paths: ["src/db/**", "migrations/**"]
```

Subdirectories are discovered recursively. Symlinks are supported.

### User Memory: `~/.claude/CLAUDE.md`

Personal instructions that apply across all repositories.

**Use cases:**
- Preferred coding style across all projects
- Personal tool preferences
- Common aliases and shortcuts

**User-level rules** at `~/.claude/rules/` load before project rules. Project rules take higher priority.

### Local Overrides: `CLAUDE.local.md`

A gitignored personal override file placed alongside `CLAUDE.md`. Discovered automatically when present.

**Use cases:**
- Personal tool preferences (editor, terminal)
- Local environment paths and sandbox URLs
- Preferred test data or fixtures
- Workflow overrides that differ from team defaults

### Hooks: `.claude/hooks/`

Shell commands executed before or after Claude actions. Unlike memory tiers, hooks are **deterministic** — they always run.

**Use cases:**
- Auto-format after file edits
- Lint before commits
- Run security scans

### Skills: `.claude/skills/`

Domain-specific knowledge loaded on demand via slash commands or trigger descriptions.

### Agents: `.claude/agents/`

Named agent configurations with specific system prompts, tool access, and permissions.

## Priority Order

When instructions conflict, later/more-specific sources win:

1. User memory (`~/.claude/CLAUDE.md`) — lowest priority
2. User rules (`~/.claude/rules/`)
3. Project memory (`./CLAUDE.md`)
4. Project rules (`.claude/rules/`)
5. Local overrides (`CLAUDE.local.md`)
6. Explicit conversation prompts — highest priority

## Decision Flowchart

```
New instruction needed
│
├─ Applies to all team members?
│  ├─ Yes, every session → CLAUDE.md
│  ├─ Yes, but only for certain files → .claude/rules/ with paths:
│  └─ Yes, but only sometimes → agent_docs/ + pointer in CLAUDE.md
│
├─ Personal preference only?
│  ├─ This project → CLAUDE.local.md
│  └─ All projects → ~/.claude/CLAUDE.md
│
├─ Must always execute (not advisory)?
│  └─ .claude/hooks/
│
└─ Domain knowledge for specific tasks?
   └─ .claude/skills/
```
