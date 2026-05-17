# Prerequisites

Verify the toolchain before scaffolding or installing dependencies.

## Runtime and tools

| Requirement | Minimum | Recommended | Why |
|---|---|---|---|
| Node.js | 18.x | 22 LTS | ESM `mcp-use/server` exports require Node 18+; Node 22 LTS matches current examples and ships with the smoothest fetch/AbortSignal behavior. |
| Package manager | npm 9 | npm 10 / pnpm 9 / yarn 4 | Any of the three work. Lockfiles persist across CI. |
| TypeScript | 5.0 | 5.5+ | Required for `module: NodeNext` and `satisfies` patterns used in templates. |

Verify:

```bash
node --version   # v18.x or higher (v22.x.x preferred)
npm --version    # 9.x.x or higher
```

## Required dependency matrix

| Package | Required for | Where to install |
|---|---|---|
| `mcp-use` | Every server | `dependencies` |
| `zod` (`^4.0.0`) | Tool / resource / prompt schemas | `dependencies` — peer dep, not auto-installed |
| `@mcp-use/cli` | `dev` (HMR), `build`, `start`, `deploy`, `generate-types` | `devDependencies` |
| `typescript` | Compilation | `devDependencies` |
| `@types/node` | Node ambient types | `devDependencies` |
| `tsx` | Optional ad-hoc `tsx src/server.ts` runs | `devDependencies` |

## Add-ons by feature

Install only when you need the feature.

| Feature | Extra packages |
|---|---|
| React widgets (MCP Apps / ChatGPT Apps) | `@mcp-use/react`, `react`, `react-dom`, `@types/react`, `@types/react-dom` |
| Redis session store / stream manager | `redis` |
| dotenv-loaded config | `dotenv` |
| Edge / serverless deploys | none — `mcp-use/server` ships an edge handler |

## `package.json` non-negotiables

```json
{
  "type": "module"
}
```

Without `"type": "module"`, imports from `mcp-use/server` fail with `SyntaxError: Unexpected token export`.

## Quick install

Fresh manual project:

```bash
npm init -y
npm install mcp-use zod
npm install -D @mcp-use/cli typescript @types/node tsx
```

Add React widgets:

```bash
npm install @mcp-use/react react react-dom
npm install -D @types/react @types/react-dom
```

For scaffold-driven setup, skip the manual install and read `02-scaffold-with-create-mcp-use-app.md`.

**Canonical doc:** https://manufact.com/docs/typescript/server/quickstart
