# check-mcp-use-version.sh

**What it checks:** Installed mcp-use/@mcp-use/cli versions; compares against npm dist-tags; detects v1 vs v2 by the package's own exports map (the `"./server"` export key exists only in v1).

**When to run:** Before starting work on an existing MCP server, or when unsure if your CLI is v1 or v2.

## Usage

```bash
bash scripts/check-mcp-use-version.sh
```

## Output interpretation

### Success indicators (v2)

```
✓ mcp-use found at: ./node_modules/.bin/mcp-use
✓ mcp-use CLI: v2 (version 4.x or later)
Local package.json mcp-use: ^2.0.0-beta.66
  → Detected v2 package (root MCPServer export, ESM only, no "./server")
```

### Warning indicators (possibly v1)

```
✓ mcp-use CLI: v1 (version 3.x or earlier)
  → Detected v1 package ("./server" export key present)
Local package.json mcp-use: ^1.34.5
```

### npm dist-tags

```
mcp-use npm tags:
  latest: 1.34.5 (v1 era)
  beta: 2.0.0-beta.66 (v2)
  legacy-v1: 1.x (v1 maintenance)
```

## What v1 vs v2 means

| Aspect | v1 | v2 |
|--------|----|----|
| **Import** | `import { MCPServer } from "mcp-use/server"` | `import { MCPServer } from "mcp-use"` |
| **ESM** | CommonJS + ESM | ESM only |
| **Node** | `^20.19.0 \|\| >=22.12.0` | `>=22.22.2` |
| **CLI** | 3.x | 4.x |
| **zod** | v3 | v4 |

## Next steps

If v1:
```bash
npm install mcp-use@beta  # mcp-use's package.json depends on @mcp-use/cli@4.0.0-beta.15; the CLI comes in transitively
npx mcp-use typecheck  # generates mcp-env.d.ts; replaces v1's `generate-types` (not a v2 command)
```

If v2:
```bash
npm run dev  # Works as-is
```
