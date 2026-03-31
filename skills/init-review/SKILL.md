---
name: init-review
description: "Use skill if you are creating or refining AI code review config for GitHub Copilot, Devin Bug Catcher, Greptile, or any combination for a repository."
---

# Init Review

Generate repo-grounded AI code review configuration for one or more platforms: **GitHub Copilot**, **Devin Bug Catcher**, and/or **Greptile**. Shared repo scan, platform-specific output.

## Trigger boundaries

Use this skill when you need to:
- Create or revise AI review config for Copilot, Devin, Greptile, or any combination
- Decide which platform(s) to configure
- Debug why an AI reviewer ignores rules, flags noise, or misses real bugs
- Scope review rules across a monorepo for any platform

Do not use when:
- Reviewing a PR directly
- Creating non-review agent files (generic `CLAUDE.md`, `AGENTS.md` without Devin context)
- Writing linter/formatter config

## Platform quick reference

| Platform | Config files | Format | Key constraint | Branch reads from |
|---|---|---|---|---|
| **Copilot** | `.github/copilot-instructions.md` + `.github/instructions/*.instructions.md` | Markdown + YAML frontmatter | 4,000 char hard limit per file | **Base branch** (main) |
| **Devin** | `REVIEW.md` + optional `AGENTS.md` (root or scoped) | Pure Markdown | ~300 lines soft limit, ~500 max | Current repo state |
| **Greptile** | `.greptile/config.json` + optional `rules.md` + `files.json` | JSON + Markdown | `scope`=array, `ignorePatterns`=newline string | **Source branch** (feature) |

## Phase 0: Determine target platforms

Before scanning, determine which platforms to generate for:

1. **User explicitly asked** — generate only what was requested
2. **Auto-detect from repo** — check for existing config:
   ```bash
   ls .github/copilot-instructions.md .github/instructions/ 2>/dev/null
   find . -maxdepth 3 -name "REVIEW.md" -o -name ".devin" 2>/dev/null | head -5
   find . -type d -name '.greptile' -o -name 'greptile.json' 2>/dev/null | head -5
   ```
3. **User said "all" or "set up AI review"** — generate for all three platforms

If existing config is found for a platform, default to **refine in place** rather than recreate.

## Phase 1: Scan the repository (shared across all platforms)

Change into the target repo root. If working from a shared fixture, copy to a scratch worktree first.

```bash
# Structure and docs
find . -maxdepth 3 -type f -name "*.md" | head -30
ls -la .github/ .cursor/ .windsurf/ .agents/ .devin/ 2>/dev/null

# Stack detection
ls package.json go.mod requirements.txt pyproject.toml Cargo.toml pom.xml build.gradle 2>/dev/null
[ -f package.json ] && head -40 package.json
[ -f README.md ] && head -30 README.md

# Existing linters/formatters
find . -maxdepth 2 -type f \( -name '.eslintrc*' -o -name 'eslint.config.*' -o -name '.prettierrc*' -o -name 'prettier.config.*' -o -name 'biome.json' -o -name 'biome.jsonc' -o -name '.golangci.yml' -o -name '.rubocop.yml' -o -name 'pyproject.toml' -o -name '.flake8' \) 2>/dev/null

# Existing review/agent config
find . -maxdepth 3 \( -name "REVIEW.md" -o -name "AGENTS.md" -o -name "CLAUDE.md" -o -name "CONTRIBUTING.md" -o -name ".cursorrules" -o -name ".windsurfrules" -o -name ".coderabbit.yaml" -o -name "greptile.json" \) | sort

# Test conventions
find . \( -name "*.test.*" -o -name "*.spec.*" -o -name "*_test.go" \) | head -10

# CI
ls .github/workflows/ .gitlab-ci.yml Jenkinsfile Makefile 2>/dev/null
```

**Collect:**
- **Structure**: single-service, multi-service, or monorepo; top-level directories
- **Stack**: languages, frameworks, ORM, transport, test tooling
- **Existing configs**: all review/agent instruction files from any platform
- **Enforcement**: linters, formatters, CI, SAST tools — rules these handle are OFF LIMITS
- **Risk zones**: auth, payments, PII, file system, shell, IPC, migrations, secrets
- **Docs/specs**: OpenAPI, Prisma schemas, ADRs, architecture docs (for Greptile `files.json`)

**Stopping test — move on when you can answer:**
1. What are the 2-4 highest-risk areas where review catches real bugs?
2. Which linter/formatter rules already enforce style?
3. What is the narrowest directory structure that separates review scopes?

## Phase 2: Generate platform-specific config

For each target platform, follow its platform section below. If generating for multiple platforms, reuse the repo scan from Phase 1 — do not re-scan.

---

### Copilot generation

> **References:** Read `references/copilot/setup-and-format.md` for file format, `references/copilot/writing-instructions.md` for SMSA quality, `references/copilot/scoping-and-targeting.md` for globs. Only expand to `references/copilot/scenarios.md` or `references/copilot/micro-library.md` when you need full examples or starter patterns.

