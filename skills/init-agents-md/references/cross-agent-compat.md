# Cross-Agent Compatibility Guide

AGENTS.md is supported by 20+ AI coding agents. This guide maps which features work everywhere versus agent-specific behavior.

## Supported Agents

| Agent | Reads AGENTS.md | Reads Root Only | Reads Nested | Notes |
|-------|-----------------|-----------------|--------------|-------|
| Codex CLI | ✅ | ✅ | ✅ | Full discovery chain, override support, 32 KiB limit |
| Cursor | ✅ | ✅ | ✅ | Also reads `.cursorrules` (agent-specific) |
| VS Code Copilot | ✅ | ✅ | ✅ | Workspace-wide, respects subdirectory files |
| GitHub Copilot Chat | ✅ | ✅ | — | Root file only in most contexts |
| Devin | ✅ | ✅ | — | Root file only |
| Jules | ✅ | ✅ | — | Root file only |
| Amp | ✅ | ✅ | — | Root file only |
| Gemini CLI | ✅ | ✅ | — | Root file only, also reads `GEMINI.md` |
| Windsurf | ✅ | ✅ | — | Also reads `.windsurfrules` |
| Claude Code | ❌ | — | — | Reads `CLAUDE.md` instead (symlink for compat) |
| Aider | ✅ | ✅ | — | Root file with `.aider` config |
| Continue | ✅ | ✅ | — | Root file via `.continue/` config |

**Legend:** ✅ = supported, — = not applicable, ❌ = uses different file

## Universal vs Agent-Specific Features

### Universal (Safe in Any AGENTS.md)

These patterns are safe because they are plain markdown that any agent reads as text:

| Feature | Example |
|---------|---------|
| Project description | "Next.js App Router with PostgreSQL" |
| Build/test/lint commands | "Run `pnpm test` before committing" |
| Directory structure | "API routes in `src/app/api/`" |
| Conventions | "Use named exports, not default exports" |
| Boundaries (Always/Ask/Never) | "Never modify migration files directly" |
| Error handling patterns | "Use Result type, not exceptions" |
| Dependency management | "Use pnpm, not npm or yarn" |
| Git workflow | "Commit messages follow Conventional Commits" |

### Agent-Specific (Do NOT Put in AGENTS.md)

| Feature | Where It Belongs | Agent |
|---------|-----------------|-------|
| `@import` syntax | `CLAUDE.md` | Claude Code only |
| `.claude/rules/` with `paths:` frontmatter | `.claude/rules/*.md` | Claude Code only |
| Hooks (pre-tool, post-tool) | `.claude/settings.json` | Claude Code only |
| `.cursorrules` config | `.cursorrules` | Cursor only |
| `.windsurfrules` config | `.windsurfrules` | Windsurf only |
| `GEMINI.md` config | `GEMINI.md` | Gemini CLI only |
| `.aider.conf.yml` | `.aider.conf.yml` | Aider only |
| MCP server config | Agent-specific config | Varies |

## Cross-Agent Strategy

### Single-Agent Team

If the team uses only one agent, use that agent's native config:
- Claude Code → `CLAUDE.md`
- Cursor → `.cursorrules` + `AGENTS.md`
- Codex CLI → `AGENTS.md`

### Multi-Agent Team (Recommended Approach)

1. **Write AGENTS.md** as the single source of truth
2. **Symlink** for Claude Code compatibility:
   ```bash
   ln -s AGENTS.md CLAUDE.md
   ```
3. **Add agent-specific config** only where needed:
   - `.cursorrules` for Cursor-specific behavior
   - `.claude/rules/` for path-scoped Claude rules
4. **Gitignore** personal overrides:
   ```gitignore
   AGENTS.override.md
   CLAUDE.local.md
   ```

### Monorepo Multi-Agent Strategy

```
repo/
├── AGENTS.md           # Universal: read by all agents
├── CLAUDE.md → AGENTS.md  # Symlink for Claude Code
├── .cursorrules        # Cursor-specific additions
├── packages/
│   ├── api/
│   │   └── AGENTS.md   # API-specific (Codex, Cursor, VS Code)
│   └── web/
│       └── AGENTS.md   # Web-specific
```

Agents that support nested files get richer context. Agents that only read root still get universal instructions.

## Migration Guide

### From `.cursorrules` to AGENTS.md

1. Copy content from `.cursorrules` to `AGENTS.md`
2. Remove Cursor-specific syntax (if any)
3. Keep `.cursorrules` with Cursor-only settings
4. Point `.cursorrules` to AGENTS.md for shared content

### From `CLAUDE.md` to AGENTS.md

1. Copy non-Claude-specific content to `AGENTS.md`
2. Remove `@import` lines (inline the referenced content)
3. Remove references to `.claude/rules/` or hooks
4. Symlink: `ln -s AGENTS.md CLAUDE.md`
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

# Cursor: Open project, check if instructions appear in chat context

# Claude Code
claude "What instructions have you loaded?"

# Generic: Ask any agent "What project conventions should you follow?"
```

The response should reflect your AGENTS.md content regardless of which agent reads it.
