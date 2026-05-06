# `<ThemeProvider>` — Host Theme Synchronization

Manages dark/light mode synchronization between the host app and the widget. Auto-included by `<McpUseProvider>` — reach for it directly only when composing providers manually.

```tsx
import { ThemeProvider } from "mcp-use/react";

<ThemeProvider>
  <App />
</ThemeProvider>
```

## Props

| Prop | Type | Required | Description |
|---|---|---|---|
| `children` | `ReactNode` | Yes | The widget content to wrap. |
| `colorScheme` | `boolean` | No | When true, set `document.documentElement.style.colorScheme` to `light` or `dark`. Default `false`. |

## Resolution priority

1. Widget theme from `useWidget()` — `window.openai.theme` (ChatGPT) or the SEP-1865 host context theme (MCP Apps).
2. System preference (`prefers-color-scheme: dark`) — fallback when no host API is present (e.g. running standalone in dev).

## What it sets

- Replaces the root theme class with `dark` or `light`.
- Sets `data-theme` to `dark` or `light`.
- Sets the `color-scheme` CSS property only when `colorScheme` is true.
- Uses `useLayoutEffect` to apply the class **synchronously before paint**, preventing a flash of incorrect theme.
- Subscribes to system theme changes via `MediaQueryList` so the widget tracks OS-level toggles.

## Tailwind compatibility

The provider works with `darkMode: "class"`:

```js
// tailwind.config.js
export default { darkMode: "class" /* ... */ };
```

```tsx
<div className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
  ...
</div>
```

## Reading the theme value

`<ThemeProvider>` only manages the class. To read the theme inside a component, use `useWidget().theme` or `useWidgetTheme()`:

```tsx
const theme = useWidgetTheme();
const isDark = theme === "dark";
```

See `11-host-context.md` for the wider host-context surface.
