# Naming Standard

This repo is a **single skills pack**. Every skill should look and behave like it belongs to the same family.

## Canonical Rules

### 1) Directory name
- Use short, stable, install-path-friendly `kebab-case`
- Prefer the name users would actually type in an install command
- Avoid suffixes like `-guide`, `-migrate`, `-v2`, or `-final` unless they are part of the permanent public name

### 2) `SKILL.md` frontmatter `name`
- Must exactly match the directory name
- No aliases
- No legacy names

### 3) README label
- Must exactly match the directory name and frontmatter `name`
- If the displayed name differs from the install path, the repo becomes harder to scan and trust

### 4) Cross-skill references
- Always use canonical repo-local names
- Example: use `design-soul-saas`, not an older or invented sibling name

### 5) Description standard
Every skill description is canonical metadata, not body copy.

Required format:
- start with `Use skill if`
- 30 words or fewer
- describe when the skill should trigger
- use concrete user intent, tools, file patterns, or workflows when helpful
- stay specific enough to avoid overlap with nearby skills
- do not mention references, packaging, evals, or long procedural detail

Good:
- `Use skill if you need direct MCP CLI commands to inspect servers, call tools, or debug transport and argument issues.`
- `Use skill if you are rebuilding saved HTML snapshots into grounded Next.js pages with self-hosted assets and extracted styles.`

Weak:
- `Best MCP skill ever.`
- `Research guide.`
- `Mandatory for all work.`
- `Includes lots of references and examples for everything.`

## Naming Anti-Patterns

Avoid these across directory names, frontmatter names, and README labels:
- `-guide`
- `-migrate`
- stale old product names
- different names for the same skill in different places
- repo-only nicknames that do not match install paths

## Preferred Formula

### Review / setup skills
- `<tool>-config`
- `<tool>-review-init`

Examples:
- `greptile-config`
- `devin-review-init`
- `copilot-review-init`

### Tooling / framework skills
- `<product>-cli`
- `<product>-devtools`
- `<product>-builder`

Examples:
- `mcp-cli`
- `playwright-cli`
- `tauri-devtools`
- `mcp-apps-builder`

### Method / workflow skills
- Use the clearest permanent noun phrase

Examples:
- `planning`
- `research-powerpack`

## Migration Rule

For published skills, prefer this order:
1. Keep the directory name stable if it is already a good public install path
2. Normalize frontmatter `name`
3. Normalize README labels
4. Normalize all cross-skill references
5. Rename directories only when the current public name is clearly wrong or harmful

## Current Canonical Skill Names

- `copilot-review-init`
- `design-soul-saas`
- `devin-review-init`
- `greptile-config`
- `mcp-apps-builder`
- `mcp-cli`
- `mcp-server-tester`
- `mcp-use-code-review`
- `planning`
- `playwright-cli`
- `research-powerpack`
- `skill-builder`
- `snapshot-to-nextjs`
- `supastarter`
- `tauri-devtools`
- `typescript`
