---
name: build-openclaw-skill
description: Use skill if you are creating OpenClaw skills — SKILL.md format, metadata gating, and ClawHub publishing.
---

# Build OpenClaw Skill

Create production-grade custom skills for the OpenClaw AI agent runtime.

## Trigger boundary

Use this skill when the task involves:

- Creating a new OpenClaw skill from scratch
- Writing or editing a SKILL.md file for an OpenClaw agent
- Configuring frontmatter fields (name, description, metadata, gating)
- Organizing reference files for progressive disclosure
- Adding metadata gating (required binaries, env vars, config keys)
- Testing a skill before deployment
- Publishing a skill to ClawHub

Do NOT use this skill for:

- General OpenClaw runtime configuration (not skill-specific)
- Building MCP servers (use optimize-mcp-server or similar)
- Writing agent orchestration logic outside the skill system
- Modifying OpenClaw core or built-in skills

## Non-negotiable rules

1. **SKILL.md is the only required file.** A valid skill is a directory containing SKILL.md with YAML frontmatter. Everything else is optional.
2. **Frontmatter starts on line 1.** No blank lines before the opening `---`. Any YAML syntax error silently prevents loading.
3. **No angle brackets in frontmatter.** Characters `<` and `>` can inject unintended instructions into the agent system prompt.
4. **No reserved names.** Skill names must not contain "claude" or "anthropic" (reserved by Anthropic).
5. **Description under 1024 chars.** The description field is the primary auto-invocation signal. Keep it dense with trigger phrases.
6. **SKILL.md under 500 lines.** Move detailed content to `references/`. The body is loaded on every invocation.
7. **Every reference file must be routed.** If a file exists in `references/`, it must be reachable from SKILL.md via a decision tree, routing table, or reading set.
8. **Metadata must be single-line JSON.** The `metadata` field uses inline JSON, not multi-line YAML.

## Decision tree

```
What do you need to do with an OpenClaw skill?
|
+-- Create a new skill from scratch
|   |
|   +-- Read references/skill-format-spec.md for the complete format
|   +-- Follow the "New skill workflow" below
|   +-- Need environment gating? --> references/metadata-gating.md
|
+-- Add metadata gating to an existing skill
|   |
|   +-- Read references/metadata-gating.md
|   +-- Need installer specs? --> references/metadata-gating.md (Installer section)
|   +-- Running in sandbox? --> references/metadata-gating.md (Sandbox section)
|
+-- Organize or restructure reference files
|   |
|   +-- Read references/reference-organization.md
|   +-- Check routing: every file in references/ must appear in SKILL.md
|
+-- Test a skill before deployment
|   |
|   +-- Read references/testing-skills.md
|   +-- Trigger tests: 5+ should-trigger, 5+ should-NOT-trigger
|   +-- Functional tests: run primary workflow end-to-end
|
+-- Publish to ClawHub
    |
    +-- Read references/clawhub-publishing.md
    +-- Run the publishing checklist before submitting
```

## New skill workflow

### 1. Choose a name

Follow kebab-case verb-noun naming: `build-dashboard`, `run-analysis`, `init-project`.

Rules:
- Lowercase letters, numbers, hyphens only
- Max 64 characters
- No leading/trailing hyphens, no consecutive hyphens
- No "claude" or "anthropic" in the name
- Directory name must match frontmatter `name` exactly

### 2. Create the directory structure

```
my-skill-name/
+-- SKILL.md              # Required
+-- references/            # Optional, for detailed guides
|   +-- topic-a.md
|   +-- topic-b.md
+-- scripts/               # Optional, for executable helpers
+-- assets/                # Optional, for templates/static files
```

### 3. Write the frontmatter

Every SKILL.md starts with YAML frontmatter:

```yaml
---
name: my-skill-name
description: Use skill if you are creating OpenClaw skills — SKILL.md format, metadata gating, and ClawHub publishing.
---
```

Required fields: `name`, `description`.

For the full field reference and optional fields, read `references/skill-format-spec.md`.

### 4. Write the description

The description is the most important field. It determines auto-invocation.

**Formula:** `Use skill if you are [action] and need [outcome] [optional: including/before/after what]. Trigger phrases include "phrase1", "phrase2".`

Guidelines:
- Include 3-5 trigger phrases users would naturally say
- Include technology or product names
- Add negative triggers if scope is broad ("Do NOT use for...")
- Stay under 1024 characters
- No `<` or `>` characters

### 5. Write the body

The body contains workflow instructions the agent follows when the skill is invoked. Structure it with:

- **Decision tree** routing to reference files based on the task
- **Quick start** for the most common use case
- **Key patterns** (2-5 essential patterns with code examples)
- **Common pitfalls** table
- **Reference routing table** mapping every reference file to a "when to read" condition
- **Guardrails** (do not... rules)

Keep the body under 500 lines. Move tutorials, long examples, and detailed specs to `references/`.

### 6. Add metadata gating (if needed)

