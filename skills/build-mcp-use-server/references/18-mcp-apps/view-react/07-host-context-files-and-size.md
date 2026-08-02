# Host context, files, and size

*Read this when you need to detect host capabilities, access the file picker, or manage view dimensions.*

## Host context

Read environment info and available capabilities.

**Signature:**
```typescript
useHostContext(): HostContextHandle

interface HostContextHandle {
  hostInfo: HostInfo;                    // { name, version }
  availableDisplayModes: DisplayMode[];
  availableCapabilities: string[];       // "message", "files", "screenshot", etc.
  safeAreaInsets: SafeAreaInsets;        // { top, bottom, left, right } — mobile safe zones
}
```

**Example:**
```typescript
import { useHostContext } from "mcp-use/react";

function FeatureDetection() {
  const { hostInfo, availableCapabilities } = useHostContext();

  return (
    <div>
      <p>Host: {hostInfo.name} {hostInfo.version}</p>
      {availableCapabilities.includes("files") && <FileUpload />}
      {!availableCapabilities.includes("message") && <p>Follow-up messages not supported</p>}
    </div>
  );
}
```

**Capabilities** (examples; consult `.d.ts` for the full list):
- `"message"` — `useSendFollowUp()` available
- `"files"` — `useFiles()` available
- `"screenshot"` — host can take view screenshots

Always check before calling hooks that depend on capabilities.

## File picker

Request the user to select files.

**Signature:**
```typescript
useFiles(): UseFilesResult

interface UseFilesResult {
  available: boolean;                      // files capability present
  requestFiles(options: {
    accept?: string[];                     // MIME types: ["image/*", "application/pdf"]
    multiple?: boolean;
  }): Promise<FileMetadata[]>;
}

interface FileMetadata {
  name: string;
  type: string;                            // MIME type
  size: number;
  data?: ArrayBuffer;                      // Content (if provided by host)
}
```

**Example:**
```typescript
import { useFiles } from "mcp-use/react";

function FileUpload() {
  const files = useFiles();

  if (!files.available) return <p>File upload not supported</p>;

  async function handleUpload() {
    try {
      const selected = await files.requestFiles({
        accept: ["image/*", "application/pdf"],
        multiple: true,
      });
      console.log("Selected", selected.length, "files");
    } catch (e) {
      console.error("File selection failed", e);
    }
  }

  return <button onClick={handleUpload}>Upload files</button>;
}
```

**Gotchas:**
- **`data` field may be null** → host may return metadata without content (size, name only)
- **No drag-and-drop by default** → `requestFiles()` opens the file picker; implement drag-and-drop UI separately if needed
- **Accept types are advisory** → host may ignore MIME type filters

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
- **`safeAreaInsets` is for mobile** → use `top`, `left`, `bottom`, `right` to avoid overlaps with mobile notches and home buttons (e.g., `<div style={{ paddingTop: insets.top }}>`)
- **Host may ignore size hints** → the host decides final iframe dimensions; `useSendSizeChanged()` is advisory

