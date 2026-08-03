# Host Capability Detection

*Read this when a View needs an optional host-mediated feature.*

Hosts negotiate features independently. Gate each operation on its own capability; do not infer support from the host product name or from an unrelated capability.

## Read Negotiated Context

```typescript
import { useHostContext } from "mcp-use/react";

export default function MyView() {
  const hostContext = useHostContext();

  console.log(hostContext.theme);       // "light" | "dark"
  console.log(hostContext.locale);      // BCP 47 locale
  console.log(hostContext.timeZone);    // IANA time zone
  console.log(hostContext.platform);    // "web" | "mobile"
  console.log(hostContext.safeArea);    // { top, right, bottom, left }
  console.log(hostContext.hostInfo);    // { name, version } | undefined
  console.log(hostContext.hostCapabilities);
  console.log(hostContext.isAvailable); // bridge connection status

  return null;
}
```

`HostContextHandle` has no `.client` object and no capability-name array. Full field and fallback details are in `view-react/07-host-context-files-and-size.md`.

## Capability Checks

A supported capability is represented by an object; an unsupported or not-yet-negotiated capability is `undefined`.

| Capability key | Gates | Check |
|-|-|-|
| `message` | `useSendFollowUp()` | `hostCapabilities?.message !== undefined` |
| `openLinks` | Host-mediated external URL opening | `hostCapabilities?.openLinks !== undefined` |
| `downloadFile` | Standard protocol `ui/download-file` | `hostCapabilities?.downloadFile !== undefined` |
| `updateModelContext` | Standard model-context updates used by `useViewState()` / `<ModelContext>` | `hostCapabilities?.updateModelContext !== undefined` |
| `serverTools` | View-to-server tool calls; `useCallTool()` requires this | `hostCapabilities?.serverTools !== undefined` |
| `serverResources` | Host-proxied reads of server resources | `hostCapabilities?.serverResources !== undefined` |
| `logging` | Host-accepted UI log messages | `hostCapabilities?.logging !== undefined` |

`serverTools.listChanged` and `serverResources.listChanged` independently indicate support for their corresponding list-change notifications. One capability never proves the other.

Display modes are negotiated separately through `useDisplayMode()`. ChatGPT file helpers exposed by `useFiles()` are also separate from standard `hostCapabilities`; gate them with `useFiles().isSupported`.

## Guard a Tool Call

`useCallTool()` self-guards and rejects if the host did not advertise `serverTools`. Check the capability as well when deciding whether to render the UI affordance:

```typescript
import { useCallTool, useHostContext } from "mcp-use/react";

export default function RefreshButton() {
  const { hostCapabilities } = useHostContext();
  const refresh = useCallTool("refresh-results");

  if (hostCapabilities?.serverTools === undefined) {
    return <p>Refresh is not available in this host.</p>;
  }

  return (
    <button onClick={() => refresh.callTool({})} disabled={refresh.isPending}>
      Refresh
    </button>
  );
}
```

## Guard a Follow-Up Message

```typescript
import { useHostContext, useSendFollowUp } from "mcp-use/react";

export default function ResultsView() {
  const { hostCapabilities } = useHostContext();
  const sendFollowUp = useSendFollowUp();

  if (hostCapabilities?.message === undefined) {
    return <div>Follow-up messages are unavailable.</div>;
  }

  return (
    <button onClick={() => sendFollowUp({ prompt: "Show 20 more results" })}>
      Show More
    </button>
  );
}
```

The capability check controls the affordance. The hook also rejects before wire traffic when `message` is unavailable.

## Host Identity Is a Hint

```typescript
const { hostInfo } = useHostContext();

if (hostInfo?.name === "some-host") {
  // A display-only hint is acceptable.
}
```

Never use `hostInfo.name` as a security boundary or feature gate. The identity is self-reported; negotiated capabilities are the operational contract.

## Display Mode Negotiation

```typescript
import { useDisplayMode } from "mcp-use/react";
import type { ViewConfig } from "mcp-use/react";

export const viewConfig: ViewConfig = {
  displayModes: ["inline", "fullscreen", "pip"],
};

export default function MyView() {
  const { displayMode, availableDisplayModes, requestDisplayMode } =
    useDisplayMode();

  if (!availableDisplayModes.includes("fullscreen")) return null;

  return (
    <button onClick={() => requestDisplayMode({ mode: "fullscreen" })}>
      Open fullscreen; current mode is {displayMode}
    </button>
  );
}
```

The available set is the runtime's negotiated set. A resolved request means the host processed it, not that the mode changed; read `displayMode` for the actual state.

## Graceful Degradation

Provide a fallback for every optional feature. For ChatGPT-specific file helpers:

```typescript
import { useFiles } from "mcp-use/react";

export default function FileFeature() {
  const files = useFiles();
  return files.isSupported ? <FilePickerUI /> : <SimpleTextOnlyUI />;
}
```

The standard protocol's `downloadFile` capability and the beta.66 `useFiles()` wrapper are not the same surface. See `view-react/07-host-context-files-and-size.md` for the shipped wrapper and its limitations.
