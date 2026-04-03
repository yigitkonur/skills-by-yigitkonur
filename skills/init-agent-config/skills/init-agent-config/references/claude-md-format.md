# CLAUDE.md Format Specification

Complete reference for CLAUDE.md — the project memory file read by Claude Code at the start of every session.

## What CLAUDE.md Does

CLAUDE.md is a markdown file placed in your project root (or at `.claude/CLAUDE.md`) that provides persistent instructions to Claude Code. It sets coding standards, architecture context, build commands, and project-specific conventions. Claude reads it automatically — no configuration needed.

**Key properties:**
- Read at session start and re-read after `/compact`
- Advisory, not deterministic — Claude follows instructions as guidance
- Supports `@import` syntax for modular organization
- Survives compaction (conversation history is trimmed, but CLAUDE.md persists)

## File Locations

### Project Memory

| Location | Purpose | Sharing |
|----------|---------|---------|
| `./CLAUDE.md` | Primary project instructions | Committed to git, shared with team |
| `./.claude/CLAUDE.md` | Alternative location (auto-discovered) | Committed to git, shared with team |
| `./CLAUDE.local.md` | Personal overrides | Gitignored, personal only |

### User Memory

| Location | Purpose |
|----------|---------|
| `~/.claude/CLAUDE.md` | Personal instructions for all projects |
| `~/.claude/rules/*.md` | Personal modular rules for all projects |

### Managed Policy (Enterprise)

| OS | Path |
|----|------|
| macOS | `/Library/Application Support/ClaudeCode/CLAUDE.md` |
| Linux/WSL | `/etc/claude-code/CLAUDE.md` |
| Windows | `C:\Program Files\ClaudeCode\CLAUDE.md` |

Managed policy is the highest priority tier — cannot be overridden by any other scope.

## Memory Hierarchy (Priority Order)

When instructions conflict, more specific scopes win:

```
1. Managed Policy          ← highest (enterprise, cannot override)
2. Conversation Context    ← explicit session instructions
3. Local Overrides         ← CLAUDE.local.md (gitignored)
4. Project Rules           ← .claude/rules/*.md
5. Project Memory          ← ./CLAUDE.md
6. User Rules              ← ~/.claude/rules/*.md
7. User Memory             ← ~/.claude/CLAUDE.md (lowest)
```

## Loading Behavior

1. Walk up directory tree from CWD, loading any `CLAUDE.md` found
2. Load `.claude/rules/*.md` files (unconditionally unless `paths:` frontmatter restricts them)
3. Load subdirectory CLAUDE.md files on-demand when files in those directories are opened

**After `/compact`:** All memory tier files are reloaded. Conversation history is trimmed but CLAUDE.md content persists. Critical rules must live in files, not conversation.

## @import Syntax

Import external files to keep CLAUDE.md lean:

```markdown
# Project Configuration

See @README.md for project overview.
See @docs/architecture.md for system design.

@agent_docs/testing.md
@agent_docs/deployment.md
```

**Rules:**
- Paths are relative to the file containing the import
- Recursive imports supported (max depth: 5)
- Cycles are detected and rejected
- Missing files fail silently (logged to debug)
- Each imported file should be ≤10 KB
- Total post-import content should stay under ~50 KB

**Warning:** Importing large files risks context bloat. If an imported file exceeds ~300 lines, reference it as a pointer instead of importing.

## Path-Scoped Rules (`.claude/rules/`)

Modular, conditionally-loaded instructions. Each `.md` file in `.claude/rules/` supports optional YAML frontmatter with `paths:` glob patterns.

### Format

```markdown
---
paths:
  - "src/api/**/*.ts"
  - "src/routes/**"
---

# API Development Rules
- Return consistent error shapes: `{ error: string, code: number }`
- Validate all inputs with Zod schemas
- Include OpenAPI documentation comments
```

### Loading Behavior

- Rules **without** `paths:` frontmatter load unconditionally (same priority as CLAUDE.md)
- Rules **with** `paths:` frontmatter load only when Claude works on files matching those patterns
- Subdirectories within `.claude/rules/` are discovered recursively
- Symlinks are supported

### Supported Glob Patterns

