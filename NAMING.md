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
- start with `Use skill if you are`
- 30 words or fewer
- describe when the skill should trigger
- use concrete user intent, tools, file patterns, or workflows when helpful
- stay specific enough to avoid overlap with nearby skills
- do not mention references, packaging, evals, or long procedural detail

Good:
- `Use skill if you are setting up GitHub Copilot review behavior with copilot-instructions.md or scoped *.instructions.md files for repo-specific pull request review.`
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

Prefer action-first canonical names when they make install paths clearer.

### Build skills
- `build-<thing>`
- Use for creation, authoring, scaffolding, or extension workflows

Examples:
- `build-mcp-sdk-server`
- `build-mcp-use-apps`
- `build-supastarter-app`
- `build-skills`

### Test skills
- `test-<thing>`
- Use for validation, debugging, protocol checks, or verification workflows

Examples:
- `test-mcp-server`
- `test-mcp-by-cli`

### Init skills
- `init-<thing>`
- Use for first-run setup that generates repo files or review configuration

Examples:
- `init-greptile-review`
- `init-devin-review`

### Debug skills
- `debug-<thing>`
- Use when the primary job is inspection, diagnosis, or live troubleshooting

Examples:
- `debug-tauri-devtools`

### Develop / Plan skills
- `develop-<thing>` for language or implementation guidance
- `plan-<thing>` for structured decision-making workflows

Examples:
- `develop-typescript`
- `plan-work`

### Keep established product names when they are already the clearest public path

Examples:
- `playwright-cli`
- `research-powerpack`
- `snapshot-to-nextjs`
- `mcp-use-code-review`
- `copilot-review-init`

## Migration Rule

For published skills, prefer this order:
1. Keep the directory name stable if it is already a good public install path
2. Normalize frontmatter `name`
3. Normalize README labels
4. Normalize all cross-skill references
5. Rename directories only when the current public name is clearly wrong or harmful

## Current Canonical Skill Names

- `build-mcp-sdk-server`
- `build-mcp-use-apps`
- `build-skills`
- `build-supastarter-app`
- `copilot-review-init`
- `debug-tauri-devtools`
- `design-soul-saas`
- `develop-typescript`
- `init-devin-review`
- `init-greptile-review`
- `mcp-use-code-review`
- `plan-work`
- `playwright-cli`
- `research-powerpack`
- `snapshot-to-nextjs`
- `test-mcp-by-cli`
- `test-mcp-server`