**Step 1: Choose file architecture**

Default shape:
```
.github/
├── copilot-instructions.md          # universal rules only
└── instructions/
    ├── <language>.instructions.md
    └── <domain>.instructions.md
```

Placement logic:
- **Root file**: truly universal (security, error philosophy, performance red flags)
- **Language file**: applies to one language/ecosystem, not just linter stuff
- **Domain file**: framework, directory, or critical path (api, auth, migrations)
- Start with **1 root + 2-4 scoped files**, grow only when justified

> If existing files exist: evaluate against SMSA, note gaps, refine in place.

**Step 2: Write rules using SMSA**

Every rule must be **Specific, Measurable, Actionable, Semantic**:
- Specific: "Flag `useEffect` calling fetch without AbortController cleanup"
- Measurable: Copilot can decide yes/no per diff hunk
- Actionable: tells reviewer what to flag and why
- Semantic: beyond what ESLint/Prettier/linter catches

Drop: formatting rules, generic advice, rules without repo evidence.

**Step 3: Draft files**

- Root: plain Markdown, no frontmatter
- Scoped: YAML frontmatter at line 1 with `applyTo` glob
- `applyTo` is a single glob string, not an array
- Keep each file under **3,500 characters** (4,000 hard limit)
- Highest-priority rules first
- Optional `excludeAgent`: `"code-review"` or `"coding-agent"`

**Step 4: Validate**

- `wc -m` each file (must be < 4,000)
- Verify globs with Python `glob.glob()` (brace-aware)
- No external links, no linter-duplicate rules, no conflicting overlapping scopes
- Plan for **base-branch** deployment (feature branch changes don't affect same PR's review)

---

### Devin generation

> **References:** Read `references/devin/review-spec.md` for format, `references/devin/review-md/format-and-directives.md` for section order and severity. Only expand to `references/devin/scenarios.md` for full examples or `references/devin/patterns/common-configurations.md` for starter patterns.

**Step 1: Choose file plan**

| Situation | Output |
|---|---|
| Single service or shared review model | Root `REVIEW.md` only |
| Monorepo with divergent package risks | Root + scoped `REVIEW.md` |
| Also need coding/task behavior guidance | Add `AGENTS.md` |
| Existing `AGENTS.md`/`CLAUDE.md` covers coding behavior | `REVIEW.md` only; align, don't duplicate |

Default to `REVIEW.md` only. Add `AGENTS.md` only when evidence justifies it.

**Step 2: Split concerns**

- `REVIEW.md`: what Bug Catcher flags in diffs, what to ignore
- `AGENTS.md`: coding standards, architecture, workflow, dependencies, testing

Rule of thumb: about **reviewing a diff** → `REVIEW.md`. About **how to work** → `AGENTS.md`.

**Step 3: Draft from evidence**

Section order: `Critical Areas` → `Security` → `Conventions` → `Performance` → `Patterns` → `Ignore` → `Testing`

Severity via phrasing:
- Severe: `must never`, `always required`, `prohibited`
- Important: `use X instead of Y`, `do not`
- Advisory: `prefer`, `consider`, `watch for`

Add `Ignore` section with globs for generated/build/lock files. Keep 100-300 lines, max 500.

**Step 4: Validate**

- Front-loaded sections match repo's highest-risk areas
- Rules testable against a diff
- No linter/formatter overlap
- Ignore patterns match real files
- No contradictions across overlapping files

---

### Greptile generation

> **References:** Read `references/greptile/config-spec.md` for JSON schema, `references/greptile/rules-engineering.md` for rule quality. Only expand to `references/greptile/patterns.md` for stack patterns or `references/greptile/scenarios.md` for full examples.

**Step 1: Choose file topology**

Always generate: `.greptile/config.json`

Generate only when needed:
- `rules.md` — rule needs >200 chars or good/bad code examples
- `files.json` — context files the reviewer needs to validate correctness (schemas, API specs)
- Child `config.json` — subtree needs different strictness/rules

**Step 2: Set strictness and comment types**

- `2` for most production code
- `1` for payments, auth, security-critical paths
- `3` for internal tools, prototypes, low-risk
- Default `commentTypes`: `["logic", "syntax"]`. Add `"style"` only when repo lacks linting.

**Step 3: Engineer rules (5-10 max)**

Every rule must be repo-specific, scoped, semantic, and identifiable:
- Tie each to actual repo paths, libraries, contracts, or failure modes
- `scope` is an **array** of globs: `["src/api/**/*.ts"]`
- Give parent-level rules an `id` for child `disabledRules`
- Litmus test: if ESLint/Pylint/grep could catch it, delete it

**Step 4: Configure targeting**

- `ignorePatterns` is a **newline-separated string**: `"dist/**\nnode_modules/**\n*.lock"`
- `patternRepositories` uses `"org/repo"` format, never URLs
- `files.json` scopes context files to the code they inform

**Step 5: Validate**

