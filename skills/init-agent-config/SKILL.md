---
name: init-agent-config
description: Use skill if you are creating or auditing CLAUDE.md and AGENTS.md files that configure AI coding agents for your project.
---

# Init Agent Config

Generate AGENTS.md and/or CLAUDE.md files that configure AI coding agents for a repository. AGENTS.md is the cross-agent standard (Codex, Cursor, VS Code, Devin, Copilot, Jules, Amp, Gemini CLI, 20+ agents). CLAUDE.md is Claude Code–specific, supporting imports, path-scoped rules, hooks, and progressive disclosure via `agent_docs/`. When both are needed, AGENTS.md is the source of truth and CLAUDE.md is a thin wrapper that imports it.

## Decision Table

| Scenario | Generate |
|----------|----------|
| Team uses multiple AI agents | AGENTS.md (primary) + CLAUDE.md (thin wrapper with `@AGENTS.md`) |
| Claude Code only | CLAUDE.md standalone |
| Single non-Claude agent only | AGENTS.md only |
| Existing CLAUDE.md, adding cross-agent support | AGENTS.md + refactor CLAUDE.md to thin wrapper |
| Existing AGENTS.md, adding Claude features | CLAUDE.md with `@AGENTS.md` import |

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

**Existing Agent Config** — Check for:
- `AGENTS.md`, `AGENTS.override.md`
- `CLAUDE.md`, `CLAUDE.local.md`, `.claude/rules/`
- `.cursorrules`, `.windsurfrules`, `GEMINI.md`
- `CONTRIBUTING.md`, `README.md`

If files exist, read them. Complement and improve — do not overwrite blindly.

**Linting & Formatting** — Critical check:
- ESLint, Prettier, Biome → skip JS/TS formatting rules
- Black, Ruff → skip Python formatting
- rustfmt, clippy → skip Rust formatting

Never document what linters enforce. Agent instructions cover semantic intent, not syntax.

**Safety Gate: Catalog Verified Commands**

Scan these sources and record only commands that actually exist:
- `package.json` scripts
- `Makefile` / `Justfile` targets
- `.github/workflows/` CI steps
- `pyproject.toml` scripts
- `Cargo.toml` aliases

NEVER invent commands. If uncertain, write `See [file]` instead of guessing.

### Phase 2: Choose Output Strategy

Apply the decision table above. Determine which files to generate and in which format.

For the dual-file pattern (AGENTS.md + thin CLAUDE.md), the architecture is:
1. AGENTS.md holds all cross-agent instructions
2. CLAUDE.md imports AGENTS.md and adds only Claude-specific features
3. Zero duplication between files

### Phase 3: Apply the WHAT/WHY/HOW Framework

Every instruction answers one of three questions:

| Layer | Content | Example |
|-------|---------|---------|
| **WHAT** | Technical reality agents cannot infer from code | "Next.js App Router, NOT Pages" |
| **WHY** | Reasoning behind non-obvious decisions | "Sessions not JWT because SSR needs server-readable auth" |
| **HOW** | Commands that must be exact | "`pnpm dev` (NOT npm — pnpm workspaces required)" |

**Exclude anything an agent can infer by reading the code.** If there is a React component, agents know it is React. If `package.json` has scripts, agents can read them. Document only the non-obvious.

### Phase 4: Right-Size the Files

| File | Ideal | Good | Maximum |
|------|-------|------|---------|
| AGENTS.md (root) | <80 lines | <150 lines | 200 lines |
| AGENTS.md (nested) | <40 lines | <60 lines | 80 lines |
| CLAUDE.md (standalone) | <60 lines | <100 lines | 200 lines |
| CLAUDE.md (thin wrapper) | <20 lines | <30 lines | 50 lines |
| Combined total (Codex limit) | — | — | 32 KiB |

**Litmus test for every line:** "Would removing this cause the agent to make a mistake?" If no → cut it.

Claude Code uses ~50 system prompt instruction slots. Frontier LLMs reliably follow 150–200 instructions. Every line in your config competes for attention against conversation context.

### Phase 5: Structure the Content

**AGENTS.md — Recommended sections:**

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

**CLAUDE.md standalone — Recommended sections:**

```markdown
# Project Name

Brief description.

## Stack
- Language/Framework + version
- Key dependencies
- Package manager

## Commands
- Dev: `pnpm dev`
- Test: `pnpm test`
- Build: `pnpm build`

## Architecture
- Key architectural decisions

## Non-Obvious Patterns
- Patterns that would cause mistakes if unknown

## Conventions
- Critical convention 1
```

**CLAUDE.md thin wrapper pattern:**

```markdown
@AGENTS.md

# Claude-Specific

## Memory
- Use `agent_docs/` for on-demand loading

## Rules
- See `.claude/rules/` for path-scoped rules

## Preferences
- [Claude-specific behavioral preferences only]
```

### Phase 6: Handle Advanced Organization

Branch based on output strategy.

**For CLAUDE.md projects — Progressive disclosure:**

When root exceeds 100 lines or the project has 3+ workflow areas:

1. Keep root `CLAUDE.md` under 60–80 lines with universal instructions
2. Create `agent_docs/` with task-specific markdown files
3. Reference those files from root with one-line descriptions

