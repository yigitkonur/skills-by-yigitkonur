# Prerequisites

*Read this to verify the development environment before scaffolding.*

## Node.js and ESM

- **Node ≥ 22** (minimum 22.22.2). ESM required; CJS not supported.
- **`"type": "module"` in `package.json`** — without it, imports fail with `SyntaxError: Unexpected token export`.

Verify:
```bash
node --version   # ≥22.22.2
```

## Package manager

Any of npm 9+, pnpm 9+, or Bun work. Reproducible builds via lockfile (git commit it).

## Zod v4 (Standard Schema)

Tool/resource/prompt schemas take any `StandardSchemaWithJSON`-conformant library (zod v4, ArkType, Valibot, ...) — zod v4 is the one used throughout this skill and the scaffolded templates. It is **not a dependency of `mcp-use`** (not listed in its `dependencies` or `peerDependencies`); install it explicitly in your own project. Zod v3 does not implement `StandardSchemaWithJSON` and is incompatible.

```bash
npm install zod@4
```

## Exact version pins (v2 stable)

Pin these exact versions in new projects:

```bash
npm install mcp-use@2.0.0-beta.66 zod@4
npm install -D @mcp-use/cli@4.0.0-beta.15 typescript @types/node
```

- **`mcp-use@2.0.0-beta.66`** — use npm dist-tag `@beta` for updates
- **`@mcp-use/cli@4.0.0-beta.15`** — thin compatibility bin; `mcp-use` itself owns the real CLI (`mcp-use dev/build/start/...`)
- **`@mcp-use/inspector@20.0.0-beta.58`** — regular dependency of `mcp-use`, resolved automatically; not something you install separately
- **Regular (non-peer) dependencies shipped by `mcp-use`:** `@modelcontextprotocol/server@2.0.0`, `@modelcontextprotocol/client@2.0.0`, `@modelcontextprotocol/core@2.0.0`, `hono@^4.12.27`, `jose@^6.1.3` — these install automatically with `mcp-use`, no separate `npm install` needed
- **Actual peer dependencies (all optional):** `@mcp-use/client@^2.0.0-alpha.0`, `react@^19.0.0`, `react-dom@^19.0.0` — only needed for MCP Apps / React views (see "For React views" below)

## Quick scaffolded setup (recommended)

```bash
npm create mcp-use-app@2.0.0-beta.14 my-server --template mcp-server --install
cd my-server
npm run dev
```

See `02-scaffold-with-create-mcp-use-app.md` for template options.

## Manual setup (from scratch)

For a blank project without scaffolding:

```bash
mkdir my-server && cd my-server
npm init -y
npm install mcp-use@2.0.0-beta.66 zod@4
npm install -D @mcp-use/cli@4.0.0-beta.15 typescript @types/node
```

Add `"type": "module"` to `package.json`, then create `index.ts`:

```typescript
import { MCPServer } from "mcp-use";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
});

export default server;
```

Run the CLI directly (the blank `npm init -y` project does not have a `dev` script yet):

```bash
npx mcp-use@2.0.0-beta.66 dev --entry index.ts
```

The CLI imports the default-exported `MCPServer` and owns the HTTP listener. Do not call `server.listen()` in this CLI-managed entry.

## For React views (MCP Apps)

Add to manual setup:

```bash
npm install react@19 react-dom@19
npm install -D @types/react @types/react-dom
```

The scaffolder (`--template mcp-apps`) pre-configures these.

## TypeScript

Shipped `create-mcp-use-app` templates pin `typescript@^7.0.2` — install a matching major version, not an older 5.x line:

```bash
npm install -D typescript@^7
```

`module`/`moduleResolution: "NodeNext"` and the template's `target: "ES2024"` need a current TypeScript; do not pin below TS 7 for new projects. See `07-tsconfig-and-types.md` for the full shipped `tsconfig.json`.
