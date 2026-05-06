# Debugging ChatGPT Apps

The Inspector emulates the OpenAI Apps SDK runtime — including the full `window.openai` API — so widgets render identically in the Inspector and in ChatGPT. Use this for development and pre-flight verification.

## Two protocols, one toggle

mcp-use widgets can target two protocols:

| Protocol | Standard | Clients | Communication |
|---|---|---|---|
| **MCP Apps** | MCP standard | Claude, Goose, generic MCP clients | JSON-RPC over `postMessage` |
| **ChatGPT Apps SDK** | OpenAI proprietary | ChatGPT | `window.openai` API |

`type: "mcpApps"` widgets target both protocols simultaneously. `type: "appsSdk"` widgets target ChatGPT only.

For dual-protocol widgets, the Inspector shows a **Protocol Toggle** to switch the runtime. See `11-protocol-toggle-and-csp-mode.md`.

## `window.openai` emulation

When testing under the ChatGPT Apps SDK protocol, the Inspector injects a complete `window.openai` mock into the widget iframe.

### Reactive globals

These properties update reactively. Components can subscribe via `openai:set_globals` events.

| Property | Value |
|---|---|
| `toolInput` | Tool call arguments from the model |
| `toolOutput` | Structured tool output (primary widget data) |
| `toolResponseMetadata` | `_meta` from the tool result |
| `widgetState` | Persistent per-widget state |
| `displayMode` | `"inline" \| "pip" \| "fullscreen"` |
| `theme` | `"light" \| "dark"` (syncs with Inspector theme) |
| `maxHeight` | Max widget container height (px), default 600 |
| `locale` | User locale (default `"en-US"`) |
| `safeArea` | `{ insets: { top, bottom, left, right } }` |
| `userAgent` | `{ device: { type }, capabilities: { hover, touch } }` |

### Methods

#### `callTool(name, params)`

Call any MCP tool from the widget. Inspector executes via the live MCP connection. Tool calls have a 30 s timeout. The returned result uses the MCP `content` field, with `structuredContent` and `_meta` preserved when present.

```ts
const result = await window.openai.callTool('get_restaurants', {
  city: 'San Francisco',
  category: 'pizza',
})
// { content: [{ type: 'text', text: '…' }] }
```

#### `sendFollowUpMessage(args)`

Post a follow-up message to the chat as if the user typed it.

```ts
await window.openai.sendFollowUpMessage({
  prompt: 'Show me more details about the first restaurant',
})
```

In the Inspector this surfaces in the Chat tab via the `mcp-inspector:widget-followup` custom event.

#### `setWidgetState(state)`

Persist widget state in `localStorage` keyed by widget instance ID. Visible to ChatGPT in production.

```ts
await window.openai.setWidgetState({
  favorites: ['restaurant-1', 'restaurant-2'],
  filters: { price: '$$' },
})
```

#### `requestDisplayMode(options)`

Request a display mode change. Uses the native Fullscreen API when available; on mobile, PiP may be coerced to fullscreen.

```ts
const result = await window.openai.requestDisplayMode({ mode: 'fullscreen' })
// { mode: 'fullscreen' }
```

#### `openExternal(payload)`

Open a URL in a new tab with `noopener,noreferrer`.

```ts
window.openai.openExternal({ href: 'https://example.com' })
window.openai.openExternal('https://example.com')  // string form
```

#### `notifyIntrinsicHeight(height)`

Tell the host the widget's natural content height for auto-sizing. The Inspector resizes the iframe and caps height per display mode. `McpUseProvider autoSize` calls this for you.

```ts
await window.openai.notifyIntrinsicHeight(800)
```

### Events

`openai:set_globals` fires whenever any reactive global changes — initial load, theme change, display mode change, tool result arrival.

```ts
window.addEventListener('openai:set_globals', (event) => {
  const { globals } = event.detail
  // globals: { toolInput, toolOutput, widgetState, displayMode,
  //            maxHeight, theme, locale, safeArea, userAgent, ... }
})
```

For React, subscribe with `useSyncExternalStore` keyed on `openai:set_globals` if you need direct `window.openai` access. Prefer the exported `useWidget` hook from `mcp-use/react`, which wraps this pattern — see `../18-mcp-apps/widget-react/03-usewidget-hook.md`.

