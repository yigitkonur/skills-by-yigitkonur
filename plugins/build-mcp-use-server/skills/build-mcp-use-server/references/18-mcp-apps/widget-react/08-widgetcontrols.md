# `<WidgetControls>` — Debug and View-Mode Overlay

Renders a small control surface over the widget — debug button, fullscreen / PiP toggles. Most widgets get these via the `debugger` and `viewControls` props on `<McpUseProvider>`. Use `<WidgetControls>` directly only when you need custom positioning or composition.

```tsx
import { WidgetControls } from "mcp-use/react";

<WidgetControls debugger viewControls position="top-right" showLabels>
  <MyWidget />
</WidgetControls>
```

## Props

| Prop | Type | Default | Description |
|---|---|---|---|
| `children` | `ReactNode` | — | Required. Widget content. |
| `debugger` | `boolean` | `false` | Show the debug-panel button. |
| `viewControls` | `boolean \| "pip" \| "fullscreen"` | `false` | `true` shows both buttons; the literal strings show one. |
| `position` | `"top-left" \| "top-center" \| "top-right" \| "center-left" \| "center-right" \| "bottom-left" \| "bottom-center" \| "bottom-right"` | `"top-right"` | Control container position. |
| `attachTo` | `HTMLElement \| null` | `undefined` | Custom mount target. |
| `showLabels` | `boolean` | `true` | Show text labels next to icons. |
| `className` | `string` | `""` | Extra CSS class on the controls container. |

## Debug panel contents

When `debugger` is on, clicking the debug button opens an overlay showing:

- Current `props`, tool `output`, response `metadata`, persisted `state`.
- Host context: `theme`, `displayMode`, `safeArea`, `userAgent`, `locale`, `maxHeight`, and API availability.
- Every key on `window.openai` (when present).
- Interactive testers: invoke `callTool`, push `sendFollowUpMessage`, fire `openExternal`, mutate `setState`.

## View-mode buttons

When `viewControls` is on, the buttons call `requestDisplayMode` for you. The host may decline — see `10-display-modes.md` for what the response means.

## Position examples

```tsx
<WidgetControls position="top-right" debugger>...</WidgetControls>
<WidgetControls position="bottom-left" viewControls>...</WidgetControls>
<WidgetControls position="center-right" viewControls="pip">...</WidgetControls>
```

## When to use this directly

| Scenario | Direct use? |
|---|---|
| Widget already wrapped by `<McpUseProvider debugger>` | No |
| You want controls over a sub-region instead of the full widget | Yes |
| You need a custom mount target via `attachTo` | Yes |
| You want both a debugger overlay at the root and a separate set of buttons elsewhere | Yes |

## Production hygiene

Ship `debugger` only behind a development flag. The debug panel exposes raw props and tool outputs — fine in dev, noisy and confusing in production widgets.
