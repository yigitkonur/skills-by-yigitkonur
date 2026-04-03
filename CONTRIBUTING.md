# Contributing a New Skill

## Source of truth

Before naming or documenting a skill, read **[NAMING.md](NAMING.md)**. Directory names, `SKILL.md` frontmatter `name`, README labels, and cross-skill references must all use the same canonical name.

## Skill Structure

Every skill lives in `skills/<skill-name>/` and follows this layout:

```
skills/my-skill/                    # Plugin root (installed by Claude Code)
├── .claude-plugin/
│   └── plugin.json                 # Auto-generated plugin manifest
└── skills/
    └── my-skill/                   # Skill content dir (must match plugin name)
        ├── SKILL.md                # Required — the skill definition
        └── references/
            ├── topic-one.md        # Optional — deep-dive reference docs
            ├── topic-two.md
            └── nested-domain/      # Optional — nested grouping for large skills
                └── detail.md
```

The `skills/<name>/` subdirectory inside the plugin root is required for Claude Code to discover and activate the skill.

### SKILL.md

The only required file. It has two parts: YAML frontmatter and markdown body.

```markdown
---
name: my-skill
description: Use skill if you are applying a specific workflow this skill owns.
---

# My Skill

The body is the actual instruction set the agent follows.
```

**Frontmatter rules:**
- `name` must exactly match the directory name
- `description` must start with `Use skill if you are`
- `description` must be 30 words or fewer
- `description` is the trigger — write when to load the skill, not a body summary
- Include concrete phrases, tools, file patterns, or workflows when they help routing
- Keep it specific enough to avoid collisions with neighboring skills

**Body rules:**
- Write for an AI agent, not a human reader
- Be directive: "Do X", "Check Y", "Never Z"
- Structure as a workflow or routing guide
- Reference files in `references/` by relative path when the agent needs deeper context
- Prefer keeping `SKILL.md` focused and moving deep detail into references when the file becomes hard to scan

### references/

Deep-dive documents the `SKILL.md` can point agents to. Every file in `references/` **must** be referenced by `SKILL.md` — unreferenced files are dead weight and should be removed or linked properly.

Good reference docs:
- Config specs with parameter tables
- Scenario templates with complete examples
- Anti-patterns and troubleshooting chains
- Architecture guides with diagrams
- Task-specific routing guides

**Naming:** Use descriptive `kebab-case`. For large skills, nested folders inside `references/` are valid when they improve discoverability.

## Adding a Skill — Step by Step

1. **Create the directory** with the canonical name from `NAMING.md`.
   ```bash
   mkdir -p skills/my-skill/skills/my-skill/references
   mkdir -p skills/my-skill/.claude-plugin
   ```

2. **Write `SKILL.md`** at `skills/my-skill/skills/my-skill/SKILL.md` — start with a frontmatter trigger description that begins with `Use skill if you are`, stays within 30 words, and clearly tells the agent when to load the skill.

3. **Add reference docs** if the skill needs them — make sure every file is explicitly referenced in `SKILL.md`.

4. **Validate locally** (catches errors before CI):
   ```bash
   python3 scripts/validate-skills.py
   ```
   This checks reference linkage, frontmatter format, junk files, and marketplace consistency.

5. **Test install**:
   ```bash
   claude --plugin-dir ./skills/my-skill
   ```

6. **Check trigger collisions** — if your skill overlaps with an existing one, test prompts that should go to both and make sure the descriptions are specific enough.

7. **Regenerate marketplace files**:
   ```bash
   python3 scripts/generate-marketplace.py
   ```
   This updates `.claude-plugin/marketplace.json` and creates `skills/<name>/.claude-plugin/plugin.json`. If the skill is new, add its category to the `CATEGORIES` dict in the script first.

8. **Update `README.md`** — add a row to the skills table (alphabetical order).

9. **Open a PR**.

---

## Quality Checklist

Before submitting:

- [ ] SKILL.md is at `skills/<name>/skills/<name>/SKILL.md` (required for Claude Code activation)
- [ ] `name` in `SKILL.md` frontmatter matches the directory name exactly
- [ ] `description` starts with `Use skill if you are`
- [ ] `description` is 30 words or fewer
- [ ] `description` includes trigger phrases a user would actually say
- [ ] Every file in `references/` is explicitly referenced in `SKILL.md`
- [ ] No unreferenced files, dead content, or stale sibling-skill names remain
- [ ] `SKILL.md` is focused enough to scan quickly, with deeper detail moved to references when useful
- [ ] No LICENSE or README files inside the skill directory unless explicitly required
- [ ] No `.DS_Store`, `.swp`, or other junk files
- [ ] `scripts/generate-marketplace.py` ran and skill appears in `.claude-plugin/marketplace.json`
- [ ] `skills/<name>/.claude-plugin/plugin.json` exists with correct name and version
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

This runs `scripts/validate-skills.py --quick` before every push. The hook catches:
- Orphaned reference files not linked from SKILL.md
- SKILL.md referencing non-existent files
- Bad frontmatter (wrong name, missing "Use skill if you are", >30 words)
- Junk files (evals/, .DS_Store, LICENSE inside skills)

The full validation (including marketplace consistency) runs in CI.

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
| Frontmatter description | Start with `Use skill if you are`, stay within 30 words, and optimize for trigger clarity |
| Code examples in SKILL.md | Use fenced blocks with language tags |
| Good/bad pattern examples | Label with `### Good` / `### Bad` headers |
