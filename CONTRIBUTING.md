# Contributing a New Skill

## Source of truth

Before naming or documenting a skill, read **[NAMING.md](NAMING.md)**. Directory names, `SKILL.md` frontmatter `name`, README labels, and cross-skill references must all use the same canonical name.

## Skill Structure

Every skill lives in `skills/<skill-name>/` and follows this layout:

```
skills/my-skill/                    # Skill root (parent dir name = skill name per agentskills.io spec)
├── SKILL.md                        # Required -- the skill definition
├── README.md                      # Required -- per-skill install command
├── references/                     # Optional -- deep-dive reference docs
│   ├── topic-one.md
│   ├── topic-two.md
│   └── nested-domain/              # Optional -- nested grouping for large skills
│       └── detail.md
├── scripts/                        # Optional -- executable helpers (.sh, .mjs, .py)
└── assets/                         # Optional -- templates, fixtures
```

Flat layout per the agentskills.io specification (https://agentskills.io/specification): SKILL.md sits directly in the skill directory, alongside `references/`, `scripts/`, `assets/`. Claude Code's discovery paths (`~/.claude/skills/<name>/SKILL.md`, `.claude/skills/<name>/SKILL.md`, `<plugin>/skills/<name>/SKILL.md`) all assume this layout.

### SKILL.md

The only required file. It has two parts: YAML frontmatter and markdown body.

```markdown
---
name: my-skill
description: Use if applying a specific workflow this skill owns.
---

# My Skill

The body is the actual instruction set the agent follows.
```

**Frontmatter rules:**
- `name` must exactly match the directory name
- `description` must start with `Use if`
- `description` must be 100 characters or fewer
- `description` is the trigger -- write when to load the skill, not a body summary
- Include concrete phrases, tools, file patterns, or workflows when they help routing
- Keep it specific enough to avoid collisions with neighboring skills

**Body rules:**
- Write for an AI agent, not a human reader
- Be directive: "Do X", "Check Y", "Never Z"
- Structure as a workflow or routing guide
- Reference files in `references/` by relative path when the agent needs deeper context
- Prefer keeping `SKILL.md` focused and moving deep detail into references when the file becomes hard to scan

### references/

Deep-dive documents the `SKILL.md` can point agents to. Every file in `references/` **must** be referenced by `SKILL.md` -- unreferenced files are dead weight and should be removed or linked properly.

Good reference docs:
- Config specs with parameter tables
- Scenario templates with complete examples
- Anti-patterns and troubleshooting chains
- Architecture guides with diagrams
- Task-specific routing guides

**Naming:** Use descriptive `kebab-case`. For large skills, nested folders inside `references/` are valid when they improve discoverability.

## Adding a Skill -- Step by Step

1. **Create the directory** with the canonical name from `NAMING.md`.
   ```bash
   mkdir -p skills/my-skill/references skills/my-skill/scripts
   ```

2. **Write `SKILL.md`** at `skills/my-skill/SKILL.md` -- start with a frontmatter trigger description that begins with `Use if`, stays within 100 characters, and clearly tells the agent when to load the skill.

3. **Add reference docs** if the skill needs them -- make sure every file is explicitly referenced in `SKILL.md`.

4. **Create `README.md`** at the skill root (`skills/my-skill/README.md`) with the skill name, description, and install command.

5. **Validate locally** (catches errors before CI):
   ```bash
   python3 scripts/validate-skills.py
   ```
   This checks reference linkage, frontmatter format, and junk files.

6. **Check trigger collisions** -- if your skill overlaps with an existing one, test prompts that should go to both and make sure the descriptions are specific enough.

7. **Update `README.md`** -- add the skill to the matching category section, then add it to a bundle in the `GROUPS` map of `scripts/gen-marketplace.py` and run `python3 scripts/gen-marketplace.py` to refresh the plugin marketplace.

8. **Open a PR**.

---

## Quality Checklist

Before submitting:

- [ ] SKILL.md is at `skills/<name>/SKILL.md` (flat layout per agentskills.io spec)
- [ ] `name` in `SKILL.md` frontmatter matches the directory name exactly
- [ ] `description` starts with `Use if`
- [ ] `description` is 100 characters or fewer
- [ ] `description` includes trigger phrases a user would actually say
- [ ] Every file in `references/` is explicitly referenced in `SKILL.md`
- [ ] No unreferenced files, dead content, or stale sibling-skill names remain
- [ ] `SKILL.md` is focused enough to scan quickly, with deeper detail moved to references when useful
- [ ] No LICENSE files inside the skill directory unless explicitly required
- [ ] No `.DS_Store`, `.swp`, or other junk files
- [ ] Single-skill install works
- [ ] Whole-pack install still makes sense if the new skill is part of the combined repo
- [ ] Trigger phrasing does not accidentally collide with nearby skills unless the overlap is intentional

---

## Modifying an Existing Skill

- Edit `SKILL.md` or reference docs directly
- If you add a new reference file, make sure `SKILL.md` routes readers to it
- If you remove a reference file, remove all references to it from `SKILL.md`
- If you rename a skill, update the directory name, frontmatter `name`, frontmatter `description`, README label, and any cross-skill references together
- If you edit an existing skill without renaming it, normalize the frontmatter `description` to the current repo standard before you finish
- Re-check install paths, README label, description format, and cross-skill references after any rename or scope change

---

## Pre-push Hook (Recommended)

Enable the git hook to block pushes when validation fails:

```bash
git config core.hooksPath .githooks
```

This runs `scripts/validate-skills.py` before every push. The hook catches:
- Orphaned reference files not linked from SKILL.md
- SKILL.md referencing non-existent files
- Bad frontmatter (wrong name, missing "Use if", >100 chars)
- Junk files (evals/, .DS_Store, LICENSE inside skills)

---

## Conventions

| Convention | Rule |
|---|---|
| Directory names | Canonical `kebab-case`, install-path-friendly |
| Frontmatter `name` | Must exactly match the directory name |
| Reference file names | Descriptive `kebab-case(.md)` |
| Reference layout | Flat or nested under `references/` |
| SKILL.md size | Prefer lean routing files; move deep detail to references when needed |
| Reference doc size | Split when navigation becomes hard, not by a rigid line count |
| Frontmatter description | Start with `Use if`, stay within 100 characters, and optimize for trigger clarity |
| Code examples in SKILL.md | Use fenced blocks with language tags |
| Good/bad pattern examples | Label with `### Good` / `### Bad` headers |
