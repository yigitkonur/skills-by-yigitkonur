# ViewConfig: View Runtime Configuration

*Read this when you need to declare display modes, auto-resize behavior, or other view-level runtime settings.*

Views export an optional `viewConfig?: ViewConfig` object that declares immutable runtime configuration. This config is normalized by the framework at view bootstrap time and sent to the host to configure rendering behavior.

## ViewConfig Shape

```typescript
import type { ViewConfig } from "mcp-use/react";

export const viewConfig: ViewConfig = {
  displayModes: ["inline", "fullscreen"],
  autoResize: true,
};
```

## Field Reference

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `displayModes` | `DisplayMode[]` | `["inline"]` | Available rendering modes host may request; host chooses intersection with its capabilities |
| `autoResize` | `boolean` | `true` | Framework auto-detects and reports intrinsic size; set `false` for manual `useSendSizeChanged()` |

## displayModes

Declare which display modes your view supports. The host negotiates the final set by taking the intersection with its capabilities.

```typescript
// View supports both inline and fullscreen
displayModes: ["inline", "fullscreen"]

// View is fullscreen-only (e.g., map explorer)
displayModes: ["fullscreen"]

// Inline only (default if omitted)
displayModes: ["inline"]
```

At runtime, read the active display mode and its available options via `useDisplayMode()`:

```typescript
import { useDisplayMode } from "mcp-use/react";

export default function MyView() {
  const { displayMode, availableDisplayModes, requestDisplayMode } = useDisplayMode();

  return (
    <div>
      <p>Current mode: {displayMode}</p>
      <button onClick={() => requestDisplayMode({ mode: "fullscreen" })}>
        Fullscreen
      </button>
    </div>
  );
}
```

## autoResize

When `autoResize: true` (default), the framework uses a ResizeObserver to detect your view's intrinsic size and automatically reports it to the host via `useSendSizeChanged()`.

When `autoResize: false`, you manually control size reporting:

```typescript
import { useSendSizeChanged } from "mcp-use/react";

export default function FixedAspectView() {
  const sendSizeChanged = useSendSizeChanged();

  useEffect(() => {
    // Explicitly report size, e.g. for aspect-ratio layouts
    sendSizeChanged({ width: 800, height: 600 });
  }, [sendSizeChanged]);

  return <div style={{ aspectRatio: "4/3" }}>...</div>;
}
```

## Immutability

`ViewConfig` is immutable — declared once at module load and never modified. The framework freezes the object to prevent accidental mutation.

```typescript
// ✅ Correct
export const viewConfig: ViewConfig = { displayModes: ["inline"] };

// ❌ Do not mutate at runtime
viewConfig.displayModes = ["fullscreen"];  // Error or no effect
```

## Normalize at Bootstrap

The framework normalizes and validates `viewConfig` when the view is mounted:

1. Merges defaults for missing fields
2. Validates against host capabilities (e.g., display mode intersection)
3. Freezes the normalized config for the view's lifetime

You do not call a normalization function; the framework handles it via `bootstrapView()` in the view iframe.

## No Config Export

If you omit `viewConfig`, the framework uses defaults:

```typescript
// No export → uses defaults
export default function MyView() {
  // displayModes defaults to ["inline"]
  // autoResize defaults to true
  return <div>...</div>;
}
```

## Example: Multi-Mode View

```typescript
import { useDisplayMode, useSendSizeChanged, useToolContext } from "mcp-use/react";
import type { ViewConfig } from "mcp-use/react";

export const viewConfig: ViewConfig = {
  displayModes: ["inline", "fullscreen"],
  autoResize: false,  // Manual size control for aspect-ratio layouts
};

export default function Dashboard() {
  const { displayMode } = useDisplayMode();
  const sendSize = useSendSizeChanged();
  const ctx = useToolContext<"show-dashboard">();

  useEffect(() => {
    if (displayMode === "fullscreen") {
      sendSize({ width: 1200, height: 800 });
    } else {
      sendSize({ width: 600, height: 400 });
    }
  }, [displayMode, sendSize]);

  return (
    <div style={{ padding: displayMode === "fullscreen" ? "2rem" : "1rem" }}>
      {/* Dashboard content */}
    </div>
  );
}
```

## Next Steps

- **CSP and sandbox permissions:** references/18-mcp-apps/server-surface/05-csp-metadata.md
- **Asset serving:** references/18-mcp-apps/server-surface/04-assets-mcp-url-and-serving.md
- **React hooks and context:** references/18-mcp-apps/view-react/01-setup-and-providers.md
