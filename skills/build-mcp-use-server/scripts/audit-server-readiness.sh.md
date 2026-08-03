# audit-server-readiness.sh

**What it checks:** v2 MCP server readiness across 7 dimensions: ESM config, root MCPServer import, zod v4, OAuth setup, views directory, tool outputSchema presence, and build artifacts.

**When to run:** Before first deploy, or after major server changes.

## Usage

```bash
cd your-mcp-server
bash scripts/audit-server-readiness.sh
```

(Script must be run in the root directory of an mcp-use project with `package.json` present.)

## Output interpretation

### Section-by-section checklist

| Section | Pass signs | Warning signs | Failure signs |
|---------|-----------|---------------|---------------|
| **ESM** | `"type": "module"` in package.json | — | Missing ESM config |
| **mcp-use version** | `2.x` range in `package.json` | `1.x` or unresolved (e.g. still says `beta`) | — |
| **zod** | `^4.` | Not v4 | — |
| **Entry point** | `index.ts` or `src/index.ts` found | — | No entry file |
| **Root import** | `import { MCPServer } from "mcp-use"` | `from "mcp-use/server"` (v1) | — |
| **views/** | Directory + `view.tsx` files | Directory missing (OK for tools-only) | — |
| **outputSchema** | Tools have `outputSchema` | No outputSchema (OK if no views) | — |
| **OAuth** | `oauth:` config present (if needed) | Missing (OK for public servers) | — |
| **Build** | `.mcp-use/build/index.js` present | Directory missing or no `index.js`; run `mcp-use build` | — |
| **mcp-env.d.ts** | File exists at project root | Missing at project root; run `mcp-use typecheck` | — |

### Example: passing v2 server

```
✓ ESM-only ("type": "module")
✓ mcp-use v2 (2.x)
✓ zod v4 (correct)
✓ Entry file: index.ts
✓ Root MCPServer import (✓ v2)
✓ views/ directory with 2 view file(s)
✓ Found 5 tool(s) defined
✓ 4 tool(s) with outputSchema (used by views)
✓ .mcp-use/build/ directory exists
✓ Build output present (.mcp-use/build/index.js)
✓ mcp-env.d.ts generated at project root (tool types for views)

✓ Pass: 11
```

### Example: server needing fixes

```
✗ Not ESM. Add "type": "module" to package.json
⚠ mcp-use may be v1. Verify: npm list mcp-use
⚠ zod not v4. Add: npm install zod@^4
✗ Found mcp-use/server import (v1 pattern). Change to: import { MCPServer } from "mcp-use"
⚠ No .mcp-use/build/. Run: mcp-use build

✓ Pass: 5
⚠ Warnings: 2
✗ Failures: 2

Fix failures above before deploying.
```

## Common fixes

| Issue | Fix |
|-------|-----|
| `Not ESM` | Add `"type": "module"` to `package.json` |
| `mcp-use/server import` | Change: `import { MCPServer } from "mcp-use"` |
| `No .mcp-use/build/index.js` | Run: `npm run build` or `mcp-use build` |
| `No mcp-env.d.ts at project root` | Run: `npm run typecheck` or `mcp-use typecheck` |
| `Deprecated helpers` | Replace `text(...)` with `{ content: [...], structuredContent: ... }` |

## Exit codes

- `0` — Ready to deploy (pass + warnings only)
- `1` — Failures detected; fix before deploy
