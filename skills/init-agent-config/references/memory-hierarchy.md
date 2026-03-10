# Memory Hierarchy

Where an instruction lives determines who sees it and when it loads. This reference covers placement decisions for Claude Code's memory system.

## Placement Decision Table

| Instruction applies to… | Place it in… |
|--------------------------|--------------|
| All developers on this project | `./CLAUDE.md` (project root) or `AGENTS.md` |
| Only when editing specific file paths | `.claude/rules/` with `paths:` frontmatter |
| All sessions across all projects | `~/.claude/CLAUDE.md` (user memory) |
| Personal project preferences (not committed) | `CLAUDE.local.md` (gitignored) |
| Org-wide policy (managed deployment) | Managed Policy tier (see below) |
| Deterministic enforcement (not advisory) | `.claude/hooks/` — not memory |
| Domain knowledge relevant only sometimes | `.claude/skills/` or supplemental docs |
| Agent-specific behavior profiles | `.claude/agents/` |

All memory tiers are **advisory** — Claude reads them as guidance but may deviate under context pressure. For deterministic enforcement, use hooks.

## Tier Details

### Managed Policy (Org-Wide)

Enterprise-managed instructions deployed by IT policy. Highest priority — cannot be overridden.

| OS | Path |
|----|------|
| macOS | `/Library/Application Support/ClaudeCode/CLAUDE.md` |
| Linux | `/etc/claude-code/CLAUDE.md` |
| Windows | `%PROGRAMDATA%\ClaudeCode\CLAUDE.md` |

**Use cases:** Security requirements, compliance rules, audit logging mandates.

### User Memory: `~/.claude/CLAUDE.md`

Personal instructions that apply across all repositories.

**Use cases:**
- Preferred coding style across all projects
- Personal tool preferences (editor, terminal)
- Common aliases and shortcuts
- Default conventions when project has none

**User-level rules** at `~/.claude/rules/` load before project rules. Project rules take higher priority.

### User Rules: `.claude/settings.json` → `user_rules`

Quick personal rules without creating a file:

```json
{
  "user_rules": [
    "Always use tabs for indentation",
    "Prefer functional style over OOP"
  ]
}
```

These load at the user tier, below project memory.

### Project Memory: `./CLAUDE.md`

The primary instruction file. Claude reads it at the start of every session.

- Committed to version control
- Shared across all team members
- Target: under 100 lines (60 preferred)
- Alternative path: `.claude/CLAUDE.md` (discovered automatically)

**Survives compaction:** CLAUDE.md is re-read after `/compact`. Instructions persist even when conversation history is trimmed.

### Project Rules: `.claude/rules/`

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

### Local Overrides: `CLAUDE.local.md`

A gitignored personal override file placed alongside `CLAUDE.md`. Discovered automatically when present.

**Use cases:**
- Personal tool preferences (editor, terminal)
- Local environment paths and sandbox URLs
- Preferred test data or fixtures
- Workflow overrides that differ from team defaults

### Conversation Context

Explicit instructions given during the session. Highest priority — overrides all files.

## Priority Order

When instructions conflict, later/more-specific sources win:

1. **Managed Policy** — highest (cannot be overridden)
2. **Conversation Context** — explicit session instructions
3. **Local Overrides** (`CLAUDE.local.md`)
4. **Project Rules** (`.claude/rules/`)
5. **Project Memory** (`./CLAUDE.md`)
6. **User Rules** (`~/.claude/rules/`, `settings.json`)
7. **User Memory** (`~/.claude/CLAUDE.md`) — lowest

## Decision Flowchart

```
New instruction needed
│
├─ Applies to all team members?
│  ├─ Yes, every session → CLAUDE.md or AGENTS.md
│  ├─ Yes, but only for certain files → .claude/rules/ with paths:
│  └─ Yes, but only sometimes → supplemental docs + pointer in CLAUDE.md
│
├─ Personal preference only?
│  ├─ This project → CLAUDE.local.md
│  └─ All projects → ~/.claude/CLAUDE.md
│
├─ Must always execute (not advisory)?
│  └─ .claude/hooks/
│
├─ Org-wide security or compliance?
│  └─ Managed Policy tier
│
└─ Domain knowledge for specific tasks?
   └─ .claude/skills/ or .claude/agents/
```

## Auto Memory

Claude Code maintains automatic project memory at:

```
~/.claude/projects/<project-hash>/memory/
```

- First 200 lines of `MEMORY.md` loaded per session
- Auto-updated when Claude learns new project context
- Supplements but does not replace CLAUDE.md
- Useful for evolving context (e.g., recent decisions, active migrations)

## `claudeMdExcludes` Setting

In monorepos, skip irrelevant CLAUDE.md files to avoid context pollution:

```json
// .claude/settings.json
{
  "claudeMdExcludes": [
    "packages/legacy/**",
    "vendor/**",
    "third-party/**"
  ]
}
```

Excluded paths' CLAUDE.md files are never loaded, even when Claude works in those directories.

## Survives Compaction

CLAUDE.md is **re-read after `/compact`**. When conversation history is trimmed to save context, all memory tier files are reloaded. This means:

- Instructions in CLAUDE.md persist across compaction boundaries
- Temporary instructions given in conversation are lost on compaction
- Critical rules must live in files, not conversation

## `.claude/` Directory Map

```
.claude/
├── settings.json        # Project settings, permissions, hooks
├── CLAUDE.md            # Alternative location for project memory
├── commands/            # Custom slash commands
│   ├── deploy.md        # /project:deploy
│   └── review.md        # /project:review
├── agents/              # Named agent configurations
│   ├── reviewer.md      # Specialized code reviewer
│   └── architect.md     # Architecture-focused agent
├── rules/               # Path-scoped rules (see above)
│   ├── api.md
│   └── frontend.md
├── hooks/               # Deterministic pre/post hooks
│   └── pre-commit.sh
└── skills/              # Domain knowledge packs
    └── database.md
```
