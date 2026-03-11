---
name: init-devin-review
description: Use skill if you are setting up Devin Bug Catcher review behavior with REVIEW.md, AGENTS.md, or repo-specific pull request review instructions.
---

# Init Devin Review

Generate optimal `REVIEW.md` and optionally `AGENTS.md` files by analyzing the actual repository — its structure, tech stack, patterns, documentation, and team conventions — then producing tailored review instruction files that make Devin's Bug Catcher catch real issues.

## Decision tree

```
What does the user need?
│
├── First-time setup
│   ├── Install GitHub App & enroll ──────────► references/setup/getting-started.md
│   ├── Understand REVIEW.md format ──────────► references/review-md/format-and-directives.md
│   └── Enable auto-review / auto-fix ────────► references/setup/getting-started.md
│
├── Write REVIEW.md
│   ├── Format spec & section order ──────────► references/review-md/format-and-directives.md
│   ├── Security scanning rules ──────────────► references/patterns/common-configurations.md
│   ├── Performance check patterns ───────────► references/patterns/common-configurations.md
│   ├── Framework-specific conventions ───────► references/patterns/common-configurations.md
│   ├── Monorepo scoping ─────────────────────► references/review-md/format-and-directives.md
│   └── Full stack-specific examples ─────────► references/scenarios.md
│
├── Write AGENTS.md
│   ├── Format & section reference ───────────► references/agents-md/configuration.md
│   ├── AGENTS.md vs REVIEW.md split ─────────► references/agents-md/configuration.md
│   └── Framework-specific examples ──────────► references/agents-md/configuration.md
│
├── Customize review behavior
│   ├── Severity tuning & phrasing ───────────► references/customization/rules-and-exclusions.md
│   ├── File exclusions & ignore patterns ────► references/customization/rules-and-exclusions.md
│   ├── Custom review rule file paths ────────► references/customization/rules-and-exclusions.md
│   ├── Auto-fix configuration ───────────────► references/customization/rules-and-exclusions.md
│   └── Reducing noise / improving accuracy ──► references/customization/rules-and-exclusions.md
│
├── Troubleshoot
│   ├── Reviews not triggering ───────────────► references/troubleshooting/common-issues.md
│   ├── Too many findings (noisy) ────────────► references/troubleshooting/common-issues.md
│   ├── Missing real bugs ────────────────────► references/troubleshooting/common-issues.md
│   ├── Auto-fix not working ─────────────────► references/troubleshooting/common-issues.md
│   ├── CLI issues ───────────────────────────► references/troubleshooting/common-issues.md
│   └── Monorepo scoping issues ──────────────► references/troubleshooting/common-issues.md
│
└── Understand the system
    ├── Bug Catcher classification ────────────► references/review-spec.md
    ├── All instruction files Devin reads ─────► references/review-spec.md
    ├── Auto-review triggers & events ─────────► references/review-spec.md
    └── Permissions & enrollment ──────────────► references/setup/getting-started.md
```

## What Devin Review is

Devin Review is an AI code review platform that hooks into GitHub PRs. It:

