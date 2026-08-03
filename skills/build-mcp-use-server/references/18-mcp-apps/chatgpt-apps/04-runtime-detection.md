# Runtime Decisions: Capabilities First, Host Name Last

*Read this if a View may need different behavior across hosts. Most Views should not detect ChatGPT at all.*

Use standard hooks and capability checks. Do not read `window.openai` directly to decide normal View behavior, and do not use `hostInfo.name` as a security or feature-availability guarantee.

## Shipped Host Context Shape

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

`hostInfo` and `hostCapabilities` come from the standard MCP Apps `ui/initialize` handshake. They are unavailable before the bridge connects. The complete public shape is documented in `references/18-mcp-apps/view-react/07-host-context-files-and-size.md`.

## Gate the Operation You Need

Capabilities are optional object-valued fields, not strings or booleans. Presence means support.

```typescript
const { hostCapabilities } = useHostContext();

const canSendFollowUp = hostCapabilities?.message !== undefined;
const canOpenLinks = hostCapabilities?.openLinks !== undefined;
const canCallServerTools = hostCapabilities?.serverTools !== undefined;
const canReadServerResources = hostCapabilities?.serverResources !== undefined;
```

Do not use `.includes()` and do not combine distinct capabilities into one check.

```typescript
// Preferred: gate the specific standard operation.
if (hostCapabilities?.message !== undefined) {
  await sendFollowUp({ prompt: "Show another result" });
}

// Avoid: self-reported name does not establish capability.
if (hostInfo?.name === "ChatGPT") {
  // This says nothing reliable about message, link, or tool support.
}
```

Shipped standard runtime methods also enforce their required capabilities at the call site.

## What `hostInfo` Is Good For

Use `hostInfo` for diagnostics or low-stakes presentation hints:

```typescript
const { hostInfo, locale, isAvailable } = useHostContext();

useEffect(() => {
  if (!isAvailable) return;
  console.debug("[view-host]", {
    name: hostInfo?.name,
    version: hostInfo?.version,
    locale,
  });
}, [isAvailable, hostInfo, locale]);
```

`hostInfo.name` is self-reported by the host. It is not cryptographically verified and must not control authorization, access to secrets, or trust decisions.

There is no `organizationId`, `conversationId`, or `threadId` field on `useHostContext()`. Do not invent them or scrape them from browser globals.

## ChatGPT-Specific Branches Do Not Need Manual Detection

The shipped runtime handles its two verified ChatGPT branches internally:

- `useViewState()` uses `window.openai.setWidgetState` and `openai:set_globals` when that state API exists; otherwise it uses standard `App.updateModelContext()` when supported.
- `useFiles()` checks the two wrapped ChatGPT file methods and exposes `isSupported`.

Use those APIs directly:

```typescript
const [state, setState] = useViewState({ selectedId: null });
const files = useFiles();

if (files.isSupported) {
  const { fileId } = await files.upload(file);
  const { downloadUrl } = await files.getDownloadUrl({ fileId });
}
```

Do not add your own `window.openai` branch around them.

## `useFiles()` Detection Limit

Shipped `view-runtime.ts` computes file support when the View runtime is created. `isSupported` requires both `window.openai.uploadFile` and `window.openai.getFileDownloadUrl`. The files channel is not updated after initialization in beta.66, so methods injected later are not reflected without recreating the runtime/iframe.

This is a runtime-capture limitation, not a reason to poll `window.openai` directly. Test the actual mounted View in real ChatGPT.

The full official ChatGPT file API also includes `selectFiles()` and an upload `{ library: true }` option; beta.66 `useFiles()` does not wrap them.

## Display Mode Uses Its Own Hook

```typescript
const {
  displayMode,
  availableDisplayModes,
  requestDisplayMode,
} = useDisplayMode();
```

Use `useDisplayMode()` rather than searching raw host globals. The host may grant a different mode from the one requested.

Use `maxHeight` and `maxWidth` from `useHostContext()` for host bounds, and `useSendSizeChanged()` to report the View's intrinsic size. There is no `dimensions: { width, height }` field.

## Verification Boundary

Current Inspector source validates the standard MCP Apps host bridge, host context/capabilities, display/layout controls, and declared CSP. It does **not** expose a verified MCP Apps-versus-ChatGPT host protocol toggle.

A connection setting labeled MCP protocol version selects MCP wire-version negotiation; it is not ChatGPT emulation. Inspector may supply mock file helpers in an MCP Apps preview, but mocks do not prove real ChatGPT injection timing, persistence, permissions, file-library behavior, or submission policy.

Use Inspector for:

- standard capability gating;
- standard hook behavior;
- layout, theme, locale, safe-area, and display-mode testing;
- standard CSP in Permissive and Widget-Declared modes.

Use real ChatGPT for:

- `useViewState()` restoration through `window.openai.widgetState`;
- `openai:set_globals` behavior;
- real `useFiles()` uploads and temporary download URLs;
- ChatGPT descriptor extensions, domain submission, and redirect policy.

For a CLI-owned listener, Inspector is normally mounted under `<basePath>/inspector` (for example `/mcp/inspector`). Direct `server.listen()`, `server.fetch`, and embedded Next.js handlers do not auto-mount it; use the external Inspector for those topologies.

## See Also

- `references/18-mcp-apps/05-host-capability-detection.md` — standard capability inventory
- `references/18-mcp-apps/view-react/07-host-context-files-and-size.md` — full hook and file-wrapper surface
- `01-dual-protocol.md` — one server wire and the verified runtime branches
- `references/20-inspector/08-debugging-chatgpt-apps.md` — standard Inspector checks versus real ChatGPT checks
