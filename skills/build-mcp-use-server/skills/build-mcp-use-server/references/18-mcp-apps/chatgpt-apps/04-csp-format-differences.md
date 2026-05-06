# CSP Format Differences

The single most visible difference between MCP Apps and ChatGPT is CSP key naming. MCP Apps uses **camelCase**; ChatGPT uses **snake_case**. mcp-use generates both from a single camelCase config.

## The mapping

| MCP Apps (you write this) | ChatGPT (auto-generated) | Allows |
|---|---|---|
| `connectDomains` | `connect_domains` | fetch, XHR, WebSocket |
| `resourceDomains` | `resource_domains` | scripts, styles, images |
| `baseUriDomains` | `base_uri_domains` | base URI (MCP Apps only) |
| `frameDomains` | `frame_domains` | iframe embeds |
| `redirectDomains` | `redirect_domains` | redirects (ChatGPT-specific) |
| `scriptDirectives` | `script_directives` | custom script CSP directives |
| `styleDirectives` | `style_directives` | custom style CSP directives |

## Single-source workflow

You write **camelCase** in your `widgetMetadata.metadata.csp` — once.

```typescript
export const widgetMetadata: WidgetMetadata = {
  description: "Widget with external API access",
  props: z.object({ data: z.any() }),
  metadata: {
    csp: {
      connectDomains: ["https://api.example.com"],
      resourceDomains: ["https://cdn.example.com"],
    },
    prefersBorder: true,
  },
};
```

mcp-use ships:

- **MCP Apps clients** receive `_meta.ui.csp.connectDomains` etc.
- **ChatGPT** receives `_meta["openai/widgetCSP"].connect_domains` etc.

```json
// What ChatGPT sees
{
  "openai/widgetCSP": {
    "connect_domains": ["https://api.example.com"],
    "resource_domains": ["https://cdn.example.com"]
  }
}
```

You never edit the snake_case form.

## What the parent CSP key is wrapped in

For ChatGPT, the whole CSP object is nested under `openai/widgetCSP`:

```json
"_meta": {
  "openai/widgetCSP": {
    "connect_domains": [...],
    "resource_domains": [...]
  }
}
```

For MCP Apps it's nested under `_meta.ui.csp`:

```json
"_meta": {
  "ui": {
    "csp": {
      "connectDomains": [...],
      "resourceDomains": [...]
    }
  }
}
```

Both are auto-generated. You only write the inner camelCase fields.

## Auto-injected origins

In addition to the conversion, `mcp-use@1.26.0` auto-adds:

- The server's own origin (from `baseUrl` / `MCP_URL`) to `connectDomains`, `resourceDomains`, and `baseUriDomains` for `type: "mcpApps"`.
- Separate legacy `appsSdk` auto-registration can seed `*.oaistatic.com` / `*.oaiusercontent.com` in `openai/widgetCSP.resource_domains`; do not rely on that for unified `metadata.csp`.

You don't list your own server origin manually; list external origins your widget actually uses.

## React-bundle directive

Most React bundles need `'unsafe-eval'` in `scriptDirectives`. The conversion preserves this:

```typescript
csp: { scriptDirectives: ["'unsafe-eval'"] }
```

→ ChatGPT sees `"script_directives": ["'unsafe-eval'"]`.

## When you'd see snake_case in your code

Only if you're maintaining a legacy `type: "appsSdk"` registration with `appsSdkMetadata`:

```typescript
// DEPRECATED — only here as legacy reference
appsSdkMetadata: {
  "openai/widgetCSP": {
    connect_domains: ["https://api.example.com"],   // snake_case
  }
}
```

Migrate to `type: "mcpApps"` and camelCase. See `06-deprecation-of-appssdk.md` and `../../28-migration/04-appssdk-to-mcpapps.md`.

## Inspector verification

The mcp-use Inspector's CSP-mode toggle (Permissive vs Widget-Declared) tests the **enforcement** side of CSP. The format mapping itself is unit-tested in mcp-use; you don't need to verify it. What you verify is "did I list every origin my widget actually uses". See `../../20-inspector/11-protocol-toggle-and-csp-mode.md`.
