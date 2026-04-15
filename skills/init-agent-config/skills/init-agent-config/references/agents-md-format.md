# AGENTS.md Authoring Guide

How to design, write, and verify an AGENTS-first instruction hierarchy with the minimum number of files that still preserves folder-local signal.

## Purpose

`AGENTS.md` is the primary instruction surface in this skill's operating model.

Use it to capture:
- commands agents must run correctly
- architecture boundaries agents cannot infer safely
- folder-local risks and conventions
- Always/Ask/Never rules that prevent real mistakes

Do not use it for:
- agent-native syntax
- generic coding advice
- duplicated README prose
- comments about unresolved uncertainty

## Core Rules

1. Plain markdown only.
2. Root file first, folder files second.
3. Each child file contains only the local delta from its parent.
4. Default to local files for meaningful `src/*`, `apps/*`, `services/*`, or `packages/*` subtrees discovered in Wave 2.
5. Every file must answer: `What does a coder working in this scope need to know to avoid mistakes?`
6. If a line would not prevent a mistake, cut it.
7. Companion agent files must point back to AGENTS rather than competing with it.

## Root vs Folder Scope

| Scope | Include | Exclude |
|------|---------|---------|
| Root `AGENTS.md` | Verified repo-wide commands, top-level architecture, shared conventions, repo-wide boundaries | Folder-only entrypoints, deep implementation trivia, duplicated docs |
| Folder `AGENTS.md` | Local entrypoints, folder-specific commands, non-obvious conventions, local risks, parent overrides | Generic advice, full root command list, repo-wide policy already stated above |

## Authoring Mental Model

Write for the coder standing in the current folder.

Ask these questions before adding a line:
- What mistake would happen here without this instruction?
- Is this shared across the repo or only true in this subtree?
- Is this a real command, boundary, or non-obvious design choice?
- Does this belong in the parent file instead?

## WHAT / WHY / HOW

Every strong instruction belongs to one of these buckets:

### WHAT

Document technical reality the agent cannot infer safely.

Good:
- `src/app/ uses App Router, not Pages Router`
- `packages/contracts/ owns public API schemas`

Bad:
- `This project uses TypeScript`
- `Components live in src/components/`

### WHY

Explain the reason behind a non-obvious choice when it changes agent behavior.

Good:
- `Use sessions, not JWT, because SSR reads auth state server-side`
- `Keep SQL in sqlc definitions because generated types are the contract`

### HOW

Document verified commands or workflows the agent must execute correctly.

Good:
- `Test API contracts: pnpm test -- src/api`
- `Regenerate types with cargo build -p contracts`

Bad:
- guessed commands
- vague steps like `run the usual tests`

## Recommended Sections

Only create a section when repo evidence justifies it.

### Root File

```markdown
# Project Name

## Commands
- Dev: `verified command`
- Test: `verified command`

## Architecture
- `src/api/` — API boundary
- `src/web/` — UI boundary

## Conventions
- Project-specific rule

## Boundaries
- Always: repo-wide invariant
- Ask: change that needs approval
- Never: dangerous action
```

### Folder File

```markdown
# src/api

## Local Focus
- HTTP handlers, request validation, error shapes

## Local Commands
- Test: `verified folder-level command`

## Local Conventions
- Rule specific to this subtree

## Local Boundaries
- Always: action required in this folder
- Never: local mistake to avoid
```

## Folder Coverage Strategy

Start from the filesystem, not from templates.

1. Run `tree -d .` or `tree -dL 2 .`.
2. Mark the repo root plus each meaningful `src/*`, `apps/*`, `services/*`, or `packages/*` folder.
3. After Wave 2, create a local `AGENTS.md` for each first-level subtree with its own workflow, entry points, or failure modes.
4. If a folder has only a tiny local delta, keep the file short instead of skipping it.
5. Add deeper nesting only when the second-level subtree has genuinely different rules from its parent.

**Default bias:** if `src/` contains `api/`, `components/`, `lib/`, and `jobs/`, assume each of those needs its own file unless discovery proves otherwise.

## Example Hierarchy

