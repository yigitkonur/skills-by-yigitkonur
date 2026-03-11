---
name: init-copilot-review
description: Use skill if you are creating or refining GitHub Copilot code review instruction files such as .github/copilot-instructions.md and scoped *.instructions.md for repository-specific PR reviews.
---

# Copilot Review Init

Create or refine GitHub Copilot review instruction files for a specific repository. Focus on repo-grounded `copilot-instructions.md` and scoped `*.instructions.md` files that improve pull request review quality without wasting character budget.

## Trigger boundaries

Use this skill when you need to:
- Create or revise `.github/copilot-instructions.md`
- Create, split, or tighten `.github/instructions/*.instructions.md`
- Decide root vs scoped review rules, monorepo/package scoping, `applyTo`, or `excludeAgent`
- Debug why Copilot review ignores, misroutes, or weakly follows instruction files

Do not use this skill when:
- You are reviewing a PR directly instead of authoring Copilot review instructions
- You are creating non-Copilot agent files such as `CLAUDE.md`, `AGENTS.md`, or generic review docs
- You want generic best-practice prose without grounding it in the target repository

## Start with the smallest relevant reference set

| Need | Read |
| --- | --- |
| File locations, root vs scoped format, base-branch behavior, character limits | `references/setup-and-format.md` |
| Rule-writing quality, root vs scoped content decisions, character budgeting, iteration | `references/writing-instructions.md` |
| `applyTo`, `excludeAgent`, precedence, monorepo layout, overlapping scopes | `references/scoping-and-targeting.md` |
| Ignored instructions, wrong file scope, debugging order, verification | `references/troubleshooting.md` |
| Full-stack examples after the file architecture is chosen | `references/scenarios.md` |
| Small starter patterns after repo grounding | `references/micro-library.md` |

Do not read every reference by default. Start with the minimum set that fits the task, then expand only if a real uncertainty remains.

## Workflow

### 1. Ground on the repository before drafting

Inspect the actual repository first:
- Structure: single app, multi-service, or monorepo
- Dominant languages, frameworks, and path boundaries
- Existing `.github/copilot-instructions.md`, `.github/instructions/`, `CONTRIBUTING.md`, `CLAUDE.md`, and similar repo guidance
- Linter, formatter, test, and CI configuration so you do not waste rule budget on enforced style rules
- Representative files in each scope you may target
- Recurring review themes from existing conventions, risk areas, or repeated code patterns

Repo evidence is the source of truth. If the repository does not clearly support a stack-specific rule, do not invent it.

### 2. Choose the instruction architecture before writing prose

Start from this default shape:

```text
.github/
├── copilot-instructions.md
└── instructions/
    ├── <language>.instructions.md
    └── <domain-or-package>.instructions.md
```

Use this placement logic:

| Put it in | When |
| --- | --- |
| `.github/copilot-instructions.md` | The rule is truly universal across the repo: security fundamentals, shared error-handling philosophy, shared performance red flags, or repo-wide testing expectations |
| `.github/instructions/<language>.instructions.md` | The rule applies to one language or ecosystem and is not just a linter concern |
| `.github/instructions/<framework-or-path>.instructions.md` | The rule applies only to a framework, directory, layer, or critical path such as `api`, `auth`, `migrations`, or `components` |
| Package/service-scoped `*.instructions.md` | A monorepo package or service has unique review needs not already covered by repo-wide rules |
| `excludeAgent` | A rule should guide code review but would confuse the coding agent, or vice versa |

Steering rules:
- Start minimal: most repos should begin with **1 repo-wide file plus 2-4 scoped files**
- Grow toward **5-12 total files** only when repo breadth justifies it
- Do **not** create a file just because you detected a language or framework; create it only if you have **2-3 high-signal rules unique to that scope**
- Do **not** dump everything into `copilot-instructions.md`; that causes scope bleed and usually wastes the 4,000-character limit
- Monorepo package files must contain only package-unique rules, not repeated root rules

### 3. Select rules with evidence and reuse discipline

Every rule should be **Specific, Measurable, Actionable, and Semantic**.

Use this filter:

| Keep | Drop |
| --- | --- |
| Rules backed by repo code, configs, docs, or repeated defects | Generic best practices with no repo evidence |
| Semantic review guidance about security, architecture, data flow, error handling, performance, tests, or accessibility | Formatting, import order, spacing, quote style, or other linter territory |
| Short imperative bullets that say what to flag and why | Narrative paragraphs, hedged advice, or vague slogans like "write clean code" |
| Adapted examples using repo patterns | Copy-pasted templates or external-link references |

