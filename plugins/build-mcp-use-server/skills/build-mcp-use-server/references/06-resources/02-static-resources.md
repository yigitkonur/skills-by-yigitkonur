# Static Resources

*Read this when registering a fixed-URI resource with static or computed content.*

A static resource has a **fixed URI** known at registration time. Use `server.resource()`. No template parameters.

## Registration

```typescript
import { MCPServer } from "mcp-use";

server.resource(
  {
    name: "config",
    uri: "config://app",
    title: "Application Config",
    description: "Current application configuration",
    mimeType: "application/json",
  },
  async (uri) => ({
    contents: [
      {
        uri: uri.href,
        mimeType: "application/json",
        text: JSON.stringify({ env: "production", version: "1.0.0", debug: false }),
      },
    ],
  })
);

server.resource(
  { name: "readme", uri: "docs://readme", title: "README", mimeType: "text/markdown" },
  async (uri) => ({
    contents: [{ uri: uri.href, mimeType: "text/markdown", text: "# My Project\n\nWelcome to the project." }],
  })
);
```

Return the raw `{ contents: [...] }` envelope (`ReadResourceResult`). Each entry carries its own `uri` and `mimeType`, plus either `text` or a base64 `blob`.

## Deprecated response helpers

Import from `"mcp-use"`. All still work — the SDK converts their `CallToolResult`-shaped output into a `ReadResourceResult` automatically — but every one is marked `@deprecated` in beta.66. Prefer the raw envelope above for new code. Full list and conversion rules: `../05-responses/07-deprecated-v1-helpers.md`.

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

## Multiple content entries per read

One resource read can return several entries directly in the raw envelope — no helper needed:

```typescript
server.resource(
  { name: "report-bundle", uri: "reports://latest", title: "Latest Reports" },
  async (uri) => {
    const reportData = await getReportData();
    const chartBase64 = await generateChart(reportData);
    return {
      contents: [
        { uri: uri.href, mimeType: "text/plain", text: "Executive Summary..." },
        { uri: uri.href, mimeType: "application/json", text: JSON.stringify(reportData) },
        { uri: `${uri.href}/chart`, mimeType: "image/png", blob: chartBase64 },
      ],
    };
  },
);
```

The deprecated `mix(...results)` helper composes multiple helper-shaped results into one `CallToolResult` (concatenating `content` arrays, merging `structuredContent` and `_meta`); it is still accepted and converted, but a raw multi-entry `contents` array is direct and needs no composition step.

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
  async (uri) => ({
    contents: [{ uri: uri.href, mimeType: "application/json", text: JSON.stringify(await getMetrics()) }],
  }),
);
```

| Field | Type | Meaning |
|---|---|---|
| `audience` | `('user' \| 'assistant')[]` | Who the resource is intended for |
| `priority` | `number` (0.0–1.0) | Importance hint for ranking |
| `lastModified` | `string` (ISO 8601) | Last change timestamp |

## Handler signature

The declared `ResourceCallback` type is `(uri: URL, ctx: RequestContext<TUser, HasOAuth, TEnv>) => ...` — `uri` is always the **first** argument, `ctx` the second. JavaScript lets you omit trailing parameters you don't use, so a shorter signature still compiles:

```typescript
// uri only — when you don't need auth/request context
server.resource(
  { name: "welcome", uri: "app://welcome" },
  async (uri) => ({
    contents: [{ uri: uri.href, mimeType: "text/plain", text: "Welcome" }],
  }),
);

// uri + ctx — for auth or request metadata (ctx.auth is only populated when OAuth is configured)
server.resource(
  { name: "private", uri: "private://current" },
  async (uri, ctx) => {
    if (!ctx.auth) throw new Error("Unauthorized");
    return {
      contents: [{ uri: uri.href, mimeType: "application/json", text: JSON.stringify(await getPrivateData(ctx.auth.user)) }],
    };
  },
);
```

Do not write a single-argument callback expecting `ctx` in that position (`async (ctx) => ...`) — the first argument is always the resolved `URL`, never `ctx`.

For URI templates and `params`, see `03-resource-templates.md`.