- `python3 -m json.tool .greptile/config.json` passes
- `scope` values are arrays, `ignorePatterns` is a string
- `strictness` is 1, 2, or 3
- `commentTypes` only uses `"logic"`, `"syntax"`, `"style"`, `"info"`
- No `.greptile/` + `greptile.json` coexistence
- Include a **canary rule** for verification

---

## Phase 3: Output

For each platform, return:

1. **File tree** showing all generated files
2. **Write files** to the repo (unless user asked for draft-only)
3. **Complete file contents** in markdown blocks
4. **Per-file justification** tying rules to repo evidence

Platform-specific additions:
- **Copilot**: note that changes must reach the base branch to take effect
- **Devin**: include verification path (test PR or `npx devin-review`)
- **Greptile**: include reasoning annotations (`rule-id: evidence`) and canary test rule

## Shared principles

These apply to ALL platforms:

| Do | Don't |
|---|---|
| Ground every rule in repo evidence (files, configs, patterns) | Write generic "follow best practices" |
| Start minimal, iterate after real PRs | Dump 20+ rules hoping for coverage |
| Skip rules already enforced by linters/formatters | Duplicate ESLint, Prettier, Ruff, golangci-lint |
| Use short imperative bullets | Write prose paragraphs or vague slogans |
| Adapt scenario references to the repo | Copy templates verbatim |
| Evaluate existing config before overwriting | Start from scratch when files exist |
| Put highest-risk rules first | Bury security rules below style guidance |

## Recovery paths

| Symptom | Fix |
|---|---|
| Too many files / too broad | Collapse to root + highest-signal scoped files |
| Rules ignored | Check: branch (base vs source), file location, character limit, JSON validity |
| Too noisy | Remove linter-duplicate rules, expand ignore patterns, tighten phrasing |
| Missing real bugs | Move critical rules higher, add path-specific rules, add code examples |
| Conflicting rules across scopes | Narrow scopes until no overlap, or rewrite as additive |
| Multi-stack confusion | Treat each stack as independent scope from the start |

## Platform-specific reference routing

### Copilot references

| Need | Read |
|---|---|
| File locations, format, character limits, base-branch behavior | `references/copilot/setup-and-format.md` |
| SMSA rule quality, section ordering, character budgeting | `references/copilot/writing-instructions.md` |
| `applyTo` globs, `excludeAgent`, monorepo scoping | `references/copilot/scoping-and-targeting.md` |
| Debugging ignored/weak instructions | `references/copilot/troubleshooting.md` |
| Full-stack examples | `references/copilot/scenarios.md` |
| Starter patterns by scope | `references/copilot/micro-library.md` |

### Devin references

| Need | Read |
|---|---|
| REVIEW.md format, Bug Catcher behavior, scoping | `references/devin/review-spec.md` |
| Section order, severity phrasing, code examples | `references/devin/review-md/format-and-directives.md` |
| AGENTS.md structure and split decisions | `references/devin/agents-md/configuration.md` |
| Noise reduction, exclusions, severity tuning | `references/devin/customization/rules-and-exclusions.md` |
| Reusable security/performance/framework patterns | `references/devin/patterns/common-configurations.md` |
| Full-stack examples | `references/devin/scenarios.md` |
| Troubleshooting noisy/missing reviews | `references/devin/troubleshooting/common-issues.md` |
| Install, enrollment, verification | `references/devin/setup/getting-started.md` |

### Greptile references

| Need | Read |
|---|---|
| Install, indexing, permissions, first config | `references/greptile/setup.md` |
| config.json/files.json/rules.md parameter formats | `references/greptile/config-spec.md` |
| Rule quality bar, categories, severity, scoping | `references/greptile/rules-engineering.md` |
| Stack patterns, ignore patterns, monorepo strategy | `references/greptile/patterns.md` |
| Full end-to-end examples | `references/greptile/scenarios.md` |
| Status checks, API triggers, CI/CD wiring | `references/greptile/integration.md` |
| Diagnostic flow, common failures, canary protocol | `references/greptile/troubleshooting.md` |
| Anti-pattern catalog, preflight checks | `references/greptile/anti-patterns.md` |

## Key gotchas by platform

**Copilot:**
- Content after 4,000 characters is **silently ignored** — no warning
- Instructions must be on the **base branch** to affect the PR
- Review output is non-deterministic
- `excludeAgent` values: `"code-review"` or `"coding-agent"`

**Devin:**
- Phrasing directly controls Bug Catcher severity classification
- Devin reads 10+ other instruction file types — check for conflicts
- No documented precedence for overlapping `REVIEW.md` files — avoid contradictions
- `REVIEW.md` is for diff-flagging only; coding guidance goes in `AGENTS.md`

**Greptile:**
- `scope` as string instead of array **fails silently**
- `ignorePatterns` as array instead of string **fails silently**
- `fileChangeLimit: 0` skips **ALL** PRs
- `includeAuthors: []` means **all authors**, not none
- `.greptile/` silently overrides `greptile.json`
- Config must be on the **source branch** (opposite of Copilot)
