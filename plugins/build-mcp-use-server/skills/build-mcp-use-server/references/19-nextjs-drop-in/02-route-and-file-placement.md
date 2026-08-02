# Route handler placement & config

*Read this when setting up file paths, route positions, and Next.js config for embedded MCP.*

## Embedded route handler placement

The catch-all route must be at `app/api/mcp/[[...path]]/route.ts` (or `.js`). This catches all subpaths under `/api/mcp`:
- `GET /api/mcp` → handler
- `POST /api/mcp` → handler
- `DELETE /api/mcp/session` → handler
- `OPTIONS /api/mcp` → handler
- `GET /api/mcp/inspector` → MCP app views, served by `withMcpUse`

## Server entry file

The server file can be at the project root or `src/`. If your `@/*` alias maps only to `src/*`, place the server under `src/mcp-server.ts` or move it under `src/`. Relative imports in the route handler must resolve correctly.

```typescript app/api/mcp/[[...path]]/route.ts
import server from "@/mcp-server";  // or "@/src/mcp-server" if src-only alias
import { createNextHandler } from "mcp-use/next";

export const { GET, POST, DELETE, OPTIONS } = createNextHandler(server);
```

## withMcpUse options in next.config.ts

```typescript next.config.ts
import { withMcpUse } from "mcp-use/next";

const nextConfig = {
  // your other config
};

export default withMcpUse(nextConfig, {
  entry: "./mcp-server.ts",          // relative to project root
  basePath: "/api/mcp",               // must match route handler's nested path
  // Optional:
  viewsDir: "src/views",              // default is src/views if src/ exists, else views/
});
```

**entry** — Path to the server export (relative to project root, ESM).
**basePath** — The public MCP endpoint prefix; must match the route handler route.
**viewsDir** — Where MCP App views live (relative to project root). If unset, auto-detects `src/views` or `views/`.

## View directory structure

When using MCP Apps (optional), place views in the configured or detected views directory:
```
src/views/
├── my-view/
│   └── view.tsx
└── another-view/
    └── view.tsx
```

Each view is an MCP App component. See references/18-mcp-apps/02-register-views-and-folder-conventions.md for registration patterns.

## Configuration auto-detection

`withMcpUse` auto-detects views in `src/views` if it exists; otherwise looks for `views/`. To use a different location, set `viewsDir` explicitly.

The v2 build pipeline compiles views to `.mcp-use/build/views/` during `next build`. All assets are served by the Next.js route handler.

## Restart after changes

After modifying the MCP server (`mcp-server.ts`) or any view file, restart `next dev`. Changes to tools and resources are picked up automatically on next dev start; changes to view code trigger a rebuild.