```text
repo/
├── AGENTS.md
├── CLAUDE.md -> AGENTS.md
├── src/
│   ├── api/
│   │   ├── AGENTS.md
│   │   └── CLAUDE.md -> AGENTS.md
│   ├── components/
│   │   ├── AGENTS.md
│   │   └── CLAUDE.md -> AGENTS.md
│   ├── lib/
│   │   ├── AGENTS.md
│   │   └── CLAUDE.md -> AGENTS.md
│   └── jobs/
│       ├── AGENTS.md
│       └── CLAUDE.md -> AGENTS.md
└── tests/
    └── AGENTS.md
```

Use the same pattern at `apps/*`, `services/*`, or `packages/*` when those directories are the true architecture boundaries.

## Size and Signal

| File | Ideal | Good | Hard Ceiling |
|------|-------|------|--------------|
| Root `AGENTS.md` | <80 lines | <120 lines | 200 lines |
| Folder `AGENTS.md` | <25 lines | <40 lines | 80 lines |

For every line, ask:

| Check | If true |
|------|---------|
| The agent can infer it from code | Cut it |
| Tooling already enforces it | Cut it |
| It belongs in the parent file | Move it up |
| It belongs in one folder only | Move it down |
| It is generic advice | Rewrite or cut it |
| It would not prevent a mistake | Cut it |

## Good vs Bad Nested Files

### Bad: child file repeats the parent

```markdown
# src/api

## Commands
- Dev: `pnpm dev`
- Test: `pnpm test`

## Conventions
- Use pnpm
- Run tests before committing
```

This wastes context because it mostly repeats root-level rules.

### Good: child file is local

```markdown
# src/api

## Local Focus
- HTTP handlers, request validation, response contracts

## Local Commands
- Contract tests: `pnpm test -- src/api`

## Local Boundaries
- Always: update request schema and response contract together
- Never: bypass the shared error formatter in `src/api/errors`
```

## Common Bloat Patterns

| Pattern | Why it is bad | Better move |
|--------|----------------|-------------|
| Full directory tree dump | The agent can inspect the tree | Keep only meaningful boundaries |
| README copy | Duplicates existing docs | Reference README instead |
| Generic best practices | Too vague to change behavior | Use specific local rules |
| Full dependency list | Package manifests already exist | Document only non-obvious choices |
| Repeated root commands in child files | Wastes context twice | Keep only local commands in child files |

## Discovery Handoff

Do not draft from templates before discovery is complete.

### Wave 1 must answer
- repo-wide command sources
- top-level architecture
- current instruction surfaces
- candidate local file boundaries

### Wave 2 must answer
- what a coder in this folder needs to know
- folder-local commands and workflows
- non-obvious patterns and WHY context
- which rules belong in the parent instead

### Writer prompts must include
- target file path
- folder ownership
- parent-child boundary
- verified commands and paths
- relevant Wave 1 and Wave 2 findings

## Companion File Rule

After an `AGENTS.md` file is finalized:

1. create sibling `CLAUDE.md -> AGENTS.md`
2. if symlinks are impossible, use the fallback wrapper:
   ```markdown
   @AGENTS.md
   ```
3. keep agent-native behavior outside the AGENTS file

See `agent-entrypoints.md` for the full policy and cross-agent behavior.

## Verification

```bash
find . -name AGENTS.md | sort
find . -name CLAUDE.md -maxdepth 6 -print
find . -type l -name CLAUDE.md ! -exec test -e {} \; -print
```

Then ask the target agents to summarize the instructions they see for a folder you touched.

## Derailments

| Pattern | Trigger | Correction |
|---------|---------|------------|
| AGENTS-second drafting | Editing native files first | Write AGENTS first |
| One-wave exploration | Writing after Wave 1 only | Complete Wave 2 first |
| Weak explorer prompts | Short vague dispatches | Use substantive prompts with scope and deliverables |
| Writers too early | Findings not merged | Synthesize before dispatch |
| Missing folder coverage | Root-only file plan | Add local AGENTS files |
| Root duplication | Child file repeats root | Keep child files local |
| Invented commands | Unsure command syntax | Verify or mark `[unverified]` |
| Missing WHY | Non-obvious choice documented | Pair WHAT with WHY |
| Generic best practices | Vague advice shows up | Replace with measurable rules |
| Unknowns in files | Caveats inside docs | Put caveats in the response |
| Over-nesting | Too many empty local files | Keep only meaningful local files |
