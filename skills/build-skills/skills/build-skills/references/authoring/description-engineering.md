# Description Engineering

The description field is the single most impactful part of a skill. It determines whether Claude auto-invokes the skill, when it fires, and when it stays silent.

## Why descriptions matter more than instructions

The description is loaded at Level 1 — always present in Claude's system prompt at ~100 tokens per skill. It is the only thing Claude sees when deciding whether to activate a skill. A perfect body with a weak description means the skill never fires.

## The official formula

From Anthropic's engineering blog: the description must communicate both **what** the skill does and **when** to use it.

```
[What it does] + [When to use it] + [Key capabilities]
```

### Alternative formula for Claude Code skills

```
Use skill if you are [doing what action] and need [what outcome] [optional: before/after/including what].
```

Both formulas work. The first is better for Claude.ai; the second is more precise for Claude Code auto-invocation.

## Trigger phrase engineering

Users do not say "invoke skill X." They say things like "help me plan this sprint" or "set up a new project." Your description must contain the words and phrases users naturally say.

### How to find trigger phrases

1. **List the tasks** the skill handles
2. **Write 5 ways** a user might ask for each task
3. **Extract keywords** that appear across multiple phrasings
4. **Include technology names** users would mention (`Linear`, `Playwright`, `TypeScript`)
5. **Include file types** if relevant (`.fig`, `CSV`, `PDF`)

### Example: building trigger phrases

```
Task: Sprint planning in Linear

User might say:
- "help me plan this sprint"
- "create sprint tasks"
- "set up the next sprint in Linear"
- "Linear sprint planning"
- "organize tasks for the sprint"

Keywords to include: sprint, Linear, tasks, planning, create
```

## Negative triggers

When a skill triggers too broadly, add explicit exclusions to the description.

### When to use negative triggers

- The skill's topic overlaps with another skill
- Generic keywords cause false positives
- Users report the skill loading for unrelated queries

### How to write negative triggers

```yaml
# Without negative trigger — fires on any "data" query
description: Processes data files for analysis.

# With negative trigger — scoped correctly
description: Advanced statistical analysis for CSV files including
  regression, clustering, and hypothesis testing. Use for statistical
  modeling. Do NOT use for simple data exploration or visualization
  (use data-viz skill instead).
```

### Negative trigger patterns

| Pattern | Example |
|---|---|
| Exclude by scope | "Do NOT use for general financial queries" |
| Redirect to other skill | "Use data-viz skill instead for charts" |
| Exclude by file type | "Not for JSON or XML — only CSV and TSV" |
| Exclude by action | "Not for reading or exploring data" |

## Testing your description

### The Claude test

Ask Claude directly:

```
"When would you use the [skill-name] skill?"
```

Claude will quote the description back. If the answer doesn't match your intent, the description needs work.

### The trigger test matrix

Build a test matrix before shipping:

```
Should trigger:
- "Help me set up a new ProjectHub workspace"           ✅
- "I need to create a project in ProjectHub"             ✅
- "Initialize a ProjectHub project for Q4 planning"      ✅
- "set up project" (generic, but relevant)                ✅

Should NOT trigger:
- "What's the weather in San Francisco?"                  ❌
- "Help me write Python code"                             ❌
- "Create a spreadsheet"                                  ❌
- "Tell me about project management theory"               ❌
```

Run at least 5 should-trigger and 5 should-NOT-trigger queries before publishing.

## Description length optimization

The hard limit is 1024 characters. Effective descriptions are typically 100-300 characters.

| Length | Risk |
|---|---|
| Under 50 chars | Too vague — won't trigger reliably |
| 50-150 chars | Adequate for simple skills |
| 150-300 chars | Ideal — specific with trigger phrases |
| 300-500 chars | Acceptable for complex multi-workflow skills |
| 500-1024 chars | Likely too verbose — consider splitting the skill |

## Ranked examples

### Excellent — technology + use cases + trigger phrases

```yaml
description: Use skill if you are building TypeScript applications with the
  GitHub Copilot SDK (@github/copilot-sdk), including sessions, tools,
  streaming, hooks, custom agents, or BYOK.
```

Why: Names the technology, the SDK package, AND lists 6 specific capabilities.

### Excellent — workflow + outcome + methodology

```yaml
description: Use skill if you are reviewing a GitHub pull request with a
  systematic, evidence-based workflow that clusters files, correlates
  existing comments, validates goals, and produces actionable findings.
```

Why: Describes what happens AND how it happens, with trigger phrases embedded.

### Excellent — action + prerequisite + outcome

```yaml
description: Use skill if you are creating or redesigning a Claude skill and
  need workspace-first evidence, remote skill research, and comparison
  before drafting.
```

Why: States the action, prerequisite methodology, and implied outcome.

### Good — MCP enhancement with trigger phrases

```yaml
description: Manages Linear project workflows including sprint planning,
  task creation, and status tracking. Use when user mentions "sprint",
  "Linear tasks", "project planning", or asks to "create tickets".
```

Why: Lists the MCP service AND explicit trigger phrases.

### Good — clear value proposition

```yaml
description: End-to-end customer onboarding workflow for PayFlow. Handles
  account creation, payment setup, and subscription management. Use when
  user says "onboard new customer", "set up subscription", or "create
  PayFlow account".
```

Why: States the complete workflow AND quotes user language.

### Adequate — functional but could be more specific

```yaml
description: Use skill if you are setting up automated npm publishing via
  GitHub Actions.
```

Why: Clear action, but no trigger phrases or specific capabilities listed.

### Poor — too vague, no triggers

```yaml
description: Helps with projects.
```

Why: No action, no outcome, no trigger phrases. Will not auto-invoke reliably.

### Poor — missing user triggers

```yaml
description: Creates sophisticated multi-page documentation systems.
```

Why: Says what it does but not when. No words a user would naturally say.

### Bad — too technical, no user language

```yaml
description: Implements the Project entity model with hierarchical relationships.
```

Why: Implementation language, not user intent language.

### Dangerous — angle brackets inject instructions

```yaml
description: Use skill to <generate> React components with <proper> typing.
```

Why: `<` and `>` can inject instructions into the agent's system prompt.

## Common mistakes ranked by severity

| Severity | Mistake | Fix |
|---|---|---|
| Critical | Angle brackets in description | Remove all `<` and `>` |
| Critical | Missing `---` delimiters | Add `---` on line 1 |
| High | No trigger phrases | Add 3-5 phrases users would say |
| High | Too vague ("helps with code") | State specific action + outcome |
| Medium | No negative triggers on broad topic | Add "Do NOT use for..." |
| Medium | Missing technology keywords | Add tool/framework/file type names |
| Low | Description too long (>500 chars) | Trim to essentials or split skill |
| Low | No file type mentions | Add if skill handles specific formats |

## Description field security

- No `<` or `>` characters (XML injection risk)
- No "claude" or "anthropic" in the skill name (reserved by Anthropic)
- Descriptions appear in the system prompt — treat them as security-sensitive
- YAML safe parsing prevents code execution in frontmatter


---

> Tip: Test your description against both should-trigger and should-NOT-trigger queries before finalizing. A description that triggers too broadly is worse than one that triggers too narrowly.
