# AGENTS.md Format Specification

Complete reference for AGENTS.md — the cross-agent configuration standard read by 20+ AI coding agents. Maintained by the Agentic AI Foundation under the Linux Foundation.

## What AGENTS.md Does

AGENTS.md is a plain markdown file placed at the repository root that provides project instructions to AI coding agents. Unlike agent-specific config files (CLAUDE.md, .cursorrules), AGENTS.md works across all major agents — making it the universal standard for multi-agent teams.

**Key properties:**
- Plain markdown only — no YAML frontmatter, no `@import`, no special syntax
- Read automatically by 20+ agents (Codex CLI, Cursor, VS Code Copilot, Devin, Jules, Amp, etc.)
- Supports nested files in subdirectories for monorepos
- Override mechanism via `AGENTS.override.md`
- Maximum combined size: 32 KiB (Codex CLI enforced)

## Adoption

Used by 60,000+ open-source projects. The standard is stewarded by the **Agentic AI Foundation** under the Linux Foundation. It is the closest thing to a universal agent configuration format.

## Format Rules

1. **Plain markdown** — any headings and structure work
2. **No YAML frontmatter** — agents parse raw text, not structured metadata
3. **No `@import` syntax** — that is a CLAUDE.md feature; inline everything
4. **No required fields** — write whatever sections are useful
5. **No file size enforcement by format** — but Codex CLI stops at `project_doc_max_bytes`

## Recommended Sections

```markdown
# Project Name

Brief description of what this project does.

## Commands
- Dev: `pnpm dev`
- Test: `pnpm test`
- Build: `pnpm build`
- Lint: `pnpm lint`

## Structure
- `src/` — Application source
- `tests/` — Test suites

## Conventions
- Critical convention 1
- Critical convention 2

## Boundaries
- Always: Run tests before committing
- Ask: Before adding production dependencies
- Never: Modify migration files directly

## Troubleshooting
- Common issue → fix
```

### The Boundaries Section

The **Boundaries** section is the most impactful part of AGENTS.md. It uses the Always/Ask/Never pattern to define clear guardrails:

| Level | Meaning | Example |
|-------|---------|---------|
| **Always** | Agent must do this every time | "Always run `pnpm typecheck && pnpm test` before committing" |
| **Ask** | Agent must get human approval first | "Ask before adding new production dependencies" |
| **Never** | Agent must never do this | "Never modify existing migration files" |

This pattern works across all agents because it uses natural language — no special syntax required.

## Discovery Algorithm (Codex CLI)

Codex builds an instruction chain once per session:

### Step 1: Global Scope

Check `~/.codex/` for:
1. `AGENTS.override.md` (if exists and non-empty) → use it
2. Else `AGENTS.md` (if exists and non-empty) → use it

At most one file at this level.

### Step 2: Project Scope

Starting at the project root (git root), walk down the directory tree to the current working directory. At each directory, check in order:

1. `AGENTS.override.md`
2. `AGENTS.md`
3. Any name in `project_doc_fallback_filenames`

Include at most one file per directory (first non-empty found).

### Step 3: Merge

Concatenate all discovered files from root → leaf, separated by blank lines. Files closer to the current directory appear later and **override** earlier content.

### Step 4: Size Limit

Stop adding files when combined size reaches `project_doc_max_bytes` (default: 32,768 bytes / 32 KiB). Empty files are skipped entirely.

## Override Mechanism

`AGENTS.override.md` takes precedence over `AGENTS.md` in the same directory.

When both exist, only `AGENTS.override.md` is read. The base `AGENTS.md` is ignored for that directory level.

**Use cases for overrides:**
- Temporary instructions during a migration
- Environment-specific rules (staging vs production)
- Quick experiments without modifying the shared file
- Sprint-specific priorities

Remove the override file to restore shared guidance.

## Codex CLI Configuration

Settings in `~/.codex/config.toml`:

