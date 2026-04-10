# MCP Servers in Plugins

Plugins expose MCP servers to the agent by including a `.mcp.json` file in the plugin root.

## How It Works

1. Each plugin with a `.mcp.json` contributes its `mcpServers` entries
2. Athena merges all entries into a temp file at `/tmp/athena-mcp-<PID>.json`
3. The temp file is passed to the agent harness at startup (`--strict-mcp-config`)
4. The harness manages the MCP server processes — Athena does not start or monitor them

## `.mcp.json` Format

```json
{
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["./server/index.js"],
      "env": {
        "MY_VAR": "value"
      }
    }
  }
}
```

Follows the standard MCP config format used by Claude Code.

## MCP Server Options

Plugins can declare configurable options in their MCP config:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["./server/index.js"],
      "options": [
        {
          "name": "API_KEY",
          "env": "MY_API_KEY",
          "description": "API key for the service",
          "required": true
        }
      ]
    }
  }
}
```

The setup wizard or `MCP server config wizard` prompts users for these values. The `options` field is stripped before writing the final merged config (Claude Code doesn't understand it).

## Name Uniqueness

MCP server names must be unique across all loaded plugins. A collision causes a startup error:

```
MCP server name collision: "my-server" is defined by multiple plugins.
Each MCP server must have a unique name across all plugins.
```

## Skills with MCP Access

When a plugin has both skills and an MCP server, its skills run with the MCP server's tools available. The agent can call MCP tools prefixed with `mcp__<server-name>__<tool-name>`.

Example: The `e2e-test-builder` plugin includes an `agent-web-interface` MCP server. Its skills can use browser automation tools like `mcp__agent-web-interface__navigate`, `mcp__agent-web-interface__snapshot`, etc.

## MCP Config Merging Process

1. Collect `.mcp.json` from all loaded plugins
2. Detect name collisions (error if found)
3. Apply user's MCP server option choices (env overrides)
4. Strip `options` field from each server entry
5. Write merged config to `/tmp/athena-mcp-<PID>.json`
6. Pass temp file path to harness via `--strict-mcp-config`

## Isolation and MCP

MCP server access depends on the isolation preset:

| Preset | MCP Access |
|--------|------------|
| `strict` | All MCP servers blocked |
| `minimal` | Project servers allowed (`mcp__*` tools permitted) |
| `permissive` | Project servers allowed (`mcp__*` tools permitted) |
