---
name: init-agent-config
description: Use skill if you are creating or auditing CLAUDE.md and AGENTS.md files that configure AI coding agents for your project.
---

# Init Agent Config

Generate, audit, or migrate AGENTS.md and/or CLAUDE.md files that configure AI coding agents for a repository. AGENTS.md is the cross-agent standard (Codex, Cursor, VS Code, Devin, Jules, Amp, Gemini CLI, 20+ agents). CLAUDE.md is Claude Code–specific, supporting `@import`, path-scoped rules, hooks, commands, named agents, and progressive disclosure via `agent_docs/`. When both are needed, AGENTS.md is the source of truth and CLAUDE.md is a thin wrapper that imports it.

## Decision tree

```
What do you need?
│
├── Create new agent config
│   ├── Which agents does the team use?
│   │   ├── Multiple AI agents ──────────────► AGENTS.md + thin CLAUDE.md wrapper
│   │   ├── Claude Code only ────────────────► CLAUDE.md standalone
│   │   └── Single non-Claude agent only ────► AGENTS.md only
│   │
│   ├── What type of project?
│   │   ├── Minimal / script / CLI ──────────► references/project-templates.md §1
│   │   ├── Node.js / TypeScript ────────────► references/project-templates.md §2
│   │   ├── Python ──────────────────────────► references/project-templates.md §3
│   │   ├── Go ──────────────────────────────► references/project-templates.md §4
│   │   ├── Rust ────────────────────────────► references/project-templates.md §5
│   │   ├── React / Next.js ─────────────────► references/project-templates.md §6
│   │   ├── Monorepo ────────────────────────► references/project-templates.md §7
│   │   └── Django ──────────────────────────► references/project-templates.md §8
│   │
│   ├── How to write effective instructions
│   │   ├── WHAT/WHY/HOW framework ──────────► references/writing-guidelines.md
│   │   ├── Context window economics ────────► references/writing-guidelines.md
│   │   ├── Progressive disclosure ──────────► references/writing-guidelines.md
│   │   └── Dual-file strategy ──────────────► references/writing-guidelines.md
│   │
│   └── Need CLAUDE.md features?
│       ├── @import syntax ──────────────────► references/claude-md-format.md
│       ├── Path-scoped rules (.claude/rules/) ► references/claude-md-format.md
│       ├── Memory hierarchy ────────────────► references/claude-md-format.md
│       ├── Commands / hooks / agents ───────► references/claude-md-format.md
│       └── Settings and exclusions ─────────► references/claude-md-format.md
│
├── Audit existing config
│   ├── Quality scoring rubric ──────────────► references/audit-and-migration.md
│   ├── Audit checklist (6 phases) ──────────► references/audit-and-migration.md
│   └── Audit output template ───────────────► references/audit-and-migration.md
│
├── Migrate between formats
│   ├── .cursorrules → AGENTS.md ────────────► references/audit-and-migration.md
│   ├── Standalone CLAUDE.md → dual-file ────► references/audit-and-migration.md
│   ├── copilot-instructions.md → AGENTS.md ─► references/audit-and-migration.md
│   └── No config → new setup ───────────────► references/audit-and-migration.md
│
├── AGENTS.md specifics
│   ├── Format specification ────────────────► references/agents-md-format.md
│   ├── Discovery algorithm (Codex CLI) ─────► references/agents-md-format.md
│   ├── Override mechanism ──────────────────► references/agents-md-format.md
│   ├── Monorepo nesting ───────────────────► references/agents-md-format.md
│   └── Size limits & troubleshooting ───────► references/agents-md-format.md
│
└── Cross-agent compatibility
    ├── Agent support matrix (15+ agents) ───► references/cross-agent-compat.md
    ├── Universal vs agent-specific features ► references/cross-agent-compat.md
    ├── Multi-agent repository layout ───────► references/cross-agent-compat.md
    └── Per-agent config snippets ───────────► references/cross-agent-compat.md
```

## Quick start

### Fastest path: single-agent CLAUDE.md

```markdown
# My Project

TypeScript API using Fastify + Drizzle ORM + PostgreSQL.

## Commands
- Dev: `pnpm dev`
- Test: `pnpm test`
- Build: `pnpm build`
- Lint: `pnpm lint`

## Conventions
- Strict TypeScript (no `any` without justification comment)
- Named exports only, no default exports
- Validate inputs with Zod schemas

## Boundaries
- Always: Run `pnpm typecheck && pnpm test` before committing
- Ask: Before adding production dependencies
- Never: Modify migration files directly
```

