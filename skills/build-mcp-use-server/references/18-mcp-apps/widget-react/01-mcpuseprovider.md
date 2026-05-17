# `<McpUseProvider>` — The Widget Root Wrapper

Universal wrapper that composes the common React shell for a widget. Protocol-agnostic — works unchanged in MCP Apps clients (Claude, Goose) and ChatGPT Apps SDK environments.

```tsx
import { McpUseProvider } from "mcp-use/react";

export default function Widget() {
  return (
    <McpUseProvider autoSize>
      <MyWidget />
    </McpUseProvider>
  );
}
```

## What it provides

| Layer | Responsibility |
|---|---|
| `StrictMode` | React development checks |
| `ThemeProvider` | Dark/light synchronization with the host (sets `light`/`dark` class and `data-theme` on `<html>`) |
| `WidgetControls` (optional) | Debug overlay and view-mode toggles when `debugger` or `viewControls` is set |
| `ErrorBoundary` | Catches render errors so a single component crash doesn't blank the iframe |
| Auto-size wrapper | `ResizeObserver` reports intrinsic height to the host when `autoSize` is true |

Host context (`callTool`, `setState`, `theme`, `displayMode`, etc.) comes from `useWidget()`, which reads the host runtime directly. `McpUseProvider` is still the normal widget root because it adds theme sync, error isolation, debug controls, and auto-sizing.

## Props

| Prop | Type | Default | Description |
|---|---|---|---|
| `children` | `ReactNode` | — | Required. The widget content. |
| `debugger` | `boolean` | `false` | Show the debug panel button. |
| `viewControls` | `boolean \| "pip" \| "fullscreen"` | `false` | `true` shows both buttons; `"pip"` or `"fullscreen"` shows just one. |
| `autoSize` | `boolean` | `true` | Wrap children in a `ResizeObserver` that reports size changes to the host. |
| `colorScheme` | `boolean` | `false` | Also set `document.documentElement.style.colorScheme`; leave off for transparent iframe backgrounds. |

## Rules

- One `<McpUseProvider>` at the root of every `widget.tsx`. Never nest two.
- Do not pass props through React props to children — children read from `useWidget()`. See `03-usewidget-hook.md`.
- `autoSize` is already enabled by default; pass `autoSize={false}` only for fixed-height layouts. See `14-notify-intrinsic-height.md`.
- No router is included. If your widget uses a router, wrap that provider explicitly inside `<McpUseProvider>`.

## Common shape

```tsx
// resources/my-widget/widget.tsx
import { McpUseProvider } from "mcp-use/react";
import { MyWidgetContent } from "./components/MyWidgetContent";

export default function Widget() {
  return (
    <McpUseProvider autoSize debugger viewControls="fullscreen">
      <MyWidgetContent />
    </McpUseProvider>
  );
}
```

For widgets that need a separate MCP client connection (multi-server consoles), pair this with `<McpClientProvider>` — see `02-mcpclientprovider.md`.

**Canonical doc:** [manufact.com/docs/typescript/server/mcp-apps](https://manufact.com/docs/typescript/server/mcp-apps)
