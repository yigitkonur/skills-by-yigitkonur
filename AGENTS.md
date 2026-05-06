# AGENTS.md — skills-by-yigitkonur

This repository is a curated skills pack for AI coding agents — 44 skills sharing one naming system, one tone, one structure. Your job is to maintain that consistency when adding or editing skills.

## What this repo is

A single combined skills pack — not a loose collection. Every skill must feel like it belongs to the same family. Consistency, clarity, and install-path stability are more important than clever naming or one-off structure.

**Distribution model:**
- Users install the full pack: `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur`
- Or install a single skill: `npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/<skill-name>`

## Repository layout

```
.
├── skills/                         # All skills live here
│   └── <verb>-<object>/            # Each skill directory
│       ├── README.md               # Required — install instructions and overview
│       └── skills/
│           └── <verb>-<object>/    # Skill content dir (must match skill name)
│               ├── SKILL.md        # Required — the skill definition (hand-written)
│               └── references/     # Optional — deep-dive docs routed from SKILL.md
├── scripts/
│   └── validate-skills.py          # Validates all skills (references, frontmatter, junk)
├── .github/workflows/
│   └── validate-skill-references.yml  # CI: validates on push/PR
├── .githooks/
│   └── pre-push                    # Blocks push on validation failure
├── NAMING.md                       # Intent-verb naming principle, rules, and canonical names
├── CONTRIBUTING.md                 # Skill structure, quality checklist, contribution guide
└── README.md                       # Skill table, install commands, notes
```

## Commands

```bash
# Validate all skills (run before every push)
python3 scripts/validate-skills.py

# Enable pre-push hook (one-time setup)
git config core.hooksPath .githooks
```

---

## Naming

Every skill name follows **`verb-object`** in `kebab-case`. The verb is the most important word — users scan by what they want to *do*.

### Intent verb test

The verb in a skill name must be the verb you'd say out loud when reaching for it. Test by completing: *"I want to ___ ___"*. If the natural verb isn't in the name, rename.

Memory beats taxonomy. The right verb is the one that pops into your head when you need the skill — not the one a maintainer files it under.

Anchor on this set of plain-English verbs:

| Verb | Use when | Example |
|---|---|---|
| `build` | Write app code with a framework or SDK | `build-chrome-extension`, `build-mcp-server-sdk-v1` |
| `do` | Generic "let me do this" entry-point skill | `do-debug`, `do-think`, `do-review` |
| `apply` | Apply a methodology or standard to a codebase | `apply-clean-architecture`, `apply-macos-hig`, `apply-liquid-glass` |
| `ask` | Hand off / request something | `ask-review` |
| `run` | Drive a CLI, tool, or workflow | `run-agent-browser`, `run-codex-exec`, `run-research` |
| `convert` | Transform A to B | `convert-url-to-nextjs` |
| `check` | Audit for completeness | `check-completion` |
| `evaluate` | Triage existing feedback or input | `evaluate-code-review` |
| `extract` | Pull data, design, or assets from existing artifacts | `extract-saas-design` |
| `init` | Generate config or instruction files | `init-agent-config` |
| `enhance` | Improve a prompt, skill, or instruction | `enhance-prompt`, `enhance-skill-by-derailment` |
| `make` | Author Makefile targets / `make X` deployment & workflow scaffolding | `make-local`, `make-railway`, `make-vercel` |
| `optimize` | Tune for a constraint (e.g. agentic) | `optimize-agentic-cli`, `optimize-agentic-mcp` |
| `develop` | Apply language-level patterns and standards | `develop-typescript` |
| `publish` | Release to a registry | `publish-npm-package` |
| `test` | Verify with pass/fail | `test-by-mcpc-cli`, `test-macos-snapshots` |
| `use` | Drive a CLI utility for ongoing operations | `use-railway` |

### Object rules

1. **Name the thing acted on** — not the technique. `build-chrome-extension`, not `build-with-manifest-v3`.
2. **Preserve distinctive methodology names** in the object (e.g. `-by-derailment`, `-by-mcpc-cli`, `-to-nextjs`, `-for-agents`, `-sdk-v1`) — strip only the generic verb category, never the named technique.
3. **Use the ecosystem's own name** — `mcpc`, `liquid-glass`, `daisyui`.
4. **Keep it short** — 2-3 words max after the verb.
5. **No generic suffixes** — no `-guide`, `-helper`, `-util`.
6. **No version suffixes** unless the version is the point — `-sdk-v1` is OK because v1 and v2 are genuinely different SDKs.

### When two skills overlap, use distinct verbs to disambiguate

- `do-review` (do a PR review) vs `ask-review` (ask for a review on your branch)
- `do-debug` (entry-level systematic debug) vs `do-think` (deep reasoning framework)
- `optimize-agentic-cli` (CLI for agents) vs `optimize-agentic-mcp` (MCP server for agents)

### Anti-patterns

