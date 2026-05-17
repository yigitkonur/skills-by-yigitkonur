# Deprecation of `type: "appsSdk"`

`type: "appsSdk"` is the legacy ChatGPT-only widget path. Existing widgets continue to function, but new work and any non-trivial edits should migrate to `type: "mcpApps"`.

Source note: `mcp-use@1.26.0/package/dist/src/server/types/widget.d.ts` lines 61-69 marks `appsSdkMetadata` deprecated, while `types/resource.d.ts` lines 517-554 still exposes both `AppsSdkUIResource` and `McpAppsUIResource`; treat `appsSdk` as legacy, not removed.

## Why deprecated

`appsSdk` is ChatGPT-only:

- MIME: `text/html+skybridge` only.
- CSP keys: snake_case (`connect_domains`).
- Metadata: must use `appsSdkMetadata` with `openai/*` keys directly.
- No MCP Apps clients (Claude, Goose, MCP Inspector) can render it.

`mcpApps` covers the same ChatGPT support **and** adds MCP Apps. There's no remaining advantage to the legacy type.

## Status table

| Type | ChatGPT | MCP Apps clients | Status |
|---|---|---|---|
| `mcpApps` | Yes | Yes | **Recommended** |
| `appsSdk` | Yes | No | **Legacy** |

## What "deprecated" means in mcp-use

- **Still functional** — existing `appsSdk` registrations keep working. mcp-use 1.26.0 still exposes the type.
- **Legacy metadata** — `appsSdkMetadata` is marked deprecated in the widget metadata type; prefer unified `metadata`.
- **No runtime warning guarantee** — do not claim startup warnings unless the installed package logs them.
- **Doc trail** — internal references to `appsSdk` should point here or to the migration guide.

## Migration is non-breaking for the widget

Your widget code (the `widget.tsx` and any React components) does **not** change. Only the server registration changes:

```typescript
// Before — deprecated
server.uiResource({
  type: "appsSdk",
  name: "my-widget",
  htmlTemplate: `...`,
  appsSdkMetadata: {
    "openai/widgetCSP": {
      connect_domains: ["https://api.example.com"],
      resource_domains: ["https://cdn.example.com"],
    },
    "openai/widgetPrefersBorder": true,
    "openai/widgetDescription": "My widget description",
  },
});

// After — recommended
server.uiResource({
  type: "mcpApps",
  name: "my-widget",
  htmlTemplate: `...`,
  metadata: {
    csp: {
      connectDomains: ["https://api.example.com"],
      resourceDomains: ["https://cdn.example.com"],
    },
    prefersBorder: true,
    widgetDescription: "My widget description",
  },
});
```

## Migration steps (summary)

1. Change `type: "appsSdk"` → `type: "mcpApps"`.
2. Rename `appsSdkMetadata` → `metadata`.
3. Convert CSP fields camelCase: `connect_domains` → `connectDomains`, etc.
4. Strip the `"openai/"` prefix from all other keys.
5. Test in both ChatGPT and an MCP Apps client (Inspector).

The full migration walk-through with field mappings and verification steps lives at `../../28-migration/04-appssdk-to-mcpapps.md`. Use that as the canonical migration reference.

## Field-name mapping reminder

| Legacy `appsSdkMetadata` key | New `metadata` key |
|---|---|
| `"openai/widgetCSP"` | `csp` |
| `"openai/widgetPrefersBorder"` | `prefersBorder` |
| `"openai/widgetDescription"` | `widgetDescription` |
| `"openai/widgetDomain"` | `domain` |
| `"openai/widgetAccessible"` | `widgetAccessible` |
| `"openai/locale"` | `locale` |
| `"openai/toolInvocation/invoking"` | `invoking` |
| `"openai/toolInvocation/invoked"` | `invoked` |
| `connect_domains` | `connectDomains` |
| `resource_domains` | `resourceDomains` |
| `frame_domains` | `frameDomains` |
| `redirect_domains` | `csp.redirectDomains` |
| `base_uri_domains` | `csp.baseUriDomains` |
| `script_directives` | `csp.scriptDirectives` |
| `style_directives` | `csp.styleDirectives` |

Full table with notes: `../../28-migration/04-appssdk-to-mcpapps.md`.

## When ChatGPT-only flags are needed

`type: "mcpApps"` accepts `appsSdkMetadata` as an escape hatch for supported ChatGPT-specific overrides:

```typescript
server.uiResource({
  type: "mcpApps",
  name: "my-widget",
  htmlTemplate: `...`,
  metadata: { /* shared */ },
  appsSdkMetadata: {
    "openai/widgetDomain": "https://chatgpt.com",
    "openai/widgetAccessible": true,
  },
});
```

Prefer encoding everything in `metadata`. In `mcp-use@1.26.0`, the Apps SDK adapter copies a known resource-metadata set from `appsSdkMetadata` (`widgetAccessible`, `locale`, `widgetCSP`, `widgetPrefersBorder`, `widgetDomain`, `widgetDescription`) plus known tool invocation fields.
