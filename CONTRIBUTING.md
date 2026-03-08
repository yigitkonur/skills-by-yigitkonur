# Contributing a New Skill

## Skill Structure

Every skill lives in `skills/<skill-name>/` and follows this layout:

```
skills/my-skill/
├── SKILL.md                    # Required — the skill definition
├── evals/
│   └── evals.json              # Optional — evaluation test cases
└── references/
    ├── topic-one.md            # Optional — deep-dive reference docs
    └── topic-two.md
```

### SKILL.md

The only required file. It has two parts: YAML frontmatter and markdown body.

```markdown
---
name: my-skill
description: >
  One paragraph that tells the AI agent WHEN to activate this skill.
  Be specific about trigger phrases, file patterns, and user intents.
  This is what the skills registry uses to match user requests to your skill.
---

# My Skill

The body is the actual instruction set the agent follows.
```

**Frontmatter rules:**
- `name` must match the directory name
- `description` is the trigger — write it like a search query, not a summary. Include the exact phrases a user would say ("set up code review", "debug Tauri app", "convert HTML to Next.js")

**Body rules:**
- Write for an AI agent, not a human reader. Be directive: "Do X", "Check Y", "Never Z"
- Structure as a workflow with numbered phases
- Reference files in `references/` by relative path when the agent needs deeper context
- Keep under 500 lines — if longer, move content to reference docs

### references/

Deep-dive documents the SKILL.md can point agents to. Every file in `references/` **must** be referenced by SKILL.md — unreferenced files are dead weight and will be removed in cleanup.

Good reference docs:
- Config specs with parameter tables
- Scenario templates with complete examples
- Anti-patterns and troubleshooting chains
- Architecture guides with diagrams

**Naming:** Use kebab-case, descriptive names. `config-spec.md` not `ref1.md`.

### evals/evals.json

Test cases for the skills.sh evaluation system. Format:

```json
{
  "skill_name": "my-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "The exact user message that should trigger this skill",
      "expected_output": "What a correct response must include — be specific and measurable",
      "files": []
    }
  ]
}
```

Each eval should test a different scenario or edge case. Include 5–10 evals for good coverage.

---

## Adding a Skill — Step by Step

1. **Create the directory:**
   ```bash
   mkdir -p skills/my-skill/references
   ```

2. **Write SKILL.md** — start with the frontmatter trigger description, then the workflow phases

3. **Add reference docs** if the skill needs them — make sure every file is referenced in SKILL.md

4. **Add evals** if you want automated quality testing on skills.sh

5. **Test locally** — install the skill in a project and verify it triggers correctly:
   ```bash
   npx skills add ./skills/my-skill
   ```

6. **Update README.md** — add your skill to the appropriate category table with a one-sentence description

7. **Open a PR**

---

## Quality Checklist

Before submitting:

- [ ] `name` in SKILL.md frontmatter matches the directory name
- [ ] `description` includes trigger phrases a user would actually say
- [ ] Every file in `references/` is explicitly referenced in SKILL.md
- [ ] No unreferenced files, no dead content
- [ ] SKILL.md is under 500 lines (move excess to references)
- [ ] No LICENSE or README files inside the skill directory (the repo root handles those)
- [ ] No `.DS_Store`, `.swp`, or other junk files
- [ ] Tested locally — the skill triggers and produces correct output

---

## Modifying an Existing Skill

- Edit SKILL.md or reference docs directly
- If you add a new reference file, make sure SKILL.md references it
- If you remove a reference file, remove all references to it from SKILL.md
- Run the skill's evals if they exist to check for regressions

---

## Conventions

| Convention | Rule |
|---|---|
| Directory names | `kebab-case`, descriptive |
| Reference file names | `kebab-case.md`, descriptive |
| SKILL.md size | Under 500 lines |
| Reference doc size | No hard limit, but split at ~300 lines |
| Frontmatter description | Include trigger phrases, not just a summary |
| Code examples in SKILL.md | Use fenced blocks with language tags |
| Good/bad pattern examples | Label with `### Good` / `### Bad` headers |
