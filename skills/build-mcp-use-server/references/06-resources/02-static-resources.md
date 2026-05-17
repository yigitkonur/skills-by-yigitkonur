# Static Resources

A static resource has a **fixed URI** known at registration time. Use `server.resource()`. No template parameters.

## Registration

```typescript
import { object, text } from "mcp-use/server";

server.resource(
  {
    name: "config",
    uri: "config://app",
    title: "Application Config",
    description: "Current application configuration",
    mimeType: "application/json",
  },
  async () => object({ env: "production", version: "1.0.0", debug: false })
);

server.resource(
  { name: "readme", uri: "docs://readme", title: "README", mimeType: "text/markdown" },
  async () => text("# My Project\n\nWelcome to the project.")
);
```

## Response helpers

Import from `"mcp-use/server"`. Helpers carry response content and, for most text/object/binary helpers, MIME metadata. Still set `mimeType` on the resource definition when client rendering matters.

| Helper | Use for |
|---|---|
| `text(content)` | Plain text |
| `markdown(content)` | Markdown |
| `html(content)` | HTML |
| `xml(content)` | XML |
| `css(content)` | CSS |
| `javascript(content)` | JavaScript source |
| `object(value)` | JSON-serializable value |
| `array(items)` | JSON array |
| `image(data, mime?)` | Image — see `04-binary-and-image.md` |
| `audio(data, mime?)` | Audio — see `04-binary-and-image.md` |
| `binary(data, mime)` | Generic binary — see `04-binary-and-image.md` |
| `mix(...responses)` | Composite, multiple content items |

## Composite responses with `mix()`

A single resource can return multiple content items:

```typescript
import { mix, text, object, image } from "mcp-use/server";

server.resource(
  { name: "report-bundle", uri: "reports://latest", title: "Latest Reports" },
  async () => {
    const reportData = await getReportData();
    const chart = await generateChart(reportData);
    return mix(
      text("Executive Summary..."),
      object(reportData),
      image(chart, "image/png"),
    );
  },
);
```

## Annotations

Annotations are metadata hints — clients use them for filtering, ranking, and display. They never affect content.

```typescript
server.resource(
  {
    name: "metrics",
    uri: "data://metrics",
    annotations: {
      audience: ["user", "assistant"],
      priority: 0.9,
      lastModified: new Date().toISOString(),
    },
  },
  async () => object(await getMetrics()),
);
```

| Field | Type | Meaning |
|---|---|---|
| `audience` | `('user' \| 'assistant')[]` | Who the resource is intended for |
| `priority` | `number` (0.0–1.0) | Importance hint for ranking |
| `lastModified` | `string` (ISO 8601) | Last change timestamp |

## Handler signatures

Static resource callbacks receive no URI or template params. Use no arguments for public data, or one `ctx` argument when you need request/auth context.

```typescript
// No arguments — when URI carries no information you need
server.resource(
  { name: "welcome", uri: "app://welcome" },
  async () => text("Welcome"),
);

// With ctx — for auth or request metadata
server.resource(
  { name: "private", uri: "private://current" },
  async (ctx) => {
    if (!ctx.auth?.userId) throw new Error("Unauthorized");
    return object(await getPrivateData(ctx.auth.userId));
  },
);
```

For URI templates and `params`, see `03-resource-templates.md`.
