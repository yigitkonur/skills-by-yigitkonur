# Template Overview and Decision Matrix

*Read this when choosing a template for a new MCP server or deciding whether to scaffold at all.*

Three templates ship with `create-mcp-use-app@2.0.0-beta.14`. Each generates a ready-to-dev project with package.json scripts, tsconfig, and a working MCP server.

Aliases accepted by `--template`: `starter` resolves to `mcp-server`, `apps-sdk` resolves to `mcp-apps`. `--template` also accepts a GitHub repository URL, cloned in place of a built-in name.

## Decision Matrix

| Template | Use when | Entry | Includes | Output |
|----------|----------|-------|----------|--------|
| **`mcp-server`** | Building tools and prompts (no views) | `index.ts` (MCPServer default export) | `mcp-use`, `zod@^4.4.3` | `fetch-weather` tool (demo weather lookup) + `review-code` prompt (completable `language` argument) |
| **`mcp-apps`** | Building tools + interactive views/widgets | `index.ts` (MCPServer default export) | `mcp-use`, `react@^19.2.7`, `react-dom@^19.2.7`, `zod@^4.4.3` | `show-app` tool bound to `views/my-view/` + plain `say-hello` tool the view calls via `useCallTool` |
| **`blank`** | Starting from scratch (minimal) | `index.ts` (empty MCPServer, no `.listen()` call) | `mcp-use` only | No tools, prompts, or views; you build everything |

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
  --skills  # Install the mcp-apps-builder skill for Cursor, Claude Code, and Codex
```

Full flag reference: `-t, --template <template>`, `--list-templates`, `--install`/`--no-install`, `--skills`/`--no-skills`, `--no-git`, `--dev` (use workspace deps), `--sdk-version <version>` (pin `mcp-use` to an npm version or dist-tag), `--npm`/`--pnpm`/`--bun`, `-h, --help`, `-V, --version`. `--dev` and `--sdk-version` are mutually exclusive.

Without a project name in a non-interactive shell, the CLI exits with an error rather than prompting. Without `--template` in an interactive shell, it prompts for one; non-interactively it silently falls back to `mcp-server`.

## Common Generated Files (All Templates)

Every template includes:
- `index.ts` — MCP server entry point (no `.listen()` call; `mcp-use dev`/`start` own the socket)
- `package.json` with scripts: `dev`, `build`, `typecheck`, `start`, `deploy` (each shells out to the `mcp-use` CLI, e.g. `"dev": "mcp-use dev"`); `engines.node: ">=22.22.2"`
- `tsconfig.json` — `target: ES2024`, `module`/`moduleResolution: NodeNext`, `jsx: react-jsx`, `strict: true`, includes `.mcp-use/**/*.d.ts`
- `mcp-env.d.ts` — Managed typing bridge (auto-generated; imports `mcp-use/vite-client`, declares `Register.tools`)
- `gitignore` — Node + build artifacts (`node_modules/`, `dist/`, `.mcp-use/`, `.vite/`, `.env*`, logs, OS/IDE files)
- `public/icon.svg` — Server icon
- `README.md` — Quick reference (dev server URL, deploy command)

`{{PROJECT_NAME}}` placeholders in `index.ts` (`name`/`title` fields of the `MCPServer` config) are substituted with the scaffolded project name at generation time. `package.json`'s own `name` field stays the literal `"mcp-use server"`.

## Detailed Template Walkthrough

See the following for complete file trees:
- references/29-templates/02-template-mcp-server.md
- references/29-templates/03-template-mcp-apps.md
- references/29-templates/04-template-blank-and-manual.md
