# `mcp-use start`

Runs the built server from `dist/`. The production counterpart to `mcp-use dev`.

## Usage

```bash
mcp-use start [options]
```

Entry is not positional. The CLI reads `dist/mcp-use.json` for the entry point and falls back to built files under `dist/`.

## Flags

| Flag | Description | Default |
|---|---|---|
| `-p, --path <path>` | Project directory | `.` |
| `--entry <file>` | Declared in help, but `@mcp-use/cli@3.1.2` runtime uses manifest/fallback discovery | do not rely on it |
| `--mcp-dir <dir>` | Folder holding MCP entry and resources | — |
| `--port <port>` | HTTP port | `3000` |
| `--tunnel` | Expose the running server via tunnel | `false` |

## Mode

`mcp-use start` runs the HTTP transport built into `MCPServer`. There is no stdio mode flag — `mcp-use` is HTTP-first. If you need a stdio child process, see `../02-setup/04-manual-stdio-server.md`.

## Prerequisite

`mcp-use build` must have run first. Without `dist/`, start fails:

```
Error: dist/ not found. Run `mcp-use build` first.
```

The current CLI error text lists the files it checked, including `dist/mcp-use.json`, `dist/index.js`, `dist/server.js`, `dist/src/index.js`, and `dist/src/server.js`.

## Examples

```bash
mcp-use start
mcp-use start --port 8080
mcp-use start --tunnel              # exposes the server via tunnel for remote testing
mcp-use start -p ./packages/api
```

## What it serves

| Path | Notes |
|---|---|
| `/mcp` | JSON-RPC endpoint (POST), SSE stream (GET), session DELETE, HEAD |
| `/inspector` | Only if the build was made with `--with-inspector` |
| `/mcp-use/widgets/*` | Widget bundles emitted by `mcp-use build` |
| `/sse` | Legacy alias for older clients |

## Common failures

| Symptom | Cause | Fix |
|---|---|---|
| `dist/ not found` | Build skipped | `mcp-use build && mcp-use start` |
| Widget assets 404 | Build was made without `MCP_SERVER_URL` | Rebuild with the public URL |
| `/inspector` 404 | Build did not include Inspector | Rebuild with `--with-inspector` (debug builds only) |
| `EADDRINUSE` | Another process on the port | Change `--port` or kill the holder |

## Local prod parity

```bash
mcp-use build && mcp-use start --port 4000
```

Useful for verifying widget asset paths and the manifest before deploying.

## Tunnel mode

`--tunnel` opens a public URL pointing at the local instance. Use to share a running server with ChatGPT or to debug remote OAuth callbacks. Tunnel subdomain persists across runs once `dist/mcp-use.json` records it.

```bash
mcp-use build && mcp-use start --tunnel
```

The CLI prints the public URL on startup.

## See also

- `04-mcp-use-build.md` — produces `dist/`
- `06-mcp-use-deploy.md` — runs `start` for you on Manufact Cloud
- `10-mcp-use-serve.md` — tombstone for a non-shipped command name
