# create-mcp-use-app

*Read this to scaffold a new MCP server project.*

Scaffolds a new MCP server with TypeScript, package scripts, and optional views. This is the canonical entry point for new projects.

## Usage

```bash
npx create-mcp-use-app@2.0.0-beta.14 <project-name> [options]
```

Always use the `@beta` tag for v2; stable v1 (1.x) scaffolds v1 projects.

## Flags

| Flag | Type | Default | Effect |
|------|------|---------|--------|
| `-t, --template <name>` | string | `mcp-server` | Template: `mcp-server`, `mcp-apps`, or `blank` |
| `--list-templates` | boolean | — | List available templates and exit |
| `--install / --no-install` | boolean | auto-prompt | Run `npm install` after scaffold |
| `--skills / --no-skills` | boolean | auto-prompt | Install mcp-apps-builder skill (Claude Code/Cursor/Codex) |
| `--dev` | boolean | false | Use `workspace:*` for mcp-use dependency (monorepo) |
| `--sdk-version <version>` | string | latest beta | Pin mcp-use to specific version |
| `--npm / --pnpm / --bun` | boolean | auto-detect | Force package manager |
| `-h, --help` | boolean | — | Show help and exit |
| `-V, --version` | boolean | — | Show version and exit |

## Templates

Three templates come packaged:

| Template | Use case | Dependencies | Entry |
|----------|----------|--------------|-------|
| **`mcp-server`** | Tools + prompts (no UI) | `mcp-use`, `zod@4` | `index.ts` with sample weather tool |
| **`mcp-apps`** | Tools + React views | `mcp-use`, `react@19`, `zod@4` | `index.ts` with sample tool + view |
| **`blank`** | Minimal starter | `mcp-use` only | Empty `index.ts` (no samples) |

## Examples

**Default (mcp-server template, auto-install):**
```bash
npx create-mcp-use-app@2.0.0-beta.14 my-server
```

**With views:**
```bash
npx create-mcp-use-app@2.0.0-beta.14 my-server --template mcp-apps
```

**Minimal (blank template, skip install):**
```bash
npx create-mcp-use-app@2.0.0-beta.14 my-server --template blank --no-install
```

**For monorepo (workspace deps):**
```bash
npx create-mcp-use-app@2.0.0-beta.14 my-server --dev
```

**List templates:**
```bash
npx create-mcp-use-app@2.0.0-beta.14 --list-templates
```

## Generated structure

```
my-server/
├── index.ts                    # Server entry (ESM)
├── package.json               # Scripts: dev, build, typecheck, start, deploy
├── tsconfig.json
├── mcp-env.d.ts              # MCP type definitions (auto-generated)
├── views/                     # (if mcp-apps template)
│   ├── my-view/
│   │   └── view.tsx
│   └── ...
├── .gitignore
├── README.md
└── node_modules/              # (if --install not skipped)
```

## Post-scaffold steps

```bash
cd my-server

# If --no-install was used
npm install

# Start development
npm run dev
# → Opens Inspector at http://localhost:3000/mcp/inspector

# Test build
npm run build

# Verify types
npm run typecheck
```

## Skills installation

With `--skills` (default, prompts), the scaffolder installs the `mcp-apps-builder` skill if your environment supports it (Claude Code, Cursor, or Codex). This enables AI-powered view generation and skill building.

Telemetry is sent silently (errors swallowed); no opt-out flag exists currently.

## Package managers

Auto-detects from `npm_config_user_agent`; override with `--npm`, `--pnpm`, or `--bun`.

## Next steps

- Read the generated `README.md` for project-specific guidance
- Start with `npm run dev` and open the Inspector
- For views, see `references/18-mcp-apps/`
- For deployment, see `06-mcp-use-deploy-and-cloud.md`
