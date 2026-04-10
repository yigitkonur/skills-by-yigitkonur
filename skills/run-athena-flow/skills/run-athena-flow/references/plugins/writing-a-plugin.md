# Writing a Plugin

## Step 1: Create the Directory

```bash
mkdir my-plugin && cd my-plugin
mkdir -p .claude-plugin skills/analyze-deps
```

## Step 2: Write the Manifest

```json
// .claude-plugin/plugin.json
{
  "name": "my-plugin",
  "description": "Custom dependency analysis skill.",
  "version": "1.0.0",
  "author": { "name": "Your Name" }
}
```

## Step 3: Define a Skill

Create `skills/analyze-deps/SKILL.md`:

```markdown
---
name: analyze-deps
description: Analyze project dependencies for outdated packages and vulnerabilities
user-invocable: true
argument-hint: "[path]"
allowed-tools:
  - Read
  - Bash
---

Analyze the dependencies of this project.

Target path: $ARGUMENTS

Identify:
- Outdated packages with available updates
- Packages with known vulnerabilities
- Unused dependencies

Output a structured report grouped by severity.
```

`$ARGUMENTS` is replaced with whatever the user types after the command name.

## Step 4: Load the Plugin

```bash
athena-flow --plugin=./my-plugin
```

Or add to `.athena/config.json`:

```json
{
  "plugins": ["./my-plugin"]
}
```

## Step 5: Test the Skill

```
/analyze-deps ./src
```

## Step 6: Add an MCP Server (Optional)

Create `.mcp.json` alongside `.claude-plugin/`:

```json
{
  "mcpServers": {
    "my-tools": {
      "command": "node",
      "args": ["./server/index.js"]
    }
  }
}
```

Skills in this plugin get access to `my-tools`'s custom tools.

## Step 7: Add a Workflow (Optional)

Place a `workflow.json` at the plugin root for auto-discovery:

```json
{
  "name": "my-workflow",
  "promptTemplate": "Run the analysis...",
  "plugins": [],
  "isolation": "strict"
}
```

If exactly one workflow is discovered and no `--workflow` flag is set, it activates automatically.

## Step 8: Publish to a Marketplace

Place your plugin in a marketplace repo and register it in `.claude-plugin/marketplace.json`:

```json
{
  "name": "my-marketplace",
  "owner": { "name": "Your Name" },
  "metadata": { "pluginRoot": "./plugins" },
  "plugins": [
    { "name": "my-plugin", "source": "my-plugin", "description": "What it does" }
  ]
}
```

Once committed, reference it as:

```json
{
  "plugins": ["my-plugin@your-org/your-marketplace-repo"]
}
```

## Tips

- Keep each skill focused on one task
- Test locally with `--plugin` before publishing
- Skills without `user-invocable: true` are loaded but not surfaced as commands — useful for workflow-invoked skills
- Plugin names must be unique across all loaded plugins
- MCP server names must be unique across all loaded plugins
