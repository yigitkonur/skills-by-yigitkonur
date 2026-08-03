# mcp-use start

*Read this to serve a production build locally or before deploying to cloud.*

## Command

```bash
mcp-use start [options]
```

Serves the production build from `.mcp-use/build/` at `http://127.0.0.1:3000/mcp` (default). This is the closest local simulation of production behavior.

## Flags

| Flag | Type | Default | Effect |
|------|------|---------|--------|
| `-p, --port <n>` | number | `$PORT` or `3000` | Server port |
| `--host <host>` | string | `$HOST` or `127.0.0.1` | Bind address |
| `--tunnel` | boolean | false | Expose via public HTTPS URL |
| `--with-inspector` | boolean | false | Mount Inspector on production listener (optional) |
| `--path <directory>` | string | current dir | Project root |

## Prerequisites

`mcp-use start` requires a prior `mcp-use build`. If no build exists:

```bash
mcp-use build
mcp-use start
```

## Examples

**Production test locally:**
```bash
mcp-use build
mcp-use start
```

**With Inspector for debugging (optional):**
```bash
mcp-use start --with-inspector
# → http://127.0.0.1:3000/mcp
# → http://127.0.0.1:3000/mcp/inspector (optional debug UI)
```

**Public tunnel (for live testing):**
```bash
mcp-use start --tunnel
# Output:
# mcp-use server running at http://127.0.0.1:3000/mcp
# mcp-use public MCP URL: https://happy-blue.local.mcp-use.run/mcp
```

## Environment Variables

- `$NODE_ENV` — Set to `production` by start command only if not already set (`process.env.NODE_ENV ??= "production"`); an explicit `NODE_ENV` is never overridden
- `$PORT` — Used if no `--port` flag
- `$HOST` — Used if no `--host` flag

## Exit Codes

- `0` — Server started (never exits normally; press Ctrl+C to stop)
- `1` — Startup or config failure
- `2` — Invalid arguments

## When to use start

1. **Before cloud deploy** — verify build works locally
2. **Production simulation** — test error handling, env vars, auth flows
3. **Load testing** — use stateless build for scale testing
4. **Remote client testing** — tunnel + Inspector for external debugging

For CI/CD, `mcp-use build` is sufficient; the deploy step handles serving.
