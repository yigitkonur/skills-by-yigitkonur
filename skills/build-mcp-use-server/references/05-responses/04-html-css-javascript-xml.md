# `html()`, `css()`, `javascript()`, `xml()`

Four text helpers with non-default MIME types. Each accepts a single `string`. Use them only when the client explicitly expects that format — they are not substitutes for `text()` or `markdown()`.

## `html(content)` — `text/html`

Use for HTML the client will render in a browser surface or widget. Do not use for prose with HTML tags sprinkled in.

```typescript
import { html } from "mcp-use/server";

server.tool(
  { name: "generate-report", schema: z.object({ total: z.number() }) },
  async ({ total }) => html(`<div class="report"><h2>Report</h2><p>Total: ${total}</p></div>`)
);

return html("<section><h2>Build status</h2><p>Healthy</p></section>");
```

Signature: `html(content: string): CallToolResult`.

## `css(content)` — `text/css`

Use to expose stylesheets as MCP resources or to deliver CSS payloads that a widget will inject.

```typescript
import { css } from "mcp-use/server";

server.resource({ name: "styles", uri: "asset://theme.css" }, async () =>
  css("body { margin: 0; font-family: sans-serif; }")
);
```

## `javascript(content)` — `text/javascript`

Use to deliver JavaScript code as a resource (widget bootstrap scripts, generated client snippets).

```typescript
import { javascript } from "mcp-use/server";

server.resource({ name: "script", uri: "asset://main.js" }, async () =>
  javascript('console.log("Application started");')
);
```

## `xml(content)` — `text/xml`

Use for sitemaps, RSS/Atom feeds, SOAP payloads, or any integration that explicitly expects XML.

```typescript
import { xml } from "mcp-use/server";

return xml('<?xml version="1.0"?><status><state>ok</state></status>');

server.resource({ name: "sitemap", uri: "data://sitemap" }, async () =>
  xml('<?xml version="1.0"?><urlset>...</urlset>')
);
```

## Signatures and MIME types

| Helper | Signature | MIME |
|---|---|---|
| `html` | `html(s: string)` | `text/html` |
| `css` | `css(s: string)` | `text/css` |
| `javascript` | `javascript(s: string)` | `text/javascript` |
| `xml` | `xml(s: string)` | `text/xml` |

All four return `CallToolResult` with `_meta.mimeType` set.

## When to use which

| Need | Helper |
|---|---|
| Browser-renderable markup | `html()` |
| CSS stylesheet for a widget or client asset | `css()` |
| JavaScript code as a resource | `javascript()` |
| XML feed, sitemap, or SOAP body | `xml()` |
| Anything else with text | `text()` or `markdown()` |

## Anti-patterns

- **HTML for prose.** Wrapping `<p>` around a sentence is not HTML — it's text. Use `text()` or `markdown()`.
- **HTML to bypass markdown.** If you want headings, use `markdown()` (`## heading`), not `html()` (`<h2>`).
- **CSS or JS as `text()`.** Use the typed helper so `_meta.mimeType` is correct; clients use it to decide how to handle the content.
- **XML to ship structured data.** When a typed consumer wants fields, use `object()`. XML is for explicit XML contracts only.
