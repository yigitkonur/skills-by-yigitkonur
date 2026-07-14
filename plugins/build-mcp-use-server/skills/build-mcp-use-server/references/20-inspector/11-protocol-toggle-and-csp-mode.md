# Protocol Toggle and CSP Mode

Two Inspector controls specific to widget testing: **Protocol Toggle** verifies a widget works across both rendering protocols, and **CSP Mode** surfaces Content Security Policy violations before production.

## Protocol Toggle

### What it switches

Widgets built with `type: "mcpApps"` support both protocols simultaneously. The Inspector lets you flip between them at runtime to verify cross-compatibility without redeploying.

| Mode | Communication | Mock global |
|---|---|---|
| **MCP Apps** | JSON-RPC over `postMessage` | None — use `mcp-use/react` hooks |
| **ChatGPT Apps** | OpenAI Apps SDK | `window.openai` API |

The toggle is hidden for single-protocol widgets:

| Widget `type` | Toggle visible? | Renders with |
|---|---|---|
| `"mcpApps"` | Yes | Either protocol |
| `"appsSdk"` | No | ChatGPT only |

### Where to find it

When viewing a rendered widget result, the Protocol Toggle sits in the widget's debug toolbar above the iframe. Click to switch — the iframe re-mounts with the chosen runtime.

### What to verify in each mode

**MCP Apps mode:**

- Widget calls tools through `useWidget().callTool` or `useCallTool` from `mcp-use/react` and gets results.
- `useWidget` and `useCallTool` hooks resolve correctly.
- `_meta.ui.resourceUri` resolves to the right resource.
- `notifications/list_changed` propagates and refreshes UI.

**ChatGPT Apps mode:**

- `window.openai` API is present.
- `toolInput` / `toolOutput` / `widgetState` / `theme` / `displayMode` all populate.
- `callTool`, `setWidgetState`, `requestDisplayMode`, `sendFollowUpMessage`, `openExternal`, `notifyIntrinsicHeight` all work.
- `openai:set_globals` event fires on every reactive update.

For full ChatGPT-side detail, see `09-debugging-chatgpt-apps.md`.

### Common cross-protocol bugs

- **Hardcoded `window.openai`** — reads break in MCP Apps mode. Use `useWidget` / `useCallTool` from `mcp-use/react`, which abstract both protocols.
- **`structuredContent` shape mismatch** — MCP Apps reads from `structuredContent`; ChatGPT reads from `toolOutput`. mcp-use generates both, but custom servers must too.
- **Missing `_meta` keys** — set both `_meta["openai/outputTemplate"]` and `_meta.ui.resourceUri` to ensure the widget renders in either client.

## CSP Mode

Content Security Policy enforcement controls what the widget iframe is allowed to do. Toggle in the widget debug toolbar.

### Modes

| Mode | Behavior | Use when |
|---|---|---|
| **Permissive** | Relaxed CSP. Inline scripts/styles allowed. Most external resources allowed. | Active development, debugging, prototyping. |
| **Widget-Declared** | The widget's own declared CSP is enforced (matches production). Violations appear in browser console. | Pre-release verification, regression tests. |

### Why this matters

Production hosts (ChatGPT, Claude) enforce strict CSP. A widget that works in dev under Permissive can blow up in production under Widget-Declared:

- `eval()` blocked
- Inline `<script>` blocked
- Cross-origin `fetch` blocked unless declared in `connect-src`
- Inline styles blocked unless `style-src 'unsafe-inline'` is allowed
- Web fonts blocked unless `font-src` allows the origin

### Workflow

1. Build and test widget under **Permissive** for fast iteration.
2. Switch to **Widget-Declared** before merging.
3. Open browser DevTools → Console.
4. Trigger every interactive path in the widget.
5. Fix any `Refused to load …` or `Refused to execute inline script` violations by either:
   - Removing the offending resource (preferred), or
   - Updating the widget's declared CSP via `widgetMeta.csp` on the server.

### Declaring a widget CSP

Server-side, declare CSP in the widget's unified metadata. mcp-use writes protocol-specific CSP metadata for MCP Apps and ChatGPT.

```ts
import type { WidgetMetadata } from 'mcp-use/react'

export const widgetMetadata: WidgetMetadata = {
  description: 'Dashboard widget',
  metadata: {
    csp: {
      connectDomains: ['https://api.example.com'],
      resourceDomains: ['https://cdn.example.com'],
      frameDomains: ['https://trusted-embed.example.com'],
      scriptDirectives: ["'unsafe-eval'"],
    },
  },
}
```

See `../18-mcp-apps/` for the full widget metadata reference and the canonical [Content Security Policy doc](https://manufact.com/docs/typescript/server/content-security-policy).

## Combined verification recipe

For a dual-protocol widget heading to production:

1. **Permissive + MCP Apps** — confirm baseline functionality.
2. **Permissive + ChatGPT Apps** — confirm `window.openai` paths.
3. **Widget-Declared + MCP Apps** — catch CSP violations from the MCP-protocol code path.
4. **Widget-Declared + ChatGPT Apps** — catch CSP violations from the OpenAI code path.
5. **Real ChatGPT** — final smoke test.

## See also

- `09-debugging-chatgpt-apps.md` — full `window.openai` API reference.
- `12-device-and-locale-panels.md` — device, locale, safe-area simulation.
- `../18-mcp-apps/server-surface/` — widget tools and metadata server-side.
- `../18-mcp-apps/widget-react/` — widget components and hooks.
