# ChatGPT Apps SDK — Protocol Overview

The ChatGPT Apps SDK is OpenAI's proprietary protocol for embedding interactive widgets in ChatGPT. It predates the open MCP Apps standard; mcp-use supports it as a second backend so the same widget code ships to both ChatGPT and MCP Apps clients.

## How it differs from MCP Apps

| Aspect | MCP Apps (open) | ChatGPT Apps SDK |
|---|---|---|
| Spec owner | MCP community (SEP-1865) | OpenAI |
| Communication | JSON-RPC 2.0 over `postMessage` | `window.openai.*` global API |
| MIME type | `text/html;profile=mcp-app` | `text/html+skybridge` |
| Architecture | Double-iframe sandbox | Single iframe |
| CSP keys | camelCase | snake_case |
| Metadata namespace | `_meta.ui.*` | `_meta["openai/*"]` |
| State persistence | `ui/update-model-context` JSON-RPC | `window.openai.setWidgetState()` |
| Theme | postMessage event | `window.openai.theme` |
| Follow-up messages | `ui/message` JSON-RPC, accepts content blocks | `window.openai.sendFollowUpMessage({ prompt })`, text prompt only |
| Display modes | `inline | pip | fullscreen` | Same; behavior slightly different |

## Mental model

```
┌──────────────────────────────────────┐
│  Widget Code (React + useWidget)     │
├──────────────────────────────────────┤
│  Runtime Detection Layer             │
├─────────────────┬────────────────────┤
│  MCP Apps Mode  │  ChatGPT Mode      │
│  (postMessage)  │  (window.openai)   │
└─────────────────┴────────────────────┘
```

When loaded inside ChatGPT, the iframe has `window.openai` injected. The `useWidget` hook detects it and uses the OpenAI bridge. When loaded in an MCP Apps client (Claude, Goose), the iframe communicates via `postMessage` JSON-RPC.

## What ChatGPT requires

- **HTTPS** — ChatGPT only loads widgets from HTTPS endpoints. No `http://` in production.
- **CORS** — Configure `MCPServer({ cors })` if you need to restrict browser origins. `allowedOrigins` is DNS-rebinding Host-header validation, not CORS.
- **Public reachability** — The MCP server URL must be reachable from the public internet. Use a tunnel (`ngrok`, Cloudflare Tunnel) for local dev.

```typescript
const server = new MCPServer({
  name: "my-widget-app",
  version: "1.0.0",
  cors: {
    origin: [
      "https://chat.openai.com",
      "https://chatgpt.com",
    ],
  },
  allowedOrigins: [
    "https://my-server.example.com",
  ],
});
```

Use `allowedOrigins` for the public hostnames your server should accept in the `Host` header.

## Adding a server in ChatGPT

ChatGPT (Developer Mode) lets users register MCP servers via Connectors → Advanced. Point it at your server URL:

```
https://my-server.example.com/mcp
```

For local development, expose via tunnel:

```bash
ngrok http 3000
# point ChatGPT at https://abc123.ngrok.io/mcp
```

## What works automatically with `type: "mcpApps"`

When you register a widget with `type: "mcpApps"`, mcp-use:

1. Registers the MCP Apps resource shape (`text/html;profile=mcp-app`).
2. Generates both metadata payloads — `_meta.ui.*` for MCP Apps and `_meta["openai/*"]` for ChatGPT tool/resource metadata.
3. Converts CSP camelCase → snake_case for ChatGPT.
4. Enriches the server's own origin into MCP Apps CSP before registration; legacy `appsSdk` auto-registration has separate OpenAI-origin defaults.

You don't write protocol-specific code.

## ChatGPT-only metadata fields

Some fields make sense only in ChatGPT. Pass them in the same `metadata` object — adapters route them:

| Field | ChatGPT only | Purpose |
|---|---|---|
| `widgetDescription` | Yes | Extra LLM-facing description shown in ChatGPT context |
| `domain` | Yes | Maps to `openai/widgetDomain` for custom-domain attribution |
| `widgetAccessible` | Yes | A11y compliance flag |
| `locale` | Yes | Force a BCP-47 locale |
| `csp.redirectDomains` | Yes | CSP redirect-target allowlist |

MCP Apps clients ignore these.

## When you'd use `type: "appsSdk"` instead

You wouldn't, for new code. `type: "appsSdk"` is legacy — see `06-deprecation-of-appssdk.md`. The only reason to keep an `appsSdk` registration is compatibility while you migrate.

**Canonical doc:** https://manufact.com/docs/guides/chatgpt-apps-flow
