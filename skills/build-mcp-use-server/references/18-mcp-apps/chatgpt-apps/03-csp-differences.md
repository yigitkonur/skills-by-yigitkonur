# CSP: Standard Fields and the ChatGPT Redirect Extension

*Read this when declaring CSP for a View that must render in standard MCP Apps hosts and ChatGPT.*

Use standard MCP Apps CSP first. mcp-use emits one generated resource `_meta.ui.csp` object for every host; it does not rename categories or emit a second ChatGPT policy. One ChatGPT-only resource extension remains relevant for a narrower case: `openai/widgetCSP.redirect_domains` for trusted `window.openai.openExternal(...)` redirect targets.

## Standard CSP Emitted by mcp-use

The MCP Apps CSP type contains four categories:

```typescript
interface McpUiResourceCsp {
  connectDomains?: string[];
  resourceDomains?: string[];
  frameDomains?: string[];
  baseUriDomains?: string[];
}
```

Set them through `view.csp`:

```typescript
view: {
  name: "data-view",
  csp: {
    connectDomains: ["https://api.example.com"],
    resourceDomains: ["https://cdn.example.com"],
    frameDomains: ["https://embed.example.com"],
  },
}
```

Source boundaries:

- the literal standard categories come from `@modelcontextprotocol/ext-apps` `McpUiResourceCsp`;
- `packages/server/src/views/csp-env.ts` merges the policy;
- `packages/server/src/views/wire.ts` emits it under resource `_meta.ui.csp`.

`resourceDomains` is one standard bucket for static assets; mcp-use does not split it into ChatGPT-specific script/style/font categories.

## Merge Behavior Is Host-Independent

For every generated View resource, mcp-use additively combines:

1. author `view.csp` entries;
2. per-category environment values, or `CSP_URLS` as the category fallback;
3. the server origin in `connectDomains` and the assets origin in `resourceDomains`.

Entries are deduplicated while preserving first-seen order. “Priority” describes ordering, not replacement: lower segments are still included when they contain distinct origins.

```bash
CSP_CONNECT_DOMAINS=https://api.example.com
CSP_RESOURCE_DOMAINS=https://cdn.example.com
CSP_FRAME_DOMAINS=https://embed.example.com
CSP_BASE_URI_DOMAINS=https://components.example.com
```

The result is the same standard `_meta.ui.csp` object regardless of host.

## Keep the Browser/Server Boundary Clear

View CSP constrains requests made by the sandboxed browser View. It does not authorize or block a Node/server tool callback's `fetch`.

```typescript
// This browser request needs view.csp.connectDomains.
const response = await fetch("https://api.example.com/data");
```

A server-side callback fetching the same URL does not need that origin in the View CSP unless the rendered View also contacts it.

## ChatGPT's Remaining Redirect Extension

The official OpenAI Plugin UI reference says:

- standard `_meta.ui.csp` is preferred for `connectDomains`, `resourceDomains`, and `frameDomains`;
- `_meta["openai/widgetCSP"]` is a legacy ChatGPT compatibility object using snake_case fields;
- `redirect_domains` remains required when using trusted redirect targets with `window.openai.openExternal(...)`, because standard `_meta.ui.csp` has no equivalent redirect field.

Literal resource key:

```text
_meta["openai/widgetCSP"].redirect_domains
```

This does **not** create a second general CSP model for mcp-use. It is a ChatGPT-only extension for that redirect behavior.

## mcp-use Authoring Boundary

For normal external links, use the shipped standard hook:

```typescript
import { useOpenExternal } from "mcp-use/react";

const openExternal = useOpenExternal();
await openExternal({ url: "https://example.com/docs" });
```

Shipped `useOpenExternal()` calls the standard MCP Apps `App.openLink()` path. It does not directly call `window.openai.openExternal`, does not expose ChatGPT's `redirectUrl` option, and does not require authors to detect ChatGPT.

beta.66's generated View resource builder exposes standard `view.csp`, `view.domain`, `view.permissions`, and `view.prefersBorder`, but no public arbitrary resource `_meta` authoring surface. Therefore you cannot configure `openai/widgetCSP.redirect_domains` on a generated mcp-use View through a documented public API.

If the product specifically requires ChatGPT's redirect-target feature rather than ordinary host-mediated link opening, treat it as a current framework limitation. Do not invent a `view` property, write direct `window.openai` code around an existing standard hook, or claim Inspector can validate unsupported resource metadata.

## Dedicated Domain for ChatGPT Submission

The standard resource field is `_meta.ui.domain`, configured through `view.domain`:

```typescript
view: {
  name: "checkout",
  domain: "https://components.example.com",
}
```

The official OpenAI reference says a dedicated component origin is required when submitting a plugin with UI and must be unique per plugin. This is a ChatGPT submission requirement applied to the standard field, not a reason to use the `openai/widgetDomain` compatibility alias. Confirm the exact origin and submission acceptance in real ChatGPT.

## Verify Standard CSP in Inspector

Current Inspector source provides CSP diagnostics with two modes:

- **Permissive** — records requests that the declared policy would block;
- **Widget-Declared** — enforces the resource metadata policy.

Use Widget-Declared mode before shipping. Check the iframe console and CSP findings for browser fetches, assets, and frames.

Inspector validates standard resource CSP. It has no verified ChatGPT protocol toggle and does not prove `window.openai.openExternal` redirect handling or ChatGPT submission policy. Test those ChatGPT-specific concerns in real ChatGPT.

## Troubleshooting

| Symptom | Check |
|---|---|
| Browser fetch blocked | Add only the required origin to `view.csp.connectDomains` |
| Image, font, script, or stylesheet blocked | Add its origin to `view.csp.resourceDomains` |
| Embedded iframe blocked | Add its origin to `view.csp.frameDomains`; expect stricter host review |
| Works only in Inspector Permissive mode | Re-run in Widget-Declared mode and inspect recorded policy differences |
| Ordinary external link fails | Use `useOpenExternal()` and verify host `openLinks` capability |
| ChatGPT redirect-target flow fails | Check real ChatGPT requirements; `redirect_domains` is not publicly configurable on generated Views in beta.66 |

## See Also

- `references/18-mcp-apps/server-surface/05-csp-metadata.md` — complete standard CSP configuration and merge rules
- `01-dual-protocol.md` — descriptor/resource metadata matrix and framework limits
- `04-runtime-detection.md` — capability-first feature gating
