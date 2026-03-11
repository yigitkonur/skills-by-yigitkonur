# Derailment Test: init-copilot-review on "dubinc/dub Next.js monorepo"

Date: 2025-07-18
Skill under test: init-copilot-review
Test task: Create Copilot review instruction files for dubinc/dub (Turborepo monorepo with Next.js App Router, TypeScript, Prisma, Stripe, Zod v4, Vitest)
Method: Follow SKILL.md steps 1-6 exactly as written

---

## Target repository profile

- **Repo**: dubinc/dub -- open-source link management platform
- **Architecture**: Turborepo monorepo with 11+ packages
- **Stack**: Next.js 15 App Router, TypeScript, Prisma ORM, Stripe billing, Zod v4 validation, Vitest testing, Tailwind CSS
- **Key paths**: `apps/web/` (main app), `packages/` (shared libs), `apps/web/app/api/` (API routes)
- **Existing config**: ESLint, Prettier, Turbo, no prior Copilot instructions

---

## Friction points

### Step 1 -- Ground on the repository

**F-01 -- No inspection commands provided** (P2)
Step 1 says "Inspect the actual repository first" but provides no shell commands or tooling suggestions. I had to invent my own `find`, `ls`, `cat` workflow to survey the repo structure, linter configs, and test conventions.
Root cause: M4 (Missing execution method)
Fix: Add a "Quick repo scan recipe" code block with 4 shell one-liners.

**F-02 -- "Representative files" is undefined** (P1)
Step 1 says to inspect "Representative files in each scope you may target" but does not define how many files, what makes a file representative, or when to stop.
Root cause: M1 (Ambiguous threshold)
Fix: Change to "examine 2-3 files per scope: one typical, one complex, one boundary-case."

**F-03 -- No stopping criterion for exploration** (P1)
Step 1 lists 6 things to gather but provides no signal for when exploration is complete. In a 500+ file monorepo, I could have spent unlimited time inspecting.
Root cause: M1 (Ambiguous threshold)
Fix: Add a 3-question stopping test.

**F-04 -- "Recurring review themes" has no method** (P1)
Step 1 says to find "Recurring review themes from existing conventions, risk areas, or repeated code patterns" but doesn't say where to look for them.
Root cause: M4 (Missing execution method)
Fix: Add "look for repeated patterns in recent PRs, open issues, code comments, and CONTRIBUTING.md."

### Step 2 -- Choose instruction architecture

**F-05 -- "High-signal" is undefined** (P2)
Step 2 says create a file "only if you have 2-3 high-signal rules unique to that scope" but doesn't define what makes a rule high-signal vs low-signal.
Root cause: M1 (Ambiguous threshold)
Fix: Parenthetical definition of high-signal.

**F-06 -- Monorepo utility package threshold unclear** (P1)
For packages like `packages/utils/` or `packages/ui/`, the placement logic table says "A monorepo package or service has unique review needs" but doesn't quantify "unique review needs."
Root cause: M1 (Ambiguous threshold)
Fix: Add "A package qualifies for its own file only when it has 2+ rules that do not apply to any other package."

**F-07 -- No Next.js route group guidance** (P2)
The dub repo uses Next.js route groups like `app/(dashboard)/`, `app/(auth)/`. The skill has no guidance for framework-specific directory conventions like route groups.
Root cause: O3 (Edge case unhandled)
Fix: Add note about route groups.

### Step 3 -- Select rules

**F-08 -- SMSA acronym not defined inline** (P2)
Step 3 says "Every rule should be Specific, Measurable, Actionable, and Semantic" but the reference routing table says "SMSA rule quality" -- using an acronym never formally introduced.
Root cause: M5 (Assumed knowledge)
Fix: Add "(SMSA)" after the expanded form in Step 3.

**F-09 -- Reference triggers for scenarios.md and micro-library.md unclear** (P2)
The instruction "If you use references/scenarios.md or references/micro-library.md, treat them as pattern libraries" doesn't say WHEN to consult them.
Root cause: M6 (Vague verb)
Fix: Add inline trigger descriptions.

### Step 4 -- Draft files

