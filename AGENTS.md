# AGENTS.md -- skills-by-yigitkonur

This repository contains 47 skills for AI coding agents. Every skill is a first-class member of one curated pack -- same naming, same tone, same structure. Your job is to maintain that consistency.

## Repository layout

```
.
├── skills/                         # All skills live here
│   └── <verb>-<object>/            # Each skill directory
│       ├── README.md               # Install instructions and overview
│       └── skills/
│           └── <verb>-<object>/    # Skill content dir (matches skill name)
│               ├── SKILL.md        # Required -- the skill definition (hand-written)
│               └── references/     # Optional -- deep-dive docs routed from SKILL.md
├── scripts/
│   └── validate-skills.py          # Validates all skills (references, frontmatter, junk)
├── .github/workflows/
│   └── validate-skill-references.yml  # CI: validates on push/PR
├── .githooks/
│   └── pre-push                    # Blocks push on validation failure (quick mode)
├── NAMING.md                       # Verb-first prefix registry with full disambiguation rules
├── CONTRIBUTING.md                 # Skill structure, quality checklist, step-by-step contribution guide
└── README.md                       # Skill table, install commands, notes
```

## Commands

```bash
# Validate all skills (run before every push)
python3 scripts/validate-skills.py

# Enable pre-push hook (one-time setup)
git config core.hooksPath .githooks
```

## How users install

```bash
# Install all skills
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur

# Install a single skill
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/<skill-name>
```

## Naming -- the single most important convention

Every skill name is `verb-object` in `kebab-case`. The verb comes from a closed prefix registry in `NAMING.md`. Read that file before naming anything.

### Prefix quick reference

| Prefix | Creates what |
|---|---|
| `build-` | Application code using a framework/SDK |
| `convert-` | Transforms an existing artifact into a different format |
| `debug-` | Uses a diagnostic tool to investigate runtime behavior |
| `develop-` | Applies language-level standards while coding |
| `enhance-` | Tests and improves a skill's instructional quality |
| `extract-` | Reads code/assets and produces documentation |
| `init-` | Generates config files for an external tool |
| `optimize-` | Audits and improves an existing system |
| `plan-` | Applies structured thinking methods |
| `publish-` | Automates package releasing and CI/CD |
| `review-` | Evaluates existing code for quality |
| `run-` | Drives an external CLI tool or API |
| `test-` | Runs verification checks with pass/fail criteria |
| `use-` | Drives a CLI utility for a specific workflow |

### Naming rules

- Directory name = frontmatter `name` = README label. Always identical.
- Object names the thing acted on, not the technique: `build-supastarter-app` not `build-with-orpc-and-prisma`.
- Use the ecosystem's own name: `daisyui-mcp` not `component-library-server`.
- 2-3 words max after the verb. No `-guide`, `-helper`, `-util`, `-tool`, `-v2`, `-final` suffixes.
- If no prefix fits, propose a new one via PR with a full registry entry (see `NAMING.md`).

## Creating a new skill end-to-end

### 1. Pick the canonical name

Use the decision tree in `NAMING.md`. Verify no collision with existing skill directories in `skills/`.

### 2. Research before writing

For non-trivial skills, use `skill-dl` to search and download existing skills as evidence:

```bash
skill-dl search typescript mcp server sdk patterns --top 20
skill-dl https://playbooks.com/skills/owner/repo/skill-name -o ./corpus
```

Build a comparison table before synthesizing. Never copy a source skill wholesale -- distill patterns into repo-fit output.

### 3. Create the skill directory

```bash
mkdir -p skills/<skill-name>/skills/<skill-name>/references
```

### 4. Write SKILL.md

Write the skill definition at `skills/<skill-name>/skills/<skill-name>/SKILL.md`.

**Frontmatter** (required):
```yaml
---
name: verb-object
description: Use skill if you are [concrete trigger in 30 words or fewer].
---
```

Frontmatter rules:
- `name` exactly matches directory name
- `description` starts with `Use skill if you are`
- `description` is 30 words or fewer
- `description` describes *when to trigger*, not what the body contains
- Wrap description in double quotes if it contains colons
- No `<` or `>` characters in frontmatter
- No "claude" or "anthropic" in the skill name

**Body:**
- Write for an AI agent -- directive and operational ("Do X", "Check Y", "Never Z")
- Structure as a workflow or routing guide
- Keep under 500 lines -- move deep detail to `references/`
- Every file in `references/` must be explicitly routed from SKILL.md
- No unreferenced files -- they are dead weight

### 5. Create README.md

Add a `README.md` at the skill root (`skills/<skill-name>/README.md`) with the skill name, description, and install command.

### 6. Update root README.md

Add a row to the alphabetical skills table:

```markdown
| [verb-object](skills/verb-object/) | category | Short description (under 80 chars) |
```

### 7. Validate

```bash
python3 scripts/validate-skills.py
```

### 8. Push

```bash
git add skills/<skill-name>/ README.md NAMING.md
git commit -m "feat: add <skill-name> skill"
git push
```

## Editing an existing skill

1. Read the full existing SKILL.md and its references before changing anything.
2. Normalize frontmatter `description` to current standards while you are in there.
3. If you add a reference file, route it from SKILL.md. If you remove one, remove all references.
4. If you rename, update directory + frontmatter + README + NAMING.md + cross-skill references together.
5. Run `python3 scripts/validate-skills.py` before pushing.

## Quality checklist

Before finishing any skill work:

- [ ] Directory name starts with a verb prefix from the registry
- [ ] SKILL.md is at `skills/<name>/skills/<name>/SKILL.md`
- [ ] Frontmatter `name` exactly matches directory name
- [ ] Description starts with `Use skill if you are`, 30 words or fewer
- [ ] Every `references/` file is routed from SKILL.md
- [ ] No junk files (.DS_Store, .swp, LICENSE inside skill dirs)
- [ ] SKILL.md under 500 lines
- [ ] `python3 scripts/validate-skills.py` passes
- [ ] README.md exists at skill root with install command
- [ ] Root README row added/updated in alphabetical order