```toml
project_doc_max_bytes = 32768
project_doc_fallback_filenames = ["TEAM_GUIDE.md", ".agents.md"]
```

| Setting | Default | Purpose |
|---------|---------|---------|
| `project_doc_max_bytes` | 32768 | Maximum combined instruction size |
| `project_doc_fallback_filenames` | `[]` | Alternate filenames to check |

Check order per directory: `AGENTS.override.md` → `AGENTS.md` → fallback filenames in order.

## Monorepo Nesting

Place nested AGENTS.md files in sub-packages. Agents that support nesting (Codex, Cursor, VS Code) read the nearest file.

```
repo/
├── AGENTS.md                          # Root: universal instructions
├── services/
│   ├── payments/
│   │   ├── AGENTS.md                  # Payment service specifics
│   │   └── AGENTS.override.md         # Temporary migration rules
│   └── auth/
│       └── AGENTS.md                  # Auth service specifics
└── packages/
    └── shared/
        └── AGENTS.md                  # Shared library rules
```

### What Codex Loads When Working in `services/payments/`

1. `~/.codex/AGENTS.md` (global)
2. `repo/AGENTS.md` (root)
3. `repo/services/payments/AGENTS.override.md` (nearest — override wins)

The base `services/payments/AGENTS.md` is skipped because the override exists.

### Nesting Rules

- Nested files should NOT repeat root-level instructions
- Each nested file should contain only instructions specific to that directory
- Root file: universal project conventions
- Nested files: package/service-specific rules
- Combined total across all levels must stay under 32 KiB

## General Agent Discovery (Non-Codex)

Most agents follow a simpler model:

1. Look for `AGENTS.md` at the repository root
2. Read it as context before starting work
3. Explicit user prompts override file content

| Agent | Reads Nested | Notes |
|-------|-------------|-------|
| Codex CLI | ✅ Full walk | Global → project → nested, with override support |
| Cursor | ✅ Workspace | Auto-reads from workspace root and subdirectories |
| VS Code Copilot | ✅ Workspace | Workspace-wide including subdirectories |
| Devin | ❌ Root only | Reads root AGENTS.md only |
| Jules | ❌ Root only | Reads root AGENTS.md only |
| Amp | ❌ Root only | Reads root AGENTS.md only |
| Gemini CLI | ❌ Root only | Also reads GEMINI.md natively |
| Windsurf | ❌ Root only | Uses .windsurfrules primarily |
| Aider | ❌ Root only | Requires `read: AGENTS.md` in config |

**For agents that only read root:** Keep the root file comprehensive. For agents that support nesting, root + nested files give richer context.

## Size Guidelines

| Scope | Ideal | Good | Maximum |
|-------|-------|------|---------|
| Root AGENTS.md | <80 lines | <150 lines | 200 lines |
| Nested AGENTS.md | <40 lines | <60 lines | 80 lines |
| Combined total | — | — | 32 KiB |

### Handling Large Projects

When content exceeds targets:

1. **Split into nested files** — move package-specific content to `packages/name/AGENTS.md`
2. **Use pointer references** — `"See docs/api-design.md for API conventions"` instead of inlining
3. **Trim ruthlessly** — apply the litmus test: "Would removing this cause the agent to make a mistake?"
4. **Deduplicate** — if a linter enforces a rule, do not repeat it in AGENTS.md

## Per-Agent Configuration Snippets

### Aider

```yaml
# .aider.conf.yml
read:
  - AGENTS.md
```

### Gemini CLI

```json
// .gemini/settings.json
{
  "contextFileName": "AGENTS.md"
}
```

### Cursor

No configuration needed — auto-reads AGENTS.md from workspace root.

### VS Code Copilot

No configuration needed — reads AGENTS.md workspace-wide.

### Claude Code

Claude Code reads `CLAUDE.md`, not `AGENTS.md`. For compatibility:

