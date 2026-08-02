# mcp-use dev

*Read this to start local development with HMR, Inspector, and type refresh.*

## Command

```bash
mcp-use dev [options]
```

Starts a local development server at `http://127.0.0.1:3000/mcp` (default) with:

- **Hot module reload (HMR)** — view changes reload without restarting
- **Inspector automount** — UI at `/mcp/inspector` (disable with `--no-inspector`)
- **Type generation** — `.mcp-use/mcp-env.d.ts` refreshed on every change
- **Public tunnel** (optional) — expose via `--tunnel`

## Flags

| Flag | Type | Default | Effect |
|------|------|---------|--------|
| `-p, --port <n>` | number | `$PORT` or `3000` | Server port |
| `--host <host>` | string | `$HOST` or `127.0.0.1` | Bind address (localhost-only by default) |
| `--entry <path>` | string | `package.json#main` | Server entry module |
| `--mcp-dir <dir>` | string | auto-detect | Directory containing entry + `views/` |
| `--views-dir <dir>` | string | `views/` or `<mcp-dir>/views/` | React view components |
| `--tunnel` | boolean | false | Expose via public HTTPS URL |
| `--no-open` | boolean | false | Don't auto-open Inspector in browser |
| `--no-inspector` | boolean | false | Skip Inspector module entirely |
| `--path <directory>` | string | current dir | Project root |

## Examples

**Basic dev (with Inspector):**
```bash
mcp-use dev
# → http://127.0.0.1:3000/mcp
# → http://127.0.0.1:3000/mcp/inspector (auto-opens)
```

**Public tunnel (for testing with remote clients):**
```bash
mcp-use dev --tunnel
# Output:
# mcp-use server running at http://127.0.0.1:3000/mcp
# mcp-use public MCP URL: https://happy-blue.local.mcp-use.run/mcp
```

**Headless (no browser, no Inspector):**
```bash
mcp-use dev --no-inspector --no-open
```

**Custom port:**
```bash
mcp-use dev --port 4000
```

## Inspector at /mcp/inspector

When `mcp-use dev` runs, Inspector is **automatically mounted** at `/mcp/inspector` unless `--no-inspector` is passed. You can:

- Connect to local server immediately (no configuration needed)
- Call tools, read resources, inspect prompts
- Preview MCP Apps views
- Enable protocol toggle to test ChatGPT Apps compatibility
- Copy client setup commands for external clients

Access it at `http://localhost:3000/mcp/inspector`.

## Environment Variables

- `$PORT` — Used if no `--port` flag
- `$HOST` — Used if no `--host` flag
- `$MCP_URL` — Set automatically to tunnel URL if `--tunnel` used; can be overridden for debugging

## Exit Codes

- `0` — Server started (never exits normally; press Ctrl+C to stop)
- `2` — Invalid arguments
- `1` — Startup failure

## Next Steps

- Test tools and views via Inspector
- When ready to deploy, run `mcp-use build`
- For deployment, see `06-mcp-use-deploy-and-cloud.md`
