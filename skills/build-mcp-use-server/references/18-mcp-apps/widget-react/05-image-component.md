# `<Image>` — CSP-Aware Image Component

CSP-aware image component that resolves relative or `/`-prefixed paths to the MCP server's public assets URL at runtime. Use it instead of `<img>` for any asset you serve from your own server.

```tsx
import { Image } from "mcp-use/react";

<Image src="/fruits/apple.png" alt="Apple" />
<Image src="https://cdn.example.com/img.jpg" alt="External" />
<Image src="data:image/png;base64,iVBOR..." alt="Inline" />
```

## Why not plain `<img>`

The widget runs inside a sandboxed iframe with a strict CSP. The widget bundle does not know at build time where its public assets are actually served from — that depends on whether the host runs the dev server, a static deployment, or a tunnel.

`<Image>` solves this by resolving non-absolute paths through the runtime's globals:

1. If `src` is `http://`, `https://`, or `data:` — passed through unchanged.
2. Else if `window.__mcpPublicAssetsUrl` is set — prefixed with that.
3. Else falls back to `window.__mcpPublicUrl` (e.g. `http://localhost:3000/mcp-use/public`).

A hand-written `<img src="/fruits/apple.png">` will request the iframe's own origin, which has no public assets. It will 404 silently.

## Props

| Prop | Type | Default | Description |
|---|---|---|---|
| `src` | `string` | — | Required. Absolute URL, data URI, or relative/public asset path. |
| `alt` | `string` | `""` | Alternate text. |
| *(any `<img>` attribute)* | various | — | `width`, `height`, `loading`, `className`, `style`, etc. |

## CSP requirements

Hosted images that aren't on your server need their domains in the widget's CSP `resourceDomains`. Otherwise the iframe will refuse to load them. See `../server-surface/05-csp-metadata.md` for the `widgetMetadata.metadata.csp` reference.

```typescript
export const widgetMetadata: WidgetMetadata = {
  description: "...",
  props: z.object({ /* ... */ }),
  metadata: {
    csp: {
      resourceDomains: ["https://cdn.example.com", "https://images.unsplash.com"],
    },
  },
};
```

## Rule of thumb

| Asset source | Use |
|---|---|
| File you ship in `resources/<widget>/public/` | `<Image src="/path.png" />` or `<Image src="path.png" />` |
| External CDN | `<Image src="https://..." />` and add domain to `resourceDomains` |
| Inline SVG / data URI | `<Image src="data:..." />` (no CSP impact) |
| Anywhere else | Treat as external |
