# Packages and Imports

The v1→v2 split is a packaging change, not a protocol change. Most of the rewrite is mechanical import-line edits.

## The split

| v1 (single package) | v2 (split packages) | Purpose |
|---|---|---|
| `@modelcontextprotocol/sdk` | `@modelcontextprotocol/server` | `McpServer`, stdio transport, registration APIs, protocol errors, shared types |
| | `@modelcontextprotocol/client` | `Client`, client transports, middleware |
| | `@modelcontextprotocol/node` | `NodeStreamableHTTPServerTransport` (HTTP for Node) |
| | `@modelcontextprotocol/express` | `createMcpExpressApp`, Express adapter |
| | `@modelcontextprotocol/hono` | `createMcpHonoApp`, Hono adapter (new in v2) |
| | future/verified transition packages | Auth or meta-package shims, only if published for the target alpha |

As of npm verification on 2026-05-09, `@modelcontextprotocol/core`, `@modelcontextprotocol/sdk@2.0.0-alpha.2`, and `@modelcontextprotocol/server-auth-legacy` are not published. Do not plan around those packages unless the target alpha's npm registry state or changelog confirms they exist.

## Naming pitfall

`@modelcontextprotocol/hono` (official, alpha.2) is **not** the same as `@hono/mcp` (separate community package maintained by the Hono team). Use `@modelcontextprotocol/hono` for SDK-coherent v2 work; `@hono/mcp` is for users who want the Hono team's MCP integration independent of the official SDK split.

## Import rewriter

```typescript
// ─── v1 ───
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { WebStandardStreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp/webStandard.js";
import { createMcpExpressApp } from "@modelcontextprotocol/sdk/server/express.js";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import { McpError, ErrorCode } from "@modelcontextprotocol/sdk/types.js";

// ─── v2 (full migration, direct package imports) ───
import { McpServer, StdioServerTransport } from "@modelcontextprotocol/server";
import { NodeStreamableHTTPServerTransport } from "@modelcontextprotocol/node";
import { WebStandardStreamableHTTPServerTransport } from "@modelcontextprotocol/server";
import { createMcpExpressApp } from "@modelcontextprotocol/express";
import { Client, StdioClientTransport, StreamableHTTPClientTransport } from "@modelcontextprotocol/client";
import { ProtocolError, ProtocolErrorCode } from "@modelcontextprotocol/server";

// ─── v2 (meta-package shim, transitional, only if published) ───
// Same import lines as v1 — a verified meta-package would re-export them under v2 internals.
```

## tsconfig changes

```jsonc
// v1 — single package with subpath exports requires Node-style resolution
{
  "compilerOptions": {
    "module": "Node16",          // or "NodeNext"
    "moduleResolution": "Node16" // or "NodeNext"
  }
}

// v2 — same settings work; .js extensions in subpaths are no longer required
// because top-level imports are re-exported. Keep Node16/NodeNext for ESM correctness.
```

`"type": "module"` in `package.json` is **mandatory** for v2 — it's ESM-only. If your v1 server is CommonJS, this is the highest-risk change in the migration; the failure mode is silent (extension resolution differs) and surfaces at runtime.

## package.json before/after

```jsonc
// v1
{
  "type": "module",  // optional in v1
  "engines": { "node": ">=18" },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.27.0",
    "express": "^5.0.0",
    "zod": "^3.23.0"
  }
}

// v2 (full migration)
{
  "type": "module",  // required
  "engines": { "node": ">=20" },
  "dependencies": {
    "@modelcontextprotocol/server": "2.0.0-alpha.2",
    "@modelcontextprotocol/client": "2.0.0-alpha.2",
    "@modelcontextprotocol/node": "2.0.0-alpha.2",
    "@modelcontextprotocol/express": "2.0.0-alpha.2",
    "express": "^5.0.0",
    "zod": "^4.0.0"  // v4 only
  }
}
```

Pin alpha versions exactly (no `^`) — alphas can ship breaking changes between any two patches.

## Common rewrite mistakes

- **Mixing v1 and v2 packages** in the same module graph without the meta-package. Two `McpServer` classes from two packages don't interoperate. TypeScript will accept the duplicate types; `instanceof` checks and class identity break at runtime.
- **Forgetting `WebStandardStreamableHTTPServerTransport` moved to `@modelcontextprotocol/server`** (in v1 it's a deep subpath of the SDK). Don't import it from `/node` — that package only has the Node-specific transport.
- **Assuming a meta-package shim exists** without verifying the target alpha. If the shim is unpublished, direct package imports are the only v2 path.
- **Installing `@hono/mcp` instead of `@modelcontextprotocol/hono`**. They are different packages — the SDK adapter exports `createMcpHonoApp`, the community one does not.
