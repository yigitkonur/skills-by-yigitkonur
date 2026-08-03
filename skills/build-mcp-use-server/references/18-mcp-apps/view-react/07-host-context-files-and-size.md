# Host context, files, and size

*Read this when you need host environment details, file capability boundaries, or manual View sizing.*

## Host context

`useHostContext()` returns normalized convenience fields plus the raw standard MCP Apps host context and negotiated capabilities.

```typescript
useHostContext(): HostContextHandle

interface HostContextHandle {
  theme: "light" | "dark";
  locale: string;
  timeZone: string;
  userAgent: string;
  platform: "web" | "mobile";
  displayMode: DisplayMode;
  safeArea: SafeAreaInsets;
  maxHeight: number | undefined;
  maxWidth: number | undefined;
  hostInfo: HostInfo | undefined;
  hostCapabilities: HostCapabilities | undefined;
  hostContext: HostContext | undefined;
  isAvailable: boolean;
}
```

```typescript
import { useHostContext } from "mcp-use/react";

function HostDetails() {
  const { hostInfo, locale, safeArea, isAvailable } = useHostContext();

  if (!isAvailable) return <p>Connecting to host…</p>;

  return (
    <div style={{ paddingTop: safeArea.top }}>
      <p>Host: {hostInfo?.name ?? "Unknown"} {hostInfo?.version}</p>
      <p>Locale: {locale}</p>
    </div>
  );
}
```

Capability-dependent hooks reject unsupported calls. Inspect `hostCapabilities` when an optional affordance must be hidden or disabled. The raw `hostContext` preserves the host's fields without the hook's fallbacks and allows additional properties for protocol evolution.

### Convenience-field fallbacks

| Field | Fallback or normalization |
|---|---|
| `theme` | `"light"` |
| `locale` | `"en-US"` |
| `timeZone` | Browser timezone, then `"UTC"` |
| `userAgent` | Browser `navigator.userAgent` |
| `platform` | `"mobile"` only when reported; `"desktop"` and other values normalize to `"web"` |
| `displayMode` | `"inline"` |
| `safeArea` | `{ top: 0, right: 0, bottom: 0, left: 0 }` |
| `maxHeight` / `maxWidth` | `undefined`, treated as unbounded |

`maxHeight` and `maxWidth` derive from `hostContext.containerDimensions`: exact `height`/`width` wins when fixed, otherwise the corresponding maximum is used. Read the raw dimensions for distinctions the convenience fields do not preserve.

### Important raw host-context fields

Prefer `useViewTheme()` for reactive theme branching and `useDisplayMode()` for negotiated display-mode controls. Reach into `hostContext` when the higher-level hooks intentionally do not expose the field you need:

| Raw field | Standard meaning | Typical use |
|---|---|---|
| `deviceCapabilities` | Optional `{ touch?, hover? }` input capabilities | Choose touch-sized controls or avoid hover-only interactions |
| `styles` | Optional host-provided `variables` and injectable CSS blocks | Advanced host styling integration; treat values as host input |
| `toolInfo` | Tool definition plus optional `tools/call` request ID that instantiated the App | Diagnostics, telemetry correlation, or displaying tool identity |
| `availableDisplayModes` | Modes the host reports it supports | Raw negotiation diagnostics; use `useDisplayMode()` for the runtime's configured-and-host-supported modes |
| `containerDimensions` | Fixed or maximum iframe dimensions | Layout decisions beyond derived `maxWidth` / `maxHeight` |
| Additional keys | Allowed for forward compatibility | Feature-detect; do not assume cross-host support |

```typescript
import { useHostContext } from "mcp-use/react";

function InputHint() {
  const { hostContext } = useHostContext();
  const touch = hostContext?.deviceCapabilities?.touch === true;
  const hover = hostContext?.deviceCapabilities?.hover === true;

  return <p>{touch && !hover ? "Tap an item" : "Select an item"}</p>;
}
```

## Files: standard protocol versus ChatGPT extension

Do not treat all file support as one cross-host API.

| Capability | Classification in beta.66 |
|---|---|
| Host-mediated `ui/download-file` and `hostCapabilities.downloadFile` | Standard MCP Apps protocol capability |
| Public `mcp-use/react` wrapper for standard `ui/download-file` | **Not shipped in beta.66** |
| `useFiles().upload()` | ChatGPT-only wrapper over `window.openai.uploadFile` |
| `useFiles().getDownloadUrl()` | ChatGPT-only wrapper over `window.openai.getFileDownloadUrl` |

The standard protocol can advertise file download support, but beta.66 exposes no public React hook or runtime method for a View author to invoke `ui/download-file`. Checking `hostCapabilities.downloadFile` therefore detects host capability but does not make a standard download callable through the published `mcp-use/react` surface.

`useFiles()` is a separate, narrower ChatGPT extension:

```typescript
useFiles(): UseFilesResult

interface UseFilesResult {
  isSupported: boolean;
  upload(file: File): Promise<FileMetadata>;
  getDownloadUrl(file: FileMetadata): Promise<{ downloadUrl: string }>;
}

type FileMetadata = { fileId: string };
```

```typescript
import { useFiles } from "mcp-use/react";

function FileUpload() {
  const files = useFiles();

  if (!files.isSupported) {
    return <p>This host does not expose the ChatGPT file methods used by this View.</p>;
  }

  async function handleFile(file: File) {
    const uploaded = await files.upload(file);
    const { downloadUrl } = await files.getDownloadUrl(uploaded);
    console.log(downloadUrl);
  }

  return (
    <input
      type="file"
      onChange={(event) => {
        const file = event.currentTarget.files?.[0];
        if (file) void handleFile(file);
      }}
    />
  );
}
```

`isSupported` requires both ChatGPT methods. Unsupported calls reject, so check it before either operation. The beta.66 hook does not wrap other ChatGPT file features such as a host file picker, `selectFiles`, or upload library options.

### Availability snapshot timing

In beta.66, file support is resolved once when the View runtime is created. The files subscription is not updated afterward. If `window.openai` or its file methods are injected later, `useFiles().isSupported` remains at its initial value for that mounted runtime. A fresh iframe/runtime is required to take a new availability snapshot; do not promise reactive late-injection detection.

## Send size changed

Use `useSendSizeChanged()` to notify the host of intrinsic dimensions when `viewConfig.autoResize` is `false`.

```typescript
useSendSizeChanged(): (size: { width?: number; height?: number }) => Promise<void>
```

```typescript
import { useSendSizeChanged } from "mcp-use/react";
import { useEffect, useRef } from "react";

function Chart() {
  const containerRef = useRef<HTMLDivElement>(null);
  const sendSizeChanged = useSendSizeChanged();

  useEffect(() => {
    const element = containerRef.current;
    if (!element) return;
    const { width, height } = element.getBoundingClientRect();
    void sendSizeChanged({ width, height });
  }, [sendSizeChanged]);

  return <div ref={containerRef}>{/* chart content */}</div>;
}
```

Use it for manual sizing, fixed-aspect layouts, or content that changes dimensions while auto-resize is disabled. Do not send duplicate manual hints when `autoResize: true` already manages them. Size hints are advisory; the host decides the final container dimensions.

See `references/18-mcp-apps/view-react/05-display-modes.md` for display-mode and auto-resize interaction.
