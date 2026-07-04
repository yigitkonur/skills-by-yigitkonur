# Template Flags for `create-mcp-use-app`

Pick the template that matches the surface you intend to ship — tools-only, MCP Apps widgets, or MCP-UI UIResources.

## Templates

| Template | Flag | Includes | Pick when |
|---|---|---|---|
| `starter` | `--template starter` (default) | Tools, resources, prompts, one example widget | Building a general-purpose server; unsure which surface to use. |
| `mcp-apps` | `--template mcp-apps` | React widgets pre-wired with `useWidget` / `useCallTool`, dual-protocol (MCP Apps + ChatGPT Apps SDK), Tailwind | Shipping interactive React widgets that render inside ChatGPT or MCP App hosts. |
| `mcp-ui` | `--template mcp-ui` | Examples for all three MCP-UI `UIResource` types: iframe, raw HTML, Remote DOM | Targeting MCP-UI `ui://` resources rather than MCP Apps widgets. |

## Other flags

| Flag | Effect | Default |
|---|---|---|
| `--template <name>` | Selects the template above | `starter` |
| `--no-skills` | Skips installing AI agent skills into `.cursor/skills/`, `.claude/skills/`, `.agent/skills/` | `false` (skills install) |

Use `--no-skills` while iterating on a brand-new project — it removes unrelated agent-skill installation noise from the first build.

## Examples

```bash
# Default — starter
npx create-mcp-use-app@latest my-server

# MCP Apps (recommended for widget work)
npx create-mcp-use-app@latest my-server --template mcp-apps --no-skills

# MCP-UI
npx create-mcp-use-app@latest my-server --template mcp-ui --no-skills
```

## How to choose

| You intend to | Template |
|---|---|
| Expose tools and resources only, no UI | `starter` |
| Ship React widgets that render in ChatGPT or MCP Apps hosts | `mcp-apps` |
| Ship arbitrary HTML / iframe / Remote DOM UIResources | `mcp-ui` |
| Migrate an existing app — see `06-add-to-existing-app.md`, no template applies | — |

For deep widget guidance after picking `mcp-apps`, route to `18-mcp-apps/` in this skill.

## Help

```bash
npx create-mcp-use-app@latest --help
```

Prints the live flag list at install time — authoritative when this doc lags behind a CLI release.
