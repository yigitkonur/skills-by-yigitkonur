# Cross-Agent Compatibility Guide

Which features work across agents, agent-specific config files, and strategies for multi-agent teams.

## Agent Support Matrix

| Agent | Reads AGENTS.md | Reads Nested | Native Config File | Size Limit | Notes |
|-------|-----------------|--------------|-------------------|------------|-------|
| Codex CLI | ✅ | ✅ | `AGENTS.md` + `config.toml` | 32 KiB | Full discovery chain, override support |
| Cursor | ✅ | ✅ | `.cursor/rules/*.mdc` | — | `.cursorrules` deprecated; auto-reads workspace |
| VS Code Copilot | ✅ | ✅ | `.github/copilot-instructions.md` | — | Workspace-wide, subdirectory support |
| GitHub Copilot Chat | ✅ | — | `.github/copilot-instructions.md` | — | Root file only |
| Claude Code | ❌ | — | `CLAUDE.md` + `.claude/` | ~50 KB | Symlink or thin wrapper for AGENTS.md compat |
| Devin | ✅ | — | `REVIEW.md` + `AGENTS.md` | — | Root file only |
| Jules | ✅ | — | `AGENTS.md` | — | Root file only |
| Amp | ✅ | — | `AGENTS.md` | — | Root file only |
| Gemini CLI | ✅ | — | `GEMINI.md` + `.gemini/settings.json` | — | Also reads AGENTS.md natively |
| Windsurf | ✅ | — | `.windsurfrules` | ~12K chars | Root file only |
| Aider | ✅ | — | `.aider.conf.yml` | — | Requires `read: AGENTS.md` in config |
| Continue | ✅ | — | `.continue/config.json` | — | Root file via config |
| Cline | ✅ | — | `.clinerules` | — | Root file only |
| Roo Code | ✅ | — | `.roo/rules/` | — | Mode-scoped rules |
| Amazon Q | ✅ | — | `.amazonq/rules/` | — | Root file only |
| Tabnine | ✅ | — | `.tabnine/` | — | Root file only |

## Universal vs Agent-Specific Features

### Universal (Safe in Any AGENTS.md)

Plain markdown that every agent reads as text:

| Feature | Example |
|---------|---------|
| Project description | `"Next.js App Router with PostgreSQL"` |
| Build/test/lint commands | `"Run pnpm test before committing"` |
| Directory structure | `"API routes in src/app/api/"` |
| Conventions | `"Use named exports, not default exports"` |
| Boundaries (Always/Ask/Never) | `"Never modify migration files directly"` |
| Error handling patterns | `"Use Result type, not exceptions"` |
| Dependency management | `"Use pnpm, not npm or yarn"` |
| Git workflow | `"Commit messages follow Conventional Commits"` |

### Agent-Specific (Keep Out of AGENTS.md)

| Feature | Where It Belongs | Agent |
|---------|-----------------|-------|
| `@import` syntax | `CLAUDE.md` | Claude Code |
| `paths:` frontmatter rules | `.claude/rules/*.md` | Claude Code |
| Hooks (pre-tool, post-tool) | `.claude/settings.json` | Claude Code |
| Custom slash commands | `.claude/commands/*.md` | Claude Code |
| Named agents/subagents | `.claude/agents/*.md` | Claude Code |
| `.mdc` files with frontmatter | `.cursor/rules/*.mdc` | Cursor |
| `.windsurfrules` config | `.windsurfrules` | Windsurf |
| `GEMINI.md` config | `GEMINI.md` | Gemini CLI |
| `.aider.conf.yml` | `.aider.conf.yml` | Aider |
| MCP server config | Agent-specific settings | Varies |

## Agent-Specific Config File Reference

### Claude Code

```
CLAUDE.md                    # Project memory (or .claude/CLAUDE.md)
CLAUDE.local.md              # Personal overrides (gitignored)
.claude/
├── settings.json            # Permissions, hooks, MCP servers
├── settings.local.json      # Personal settings (gitignored)
├── commands/                # Custom slash commands (/project:*)
│   └── deploy.md
├── agents/                  # Named agent profiles (subagents)
│   └── reviewer.md
└── rules/                   # Path-scoped rules with paths: frontmatter
    ├── api.md               # paths: ["src/api/**"]
    └── frontend.md          # paths: ["src/components/**"]
```

