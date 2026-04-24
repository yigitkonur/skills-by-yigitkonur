# Local Dev Commands — `dev`, `build`, `start`, `generate-types`

These are the four commands you run against a local project directory, before anything touches the cloud. All four accept `-p, --path <path>` to target a project other than `cwd`. The three Next.js drop-in flags (`--mcp-dir`, auto-shims, env cascade) apply to `dev` and `build`; `start` also accepts `--mcp-dir`.

---

## `mcp-use dev`

Run the development server with auto-reload + inspector + optional tunnel.

### Verbatim `--help`

```
Usage: mcp-use dev [options]

Run development server with auto-reload and inspector

Options:
  -p, --path <path>    Path to project directory (default: cwd)
  --entry <file>       Path to MCP server entry file (relative to project)
  --widgets-dir <dir>  Path to widgets directory (relative to project)
  --mcp-dir <dir>      Folder holding the MCP entry + resources (e.g. 'src/mcp'
                       for Next.js apps)
  --port <port>        Server port (default: "3000")
  --host <host>        Server host (use 0.0.0.0 to listen on all interfaces)
                       (default: "0.0.0.0")
  --no-open            Do not auto-open inspector
  --no-hmr             Disable hot module reloading (use tsx watch instead)
  --tunnel             Expose server through a tunnel
  -h, --help           display help for command
```

### Option table

| Flag | Default | Purpose |
|---|---|---|
| `-p, --path <path>` | `cwd` | Project root to run from |
| `--entry <file>` | detected (`index.ts`, `src/index.ts`, `src/mcp/index.ts`) | Override server entry |
| `--widgets-dir <dir>` | auto-detected | Location of widgets for `ui://widget/...` resources |
| `--mcp-dir <dir>` | `src/mcp` when Next.js is detected | Folder that holds MCP entry + resources |
| `--port <port>` | `3000` | HTTP port |
| `--host <host>` | `0.0.0.0` | Bind address — `0.0.0.0` exposes on LAN |
| `--no-open` | opens by default | Suppress auto-opening the inspector browser tab |
| `--no-hmr` | HMR on | Switch from HMR to `tsx watch` full-process restart |
| `--tunnel` | off | Open a public tunnel to the local server |

### Use cases

1. **Plain start on a fresh project**
   ```bash
   npx -y @mcp-use/cli dev
   ```
2. **Different port + no auto-open (for a tmux pane)**
   ```bash
   mcp-use dev --port 4040 --no-open
   ```
3. **Next.js drop-in project with `src/mcp/`**
   ```bash
   mcp-use dev --mcp-dir src/mcp
   ```
4. **Expose to a mobile device via tunnel**
   ```bash
   mcp-use dev --tunnel --host 0.0.0.0
   ```
5. **Debugging a crash loop — disable HMR so stack traces are clean**
   ```bash
   mcp-use dev --no-hmr --entry src/server.ts
   ```

### Source cross-reference

- `libraries/typescript/packages/cli/src/index.ts` — command wiring for `dev`
- `libraries/typescript/packages/cli/src/utils/next-shims.ts` — Next.js detection + shims (v1.25.0+)

### Gotchas

- `.mcp-use/tool-registry.d.ts` is regenerated on server init, HMR, and widget file changes in dev. It's gitignored via the `.mcp-use` auto-append described in `config-files/00-overview.md`.
- When Next.js is detected, the CLI auto-shims `server-only`, `client-only`, `next/cache`, `next/headers`, `next/navigation`, `next/server`. If a widget transitively imports any of these, the **widget build fails fast** — the error explicitly names the offending module.
- Next.js env cascade (`.env.development.local` → `.env.local` → `.env.development` → `.env`) is loaded the same way `next dev` loads it, in dev only.

---

## `mcp-use build`

Compile TypeScript + widget bundles for production.

### Verbatim `--help`

```
Usage: mcp-use build [options]

Build TypeScript and MCP UI widgets

Options:
  -p, --path <path>    Path to project directory (default: cwd)
  --entry <file>       Path to MCP server entry file (relative to project)
  --widgets-dir <dir>  Path to widgets directory (relative to project)
  --mcp-dir <dir>      Folder holding the MCP entry + resources (e.g. 'src/mcp' for Next.js apps)
  --with-inspector     Include inspector in production build
  --inline             Inline all JS/CSS into HTML (required for VS Code MCP Apps)
  --no-inline          Keep JS/CSS as separate files (default)
  --no-typecheck       Skip TypeScript type checking (faster builds)
  -h, --help           display help for command
```

### Option table

| Flag | Default | Purpose |
|---|---|---|
| `-p, --path <path>` | `cwd` | Project root |
| `--entry <file>` | detected | Server entry override |
| `--widgets-dir <dir>` | auto-detected | Widgets source folder |
| `--mcp-dir <dir>` | `src/mcp` if Next.js detected | MCP entry + resources folder |
| `--with-inspector` | off | Bundle the inspector in prod output |
| `--inline` | off | Inline JS/CSS into HTML (required for VS Code MCP Apps) |
| `--no-inline` | default | Keep separate asset files (default) |
| `--no-typecheck` | typecheck on | Skip `tsc --noEmit` for faster local builds |

