# Troubleshooting

Diagnosis and resolution for the most common skill problems, organized by symptom.

## Problem 1: Skill won't upload

### Error: "Could not find SKILL.md in uploaded folder"

**Cause**: File not named exactly `SKILL.md` (case-sensitive).

**Fix**:
```bash
# Check the exact filename
ls -la | grep -i skill

# Must show exactly SKILL.md — not:
# skill.md ❌
# SKILL.MD ❌
# Skill.md ❌
```

Rename to exactly `SKILL.md` if needed.

### Error: "Invalid frontmatter"

**Cause**: YAML formatting issue.

**Common mistakes**:

```yaml
# Wrong — missing delimiters
name: my-skill
description: Does things

# Wrong — unclosed quotes
---
name: my-skill
description: "Does things
---

# Wrong — tabs instead of spaces
---
name:	my-skill
description:	Does things
---

# Correct
---
name: my-skill
description: Does things.
---
```

**Diagnosis checklist**:
- [ ] `---` on line 1 (no blank lines before it)
- [ ] Closing `---` after all fields
- [ ] No tabs (use spaces only)
- [ ] Strings with colons are quoted: `description: "Note: this needs quotes"`
- [ ] Multi-line strings use proper YAML syntax

### Error: "Invalid skill name"

**Cause**: Name contains spaces, capitals, or special characters.

```yaml
# Wrong
name: My Cool Skill
name: my_cool_skill
name: MyCoolSkill

# Correct
name: my-cool-skill
```

**Rules**: kebab-case, lowercase, letters-numbers-hyphens only, no leading/trailing/consecutive hyphens, max 64 characters.

### Error: "Forbidden skill name"

**Cause**: Name contains "claude" or "anthropic" (reserved by Anthropic).

```yaml
# Wrong
name: claude-helper
name: anthropic-tools

# Correct
name: ai-helper
name: agent-tools
```

## Problem 2: Skill doesn't trigger

### Symptom: Skill never loads automatically

**Root cause**: Description is too vague or missing trigger phrases.

**Quick diagnosis**: Ask Claude:
```
"When would you use the [skill-name] skill?"
```

Claude quotes the description back. If the answer doesn't match your intended use cases, the description needs work.

**Common description problems**:

| Problem | Example | Fix |
|---|---|---|
| Too generic | "Helps with projects" | Add specific actions and tools |
| No trigger phrases | "Creates documentation" | Add user-natural language |
| Missing technology names | "Builds apps" | Add framework/tool names |
| No "when to use" | "Processes CSV files" | Add "Use when..." clause |

**Fix template**:
```yaml
description: [What it does] for [specific technology/domain].
  [Key capabilities]. Use when user [trigger phrase 1],
  [trigger phrase 2], or [trigger phrase 3].
```

### Symptom: Triggers on direct `/name` only

**Root cause**: Description doesn't contain the words users naturally say.

**Fix**: List 5 ways a user would ask for this task. Extract keywords. Add them to the description.

## Problem 3: Skill triggers too often

### Symptom: Skill loads for unrelated queries

**Solution 1 — Add negative triggers**:
```yaml
description: Advanced data analysis for CSV files. Use for statistical
  modeling, regression, clustering. Do NOT use for simple data
  exploration (use data-viz skill instead).
```

**Solution 2 — Be more specific**:
```yaml
# Too broad
description: Processes documents.

# Specific
description: Processes PDF legal documents for contract review.
```

**Solution 3 — Clarify scope**:
```yaml
description: PayFlow payment processing for e-commerce. Use specifically
  for online payment workflows, not for general financial queries.
```

### Symptom: Conflicts with another skill

Both skills trigger on similar queries.

**Fix**: Differentiate descriptions and add mutual negative triggers:

```yaml
# Skill A
description: Statistical analysis for CSV. Do NOT use for visualization
  (use data-viz instead).

# Skill B (data-viz)
description: Data visualization and charting. Do NOT use for statistical
  modeling (use data-analysis instead).
```

## Problem 4: MCP connection issues

### Symptom: Skill loads but MCP calls fail

**Diagnosis checklist**:

1. **Verify MCP is connected**
   - Claude.ai: Settings > Extensions > [Service] → should show "Connected"
   - Claude Code: Check MCP server configuration