### Cursor

```
.cursor/
└── rules/
    ├── general.mdc          # Always loaded (no frontmatter or globs: [])
    ├── api.mdc              # globs: ["src/api/**"]
    └── testing.mdc          # globs: ["tests/**"]
```

`.mdc` frontmatter format:
```yaml
---
description: "Rules for API development"
globs: ["src/api/**/*.ts"]
alwaysApply: false
---
```

Note: `.cursorrules` at project root is deprecated but still read for backwards compatibility.

### Windsurf

```
.windsurfrules               # Plain text, max ~12K characters
```

Single file at project root. No nesting, no frontmatter. Keep concise.

### Gemini CLI

```
GEMINI.md                    # Gemini-specific instructions
.gemini/
└── settings.json            # Configuration (can point to AGENTS.md)
```

```json
{
  "contextFileName": "AGENTS.md"
}
```

### GitHub Copilot (VS Code)

```
.github/
├── copilot-instructions.md  # Global Copilot instructions
└── instructions/
    ├── api.instructions.md  # Scoped instructions
    └── tests.instructions.md
```

### Aider

```yaml
# .aider.conf.yml
read:
  - AGENTS.md
  - docs/architecture.md
```

### Codex CLI

```toml
# ~/.codex/config.toml
project_doc_max_bytes = 32768
project_doc_fallback_filenames = ["TEAM_GUIDE.md"]
```

## Cross-Agent Strategies

### Single-Agent Team

Use the agent's native config directly:

| Agent | Primary Config |
|-------|---------------|
| Claude Code | `CLAUDE.md` + `.claude/` |
| Cursor | `.cursor/rules/*.mdc` |
| Codex CLI | `AGENTS.md` |
| Gemini CLI | `GEMINI.md` |
| Windsurf | `.windsurfrules` |

### Multi-Agent Team (Recommended)

1. **Write AGENTS.md** as the single source of truth (universal content only)
2. **Create agent-specific wrappers:**
   - Claude Code: use the canonical thin wrapper from Step 3 of `SKILL.md`
   - If Claude needs no extra memory or features, the wrapper can be just `@AGENTS.md`
   - Use a symlink only when the repo truly wants identical content and the environment supports it
3. **Add agent-specific config** only where needed:
   - `.claude/rules/` for path-scoped Claude rules
   - `.cursor/rules/` for Cursor-specific behavior
   - `.windsurfrules` for Windsurf-specific concise rules
4. **Gitignore personal overrides:**
   ```gitignore
   AGENTS.override.md
   CLAUDE.local.md
   ```

### Full Multi-Agent Repository Layout

```
repo/
├── AGENTS.md                    # ← Source of truth (universal content)
├── CLAUDE.md                    # @AGENTS.md + Claude-specific additions
├── GEMINI.md                    # Gemini-specific (refs AGENTS.md content)
├── .windsurfrules               # Condensed version for Windsurf's 12K limit
├── .github/
│   └── copilot-instructions.md  # Copilot-specific (refs AGENTS.md content)
├── .cursor/
│   └── rules/
│       └── general.mdc          # Cursor-specific rule format
├── .claude/
│   └── rules/
│       └── api.md               # Claude path-scoped rules
└── .aider.conf.yml              # read: [AGENTS.md]
```

**Maintenance rule:** Edit AGENTS.md first. Propagate to agent-specific files only if they contain unique content beyond the pointer.

### Monorepo Multi-Agent Strategy

```
repo/
├── AGENTS.md                    # Universal root instructions
├── CLAUDE.md → AGENTS.md        # Symlink for Claude Code
├── packages/
│   ├── api/
│   │   └── AGENTS.md            # API-specific (Codex, Cursor, VS Code read this)
│   └── web/
│       └── AGENTS.md            # Web-specific
└── .claude/
    └── rules/
        ├── api.md               # paths: ["packages/api/**"]
        └── web.md               # paths: ["packages/web/**"]
```

Agents that support nested files get richer context. Agents that only read root still get universal instructions.

## Migration Guides

