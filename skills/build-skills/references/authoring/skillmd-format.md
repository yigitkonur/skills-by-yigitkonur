# SKILL.md Format Specification

Complete reference for the SKILL.md file format used by AI coding agents.

## File requirements

- File must be named exactly `SKILL.md` (case-sensitive)
- Must be placed inside a named directory (the directory name becomes the skill identifier)
- Frontmatter must start on line 1

## Frontmatter

YAML frontmatter is enclosed between `---` delimiters. It configures how the skill is discovered, loaded, and executed.

```yaml
---
name: my-skill-name
description: Use skill if you are doing X and need Y before Z.
---
```

### Field reference

| Field | Required | Type | Constraints | Purpose |
|---|---|---|---|---|
| `name` | Recommended | string | Lowercase letters, numbers, hyphens only. Max 64 chars. No leading/trailing hyphen. No consecutive hyphens. | Display name and `/slash-command` identifier. Defaults to directory name if omitted. |
| `description` | Recommended | string | Max 1024 chars. Avoid `<` and `>` (can inject unintended instructions). | Primary signal for auto-invocation. Must state **what** the skill does AND **when** to use it. |
| `allowed-tools` | No | string (comma-separated) | Tool identifiers like `Read, Grep, Glob` | Pre-approves specific tools without per-use confirmation. Supports wildcards. |
| `disable-model-invocation` | No | boolean | `true` or `false` | When `true`, prevents auto-loading. Only manual `/name` invocation works. Use for side-effect-heavy skills. |
| `user-invocable` | No | boolean | `true` or `false` | When `false`, hides from the `/` menu. For background-knowledge skills only. |
| `model` | No | string | Model identifier or `inherit` | Override the model when skill is active. Defaults to session model. |
| `context` | No | string | `fork` | Runs the skill in an isolated sub-agent context. |
| `agent` | No | string | Agent type like `Explore`, `Plan` | Sub-agent type when `context: fork` is set. |
| `argument-hint` | No | string | e.g., `[issue-number]` | Autocomplete hint showing expected arguments. |
| `mode` | No | boolean | `true` | Marks skill as a "mode command" in a separate UI section. |
| `version` | No | string | SemVer e.g., `1.0.0` | Human-readable version for tracking. |
| `hooks` | No | map | Hook definitions | Hooks scoped to the skill's lifecycle. |
| `license` | No | string | e.g., `MIT`, `Apache-2.0` | License for open-source distribution. Common: MIT, Apache-2.0. |
| `compatibility` | No | string | 1-500 characters | Environment requirements: intended product, required system packages, network access needs. |
| `metadata` | No | map | Custom key-value pairs | Suggested keys: `author`, `version`, `mcp-server`, `category`, `tags`, `documentation`, `support`. |

### Frontmatter rules

1. Must start on line 1 of the file — no blank lines before `---`
2. Any YAML syntax error silently prevents loading
3. Avoid XML angle brackets (`<`, `>`) — they can inject instructions
4. Unknown fields are ignored by the loader
5. If `name` is omitted, the parent directory name is used
6. If `description` is omitted, the first paragraph of the markdown body is used
7. Skills named with "claude" or "anthropic" prefix are reserved by Anthropic and forbidden

## Body structure

The markdown body after frontmatter contains the instructions the agent follows when the skill is invoked.

### Recommended sections

```markdown
# Skill Title

Brief one-line purpose statement.

## Decision tree

Route the agent to the correct reference file based on the task.

## Quick start

Minimal steps to accomplish the most common use case.

## Key patterns

2-5 essential patterns with code examples.

## Common pitfalls

| Pitfall | Fix |
|---------|-----|

## Minimal reading sets

### "I need to do X"
- `references/relevant-file.md`

## Reference files

| File | When to read |
|---|---|

## Guardrails

- Do not...
- Do not...
```

### Body guidelines

| Guideline | Rationale |
|---|---|
| Keep under 500 lines | Larger files consume excessive context budget |
| Use imperative language ("Run...", "Write...") | Clearer agent instructions than passive voice |
| Reference files via relative paths | Portability across environments |
| Use `{baseDir}` for script references | Agent resolves to the skill's directory |
| Include 1-3 inline examples | Demonstrates expected behavior without bloat |
| Move large docs to `references/` | Progressive disclosure — loaded only when needed |

## Three-level loading system

Understanding how agents load skills is critical for sizing decisions.

### Level 1 — Discovery (always loaded)

At session start, the agent reads every skill's `name` + `description` from frontmatter.

- Cost: ~100 tokens per skill
- Purpose: Decides which skills exist and when to invoke them
- Implication: `description` must contain trigger phrases the user would naturally say

