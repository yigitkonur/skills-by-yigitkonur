# Theme and components

*Read this when you need to subscribe to theme changes, render safe images, or add a control bar to your view.*

## Theme subscription

Subscribe to host theme changes (light/dark).

**Signature:**
```typescript
useViewTheme(): "light" | "dark"
```

**Example:**
```typescript
import { useViewTheme } from "mcp-use/react";

function ThemeAware() {
  const theme = useViewTheme();

  return (
    <div style={{ color: theme === "dark" ? "#fff" : "#000" }}>
      Current theme: {theme}
    </div>
  );
}
```

**Note:** `useViewTheme()` only notifies of theme changes. CSS custom properties from `<ThemeProvider>` are already applied. Use this hook when you need to fork logic or conditional rendering based on theme.

The hook does **not** re-render on locale or dimension updates — only color scheme changes. Use `useHostContext()` for safe area insets instead.

## Image component

A thin `<img>` wrapper that resolves root-relative `src` paths against the project's `public/` folder. It accepts every `React.ImgHTMLAttributes<HTMLImageElement>` prop (`alt`, `width`, `height`, `loading`, `onError`, `className`, `style`, ...) and passes them straight through to the rendered `<img>`.

**Signature:**
```typescript
const Image: React.FC<React.ImgHTMLAttributes<HTMLImageElement>>
```

**Path resolution** (via the internal `publicAsset()` helper, not part of the public API):

| `src` form | Resolved to |
|---|---|
| `/logo.svg` (root-relative) | `${basePath}/_mcp-use/public/logo.svg`, using the request-scoped base injected per view render |
| `https://...`, `http://...`, `data:...` | Passed through unchanged |
| `assets/logo.svg` (relative, no leading `/`) | Passed through unchanged (resolves relative to the iframe document) |
| `""` (empty string) | Passed through unchanged |

**Example:**
```typescript
import { Image } from "mcp-use/react";

function ProductCard({ product }) {
  return (
    <div>
      <Image
        src="/logo-mcp-use.svg"
        alt={product.name}
        width={200}
        height={150}
        loading="lazy"
        className="product-image"
      />
      <p>{product.name}</p>
    </div>
  );
}
```

**Use `<Image>` for files shipped in your project's `public/` folder** (referenced by a root-relative path) so the URL resolves correctly behind proxies, tunnels, and `MCP_ASSETS_URL` — a bare `<img src="/logo.svg">` would resolve against the host's own origin instead, not the server's public assets. For remote images (`https://...`) `<Image>` and `<img>` behave identically; `<Image>` does **not** enforce CSP, filter by domain, or provide a fallback for a broken image — CSP `resourceDomains` restrictions (see `references/18-mcp-apps/server-surface/05-csp-metadata.md` for the tool `view.csp` config) apply to the browser's own image loading regardless of which component renders the tag, and a failed load still fires the standard `onerror` event you can handle via the `onError` prop.

To read the resolved public-folder base URL directly (for example, for a stylesheet `<link>` or a non-`<img>` asset), call `getPublicBaseUrl()`, also exported from `mcp-use/react`. The returned base always ends with `/`, so append a public-folder path **without** a leading slash:

```typescript
import { getPublicBaseUrl } from "mcp-use/react";

const publicBaseUrl = getPublicBaseUrl();
const stylesheetUrl = `${publicBaseUrl}styles/widget.css`;
const workerUrl = `${publicBaseUrl}workers/chart-worker.js`;
```

Outside a synthesized browser View document, `getPublicBaseUrl()` returns an empty string.

## ViewControls

Wrap a view subtree with optional development controls.

**Signature:**
```typescript
<ViewControls debugger?: boolean viewControls?: boolean | "pip" | "fullscreen">
  {children}
</ViewControls>
```

**Example:**
```typescript
import { ViewControls } from "mcp-use/react";

function Dashboard() {
  return (
    <ViewControls debugger viewControls="fullscreen">
      <DashboardContent />
    </ViewControls>
  );
}
```

`debugger` shows the debug overlay. `viewControls` enables display-mode buttons; use `true` for all supported controls or select only `"pip"` or `"fullscreen"`. This component is development-oriented, so most views should use plain buttons in their production UI.

## Combining ThemeProvider, Image, and ViewControls

A complete view:

```typescript
import { ThemeProvider, Image, ViewControls, useViewTheme } from "mcp-use/react";

export default function View() {
  const theme = useViewTheme();

  return (
    <ThemeProvider>
      <ViewControls debugger viewControls="fullscreen">
        <div style={{ background: theme === "dark" ? "#222" : "#fff" }}>
          <Image src="/logo.png" alt="Logo" width={100} height={100} />
          <h1>My view</h1>
        </div>
      </ViewControls>
    </ThemeProvider>
  );
}
```

## Gotchas

- **`useViewTheme()` returns `"light" | "dark"` directly** — do not destructure `colorScheme`
- **`<Image>` does not enforce CSP** → CSP `resourceDomains` are a browser-level restriction the host applies to the iframe regardless of which component rendered the `<img>`; `<Image>` only resolves root-relative paths against the public-assets base
- **ViewControls is a wrapper component with `debugger` and `viewControls` props**, not a compound component (`ViewControls.Action` does not exist)
- **ViewControls internally calls `useToolContext()`, `useHostContext()`, and `useDisplayMode()`** → mount it inside the same provider tree as the rest of the view (it does not need its own `ThemeProvider`, but it does need an active runtime)

