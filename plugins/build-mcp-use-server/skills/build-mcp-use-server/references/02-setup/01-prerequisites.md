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

`zod@4.x` is **required** (peer dependency, not auto-installed). The framework uses its `StandardSchemaWithJSON` interface for validation; v3 is incompatible.

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
- **`@mcp-use/cli@4.0.0-beta.15`** — scaffolder `create-mcp-use-app@2.0.0-beta.14`
- **`@mcp-use/inspector@20.0.0-beta.58`** — auto-included by CLI
- **Node peer dependencies:** `@modelcontextprotocol/server@2.0.0`, `@modelcontextprotocol/client@2.0.0`, `@modelcontextprotocol/core@2.0.0` (shipped by `mcp-use`)

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

await server.listen(3000);
```

```bash
npm run dev  # or npx @mcp-use/cli@4.0.0-beta.15 dev
```

## For React views (MCP Apps)

Add to manual setup:

```bash
npm install react@19 react-dom@19
npm install -D @types/react @types/react-dom
```

The scaffolder (`--template mcp-apps`) pre-configures these.

## TypeScript 5.5+

ESM `module: "NodeNext"` and `.satisfies` patterns require TS 5.0+; 5.5+ recommended.

```bash
npm install -D typescript@latest
```