If your skill requires specific binaries, environment variables, or config keys, add the `metadata` field. Read `references/metadata-gating.md` for the complete guide.

```yaml
metadata: {"openclaw": {"requires": {"bins": ["node"], "env": ["API_KEY"], "config": ["settings.json"]}, "primaryEnv": "API_KEY"}}
```

### 7. Organize references

Move detailed content to `references/` using progressive disclosure. Read `references/reference-organization.md` for sizing, naming, and structure guidelines.

### 8. Test the skill

Read `references/testing-skills.md` for the full testing methodology. At minimum:

1. **Install the skill** to the appropriate location
2. **Run 5+ trigger tests** (should-trigger and should-NOT-trigger)
3. **Run 1+ functional test** of the primary workflow end-to-end
4. **Ask the agent** "When would you use [skill-name]?" and verify the answer

### 9. Publish (optional)

Read `references/clawhub-publishing.md` for the ClawHub publishing workflow and checklist.

## Skill locations and precedence

OpenClaw discovers skills from multiple locations with this precedence:

| Priority | Location | Scope | Use case |
|---|---|---|---|
| 1 (highest) | `project/skills/` | Workspace | Project-specific skills |
| 2 | `~/.openclaw/skills/` | Personal | User-wide personal skills |
| 3 | Bundled (npm) | Global | Official skills shipped with OpenClaw |
| 4 | Extra dirs | Configurable | Organization-managed skill directories |

When names conflict, higher-priority locations win. The skills watcher provides hot-reload with configurable debounce.

## Token budget awareness

Skills consume context at three levels:

| Level | When loaded | Cost | Contains |
|---|---|---|---|
| Discovery | Session start, always | ~195 chars base + 97 chars/skill + field lengths | name + description only |
| Activation | On trigger match | Up to ~5K tokens | Full SKILL.md body |
| Deep reference | On explicit Read | Variable, unlimited | reference files |

Implication: keep the description dense with trigger phrases (Level 1), the body focused on routing and decisions (Level 2), and reference material in separate files (Level 3).

## Common pitfalls

| Pitfall | What goes wrong | Fix |
|---|---|---|
| Blank line before `---` | Frontmatter silently fails to parse | Ensure `---` is on line 1 |
| Angle brackets in description | Can inject agent instructions | Remove all `<` and `>` |
| Multi-line metadata YAML | OpenClaw expects single-line JSON | Use inline JSON format |
| SKILL.md over 500 lines | Excessive token consumption on every invocation | Move detail to references/ |
| Orphaned reference files | Agent never loads the content | Add routing in SKILL.md |
| Vague description | Skill never auto-triggers | Add trigger phrases, use the formula |
| Name contains "claude" | Rejected by the system | Use a different name |
| Missing `name` field | Falls back to directory name (unreliable) | Always set `name` explicitly |
| Nested metadata YAML | Parse error, gating ignored | Use single-line JSON: `metadata: {"openclaw": {...}}` |
| Testing without installing | False positive trigger results | Install to `~/.openclaw/skills/` first |

## Reference routing table

| File | Read when |
|---|---|
| `references/skill-format-spec.md` | Writing frontmatter, checking field constraints, understanding optional fields like allowed-tools, model, context, hooks |
| `references/metadata-gating.md` | Adding environment requirements (bins, env vars, config), writing installer specs, configuring sandbox dependencies |
| `references/reference-organization.md` | Organizing reference files, choosing flat vs. nested structure, sizing files, naming conventions, routing verification |
| `references/testing-skills.md` | Planning trigger tests, running functional tests, debugging trigger failures, measuring skill quality |
| `references/clawhub-publishing.md` | Publishing to ClawHub, preparing a skill for distribution, versioning, community standards |

## Guardrails

- Do not write SKILL.md without frontmatter starting on line 1.
- Do not use `<` or `>` anywhere in frontmatter values.
- Do not use "claude" or "anthropic" in the skill name.
- Do not leave reference files unrouted from SKILL.md.
- Do not put detailed tutorials or long examples in the SKILL.md body.
- Do not use multi-line YAML for the metadata field.
- Do not skip trigger testing before deploying a skill.
- Do not assume a skill triggers correctly without installing it first.

## Final checks

Before declaring a skill complete:

- [ ] `name` in frontmatter matches directory name exactly
- [ ] `name` does not contain "claude" or "anthropic"
- [ ] Description follows "Use skill if you are..." formula
- [ ] Description is under 1024 characters with no `<` or `>`
- [ ] SKILL.md body is under 500 lines
- [ ] Every file in `references/` is routed from SKILL.md
- [ ] Metadata field (if present) uses single-line JSON
- [ ] At least 5 trigger tests run (should-trigger and should-NOT-trigger)
- [ ] Primary workflow completes without error in at least one functional test
- [ ] Routing verification passes:

```bash
for f in $(find references -name '*.md' -type f); do
  grep -q "$(basename $f)" SKILL.md || echo "ORPHAN: $f"
done
```
