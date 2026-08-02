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

**Always runs:**
- TypeScript compilation (no `--no-typecheck` flag)
- View bundling (if `views/` exists)

## mcp-use typecheck

Refreshes `.mcp-use/mcp-env.d.ts` and runs your project's TypeScript compiler:

```bash
mcp-use typecheck [options] [-- <tsc options>]
```

### Flags

- `--entry <path>` — Server entry module
- `--mcp-dir <dir>` — Directory containing entry
- `--path <directory>` — Project root (default: current directory)
- `--` — Forward remaining flags to `tsc` (e.g., `mcp-use typecheck -- --strict`)

### Regenerated Files

- `.mcp-use/mcp-env.d.ts` — Tool and prompt type definitions based on your server's schema

### Example

```bash
mcp-use typecheck -- --strict --noUnusedLocals
```

## Build output layout

```
.mcp-use/build/
├── index.js          # Compiled server
├── mcp-env.d.ts      # Type definitions
└── views/            # (if views exist)
    ├── chart/
    │   ├── view.js
    │   └── view.html
    └── form/
        ├── view.js
        └── view.html
```

Use `mcp-use start` to serve this build locally, or deploy it to Manufact Cloud or another runtime.

## CI/CD

Always run typecheck before build in CI:

```bash
npm run typecheck && npm run build
```

This catches type errors early and avoids deploying broken builds.