Reusable categories are helpful only when the repository actually needs them:
- Repo-wide candidates: security, shared error handling, shared performance risks, testing philosophy
- Scoped candidates: language idioms, framework conventions, API validation, auth/payment paths, migrations, package boundaries, test-file rules

If you use `references/scenarios.md` or `references/micro-library.md`, treat them as pattern libraries. Adapt them to the repo; never copy them verbatim.

### 4. Draft files with scope-safe formatting

When writing files:
- `copilot-instructions.md` is plain Markdown in `.github/` and has **no frontmatter**
- Every scoped file lives under `.github/instructions/`
- Every scoped file starts at **line 1** with YAML frontmatter
- `applyTo` is a **single quoted or double-quoted glob string** relative to repo root
- `excludeAgent`, when used, should be either `"code-review"` or `"coding-agent"`
- File names should use `kebab-case.instructions.md`
- Highest-priority rules go first
- Keep examples short and include them only when they clarify a semantic rule

Overlapping scoped files are acceptable only when the rules are **additive**. If two matching files would disagree, narrow `applyTo` until they no longer conflict. Multiple matching scoped files are concatenated, so never rely on overlap to resolve contradictions for you.

### 5. Validate before presenting anything

Check all of these:
- Each file stays under the **hard 4,000-character limit**; aim for **2,500-3,500**
- Frontmatter counts toward the limit
- No external links
- No attempts to control Copilot's comment formatting, severity labels, approvals, or merge blocking
- No rules duplicated from linter or formatter config
- No contradictory rules across overlapping scopes
- Root file contains only universal rules
- Package/service files do not repeat root rules
- Instruction changes are intended for the **base branch** of the PR, because feature-branch instruction changes do not affect the same PR's review

Use `wc -c` for character counts and verify that representative files actually match each `applyTo` pattern.

### 6. Present the result as an architecture, not just a dump

Return:
- The `.github/` file tree
- Full contents of each generated instruction file
- A brief per-file explanation covering:
  - Why this file exists
  - What scope it targets
  - Which repo evidence justified its rules
  - Why the rule set was kept out of other files

If repo evidence is weak or mixed, say so explicitly and keep the instruction set conservative.

## Do this, not that

| Do this | Not that |
| --- | --- |
| Use repo code and configs as the primary evidence base | Write generic rules from memory |
| Put universal semantic rules in `copilot-instructions.md` | Put framework- or path-specific rules in the root file |
| Add a scoped file only when the scope has unique review value | Generate one file for every detected tool |
| Use short, imperative, semantic bullets | Write long prose or vague quality slogans |
| Adapt scenario and template references to the repo | Copy templates verbatim |
| Split files when they near 4,000 characters | Assume trailing content will still be read |
| Make overlapping files complementary | Rely on conflicting files and hope Copilot resolves them |
| Plan for base-branch rollout and re-review | Assume feature-branch changes affect the current PR automatically |

## Recovery paths

If the task starts drifting, recover in this order:
1. **Too broad or too many files** → collapse to the root file plus only the highest-signal scoped files
2. **File near 4,000 characters** → remove low-priority rules, shorten examples, or split by narrower `applyTo`
3. **Unclear scoping** → inspect representative repo files and choose the narrowest glob that still matches the intended scope
4. **Conflicting rules** → make scopes non-overlapping or rewrite the rules to be additive
5. **Weak or generic Copilot comments** → rewrite rules for specificity and remove linter-level noise
6. **Instructions seem ignored** → follow `references/troubleshooting.md` in order: location → character count → frontmatter → base branch → glob match → conflicts → specificity → incremental retest → re-review

## Reference routing

- **`references/setup-and-format.md`** — file locations, root vs scoped formats, character limits, review modes, configuration levels, and base-branch behavior
- **`references/writing-instructions.md`** — SMSA rule quality, section ordering, root vs scoped content decisions, character budgets, code examples, and iteration workflow
- **`references/scoping-and-targeting.md`** — `applyTo`, `excludeAgent`, precedence, additive overlap, monorepo layout, and optimal file counts
- **`references/troubleshooting.md`** — ignored instructions, scope mistakes, architecture mistakes, debugging order, verification, and non-determinism
- **`references/scenarios.md`** — full-stack examples to adapt only after the file architecture is already chosen
- **`references/micro-library.md`** — small templates to adapt only after repo grounding when you need a starter pattern for a specific scope
