# Plugins Overview

A plugin is a directory that extends the agent with slash commands (skills) and MCP server tools. Athena loads plugins from paths in your config or via `--plugin`.

## What Plugins Provide

**Skills** — Slash commands defined as `SKILL.md` files with YAML frontmatter. Skills marked `user-invocable: true` appear as commands:

```
/add-e2e-tests <url> <feature>
/analyze-test-codebase [path]
/plan-test-coverage <url> <feature>
```

**MCP Servers** — A `.mcp.json` file in the plugin root exposes tools to the agent. Athena merges all plugin MCP configs into a single temp file passed to the harness at startup.

## Directory Structure

```
my-plugin/
  .claude-plugin/
    plugin.json          # required — manifest
  skills/
    add-tests/
      SKILL.md           # skill definition
    analyze/
      SKILL.md
  .mcp.json              # optional — MCP server config
  workflow.json           # optional — auto-discovered workflow
```

## The Manifest: `.claude-plugin/plugin.json`

```json
{
  "name": "e2e-test-builder",
  "description": "Iterative workflow runner for adding Playwright E2E tests.",
  "version": "1.0.0",
  "author": { "name": "Your Name" },
  "repository": "https://github.com/..."
}
```

| Field | Type | Required |
|-------|------|----------|
| `name` | string | Yes |
| `description` | string | Yes |
| `version` | string | Yes |
| `author` | object | No |
| `repository` | string | No |

## Plugin Loading

Plugins resolve from multiple sources, merged and deduplicated:

1. Workflow `plugins[]`
2. Global config `plugins[]`
3. Project config `plugins[]`
4. `--plugin` CLI flags

Entries can be:
- **Relative paths** — `./plugins/custom-commands`
- **Absolute paths** — `/home/user/my-plugin`
- **Marketplace refs** — `name@owner/repo`
- **Versioned refs** — `{ "ref": "name@owner/repo", "version": "1.0.0" }`

Later entries win on name conflicts.

## Plugin Loading Process

1. Read `.claude-plugin/plugin.json` manifest
2. Scan `skills/` directory for `*/SKILL.md` files
3. Parse YAML frontmatter for each skill
4. Convert `user-invocable: true` skills to `PromptCommand` objects
5. Register slash commands in the command registry
6. Read `.mcp.json` if present and merge into MCP config

## Available Marketplace Plugins

The `lespaceman/athena-workflow-marketplace` contains:

**e2e-test-builder** — Skills for Playwright E2E test generation:
- `/add-e2e-tests <url> <feature>` — Full pipeline orchestrator
- `/analyze-test-codebase [path]` — Detect Playwright config and conventions
- `/plan-test-coverage <url> <feature>` — Build prioritized coverage plan
- `/explore-website <url> <goal>` — Extract selectors via browser interaction
- `/generate-test-cases <url> <journey>` — Generate structured TC-ID specs
- `/write-e2e-tests <description>` — Implement executable Playwright tests

**site-knowledge** — Auto-applied automation patterns for Airbnb, Amazon, Apple Store, Apple testing.
