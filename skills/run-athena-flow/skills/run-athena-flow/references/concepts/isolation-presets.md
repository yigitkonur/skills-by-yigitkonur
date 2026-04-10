# Isolation Presets

Isolation presets control what the agent is allowed to do per-session. They enforce tool and MCP server access through PreToolUse hooks.

## Presets

| Preset | MCP Servers | Allowed Tools |
|--------|-------------|---------------|
| `strict` | Blocked | `Read`, `Edit`, `Glob`, `Grep`, `Bash`, `Write` |
| `minimal` | Project servers | Above + `WebSearch`, `WebFetch`, `Task`, `Agent`, `Skill`, `mcp__*` |
| `permissive` | Project servers | Above + `NotebookEdit` |

## How Isolation Works

All presets enforce isolation by:

1. **`--setting-sources ""`** — Fully isolates from Claude Code's own settings file
2. **`--strict-mcp-config`** — Only MCP servers from Athena's merged config are available
3. **`--disallowedTools`** — Blocks first-party cloud integrations (Gmail, Calendar, Atlassian MCP, etc.)
4. **PreToolUse hooks** — Every tool call is checked against the allowed tool list

## IsolationConfig Type

The `IsolationConfig` type has 30+ fields mapping to Claude CLI flags. A declarative `FLAG_REGISTRY` maps each field to a CLI flag:

```typescript
type FlagDef = {
  flag: string;           // CLI flag name
  configKey: string;      // IsolationConfig field
  type: 'boolean' | 'string' | 'string[]';
  description: string;
};
```

## Workflow Isolation Escalation

Workflows can declare an isolation preset. The merge rule:

- **Workflow can escalate** (e.g., from `strict` to `minimal`) — with a warning in the UI
- **Workflow cannot reduce** — if the user sets `permissive`, a workflow requesting `strict` still uses `permissive`

The escalation order: `strict` < `minimal` < `permissive`.

## Usage

```bash
# Command line
athena-flow --isolation=minimal

# Config file
{
  "isolation": "permissive"
}

# Workflow definition
{
  "isolation": "minimal"
}
```

## Blocked Cloud Integrations

All presets block these first-party MCP tools by default:

- Gmail MCP tools
- Google Calendar MCP tools
- Atlassian (Jira/Confluence) MCP tools

This prevents the agent from accessing cloud services unless explicitly configured.

## MCP Server Access by Preset

- **strict**: All MCP servers blocked. No `mcp__*` tool calls allowed.
- **minimal**: Project-scoped MCP servers allowed. Tools prefixed with `mcp__` are permitted.
- **permissive**: Same as minimal for MCP access.

The difference between minimal and permissive is primarily about first-party tools like `NotebookEdit`.
