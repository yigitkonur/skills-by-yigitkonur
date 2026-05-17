# What MCP Apps Are

An **MCP App** is an interactive UI widget returned by an MCP tool. The LLM calls a tool, the server returns structured data, and a widget renders it as a rich component — not just text — inside a chat client (Claude, Goose, ChatGPT, etc.).

## Architecture

The widget is HTML/JS shipped as a UI resource and embedded in a sandboxed iframe by the host. It talks to the server **over JSON-RPC carried on `postMessage`** between the iframe and the host page. The host bridges the iframe's RPC to the live MCP session.

```
User: "Show me the weather in Paris"
  ↓ LLM
tool call: get-weather { city: "Paris" }
  ↓ server
widget({ props: { city, temp, conditions }, output: text("...") })
  ↓ host
iframe sandbox renders <WeatherWidget /> from props
```

## Three visibility channels

A widget tool result has three fields with different audiences:

| Field | LLM sees? | Widget sees? | Purpose |
|---|---|---|---|
| `content` | **Yes** | Yes | Text summary for the model's conversation context |
| `structuredContent` | **No** | Yes (as `props`) | Render data for the widget |
| `_meta` | **No** | Yes (as `metadata`) | Private/UI-only hydration data |

This separates the model transcript from widget rendering data. `metadata` is not added to the model context, but it is still delivered to the host/widget, so do not put credentials in any tool-result channel.

## MIME types

| Protocol | MIME |
|---|---|
| MCP Apps standard (SEP-1865) | `text/html;profile=mcp-app` |
| ChatGPT Apps SDK (legacy) | `text/html+skybridge` |

mcp-use auto-emits both variants when you register a widget with `type: "mcpApps"` — see `02-mcp-apps-vs-chatgpt-apps-sdk.md` and `chatgpt-apps/03-skybridge-mime.md`.

## Why widgets, not plain text

Widgets earn their cost when the data is **inherently visual** (charts, maps, product cards), **interactive** (filters, selections, multi-step flows), or **dense** (tables, dashboards) where text is lossy. For everything else, plain `text()` is faster, cheaper, and works in every client. See `04-when-to-use-vs-tools-only.md`.

## Where this maps in the codebase

- Server side — the `widget()` helper, `server.uiResource()`, and the `widget` config on `server.tool()`. See `server-surface/`.
- Client side — `useWidget`, `useCallTool`, `McpUseProvider`, host context. Covered in the `widget-react/` cluster.
- Streaming partial tool input into a widget — covered in `streaming-tool-props/`.
- Real-world patterns and recipes — covered in `widget-recipes/` and `widget-anti-patterns/`.

## Vocabulary at a glance

- **Widget** / **MCP App** — the UI component rendered by the host.
- **`widget()` helper** — server-side function that builds the widget tool result.
- **`useWidget`** — client-side React hook that exposes props, host context, and actions.
- **`uiResource`** — a registered HTML/JS template the host loads into the iframe.

Full term-by-term breakdown in `03-vocabulary.md`.

**Canonical doc:** https://manufact.com/docs/typescript/server/mcp-apps