| Anti-pattern | Fix |
|---|---|
| No verb prefix (`agent-browser`) | Add the natural intent verb (`run-agent-browser`) |
| Awkward verb (`do-X` when a better verb fits) | Use the better verb (`extract-saas-design`, not `do-extract-design`) |
| Stripping a distinctive method (`enhance-skill` instead of `enhance-skill-by-derailment`) | Keep the method, normalize the verb only |
| Generic noun-only object (`build-app`) | Specific noun (`build-chrome-extension`) |
| Mismatched names | Directory = frontmatter `name` = README label, all identical |

---

## Skill structure

Every skill lives at `skills/<skill-name>/` with this layout:

```
skills/<verb>-<object>/
├── README.md                   # Required — install instructions and overview
└── skills/
    └── <verb>-<object>/        # Skill content dir (must match skill name)
        ├── SKILL.md            # Required — the skill definition
        └── references/         # Optional — deep-dive docs
            ├── topic-one.md
            ├── topic-two.md
            └── nested-domain/  # Nested folders are valid for large skills
                └── detail.md
```

Rules:
- `SKILL.md` is the main skill definition file
- `README.md` at the skill root has the skill name, description, category, and install command
- Every file in `references/` **must** be explicitly referenced from `SKILL.md` — unreferenced files are dead weight
- No junk files (`.DS_Store`, `.swp`, LICENSE files inside skill directories)
- No eval-related files or eval instructions

---

## Frontmatter requirements

```yaml
---
name: verb-object
description: Use skill if you are [concrete trigger in 30 words or fewer].
---
```

### Rules

| Rule | Detail |
|---|---|
| `name` | Must exactly match the directory name |
| `description` starts with | `Use skill if you are` |
| `description` word limit | 30 words or fewer |
| `description` purpose | Describe **when** the skill should trigger — not what the body contains |
| `description` content | Include concrete user intent, tools, file patterns, or workflows |
| `description` specificity | Specific enough to avoid accidental overlap with neighboring skills |
| `description` YAML safety | Wrap in double quotes if it contains colons |
| No `<` or `>` | Forbidden in frontmatter values |
| No "claude" or "anthropic" | Forbidden in skill names |

### Good descriptions

```
Use skill if you are reviewing a GitHub pull request with a systematic, evidence-based
workflow that clusters files, correlates existing comments, validates goals, and produces
actionable findings.
```

```
Use skill if you are building or extending a Convex + Clerk SwiftUI app and need
project-grounded patterns for reactive queries, auth, schema, or iOS/macOS integration.
```

```
Use skill if you are converting saved HTML snapshots into buildable Next.js pages with
self-hosted assets and extracted styles.
```

### Bad descriptions

| Example | Problem |
|---|---|
| `Best MCP skill ever.` | Hype, no trigger signal |
| `Research guide.` | No verb, no trigger, too vague |
| `Mandatory for all work.` | Overreaching, not actionable |
| `Guide for X that includes references, examples, and many workflows.` | Describes the body, not when to trigger |

---

## SKILL.md body requirements

Write for an AI agent, not a human tutorial reader. Keep under 500 lines — move deep detail into `references/`.

**Do:**
- Be directive and operational — "Do X", "Check Y", "Never Z"
- Structure as a workflow or routing guide
- Route clearly to reference docs by relative path (`references/topic.md`)
- Stay focused and scannable
- Move deep detail into `references/` when the top-level file gets heavy

**Don't:**
- Use stale external doc links when repo-local references exist
- Use inconsistent naming (the canonical name appears everywhere)
- Use vague hype language
- Duplicate instruction blocks

---

## README.md for each skill

Every skill needs a `README.md` at its root (`skills/<skill-name>/README.md`) with this format:

```markdown
# <skill-name>

<Description derived from SKILL.md frontmatter, with "Use skill if you are" prefix stripped>.

**Category:** <category>

## Install

Install this skill individually:

​```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/<skill-name>
​```

Or install the full pack:

​```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
​```
```

### Category map

| Category | When to use |
|---|---|
| `development` | Skills that write or review code, build apps, or apply language standards |
| `productivity` | Skills for planning, research, code review setup, skill creation |
| `configuration` | Skills that generate agent instruction files (CLAUDE.md, AGENTS.md) |
| `design` | Skills that extract or convert visual designs |
| `testing` | Skills that automate browser testing or verification |
| `orchestration` | Skills for multi-agent coordination |
| `platform` | Skills for a specific platform ecosystem (e.g., Railway) |
| `workflow` | Skills that author Makefile targets / multi-step scaffolding workflows for deployment, CI, or local dev |

---

## Root README integration

When adding or renaming a skill, add a row to the single alphabetical table in `README.md`:

```markdown
| [verb-object](skills/verb-object/) | category | Short description |
```

Keep descriptions short (under 80 chars). Match the terse style of existing rows. Place the row in alphabetical order.

---

## Current canonical skill names (49 skills)

Use this list to check for naming collisions:

