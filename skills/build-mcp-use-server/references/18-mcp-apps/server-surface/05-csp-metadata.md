# CSP Metadata

Widget iframes are sandboxed. Any external request (fetch, script, image, embed, redirect) must be explicitly allowed by Content Security Policy. Configure CSP once in your widget metadata; mcp-use generates the right syntax for both protocols.

## Where CSP lives

Set `widgetMetadata.metadata.csp` (in `widget.tsx`) or `server.uiResource({ metadata: { csp } })`.

```typescript
export const widgetMetadata: WidgetMetadata = {
  description: "Display weather",
  props: propSchema,
  metadata: {
    csp: {
      connectDomains: ["https://api.weather.com"],
      resourceDomains: ["https://cdn.weather.com"],
      baseUriDomains: ["https://myserver.com"],
      frameDomains: ["https://trusted-embed.com"],
      redirectDomains: ["https://oauth.provider.com"],
      scriptDirectives: ["'unsafe-eval'"],   // for React bundles
      styleDirectives: [],
    },
  },
};
```

## Field reference

| Field (camelCase) | snake_case (ChatGPT) | Allows |
|---|---|---|
| `connectDomains` | `connect_domains` | `fetch`, `XMLHttpRequest`, `WebSocket`, `EventSource` |
| `resourceDomains` | `resource_domains` | `<script>`, `<style>`, `<img>`, `<link>`, fonts |
| `baseUriDomains` | `base_uri_domains` | `<base href>` (MCP Apps only) |
| `frameDomains` | `frame_domains` | `<iframe>`, `<frame>` embeds |
| `redirectDomains` | `redirect_domains` | Navigation/redirect targets (ChatGPT-specific) |
| `scriptDirectives` | `script_directives` | Custom directives appended to `script-src` (e.g. `'unsafe-eval'`) |
| `styleDirectives` | `style_directives` | Custom directives appended to `style-src` |

## Format differences — same source, two outputs

You write **camelCase**. mcp-use ships:

- **MCP Apps clients** receive `_meta.ui.csp.connectDomains` etc., camelCase preserved.
- **ChatGPT** receives `_meta["openai/widgetCSP"].connect_domains` etc., snake_case keys, openai-prefixed parent.

```typescript
// What you write
metadata: {
  csp: {
    connectDomains: ["https://api.example.com"],
    resourceDomains: ["https://cdn.example.com"],
  }
}

// ChatGPT actually sees
{
  "openai/widgetCSP": {
    connect_domains: ["https://api.example.com"],
    resource_domains: ["https://cdn.example.com"],
  }
}
```

You never write the snake_case form. If you have a legacy `appsSdk` registration with snake_case, migrate via `../../28-migration/04-appssdk-to-mcpapps.md`.

## Auto-injected origins

When `baseUrl` is set (constructor or `MCP_URL` env), mcp-use **auto-adds the server origin** to:

- `connectDomains` — so `useWidget().callTool()` can reach the server.
- `resourceDomains` — so widget JS bundles load.
- `baseUriDomains` — so relative `<a href>` work.

You do **not** need to add your own server origin manually. See `04-baseurl-and-asset-serving.md`.

For auto-discovered bundled widgets, mcp-use also injects dev/build support entries such as the server websocket origin and `'unsafe-eval'` when needed by the widget bundle.

## React-bundle gotcha — `'unsafe-eval'`

Most React bundles use `Function()` or eval-like dynamic code. Without `'unsafe-eval'` in `scriptDirectives`, the widget loads but crashes with a CSP violation:

```typescript
metadata: {
  csp: {
    scriptDirectives: ["'unsafe-eval'"],  // required for typical React bundles
  },
}
```

If you build with a CSP-friendly bundler that emits no eval, you can omit this. Most setups need it.

## Inspector "CSP mode" toggle

The mcp-use Inspector has a CSP mode toggle:

- **Permissive** — Relaxed CSP. Useful while iterating. Hides bugs that production will trigger.
- **Widget-Declared** — Enforces exactly the CSP your widget declares. Production-equivalent.

Test in Widget-Declared mode before shipping. CSP violations log to the console; missing domains surface immediately. See `../../20-inspector/11-protocol-toggle-and-csp-mode.md`.

## Per-scenario examples

### External REST API

```typescript
csp: { connectDomains: ["https://api.example.com"] }
```

### CDN images and scripts

```typescript
csp: { resourceDomains: ["https://cdn.jsdelivr.net", "https://images.unsplash.com"] }
```

### Maps + analytics + React

```typescript
csp: {
  connectDomains: ["https://api.mapbox.com", "https://analytics.example.com"],
  resourceDomains: ["https://api.mapbox.com", "https://tiles.mapbox.com"],
  scriptDirectives: ["'unsafe-eval'"],
}
```

## Related

- `baseUrl` and auto-injection: `04-baseurl-and-asset-serving.md`.
- ChatGPT format conversion: `../chatgpt-apps/04-csp-format-differences.md`.
- Migration of legacy snake_case configs: `../../28-migration/04-appssdk-to-mcpapps.md`.