2. **Test MCP independently**
   ```
   "Use [Service] MCP to fetch my projects"
   ```
   If this fails, the issue is the MCP connection, not the skill.

3. **Check authentication**
   - API keys valid and not expired
   - Proper permissions/scopes granted
   - OAuth tokens refreshed

4. **Verify tool names**
   - Skill references correct MCP tool names (case-sensitive)
   - Check MCP server documentation for current tool names
   - Tools may have been renamed in updates

### Symptom: Intermittent MCP failures

**Common causes**:

| Cause | Fix |
|---|---|
| Rate limiting | Add delays between bulk operations |
| Token expiry | Add token refresh check before workflows |
| Network timeouts | Add retry logic with backoff |
| Pagination needed | Add pagination handling for large result sets |

## Problem 5: Instructions not followed

### Symptom: Claude ignores parts of the instructions

**Cause 1 — Instructions too verbose**

SKILL.md over 500 lines overwhelms the context. The agent prioritizes recent and prominent instructions.

**Fix**: Move detailed content to `references/`. Keep SKILL.md to routing + essential patterns.

**Cause 2 — Critical instructions buried**

Instructions at the bottom of a long file get less attention.

**Fix**: Put critical instructions at the top. Use `## CRITICAL` or `## Important` headers.

**Cause 3 — Ambiguous language**

```markdown
# Bad — ambiguous
Make sure to validate things properly.

# Good — specific
CRITICAL: Before calling create_project, verify:
- Project name is non-empty
- At least one team member assigned
- Start date is not in the past
```

**Cause 4 — Model laziness on long workflows**

For long workflows, the model may skip steps it considers low-value.

**Fix options**:

| Option | When to use |
|---|---|
| Add "Do not skip any steps" | Simple reminder |
| Use validation scripts | Deterministic checks |
| Break into smaller sub-workflows | Complex multi-step processes |
| Add "Quality > speed" note | When thoroughness matters |

**Advanced fix**: Bundle a validation script that checks outputs programmatically. Code is deterministic; language instructions are not.

```markdown
After generating the report, run:
`python scripts/validate_report.py --input output.md`

This checks: section count, formatting, data completeness.
```

## Problem 6: Large context issues

### Symptom: Skill feels slow or responses degrade

**Cause 1 — SKILL.md too large**

```
Before: SKILL.md (1200 lines) — all loaded at once
After:  SKILL.md (250 lines) + references/ (5 files loaded on demand)
```

**Cause 2 — Too many skills enabled**

More than 20-50 skills enabled simultaneously can degrade performance. Each skill's description (~100 tokens) is always in context.

**Fix**: Disable skills not needed for the current task. Consider grouping related skills into packs.

**Cause 3 — No progressive disclosure**

All content in SKILL.md means everything loads at Level 2, even if only 20% is relevant.

**Fix**: Keep SKILL.md to routing + quick start. Move detailed guides to `references/` (Level 3 — loaded only when needed).

## Diagnostic flowchart

```
Skill problem?
│
├── Won't upload?
│   ├── Check filename: exactly SKILL.md
│   ├── Check frontmatter: --- delimiters, valid YAML
│   └── Check name: kebab-case, no reserved words
│
├── Doesn't trigger?
│   ├── Ask Claude when it would use the skill
│   ├── Add trigger phrases to description
│   └── Add technology keywords
│
├── Triggers too often?
│   ├── Add negative triggers
│   ├── Narrow scope in description
│   └── Add mutual exclusions with other skills
│
├── MCP fails?
│   ├── Test MCP independently first
│   ├── Check auth and tool names
│   └── Add error handling to skill
│
├── Instructions ignored?
│   ├── Move content to references (reduce SKILL.md size)
│   ├── Put critical instructions at top
│   ├── Replace ambiguous language with specifics
│   └── Use validation scripts for deterministic checks
│
└── Performance degraded?
    ├── Reduce SKILL.md size
    ├── Disable unused skills
    └── Use progressive disclosure (references/)
```


---

> **Steering tip:** When diagnosing trigger issues, distinguish between "skill not loaded" (installation problem) and "skill loaded but didn't activate" (description problem). For new skills, verify installation first — see `references/steering/derailment-lessons.md` Trap 5.
