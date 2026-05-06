# Flag Reference

Every CLI flag across every command in one table. For per-command detail and examples, see the individual command files.

## Master table

| Flag | Applies to | What it does |
|---|---|---|
| `-p, --path <path>` | `dev`, `build`, `start`, `generate-types`, `skills add`, `skills install` | Project directory; defaults to `.`. |
| `--entry <file>` | `dev`, `build`, `start` | MCP server entry file for `dev`/`build`; declared but not consumed by `start` in 3.1.2. |
| `--widgets-dir <dir>` | `dev`, `build` | Widgets/resources directory. |
| `--mcp-dir <dir>` | `dev`, `build`, `start` | MCP folder override for drop-in layouts. |
| `--port <port>` | `dev`, `start`, `deploy` | HTTP port; default `3000`. |
| `--host <host>` | `dev` | Host interface; default `0.0.0.0`. |
| `--no-open` | `dev` | Don't auto-open the Inspector in the browser. |
| `--no-hmr` | `dev` | Disable HMR; fall back to `tsx watch`. |
| `--tunnel` | `dev`, `start` | Expose the server via tunnel for remote testing. |
| `--with-inspector` | `build` | Bundle the Inspector into the build output. |
| `--inline` / `--no-inline` | `build` | Inline widget JS/CSS or keep separate files. |
| `--no-typecheck` | `build` (v1.21.5+) | Skip TS type-checking; transpile only. |
| `--server <file>` | `generate-types` | Server entry file; default `index.ts`. |
| `--name <name>` | `deploy` | Custom deployment name. |
| `--runtime <runtime>` | `deploy` | `node` or `python`; default `node`. |
| `--open` | `deploy` | Open the deployment URL in a browser. |
| `--new` | `deploy` | Force creation of a new deployment. |
| `--env <key=value...>` | `deploy` | Environment variables. |
| `--env-file <path>` | `deploy` | Load env vars from a `.env` file. |
| `--root-dir <path>` | `deploy` | Monorepo root directory. |
| `--org <slug-or-id>` | `deploy` | One-off org override; persistent default via `org switch`. |
| `-y, --yes` | `deploy`, `deployments delete`, `servers delete` | Skip confirmation prompts. |
| `--region <region>` | `deploy` | Deploy region: `US`, `EU`, or `APAC`. |
| `--build-command <cmd>` | `deploy` | Override auto-detected build command. |
| `--start-command <cmd>` | `deploy` | Override auto-detected start command. |
| `--api-key <key>` | `login` | Non-interactive API-key login. |
| `--org <slug|id|name>` | `login` | Select organization after login. |
| `--name <name>` | `client connect` | Save a terminal client session name. |
| `--stdio` | `client connect` | Use stdio connector instead of HTTP. |
| `--auth <token>` | `client connect` | Pass an authentication token. |
| `--all` | `client disconnect` | Disconnect all saved sessions. |
| `--session <name>` | `client tools`, `client resources`, `client prompts`, `client interactive` | Use a named client session. |
| `--json` | `client tools list/call`, `client resources list/read`, `client prompts list/get` | Output JSON. |
| `--timeout <ms>` | `client tools call` | Tool call timeout in milliseconds. |
| `-f, --follow` | `deployments restart`, `deployments logs` | Follow build logs. |
| `-b, --build` | `deployments logs` | Show build logs instead of runtime logs. |
| `--org <slug-or-id>` | `servers list/get/delete` | Cloud server organization context. |
| `--limit <n>` | `servers list` | Server list page size. |
| `--skip <n>` | `servers list` | Server list offset. |
| `--sort <field:asc|desc>` | `servers list` | Server list sort order. |
| `--server <id>` | `servers env list/add/update/remove` | Target server UUID. |
| `--show-values` | `servers env list` | Reveal non-sensitive env var values. |
| `--env <environments>` | `servers env add/update` | Comma-separated environments: production, preview, development. |
| `--sensitive` / `--no-sensitive` | `servers env add/update` | Mark or unmark an env var as sensitive. |
| `--value <value>` | `servers env update` | New env var value. |
| `--template <template>` | `create-mcp-use-app` | Template name or GitHub repo URL. |
| `--list-templates` | `create-mcp-use-app` | List packaged templates. |
| `--install` / `--no-install` | `create-mcp-use-app` | Force or skip dependency install. |
| `--skills` / `--no-skills` | `create-mcp-use-app` | Install or skip agent skills. |
| `--no-git` | `create-mcp-use-app` | Skip git init. |
| `--dev` | `create-mcp-use-app` | Use workspace dependency versions. |
| `--canary` | `create-mcp-use-app` | Use canary package versions. |
| `--npm` / `--yarn` / `--pnpm` | `create-mcp-use-app` | Force package manager. |
| `--help` | every command | Print live help for that command. |

## Flag vs env var matrix

When both exist, prefer flags for ad-hoc work and env vars for persistent or sensitive configuration.

| Need | Prefer flag | Prefer env var |
|---|---|---|
| Quick port override | `--port 4000` | — |
| Persistent port | — | `PORT=4000` |
| Public URL for widget assets | — | `MCP_SERVER_URL=https://…` |
| Local debugging Inspector | `--with-inspector` | — |
| CLI login in CI | `mcp-use login --api-key ...` | `MCP_USE_API_KEY=...` |
| Deploy secrets | `--env-file` (file-based) | CI secret store |

## Help output is authoritative

Every command supports `--help`. When this file disagrees with `mcp-use <command> --help`, trust `--help` — it reflects the binary you installed.

```bash
mcp-use --help
mcp-use dev --help
mcp-use build --help
mcp-use deploy --help
mcp-use generate-types --help
```

## See also

- Individual command files in this cluster (`03-` through `11-`)
- `14-environment-variables.md` — all CLI-side env vars
- `../02-setup/09-env-vars.md` — server-side env vars