| Pattern | Matches | Example Use |
|---------|---------|-------------|
| `**/*.ts` | All TypeScript files recursively | TypeScript-specific rules |
| `src/**/*` | Everything under src/ | Source code rules |
| `src/**/*.{ts,tsx}` | TypeScript and TSX files | React component rules |
| `tests/**` | Everything under tests/ | Test-specific rules |
| `!tests/**` | Exclude tests directory | Negate a pattern |
| `?` | Single character | Single-char wildcard |
| `[abc]` | Character sets | Character matching |
| `{a,b}` | Brace expansion | Multiple alternatives |

### Organization Example

```
.claude/rules/
├── code-style.md        # No paths: → always loads
├── api.md               # paths: ["src/api/**"]
├── testing.md           # paths: ["tests/**", "**/*.test.*"]
├── frontend/
│   └── react.md         # paths: ["src/components/**"]
└── backend/
    └── database.md      # paths: ["src/db/**", "migrations/**"]
```

## `.claude/` Directory Structure

```
.claude/
├── settings.json        # Project settings, permissions, hooks, MCP servers
├── settings.local.json  # Personal settings (gitignored)
├── CLAUDE.md            # Alternative project memory location
├── commands/            # Custom slash commands
│   ├── deploy.md        # /project:deploy
│   └── review.md        # /project:review
├── agents/              # Named agent configurations (subagents)
│   ├── reviewer.md      # Specialized code reviewer
│   └── architect.md     # Architecture-focused agent
├── rules/               # Path-scoped rules (see above)
│   ├── api.md
│   └── frontend.md
└── hooks/               # Lifecycle hooks (deterministic, not advisory)
    └── pre-commit.sh
```

### Custom Slash Commands (`.claude/commands/`)

Markdown files that define reusable workflows triggered via `/project:command-name`:

```markdown
# Deploy to Staging

1. Run `pnpm build`
2. Run `pnpm test`
3. Deploy with `pnpm deploy:staging`
4. Verify deployment at $STAGING_URL
```

### Named Agents (`.claude/agents/`)

Markdown files with YAML frontmatter defining specialized agent profiles:

```markdown
---
name: reviewer
description: Focused code reviewer
tools:
  - read_file
  - grep
  - glob
---

# Code Reviewer

Review code changes for:
- Security vulnerabilities
- Performance issues
- API contract violations
```

### Hooks (`.claude/hooks/`)

Deterministic scripts that execute on lifecycle events. Unlike CLAUDE.md instructions (advisory), hooks are enforced:

- Pre-tool-use hooks run before tool execution
- Post-tool-use hooks run after tool execution
- Configured in `.claude/settings.json`

## Settings Configuration

### `.claude/settings.json`

```json
{
  "autoMemoryEnabled": true,
  "claudeMdExcludes": [
    "packages/legacy/**",
    "vendor/**"
  ],
  "user_rules": [
    "Always use tabs for indentation",
    "Prefer functional style over OOP"
  ]
}
```

### Key Settings

| Setting | Purpose |
|---------|---------|
| `autoMemoryEnabled` | Toggle auto memory (default: true) |
| `claudeMdExcludes` | Skip CLAUDE.md files matching these globs (useful in monorepos) |
| `user_rules` | Quick personal rules without creating a file |

### Scope Precedence for Settings

Settings files exist at multiple scopes. For arrays (like permissions), values merge across layers:

```
Managed → Command-line → Local → Project → User
```

## Auto Memory

Claude Code maintains automatic project memory at:

```
~/.claude/projects/<project-hash>/memory/
├── MEMORY.md          # Index (first 200 lines loaded per session)
├── debugging.md       # Topic-specific learnings
├── api-conventions.md
└── ...
```

- Auto-updated when Claude learns new project context
- Supplements but does not replace CLAUDE.md
- Toggle with `/memory` command or `autoMemoryEnabled` setting
- Disable globally: `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`

## Environment Variables

| Variable | Effect |
|----------|--------|
| `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1` | Load CLAUDE.md from `--add-dir` directories |
| `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` | Disable auto memory globally |

## Size Guidelines

