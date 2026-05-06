# Integration

Mount the Inspector as a route on your own Express or Hono app. With `mcp-use/server` this happens automatically; with raw frameworks, use `mountInspector`.

## Auto-mount with mcp-use

`MCPServer.listen()` mounts the Inspector at `/inspector` automatically.

```ts
import { MCPServer } from 'mcp-use/server'

const server = new MCPServer({ name: 'my-server', version: '1.0.0' })
server.addTool(/* ... */)
server.listen(3000)
// Inspector → http://localhost:3000/inspector
```

No further setup required. `mcp-use dev` enables dev mode for HMR.

## Manual integration with `mountInspector`

### Express

```ts
import express from 'express'
import { mountInspector } from '@mcp-use/inspector'

const app = express()

app.get('/api/health', (req, res) => res.json({ status: 'ok' }))

mountInspector(app)

app.listen(3000)
// Inspector → http://localhost:3000/inspector
```

### Hono

```ts
import { Hono } from 'hono'
import { mountInspector } from '@mcp-use/inspector'

const app = new Hono()
app.get('/api/health', (c) => c.json({ status: 'ok' }))

mountInspector(app)
export default app
```

Framework is auto-detected. As of v3.0.1 Hono detection is duck-typed (`.fetch(Request) => Response`) instead of `instanceof`, so it works when host and inspector resolve different Hono module records.

## Custom mount path

The default mount is `/inspector`. Move it with a sub-router.

### Express

```ts
const inspectorRouter = express.Router()
mountInspector(inspectorRouter)
app.use('/debug', inspectorRouter)
// Inspector → http://localhost:3000/debug/inspector
```

### Hono

```ts
const inspectorApp = new Hono()
mountInspector(inspectorApp)
app.route('/debug', inspectorApp)
// Inspector → http://localhost:3000/debug/inspector
```

## `mountInspector` options

```ts
mountInspector(app, {
  autoConnectUrl: 'http://localhost:3000/mcp',
  devMode: true,
  sandboxOrigin: 'https://sandbox.example.com',
})
```

| Option | Type | Default | Purpose |
|---|---|---|---|
| `autoConnectUrl` | `string \| null` | undefined | MCP server URL to auto-connect on load |
| `devMode` | `boolean` | `true` if not production | Same-origin sandbox for MCP Apps widgets — required behind reverse proxies that lack a `sandbox-{hostname}` subdomain |
| `sandboxOrigin` | `string \| null` | undefined | Override the sandbox origin for MCP Apps widget iframes |

When using `mcp-use/server`, `devMode` is set to `true` in development and `false` in production automatically.

## Embeddable chat components

The inspector exports React components from `@mcp-use/inspector/client` for use in your own app.

### `ChatTab` quick-start

```tsx
import { ChatTab } from '@mcp-use/inspector/client'

<ChatTab
  connection={connection}
  isConnected={isConnected}
  prompts={prompts}
  serverId={serverId}
  callPrompt={callPrompt}
  readResource={readResource}
  hideTitle
  hideModelBadge
  hideServerUrl
  clearButtonLabel="Start over"
  clearButtonHideShortcut
  clearButtonVariant="ghost"
/>
```

### `ChatTab` customization props

| Prop | Type | Effect |
|---|---|---|
| `hideTitle` | boolean | Hide chat header title |
| `hideModelBadge` | boolean | Hide selected-model badge |
| `hideServerUrl` | boolean | Hide MCP server URL in landing state |
| `clearButtonLabel` | string | Custom label for clear/new-chat button |
| `clearButtonHideIcon` | boolean | Hide icon |
| `clearButtonHideShortcut` | boolean | Hide keyboard shortcut hint |
| `clearButtonVariant` | `default \| secondary \| ghost \| outline` | Button variant |
| `hideToolSelector` | boolean | Hide tool selector (disabled tools sent as `disabledTools`) |
| `managedLlmConfig` | LLM config | Host-managed LLM config; bypasses local API-key UI |
| `enableFreeTierUpgrade` | boolean | Opt in to Manufact free-tier upgrade UI; default `false` |
| `hideClearButton` | boolean | Hide the new-chat / clear button |
| `chatQuickQuestions` | string[] | Initial quick questions below the landing input |
| `chatFollowups` | string[] | Initial follow-ups above the active chat input |
| `streamProtocol` | `sse \| data-stream` | Inspector SSE (default) or Vercel AI SDK data-stream |
| `credentials` | `RequestCredentials` | e.g. `"include"` for cross-origin cookies |
| `extraHeaders` | `Record<string,string>` | Headers on every streaming POST |
| `body` | `(messages) => unknown` | Custom JSON body builder |

### Lower-level components

For custom layouts, compose `MessageList`, `ChatHeader`, `ChatLandingForm` from `@mcp-use/inspector/client` directly. When using `MessageList`, pass `serverBaseUrl` from your MCP connection URL so widget resource rendering uses the correct origin.

## Environment-specific behavior

### Reverse proxies (ngrok, E2B, Cloudflare)

Set `MCP_URL` to the public-facing URL:

```bash
MCP_URL=https://abc123.ngrok.io npx @mcp-use/cli dev
```

This routes widget asset URLs and Vite HMR WebSockets through the proxy. `devMode` enables same-origin sandboxing automatically in dev so widgets work without a `sandbox-{hostname}` subdomain.

### Widgets accessing the server URL

Widgets should read the server base URL from `useWidget().mcp_url` instead of hardcoding `localhost`. Internally, mcp-use derives this from `window.__mcpPublicUrl`.

> Source note: canonical Inspector docs still mention `window.__mcpServerUrl`; `mcp-use@1.26.0` exposes `window.__mcpPublicUrl` plus `useWidget().mcp_url`, so the package surface wins.

```ts
import { useWidget } from 'mcp-use/react'

const { mcp_url } = useWidget()
const data = await fetch(`${mcp_url}/api/data`)
```

### Embedding inspector iframes

Set `MCP_INSPECTOR_FRAME_ANCESTORS` to whitelist embedding origins:

```bash
MCP_INSPECTOR_FRAME_ANCESTORS="https://app.example.com https://admin.example.com" node server.js
```

## Auth in front of the inspector

Wrap with auth middleware before mounting:

```ts
app.use('/inspector', requireAuth)
mountInspector(app)
```

Recommended for staging deployments that expose the inspector on the open internet.

## CORS

If the MCP server lives on a different origin from the host app:

```ts
app.use(cors({
  origin: ['http://localhost:3000', 'https://your-domain.com'],
  credentials: true,
}))
mountInspector(app)
```

## Troubleshooting

**Blank inspector page** — client files not built. Run `yarn build` in the inspector package or reinstall `@mcp-use/inspector`.

**Route conflicts** — your app's routes overlap with `/inspector/*`. Use a custom mount path.

**Build errors** — verify `@mcp-use/inspector` is installed, Node ≥ 18, and dependencies are present.

## See also

- `02-cli.md` — standalone CLI mode.
- `10-self-hosting.md` — Docker deployment.
- `11-protocol-toggle-and-csp-mode.md` — widget debug controls.
