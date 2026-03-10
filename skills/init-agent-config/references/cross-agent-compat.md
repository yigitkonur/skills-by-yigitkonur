# Cross-Agent Compatibility Guide

AGENTS.md is supported by 20+ AI coding agents. This guide maps which features work everywhere, agent-specific configuration files, and strategies for multi-agent teams.

## Supported Agents

| Agent | Reads AGENTS.md | Reads Nested | Native Config File | Notes |
|-------|-----------------|--------------|-------------------|-------|
| Codex CLI | ✅ | ✅ | `AGENTS.md` + `config.toml` | Full discovery chain, override support, 32 KiB limit |
| Cursor | ✅ | ✅ | `.cursor/rules/*.mdc` | `.cursorrules` deprecated; auto-reads workspace root |
| VS Code Copilot | ✅ | ✅ | `.github/copilot-instructions.md` | Workspace-wide, respects subdirectory files |
| GitHub Copilot Chat | ✅ | — | `.github/copilot-instructions.md` | Root file only in most contexts |
| Claude Code | ❌ | — | `CLAUDE.md` + `.claude/` | Reads CLAUDE.md; symlink AGENTS.md for compat |
| Devin | ✅ | — | `REVIEW.md` + `AGENTS.md` | Root file only |
| Jules | ✅ | — | `AGENTS.md` | Root file only |
| Amp | ✅ | — | `AGENTS.md` | Root file only |
| Gemini CLI | ✅ | — | `GEMINI.md` + `.gemini/settings.json` | Also reads AGENTS.md natively |
| Windsurf | ✅ | — | `.windsurfrules` | Max ~12K chars; root file only |
| Aider | ✅ | — | `.aider.conf.yml` | Requires `read: AGENTS.md` in config |
| Continue | ✅ | — | `.continue/config.json` | Root file via config |
| Cline | ✅ | — | `.clinerules` | Root file only |
| Roo Code | ✅ | — | `.roo/rules/` | Root file with mode-scoped rules |
| Amazon Q | ✅ | — | `.amazonq/rules/` | Root file only |
| Tabnine | ✅ | — | `.tabnine/` | Root file only |

**Legend:** ✅ = supported, — = not applicable / not supported, ❌ = uses different file

## Universal vs Agent-Specific Features

### Universal (Safe in Any AGENTS.md)

Plain markdown that any agent reads as text:

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
| Named agents | `.claude/agents/*.md` | Claude Code |
| `.mdc` files with frontmatter | `.cursor/rules/*.mdc` | Cursor |
| `.windsurfrules` config | `.windsurfrules` | Windsurf |
| `GEMINI.md` config | `GEMINI.md` | Gemini CLI |
| `.aider.conf.yml` | `.aider.conf.yml` | Aider |
| MCP server config | Agent-specific | Varies |

## Agent-Specific Config Files Reference

### Claude Code

```
CLAUDE.md                    # Project memory (or .claude/CLAUDE.md)
CLAUDE.local.md              # Personal overrides (gitignored)
.claude/
├── settings.json            # Permissions, hooks, MCP servers
├── commands/                # Custom slash commands (/project:*)
│   └── deploy.md
├── agents/                  # Named agent profiles
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
GEMINI.md                    # Project instructions (Gemini-specific)
.gemini/
└── settings.json            # Configuration
```

```json
// .gemini/settings.json
{
  "contextFileName": "AGENTS.md"
}
```

### GitHub Copilot (VS Code)

```
.github/
├── copilot-instructions.md  # Global instructions for Copilot
└── instructions/
    ├── api.instructions.md  # Scoped to API work
    └── tests.instructions.md
```

Additional scoped files use `*.instructions.md` naming convention.

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

Native AGENTS.md support with full discovery chain.

## Cross-Agent Strategy

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
   ```bash
   # Claude Code: thin wrapper
   echo '@AGENTS.md' > CLAUDE.md

   # Or symlink
   ln -s AGENTS.md CLAUDE.md
   ```
3. **Add agent-specific config** only where needed:
   - `.claude/rules/` for path-scoped Claude rules
   - `.cursor/rules/` for Cursor-specific behavior
   - `.windsurfrules` for Windsurf-specific concise rules
4. **Gitignore personal overrides:**
   ```gitignore
   AGENTS.override.md
   CLAUDE.local.md
   ```

### Multi-Agent Output Strategy

Maintaining one source of truth while supporting 5+ agents:

```
repo/
├── AGENTS.md                    # ← Source of truth (universal content)
├── CLAUDE.md                    # @AGENTS.md + Claude-specific additions
├── GEMINI.md                    # Gemini-specific additions (refs AGENTS.md)
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

**Maintenance rule:** When updating instructions, edit AGENTS.md first. Then propagate changes to agent-specific files only if they contain unique content beyond the pointer.

### Monorepo Multi-Agent Strategy

```
repo/
├── AGENTS.md                    # Universal root instructions
├── CLAUDE.md → AGENTS.md        # Symlink for Claude Code
├── .cursorrules                 # Cursor-specific (deprecated but backwards compat)
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
2. Remove any Cursor-specific syntax
3. Create `.cursor/rules/general.mdc` for Cursor-only settings
4. Keep `.cursorrules` as a minimal pointer or remove it

### From `CLAUDE.md` to AGENTS.md

1. Copy non-Claude-specific content to `AGENTS.md`
2. Remove `@import` lines (inline the referenced content)
3. Remove references to `.claude/rules/` or hooks
4. Replace `CLAUDE.md` with thin wrapper: `@AGENTS.md` + Claude-specific
5. Keep Claude-specific features in `.claude/` directory

### From No Agent Config

1. Start with the appropriate template from `references/templates.md`
2. Fill in project-specific details
3. Run linters and tests to verify documented commands
4. Commit and test with your agent

## Testing Cross-Compatibility

After creating AGENTS.md, verify it works with each agent:

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

# Generic (any agent)
[agent] "What project conventions should you follow?"
```

The response should reflect your AGENTS.md content regardless of which agent reads it.
