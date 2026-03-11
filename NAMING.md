# Naming Standard

This repo is a **single skills pack**. Every skill name starts with a verb prefix that signals its primary function.

## The Rule

Every skill directory, `SKILL.md` frontmatter `name`, and README label must:
- Start with a verb prefix from the table below
- Use `kebab-case`
- Be short, stable, and install-path-friendly
- Match exactly across directory name, frontmatter `name`, and README label

## Verb Prefixes

| Prefix | When to use | Examples |
|---|---|---|
| `build-` | Creation, scaffolding, authoring, extension | `build-copilot-sdk-app`, `build-daisyui-mcp`, `build-skills`, `build-supastarter-app` |
| `convert-` | Format transformation, migration, rebuild | `convert-snapshot-nextjs` |
| `debug-` | Inspection, diagnosis, live troubleshooting | `debug-tauri-devtools` |
| `develop-` | Language standards, implementation patterns, type systems | `develop-typescript` |
| `extract-` | Design extraction, data forensics, visual system documentation | `extract-saas-design` |
| `init-` | First-run setup, config generation, review platform onboarding | `init-copilot-review`, `init-devin-review`, `init-greptile-review` |
| `plan-` | Structured decision-making, prioritization, root-cause framing | `plan-work` |
| `publish-` | CI/CD, package publishing, release automation | `publish-npm-package` |
| `review-` | Code review execution, pattern checking, anti-pattern detection | `review-pr` |
| `run-` | Browser automation, playwright automation, research workflows, CLI-driven execution | `run-agent-browser`, `run-playwright`, `run-research` |

## Canonical Rules

### 1) Directory name
- Must start with a verb prefix from the table above
- Use short, stable, install-path-friendly `kebab-case`
- Prefer the name users would actually type in an install command
- Avoid suffixes like `-guide`, `-migrate`, `-v2`, or `-final`

### 2) `SKILL.md` frontmatter `name`
- Must exactly match the directory name
- No aliases, no legacy names

### 3) README label
- Must exactly match the directory name and frontmatter `name`
- If the displayed name differs from the install path, the repo becomes harder to scan and trust

### 4) Cross-skill references
- Always use canonical repo-local names

### 5) Description standard
Every skill description is canonical metadata, not body copy.

Required format:
- Start with `Use skill if you are`
- 30 words or fewer
- Describe when the skill should trigger, not what the body contains
- Use concrete user intent, tools, file patterns, or workflows when helpful
- Stay specific enough to avoid overlap with nearby skills

Good:
- `Use skill if you are setting up GitHub Copilot review behavior with copilot-instructions.md or scoped *.instructions.md files for repo-specific pull request review.`
- `Use skill if you are converting saved HTML snapshots into buildable Next.js pages with self-hosted assets and extracted styles.`

Weak:
- `Best MCP skill ever.`
- `Research guide.`
- `Mandatory for all work.`

## Naming Anti-Patterns

- Names that don't start with a verb prefix
- `-guide`, `-migrate`, `-v2` suffixes
- Marketing-heavy names (e.g., "soul", "powerpack" as primary identifiers)
- Different names in different places (directory vs frontmatter vs README)
- Noun-first names (e.g., `agent-browser` instead of `run-agent-browser`)

## Adding a New Verb Prefix

If none of the existing prefixes fit:
1. Check whether an existing prefix can stretch to cover the use case
2. If not, propose the new prefix in a PR with at least one concrete skill example
3. Keep the prefix to a single common English verb

## Migration Rule

When renaming a published skill:
1. Rename the directory
2. Update frontmatter `name` to match
3. Update frontmatter `description` to current standard
4. Update README label and install commands
5. Update NAMING.md canonical list
6. Update all cross-skill references

## Current Canonical Skill Names

- `build-copilot-sdk-app`
- `build-daisyui-mcp`
- `build-skills`
- `build-supastarter-app`
- `convert-snapshot-nextjs`
- `debug-tauri-devtools`
- `develop-typescript`
- `extract-saas-design`
- `init-agent-config`
- `init-copilot-review`
- `init-devin-review`
- `init-greptile-review`
- `plan-work`
- `publish-npm-package`
- `review-pr`
- `run-agent-browser`
- `run-playwright`
- `run-research`
