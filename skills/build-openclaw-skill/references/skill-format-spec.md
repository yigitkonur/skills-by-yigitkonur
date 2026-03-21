# Skill Format Specification

Complete reference for the SKILL.md file format in the OpenClaw skill system.

## File requirements

- File must be named exactly `SKILL.md` (case-sensitive)
- Must be placed inside a named directory (the directory name becomes the skill identifier)
- Frontmatter must start on line 1 — no blank lines before the opening `---`
- Any YAML syntax error silently prevents loading (no error message)

## Frontmatter fields

### Required fields

| Field | Type | Constraints | Purpose |
|---|---|---|---|
| `name` | string | Lowercase letters, numbers, hyphens. Max 64 chars. No leading/trailing/consecutive hyphens. | Display name and `/slash-command` identifier. Defaults to directory name if omitted. |
| `description` | string | Max 1024 chars. No `<` or `>`. | Primary signal for auto-invocation. Must state what + when + trigger phrases. |

### Optional fields

| Field | Type | Constraints | Purpose |
|---|---|---|---|
| `homepage` | string | Valid URL | Link to documentation or project page |
| `user-invocable` | boolean | `true` / `false` | When `false`, hides from the `/` menu. For background-knowledge skills only. |
| `disable-model-invocation` | boolean | `true` / `false` | When `true`, prevents auto-loading. Only manual `/name` works. Use for side-effect-heavy skills. |
| `command-dispatch` | string | `"tool"` | If set to `"tool"`, the slash command bypasses the model entirely and calls the specified tool directly. |
| `command-tool` | string | Tool identifier | Required if `command-dispatch` is `"tool"`. Specifies which tool handles the command. |
| `command-arg-mode` | string | `"raw"` | For direct dispatch, passes raw user arguments to the tool without parsing. |
| `allowed-tools` | string | Comma-separated tool identifiers | Pre-approves tools without per-use confirmation. Supports wildcards. |
| `model` | string | Model identifier or `inherit` | Override the model when skill is active. |
| `context` | string | `fork` | Runs the skill in an isolated sub-agent context. |
| `agent` | string | Agent type | Sub-agent type when `context: fork` is set. |
| `argument-hint` | string | e.g., `[issue-number]` | Autocomplete hint showing expected arguments. |
| `mode` | boolean | `true` | Marks skill as a "mode command" in a separate UI section. |
| `version` | string | SemVer e.g., `1.0.0` | Human-readable version for tracking. |
| `hooks` | map | Hook definitions | Hooks scoped to the skill's lifecycle. |
| `license` | string | e.g., `MIT`, `Apache-2.0` | License for open-source distribution. |
| `compatibility` | string | 1-500 chars | Environment requirements, intended product, system packages. |
| `metadata` | map | Single-line JSON | Custom key-value pairs for gating and metadata. See `references/metadata-gating.md`. |

### The metadata field

The `metadata` field is special. It must be written as **single-line JSON**, not multi-line YAML. OpenClaw parses it as an inline JSON object.

```yaml
# CORRECT — single-line JSON
metadata: {"openclaw": {"requires": {"bins": ["node", "npm"], "env": ["GITHUB_TOKEN"]}, "primaryEnv": "GITHUB_TOKEN"}}

# WRONG — multi-line YAML (will not parse correctly for gating)
metadata:
  openclaw:
    requires:
      bins:
        - node
```

For full metadata gating documentation, see `references/metadata-gating.md`.

## Frontmatter rules

1. Must start on line 1 — no blank lines, no BOM, no whitespace before `---`
2. Any YAML syntax error silently prevents loading (the skill disappears)
3. Avoid `<` and `>` — they can inject instructions into the agent system prompt
4. Unknown fields are silently ignored by the loader
5. If `name` is omitted, the parent directory name is used (but always set it explicitly)
6. If `description` is omitted, the first paragraph of the body is used (unreliable for triggering)
7. Skill names starting with "claude" or "anthropic" are reserved and forbidden

## Body structure

The markdown body after frontmatter contains the instructions the agent follows on invocation.

### Recommended sections

```markdown
# Skill Title

Brief one-line purpose statement.

## Trigger boundary

When to use / when NOT to use this skill.

## Decision tree

Route the agent to the correct reference file based on the task.

## Workflow

Steps for the primary use case.

## Common pitfalls

| Pitfall | Fix |
|---------|-----|

## Reference routing table

| File | When to read |
|---|---|

## Guardrails

- Do not...

## Final checks

- [ ] Checklist item...
```

### Body guidelines

| Guideline | Rationale |
|---|---|
| Keep under 500 lines | Larger files consume excessive context on every invocation |
| Use imperative language ("Run...", "Write...") | Clearer agent instructions than passive voice |
| Reference files via relative paths | Portability across environments |
| Include 1-3 inline examples | Demonstrates expected behavior without bloat |
| Move large docs to `references/` | Progressive disclosure — loaded only when needed |
| Use tables for structured lookups | Faster agent parsing than prose |
| Include a decision tree | Agents need clear routing to know which reference to load |

