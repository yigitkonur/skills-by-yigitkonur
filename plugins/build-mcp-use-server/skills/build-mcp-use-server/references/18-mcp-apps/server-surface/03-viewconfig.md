# ViewConfig: View Runtime Configuration

*Read this when declaring display modes or automatic size reporting for a View.*

A View may export `viewConfig`. Generated bootstrap code normalizes it before constructing the mounted MCP Apps runtime.

## Shape

```typescript
import type { ViewConfig } from "mcp-use/react";

export const viewConfig: ViewConfig = {
  displayModes: ["inline", "fullscreen"],
  autoResize: true,
};
```

## Fields

| Field | Type | Default | Contract |
|-|-|-|-|
| `displayModes` | `readonly ("inline" | "fullscreen" | "pip")[]` | `["inline", "fullscreen", "pip"]` | Non-empty, no duplicates, only known values, and must include `"inline"` |
| `autoResize` | `boolean` | `true` | Lets the MCP Apps runtime observe the document and report intrinsic size changes |

## Display Modes

```typescript
export const viewConfig: ViewConfig = {
  displayModes: ["inline", "fullscreen"],
};
```

Invalid declarations throw during bootstrap:

```typescript
// Empty
export const viewConfig: ViewConfig = { displayModes: [] };

// Missing required inline mode
export const viewConfig: ViewConfig = { displayModes: ["fullscreen"] };

// Duplicate
export const viewConfig: ViewConfig = {
  displayModes: ["inline", "inline"],
};
```

The config declares what the View can render. The runtime advertises those modes to the host; the host returns its available modes. Read the negotiated set and current mode with `useDisplayMode()`:

```typescript
import { useDisplayMode } from "mcp-use/react";

export default function MyView() {
  const { displayMode, availableDisplayModes, requestDisplayMode } =
    useDisplayMode();

  const canFullscreen = availableDisplayModes.includes("fullscreen");

  return (
    <button
      disabled={!canFullscreen}
      onClick={() => requestDisplayMode({ mode: "fullscreen" })}
    >
      Current: {displayMode}
    </button>
  );
}
```

A mode request is host-mediated. Promise resolution does not prove that the host changed modes; observe `displayMode` for the result.

## Automatic and Manual Size Reporting

With the default `autoResize: true`, the underlying MCP Apps runtime observes the document and reports size changes.

Set it to `false` when the View owns reporting:

```typescript
import { useEffect } from "react";
import { useSendSizeChanged } from "mcp-use/react";
import type { ViewConfig } from "mcp-use/react";

export const viewConfig: ViewConfig = {
  displayModes: ["inline"],
  autoResize: false,
};

export default function FixedAspectView() {
  const sendSizeChanged = useSendSizeChanged();

  useEffect(() => {
    sendSizeChanged({ width: 800, height: 600 });
  }, [sendSizeChanged]);

  return <div style={{ aspectRatio: "4/3" }}>...</div>;
}
```

## Mounted-Runtime Snapshot

Treat `viewConfig` as static module configuration, but describe the lifecycle precisely:

1. `bootstrapView()` reads the export and creates a new normalized object with defaults.
2. The first mount stores that normalized config on the mounted runtime.
3. HMR reuses the existing React root and MCP Apps runtime.
4. If HMR supplies different `autoResize` or `displayModes`, the framework warns and keeps the original mounted config.
5. A full iframe reload, or an explicit advanced dispose-and-bootstrap cycle, is required for new config to take effect.

The framework does **not** call `Object.freeze()` on `viewConfig` or the normalized object. "Fixed for the mounted runtime" is the behavior; JavaScript-level freezing is not.

Do not mutate configuration at runtime:

```typescript
export const viewConfig: ViewConfig = {
  displayModes: ["inline"],
};

// Do not do this. It does not reconfigure the mounted runtime.
viewConfig.displayModes = ["inline", "fullscreen"];
```

Use hooks and component state for live behavior. Change the export and reload the iframe when changing pre-render runtime configuration.

## No Config Export

Omitting `viewConfig` uses:

```typescript
{
  autoResize: true,
  displayModes: ["inline", "fullscreen", "pip"]
}
```

Generated View modules call `bootstrapView()`; normal View authors do not call it manually.

## Related

- Host capability and display-mode checks: `../05-host-capability-detection.md`
- View setup and generated providers: `../view-react/01-setup-and-providers.md`
- Manual size reporting details: `../view-react/07-host-context-files-and-size.md`
- Asset serving: `04-assets-mcp-url-and-serving.md`
