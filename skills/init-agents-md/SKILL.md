---
name: init-agents-md
description: Use skill if you are creating, auditing, or maintaining AGENTS.md files that provide cross-agent instructions for AI coding tools.
---

# Init AGENTS.md

Generate an AGENTS.md file — the open standard for AI coding agent instructions, supported by 20+ agents including Codex, Cursor, VS Code, Devin, GitHub Copilot, Jules, Amp, Gemini CLI, and more.

## What This Produces

An `AGENTS.md` file at the project root that AI coding agents read before starting work. For monorepos, also generates nested `AGENTS.md` files in sub-packages. Unlike CLAUDE.md (Claude-specific), AGENTS.md works across the entire agent ecosystem.

## When to Use AGENTS.md vs CLAUDE.md

| Scenario | Use |
|----------|-----|
| Team uses multiple AI agents | AGENTS.md (cross-compatible) |
| Claude Code only | CLAUDE.md (supports imports, rules, hooks) |
| Both | AGENTS.md as source of truth + symlink CLAUDE.md |

To share one file across both:
```bash
# Write instructions in AGENTS.md, symlink for Claude
ln -s AGENTS.md CLAUDE.md
```

## Workflow

### Phase 1: Explore the Repository

Map the codebase before writing anything.

**Structure**
- Monorepo vs single-service
- Directory layout, package boundaries
- Build output directories

**Tech Stack** — Scan config files:
- `package.json`, `tsconfig.json` → TypeScript/JavaScript
- `pyproject.toml`, `requirements.txt` → Python
- `Cargo.toml` → Rust; `go.mod` → Go
- `docker-compose.yml`, `.github/workflows/` → Infrastructure/CI

**Existing Configuration** — Check for:
- `AGENTS.md`, `AGENTS.override.md`
- `CLAUDE.md`, `.cursorrules`, `.windsurfrules`
- `CONTRIBUTING.md`, `README.md`

If agent instruction files already exist, read them. Complement and improve, do not overwrite.

**Linting & Formatting** — Same rule as CLAUDE.md: never put instructions for things linters already enforce.

### Phase 2: Apply the WHAT/WHY/HOW Framework

| Layer | Content | Example |
|-------|---------|---------|
| **WHAT** | Technical reality agents cannot infer | "Next.js App Router, NOT Pages" |
| **WHY** | Reasoning behind decisions | "Sessions not JWT because SSR needs server-readable auth" |
| **HOW** | Commands that must be exact | "`pnpm dev` (NOT npm — pnpm workspaces required)" |

Exclude anything an agent can infer from reading the code.

### Phase 3: Right-Size the File

AGENTS.md is plain markdown — no `@import` syntax, no YAML frontmatter, no special features. Keep it focused.

| Target | Lines | When |
|--------|-------|------|
| Ideal | Under 80 | Simple apps |
| Good | Under 150 | Standard projects |
| Maximum | 200 | Split nested files beyond this |

**Codex CLI enforces a 32 KiB combined size limit** (`project_doc_max_bytes`). Nested files concatenate toward this limit.

**Litmus test:** "Would removing this cause the agent to make a mistake?" If no, cut it.

### Phase 4: Structure the File

Recommended sections:

```markdown
# Project Name

Brief description.

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

The **Boundaries** section (Always/Ask/Never) is an AGENTS.md pattern for defining agent guardrails. See `references/templates.md` for project-type-specific templates.

### Phase 5: Handle Monorepos

AGENTS.md supports a hierarchy where agents read the **nearest** file. Place additional files inside sub-packages:

```
repo/
├── AGENTS.md                    # Root: universal instructions
├── packages/
│   ├── api/
│   │   └── AGENTS.md            # API-specific instructions
│   ├── web/
│   │   └── AGENTS.md            # Web-specific instructions
│   └── shared/
│       └── AGENTS.md            # Shared library rules
```

**Discovery rules (Codex CLI):**
1. Start at global scope (`~/.codex/AGENTS.md`)
2. Walk from project root down to current working directory
3. At each directory: check `AGENTS.override.md`, then `AGENTS.md`
4. Concatenate root → leaf (later files override earlier ones)
5. Stop when combined size reaches 32 KiB

**Override mechanism:** `AGENTS.override.md` takes precedence over `AGENTS.md` in the same directory. Use for temporary overrides without deleting the base file.

See `references/discovery-spec.md` for the complete discovery algorithm.

### Phase 6: Validate

- [ ] Plain markdown only — no `@import`, no YAML frontmatter
- [ ] Under 200 lines per file, under 32 KiB combined
- [ ] All documented commands verified against actual project config
- [ ] Directory references match actual structure
- [ ] No stale paths or outdated dependency versions
- [ ] Instructions are specific, not vague
- [ ] Monorepo nested files do not repeat root-level instructions
- [ ] No secrets or credentials in the file
- [ ] Boundaries section uses Always/Ask/Never format

### Phase 7: Output

Present generated files as:

1. **File tree** showing all generated files
2. **Each file** in a fenced code block with path as heading
3. **Supported agents note** listing which agents will read the file

## Reference Files

| File | When to read |
|------|--------------|
| `references/discovery-spec.md` | Read when handling monorepo hierarchies, override files, or understanding how agents discover and merge AGENTS.md files. |
| `references/cross-agent-compat.md` | Read when the team uses multiple AI agents and needs to understand which features work across agents vs are agent-specific. |
| `references/templates.md` | Read when generating a new AGENTS.md and need a starting template for the detected project type. |

## Anti-Patterns

- **Using `@import` syntax** — Not supported in AGENTS.md (Claude-specific feature). Inline all content.
- **Adding YAML frontmatter** — AGENTS.md is plain markdown. No frontmatter.
- **Duplicating between root and nested files** — Nested files override, not supplement. Do not repeat.
- **Documenting the obvious** — If the code shows it, agents already know it.
- **Exceeding 32 KiB combined** — Codex truncates beyond this. Split into nested files or trim.
- **Mixing human docs with agent docs** — AGENTS.md complements README.md, do not merge them.
