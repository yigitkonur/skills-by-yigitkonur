# `create-mcp-use-app`

Scaffolder. Separate npm package from `@mcp-use/cli`, but documented here because it's the canonical entry point for new projects.

## Usage

```bash
npx create-mcp-use-app@latest <project-name> [flags]
```

Always pin `@latest` — the scaffolder evolves quickly and stale npx caches produce outdated projects.

## Flags

| Flag | Description | Default |
|---|---|---|
| `-t, --template <template>` | Template name or GitHub repo URL (`owner/repo`, URL, optional `#branch`) | prompt, then `starter` fallback |
| `--list-templates` | Print templates packaged in the installed CLI | — |
| `--install` / `--no-install` | Force or skip dependency install | prompt unless template was passed |
| `--skills` / `--no-skills` | Install or skip agent skills | prompt unless template was passed |
| `--no-git` | Skip git init | `false` |
| `--dev` | Use workspace dependency versions | `false` |
| `--canary` | Use canary package versions | `false` |
| `--npm` / `--yarn` / `--pnpm` | Force package manager | auto-detect |

`create-mcp-use-app@0.14.10` ships `blank`, `mcp-apps`, and `starter` directories. Its help text also mentions `mcp-ui`; treat `--list-templates` and the packaged `dist/templates/` directory as authoritative for the installed version.

For full template descriptions, see `../02-setup/03-template-flags.md`.

## Examples

```bash
npx create-mcp-use-app@latest my-server
npx create-mcp-use-app@latest my-server --template mcp-apps --no-skills
npx create-mcp-use-app@latest my-server --template owner/repo#branch-name
npx create-mcp-use-app@latest --list-templates
```

## What gets generated

Default (`starter`) layout:

```
my-server/
├── resources/
├── public/
├── index.ts
├── package.json
├── tsconfig.json
├── README.md
└── .mcp-use/
```

Entry file is `index.ts` at the project root — not `src/server.ts`. `package.json` ships with the canonical script set (`dev`, `build`, `start`, `deploy`).

For the full structure walkthrough and post-scaffold checks, route to `../02-setup/02-scaffold-with-create-mcp-use-app.md`.

## Post-scaffold steps

```bash
cd my-server
npm install         # run if scaffolder skipped install
npm run dev         # boot dev server + Inspector
```

Verify the build path before adding custom code:

```bash
npm run build
npx mcp-use generate-types
```

## When not to use the scaffolder

| Situation | Use instead |
|---|---|
| Adding MCP to an existing app | `../02-setup/06-add-to-existing-app.md` |
| You want full control over `tsconfig` and dependencies | `../02-setup/05-manual-http-server.md` |
| Targeting raw stdio without `mcp-use` HTTP | `../02-setup/04-manual-stdio-server.md` |

## Help

```bash
npx create-mcp-use-app@latest --help
```

Lists all live flags. Trust the binary over docs when in doubt.