### Fastest path: multi-agent (AGENTS.md + thin CLAUDE.md)

**AGENTS.md** — same content as above (universal, plain markdown)

**CLAUDE.md** — thin wrapper:

```markdown
@AGENTS.md

## Claude-Specific
- Path-scoped rules in `.claude/rules/`
- Use `/compact` when context grows large
```

## Workflow

### Phase 1: Explore the Repository

Map the codebase before writing anything.

**Tech stack** — scan config files:
- `package.json`, `tsconfig.json` → TypeScript/JavaScript
- `pyproject.toml`, `requirements.txt` → Python
- `Cargo.toml` → Rust; `go.mod` → Go
- `docker-compose.yml`, `.github/workflows/` → Infrastructure/CI

**Existing agent config** — check for:
- `AGENTS.md`, `AGENTS.override.md`
- `CLAUDE.md`, `CLAUDE.local.md`, `.claude/rules/`
- `.cursorrules`, `.windsurfrules`, `GEMINI.md`
- `.github/copilot-instructions.md`
- `CONTRIBUTING.md`, `README.md`

If files exist, read them. Complement — do not blindly overwrite.

**Linting & formatting** — critical check:
- ESLint, Prettier, Biome → skip JS/TS formatting rules
- Black, Ruff → skip Python formatting
- rustfmt, clippy → skip Rust formatting

Never document what linters enforce. Agent instructions cover semantic intent, not syntax.

**Catalog verified commands** — scan and record only commands that exist:
- `package.json` scripts
- `Makefile` / `Justfile` targets
- `.github/workflows/` CI steps
- `pyproject.toml` scripts
- `Cargo.toml` aliases

NEVER invent commands. If uncertain, write `See [file]` instead of guessing.

### Phase 2: Choose Output Strategy

| Scenario | Generate |
|----------|----------|
| Team uses multiple AI agents | AGENTS.md (primary) + CLAUDE.md (thin wrapper with `@AGENTS.md`) |
| Claude Code only | CLAUDE.md standalone |
| Single non-Claude agent only | AGENTS.md only |
| Existing CLAUDE.md, adding cross-agent | AGENTS.md + refactor CLAUDE.md to thin wrapper |
| Existing AGENTS.md, adding Claude features | CLAUDE.md with `@AGENTS.md` import |

### Phase 3: Write Using WHAT/WHY/HOW

Every instruction answers one of three questions:

| Layer | Content | Example |
|-------|---------|---------|
| **WHAT** | Technical reality agents cannot infer from code | "Next.js App Router, NOT Pages" |
| **WHY** | Reasoning behind non-obvious decisions | "Sessions not JWT because SSR needs server-readable auth" |
| **HOW** | Commands that must be exact | "`pnpm dev` (NOT npm — pnpm workspaces required)" |

Exclude anything an agent can infer by reading the code.

### Phase 4: Right-Size the Files

| File | Ideal | Good | Maximum |
|------|-------|------|---------|
| AGENTS.md (root) | <80 lines | <150 lines | 200 lines |
| AGENTS.md (nested) | <40 lines | <60 lines | 80 lines |
| CLAUDE.md (standalone) | <60 lines | <100 lines | 200 lines |
| CLAUDE.md (thin wrapper) | <20 lines | <30 lines | 50 lines |
| Combined total (Codex limit) | — | — | 32 KiB |

**Litmus test:** "Would removing this cause the agent to make a mistake?" If no → cut it.

### Phase 5: Structure the Content

**AGENTS.md sections:** Project description → Commands → Structure → Conventions → Boundaries → Troubleshooting

**CLAUDE.md standalone sections:** Project description → Stack → Commands → Architecture → Non-obvious patterns → Conventions

**CLAUDE.md thin wrapper:** `@AGENTS.md` → Claude-specific additions only

For advanced organization (monorepos, progressive disclosure, path-scoped rules), see the references routed from the decision tree.

### Phase 6: Validate

- [ ] All commands verified against package.json / Makefile / CI
- [ ] No instructions for things linters enforce
- [ ] No obvious facts agents can infer from code
- [ ] File sizes within targets
- [ ] No secrets or credentials
- [ ] No stale paths or outdated versions
- [ ] Instructions are specific and measurable

### Phase 7: Output

