---
name: init-greptile-review
description: Use skill if you are generating `.greptile/` review config, scoped rules, or context-file mappings for Greptile pull request reviews in a specific repository.
---

# Init Greptile Review

Generate repo-specific Greptile configuration that makes Greptile catch meaningful bugs, security issues, architectural violations, and contract drift without wasting semantic review budget on lint-like trivia.

## What good Greptile setup looks like

Greptile is a semantic PR reviewer, not a linter.

- Use Greptile for architecture boundaries, security invariants, API contracts, performance pitfalls, dependency misuse, compliance, and cross-file reasoning.
- Leave semicolons, formatting, import sorting, and other linter/formatter work to ESLint, Prettier, Ruff, RuboCop, golangci-lint, and similar tools.
- Greptile reads repo-local config from the **source branch** of the PR.
- Changes apply on the **next PR or re-review**, not retroactively.
- Prefer `.greptile/` over legacy `greptile.json`.

## Decision tree

```
What are you doing?
│
├── First-time setup, permissions, or indexing ───────────────► references/setup.md
├── Authoring or tuning .greptile/config.json / files.json ──► references/config-spec.md
├── Designing repo-specific review rules ─────────────────────► references/rules-engineering.md
├── Matching a common stack or monorepo layout ───────────────► references/patterns.md
├── Needing full end-to-end examples ─────────────────────────► references/scenarios.md
├── Wiring status checks, API triggers, or CI/CD ─────────────► references/integration.md
└── Debugging ignored config, noisy reviews, or rollout checks ► references/troubleshooting.md + references/anti-patterns.md
```

## Quick start

By default, generate only the files the repo actually needs:

```
.greptile/
├── config.json      # always
├── rules.md         # only when rules need examples, migration notes, or nuanced narrative
└── files.json       # only when docs/specs/schemas materially improve review

packages/payments/.greptile/config.json  # only when a subtree needs different strictness or extra rules
```

Start lean:

- Default to `strictness: 2` and `commentTypes: ["logic", "syntax"]`
- Add `"style"` only when the repo lacks strong formatting/linting
- Start with **5-10 high-signal rules**, not 20 generic ones
- If migrating from `greptile.json`, move to `.greptile/` and delete the legacy file

## Workflow

Follow these six phases in order.

### Phase 1: Classify the request and current Greptile state

Before writing anything, determine what kind of job this is:

- **New setup** — no existing `.greptile/` or `greptile.json`
- **Tune existing config** — root config exists and should be extended, not replaced
- **Monorepo split** — different packages/services need different strictness or rules
- **Troubleshooting** — existing config is ignored, noisy, or missing real issues
- **Integration** — status checks, API triggers, CI/CD, or merge gating

Inspect for:

- Existing `.greptile/` folders at root and child directories
- Legacy `greptile.json`
- Existing docs/specs/schemas that could become `files.json`
- Existing linters/formatters so you do not duplicate them

If config already exists, preserve working pieces and tighten only what the repo evidence supports.

### Phase 2: Map the review surface

Explore the repository before choosing rules:

1. **Structure** — monorepo vs single-service, top-level packages/apps/services, critical directories
2. **Stack** — languages, frameworks, ORM, transport layers, testing stack
3. **Risk zones** — auth, payments, PII, file system, shell execution, IPC, migrations, infra
4. **Generated/noisy files** — build output, generated code, lockfiles, snapshots, vendored code
5. **Useful context files** — architecture docs, ADRs, OpenAPI, schemas, shared types, contribution guides
6. **Existing quality controls** — linters, formatters, CI, custom rules, security scanners
7. **Recurring failure patterns** — user-stated pain points, incident history, review gaps, repeated bugs

Treat file targeting as part of the design: the same repo map should drive `rules`, `files.json`, `ignorePatterns`, child configs, and any `patternRepositories`.

### Phase 3: Choose file topology and strictness

**Always generate:** root `.greptile/config.json`

**Generate only when needed:**

