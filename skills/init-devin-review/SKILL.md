---
name: init-devin-review
description: Use skill if you are creating or refining REVIEW.md, AGENTS.md, or repo-scoped Devin Bug Catcher review instructions.
---

# Init Devin Review

Generate Devin review configuration from repository evidence. `REVIEW.md` controls what Bug Catcher flags in diffs. `AGENTS.md` controls how Devin should behave while working in the repo. Default to the smallest configuration that meaningfully improves review quality.

## Use this skill when

- setting up Devin Bug Catcher for a repository
- fixing noisy or weak `REVIEW.md` guidance
- deciding whether the repo needs only `REVIEW.md` or both `REVIEW.md` and `AGENTS.md`
- scoping review rules across packages or services in a monorepo

## Core working rules

- Start with the repository, not the scenario library.
- Inspect existing instruction files before writing anything: `REVIEW.md`, `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `.cursorrules`, `.windsurfrules`, `*.rules`, `*.mdc`.
- Reuse the repo's real paths, libraries, commands, docs, and pain points. Never copy reference text verbatim.
- `REVIEW.md` can live at the root or in scoped subdirectories. `AGENTS.md` should stay root-only.
- Keep `REVIEW.md` focused on reviewable diff issues. Put coding workflow, architecture, and task-execution behavior in `AGENTS.md` only when needed.
- Prefer one strong root `REVIEW.md` over many weak files. Add scoped `REVIEW.md` files only where review concerns truly diverge.
- Do not encode formatter, linter, or CI rules unless Devin adds value beyond existing automation.

## Required workflow

### 1. Scan the repo

Collect only the evidence needed to write grounded rules:

- structure: single-service repo or monorepo; top-level apps, packages, or services
- stack: languages, frameworks, ORM or database layer, transport/runtime, test tooling
- existing instructions: Devin, Claude, editor, and project guidance files
- contracts and docs: OpenAPI, Prisma schema, ADRs, architecture docs, security docs
- enforcement already present: ESLint, Prettier, CI, pre-commit, clippy, mypy, etc.
- recurring risk areas: auth, billing, IPC, migrations, permissions, secrets, data integrity, generated code

### 2. Choose the file plan

| Situation | Output |
| --- | --- |
| Single service or one shared review model | Root `REVIEW.md` |
| Monorepo with cross-cutting rules plus package-specific risks | Root `REVIEW.md` + scoped `REVIEW.md` only in divergent directories |
| User asks for Devin coding or task behavior too | Root `REVIEW.md` + root `AGENTS.md` |
| Existing `AGENTS.md` or `CLAUDE.md` already covers coding behavior | Usually `REVIEW.md` only; extend or align instead of duplicating |

Default to `REVIEW.md` only unless the request or repo evidence clearly calls for `AGENTS.md`.

### 3. Split concerns correctly

| Concern | `REVIEW.md` | `AGENTS.md` |
| --- | --- | --- |
| What Bug Catcher should flag in diffs | ✅ | ❌ |
| What files or changes to ignore | ✅ | ❌ |
| Coding standards, architecture, workflow, dependency choices | ❌ | ✅ |
| Test, run, or commit expectations for Devin | ❌ | ✅ |

Rule of thumb: if the statement is about **reviewing a diff**, it belongs in `REVIEW.md`. If it is about **how Devin or contributors should work**, it belongs in `AGENTS.md`.

### 4. Draft from evidence

When writing `REVIEW.md`:

1. Put high-signal sections near the top. Preferred order: `Critical Areas` → `Security` → `Conventions` → `Performance` → `Patterns` → `Ignore` → `Testing`.
2. Reference real repo details in every important section: paths, middleware, libraries, commands, docs, or contracts.
3. Use severity intentionally:
   - severe bug language: `must never`, `always required`, `prohibited`
   - important but not always severe: `use X instead of Y`, `do not`
   - lower-priority guidance: `prefer`, `consider`, `watch for`
4. Include Good/Bad examples only for patterns the repo actually uses.
5. Add an `Ignore` section so generated files, lockfiles, build output, snapshots, and similar noise do not consume review bandwidth.

When writing `AGENTS.md`:

- keep it root-scoped
- focus on architecture, workflow, dependencies, file organization, testing, and communication expectations
- do not restate bug-finding rules that already belong in `REVIEW.md`

## Do this, not that

| Do | Don't |
| --- | --- |
| Extend or align with existing instruction files | Overwrite or contradict them blindly |
| Reference actual paths and libraries like `src/auth/`, `openapi.yaml`, `portable-pty`, `rusqlite`, `NextAuth`, or `select_related()` | Write generic advice like "validate inputs" or "be secure" |
| Use scoped `REVIEW.md` only for real package or service differences | Copy the same root rules into every subdirectory |
| Remove rules already enforced by linters, formatters, or CI | Turn `REVIEW.md` into a duplicate style guide |
| Keep `REVIEW.md` compact, usually 100-300 lines and under 500 max | Cram every possible rule into one file |
| Use scenario and pattern references as raw material | Paste scenario text verbatim |

## Validation checklist

Before returning any configuration, verify:

- the front-loaded sections match the repo's highest-risk areas
- rules are specific enough to test against a diff
- no obvious overlap with ESLint, Prettier, CI, clippy, mypy, or similar tooling
- ignore patterns match actual generated and build files in the repo
- monorepo scoped files add new package-specific guidance instead of duplicating root rules
- `AGENTS.md` is only included when agent-behavior guidance is truly needed
- no contradictions with `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, or editor rule files
- `REVIEW.md` stays lean enough for Bug Catcher to focus

