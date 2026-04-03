# Plugin Skills Bundling

Plugins can bundle skill directories that are automatically loaded when the plugin is enabled. This allows plugins to ship domain-specific prompt workflows alongside their tools, channels, and providers.

## How bundled skills work

When a plugin declares `"skills": ["skills"]` in its manifest, OpenClaw:

1. Resolves the path relative to the plugin root
2. Scans for subdirectories containing `SKILL.md`
3. Loads each discovered skill into the active skill registry
4. Skills become available to users as if they were standalone skills

**The skills are only loaded when the plugin is enabled** (config gating passed). If the plugin is disabled, its skills are also unavailable.

## Directory structure

```
my-plugin/
+-- openclaw.plugin.json
+-- package.json
+-- src/
|   +-- index.ts
|   +-- tools/
+-- skills/                      # Declared in manifest: "skills": ["skills"]
    +-- analyze-data/            # Each subdirectory is a skill
    |   +-- SKILL.md
    |   +-- references/
    |       +-- analysis-guide.md
    +-- generate-report/
        +-- SKILL.md
        +-- references/
            +-- report-format.md
            +-- templates.md
```

## Manifest configuration

The `skills` field is an array of relative paths to directories containing skills:

```json
{
  "skills": ["skills"]
}
```

You can declare multiple skill directories:

```json
{
  "skills": ["skills/core", "skills/advanced"]
}
```

Each path is resolved relative to the plugin root (where `openclaw.plugin.json` lives).

## Writing bundled skills

Bundled skills follow the same format as standalone skills:

### SKILL.md requirements

```markdown
---
name: analyze-data
description: Use skill if you are analyzing structured data...
---

# Analyze Data

[Skill content follows standard SKILL.md format]
```

**Rules:**

- Frontmatter `name` must match the directory name
- Description follows the standard formula ("Use skill if you are...")
- No angle brackets in frontmatter
- Do not use "claude" or "anthropic" in the skill name
- Reference files go in `references/` subdirectory
- Every reference file must be routed from SKILL.md

### Referencing plugin tools from skills

Bundled skills often guide the user through workflows that use the plugin's tools. Reference tools by their registered name:

```markdown
## Workflow

1. Use the `search_documents` tool to find relevant data
2. Use the `analyze_results` tool to process findings
3. Present a summary to the user
```

Do not hard-code tool behavior in the skill — describe when and why to use the tool, not how the tool works internally.

## Skills and tool profiles interaction

Bundled skills remain loaded even if the tools they reference are denied by the active profile or allow/deny lists. The skill's text is still available, but the tool calls it recommends will fail.

**Handle this in skill design:**

```markdown
## Prerequisites

This skill requires the following tools to be available:
- `search_documents` (group:memory)
- `analyze_results` (group:runtime)

If these tools are not available under the current profile, the workflow
cannot complete. Check the active tool profile and ensure the required
groups are enabled.
```

## When to bundle skills vs. keep them standalone

| Bundle inside plugin when... | Keep standalone when... |
|---|---|
| Skill requires the plugin's tools to function | Skill works without any specific plugin |
| Skill and tools are versioned together | Skill has independent release cycle |
| Skill is meaningless without the plugin context | Skill is useful across different tool sets |
| Distribution: users get tools + workflows in one install | Distribution: skill is shared across teams with different plugins |

## Publishing considerations

When publishing a plugin with bundled skills to npm:

1. Include the `skills/` directory in `package.json` `files`:

```json
{
  "files": [
    "dist/",
    "openclaw.plugin.json",
    "skills/"
  ]
}
```

2. Verify skills are included in the published package:

```bash
npm pack --dry-run
# Check that skills/ directories appear in the file list
```

3. Test the installed package:

```bash
npm install ./my-plugin-1.0.0.tgz
# Verify skills load in OpenClaw
```

## Common mistakes

| Mistake | Impact | Fix |
|---|---|---|
| Skills directory not in `package.json` `files` | Skills missing from published package | Add `"skills/"` to `files` array |
| Absolute path in manifest `skills` field | Breaks on other machines | Use relative path from plugin root |
| Skill `name` does not match directory name | Skill fails to load | Align `name` in frontmatter with directory name |
| Skill assumes tools are always available | Workflow fails under restricted profiles | Document required tools and groups |
| No reference routing in bundled SKILL.md | References are orphaned | Route every reference file from SKILL.md |
| Bundling skills that work without the plugin | Unnecessary coupling | Keep those as standalone skills |
