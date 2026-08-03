# Assets, MCP_URL, and MCP_ASSETS_URL

*Read this when deploying View bundles, public assets, or a separate asset origin.*

The View build produces a manifest plus JS/CSS assets. The server synthesizes HTML when the MCP resource is read and resolves every external asset URL for that request.

## Served Namespaces

With the default `basePath` `/mcp`:

| HTTP path | Disk source in a production build |
|-|-|
| `/mcp/_mcp-use/views/<name>/<asset>` | `.mcp-use/build/views/<name>/<asset>` |
| `/mcp/_mcp-use/public/<asset>` | `.mcp-use/build/views/public/<asset>` |

In dev, View modules are served by Vite and public files are read from the project's `public/` directory. Asset responses support `GET`/`HEAD`; unsafe or missing paths return 404.

## Build Artifacts

Default external build:

```text
.mcp-use/build/
├── index.js
├── manifest.json
└── views/
    ├── product-search/
    │   └── assets/
    │       ├── product-search-ABC123.js
    │       └── product-search-DEF456.css
    └── public/
        ├── logo.svg
        └── icons/star.png
```

The corresponding `manifest.json` contains a `views` map:

```json
{
  "entryPoint": "index.js",
  "views": {
    "product-search": {
      "kind": "external",
      "entry": "assets/product-search-ABC123.js",
      "css": ["assets/product-search-DEF456.css"]
    }
  }
}
```

`mcp-use build --inline` stores minified `js` and aggregated `css` strings in each manifest entry instead of writing that View's separate JS/CSS bundle.

No build mode requires a physical per-View `index.html`. During `resources/read`, `synthesizeViewDocument()` creates the complete document:

| Manifest kind | Synthesized HTML |
|-|-|
| `external` | Absolute `<script type="module" src="...">` and `<link rel="stylesheet" href="...">` URLs |
| `inline` | Embedded `<script type="module">` and optional `<style>` |

The synthesized document also injects the request-resolved `publicBase` before the View module runs.

## MCP_URL

`MCP_URL` identifies the public server origin used for View CSP and request-independent serving contexts.

```bash
MCP_URL=https://mcp.example.com
```

- A valid value is reduced to its URL **origin**; a path suffix is ignored.
- The server origin is appended to resource `_meta.ui.csp.connectDomains`.
- In dev, its WebSocket origin is also appended for HMR.
- If absent or invalid during an HTTP request, the framework resolves the origin from `Forwarded`, `X-Forwarded-Proto` + `X-Forwarded-Host`, or the request URL.

## MCP_ASSETS_URL

`MCP_ASSETS_URL` is an optional asset URL prefix. Unlike `MCP_URL`, it may include a path:

```bash
MCP_ASSETS_URL=https://cdn.example.com/mcp-assets
```

- Trailing slashes are removed.
- Its origin is appended to resource `_meta.ui.csp.resourceDomains`.
- External builds rewrite manifest JS/CSS paths to full CDN URLs when the variable is set at build time.
- Without it, external View assets and public files resolve against the server origin and `basePath`.
- Inline View JS/CSS does not need an external bundle URL, but public assets still use the resolved public base.

If the build manifest contains full CDN URLs, publish the contents of `.mcp-use/build/views/` at the matching `<MCP_ASSETS_URL><basePath>/_mcp-use/views/<view-name>/` layout.

## URL Resolution Truth Table

| Manifest asset value | Resolution |
|-|-|
| `https://cdn.example.com/file.js` | Used unchanged |
| `data:...` | Used unchanged |
| `/@id/...` or another `/...` dev path | Prefixed with the request-resolved assets base |
| `assets/view-ABC.js` | Resolved under `<assetsBase><basePath>/_mcp-use/views/<name>/` |

## Public Assets

Author public files live in `public/` and are copied to `.mcp-use/build/views/public/` for production.

```text
public/
├── logo.svg
└── icons/star.png
```

Use the published React helper:

```typescript
import { getPublicBaseUrl } from "mcp-use/react";

export default function MyView() {
  const publicBase = getPublicBaseUrl();
  return <img src={`${publicBase}logo.svg`} alt="Logo" />;
}
```

`getPublicBaseUrl()` returns an absolute prefix with a trailing slash inside a synthesized View document. Append paths **without** a leading slash. Outside that document it returns an empty string.

For the default base path and no separate asset host, `logo.svg` resolves to:

```text
https://mcp.example.com/mcp/_mcp-use/public/logo.svg
```

## CSP Boundary

View CSP governs browser activity inside the sandboxed iframe. It does not govern server-side `fetch()` calls made by a tool callback. Add a `connectDomains` entry only when View code itself connects to that origin.

## Next Steps

- Manifest priming and binding validation: `02-register-views-and-folder-conventions.md`
- CSP merge rules: `05-csp-metadata.md`
- Deployment references: `../../25-deploy/01-decision-matrix.md`
