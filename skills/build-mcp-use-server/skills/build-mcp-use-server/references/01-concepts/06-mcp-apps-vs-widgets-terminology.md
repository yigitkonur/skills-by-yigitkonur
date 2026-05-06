# MCP Apps vs widgets — vocabulary

The widget-rendering surface of mcp-use has overlapping terminology. Keep these distinct.

## The four words

| Term | What it means | Scope |
|---|---|---|
| **MCP Apps** | The open standard widget protocol — JSON-RPC 2.0 over `postMessage` between widget iframe and host. MIME type `text/html;profile=mcp-app`. | Cross-host (Claude, Goose, any MCP-compliant client). CSP fields use camelCase (`connectDomains`). |
| **ChatGPT Apps SDK** | OpenAI's proprietary widget protocol — `window.openai` global API. MIME type `text/html+skybridge`. | ChatGPT-only. CSP fields use snake_case (`connect_domains`). Deprecated in favor of MCP Apps for new builds. |
| **Widget** | The collective UI artifact — an interactive React (or HTML / Remote DOM) view that renders inside an iframe sandbox in a host. | Either protocol. The user-facing word. |
| **UI resource** | The server-side artifact: a resource registered via `server.uiResource(...)` with one of the widget MIME types, OR a `tool.widget` config that points at a `resources/<name>/widget.tsx`. | The server-side concept. |

## How `mcp-use` handles both protocols

- `server.uiResource({ type: "mcpApps", ... })` registers a UI resource that works in **both MCP Apps and ChatGPT Apps SDK** hosts. mcp-use auto-generates the right MIME and CSP variant.
- `useWidget()` (the React hook) abstracts the protocol difference — your widget code is the same regardless of host.
- `type: "appsSdk"` is **deprecated**. Use `type: "mcpApps"` for dual-protocol support.

## Quick decision

- Building a widget that needs to work in ChatGPT and MCP Apps clients → `type: "mcpApps"`.
- Building a widget for a single MCP Apps host → `type: "mcpApps"`.
- Building a widget only for ChatGPT and you must use the legacy SDK → `type: "appsSdk"` (and prepare for migration).
- Building plain server-rendered HTML for a host that doesn't support widgets → `type: "rawHtml"`.
- Building a Remote DOM widget (mcp-ui spec, not iframes) → `type: "remoteDom"`.

## Read next

- `18-mcp-apps/01-what-are-mcp-apps.md`
- `18-mcp-apps/02-mcp-apps-vs-chatgpt-apps-sdk.md`
- `18-mcp-apps/04-when-to-use-vs-tools-only.md`

**Canonical doc:** https://manufact.com/docs/typescript/server/mcp-apps
