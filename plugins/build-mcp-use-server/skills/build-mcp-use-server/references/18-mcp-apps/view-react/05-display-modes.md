# Display modes

*Read this when a view needs to request more screen space (fullscreen, picture-in-picture) or detect the current display size.*

## Signature

```typescript
useDisplayMode(): {
  displayMode: DisplayMode;                 // "inline" | "fullscreen" | "pip"
  availableDisplayModes: readonly DisplayMode[]; // Negotiated modes
  requestDisplayMode(args: { mode: DisplayMode }): Promise<void>;
}

type DisplayMode = "inline" | "fullscreen" | "pip";
```

## Basic usage

Read the current mode and request a change:

```typescript
import { useDisplayMode } from "mcp-use/react";

function ExpandButton() {
  const { displayMode, availableDisplayModes, requestDisplayMode } = useDisplayMode();

  const isExpanded = displayMode === "fullscreen" || displayMode === "pip";

  return (
    <button
      onClick={() => requestDisplayMode({ mode: isExpanded ? "inline" : "fullscreen" })}
      disabled={!availableDisplayModes.includes("fullscreen")}
    >
      {isExpanded ? "Exit fullscreen" : "Expand"}
    </button>
  );
}
```

## Display modes explained

| Mode | Use when | Host grants? |
|---|---|---|
| `inline` | View fits within conversation flow | Default; always available |
| `fullscreen` | View needs full viewport (e.g., map, editor) | Advisory; host may deny |
| `pip` | View should float over conversation (rare) | Advisory; host may deny |

**The host decides** → `requestDisplayMode()` is advisory. Requested mode may be denied. Always read `displayMode` after requesting.

## Pairing with viewConfig

Declare which modes your view supports in `viewConfig`:

```typescript
import type { ViewConfig } from "mcp-use/react";

export const viewConfig: ViewConfig = {
  displayModes: ["inline", "fullscreen"],
  autoResize: true,
};
```

The final available modes are the **intersection** of `viewConfig.displayModes` and the host's capabilities.

See `references/18-mcp-apps/server-surface/03-viewconfig.md` for the full `ViewConfig` schema.

## Combine with autoResize

When `autoResize: true` (default), the host resizes the iframe to content height. Disable it for layouts with fixed aspect ratios:

```typescript
export const viewConfig = {
  displayModes: ["inline", "fullscreen"],
  autoResize: false,  // You'll manage size with useSendSizeChanged()
};
```

Then call `useSendSizeChanged()` on layout changes:

```typescript
import { useSendSizeChanged } from "mcp-use/react";

function AspectRatioChart() {
  const sendSize = useSendSizeChanged();

  useEffect(() => {
    // Notify host when the chart resizes
    sendSize({ width: 600, height: 400 });
  }, []);

  return <svg width="600" height="400">{/* chart */}</svg>;
}
```

See `references/18-mcp-apps/view-react/07-host-context-files-and-size.md` for `useSendSizeChanged()`.

## Gotchas

- **Request does not guarantee the mode** → always check `displayMode` after calling `requestDisplayMode()`
- **`availableDisplayModes` may change** → host capability changes if user resizes or switches apps (rare)
- **Fullscreen breaks form focus** → on iOS/mobile, fullscreen mode may hide the keyboard; test thoroughly

