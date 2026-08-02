# Template flags

*Read this to choose the right scaffold template.*

Three templates exist; all are v2 beta.14. Pick one matching your surface intent.

## Template matrix

| Template | Includes | Use when |
|----------|----------|----------|
| **`mcp-server`** | Tools, resources, prompts (no UI) | Building a CLI-driven or tool-only server. Demo: weather tool, code-review prompt. |
| **`mcp-apps`** | React views, `useToolContext`, `useCallTool`, CSP config | Shipping interactive React components bound to tools. Dual MCP Apps + ChatGPT protocol. |
| **`blank`** | Empty `MCPServer` | Minimal starting point; add everything yourself. |

## Flag usage

```bash
# mcp-server (default)
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
| `--install` / `--no-install` | Run npm install after scaffold (default: `--no-install`) |
| `--npm` / `--pnpm` / `--bun` | Force package manager (default: auto-detect) |
| `--skills` / `--no-skills` | Install mcp-apps-builder skill (Claude Code / Cursor / Codex) |
| `--dev` | Use `workspace:*` for mcp-use dependency (v2 development only) |
| `--sdk-version <version>` | Pin a specific mcp-use version (default: `2.0.0-beta.66`) |

## Choosing

- **No UI needed?** → `mcp-server`
- **React views (ChatGPT, MCP Apps host)?** → `mcp-apps`
- **Starting from scratch?** → `blank` or `mcp-server`

For post-scaffold guidance, see:
- `04-manual-http-server.md` — write a server without scaffold
- `05-add-to-existing-app.md` — embed MCP in existing app
- `references/18-mcp-apps/` — React view patterns
