# Host Capability Detection

*Read this when your view needs to use optional platform features.*

Not all MCP Apps hosts support the same features (follow-up messages, file picker, display-mode requests). Query the host's capabilities before calling platform-specific APIs.

## UseHostContext

Access host capabilities via the `useHostContext()` hook:

```typescript
import { useHostContext } from "mcp-use/react";

export default function MyView() {
  const hostContext = useHostContext();
  
  // Host environment info
  console.log(hostContext.client.name);           // "ChatGPT", "Claude", etc. (if available)
  console.log(hostContext.client.locale);         // User locale
  console.log(hostContext.client.safeAreaInsets); // Notch/safe area info
  
  // Available features
  console.log(hostContext.availableCapabilities); // string[]
  
  // Available display modes (intersection of viewConfig + host support)
  console.log(hostContext.availableDisplayModes); // DisplayMode[]
  
  // View dimensions and theme
  console.log(hostContext.dimensions);            // { width, height }
  console.log(hostContext.theme);                 // "light" | "dark"
}
```

## Capability Checks

| Capability | Needed For | Hook | How to Check |
|-|-|-|-|
| `message` | `useSendFollowUp()` | Check before calling | `hostContext.availableCapabilities.includes("message")` |
| `files` | `useFiles()` | Check before calling | `hostContext.availableCapabilities.includes("files")` |
| Display modes | `useDisplayMode()` | Optional; defaults to `["inline", "fullscreen"]` | `hostContext.availableDisplayModes` |
| Theme changes | `useViewTheme()` | Optional; default `"light"` | No capability check needed |

## Guarding APIs by Capability

```typescript
import { useHostContext, useSendFollowUp } from "mcp-use/react";

export default function ResultsView() {
  const hostContext = useHostContext();
  const sendFollowUp = useSendFollowUp();
  
  // Only show "Ask for more" button if host supports follow-up
  if (!hostContext.availableCapabilities.includes("message")) {
    return <div>Feature not available in this host</div>;
  }
  
  const handleAskMore = async () => {
    await sendFollowUp({ prompt: "Show 20 more results" });
  };
  
  return (
    <div>
      <Results />
      <button onClick={handleAskMore}>Show More</button>
    </div>
  );
}
```

## Client Detection (Low Trust)

The `hostContext.client` object carries hints about the platform (name, locale, user agent, etc.), but is **not authoritative**:

```typescript
const { client } = useHostContext();

// Hints only — client can spoof these values
if (client.name === "ChatGPT") {
  // ChatGPT-specific hint, but don't trust it
}
```

Use capabilities checks for feature gates, not client name. Features are verified by the host.

## Display Mode Negotiation

Views can declare supported display modes in `viewConfig`:

```typescript
// views/my-view/view.tsx
import type { ViewConfig } from "mcp-use/react";

export const viewConfig: ViewConfig = {
  displayModes: ["inline", "fullscreen", "pip"],
  autoResize: true,
};

export default function MyView() {
  const { availableDisplayModes, currentDisplayMode } = useHostContext();
  // Intersection: only ["inline", "fullscreen", "pip"] that host also supports
}
```

The host decides the final display mode; the view can request a change via `useDisplayMode()`:

```typescript
const { displayMode, requestDisplayMode } = useDisplayMode();

// Request change; host may ignore
await requestDisplayMode({ mode: "fullscreen" });
```

## Graceful Degradation

Always provide fallback UI for missing capabilities:

```typescript
export default function AdvancedFeatureView() {
  const hostContext = useHostContext();
  
  if (!hostContext.availableCapabilities.includes("files")) {
    return <SimpleTextOnlyUI />;
  }
  
  return <FilePickerUI />;
}
```

See `references/18-mcp-apps/view-react/07-host-context-files-and-size.md` for detailed file and size APIs.
