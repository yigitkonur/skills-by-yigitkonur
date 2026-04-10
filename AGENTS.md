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
├── NAMING.md                       # Verb-first prefix registry with full disambiguation rules
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

## Verb-first naming

Every skill name follows the pattern **`verb-object`** in `kebab-case`:
- **verb** — a prefix from the registry below that tells the user *what the skill does*
- **object** — a short noun phrase that tells the user *what it acts on*

The verb is the most important word. Users scan by verb: "I want to build something" → `build-*`, "I need to set something up" → `init-*`.

### Prefix registry

| Prefix | When to use | Not when |
|---|---|---|
| `build-` | Agent writes application code using a framework/SDK/library | Agent generates config (`init-`), runs a tool (`run-`), or reviews code (`review-`) |
| `convert-` | Agent transforms an existing artifact into a different format | Agent creates from scratch (`build-`), or produces documentation only (`extract-`) |
| `debug-` | Agent uses a diagnostic tool (DevTools, profiler, tracer) to investigate runtime issues | Agent runs a test suite (`test-`), reviews source code (`review-`) |
| `develop-` | Agent applies language-level standards — types, idioms, compiler config | Agent works within a specific framework (`build-`), or reviews a PR (`review-`) |
| `enhance-` | Agent tests and improves a skill's instructional quality | Agent creates a new skill (`build-skills`), reviews code (`review-`) |
| `extract-` | Agent reads code/CSS/assets and produces design documentation or structured data | Agent produces a buildable project (`convert-`), writes new code (`build-`) |
| `init-` | Agent generates config/instruction files consumed by an external tool | Agent writes application code (`build-`), or runs the tool interactively (`run-`) |
| `optimize-` | Agent audits and improves an existing system's quality | Agent writes new code (`build-`), runs diagnostics (`debug-`) |
| `plan-` | Agent frames a problem, compares options, or applies a decision methodology | Agent writes code (`build-`), generates config (`init-`), researches externally (`run-`) |
| `publish-` | Agent sets up automated publishing to a registry or creates release CI/CD | Agent writes the application itself (`build-`), generates non-CI config (`init-`) |
| `review-` | Agent evaluates existing code for quality, security, correctness | Agent generates review rules (`init-`), writes new code (`develop-`) |
| `run-` | Agent drives an external CLI tool, browser, or API for a productive task | Agent generates static config (`init-`), writes app code (`build-`), diagnoses bugs (`debug-`) |
| `test-` | Agent runs verification/validation checks with pass/fail expectations | Agent investigates unknowns (`debug-`), reviews source code (`review-`) |
| `use-` | Agent drives a CLI utility or external tool for a specific workflow | Agent writes app code (`build-`), generates config (`init-`) |

### Choosing a prefix — decision tree

```
What does the skill primarily do?
│
├─ Writes application code using a framework/SDK?          → build-
├─ Transforms an existing artifact into a different format? → convert-
├─ Uses a diagnostic tool to investigate runtime behavior?  → debug-
├─ Applies language-level patterns and standards?           → develop-
├─ Tests and improves a skill's instructional quality?      → enhance-
├─ Reads a codebase and produces design documentation?      → extract-
├─ Generates config/instruction files for an external tool? → init-
├─ Audits and improves an existing system?                  → optimize-
├─ Applies structured thinking methods to frame a decision? → plan-
├─ Automates package releasing and CI/CD publishing?        → publish-
├─ Evaluates existing code for quality/security/correctness?→ review-
├─ Drives an external CLI tool or API for a productive task?→ run-
├─ Runs verification checks with pass/fail criteria?        → test-
├─ Drives a CLI utility for a specific workflow?            → use-
└─ None of the above? → Propose a new prefix via PR
```

### Object naming rules

1. **Name the thing acted on**, not the technique — `build-supastarter-app` not `build-with-orpc-and-prisma`
2. **Use the ecosystem's own name** — `daisyui-mcp` not `component-library-server`
3. **Keep it short** — 2-3 words max after the verb
4. **No generic suffixes** — no `-guide`, `-helper`, `-util`, `-tool`, `-v2`, `-final`
5. **No redundancy with the verb** — `test-mcp-server` not `test-mcp-server-tests`
6. **Prefer specificity** — `publish-npm-package` not `publish-package`

### Naming anti-patterns

| Anti-pattern | Fix |
|---|---|
| No verb prefix (`agent-browser`) | `run-agent-browser` |
| Noun-first (`typescript-develop`) | `develop-typescript` |
| Generic suffix (`mcp-guide`) | `build-mcp-sdk-server` |
| Version suffix (`snapshot-nextjs-v2`) | `convert-snapshot-nextjs` |
| Marketing name as primary ID (`soul`) | Use verb-object for directory; marketing name in SKILL.md title only |
| Mismatched names across files | One canonical name everywhere: directory = frontmatter = README |
| Overly broad (`build-app`, `run-tool`) | `build-supastarter-app`, `run-playwright` |

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
Use skill if you are building or extending a Supastarter app and need project-grounded
patterns for routing, auth, API, billing, UI, storage, or deployment.
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

\`\`\`bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/<skill-name>
\`\`\`

Or install the full pack:

\`\`\`bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur
\`\`\`
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
| `platform` | Skills for a specific platform ecosystem (e.g., OpenClaw) |

---

## Root README integration

When adding or renaming a skill, add a row to the single alphabetical table in `README.md`:

```markdown
| [verb-object](skills/verb-object/) | category | Short description |
```

Keep descriptions short (under 80 chars). Match the terse style of existing rows. Place the row in alphabetical order.

---

## Current canonical skill names (45 skills)

Use this list to check for naming collisions:

```
build-chrome-extension      build-convex-clerk-swiftui   build-copilot-sdk-app
build-daisyui-mcp           build-hcom-systems           build-langchain-ts-app
build-mcp-use-agent         build-mcp-use-apps-widgets   build-mcp-use-client
build-mcp-sdk               build-mcp-sdk-v2             build-mcp-use-server
build-openclaw-plugin
build-openclaw-skill
build-openclaw-workflow      build-raycast-script-command build-skills
build-supastarter-app       convert-snapshot-nextjs       convert-vue-nextjs
debug-tauri-devtools        develop-clean-architecture    develop-macos-hig
develop-macos-liquid-glass  develop-typescript            enhance-prompt
enhance-skill-by-derailment extract-saas-design           init-agent-config
init-openclaw-agent         init-review                   optimize-mcp-server
publish-npm-package         review-pr                     run-agent-browser
run-athena-flow             run-codex-subagents           run-github-scout
run-hcom-agents             run-issue-tree                run-openclaw-agents
run-openclaw-deploy         run-playwright                run-research
test-by-mcpc-cli
```

---

## Creating a new skill

1. **Choose the canonical name** using the prefix registry and decision tree above
2. **Verify no naming collision** with the 44 existing skills
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

- [ ] Directory name is canonical `kebab-case`, starts with a verb prefix
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
- [ ] The skill reads like it belongs in the same repo family as the existing 43 skills

---

## Key design principles

- **Workspace first.** Always inspect the repo before searching remotely or drafting.
- **Evidence over instinct.** New skills require research (skill-dl search, comparison tables) before synthesis.
- **Progressive disclosure.** Trigger logic in frontmatter, workflow in SKILL.md, bulk detail in `references/`.
- **Original, repo-fit output.** Distill patterns from sources — never rename-clone another skill.
- **Lean is better.** If SKILL.md is growing because of examples or templates, move them to references or cut them.
- **Test before shipping.** Trigger tests + functional test + validation script.
