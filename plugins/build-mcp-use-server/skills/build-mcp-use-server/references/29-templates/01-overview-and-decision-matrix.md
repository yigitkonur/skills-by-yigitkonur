# Template Overview and Decision Matrix

*Read this when choosing a template for a new MCP server or deciding whether to scaffold at all.*

Three templates ship with `create-mcp-use-app@2.0.0-beta.14`. Each generates a ready-to-dev project with package.json scripts, tsconfig, and a working MCP server.

## Decision Matrix

| Template | Use when | Entry | Includes | Output |
|----------|----------|-------|----------|--------|
| **`mcp-server`** | Building tools and prompts (no views) | `index.ts` (MCPServer default export) | `mcp-use`, `zod@4.4.3` | Weather tool + code-review prompt demo |
| **`mcp-apps`** | Building tools + interactive views/widgets | `index.ts` (MCPServer default export) | `mcp-use`, `react@19.2.7`, `react-dom@19.2.7`, `zod@4.4.3` | My-view tool with React component demo + Vite CSS |
| **`blank`** | Starting from scratch (minimal) | `index.ts` (empty MCPServer) | `mcp-use` only | No tools, prompts, or views; you build everything |

## Commands

```bash
# Scaffold with a template
npx create-mcp-use-app@2.0.0-beta.14 my-project --template mcp-server

# List available templates
npx create-mcp-use-app@2.0.0-beta.14 --list-templates

# With flags
npx create-mcp-use-app@2.0.0-beta.14 my-project \
  --template mcp-apps \
  --npm \
  --install \
  --skills  # Install mcp-apps-builder skill
```

## Common Generated Files (All Templates)

Every template includes:
- `index.ts` — MCP server entry point
- `package.json` with scripts: `dev`, `build`, `typecheck`, `start`, `deploy`
- `tsconfig.json` configured for ESM + MCP types
- `mcp-env.d.ts` — Managed typing bridge (auto-generated)
- `gitignore` — Standard Node + build artifacts
- `public/icon.svg` — Server icon
- `README.md` — Quick reference

## Detailed Template Walkthrough

See the following for complete file trees:
- references/29-templates/02-template-mcp-server.md
- references/29-templates/03-template-mcp-apps.md
- references/29-templates/04-template-blank-and-manual.md
