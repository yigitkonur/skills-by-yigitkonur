# `@mcp-use/cli` Overview

The build, dev, and deploy tool for `mcp-use` servers. Wraps TypeScript compilation, widget bundling, HMR, type generation, Inspector embedding, and Manufact Cloud deploys behind a single binary.

## Install

```bash
npx -y @mcp-use/cli <command>          # No install needed
npm install --save-dev @mcp-use/cli    # Project devDependency (recommended)
npm install -g @mcp-use/cli            # Global (rarely needed)
```

`mcp-use@1.26.0` exposes the `mcp-use` binary and imports `@mcp-use/cli@3.1.2` internally. Scaffolded projects depend on `mcp-use`; installing `@mcp-use/cli` directly is only needed when you want the CLI package without the full framework dependency.

## Commands

| Command | One-line description | Reference |
|---|---|---|
| `create-mcp-use-app` | Scaffold a new project (separate npm package) | `02-create-mcp-use-app.md` |
| `mcp-use dev` | Run dev server with HMR + Inspector + type-gen | `03-mcp-use-dev.md` |
| `mcp-use build` | Compile TS and bundle widgets to `dist/` | `04-mcp-use-build.md` |
| `mcp-use start` | Run the built server from `dist/` | `05-mcp-use-start.md` |
| `mcp-use deploy` | Deploy to Manufact Cloud | `06-mcp-use-deploy.md` |
| `mcp-use generate-types` | Regenerate `.mcp-use/tool-registry.d.ts` from Zod schemas | `07-mcp-use-generate-types.md` |
| `mcp-use org list` | List orgs you belong to | `08-mcp-use-org-list-and-switch.md` |
| `mcp-use org switch` | Interactively switch active org for `deploy` | `08-mcp-use-org-list-and-switch.md` |
| `mcp-use org current` | Show the active org | `08-mcp-use-org-list-and-switch.md` |
| `mcp-use login` | Authenticate via device-code flow | `13-device-flow-login.md` |
| `mcp-use whoami` | Print the active session | `13-device-flow-login.md` |
| `mcp-use logout` | Drop credentials | `13-device-flow-login.md` |
| `mcp-use skills add` / `install` | Install AI agent skills into the project | — |

Additional shipped command groups in `@mcp-use/cli@3.1.2`:

| Command group | Purpose |
|---|---|
| `mcp-use client ...` | Terminal MCP client: connect, sessions, tools, resources, prompts, interactive REPL. |
| `mcp-use deployments ...` | List, inspect, restart, delete, stop/start, and view logs for cloud deployments. |
| `mcp-use servers ...` | List, inspect, delete cloud servers; `servers env ...` manages server env vars. |

`mcp-use introspect`, `mcp-use serve`, and `mcp-use generate-docs` are not commands in the `mcp-use@1.26.0` installed CLI dependency. Files `09` through `11` are kept as tombstones so agents do not reintroduce those names.

For the full flag matrix in one place, see `12-flag-reference.md`. For env vars the CLI itself reads, see `14-environment-variables.md`.

## Help anywhere

```bash
mcp-use --help
mcp-use <command> --help
npx @mcp-use/cli <command> --help
```

`--help` reflects the live binary — authoritative when this skill lags behind a CLI release.

## Typical lifecycle

```bash
npx create-mcp-use-app@latest my-server   # scaffold
cd my-server
npm run dev                                # mcp-use dev
npm run build                              # mcp-use build
npm run start                              # mcp-use start
mcp-use login                              # one-time
npm run deploy                             # mcp-use deploy
```

## Output artifacts

| File | Created by | Purpose |
|---|---|---|
| `dist/` | `mcp-use build` | Compiled server + widget bundles |
| `dist/mcp-use.json` | `mcp-use build` | Build manifest — entry point, widget schemas, build ID, tunnel config |
| `.mcp-use/tool-registry.d.ts` | `mcp-use generate-types` (and `dev`) | Tool argument / return types |
| `~/.mcp-use/cli-sessions.json` | `mcp-use client` | Persists terminal client sessions |
| `.mcp-use/project.json` | `mcp-use deploy` | Links local project to a cloud deployment for stable URLs |
| `~/.mcp-use/config.json` | `mcp-use login` | User-scope auth credentials |

`.mcp-use/` is auto-added to `.gitignore`.

**Canonical doc:** https://manufact.com/docs/typescript/server/cli-reference
