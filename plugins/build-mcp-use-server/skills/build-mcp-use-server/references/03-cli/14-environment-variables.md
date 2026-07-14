# CLI Environment Variables

Env vars the `@mcp-use/cli` itself reads. For env vars the running server reads, see `../02-setup/09-env-vars.md`.

## Build, dev, and start

| Variable | Read by | Effect | Default |
|---|---|---|---|
| `PORT` | `start` reads; `dev` sets for child/server | HTTP port, unless `--port` is supplied | `3000` |
| `HOST` | `dev` sets; server `listen()` can read | Host interface | `0.0.0.0` in CLI dev |
| `NODE_ENV` | `dev`, `build`, `start`, server runtime | Development/production behavior | `development` or `production` by command |
| `MCP_URL` | `dev`, `start`, `build` widget bundler, server runtime | Public/base MCP URL and widget bundle base | `http://localhost:<port>` in CLI runs |
| `MCP_SERVER_URL` | `build` | Injected public server/base URL into built widget HTML | — |
| `MCP_USE_WIDGETS_DIR` | `dev`, server widget mounting | Override resources/widgets directory | `resources` |

Set both `MCP_URL` and `MCP_SERVER_URL` for static or remote widget builds.

## Deploy and cloud

| Variable | Read by | Effect | Default |
|---|---|---|---|
| `MCP_WEB_URL` | `login`, `deploy` | Frontend URL for the auth flow / dashboard | `https://manufact.com` |
| `MCP_API_URL` | `login`, `deploy`, cloud command groups | Backend API URL the CLI talks to | `https://cloud.mcp-use.com/api/v1` |
| `MCP_USE_API_KEY` | `login` | API key for non-interactive login | — |
| `MCP_USE_API` | `dev`, `start` tunnel cleanup | Local tunnel API base override | `https://local.mcp-use.run` |
| `MCP_USE_TUNNEL_API` | `dev` tunnel startup | Local tunnel API base override for initial tunnel deletion | `https://local.mcp-use.run` |

Override both for local Manufact Cloud development:

```bash
export MCP_WEB_URL=http://localhost:3000
export MCP_API_URL=http://localhost:8000
mcp-use login
mcp-use deploy
```

## Logging

| Variable | Read by | Effect | Default |
|---|---|---|---|
| `DEBUG` | CLI internals and mcp-use runtime | Enables verbose debug behavior when truthy | — |
| `VERBOSE` | CLI internals | Enables extra debug output in selected paths | — |
| `MCP_DEBUG_LEVEL` | mcp-use server runtime, not the CLI command parser | Server log level: `info`, `debug`, or `trace` | `info` |

Use `MCP_DEBUG_LEVEL=debug` (or `trace`) for server runtime logs. Use `DEBUG=1` or `VERBOSE=1` only when you need CLI internals.

## Auth (CLI-side)

| Variable | Read by | Effect |
|---|---|---|
| `MCP_USE_API_KEY` | `mcp-use login` | Save an API key without device-code flow |

`MCP_USE_TOKEN` is not read by `@mcp-use/cli@3.1.2`. The persistent fallback is `~/.mcp-use/config.json`, written by `mcp-use login`. See `13-device-flow-login.md`.

## Precedence

When the same setting is reachable both as a flag and as an env var, the flag wins. When the same setting is reachable both as a runtime env var (`MCP_URL`) and a build-time env var (`MCP_SERVER_URL`), they apply at different stages — set both for production.

## Where these vars come from

| Source | Notes |
|---|---|
| Shell session | `export FOO=…` for the current shell |
| `.env`, `.env.local` | Loaded by Next.js shim handling and user runtime code; do not assume all CLI commands source them |
| CI environment | Most CI providers expose env vars; use them for `MCP_USE_API_KEY`, `MCP_DEBUG_LEVEL` |

If you want `MCP_DEBUG_LEVEL=debug` to apply to the server launched by `mcp-use dev`, export it in the shell or prepend it to the command:

```bash
MCP_DEBUG_LEVEL=debug mcp-use dev
```

## Quick reference

```bash
# Verbose dev logs
MCP_DEBUG_LEVEL=debug mcp-use dev

# Build with prod asset URLs
MCP_URL=https://static.example.com/widgets \
MCP_SERVER_URL=https://mcp.example.com \
mcp-use build

# Talk to a self-hosted Manufact Cloud
MCP_WEB_URL=http://localhost:3000 \
MCP_API_URL=http://localhost:8000 \
mcp-use deploy

# Non-interactive CLI login
MCP_USE_API_KEY=mk_live_... mcp-use login
```

## See also

- `../02-setup/09-env-vars.md` — env vars the running server reads
- `12-flag-reference.md` — flag vs env-var precedence matrix
- `13-device-flow-login.md` — how login uses these vars
