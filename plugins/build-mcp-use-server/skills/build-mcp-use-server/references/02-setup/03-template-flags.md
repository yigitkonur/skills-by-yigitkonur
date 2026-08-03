# Template flags

*Read this to choose the right scaffold template.*

Three templates exist; all are v2 beta.14. Pick one matching your surface intent.

## Template matrix

| Template | Includes | Use when |
|----------|----------|----------|
| **`mcp-server`** | Tools, resources, prompts (no UI) | Building a CLI-driven or tool-only server. Demo: weather tool, code-review prompt. |
| **`mcp-apps`** | React views, `useToolContext`, `useCallTool`, CSP config | Shipping interactive React components bound to tools. Dual MCP Apps + ChatGPT protocol. |
| **`blank`** | Empty `MCPServer` | Minimal starting point; add everything yourself. |

Omitting `--template`: a non-interactive invocation (CI, piped stdin) defaults to `mcp-server`; an interactive terminal prompts, with `mcp-apps` pre-selected as the default choice.

## Flag usage

```bash
# mcp-server (non-interactive default)
npm create mcp-use-app@2.0.0-beta.14 my-server --template mcp-server --install

# mcp-apps (React views)
npm create mcp-use-app@2.0.0-beta.14 my-server --template mcp-apps --install

# blank (empty)
npm create mcp-use-app@2.0.0-beta.14 my-server --template blank --install

# Force package manager
npm create mcp-use-app@2.0.0-beta.14 my-server --template mcp-apps --pnpm --install
npm create mcp-use-app@2.0.0-beta.14 my-server --template mcp-apps --bun --install
```

## Optional flags

| Flag | Effect |
|------|--------|
| `--install` / `--no-install` | Run npm install after scaffold (default: `false` when `--template` or non-interactive is set; interactive runs prompt) |
| `--npm` / `--pnpm` / `--bun` | Force package manager (default: auto-detect from `npm_config_user_agent`, else `npm`) |
| `--skills` / `--no-skills` | Install mcp-apps-builder skill into `.claude/skills/`, `.cursor/skills/`, `.agent/skills/` (default varies — see `02-scaffold-with-create-mcp-use-app.md`) |
| `--no-git` | Skip initializing a git repository (listed in `--help`; git init behavior is otherwise on by default) |
| `--dev` | Use `workspace:*` for the mcp-use dependency (mcp-use monorepo development only; mutually exclusive with `--sdk-version`) |
| `--sdk-version <version>` | Pin mcp-use to a specific npm version or dist-tag (e.g. `canary`, `1.34.0`). Omitted: the CLI fetches the current `beta` dist-tag from the npm registry at scaffold time — there is no hardcoded default version baked into the CLI |
| `-t`, `--template <name-or-url>` | Template name, or a GitHub repo URL/`owner/repo`/`owner/repo#branch` to scaffold from a custom template (requires git) |
| `--list-templates` | Print all available templates and exit |

## GitHub repo as template

Any public GitHub repository can be used as a template instead of a built-in name:

```bash
npm create mcp-use-app@2.0.0-beta.14 my-project --template owner/repo
npm create mcp-use-app@2.0.0-beta.14 my-project --template https://github.com/owner/repo
npm create mcp-use-app@2.0.0-beta.14 my-project --template owner/repo#branch-name
```

Requires git; useful for organization-specific or community templates.

## Choosing

- **No UI needed?** → `mcp-server`
- **React views (ChatGPT, MCP Apps host)?** → `mcp-apps`
- **Starting from scratch?** → `blank` or `mcp-server`

For post-scaffold guidance, see:
- `04-manual-http-server.md` — write a server without scaffold
- `05-add-to-existing-app.md` — embed MCP in existing app
- `references/18-mcp-apps/` — React view patterns