## Output requirements

When asked to generate files, return:

1. a short file plan or tree
2. each file as a complete markdown block
3. brief notes tying major sections to repository evidence
4. a simple verification path, such as a test PR, `devinreview.com` URL swap, or `npx devin-review`

## Recovery loops

- **Too much noise:** shorten the file, add or expand `Ignore`, delete vague rules, and remove rules already enforced elsewhere. See `references/customization/rules-and-exclusions.md` and `references/troubleshooting/common-issues.md`.
- **Missing real bugs:** move critical rules higher, add path-specific critical areas, tighten phrasing, and add repo-accurate examples. See `references/review-md/format-and-directives.md` and `references/troubleshooting/common-issues.md`.
- **Monorepo confusion:** keep root rules cross-cutting; put only package-specific risks in scoped files. See `references/patterns/common-configurations.md`.
- **`REVIEW.md` vs `AGENTS.md` overlap:** move diff-catching rules back to `REVIEW.md`; keep coding workflow in `AGENTS.md`. See `references/agents-md/configuration.md`.
- **Need a starting pattern for a known stack:** use the closest scenario as inspiration, then rewrite it against the repo. `references/scenarios.md` covers TypeScript backends, Next.js sites and dashboards, Django APIs, Tauri apps, MCP servers, Python `mcp-use`, and monorepos.

## Reference routing

| Need | Read |
| --- | --- |
| section order, phrasing, weighting, monorepo `REVIEW.md` behavior | `references/review-md/format-and-directives.md` |
| `AGENTS.md` structure and file-split decisions | `references/agents-md/configuration.md` |
| noise reduction, exclusions, severity tuning | `references/customization/rules-and-exclusions.md` |
| reusable security, performance, framework, and monorepo patterns | `references/patterns/common-configurations.md` |
| full stack examples to adapt, not copy | `references/scenarios.md` |
| noisy reviews, missed bugs, and triggering/debug issues | `references/troubleshooting/common-issues.md` |
| install, enrollment, and system behavior | `references/setup/getting-started.md`, `references/review-spec.md` |

## Final reminder

The best Devin review config is not the longest one. It is the smallest repo-grounded set of instructions that makes Bug Catcher focus on the bugs your team actually cares about.
