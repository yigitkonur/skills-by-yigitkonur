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

Render images safely within views. Handles MIME types, fallbacks, and host constraints.

**Signature:**
```typescript
<Image
  src: string;
  alt: string;
  width?: number;
  height?: number;
  loading?: "lazy" | "eager";
  onError?: () => void;
/>
```

**Example:**
```typescript
import { Image } from "mcp-use/react";

function ProductCard({ product }) {
  return (
    <div>
      <Image
        src={product.imageUrl}
        alt={product.name}
        width={200}
        height={150}
        loading="lazy"
      />
      <p>{product.name}</p>
    </div>
  );
}
```

**Use instead of `<img>`:**
- Respects view CSP constraints
- Handles missing images gracefully
- Supports resource domain filtering

Do not use regular `<img>` for images in CSP-restricted views; always use `<Image>`.

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
- **`<Image>` honors CSP constraints** → if `resourceDomains` does not include the image origin, the image will not load
- **ViewControls is a wrapper component with `debugger` and `viewControls` props**, not a compound component (`ViewControls.Action` does not exist)