### From `.cursorrules` to AGENTS.md

1. Copy content from `.cursorrules` to `AGENTS.md`
2. Remove any Cursor-specific syntax (frontmatter, globs)
3. Create `.cursor/rules/general.mdc` for Cursor-only settings
4. Keep `.cursorrules` as a minimal pointer or remove it

### From `CLAUDE.md` to AGENTS.md

1. Copy non-Claude-specific content to `AGENTS.md`
2. Remove `@import` lines (inline the referenced content)
3. Remove references to `.claude/rules/` or hooks
4. Replace `CLAUDE.md` with thin wrapper: `@AGENTS.md` + Claude-specific additions
5. Keep Claude-specific features in `.claude/` directory

### From `copilot-instructions.md` to AGENTS.md

1. Copy content from `.github/copilot-instructions.md` to `AGENTS.md`
2. Remove any Copilot-specific references
3. Keep `.github/copilot-instructions.md` as a pointer: `"See AGENTS.md for project conventions"`
4. Move Copilot-specific instructions to `.github/instructions/*.instructions.md`

### From No Agent Config

1. Start with a template from `references/project-templates.md`
2. Fill in project-specific details
3. Verify every documented command against actual config
4. Commit and test with your agent

## Testing Cross-Compatibility

```bash
# Codex CLI
codex "Summarize your current instructions"

# Claude Code
claude "What instructions have you loaded?"

# Cursor: Open project → check if instructions appear in chat context

# Gemini CLI
gemini "What project conventions should you follow?"

# Aider
aider --message "List the project conventions you know about"
```

The response should reflect your AGENTS.md content regardless of which agent reads it.

## Real-World Setup Examples

### Example 1: Small Team, Claude + Cursor

```
AGENTS.md              # Universal: commands, conventions, boundaries
CLAUDE.md              # @AGENTS.md + Claude-specific (thin wrapper)
.cursor/rules/api.mdc  # Cursor-specific: API route patterns
```

Both agents read AGENTS.md for shared instructions. Claude additionally reads CLAUDE.md. Cursor additionally reads `.cursor/rules/`. No content is duplicated.

### Example 2: Open Source Project, Multi-Agent

```
AGENTS.md              # Universal: all instructions here
```

One file, maximum portability. No agent-specific files needed because the project does not use Claude-only or Cursor-only features. Contributors using any agent get the same instructions.

### Example 3: Enterprise Monorepo, Claude + Copilot + Codex

```
AGENTS.md                           # Root: universal conventions, commands
apps/web/AGENTS.md                  # Web app specific
apps/api/AGENTS.md                  # API specific
packages/shared/AGENTS.md           # Shared library specific
CLAUDE.md                           # @AGENTS.md + Claude-specific (thin wrapper)
.github/copilot-instructions.md     # Points to AGENTS.md or contains Copilot-specific
```

All agents read root AGENTS.md. Codex and Cursor also read nested AGENTS.md files. Claude reads CLAUDE.md which imports AGENTS.md. Copilot reads its own config. Content stays DRY because AGENTS.md is the single source of truth.

## Agent-Specific Notes

### Cursor

- `.cursorrules` is deprecated -- use `.cursor/rules/*.mdc` instead
- Cursor auto-reads AGENTS.md from workspace root
- `.mdc` files support `description:` and `globs:` frontmatter for path-scoping (similar to `.claude/rules/`)
- If migrating from `.cursorrules`, extract universal content to AGENTS.md and keep Cursor-specific patterns in `.cursor/rules/`

### Gemini CLI

- Reads both `GEMINI.md` and `AGENTS.md` natively
- `GEMINI.md` is the Gemini-specific config (like CLAUDE.md is for Claude)
- `.gemini/settings.json` for Gemini-specific settings
- For dual-agent teams (Claude + Gemini), put shared rules in AGENTS.md and use both CLAUDE.md and GEMINI.md as thin wrappers

### GitHub Copilot

- Reads AGENTS.md from workspace root
- `.github/copilot-instructions.md` is the Copilot-native config
- Scoped instruction files: `.github/instructions/*.instructions.md` with `applyTo:` frontmatter
- For review-specific config, use the `init-review` skill instead
