# Display Modes — `displayMode` and `requestDisplayMode`

Hosts render widgets in three modes: inline, picture-in-picture, fullscreen. Read the current mode from `useWidget().displayMode` and ask the host to change it via `requestDisplayMode`.

```typescript
const { displayMode, requestDisplayMode } = useWidget();
// displayMode: "inline" | "pip" | "fullscreen"
```

## Modes

| Mode | When the host uses it |
|---|---|
| `inline` | Default — widget rendered inline within the conversation. |
| `pip` | Picture-in-picture — small floating panel, non-blocking. |
| `fullscreen` | Modal-like takeover for immersive widgets (charts, dashboards). |

## Requesting a mode

```tsx
const result = await requestDisplayMode("fullscreen");
// result.mode is the mode the host actually granted — may differ from the request.
```

Important: **the host may decline or coerce.** Always read `result.mode` and adapt rather than assuming the request succeeded. For example, the package types document that ChatGPT on mobile coerces PiP requests to `"fullscreen"`.

## Pattern — adapt layout to mode

```tsx
import { useWidget } from "mcp-use/react";

const ExpandableChart: React.FC = () => {
  const { displayMode, requestDisplayMode } = useWidget();
  const isFullscreen = displayMode === "fullscreen";
  const isPip = displayMode === "pip";

  return (
    <div className={isFullscreen ? "h-screen w-full p-6" : "h-64 p-4"}>
      <div className="flex justify-between mb-4">
        <h2>Analytics</h2>
        <div className="flex gap-2">
          {!isFullscreen && !isPip && (
            <>
              <button onClick={() => requestDisplayMode("pip")}>PiP</button>
              <button onClick={() => requestDisplayMode("fullscreen")}>Expand</button>
            </>
          )}
          {(isFullscreen || isPip) && (
            <button onClick={() => requestDisplayMode("inline")}>Exit</button>
          )}
        </div>
      </div>
      {/* layout responds to mode */}
    </div>
  );
};
```

## Built-in buttons via `<WidgetControls>`

If the buttons are all you want, let the framework do it:

```tsx
<McpUseProvider viewControls>...</McpUseProvider>
// or
<McpUseProvider viewControls="fullscreen">...</McpUseProvider>
```

See `08-widgetcontrols.md`.

## Anti-patterns

- Triggering `requestDisplayMode` automatically on mount — the user did not ask for fullscreen. Wait for explicit interaction.
- Assuming `requestDisplayMode("fullscreen")` succeeded; render based on the next `displayMode` value, not the request.
- Hard-coding fixed pixel heights for fullscreen — read `maxHeight` from `useWidget()` (see `11-host-context.md`).
