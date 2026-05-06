# `mcp-use dev`

Boots the dev server with HMR, type generation, and the Inspector. The default workflow for everything except production.

## Usage

```bash
mcp-use dev [options]
npx @mcp-use/cli dev [options]
```

Entry is not positional in `@mcp-use/cli@3.1.2`. Use `--entry <file>` to override the default server entry discovery.

## Flags

| Flag | Description | Default |
|---|---|---|
| `-p, --path <path>` | Project directory | `.` |
| `--entry <file>` | MCP server entry file, relative to project | auto-detected |
| `--widgets-dir <dir>` | Widgets/resources directory | `resources` |
| `--mcp-dir <dir>` | Folder holding the MCP entry and resources, for drop-in layouts | — |
| `--port <port>` | HTTP port | `3000` |
| `--host <host>` | Host interface | `0.0.0.0` |
| `--no-open` | Don't auto-open the Inspector | `false` |
| `--no-hmr` | Disable HMR; fall back to `tsx watch` | `false` |
| `--tunnel` | Expose dev server via tunnel | `false` |

## What happens

1. Sets `MCP_USE_CLI_DEV=1`, `PORT`, `HOST`, `NODE_ENV=development`, and `MCP_URL` when missing.
2. Finds the server entry via `--entry`, `--mcp-dir`, or default discovery.
3. Starts the server in HMR mode, or uses `tsx watch` when `--no-hmr` is passed.
4. Opens `http://localhost:<port>/inspector` unless `--no-open` is set.
5. Serves the MCP endpoint at `http://localhost:<port>/mcp`.

## HMR signals

`mcp-use dev` logs which subsystem reloaded. Use these to confirm HMR is working when behavior looks stale.

| Log line | What it means | Client effect |
|---|---|---|
| `HMR enabled - changes will hot reload without dropping connections` | HMR path active | Server module will be re-imported on changes |
| `[HMR] Watcher ready, watching ... paths` | Watcher is attached | Edits should trigger reloads |
| `[HMR] File changed: ...` | A watched file changed | Reload cycle begins |
| `[HMR] Reloaded: ...` | Registrations changed and synced | List-changed notifications may fire |
| `[HMR] No changes detected (...)` | Module reloaded but registrations were unchanged | No client surface change |
| `[HMR] Reload failed: ...` | Reload threw | Restart or use `--no-hmr` to isolate |

## What HMR can and cannot do

| Change | HMR? |
|---|---|
| Add / update / remove tools, resources, prompts, resource templates | Yes |
| Change descriptions, schemas, handlers | Yes |
| Edit a widget component | Yes |
| Change `MCPServer` constructor (`name`, `version`, `port`, `oauth`, middleware) | No — restart |
| Add new top-level middleware via `server.use(...)` | No — restart |

## Diagnostics for HMR failures

| Symptom | Likely cause | Action |
|---|---|---|
| Code edits not reflected | HMR reload failed | Watch for `[HMR] Reload failed`; restart with `--no-hmr` to confirm logic still builds |
| Widget UI stuck on old props | Widget rebuilt but client cached | Reload the host pane / Inspector |
| Types stale in widget hooks | `generate-types` failed silently | Run `mcp-use generate-types` manually; fix Zod errors it surfaces |
| Inspector blank | Browser blocked auto-open or `--no-open` set | Open `http://localhost:<port>/inspector` manually |
| Port already bound | Another process on `--port` | CLI picks an available port; use `--port` or `lsof -i :<port>` if you need a fixed port |

## Examples

```bash
mcp-use dev                            # uses index.ts on :3000
mcp-use dev --entry src/server.ts      # explicit entry
mcp-use dev --port 8080
mcp-use dev --host 127.0.0.1
mcp-use dev --no-open                  # CI / headless
mcp-use dev --no-hmr                   # debug bundler issues
mcp-use dev --tunnel                   # ChatGPT widget testing
mcp-use dev -p ./packages/api          # monorepo
```

## Anti-pattern

Disabling HMR by default. `--no-hmr` is a debugging escape hatch, not a production flag — without HMR, schema edits drop client connections.

## See also

- `04-mcp-use-build.md` — the production counterpart
- `07-mcp-use-generate-types.md` — what auto-runs in dev
- `../02-setup/09-env-vars.md` — `PORT`, `HOST`, `MCP_URL` precedence