| File | Ideal | Good | Maximum |
|------|-------|------|---------|
| CLAUDE.md (standalone) | <60 lines | <100 lines | 200 lines |
| CLAUDE.md (thin wrapper) | <20 lines | <30 lines | 50 lines |
| Per import file | <100 lines | <200 lines | 300 lines |
| Total post-import | <3,000 tokens | <5,000 tokens | ~50 KB |

**Why size matters:** Claude has ~50 system prompt instruction slots. Every line in CLAUDE.md competes for attention against conversation context and system prompts. Irrelevant instructions degrade adherence to all instructions.

## Decision Flowchart: Where to Put an Instruction

```
New instruction needed
│
├─ Applies to all team members?
│  ├─ Yes, every session → CLAUDE.md (or AGENTS.md for cross-agent)
│  ├─ Yes, but only for certain files → .claude/rules/ with paths:
│  └─ Yes, but only sometimes → agent_docs/ + pointer in CLAUDE.md
│
├─ Personal preference only?
│  ├─ This project → CLAUDE.local.md
│  └─ All projects → ~/.claude/CLAUDE.md
│
├─ Must always execute (not advisory)?
│  └─ .claude/hooks/ (deterministic enforcement)
│
├─ Org-wide security or compliance?
│  └─ Managed Policy tier
│
└─ Domain knowledge for specific tasks?
   └─ .claude/agents/ or agent_docs/
```

## Generating CLAUDE.md

Use the `/init` command in Claude Code to generate a starter CLAUDE.md. The command:
- Scans the project for tech stack, commands, and structure
- Suggests improvements rather than overwriting existing files
- Produces a starting point that needs manual curation

**Important:** `/init` output is a draft, not a final product. Always review and trim.

## Compaction Behavior

When `/compact` runs (manually or auto at ~10k tokens):

| Content | Preserved? |
|---------|-----------|
| CLAUDE.md (full content) | ✅ Yes — re-read from disk |
| .claude/rules/ (all files) | ✅ Yes — re-read from disk |
| @imported files | ✅ Yes — re-read from disk |
| Auto memory (MEMORY.md) | ✅ Yes — re-read from disk |
| Conversation history | ❌ No — trimmed to save context |
| Session-specific instructions | ❌ No — lost on compaction |

**Implication:** Critical rules must live in files, not conversation. Anything said in chat that must persist should be added to CLAUDE.md or a rule file.

## When to Use Each Feature

Use this decision table to pick the right CLAUDE.md feature for a given need:

| Need | Feature | Why |
|------|---------|-----|
| Universal instructions shared across agents | Put in AGENTS.md, import via `@AGENTS.md` | CLAUDE.md imports it; other agents read it natively |
| Claude-only coding conventions | CLAUDE.md `## Claude-Specific` section | Stays thin, does not pollute AGENTS.md |
| Path-specific rules (e.g., "in tests/, always mock DB") | `.claude/rules/` with `paths:` filter | Only injected when Claude works in matching paths |
| One-off memory for current session | `/memory add "note"` -> CLAUDE.md edit | Persists through compaction |
| Complex domain knowledge for specific tasks | `.claude/agents/` with YAML config | Agent-specific context loaded on demand |
| Pre/post-command automation | `.claude/hooks/` | Runs shell scripts at lifecycle points |
| Personal preferences not shared with team | `CLAUDE.local.md` | Gitignored, personal overrides |

## Common Gotchas

| Gotcha | Why it bites | Prevention |
|--------|-------------|------------|
| `@import` in AGENTS.md | AGENTS.md does not support imports -- content silently ignored | Only use `@import` in CLAUDE.md |
| Huge CLAUDE.md (100+ lines) | Wastes context budget, agents de-prioritize late content | Keep under 60 lines standalone, 20 lines for thin wrapper |
| `.claude/rules/` without `paths:` filter | Rule applies globally, like putting it in CLAUDE.md directly | Always add `paths:` unless truly global |
| Referencing `.claude/rules/` that do not exist | Agents look for a directory that is not there | Only reference if directory exists or you are creating files |
| Putting universal rules in CLAUDE.md instead of AGENTS.md | Other agents (Cursor, Codex, Copilot) never see them | Universal rules go in AGENTS.md |
| CLAUDE.local.md committed to git | Personal overrides shared with team | Add to `.gitignore` |