1. **Reads instruction files** in the repo (`REVIEW.md`, `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `.cursorrules`, `.windsurfrules`, `*.rules`, `*.mdc`)
2. **Analyzes diffs** with the Bug Catcher, classifying findings as **Bugs** (severe/non-severe) or **Flags** (investigate/informational)
3. **Posts reviews** with smart diff organization, copy/move detection, and inline comments synced to GitHub
4. **Supports auto-review** on PR open, push, and ready-for-review events
5. **Offers auto-fix** that proposes code changes alongside bug findings (requires human approval)

The critical insight: `REVIEW.md` is the primary mechanism for customizing what Devin's Bug Catcher looks for. Well-written review guidelines make the difference between noise and catching real bugs. Devin reads `REVIEW.md` at any directory level (`**/REVIEW.md`), so you can scope guidelines to subdirectories in monorepos.

## Quick start

Minimal `REVIEW.md` for a TypeScript project — create this at repo root:

```markdown
# Review Guidelines

## Critical Areas
- All changes to `src/auth/` must be reviewed for security implications.
- Database migration files should be checked for backward compatibility.

## Security
- Never interpolate user input into SQL queries. Use parameterized queries.
- API keys and secrets must never appear in source code.
- All API routes must verify authentication via middleware.

## Conventions
- API endpoints must validate request bodies using Zod schemas.
- All public functions require explicit TypeScript return types.
- Use the structured logger — never `console.log` in production.

## Ignore
- Auto-generated files in `src/generated/` do not need review.
- Lock files can be skipped unless dependencies changed.
- Build output in `dist/` should never be committed.
```

Three ways to verify it works:

1. **Dashboard**: Open `https://app.devin.ai/review` and check your PR
2. **URL swap**: Replace `github.com` with `devinreview.com` in any PR URL
3. **CLI**: `npx devin-review https://github.com/owner/repo/pull/123`

## Workflow

Follow these four phases in order.

### Phase 1: Explore the repository

Before writing anything, map the territory. Use tools to answer:

1. **Structure** — Monorepo or single-service? What are the top-level directories?
   ```
   Run: ls -la at root, look for packages/, apps/, services/, src/
   ```
2. **Tech stack** — Languages, frameworks, ORMs, testing tools?
   ```
   Check: package.json, requirements.txt, go.mod, Cargo.toml, pyproject.toml
   Look at: tsconfig.json, .eslintrc, prettier config, Dockerfile
   ```
3. **Existing instruction files** — Does the repo already have REVIEW.md, AGENTS.md, CLAUDE.md, CONTRIBUTING.md, .cursorrules?
   ```
   Search for: REVIEW.md, AGENTS.md, CLAUDE.md, CONTRIBUTING.md, .cursorrules, .windsurfrules
   If they exist, read them — you'll extend rather than replace
   ```
4. **Documentation** — What context files exist?
   ```
   Search for: docs/, architecture.md, ADRs, openapi/, swagger/, prisma/schema.prisma
   ```
5. **Existing linting & CI** — What does the toolchain already catch?
   ```
   Check: .eslintrc, .prettierrc, CI configs, pre-commit hooks
   Don't duplicate what linters already enforce
   ```
6. **Pain points** — Look at recent PRs, issues, and git history for patterns
   ```
   Check: common bug patterns, frequently reverted commits, security incidents
   ```

### Phase 2: Decide file strategy

**Which files to generate:**

| Situation | Files |
|---|---|
| Single-service repo | Root `REVIEW.md` |
| Monorepo with different review needs per package | Root `REVIEW.md` + scoped `REVIEW.md` in subdirectories |
| Team using Devin for task execution too | Root `REVIEW.md` + `AGENTS.md` |
| Repo already has CLAUDE.md or .cursorrules | Root `REVIEW.md` (complement, don't duplicate existing files) |

**REVIEW.md vs AGENTS.md:**

- `REVIEW.md` — Review-specific guidelines: what to check, what to flag, what to ignore. Read by Bug Catcher during PR analysis.
- `AGENTS.md` — Agent behavior instructions: coding style, architecture decisions, workflow patterns. Read by Devin during task execution (not just reviews).

If the user only mentions review/PR setup, generate `REVIEW.md` only. If they mention Devin task execution or agent behavior, also generate `AGENTS.md`.

### Phase 3: Write the files

Structure `REVIEW.md` using this section order (Bug Catcher weights top content higher):

1. **Critical Areas** — path-specific areas needing extra scrutiny with reasoning
2. **Security** — rules flagged as severe bugs; use absolute language ("must never", "always required")
3. **Conventions** — specific, measurable coding standards; reference actual paths/libraries
4. **Performance** — anti-patterns to flag; describe the problem and the correct alternative
5. **Patterns** — Good/Bad code examples in fenced blocks for pattern matching
6. **Ignore** — files to skip (generated code, lock files, build output)
7. **Testing** — test requirements and conventions

For detailed format specification, see `references/review-md/format-and-directives.md`. For stack-specific examples, see `references/scenarios.md`. For AGENTS.md format, see `references/agents-md/configuration.md`.

### Phase 4: Validate and output

**Before outputting, verify:**

- [ ] `REVIEW.md` is under 500 lines (ideally 100-300)
- [ ] No duplicate rules that existing linters already catch
- [ ] Rules are specific and measurable, not vague platitudes
- [ ] Critical/security sections are near the top
- [ ] Code examples use the repo's actual language and framework patterns
- [ ] Ignore patterns match the repo's actual generated/build directories
- [ ] If CLAUDE.md or .cursorrules exist, REVIEW.md doesn't repeat their content
- [ ] Monorepo subdirectory REVIEW.md files don't repeat root-level rules

**Output format:**

For every configuration you produce, include:

1. **File tree** showing exactly which files go where and what each is for
2. **Each file** as a complete markdown code block
3. **Reasoning annotations** after each file explaining WHY each major section was included, referencing specific repo context
4. **Verification step** — how to test the config works (open a test PR, use the URL swap `devinreview.com`, or run `npx devin-review`)

## Common pitfalls

| Pitfall | Fix |
|---------|-----|
| REVIEW.md over 500 lines | Keep under 300 lines; split into scoped files for monorepos |
| Duplicating linter rules | Check `.eslintrc`, CI configs first; only add rules linters can't catch |
| Vague rules ("write clean code") | Every rule must be specific enough to test against a diff |
| All rules at same severity | Vary phrasing: "must never" (severe) vs "consider" (investigate) |
| Missing Ignore section | Always add one — generated files, lock files, build output create noise |
| Copying scenario examples verbatim | Adapt every rule to reference real repo paths and libraries |
| Deep header nesting (H4+) | Stick to H2/H3 with flat bullet lists — deep nesting reduces parsing accuracy |
| Repeating root rules in subdirectory REVIEW.md | Subdirectory files complement root — don't duplicate |
| Generic security rules | Reference specific attack vectors: "to prevent XSS", "to avoid SQL injection" |
| REVIEW.md and AGENTS.md overlap | Review criteria → REVIEW.md; coding behavior → AGENTS.md |
| No code examples for anti-patterns | Add Good/Bad pattern blocks — the Bug Catcher uses them for matching |
| Ignoring existing instruction files | Check for CLAUDE.md, .cursorrules, CONTRIBUTING.md first — complement them |

## Minimal reading sets

### "I need to set up Devin Review from scratch"

- `references/setup/getting-started.md`
- `references/review-md/format-and-directives.md`
- `references/scenarios.md`

### "I need to write a REVIEW.md for my stack"

- `references/review-md/format-and-directives.md`
- `references/patterns/common-configurations.md`
- `references/scenarios.md`

### "I need both REVIEW.md and AGENTS.md"

- `references/review-md/format-and-directives.md`
- `references/agents-md/configuration.md`
- `references/patterns/common-configurations.md`

### "I need to reduce noisy reviews"

- `references/customization/rules-and-exclusions.md`
- `references/troubleshooting/common-issues.md`

### "I need to configure a monorepo"

- `references/review-md/format-and-directives.md`
- `references/patterns/common-configurations.md`
- `references/troubleshooting/common-issues.md`

### "I need to understand how Devin Review works"

- `references/review-spec.md`
- `references/setup/getting-started.md`

### "I need to troubleshoot review issues"

- `references/troubleshooting/common-issues.md`
- `references/customization/rules-and-exclusions.md`
- `references/setup/getting-started.md`

## What makes a good REVIEW.md

Six principles that determine whether the Bug Catcher catches real bugs or generates noise:

1. **Specific over vague** — "All API endpoints must validate request body with Zod" beats "validate inputs"
2. **Actionable** — The developer reading a flag should know exactly what to fix
3. **Prioritized** — Lead with critical areas (security, auth, data integrity) so the Bug Catcher weighs them higher
4. **Code examples help** — Good/bad patterns in fenced code blocks let the Bug Catcher match against actual anti-patterns
5. **Keep it under 300 lines** — Overly verbose files dilute signal and slow AI parsing; use monorepo scoping for large repos
6. **Flat structure** — Use H2/H3 headers and bullet lists; deep nesting reduces parsing accuracy

## Reference files

Read these when you need detailed specifications or examples:

| Reference | What it covers | When to read |
|-----------|---------------|--------------|
| `references/setup/getting-started.md` | GitHub App install, enrollment, auto-review/fix config, CLI, permissions | First-time setup |
| `references/review-md/format-and-directives.md` | REVIEW.md format spec, sections, weighting, monorepo scoping, phrasing guide | Writing any REVIEW.md |
| `references/agents-md/configuration.md` | AGENTS.md format, sections, REVIEW.md vs AGENTS.md split, framework examples | Writing AGENTS.md |
| `references/patterns/common-configurations.md` | Security, performance, framework-specific patterns (Next.js, React, Django, Go, Rust) | Building rule sets |
| `references/customization/rules-and-exclusions.md` | Severity tuning, file exclusions, auto-fix config, noise reduction, accuracy improvement | Tuning review quality |
| `references/troubleshooting/common-issues.md` | Reviews not triggering, noisy reviews, missing bugs, CLI issues, monorepo problems | Debugging issues |
| `references/review-spec.md` | Bug Catcher classification, instruction files list, auto-review triggers, permissions | Understanding the system |
| `references/scenarios.md` | Complete REVIEW.md examples for TypeScript, Next.js, Django, Tauri, MCP, monorepo | Stack-specific inspiration |

## Key gotchas

- `REVIEW.md` is read from **any directory level** (`**/REVIEW.md`) — use this for monorepo scoping
- Devin also reads `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `.cursorrules`, `.windsurfrules`, `*.rules`, `*.mdc` — check for conflicts
- Auto-review triggers on PR open, push to PR, and when a draft is marked ready
- The Bug Catcher classifies findings as: **Bugs** (severe, non-severe) and **Flags** (investigate, informational)
- Keep REVIEW.md focused on review concerns — put coding/architecture standards in AGENTS.md or CLAUDE.md instead
- Custom review rule file paths can be configured in Settings > Review, but `**/REVIEW.md` is always read by default
- Auto-Fix requires human approval — Devin never merges fixes automatically
- Content near the top of REVIEW.md gets higher weighting — put critical/security rules first
- Phrasing matters: "must never" → severe bug; "consider" → investigate flag
- Draft PRs are skipped — auto-review only triggers when marked ready

## Final reminder

This skill is split into focused reference files organized by domain. Do not load everything at once. Start with the smallest relevant reading set above, then expand into neighboring references only when the task actually requires them. Every reference file in `references/` is explicitly routed from the decision tree above.