```
apply-clean-architecture     apply-liquid-glass           apply-macos-hig
ask-review                   build-chrome-extension       build-convex-clerk-swiftui
build-copilot-sdk-app        build-effect-ts-v3           build-kernel-ts-sdk
build-langchain-ts-app       build-mcp-server-sdk-v1      build-mcp-server-sdk-v2
build-mcp-use-agent          build-mcp-use-client         build-mcp-use-server
build-raycast-script-command build-skills                 check-completion
convert-url-to-nextjs        develop-typescript           do-debug
do-review                    do-think                     enhance-prompt
enhance-skill-by-derailment  evaluate-code-review         extract-saas-design
init-agent-config            make-local                   make-railway
make-vercel                  optimize-agentic-cli         optimize-agentic-mcp
publish-npm-package          run-agent-browser            run-batch-codex-research
run-codex-exec               run-codex-review             run-github-scout
run-industry-research        run-issue-tree               run-playwright
run-repo-cleanup             run-research                 swift-quality-hooks
test-by-mcpc-cli             test-macos-snapshots         use-linear-cli
use-railway
```

---

## Creating a new skill

1. **Choose the canonical name** using the intent verb test and the verb table above
2. **Verify no naming collision** with the existing skills in this pack
3. **Research before writing** — for non-trivial skills, use `skill-dl` to search and download existing skills as evidence:
   ```bash
   skill-dl search typescript mcp server sdk patterns --top 20
   skill-dl https://playbooks.com/skills/owner/repo/skill-name -o ./corpus
   ```
   Build a comparison table before synthesizing. Never copy a source skill wholesale.
4. **Create the skill directory:**
   ```bash
   mkdir -p skills/<skill-name>/skills/<skill-name>/references
   ```
5. **Write `SKILL.md`** at `skills/<skill-name>/skills/<skill-name>/SKILL.md` with correct frontmatter
6. **Add `references/`** docs only if the skill needs them — reference every file from `SKILL.md`
7. **Create `README.md`** at the skill root with install instructions (see format above)
8. **Update root `README.md`** — add a row to the alphabetical table
9. **Validate:**
   ```bash
   python3 scripts/validate-skills.py
   ```
10. **Commit and push**

## Editing an existing skill

1. **Read** the full existing SKILL.md and its references before changing anything
2. **Normalize** frontmatter `name`, `description`, and README label to current standards
3. **Remove** stale internal references and old names everywhere
4. If you **add** a reference file, route to it from `SKILL.md`
5. If you **remove** a reference file, remove all references to it from `SKILL.md`
6. If you **rename**, update directory + frontmatter + README + NAMING.md + all cross-skill references together
7. **Validate** before pushing: `python3 scripts/validate-skills.py`

## Testing a skill's quality

Use the `enhance-skill-by-derailment` workflow: launch a Sonnet subagent with a real task using the skill, read the execution trace for friction points (`[STUCK]`, `[GUESSED]`, `[BROKE]`), and fix the skill's instructions directly. The fixed files are the deliverable — no reports.

---

## Quality checklist

Before finishing any skill work, verify **all** of the following:

- [ ] Directory name is canonical `kebab-case`, starts with an intent verb
- [ ] SKILL.md is at `skills/<name>/skills/<name>/SKILL.md` (required for Claude Code activation)
- [ ] Frontmatter `name` exactly matches the directory name
- [ ] Frontmatter `description` starts with `Use skill if you are`
- [ ] Frontmatter `description` is 30 words or fewer
- [ ] Frontmatter `description` describes when to trigger, not body contents
- [ ] Frontmatter `description` is wrapped in quotes if it contains colons
- [ ] No `<` or `>` in frontmatter, no "claude" or "anthropic" in name
- [ ] Every file in `references/` is explicitly referenced by `SKILL.md`
- [ ] No unreferenced files, dead content, or stale sibling-skill names remain
- [ ] Cross-skill references use canonical repo-local names only
- [ ] No junk files (`.DS_Store`, `.swp`, LICENSE files)
- [ ] No eval-related files or eval instructions
- [ ] SKILL.md under 500 lines
- [ ] Trigger phrasing does not accidentally collide with nearby skills
- [ ] `README.md` exists at skill root with install command
- [ ] Root README row added in alphabetical order with short description
- [ ] `python3 scripts/validate-skills.py` passes
- [ ] The skill reads like it belongs in the same repo family as the other skills in this pack

---

## Key design principles

- **Workspace first.** Always inspect the repo before searching remotely or drafting.
- **Evidence over instinct.** New skills require research (skill-dl search, comparison tables) before synthesis.
- **Progressive disclosure.** Trigger logic in frontmatter, workflow in SKILL.md, bulk detail in `references/`.
- **Original, repo-fit output.** Distill patterns from sources — never rename-clone another skill.
- **Lean is better.** If SKILL.md is growing because of examples or templates, move them to references or cut them.
- **Test before shipping.** Trigger tests + functional test + validation script.