**F-10 -- No frontmatter example in SKILL.md** (P1)
Step 4 says "Every scoped file starts at line 1 with YAML frontmatter" but provides no inline example.
Root cause: M5 (Assumed knowledge) + M2 (Unstated location)
Fix: Add an inline YAML frontmatter example block.

**F-11 -- Glob brace expansion not mentioned** (P1)
The skill mentions `applyTo` is a "glob string" but never shows brace expansion syntax like `{ts,tsx}`.
Root cause: M5 (Assumed knowledge)
Fix: Add glob syntax summary.

**F-12 -- Split directories for one logical domain** (P1)
In dub, API routes are under `apps/web/app/api/` but API-related utilities are in `packages/utils/functions/`. The skill doesn't address how to scope when a logical domain spans multiple directories.
Root cause: O3 (Edge case unhandled)
Fix: Add broader wildcard guidance.

### Step 5 -- Validate

**F-13 -- No linter cross-reference method** (P2)
Step 5 says "No rules duplicated from linter or formatter config" but provides no method to cross-reference.
Root cause: M4 (Missing execution method)
Fix: Add grep suggestion.

**F-14 -- No method for glob pattern verification** (P1)
Step 5 says "verify that representative files actually match each applyTo pattern" but doesn't say how.
Root cause: M4 (Missing execution method)
Fix: Add `find` command recipe.

**F-15 -- `wc -c` bytes vs characters** (P2)
Step 5 says "Use `wc -c` for character counts" but `wc -c` counts bytes, not characters.
Root cause: M3 (Format inconsistency)
Fix: Add `wc -m` alternative.

### Step 6 -- Present result

**F-16 -- "Brief" is subjective** (P2)
Step 6 says "A brief per-file explanation" but doesn't quantify what brief means.
Root cause: M1 (Ambiguous threshold)
Fix: Change to "A 1-3 sentence per-file explanation."

---

## What worked well

1. **Reference routing table** -- during execution I only needed 2 of 6 references. The table prevented unnecessary reading.
2. **Placement logic table** (Step 2) -- clear and immediately actionable for mapping rules to files.
3. **Keep/Drop filter** (Step 3) -- immediately eliminated generic and linter-territory rules.
4. **"Do this, not that" table** -- caught two mistakes I was about to make.
5. **Recovery paths** -- saved time when I initially created too many scoped files.
6. **Character budget guidance** (2,500-3,500 target, 4,000 hard limit) -- prevented scope bleed.
7. **"Do not read every reference by default"** -- saved ~30 minutes of reference reading.

---

## Priority summary

| Priority | Count | Friction points |
|---|---|---|
| P0 | 0 | -- |
| P1 | 8 | F-02, F-03, F-04, F-06, F-10, F-11, F-12, F-14 |
| P2 | 8 | F-01, F-05, F-07, F-08, F-09, F-13, F-15, F-16 |

## Metrics

| Metric | Value |
|---|---|
| Total steps attempted | 6 |
| Clean passes | 0 |
| P0 | 0 |
| P1 | 8 |
| P2 | 8 |
| Total friction points | 16 |
| Friction density | 2.67 per step |

## Derailment density map

| Step | Phase | P0 | P1 | P2 | Total |
|---|---|---|---|---|---|
| 1 | Ground on repository | 0 | 3 | 1 | 4 |
| 2 | Choose architecture | 0 | 1 | 2 | 3 |
| 3 | Select rules | 0 | 0 | 2 | 2 |
| 4 | Draft files | 0 | 3 | 0 | 3 |
| 5 | Validate | 0 | 1 | 2 | 3 |
| 6 | Present result | 0 | 0 | 1 | 1 |

## Root cause distribution

| Root cause | Count | IDs |
|---|---|---|
| M1 (Ambiguous threshold) | 5 | F-02, F-03, F-05, F-06, F-16 |
| M4 (Missing execution method) | 4 | F-01, F-04, F-13, F-14 |
| M5 (Assumed knowledge) | 3 | F-08, F-10, F-11 |
| O3 (Edge case unhandled) | 2 | F-07, F-12 |
| M6 (Vague verb) | 1 | F-09 |
| M3 (Format inconsistency) | 1 | F-15 |
| M2 (Unstated location) | 1 | F-10 (compound) |
