# Scaffold with create-mcp-use-app

*Read this to generate a complete v2 project from template.*

The `create-mcp-use-app@2.0.0-beta.14` scaffolder generates a ready-to-run MCP server with optional React views. Three templates cover the most common shapes.

## Command

```bash
npm create mcp-use-app@2.0.0-beta.14 my-project --template mcp-server --install
# or with npx
npx create-mcp-use-app@2.0.0-beta.14 my-project --template mcp-server --install
```

Omit `--install` to skip npm install (run manually later).

## Templates

| Template | Use when | Includes |
|----------|----------|----------|
| **`mcp-server`** | Building tools, resources, or prompts without UI | `index.ts`, tools + prompts demo (weather tool, code-review prompt), `tsconfig.json`, `package.json` with scripts |
| **`mcp-apps`** | Building interactive React views bound to tools | Same as `mcp-server` + `views/` folder, `react`, `react-dom`, prebuilt view example |
| **`blank`** | Minimal starting point; add incrementally | Empty `MCPServer`, no tools or views; `index.ts` only |

Select with `--template <name>` or `-t <name>`.

## Generated file tree (mcp-server template)

```
my-project/
├── public/
│   └── icon.svg
├── index.ts                  # MCPServer instance + tool/prompt registration
├── mcp-env.d.ts              # Generated type bridge (refresh via `mcp-use typecheck`)
├── package.json              # Scripts: dev, build, typecheck, start, deploy
├── tsconfig.json             # ESM, NodeNext module, noEmit (see 07-tsconfig-and-types.md)
├── .gitignore
└── README.md
```

Every template (including `mcp-server` and `blank`) includes `public/`, not just `mcp-apps`.

**With `mcp-apps` template:** Add `public/logo-mcp-use.svg` and a `views/my-view/` folder with a full component example (`view.tsx`, `view.css`, `icons.tsx`, `Tooltip.tsx`, `MeshGradient.tsx`).

## Key script additions

All templates add to `package.json`:

```json
{
  "scripts": {
    "dev": "mcp-use dev",
    "build": "mcp-use build",
    "typecheck": "mcp-use typecheck",
    "start": "mcp-use start",
    "deploy": "mcp-use deploy"
  }
}
```

Run immediately after scaffold:

```bash
npm run dev          # Start dev server + Inspector at http://localhost:3000/mcp/inspector
npm run typecheck    # Refresh mcp-env.d.ts + tsc --noEmit
npm run build        # Build to `.mcp-use/build/`
npm run start        # Serve production build
npm run deploy       # Deploy to Manufact Cloud
```

## First run

After scaffold, the server listens at `http://localhost:3000/mcp`:

```bash
npm run dev
# Opens Inspector automatically at http://localhost:3000/mcp/inspector
```

In another terminal:

```bash
npx @mcp-use/cli@4.0.0-beta.15 client connect local http://localhost:3000/mcp
npx @mcp-use/cli@4.0.0-beta.15 client local tools list
```

## Package manager selection

Pass `--npm`, `--pnpm`, or `--bun` to force a specific manager (auto-detected by default):

```bash
npm create mcp-use-app@2.0.0-beta.14 my-server --template mcp-apps --pnpm --install
```

## Skills integration (Claude Code / Codex / Cursor)

Scaffold with `--skills` to auto-install the `mcp-apps-builder` skill into **all three** agent directories unconditionally (not per-detected-agent) — `.claude/skills/mcp-apps-builder/`, `.cursor/skills/mcp-apps-builder/`, `.agent/skills/mcp-apps-builder/`:

```bash
npm create mcp-use-app@2.0.0-beta.14 my-server --template mcp-apps --skills --install
```

Requires git (used to shallow sparse-clone `github.com/mcp-use/mcp-use` at the `beta` branch, path `skills/mcp-apps-builder`). If git is missing or the clone/checkout fails, scaffolding continues and prints a warning plus the manual install command:

```bash
npx --yes skills add mcp-use/mcp-use#beta --yes --skill mcp-apps-builder -a cursor -a claude-code -a codex
```

Telemetry (anonymous, fire-and-forget GET, silent on failure) reports fixed values regardless of which agents are actually detected: `event=install`, `source=mcp-use/mcp-use`, `skills=mcp-apps-builder`, `agents=cursor,claude-code,codex`, `sourceType=github`.

Skills-install default when `--skills`/`--no-skills` is omitted: `true` when `--template <name>` was passed explicitly; `false` for a non-interactive run with no template; otherwise (interactive, no template) the CLI prompts "Install AI coding skills for Cursor, Claude Code, and Codex?" (default yes). Pass `--no-skills` to opt out explicitly in any case.

## Lockfile & reproducibility

Commit `package-lock.json` (npm), `pnpm-lock.yaml` (pnpm), or `bun.lockb` (bun). CI uses exact pinned versions.

## Next steps

1. Start dev: `npm run dev`
2. Open Inspector: http://localhost:3000/mcp/inspector
3. Add first tool: Edit `index.ts`, see `references/04-tools/01-overview.md`
4. Add React view (mcp-apps only): Create `views/my-view/view.tsx`, see `references/18-mcp-apps/`
5. Deploy: `npm run deploy` (requires GitHub + login)
