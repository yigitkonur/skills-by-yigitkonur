# Build and Typecheck

*Read this to compile your server and verify types before deployment.*

## mcp-use build

Compiles the server and bundles views into `.mcp-use/build/`:

```bash
mcp-use build [options]
```

**Output directory:** `.mcp-use/build/` (portable, self-contained)

### Flags

- `--entry <path>` — Server entry module (default: inferred from `package.json#main`)
- `--mcp-dir <dir>` — Directory containing entry + `views/` folder
- `--views-dir <dir>` — Override views directory (default: `views/` or `<mcp-dir>/views/`)
- `--source-maps` — Emit source maps in output
- `--inline` — Embed view JS and CSS in MCP resources (instead of separate files)
- `--path <directory>` — Project root (default: current directory)

### Example

```bash
mcp-use build --source-maps
```

**Build is transpile-only — it never runs the TypeScript type checker.** There is deliberately no typecheck step in `mcp-use build`; run `mcp-use typecheck` as a separate script (e.g. `npm run typecheck && npm run build`) when type checking is required.

**Always runs:**
- TypeScript transpilation (types stripped, not checked)
- View bundling (if `views/` exists)

## mcp-use typecheck

Refreshes the project-root `mcp-env.d.ts` and runs your project's TypeScript compiler:

```bash
mcp-use typecheck [options] [-- <tsc options>]
```

### Flags

- `--entry <path>` — Server entry module
- `--mcp-dir <dir>` — Directory containing entry
- `--path <directory>` — Project root (default: current directory)
- `--` — Forward remaining flags to `tsc` (e.g., `mcp-use typecheck -- --strict`)

### Regenerated Files

- `mcp-env.d.ts` (project root, not under `.mcp-use/`) — Tool and prompt type definitions based on your server's schema

### Example

```bash
mcp-use typecheck -- --strict --noUnusedLocals
```

## Build output layout

```
.mcp-use/build/
├── index.js           # Compiled server entry (name from manifest.json#entryPoint)
├── manifest.json       # { buildId, entryPoint: "index.js", createdAt, views: {} }
└── views/              # (if views exist)
    ├── public/          # Copied static assets
    └── assets/
        ├── chart-<hash>.js    # Hashed filenames — not plain view.js/view.html
        └── form-<hash>.js
```

`mcp-env.d.ts` is **never** written into `.mcp-use/build/` — it only ever exists at the project root, refreshed there by `dev`/`typecheck`/`build`. Use `mcp-use start` to serve this build locally (it reads `manifest.json` to find the entry), or deploy it to Manufact Cloud or another runtime.

## Publishing view assets to a CDN

When `--inline` is not used, view JS/CSS/public assets are written as separate files under `.mcp-use/build/views/`. Set `$MCP_ASSETS_URL` to have the build rewrite each view's asset manifest to point at a CDN/static-hosting prefix instead of the server's own origin — `mcp-use build` logs `[mcp-use] MCP_ASSETS_URL set — publish <views-dir>/ at <prefix>` when it applies the rewrite. This is a build-time (and server-runtime, for the same-origin fallback) environment variable, not a CLI flag.

## CI/CD

Always run typecheck before build in CI:

```bash
npm run typecheck && npm run build
```

This catches type errors early and avoids deploying broken builds — `mcp-use build` alone does not check types.