```markdown
@AGENTS.md

## Claude-Specific
<!-- Only add the next line if .claude/rules/ exists or you are creating rule files -->
- See `.claude/rules/` for path-scoped rules
- Add Claude-only memory or imports here only if needed
```

If Claude needs no extra memory or features, the wrapper can be just `@AGENTS.md`. Use a symlink only when the repo truly wants identical content and the environment supports it.

## Verification

After creating AGENTS.md, verify agents read it:

```bash
# Codex CLI
codex "Summarize your current instructions"

# Claude Code (with symlink or wrapper)
claude "What instructions have you loaded?"

# Gemini CLI
gemini "What project conventions should you follow?"

# Aider
aider --message "List the project conventions you know about"

# Generic (any agent)
[agent] "What project conventions should you follow?"
```

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| No guidance loaded | File is empty or not at project root | Ensure file has content; check workspace root |
| Wrong instructions | Override file in parent directory | Search upward for `AGENTS.override.md` files |
| Fallback names ignored | Not listed in config | Add to `project_doc_fallback_filenames` |
| Content truncated | Combined size exceeds 32 KiB | Trim content or split into nested directories |
| Instructions from wrong level | Global file overriding project | Check `~/.codex/AGENTS.md` for conflicts |
| Agent ignores AGENTS.md | Agent uses different filename | Check cross-agent-compat.md for agent-specific config |
| Symlink not followed | OS or tool limitation | Use thin wrapper file instead of symlink |
| Monorepo loads wrong file | Working directory mismatch | Verify `pwd` matches expected discovery path |
| Sections feel like a generic template | Content not grounded in repo evidence | Every section needs 3+ repo-specific facts to justify its existence |
| Commands fail when run | Commands were guessed, not verified | Re-verify every command against package.json/Makefile/CI |
| Config file is 200+ lines | Too much noise, agents de-prioritize | Cut to <80 lines -- if that is not possible, use progressive disclosure |

## Good vs Bad Content Examples

### Commands Section

**Bad -- invented commands:**
```markdown
## Commands
- Dev: `npm run dev`
- Test: `npm test`
- Build: `npm run build`
```
*(These look plausible but were never verified. The project actually uses pnpm and has different script names.)*

**Good -- verified commands:**
```markdown
## Commands
- Dev: `pnpm dev` (runs Next.js dev server on port 3000)
- Test: `pnpm test:unit` (Jest, no watch mode in CI)
- Build: `pnpm build` (outputs to .next/)
- Lint: `pnpm lint` (ESLint + Prettier check)
```

### Conventions Section

**Bad -- generic advice:**
```markdown
## Conventions
- Write clean, readable code
- Follow best practices
- Use meaningful variable names
- Handle errors properly
```

**Good -- project-specific rules:**
```markdown
## Conventions
- Named exports only, no default exports
- Use `Result<T, E>` for error handling, not try/catch
- Route handlers in `src/app/api/` -- one file per endpoint
- Database queries go through `src/lib/db.ts`, never direct SQL
```

## AGENTS.md vs CLAUDE.md Feature Comparison

| Feature | AGENTS.md | CLAUDE.md |
|---------|-----------|-----------|
| Format | Plain markdown | Markdown + @import |
| Cross-agent support | 20+ agents | Claude Code only |
| Path-scoped rules | ❌ Use nested files | ✅ .claude/rules/ with paths: |
| Override mechanism | AGENTS.override.md | CLAUDE.local.md |
| Import syntax | ❌ Not supported | ✅ @file.md |
| Frontmatter | ❌ Not supported | ✅ Optional YAML |
| Size limit | 32 KiB (Codex) | ~50 KB post-import |
| Discovery | Walk-up algorithm | Walk-up + on-demand |
| Hooks/commands | ❌ | ✅ .claude/hooks/, .claude/commands/ |
| Named agents | ❌ | ✅ .claude/agents/ |
| Maintainer | Agentic AI Foundation | Anthropic |
