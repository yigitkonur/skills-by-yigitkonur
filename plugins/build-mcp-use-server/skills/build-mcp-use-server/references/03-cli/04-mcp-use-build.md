# `mcp-use build`

Produces the deployable artifact. Compiles TypeScript, bundles each widget into a standalone HTML file, hashes assets, minifies, and writes `dist/` plus a build manifest.

## Usage

```bash
mcp-use build [options]
```

Entry is not positional in `@mcp-use/cli@3.1.2`. Use `--entry <file>` or `--mcp-dir <dir>` for non-default layouts.

## Flags

| Flag | Description | Default |
|---|---|---|
| `-p, --path <path>` | Project directory | `.` |
| `--entry <file>` | MCP server entry file, relative to project | auto-detected |
| `--widgets-dir <dir>` | Widgets/resources directory | `resources` |
| `--mcp-dir <dir>` | Folder holding MCP entry plus resources; skips TS transpile | — |
| `--with-inspector` | Bundle the Inspector into the build (otherwise `/inspector` is dev-only) | `false` |
| `--inline` | Inline all JS/CSS into widget HTML | default path |
| `--no-inline` | Keep JS/CSS as separate files | `false` |
| `--no-typecheck` | Skip TS type-checking; transpile only (v1.21.5+) | `false` |

`--no-typecheck` is for CI where `tsc --noEmit` runs as a separate step. Don't use it as a long-term workaround for type errors — fix them.

## Build pipeline

1. Bundle widgets from `resources/*.tsx` or `resources/<name>/widget.tsx`.
2. Generate `.mcp-use/tool-registry.d.ts` when a server entry is found.
3. Compile TypeScript to `dist/` unless `--mcp-dir` mode is active.
4. Type-check unless `--no-typecheck` or `--mcp-dir` is used.
5. Copy `public/` to `dist/public` and emit `dist/mcp-use.json`.

## Output

| Path | Content |
|---|---|
| `dist/index.js` (or `dist/server.js`) | Compiled server entry. |
| `dist/resources/widgets/<name>/index.html` | Widget bundle output. |
| `dist/mcp-use.json` | Build manifest read by `mcp-use start` and `mcp-use deploy`. |

## `dist/mcp-use.json` shape

```json
{
  "includeInspector": true,
  "buildTime": "2025-02-04T10:30:00.000Z",
  "buildId": "a1b2c3d4e5f6g7h8",
  "entryPoint": "dist/index.js",
  "widgets": {
    "weather-display": {
      "title": "Weather Display",
      "description": "Shows weather information",
      "props": { "type": "object", "properties": { "city": { "type": "string" } } }
    }
  },
  "tunnel": { "subdomain": "my-server-abc123" }
}
```

## When to run

| Scenario | Command |
|---|---|
| Local prod parity check | `mcp-use build && mcp-use start` |
| CI deploy artifact | `mcp-use build` after `tsc --noEmit` |
| Static asset deploy (CDN, Supabase Storage) | Set `MCP_URL` and `MCP_SERVER_URL`, then run `mcp-use build` |
| Internal QA with Inspector | `mcp-use build --with-inspector` |

## Asset URL gotcha

Widget bundles bake their asset paths at build time. `MCP_URL` controls the widget bundle base URL; `MCP_SERVER_URL` is injected for public asset/server references. For static or remote widget hosting, set both explicitly and verify the generated `dist/resources/widgets/<name>/index.html`.

```bash
# Wrong — widgets break in prod
mcp-use build

# Right — provide the public asset origin
MCP_URL=https://static.example.com/widgets \
MCP_SERVER_URL=https://mcp.example.com \
mcp-use build
```

`MCP_URL` and `MCP_SERVER_URL` must match the hosting layout you will actually serve.

## Build profiles

| Profile | Flags | Use |
|---|---|---|
| Production (default) | none | Public deploys |
| Debug / QA | `--with-inspector` | Internal staging where you need `/inspector` |
| CI fast path | `--no-typecheck` (paired with separate `tsc --noEmit`) | Speed up CI |

## Examples

```bash
mcp-use build
mcp-use build --with-inspector
mcp-use build --no-typecheck
mcp-use build --entry src/server.ts
mcp-use build -p ./packages/api
MCP_URL=https://static.example.com/widgets MCP_SERVER_URL=https://mcp.example.com mcp-use build
```

## See also

- `05-mcp-use-start.md` — runs the artifact this command produces
- `06-mcp-use-deploy.md` — uploads the artifact to Manufact Cloud
- `../02-setup/09-env-vars.md` — `MCP_SERVER_URL` vs `MCP_URL`