- `.greptile/rules.md` — rules need good/bad examples, nuanced reasoning, or migration guidance
- `.greptile/files.json` — docs/specs/schemas genuinely improve review quality
- Child `.greptile/config.json` — a subtree needs different strictness, extra rules, or `disabledRules`

**Monorepo rule:** prefer root defaults plus child overrides only where review needs truly diverge.

Inheritance that matters:

- Child `rules` **extend** parent rules
- Child `disabledRules` turns off parent rules by `id`
- Child `strictness`, `commentTypes`, and `triggerOnUpdates` **override**
- Child `ignorePatterns` **extend**

Strictness guidance:

- `2` for most production code
- `1` for payments, auth, security-critical, or compliance-heavy paths
- `3` for internal tools, prototypes, or low-risk directories where noise must stay low

Only tune PR filters (`labels`, authors, branches, `fileChangeLimit`) or summary behavior when the user asks for it or the repo workflow clearly needs it.

### Phase 4: Engineer semantic rules from architecture signals

Every rule must be **repo-specific, specific, measurable, actionable, scoped, semantic, and identifiable**.

Use the repo signals to decide which rule categories matter:

| Repo signal you observe | Prefer rules about | Typical targeting move |
|---|---|---|
| Auth, payments, PII, file system, shell, IPC, secrets | Security + compliance | High severity, scoped to the sensitive subtree; consider child strictness `1` |
| Controllers/services/repositories, package boundaries, gateway clients, shared libraries | Architecture boundaries | Scope to the layers/packages where dependency direction matters |
| OpenAPI specs, shared SDKs, backend repos, design systems | API contracts + dependencies | Scope to routes, client hooks, components, or integration code; use `files.json` or `patternRepositories` if they materially help |
| ORM usage, query builders, background jobs, caching, async workflows | Performance + data integrity | Scope to DB, views, serializers, jobs, workers, or service paths |
| Monorepo packages with different stacks or risk profiles | Cascading configs | Root defaults, then child configs only for packages that need different behavior |

Rule-writing heuristics:

- Start with **5-10 rules max**
- Tie each rule to an actual repo path, library, contract, or failure mode
- Tell Greptile what the correct alternative is, not just what to avoid
- Give every parent-level rule an `id` if a child config might disable it
- If a rule would fire on almost every PR, narrow it or delete it

### Phase 5: Scope rules, context, and file targeting precisely

Use Greptile's semantic budget where it matters:

- `scope` must be an **array** of globs, never a comma-separated string
- `ignorePatterns` must be a **newline-separated string**, not an array
- Scope context files to the code they inform; do not attach a Prisma schema to frontend components
- Use `patternRepositories` only for real cross-repo contracts or design systems, in `org/repo` format
- Exclude generated files, lockfiles, snapshots, build output, vendored code, and other high-noise surfaces
- If strong linting/formatting already exists, do **not** add style-focused Greptile rules

When deciding between JSON rules and prose rules:

- Use `config.json` for crisp pass/fail rules
- Use `rules.md` only when examples or narrative make the rule materially easier for Greptile to apply

### Phase 6: Validate, output, and recover if needed

Before finalizing any output:

- [ ] JSON validates locally (for example: `python3 -m json.tool .greptile/config.json`)
- [ ] `scope` values are arrays of strings
- [ ] `ignorePatterns` is a newline-separated string
- [ ] `strictness` is 1, 2, or 3
- [ ] `commentTypes` only uses `"logic"`, `"syntax"`, `"style"`, `"info"`
- [ ] `patternRepositories` uses `org/repo`, not full URLs
- [ ] `files.json` only points to files that actually exist
- [ ] No rule duplicates lint/format tooling
- [ ] No `.greptile/` + `greptile.json` coexistence remains after migration

Output every generated configuration with:

1. a file tree
2. complete file contents
3. short reasoning annotations tied to specific repo evidence
4. a canary test or verification step
5. migration notes if replacing `greptile.json`