Present generated files as:
1. **File tree** showing all generated files
2. **Each file** in a fenced code block with path as heading
3. **Agent compatibility note** per file — which agents read it
4. **Quality score** (if auditing) — before/after comparison

## Common pitfalls

| Pitfall | Fix |
|---------|-----|
| Documenting what linters enforce | Linters are deterministic and cheaper. Never duplicate lint rules in agent config. |
| Using `@import` in AGENTS.md | Claude-only feature. AGENTS.md is plain markdown — inline everything. |
| Adding YAML frontmatter to AGENTS.md | Not supported. Plain markdown only. |
| Exceeding 32 KiB combined | Codex truncates beyond this. Trim or split into nested files. |
| Duplicating content between AGENTS.md and CLAUDE.md | Use thin wrapper pattern. CLAUDE.md imports AGENTS.md and adds only Claude-specific features. |
| Inventing commands | Every command must be verified against package.json, Makefile, or CI. If uncertain: `See [file]`. |
| Documenting the obvious | If the code shows it, agents already know it. "This is a React app" adds nothing. |
| Generic advice not specific to the project | "Write clean code" helps no one. "Use Zod for all API input validation" helps. |
| Mixing human docs with agent docs | AGENTS.md and CLAUDE.md complement README.md. Do not merge them. |
| Embedding stale code snippets | Reference files by path instead of pasting code that gets outdated. |
| Auto-generating without review | `/init` output is a starting point, not a final product. Always curate. |
| Missing Boundaries section | The most impactful section. Always include Always/Ask/Never rules. |

## Minimal reading sets

### "I need to create a CLAUDE.md for a Claude-only team"

- `references/claude-md-format.md`
- `references/writing-guidelines.md`
- `references/project-templates.md`

### "I need AGENTS.md for a multi-agent team"

- `references/agents-md-format.md`
- `references/cross-agent-compat.md`
- `references/project-templates.md`

### "I need to audit an existing config file"

- `references/audit-and-migration.md`
- `references/writing-guidelines.md`

### "I need to migrate from .cursorrules or another format"

- `references/audit-and-migration.md`
- `references/cross-agent-compat.md`

### "I need both AGENTS.md and CLAUDE.md (dual-file pattern)"

- `references/agents-md-format.md`
- `references/claude-md-format.md`
- `references/writing-guidelines.md`
- `references/project-templates.md`

### "I need a monorepo configuration with path-scoped rules"

- `references/claude-md-format.md`
- `references/agents-md-format.md`
- `references/project-templates.md` (§7 Monorepo + §Monorepo with Path-Scoped Rules)

### "I need the complete reference for all features"

- `references/claude-md-format.md`
- `references/agents-md-format.md`
- `references/cross-agent-compat.md`
- `references/writing-guidelines.md`
- `references/project-templates.md`
- `references/audit-and-migration.md`

## Reference files

| File | When to read |
|------|--------------|
| `references/claude-md-format.md` | Creating or modifying CLAUDE.md files. Covers @import syntax, .claude/rules/ path-scoped rules, memory hierarchy, settings, hooks, commands, and auto memory. |
| `references/agents-md-format.md` | Creating or modifying AGENTS.md files. Covers format spec, Codex CLI discovery algorithm, override mechanism, monorepo nesting, size limits, and per-agent config snippets. |
| `references/cross-agent-compat.md` | Team uses multiple AI agents. Covers the 15+ agent support matrix, universal vs agent-specific features, multi-agent repository layout, and migration guides between formats. |
| `references/writing-guidelines.md` | Writing any agent config file. Covers WHAT/WHY/HOW framework, context window economics, signal quality checks, progressive disclosure, safety gates, and writing style guide. |
| `references/project-templates.md` | Starting from a template. Contains AGENTS.md + CLAUDE.md templates for 8 project types: minimal, Node.js/TypeScript, Python, Go, Rust, React/Next.js, monorepo, and Django. |
| `references/audit-and-migration.md` | Auditing existing configs or migrating between formats. Covers quality scoring rubric (5 dimensions), 6-phase audit checklist, audit output template, and step-by-step migration guides from .cursorrules, CLAUDE.md, and copilot-instructions.md. |

## Final reminder

This skill is split into focused, atomic reference files organized by topic. Do not load everything at once. Start with the smallest relevant reading set above, then expand into neighboring references only when the task requires them. Every reference file is explicitly routed from the decision tree.
