# Host context, files, and size

*Read this when you need to detect host capabilities, access the file picker, or manage view dimensions.*

## Host context

Read environment info and available capabilities.

**Signature:**
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

**Example:**
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

Capability-dependent hooks reject unsupported calls. `useHostContext()` exposes the raw negotiated `hostCapabilities` when you need to inspect host support, while `useFiles()` also exposes its own `isSupported` flag.

## File upload and download

Upload a browser `File` through ChatGPT's optional file extension, then request a temporary download URL by opaque file ID. This extension is not part of the shared MCP Apps bridge.

**Signature:**
```typescript
useFiles(): UseFilesResult

interface UseFilesResult {
  isSupported: boolean;
  upload(file: File): Promise<{ fileId: string }>;
  getDownloadUrl(file: { fileId: string }): Promise<{ downloadUrl: string }>;
}
```

**Example:**
```typescript
import { useFiles } from "mcp-use/react";

function FileUpload() {
  const { isSupported, upload, getDownloadUrl } = useFiles();

  if (!isSupported) return <p>File handling requires ChatGPT</p>;

  async function handleFile(file: File) {
    const uploaded = await upload(file);
    const { downloadUrl } = await getDownloadUrl(uploaded);
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

Unsupported `upload()` and `getDownloadUrl()` calls reject, so check `isSupported` first.

## Send size changed

Notify the host of the view's intrinsic dimensions. Required when `viewConfig.autoResize: false`.

**Signature:**
```typescript
useSendSizeChanged(): (size: { width?: number, height?: number }) => Promise<void>
```

**Example:**
```typescript
import { useSendSizeChanged } from "mcp-use/react";
import { useEffect, useRef } from "react";

function Chart() {
  const containerRef = useRef<HTMLDivElement>(null);
  const sendSize = useSendSizeChanged();

  useEffect(() => {
    if (!containerRef.current) return;
    const { width, height } = containerRef.current.getBoundingClientRect();
    sendSize({ width, height });
  }, [sendSize]);

  return <div ref={containerRef}>{/* chart content */}</div>;
}
```

**Use when:**
- `viewConfig.autoResize: false` (you manage dimensions)
- Layout has a fixed aspect ratio (e.g., maps, embedded media)
- Content resizes dynamically (window resize, data changes)

**Do not use when:**
- `autoResize: true` (host manages size automatically)

See `references/18-mcp-apps/view-react/05-display-modes.md` for the interaction with `autoResize`.

## Gotchas

- **Size updates do not re-render the view** → `useSendSizeChanged()` is fire-and-forget
- **`safeArea` is for mobile** → use `top`, `left`, `bottom`, `right` to avoid overlaps with mobile notches and home buttons (e.g., `<div style={{ paddingTop: safeArea.top }}>`)
- **Host may ignore size hints** → the host decides final iframe dimensions; `useSendSizeChanged()` is advisory