### Use cases

1. **Standard production build**
   ```bash
   mcp-use build
   ```
2. **VS Code MCP Apps compatible build (inline all assets)**
   ```bash
   mcp-use build --inline
   ```
3. **Speed up CI compile step — already typechecked elsewhere**
   ```bash
   mcp-use build --no-typecheck
   ```
4. **Next.js repo with MCP living in `src/mcp/`**
   ```bash
   mcp-use build --mcp-dir src/mcp
   ```
5. **Ship inspector with the prod build for QA**
   ```bash
   mcp-use build --with-inspector
   ```

### Source cross-reference

- `libraries/typescript/packages/cli/src/index.ts` — `build` command definition
- `libraries/typescript/packages/cli/src/utils/next-shims.ts` — Next.js shim resolution

### Gotchas

- As of v1.21.1, `mcp-use build` invokes `generateToolRegistryTypes()` before `tsc --noEmit`, so `.mcp-use/tool-registry.d.ts` exists when typecheck runs. Skipped when `NODE_ENV=production` is set (to preserve reproducible container builds; set it in your Dockerfile ENV).
- `--inline` produces a single HTML per widget and is required for VS Code MCP Apps since the client doesn't resolve external asset URLs in that harness.
- Widget build will fail fast if a widget transitively imports a Node-only or server-only module under the Next.js shim set.

---

## `mcp-use start`

Boot the production server against a prior `build` output.

### Verbatim `--help`

```
Usage: mcp-use start [options]

Start production server

Options:
  -p, --path <path>  Path to project directory (default: cwd)
  --entry <file>     Path to MCP server entry file (relative to project)
  --mcp-dir <dir>    Folder holding the MCP entry + resources (e.g. 'src/mcp' for Next.js apps)
  --port <port>      Server port (default: "3000")
  --tunnel           Expose server through a tunnel
  -h, --help         display help for command
```

### Option table

| Flag | Default | Purpose |
|---|---|---|
| `-p, --path <path>` | `cwd` | Project root |
| `--entry <file>` | detected | Override built entry to launch |
| `--mcp-dir <dir>` | `src/mcp` if Next.js | MCP folder location |
| `--port <port>` | `3000` | HTTP port |
| `--tunnel` | off | Expose via tunnel |

### Use cases

1. **Run the built server locally on port 3000**
   ```bash
   mcp-use build && mcp-use start
   ```
2. **Bind to a non-default port in a container**
   ```bash
   PORT=8080 mcp-use start --port 8080
   ```
3. **Preview the prod build behind a tunnel for a stakeholder demo**
   ```bash
   mcp-use build && mcp-use start --tunnel
   ```
4. **Start a Next.js drop-in build**
   ```bash
   mcp-use start --mcp-dir src/mcp
   ```
5. **Launch a custom entry after a multi-entry build**
   ```bash
   mcp-use start --entry dist/server-alt.js
   ```

### Source cross-reference

- `libraries/typescript/packages/cli/src/index.ts` — `start` command definition

### Gotchas

- `start` does **not** rebuild. If you haven't run `build`, it can't find the compiled entry.
- No `--host` flag on `start`; binds to `0.0.0.0` by default (unlike `dev`, there's no override).

---

## `mcp-use generate-types`

Manually regenerate `.mcp-use/tool-registry.d.ts`.

### Verbatim `--help`

```
Usage: mcp-use generate-types [options]

Generate TypeScript type definitions for tools (writes .mcp-use/tool-registry.d.ts)

Options:
  -p, --path <path>  Path to project directory (default: cwd)
  --server <file>    Server entry file (default: "index.ts")
  -h, --help         display help for command
```

### Option table

| Flag | Default | Purpose |
|---|---|---|
| `-p, --path <path>` | `cwd` | Project root |
| `--server <file>` | `index.ts` | Server entry file to introspect for tool signatures |

### Use cases

1. **Regenerate types after editing a tool schema (outside dev)**
   ```bash
   mcp-use generate-types
   ```
2. **Types from a non-default entry**
   ```bash
   mcp-use generate-types --server src/mcp/index.ts
   ```
3. **From a repo root targeting a subpackage**
   ```bash
   mcp-use generate-types -p packages/mcp-server
   ```
4. **CI: generate types before typecheck**
   ```bash
   mcp-use generate-types && tsc --noEmit
   ```
5. **Monorepo: regenerate every package's types**
   ```bash
   for dir in packages/mcp-*; do mcp-use generate-types -p "$dir"; done
   ```

### Source cross-reference

- `libraries/typescript/packages/cli/src/index.ts` — `generate-types` command wiring
- `libraries/typescript/packages/mcp-use/src/server/*` — `generateToolRegistryTypes()` implementation (also called from `dev` + `build`)

### Gotchas

- Writes unconditionally to `.mcp-use/tool-registry.d.ts`. If your project has no `.mcp-use/` yet, it's created.
- Silent no-op in `dev`/`build` when `NODE_ENV=production`; `generate-types` itself ignores `NODE_ENV` — always writes.
- Default `--server index.ts` does **not** match the Next.js drop-in convention (`src/mcp/index.ts`); pass `--server src/mcp/index.ts` explicitly when running in a Next.js project.