```
agent_docs/
├── building.md
├── testing.md
├── code-conventions.md
└── service-architecture.md
```

Use `.claude/rules/` for path-scoped conditional rules:

```yaml
---
paths:
  - "src/api/**/*.ts"
---

# API Rules
- Return consistent error shapes: `{ error: string, code: number }`
- Validate all inputs with Zod schemas
```

Use `CLAUDE.local.md` for personal gitignored overrides. Use `@import` syntax for referencing existing docs.

**For AGENTS.md projects — Monorepo nesting:**

Place nested files in sub-packages. Agents read the **nearest** file.

```
repo/
├── AGENTS.md                    # Root: universal instructions
├── packages/
│   ├── api/
│   │   └── AGENTS.md            # API-specific
│   ├── web/
│   │   └── AGENTS.md            # Web-specific
│   └── shared/
│       └── AGENTS.md            # Shared library rules
```

Discovery rules (Codex CLI):
1. Start at global scope (`~/.codex/AGENTS.md`)
2. Walk from project root down to working directory
3. At each directory: `AGENTS.override.md` takes precedence over `AGENTS.md`
4. Concatenate root → leaf (later files override earlier)
5. Stop at 32 KiB combined

No `@import` in AGENTS.md — inline everything. No YAML frontmatter.

Symlink strategy for dual-agent teams:
```bash
ln -s AGENTS.md CLAUDE.md
```

### Phase 7: Validate

Combined checklist for both formats:

- [ ] All commands verified against package.json / Makefile / CI configs
- [ ] No instructions for things linters already enforce
- [ ] No obvious facts agents can infer from code
- [ ] File sizes within targets (see Phase 4 table)
- [ ] No secrets or credentials
- [ ] No stale paths, dead links, or outdated versions
- [ ] Instructions are specific and measurable, not vague

**AGENTS.md-specific:**
- [ ] Plain markdown only — no `@import`, no YAML frontmatter
- [ ] Under 32 KiB combined across all nested files
- [ ] Boundaries section uses Always/Ask/Never format
- [ ] Nested files do not repeat root-level instructions

**CLAUDE.md-specific:**
- [ ] Any `@import` paths resolve to real files
- [ ] Progressive disclosure files referenced from root
- [ ] `.claude/rules/` files have valid `paths:` frontmatter
- [ ] Thin wrapper pattern: no duplicated content from AGENTS.md

**Quality scoring (for audits):**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Commands | 25% | All build/test/lint/deploy commands present and verified |
| Architecture | 25% | Non-obvious architectural decisions documented |
| Non-obvious patterns | 20% | Gotchas and conventions that prevent mistakes |
| Conciseness | 15% | No filler, no linter-enforced rules, no obvious facts |
| Actionability | 15% | Every instruction is specific and measurable |

Score each 0–5. Total = weighted average. Target ≥ 4.0.

### Phase 8: Output

Present generated files as:

1. **File tree** showing all generated files
2. **Each file** in a fenced code block with path as heading
3. **Agent compatibility note** per file — which agents read it
4. **Quality score** (if auditing existing files) — before/after comparison

## Reference Files

| File | When to read |
|------|--------------|
| `references/best-practices.md` | Read when applying the WHAT/WHY/HOW framework, right-sizing files, or scoring quality of existing agent config files. |
| `references/memory-hierarchy.md` | Read when generating CLAUDE.md and need to decide what goes in the file vs `.claude/rules/` vs `agent_docs/` vs user memory. |
| `references/discovery-spec.md` | Read when handling AGENTS.md monorepo hierarchies, override files, or understanding how Codex discovers and merges instruction files. |
| `references/cross-agent-compat.md` | Read when the team uses multiple AI agents and need to understand which features work across agents vs are agent-specific. |
| `references/templates.md` | Read when generating new files and need a starting template for the detected project type. Contains both AGENTS.md and CLAUDE.md templates. |

## Anti-Patterns

- **Documenting what linters enforce** — Linters are deterministic, cheaper, and faster. Never duplicate lint rules.
- **Using `@import` in AGENTS.md** — Claude-only feature. AGENTS.md is plain markdown; inline all content.
- **Adding YAML frontmatter to AGENTS.md** — Not supported. Plain markdown only.
- **Exceeding 32 KiB combined** — Codex truncates beyond this. Trim or split into nested files.
- **Duplicating content between AGENTS.md and CLAUDE.md** — Use the thin wrapper pattern. CLAUDE.md imports AGENTS.md and adds only Claude-specific features.
- **Inventing commands** — Every command must be verified against package.json, Makefile, or CI configs. If uncertain, write `See [file]`.
- **Documenting the obvious** — If the code shows it, agents already know it.
- **Generic advice not specific to the project** — "Write clean code" helps no one. "Use Zod for all API input validation" helps.
- **Mixing human docs with agent docs** — AGENTS.md and CLAUDE.md complement README.md. Do not merge them.
- **Embedding code snippets** — Reference files by path instead of pasting stale code.
- **Auto-generating without review** — `/init` output is a starting point, not a final product. Always curate.