## Inspector debug controls

### Console proxy

Forward `console.log` from the widget iframe to the page console.

1. Open the **Console** panel (terminal icon).
2. Toggle **"Proxy logs to page console"**.
3. Logs appear in browser DevTools prefixed with `[WIDGET CONSOLE]`.

Log levels (`error`, `warn`, `info`, `debug`, `trace`) are preserved. Objects are JSON-stringified. Preference persists in `localStorage`.

### Widget state inspection

`WidgetInspectorControls` lets you view, in real time:

- `Props` — `structuredContent` from server
- `Tool Input` — original arguments
- `Output` — `toolOutput` / `structuredContent`
- `Metadata` — `_meta` (a.k.a. `toolResponseMetadata`)
- `State` — persistent `widgetState`
- `Theme` — light / dark
- `Display Mode` — inline / pip / fullscreen
- `Safe Area` — insets
- `User Agent` — device capabilities
- `Locale`

Widgets that include `<McpUseProvider debugger>` or `<WidgetControls />` surface debug info automatically.

A widget can respond to inspector state-inspection requests by listening for `mcp-inspector:getWidgetState` and replying with `mcp-inspector:widgetStateResponse`.

## Widget rendering lifecycle

Widgets render **before** the tool finishes — they should show a loading state.

1. Tool called → widget iframe created immediately
2. Widget renders with `isPending: true`, props empty
3. Tool completes → `window.openai.toolOutput` updates
4. `openai:set_globals` event fires → widget switches to `isPending: false`

Verify with a >2 s tool and console logs:

```text
[MyWidget] isPending: true,  props: {}
[MyWidget] isPending: false, props: { city: '…' }
```

## Tool-result format conversion

The Inspector normalizes tool results on their way to widgets. `mcp-use@1.26.0` uses the MCP `content` field and preserves `structuredContent` and `_meta`.

| MCP / mcp-use result | Widget-facing normalized result |
|---|---|
| `{ "content": [{ "type": "text", "text": "…" }] }` | `{ "content": [{ "type": "text", "text": "…" }], "structuredContent": { ... }, "_meta": { ... } }` |

## Differences from real ChatGPT

| Aspect | Inspector | ChatGPT |
|---|---|---|
| User Agent | Mock | Real device |
| Safe Area | Zero insets | Mobile-specific |
| Locale | Defaults `en-US` | User's locale |
| Tool result format | Normalized from MCP `content` | Native |
| Follow-ups | Surface in Inspector Chat tab | Sent to model |

Always finish with a real ChatGPT test before release.

## Debug workflow

1. **Connect** to the server (local or tunneled).
2. **Test tools** — execute each, verify schema and response.
3. **Test widgets** — execute widget-bearing tools, render, toggle Protocol if dual.
4. **Test devices** — Desktop / Mobile / Tablet via Device Emulation. See `12-device-and-locale-panels.md`.
5. **Test CSP** — switch CSP mode to **Widget-Declared** to surface violations. See `11-protocol-toggle-and-csp-mode.md`.
6. **Test in Chat** — drive tool selection from an LLM.
7. **Test in real ChatGPT** — final verification.

## Common issues

| Symptom | Check |
|---|---|
| Widget not rendering (MCP Apps) | `_meta.ui.resourceUri` set; `ui/resourceUri` flat form is deprecated |
| Widget not rendering (ChatGPT) | `_meta["openai/outputTemplate"]` set; resource exists at that path |
| `callTool` rejects | Tool name matches registered tool; arguments match schema; auth headers set |
| Display-mode change differs from request | Host may decline or coerce; mobile PiP may resolve as fullscreen |
| `notifyIntrinsicHeight` no-ops in fullscreen | Height is capped to viewport in fullscreen / pip — by design |

## See also

- `11-protocol-toggle-and-csp-mode.md` — Protocol Toggle and CSP modes.
- `12-device-and-locale-panels.md` — device, locale, timezone, safe-area simulation.
- `../18-mcp-apps/` — building widget tools server-side.
- [OpenAI Apps SDK reference](https://developers.openai.com/apps-sdk/reference)