## Three-level loading system

Understanding how OpenClaw loads skills is critical for sizing decisions.

### Level 1 — Discovery (always loaded)

At session start, the agent reads every skill's `name` + `description` from frontmatter.

- Cost formula (exact):
  ```
  totalChars = 195 + Σ(97 + len(nameEsc) + len(descEsc) + len(locEsc))
  ```
  XML escaping expands `&` `<` `>` `"` `'` into entities, increasing length. This is why avoiding special characters in name and description matters beyond the injection risk — they inflate discovery cost.
- Purpose: Decides which skills exist and when to invoke them
- Implication: `description` must contain trigger phrases the user would naturally say

### Level 2 — Activation (on demand)

When a skill matches (auto or manual `/name`), the full SKILL.md body is loaded.

- Cost: Up to ~5,000 tokens
- Purpose: Provides the workflow instructions
- Implication: Keep the body focused — offload reference material

### Level 3 — Deep reference (on demand)

When SKILL.md routes to external files (via Read or explicit links), those files are loaded.

- Cost: Variable, effectively unlimited
- Purpose: Detailed guides, specs, examples, large code samples
- Implication: Only loaded when the skill explicitly requests them

## Skill locations

OpenClaw discovers skills from these directories, in precedence order:

| Priority | Location | Scope |
|---|---|---|
| 1 (highest) | `project/skills/` | Workspace (project-specific) |
| 2 | `~/.openclaw/skills/` | Managed / personal |
| 3 | Bundled (npm package) | Global (shipped with OpenClaw) |
| 4 | Extra dirs (configurable) | Organization-managed |

When names conflict, higher-priority locations win.

## Skills watcher

OpenClaw includes a hot-reload watcher for skill directories. When you save changes to a SKILL.md or reference file, the skill is automatically reloaded with configurable debounce. This enables rapid iteration during development.

## Complete minimal example

```yaml
---
name: deploy-staging
description: Use skill if you are deploying the application to the staging environment, running pre-deploy checks, or troubleshooting staging deployments. Trigger phrases include "deploy staging", "staging deploy", "push to staging".
---

# Deploy Staging

Deploy the application to the staging environment with pre-deploy validation.

## Steps

1. Run pre-deploy checks (lint, test, build)
2. Verify staging environment variables are set
3. Execute deployment script
4. Verify deployment health

## Common pitfalls

| Pitfall | Fix |
|---|---|
| Missing env vars | Check `.env.staging` exists |
| Build failures | Run `npm run build` locally first |

## Guardrails

- Do not deploy without passing all pre-deploy checks.
- Do not skip the health check after deployment.
```

## Writing effective descriptions

### The formula

```
Use skill if you are [doing what action] and need [what outcome] [optional: including/before/after what].
Trigger phrases include "phrase1", "phrase2", "phrase3".
```

### Good descriptions

```yaml
description: Use skill if you are building a REST API with OpenClaw's built-in HTTP tools and need endpoint scaffolding, middleware configuration, or error handling patterns. Trigger phrases include "REST API", "HTTP endpoint", "API route", "middleware".
```

```yaml
description: Use skill if you are setting up CI/CD pipelines for an OpenClaw agent project, including GitHub Actions workflows, testing automation, and deployment scripts. Trigger phrases include "CI/CD", "GitHub Actions", "deploy pipeline", "automated testing".
```

### Bad descriptions

```yaml
description: Helps with skills.
# Too vague — no trigger phrases, no specificity
```

```yaml
description: A comprehensive tool for managing all aspects of skill development.
# No "when" — doesn't tell the agent what task this serves
```

## Security: realpath escaping

If a skill folder's resolved realpath escapes the configured root directory (e.g., via symlinks pointing outside the skills root), the skill is silently ignored. This prevents directory traversal attacks where a symlink could cause the loader to read arbitrary files.

## Error conditions

The following conditions cause a skill to be excluded or partially ignored at load time:

| Condition | Result |
|---|---|
| Missing required binary (from `requires.bins`) | Skill excluded at load time |
| In sandbox mode, required binary missing inside container | Skill excluded (binary must exist inside the container) |
| Missing required env var and no `skills.entries` override | Skill excluded |
| Missing required config path | Skill excluded |
| Invalid installer spec (e.g., `download` kind without `url`) | That installer entry is ignored (skill may still load) |
| Skill folder realpath escapes configured root | Skill silently ignored for security |
| YAML syntax error in frontmatter | Skill silently fails to load |

## Validation checklist

Before shipping a skill, verify:

- [ ] File is named `SKILL.md` (exact case)
- [ ] Frontmatter starts on line 1
- [ ] `name` follows rules (lowercase, hyphens, max 64 chars)
- [ ] `name` does not contain "claude" or "anthropic"
- [ ] `description` includes what + when + trigger phrases
- [ ] No `<` or `>` in frontmatter values
- [ ] Body is under 500 lines
- [ ] All referenced files actually exist
- [ ] Every file in `references/` is routed from SKILL.md
- [ ] `metadata` (if present) is single-line JSON
