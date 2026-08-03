# Route handler placement & config

*Read this when setting up file paths, route positions, and Next.js config for embedded MCP.*

## Embedded route handler placement

The route must be an **optional catch-all** at `app/api/mcp/[[...path]]/route.ts` (or `.js`) because mcp-use serves the MCP endpoint and nested view assets from the same subtree. A non-catch-all route (`app/api/mcp/route.ts`) only matches the exact `basePath` and 404s on view asset requests. Under `basePath: "/api/mcp"`, the mounted handler serves:
- `GET`/`POST`/`DELETE` `/api/mcp` → the MCP endpoint (`server.fetch`)
- `OPTIONS /api/mcp` → CORS preflight
- `GET /api/mcp/_mcp-use/views/<name>/...` → compiled view JS/CSS bundles (production)
- `GET /api/mcp/_mcp-use/public/...` → public view assets

There is no built-in `/inspector` route under the Next.js embedded topology. `withMcpUse`/`createNextHandler` do not mount `@mcp-use/inspector` — that only happens for the standalone `mcp-use dev`/`mcp-use start --with-inspector` CLI listener. Test an embedded server with the standalone `@mcp-use/inspector` CLI package pointed at the deployed URL (see Verification below), not a same-origin `/inspector` path.

## Server entry file

The server file can be at the project root or `src/`. If your `@/*` alias maps only to `src/*`, place the server under `src/mcp-server.ts` or move it under `src/`. Relative imports in the route handler must resolve correctly.

```typescript app/api/mcp/[[...path]]/route.ts
import server from "@/mcp-server";  // or "@/src/mcp-server" if src-only alias
import { createNextHandler } from "mcp-use/next";

export const { GET, POST, DELETE, OPTIONS } = createNextHandler(server);
```

## withMcpUse options in next.config.ts

`withMcpUse` returns a `Promise` — `next.config.ts` must `export default` that promise directly (Next.js awaits a config module's default export).

```typescript next.config.ts
import { withMcpUse } from "mcp-use/next";

const nextConfig = {
  // your other config
};

export default withMcpUse(nextConfig, {
  entry: "./mcp-server.ts",          // relative to project root
  basePath: "/api/mcp",               // must match route handler's nested path
  // Optional — only needed for a src-root or non-default layout:
  mcpDir: "mcp",                      // treat "mcp/" as the source root for entry + views/
  viewsDir: "mcp/views",              // explicit views dir, relative to project root
  projectRoot: process.cwd(),         // default process.cwd()
});
```

| Option | If omitted | Notes |
|---|---|---|
| `entry` | CLI entry discovery runs at the project root (or `mcpDir`, if set): first existing file wins from `src/index.ts`, `src/index.tsx`, `src/server.ts`, `src/server.tsx`, `index.ts`, `index.tsx`, `server.ts`, `server.tsx`. | Path to the server export, relative to `projectRoot`. The shipped type annotates a conventional default of `"mcp/server.ts"`, but `withMcpUse` only forwards `--entry` when this option is explicitly set — omitting it falls through to the discovery list above. |
| `mcpDir` | No `--mcp-dir` flag is forwarded; the CLI treats `projectRoot` itself as the source root. | Conventional MCP source directory containing the entry and `views/`. Not defaulted to `"mcp"` automatically — set it explicitly to use that layout. |
| `viewsDir` | No plain `views/` directory at the project root (or `<mcpDir>/views` if `mcpDir` is set) is used. | Explicit views directory, relative to `projectRoot`. |
| `basePath` | `"/api/mcp"` | Must be a concrete absolute path (not `/` alone, no scheme); must match the route handler's nested path. |
| `projectRoot` | `process.cwd()` | Next.js project root. |

There is **no `src/views` auto-detection**. Most Next.js drop-in examples set `entry` explicitly (e.g. `./mcp-server.ts` at the project root) and skip `mcpDir`/`viewsDir` entirely, relying on plain `views/` at the root for view discovery.

## View directory structure

When using MCP Apps (optional), place views under `views/` at the project root (or under `<mcpDir>/views` if `mcpDir` is set):
```
views/
├── my-view/
│   └── view.tsx
└── another-view/
    └── view.tsx
```

Each view is an MCP App component. See references/18-mcp-apps/server-surface/02-register-views-and-folder-conventions.md for registration patterns.

## Build pipeline

`withMcpUse` runs `mcp-use build` as a child process (via `node <cli-entry> build [--entry ...] [--mcp-dir ...] [--views-dir ...]`) every time Next evaluates `next.config` — for both `next dev` and `next build`. The build compiles views with Vite into `.mcp-use/build/views/`, writes a manifest at `.mcp-use/build/manifest.json`, and adds that directory to Next's `outputFileTracingIncludes` for the route so serverless bundling includes the compiled assets. `createNextHandler` reads that manifest lazily on first request and calls `server.__primeViews()` before invoking `server.fetch`.

## CORS headers

`withMcpUse` also augments the Next.js `headers()` config for the route's `basePath` (merging into an existing rule for the same source if present) with:

| Header | Value |
|---|---|
| `Access-Control-Allow-Origin` | `*` |
| `Access-Control-Allow-Methods` | `GET, POST, DELETE, OPTIONS` |
| `Access-Control-Allow-Headers` | `Authorization, Content-Type, Accept, Mcp-Protocol-Version, Mcp-Method, Mcp-Name, Mcp-Session-Id, Last-Event-ID` |
| `Access-Control-Expose-Headers` | `Mcp-Session-Id` |

No manual CORS configuration is needed for the MCP route; the `OPTIONS` handler exported by `createNextHandler` answers preflight requests.

## Restart after changes

After modifying the MCP server (`mcp-server.ts`) or any view file, restart `next dev`. Changes to tools and resources are picked up automatically on next dev start; changes to view code trigger a rebuild.
