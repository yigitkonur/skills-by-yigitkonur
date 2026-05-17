# Widget Debugging

Widgets fail in characteristic ways: blank frames, "hooks called outside provider" errors, perpetual `isPending`, plain HTML where a React tree should be. Each maps to a small set of root causes.

For widget testing inside the Inspector (CSP toggle, protocol switch, device/locale panels), see `../20-inspector/11-protocol-toggle-and-csp-mode.md`.

For deep widget patterns (state, streaming, display modes, follow-up messages), see cluster `../18-mcp-apps/widget-react/` and the streaming pattern at `../18-mcp-apps/streaming-tool-props/`.

---

## Symptom: widget shows as plain HTML / unstyled text

The frame loads but renders as raw markup, not a React tree.

| Cause | Diagnosis | Fix |
|---|---|---|
| Tool returned `text(...)` instead of `widget(...)` | Inspect the `tools/call` response — `structuredContent` will be missing | Use `widget({ props, message })` not `text(...)` |
| `widgetMetadata` not registered for the tool | Inspector's Tools tab shows the tool but no widget icon | Add `widgetMetadata` to the tool definition |
| Client doesn't support apps capability | `ctx.client.supportsApps()` returns `false` | This is correct behavior; the text fallback IS the experience for those clients |
| Asset URL unreachable | Browser network tab shows 404 on the widget bundle | Set `MCP_URL` to the public URL the client uses; for tunnels see `02-setup/` |

```typescript
// ❌ wrong — returns plain text
return text(JSON.stringify(props));

// ✅ right — returns widget envelope
return widget({ props, message: "Loaded weather for Tokyo" });
```

---

## Symptom: "hooks called outside provider" error

React throws because `useWidget()` was called from a tree not wrapped in `<McpUseProvider>`.

```tsx
// ❌ wrong — no provider
export default function Widget() {
  const { props } = useWidget();
  return <div>{props.city}</div>;
}

// ✅ right — provider wraps the tree
export default function Widget() {
  return (
    <McpUseProvider>
      <Inner />
    </McpUseProvider>
  );
}

function Inner() {
  const { props } = useWidget();
  return <div>{props.city}</div>;
}
```

The provider initializes the bridge to the host (ChatGPT or Claude). Without it, hooks have no host context to read.

---

## Symptom: `isPending` is stuck `true`

The widget mounts but `props` never arrives — `isPending` stays `true` forever.

| Cause | Diagnosis | Fix |
|---|---|---|
| Tool returned `widget(...)` with no `props` | Inspector RPC panel shows `structuredContent: {}` | Pass real props: `widget({ props: { city: "Tokyo" }, ... })` |
| Bridge initialization failed silently | Browser console has CSP error or network failure | Check Inspector CSP mode; check asset 404s |
| Widget was hot-reloaded without re-rendering | Dev-only; HMR replaced the bridge mid-flight | Hard refresh (Cmd+Shift+R) |
| Streaming tool input still pending | `isStreaming: true`, `partialToolInput` populated | Render `partialToolInput` while streaming, `props` after |

```tsx
function WidgetContent() {
  const { props, isPending, isStreaming, partialToolInput } = useWidget<{ city: string }>();

  // Render the streaming preview, then settle to props
  const display = isStreaming
    ? (partialToolInput?.city ?? "")
    : (props?.city ?? "");

  if (isPending && !isStreaming) return <Skeleton />;
  return <div>{display}</div>;
}
```

---

## Symptom: CSP violation in browser console

Console shows: `Refused to connect to '...' because it violates the following Content Security Policy directive: ...`.

The widget's CSP is enforced when the host serves the widget in production (or when the Inspector's CSP mode is set to **Widget-Declared**).

| Violation | Fix |
|---|---|
| `connect-src` blocked | Add the domain to `widgetMetadata.metadata.csp.connectDomains` |
| `img-src` / `media-src` blocked | Add the domain to `metadata.csp.resourceDomains` |
| Inline `<style>` blocked | Move CSS to imported files (no inline styles) |
| Inline `<script>` blocked | All JS must be bundled, never injected at runtime |
| `eval()` blocked | Same — no `eval`, no `new Function(...)`, no inline event handlers |

```typescript
const widgetMetadata = {
  // ...
  metadata: {
    csp: {
      connectDomains: ["https://api.weatherapi.com"],
      resourceDomains: ["https://cdn.example.com"],
    },
  },
};
```

Test in Inspector: switch CSP mode to **Widget-Declared** before declaring done. Permissive mode hides violations.

---

## Symptom: widget renders in Inspector but not Claude/ChatGPT

| Cause | Diagnosis | Fix |
|---|---|---|
| Inspector ran in Permissive CSP mode | Re-test in Widget-Declared mode in Inspector | Add domains to `metadata.csp` |
| Asset URL points at `localhost` | Production client can't reach localhost | Set `MCP_URL` to the public URL |
| Protocol mismatch | Inspector's protocol toggle showed only one protocol working | Test both MCP Apps + ChatGPT modes; widget code may be branching wrongly |
| Different display mode | Widget assumes inline; client opens in fullscreen | Read `displayMode` from `useWidget()` and adapt |
| Mixed content | Widget loads HTTPS host but tries to connect to HTTP | All asset URLs must be HTTPS in production |

---

## Symptom: state doesn't persist across messages

The user clicks once → state updates. Next message → state reset.

| Cause | Fix |
|---|---|
| Used `useState` instead of `useWidget`'s `state` / `setState` | Switch to `const { state, setState } = useWidget(...)`; see `../18-mcp-apps/widget-react/09-state-persistence.md` |
| Used `localStorage` | Doesn't sync via the bridge; switch to `setState` |
| `setState` called but never awaited | `setState` is async; await it |

---

## Symptom: `requestDisplayMode("fullscreen")` ignored

```tsx
const { displayMode, requestDisplayMode } = useWidget();

// Request fullscreen
await requestDisplayMode("fullscreen");

// Read back — it might still be "inline"
console.log(displayMode); // "inline"
```

`requestDisplayMode` is **advisory**. The host decides whether to honor it. Always read back `displayMode` to know what actually happened, and design the layout to be acceptable in any mode.

---

## Where to look

| Layer | Tool |
|---|---|
| Tool returns wrong shape | Inspector → RPC Messages → `tools/call` response |
| Bridge initialization | Browser DevTools → Console (look for CSP and bridge logs) |
| CSP violations | Browser DevTools → Console with Inspector CSP mode = Widget-Declared |
| Asset 404s | Browser DevTools → Network |
| Bridge state RPC | Browser DevTools → Console; bridge logs `ui/update-model-context` traffic |
| Host context (theme, locale, displayMode) | `<McpUseProvider debugger>` overlay |

---

## Built-in debug overlay

`<McpUseProvider autoSize debugger viewControls>` enables an in-frame overlay. Drop into the dev variant; remove for prod builds.

| Prop | Effect |
|---|---|
| `debugger` | Overlay with raw props, host context, internal state |
| `viewControls` | Manual display-mode toggle for testing inline / pip / fullscreen |
| `autoSize` | Auto-size frame to content (otherwise host-controlled) |

---

## Cross-links

- `../20-inspector/11-protocol-toggle-and-csp-mode.md` — Inspector's CSP/protocol toggles
- `../18-mcp-apps/widget-react/` — deep widget patterns (state, streaming, display modes, follow-up messages)
- `../18-mcp-apps/streaming-tool-props/` — streaming render lifecycle
