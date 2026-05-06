# MCP Apps vs ChatGPT Apps SDK

Two protocols target the same widget concept. mcp-use lets you author once and ship to both — but you should know which is which.

## Side-by-side

| Feature | MCP Apps (open standard) | ChatGPT Apps SDK (OpenAI) |
|---|---|---|
| Spec | SEP-1865 (MCP extension) | OpenAI proprietary |
| Communication | JSON-RPC 2.0 over `postMessage` | `window.openai.*` global |
| MIME type | `text/html;profile=mcp-app` | `text/html+skybridge` |
| Architecture | Double-iframe sandbox | Single iframe |
| CSP keys | **camelCase** (`connectDomains`) | **snake_case** (`connect_domains`) |
| Metadata namespace | Standard `_meta.ui.*` | `openai/*` prefixed keys |
| State persistence | `ui/update-model-context` JSON-RPC | `window.openai.setWidgetState()` |
| Theme source | `postMessage` event | `window.openai.theme` |
| Follow-up | `ui/message` JSON-RPC | `window.openai.sendFollowUpMessage()` |
| Clients | Claude, Goose, MCP Inspector, etc. | ChatGPT |

## Registration types in mcp-use

```typescript
server.uiResource({ type: "mcpApps", ... });   // Recommended — dual-protocol
server.uiResource({ type: "appsSdk", ... });   // DEPRECATED — ChatGPT only
server.uiResource({ type: "rawHtml", ... });   // Plain HTML, no MCP Apps protocol
server.uiResource({ type: "remoteDom", ... }); // Remote DOM
```

| Type | ChatGPT | MCP Apps clients | Status |
|---|---|---|---|
| `mcpApps` | Yes | Yes | **Recommended** |
| `appsSdk` | Yes | No | **Deprecated** |

Use `type: "mcpApps"` for all new work. The server emits both MIME types and metadata variants automatically; the same widget code runs in both hosts.

## Why `useWidget` exists

Without an abstraction, the same widget must branch on `"openai" in window` to pick a transport. `useWidget` from `mcp-use/react` detects the host once, picks the right bridge, and exposes a single API — props, theme, `callTool`, `setState`, follow-up messages — that works in both. Widget code stays identical.

Direct access to `window.openai` is the wrong default — see `chatgpt-apps/02-window-openai-api.md`.

## CSP is the most visible difference

The same widget is allowed to call the same APIs in both protocols, but the CSP fields are spelled differently. mcp-use generates both spellings from a single camelCase config. Details in `server-surface/05-csp-metadata.md` and `chatgpt-apps/04-csp-format-differences.md`.

## Decision

- **New widget?** `type: "mcpApps"`.
- **Existing `appsSdk` registration?** Migrate. Code in the widget itself usually does **not** need to change — start with the registration. See `../28-migration/04-appssdk-to-mcpapps.md`.
- **Need ChatGPT-only behavior?** Stay on `mcpApps` and pass ChatGPT-specific keys (`widgetDescription`, `widgetAccessible`) in the same `metadata` object — the adapter routes them.

## Cross-references

- Server-side dual emission: `chatgpt-apps/05-dual-protocol-via-mcpapps.md`.
- Runtime detection inside the widget: `chatgpt-apps/07-runtime-detection.md`.
- The `appsSdk` deprecation: `chatgpt-apps/06-deprecation-of-appssdk.md`.
