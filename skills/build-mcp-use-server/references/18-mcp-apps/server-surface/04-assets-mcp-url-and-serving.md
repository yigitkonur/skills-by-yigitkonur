# Assets, MCP_URL, and MCP_ASSETS_URL

*Read this when you need to serve static assets, configure asset URLs for production, or understand the Vite build pipeline.*

The framework serves compiled view assets and public files through two URL namespaces. Environment variables `MCP_URL` and `MCP_ASSETS_URL` control asset rewriting for production deployments.

## Asset Serving Routes

The MCP server exposes these routes under the configured `basePath` (default `/mcp`):

| Route | Purpose | Source |
|-------|---------|--------|
| `/{basePath}/_mcp-use/views/<name>/<asset>` | Compiled view JS/CSS | `.mcp-use/build/views/<name>/` |
| `/{basePath}/_mcp-use/public/<asset>` | Static files | `public/` directory |
| `/{basePath}/inspector` | Inspector UI | Automounted in dev; optional in production |

## MCP_URL Environment Variable

`MCP_URL` is the public origin of your MCP server. The framework uses this to populate the CSP `connectDomains` for views (so they can reach back to the server).

```bash
# Local development
MCP_URL=http://localhost:3000

# Staged deployment
MCP_URL=https://staging.example.com

# Production
MCP_URL=https://myserver.example.com
```

**How it affects CSP:**
- Automatically appended to view resource's `_meta.ui.csp.connectDomains`
- Allows views to fetch from the server via `fetch()`, XHR, or WebSocket
- Set by `mcp-use dev` automatically if not already set; must be explicit in production

## MCP_ASSETS_URL Environment Variable

`MCP_ASSETS_URL` rewrites compiled view asset paths for serving from a separate origin (CDN, static host, etc.). When set, relative paths like `assets/index-ABC123.js` become full URLs.

```bash
# Dev (omit or set to server origin)
MCP_ASSETS_URL=http://localhost:3000

# Production with CDN
MCP_ASSETS_URL=https://cdn.example.com/mcp-assets

# Production with Supabase static bucket
MCP_ASSETS_URL=https://project.supabase.co/storage/v1/object/public/mcp-views
```

**Build-time rewriting:**
- `mcp-use build` outputs relative asset paths (e.g., `assets/index-ABC123.js`)
- At runtime, the framework rewrites these to full URLs if `MCP_ASSETS_URL` is set
- If omitted, paths are resolved relative to the server origin

## Dev Build Pipeline

During `mcp-use dev`:

1. **Vite watches** `views/` directory
2. **Origin-absolute paths** emitted (e.g., `/src/views/product-search/view.tsx?import`)
3. **Vite dev server** serves compiled chunks via WebSocket (HMR)
4. **Fast Refresh** enabled (hot-reload on save, preserves React state)

No asset rewriting in dev; Vite handles URL resolution automatically.

## Production Build Output

After `mcp-use build`:

```bash
.mcp-use/build/views/
├── product-search/
│   ├── index.html              # Synthesized; links to assets below
│   ├── assets/
│   │   ├── index-ABC123DEF.js  # Minified view module
│   │   └── index-XYZ789.css    # Aggregated styles
└── dashboard/
    └── ...
```

**Asset paths in HTML:**
```html
<!-- Default (external paths, rewritten at runtime) -->
<script src="assets/index-ABC123DEF.js" type="module"></script>
<link rel="stylesheet" href="assets/index-XYZ789.css">

<!-- With --inline flag -->
<script type="module">(minified source)</script>
<style>(aggregated CSS)</style>
```

## --inline vs --external Build Flags

```bash
# External (default): assets served separately
mcp-use build
# Output: relative asset paths, rewritten via MCP_ASSETS_URL

# Inline: embed JS/CSS in HTML
mcp-use build --inline
# Output: minified source in <script type="module"> + <style>
```

**When to use inline:**
- Small views (< 50 KB minified)
- Assets cannot be cached separately
- Deployment prefers monolithic bundles

**When to use external:**
- Large views or many views (browser caches assets)
- Assets served from CDN
- Multi-view server (shared asset caching)

## Public Assets (public/ directory)

Place static files in `public/`:

```
my-server/
├── public/
│   ├── logo.svg
│   ├── icons/
│   │   └── star.png
│   └── data.json
```

Access from views via `getPublicBaseUrl()`:

```typescript
import { getPublicBaseUrl } from "mcp-use/react";

export default function MyView() {
  const publicUrl = getPublicBaseUrl();
  return <img src={`${publicUrl}/logo.svg`} alt="Logo" />;
}
```

**Served at:** `/{basePath}/_mcp-use/public/<asset>`

## Configuration Precedence

| Variable | Set By | Behavior |
|----------|--------|----------|
| `MCP_URL` | User or `mcp-use dev` | Server's public origin (appended to CSP connectDomains) |
| `MCP_ASSETS_URL` | User only | Asset URL prefix (for CDN rewriting); defaults to MCP_URL if omitted |

**Typical production setup:**
```bash
MCP_URL=https://myserver.example.com
MCP_ASSETS_URL=https://cdn.example.com/mcp-assets
```

Views can now connect to the server (`MCP_URL`) and load assets from the CDN (`MCP_ASSETS_URL`).

## Next Steps

- **CSP domains and permissions:** references/18-mcp-apps/server-surface/05-csp-metadata.md
- **View folder structure:** references/18-mcp-apps/server-surface/02-register-views-and-folder-conventions.md
- **Deployment:** references/25-deploy/ cluster