### Level 2 — Activation (on demand)

When a skill matches (auto or manual `/name`), the full SKILL.md body is loaded.

- Cost: Up to ~5,000 tokens
- Purpose: Provides the workflow instructions
- Implication: Keep the body focused — offload reference material

### Level 3 — Deep reference (on demand)

When SKILL.md references external files (via `Read` or explicit links), those files are loaded.

- Cost: Variable, effectively unlimited
- Purpose: Detailed guides, specs, examples, large code samples
- Implication: Only loaded when the skill explicitly requests them

```
Session start
  └─ Level 1: Load name + description (~100 tokens/skill)
       └─ Trigger match?
            └─ Level 2: Load full SKILL.md body (≤5K tokens)
                 └─ Reference needed?
                      └─ Level 3: Load references/ files (unlimited)
```

## Agent-specific locations

Skills are discovered in platform-specific directories:

| Agent | Project scope | Personal scope |
|---|---|---|
| Claude Code | `.claude/skills/<name>/` | `~/.claude/skills/<name>/` |
| Cursor | `.cursor/skills/<name>/` | `~/.cursor/skills/<name>/` |
| Codex | `.codex/skills/<name>/` | `~/.codex/skills/<name>/` |
| Generic | `skills/<name>/` | `~/.skills/<name>/` |

Project-scope skills take precedence over personal-scope when names conflict.

## Writing effective descriptions

The `description` field is the most important piece of frontmatter. It determines whether the agent auto-invokes the skill.

### Formula

```
Use skill if you are [doing what] and need [what outcome] [optional: before/after what].
```

### Good descriptions

```yaml
description: Use skill if you are building TypeScript applications with the GitHub Copilot SDK (@github/copilot-sdk), including sessions, tools, streaming, hooks, custom agents, or BYOK.
```

```yaml
description: Use skill if you are creating or redesigning a Claude skill and need workspace-first evidence, remote skill research, and comparison before drafting.
```

```yaml
description: Use skill if you are reviewing a GitHub pull request with a systematic, evidence-based workflow.
```

```yaml
description: Manages Linear project workflows including sprint planning,
  task creation, and status tracking. Use when user mentions "sprint",
  "Linear tasks", "project planning", or asks to "create tickets".
```

### Bad descriptions

```yaml
description: Helps with code.
# Too vague — no trigger phrases, no specificity
```

```yaml
description: A skill for TypeScript.
# No "when" — doesn't tell the agent what task this serves
```

```yaml
description: Use this skill to <generate> React components with proper <typing>.
# Angle brackets can inject instructions into the agent
```

```yaml
description: Implements the Project entity model with hierarchical relationships.
# Too technical — no user-natural language, no trigger phrases
```

## Validation checklist

Before shipping a skill, verify:

- [ ] File is named `SKILL.md` (exact case)
- [ ] Frontmatter starts on line 1
- [ ] `name` follows naming rules (lowercase, hyphens, ≤64 chars)
- [ ] `name` does not contain "claude" or "anthropic" (reserved)
- [ ] `description` includes what + when with trigger phrases
- [ ] No `<` or `>` in frontmatter values
- [ ] Body is under 500 lines
- [ ] All referenced files actually exist
- [ ] Every file in `references/` is routed from SKILL.md
- [ ] `allowed-tools` is minimal (not over-broad)
- [ ] Side-effect skills use `disable-model-invocation: true`
- [ ] `metadata` includes author and version for published skills

## Metadata field reference

The `metadata` field accepts any custom key-value pairs. Suggested keys:

```yaml
metadata:
  author: Company Name
  version: 1.0.0
  mcp-server: server-name
  category: productivity
  tags: [project-management, automation]
  documentation: https://example.com/docs
  support: support@example.com
```

## Complete minimal example

```yaml
---
name: create-component
description: Use skill if you are creating a new React component and need consistent file structure, typing, and test scaffolding.
allowed-tools: Read, Write, Glob
---

# Create Component

Generate a new React component with TypeScript types and test file.

## Steps

1. Ask for the component name and location
2. Create the component file with proper exports
3. Create the test file with a basic render test
4. Update the barrel export if one exists

## Output format

Each component gets three files:
- `ComponentName.tsx` — the component
- `ComponentName.test.tsx` — the test
- `index.ts` — barrel export (update if exists)

## Example

For a component named `UserCard` in `src/components/`:

```tsx
// src/components/UserCard/UserCard.tsx
export interface UserCardProps {
  name: string;
  email: string;
}

export function UserCard({ name, email }: UserCardProps) {
  return (
    <div className="user-card">
      <h3>{name}</h3>
      <p>{email}</p>
    </div>
  );
}
```