If Greptile still behaves incorrectly, recover in this order:

1. Repo indexed?
2. JSON valid?
3. `.greptile/` conflicting with `greptile.json`?
4. Config on the PR's **source branch**?
5. `scope` actually matches changed files?
6. `strictness` suppressing the severity you used?
7. Author/branch/file-limit filters excluding the PR?
8. Force a re-review, then remove any canary rule after verification

## Do this, not that

| Do this | Not that |
|---|---|
| Write rules that require semantic reasoning, architecture awareness, or cross-file understanding | Spend Greptile on semicolons, formatting, or other linter work |
| Tie each rule to actual repo evidence: paths, libraries, contracts, incident patterns | Paste generic "best practices" or framework boilerplate |
| Start lean with 5-10 high-signal rules | Dump 20-30 mediocre rules and hope strictness fixes the noise |
| Scope rules and context files aggressively | Apply database, auth, or design-system rules to the whole repo |
| Use child configs only where behavior truly differs | Create a child config for every package by default |
| Use `rules.md` for nuanced examples and migrations | Put explanatory comments inside JSON |
| Use `patternRepositories: ["org/repo"]` only when external code truly informs review | Use full GitHub URLs or add repos that do not affect review decisions |
| Raise strictness only in critical paths | Set `strictness: 1` across the whole repo without evidence |

## Minimal reading sets

### "I need to set up Greptile from scratch"

- `references/setup.md`
- `references/config-spec.md`
- `references/troubleshooting.md`

### "I need repo-specific rules that catch real issues"

- `references/rules-engineering.md`
- `references/patterns.md`
- `references/anti-patterns.md`

### "I need a monorepo design"

- `references/config-spec.md`
- `references/patterns.md`
- `references/scenarios.md`

### "I need CI/CD or status-check integration"

- `references/integration.md`
- `references/setup.md`
- `references/config-spec.md`

### "The config is noisy, ignored, or not firing"

- `references/troubleshooting.md`
- `references/anti-patterns.md`
- `references/rules-engineering.md`

## Reference files

| Reference | What it covers | When to read |
|---|---|---|
| `references/setup.md` | GitHub/GitLab install, indexing, permissions, placement, first config | First-time setup or platform questions |
| `references/config-spec.md` | Parameter formats, `.greptile/` file roles, cascading behavior, child overrides | Writing or editing `config.json`, `files.json`, or monorepo overrides |
| `references/rules-engineering.md` | Rule quality bar, categories, severity, scoping, rule lifecycle | Designing repo-specific rules |
| `references/patterns.md` | Stack patterns, ignore patterns, monorepo strategy, context-file patterns | Matching a detected architecture to a starting shape |
| `references/scenarios.md` | Complete end-to-end examples for common stacks | You need a full output example to adapt |
| `references/integration.md` | Status checks, API triggers, manual review triggers, CI/CD, notifications | Integrating Greptile into delivery workflows |
| `references/troubleshooting.md` | Diagnostic flow, common failures, validation protocol, migration steps | Config is ignored, too noisy, or not triggering |
| `references/anti-patterns.md` | Anti-pattern catalog, troubleshooting chain, canary verification | Final preflight before shipping |

## Key gotchas

- Greptile reads config from the **source branch**, not the target branch
- Config changes affect the **next PR or re-review**, not past reviews
- `ignorePatterns` skips **review**, not **indexing**
- `includeAuthors: []` means **all authors**
- `fileChangeLimit: 0` skips **all** PRs
- `statusCheck: true` suppresses "X files reviewed" comment spam better than `statusCommentsEnabled: false`
- `.greptile/` silently overrides `greptile.json`
- `scope` is an array; `ignorePatterns` is a newline-separated string
- Dashboard or org rules may still influence behavior outside repo-local files

## Final reminder

Start with the smallest relevant reading set, then expand only when the task requires it. The goal is not to write the most rules — it is to generate the smallest `.greptile/` configuration that helps Greptile catch the issues this specific repository actually misses.
