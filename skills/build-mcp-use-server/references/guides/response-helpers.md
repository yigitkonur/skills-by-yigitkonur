# Response Helpers

Guide to the 15 mcp-use response helpers — utility functions for creating standardized MCP responses with type safety and automatic MIME handling.

---

## Why Use Response Helpers

Response helpers replace manual `CallToolResult` construction with one-liner calls:

- **Consistency** — standardized format across tools, resources, and prompts
- **Type safety** — TypeScript generics infer response shapes (`TypedCallToolResult<T>`)
- **Less boilerplate** — one call replaces 6–10 lines of object construction
- **MIME handling** — each helper sets the correct `_meta.mimeType` automatically
- **Composability** — `mix()` merges multiple helpers into a single response

```typescript
// ❌ Manual
return { content: [{ type: "text", text: "Hello" }], _meta: { mimeType: "text/plain" } };

// ✅ Helper
return text("Hello");
```

---

## Text & Content Helpers

All accept a single `string` and return `CallToolResult` with the appropriate MIME type.

### `text(content)` — `text/plain`

The most common helper.

```typescript
import { text } from "mcp-use/server";

server.tool(
  { name: "greet", schema: z.object({ name: z.string() }) },
  async ({ name }) => text(`Hello, ${name}!`)
);
```

### `markdown(content)` — `text/markdown`

```typescript
import { markdown } from "mcp-use/server";

server.tool(
  { name: "format-docs" },
  async () => markdown("## Documentation\n\n- Item 1\n- Item 2")
);
```

### `html(content)` — `text/html`

```typescript
import { html } from "mcp-use/server";

server.tool(
  { name: "generate-report", schema: z.object({ total: z.number() }) },
  async ({ total }) => html(`<div class="report"><h2>Report</h2><p>Total: ${total}</p></div>`)
);
```

### `xml(content)`, `css(content)`, `javascript(content)`

```typescript
import { xml, css, javascript } from "mcp-use/server";

// xml → text/xml
server.resource({ name: "sitemap", uri: "data://sitemap" }, async () =>
  xml('<?xml version="1.0"?><urlset>...</urlset>')
);

// css → text/css
server.resource({ name: "styles", uri: "asset://theme.css" }, async () =>
  css("body { margin: 0; font-family: sans-serif; }")
);

// javascript → text/javascript
server.resource({ name: "script", uri: "asset://main.js" }, async () =>
  javascript('console.log("Application started");')
);
```

---

## Structured Data

### `object(data)`

Typed JSON with both pretty-printed text and `structuredContent`. Preferred when the LLM will process the data.

```typescript
import { object } from "mcp-use/server";

server.tool(
  { name: "get-user", schema: z.object({ userId: z.string() }) },
  async ({ userId }) => {
    const user = await fetchUser(userId);
    return object({ userId: user.id, email: user.email, name: user.name });
  }
);
```

**Return type:** `TypedCallToolResult<T>` — MIME: `application/json`

### `array(items)`

Wraps array data in `{ data: T }`. Passing an array to `object()` delegates to `array()` internally.

```typescript
import { array } from "mcp-use/server";

server.tool({ name: "list-items" }, async () => {
  const items = await getItems();
  return array(items);
});
```

**Return type:** `TypedCallToolResult<{ data: T }>`

---

## Media Content

### `image(data, mimeType?)`

Returns image content from base64 data or a data URL. Default MIME: `image/png`.

```typescript
import { image } from "mcp-use/server";

server.tool({ name: "generate-chart" }, async ({ data }) => {
  const chart = await generateChart(data);
  return image(chart, "image/png");
});
```

### `audio(dataOrPath, mimeType?)`

Accepts base64 data (sync) or file paths (async — must `await`). MIME inferred from extension for file paths. Supports WAV, MP3, OGG, M4A, WebM, FLAC, AAC.

```typescript
import { audio } from "mcp-use/server";

server.tool({ name: "synth" }, async () => audio(base64Data, "audio/wav"));

// File path — always await
server.resource({ name: "alert", uri: "audio://alert" }, async () =>
  await audio("./sounds/notification.wav")
);
```

### `binary(base64Data, mimeType)`

Arbitrary binary content as base64.

```typescript
import { binary } from "mcp-use/server";

server.resource({ name: "doc", uri: "file://doc.pdf" }, async () => {
  const pdf = await readFile("./document.pdf");
  return binary(pdf.toString("base64"), "application/pdf");
});
```

---

## Resource Embedding

### `resource(uri, ...)`

Embeds a resource in a tool response. Two calling patterns:

```typescript
import { resource, text, object } from "mcp-use/server";

// Pattern 1: Three args — resource(uri, mimeType, text)
return resource("config://app", "application/json", JSON.stringify({ api: "v2" }));

// Pattern 2: Two args — resource(uri, helperResult)
return resource("test://greeting", text("Hello"));
return resource("data://user", object({ id: 1, name: "Alice" }));
```

---

## Error Handling

### `error(message)`

Returns an error response with `isError: true`. Clients and LLMs treat this as a failure.

```typescript
import { error, text } from "mcp-use/server";

server.tool(
  { name: "divide", schema: z.object({ a: z.number(), b: z.number() }) },
  async ({ a, b }) => {
    if (b === 0) return error("Division by zero is not allowed");
    return text(`Result: ${a / b}`);
  }
);
```

**`error()` vs throwing:**

| Scenario | Use |
|---|---|
| Expected failure (not found, validation, rate limit) | `return error("...")` |
| Unexpected failure (bug, infra crash) | `throw new Error("...")` |

`error()` keeps the MCP response structure intact. Throwing signals a server-level problem.

---

## Mixed Content

### `mix(...responses)`

Combines multiple helpers into a single response. Merges `content` arrays, `structuredContent`, and `_meta`.

```typescript
import { mix, text, image, resource, object } from "mcp-use/server";

// Text + Image
server.tool({ name: "generate-report" }, async ({ data }) => {
  const chart = await generateChart(data);
  return mix(
    text("Analysis complete. See chart below:"),
    image(chart, "image/png"),
  );
});

// Text + Image + Embedded Resource
server.tool({ name: "full-report" }, async () =>
  mix(
    text("Multiple content types:"),
    image(chartPng, "image/png"),
    resource("test://data", object({ test: "data", value: 123 })),
  )
);

// Dynamic: spread an array of helpers
server.tool({ name: "batch" }, async ({ items }) => {
  const results = items.map((item) => text(`Processed ${item}`));
  return mix(...results);
});
```

---

## Widget Responses

### `widget(config)`

Creates a response for tools that render UI widgets (MCP Apps spec). Handles **runtime data only** — registration config belongs on the tool's `widget` property.

| Field | Type | Required | Visibility |
|---|---|---|---|
| `props` | `Record<string, any>` | No | Widget only (`structuredContent`) — LLM does **not** see |
| `output` | `CallToolResult` | No | LLM sees (`content`) — use any response helper |
| `metadata` | `Record<string, unknown>` | No | Widget only (`_meta`) |
| `message` | `string` | No | LLM sees — text override instead of `output` |

```typescript
import { widget, text } from "mcp-use/server";

server.tool(
  {
    name: "show-weather",
    schema: z.object({ city: z.string() }),
    widget: { name: "weather-display", invoking: "Fetching...", invoked: "Loaded" },
  },
  async ({ city }) => {
    const w = await fetchWeather(city);
    return widget({
      props: { city, temperature: w.temp, conditions: w.conditions },
      output: text(`Weather in ${city}: ${w.temp}°C, ${w.conditions}`),
      metadata: { updatedAt: Date.now() },
    });
  }
);
```

Widget reads `props` via `useWidget().props` and `metadata` via `useWidget().metadata`.

---

## Using Helpers in Prompts and Resources

Response helpers work across all MCP primitives. The server auto-converts `CallToolResult` to `GetPromptResult` (prompts) or `ReadResourceResult` (resources).

```typescript
import { text, object, mix, image, markdown } from "mcp-use/server";

// Prompt — auto-converted to GetPromptResult
server.prompt(
  { name: "greeting", schema: z.object({ name: z.string() }) },
  async ({ name }) => text(`Hello, ${name}! How can I help?`)
);

// Prompt with mixed content
server.prompt({ name: "report", schema: z.object({ dataId: z.string() }) }, async ({ dataId }) => {
  const data = await fetchData(dataId);
  return mix(text("Report"), object({ summary: data.summary }), image(data.chart, "image/png"));
});

// Resource — auto-converted to ReadResourceResult
server.resource({ name: "config", uri: "config://app" }, async () =>
  object({ version: "1.0.0", features: ["auth", "api"] })
);

// Resource template
server.resourceTemplate(
  { name: "user-profile", uriTemplate: "user://{userId}/profile" },
  async (uri, { userId }) => object(await fetchProfile(userId))
);
```

---

## Quick Reference

| Helper | Signature | Return Type | MIME / Notes |
|---|---|---|---|
| `text` | `text(str)` | `CallToolResult` | `text/plain` |
| `markdown` | `markdown(str)` | `CallToolResult` | `text/markdown` |
| `html` | `html(str)` | `CallToolResult` | `text/html` |
| `xml` | `xml(str)` | `CallToolResult` | `text/xml` |
| `css` | `css(str)` | `CallToolResult` | `text/css` |
| `javascript` | `javascript(str)` | `CallToolResult` | `text/javascript` |
| `object` | `object(obj)` | `TypedCallToolResult<T>` | `application/json` — includes `structuredContent` |
| `array` | `array(items)` | `TypedCallToolResult<{ data: T }>` | `application/json` — wraps in `{ data }` |
| `image` | `image(base64, mime?)` | `CallToolResult` | Default `image/png` |
| `audio` | `audio(dataOrPath, mime?)` | `CallToolResult \| Promise<…>` | Async for file paths; infers MIME |
| `binary` | `binary(base64, mime)` | `CallToolResult` | Any binary MIME type |
| `resource` | `resource(uri, mime, text)` or `resource(uri, helper)` | `CallToolResult` | Embedded resource content |
| `error` | `error(str)` | `CallToolResult` | Sets `isError: true` |
| `mix` | `mix(...results)` | `CallToolResult` | Merges content, structuredContent, _meta |
| `widget` | `widget({ props?, output?, metadata?, message? })` | `CallToolResult` | Props hidden from LLM; `props` defaults to `{}` if omitted |

---

## Common Mistakes

| Mistake | Problem | Fix |
|---|---|---|
| Returning raw objects without a helper | Missing MIME types, no `structuredContent` | Use `object()` for data, `text()` for messages |
| Using `text()` for structured data | LLM can't parse free-text JSON reliably | Use `object()` — provides both text and `structuredContent` |
| Throwing instead of `error()` for expected failures | Server exception vs. graceful tool failure | `return error("...")` for not-found, validation, limits |
| Forgetting to `await` file-based `audio()` | Returns a Promise instead of the result | Always `await audio("./path/to/file.wav")` |
| Building `CallToolResult` manually | Verbose, easy to miss fields | Use helpers — they exist to prevent this |
| Using `mix()` with a single argument | Unnecessary wrapper | Return the helper directly |
| Importing from `@modelcontextprotocol/sdk` | Wrong package — helpers won't resolve | Always `import { ... } from "mcp-use/server"` |


---

## Complete Helper Reference

The helpers below are the canonical response-building surface for `mcp-use/server`. Some are text-first, some are binary-first, and some are composition helpers. Use them instead of constructing `CallToolResult` objects by hand.

### Canonical import

```typescript
import {
  MCPServer,
  text,
  object,
  array,
  error,
  mix,
  widget,
  resource,
  image,
  audio,
  binary,
  markdown,
  html,
  xml,
  css,
  javascript,
} from 'mcp-use/server'
```

### Helper matrix

| Helper | Best for | Output shape |
|---|---|---|
| `text()` | Plain text | text content + `text/plain` |
| `markdown()` | Rich formatted text | text content + `text/markdown` |
| `html()` | HTML snippets | text content + `text/html` |
| `xml()` | XML payloads | text content + XML MIME |
| `css()` | CSS stylesheets | text content + CSS MIME |
| `javascript()` | JavaScript code | text content + JS MIME |
| `object()` | Structured JSON data for models | structured content + JSON MIME |
| `array()` | Array of items | structured array content |
| `image()` | Base64 image responses | image content + image MIME |
| `audio()` | Audio binary or file-path content | audio content + audio MIME |
| `binary()` | Binary data with MIME | binary content + specified MIME |
| `resource()` | Resource embedding | embedded resource content |
| `widget()` | MCP Apps widget payloads | hidden props + optional visible output |
| `error()` | Expected tool failures | sets `isError: true` |
| `mix()` | Multi-part responses | merges multiple helpers |

### `TypedCallToolResult<T>`

Helpers that return structured data — especially `object()` and `array()` — are best understood as returning a typed result. That generic type lets TypeScript know what the server is returning so your tool handlers stay self-documenting.

```typescript
type UserSummary = {
  id: string
  name: string
  plan: 'free' | 'pro'
}

const result = object<UserSummary>({
  id: 'u_123',
  name: 'Ada Lovelace',
  plan: 'pro',
})
```

### `_meta.mimeType`

Every helper sets or contributes an appropriate `_meta.mimeType`. That metadata matters for clients that need to decide whether something should be rendered as markdown, treated as a widget payload, or passed to another processing layer.

| Helper family | Typical `_meta.mimeType` |
|---|---|
| `text()` | `text/plain` |
| `markdown()` | `text/markdown` |
| `html()` | `text/html` |
| `xml()` | `text/xml` |
| `css()` | `text/css` |
| `javascript()` | `text/javascript` |
| `object()` | `application/json` |
| `image()` | `image/png`, `image/jpeg`, etc. |
| `audio()` | `audio/wav`, `audio/mpeg`, etc. |
| `binary()` | whatever MIME you pass |

---

## Text-Oriented Helpers

### `text()`

Use `text()` for plain-language summaries, confirmations, and short machine-readable-but-human-first responses.

```typescript
return text('Deployment queued successfully.')
```

### `markdown()`

Use `markdown()` when headings, lists, code fences, or emphasis improve readability.

```typescript
return markdown('## Deployment

- Status: queued
- Region: us-east-1')
```

### `html()`

Use `html()` only when the client explicitly expects HTML or when a widget/browser surface will render it safely.

```typescript
return html('<section><h2>Build status</h2><p>Healthy</p></section>')
```

### `xml()`

Use `xml()` for feeds, sitemaps, or integrations that explicitly expect XML.

```typescript
return xml('<?xml version="1.0"?><status><state>ok</state></status>')
```

### Text helper decision table

| Need | Helper |
|---|---|
| Short plain answer | `text()` |
| Rich formatting | `markdown()` |
| Browser-renderable markup | `html()` |
| XML contract | `xml()` |
| CSS stylesheets | `css()` |
| JavaScript code | `javascript()` |

❌ **BAD** — Serialize JSON into `text()` and hope clients parse it:

```typescript
return text(JSON.stringify({ total: 42 }))
```

✅ **GOOD** — Use `object()` for structured data:

```typescript
return object({ total: 42 })
```

---

## Structured Data Helpers

### `object()`

`object()` is the default helper for structured JSON results that the model may want to reason over. It provides both readable content and structured data.

```typescript
return object({
  total: 42,
  items: [{ id: '1', label: 'alpha' }],
})
```

### `array()`

Use `array()` for returning lists of items.

```typescript
return array([
  { id: '1', name: 'Alice' },
  { id: '2', name: 'Bob' }
])
```

---

## Binary and Rich Media Helpers

### `image()`

Use `image(base64, mimeType?)` for charts, screenshots, or generated previews.

```typescript
return image(chartBase64, 'image/png')
```

### `audio()`

Use `audio()` for speech output, recordings, or generated audio files. If you pass a file path, `await` it.

```typescript
return await audio('./out/greeting.wav', 'audio/wav')
```

### `binary()`

Use `binary()` for arbitrary binary payloads with a specific MIME type.

```typescript
return binary(pdfBase64, 'application/pdf')
```

### Media helper table

| Helper | Common MIME values |
|---|---|
| `image()` | `image/png`, `image/jpeg`, `image/webp` |
| `audio()` | `audio/wav`, `audio/mpeg`, `audio/ogg` |
| `binary()` | `application/pdf`, `application/zip`, `application/octet-stream` |

❌ **BAD** — Return binary base64 through `text()`:

```typescript
return text(pdfBase64)
```

✅ **GOOD** — Use `binary()` with the correct MIME type:

```typescript
return binary(pdfBase64, 'application/pdf')
```

---

## Expected Failure Helper

### `error()`

Use `error()` for **expected** failures: missing permissions, validation problems, quota limits, not-found conditions, or unsupported client capabilities.

```typescript
if (!ctx.auth) return error('Authentication required.')
if (!ctx.client.can('sampling')) return error('Sampling not supported by this client.')
```

### `error()` vs throwing

| Use `error()` for... | Throw for... |
|---|---|
| User/input mistakes | Unexpected exceptions |
| Permissions and policy failures | Programmer bugs |
| Known not-found or quota states | Broken dependencies |
| Missing client capabilities | Corrupted internal state |

---

## Composition with `mix()`

`mix()` is the right choice when a single response should contain multiple complementary parts.

### Common composition patterns

| Pattern | Example |
|---|---|
| Summary + data | `mix(text('Done'), object({...}))` |
| Markdown + image | `mix(markdown('## Chart'), image(...))` |
| Text + structured data | `mix(text('Generated'), object({...}))` |
| Visible result + widget props | `mix(text('Dashboard ready'), widget({...}))` |

```typescript
return mix(
  markdown('## Export complete

Attached files are ready.'),
  object({ rowCount: 1, generatedAt: Date.now() })
)
```

### Composition rules

1. Lead with the most user-readable helper.
2. Add structured payloads second.
3. Add large binary assets only when the client benefits from them.
4. Avoid duplicating the same information in conflicting formats.

❌ **BAD** — Repeat the full same payload three times:

```typescript
return mix(text(bigJson), markdown(bigJson), text(bigJson))
```

✅ **GOOD** — Use one readable surface and one structured surface:

```typescript
return mix(text('User export complete.'), object({ totalUsers: 42 }))
```

---

## Widget Responses

`widget()` is for MCP Apps and other clients that understand hidden props, metadata, and optional visible output. The important design principle is that widget props can stay available to the app without forcing the language model to parse them as prose.

### Widget fields

| Field | Purpose |
|---|---|
| `props` | Hidden structured data for the widget/app |
| `output` | Optional visible helper output |
| `metadata` | Extra non-LLM state or rendering hints |
| `message` | Optional short visible label |

```typescript
return widget({
  props: {
    title: 'Team Dashboard',
    metrics: [{ label: 'Open incidents', value: 3 }],
  },
  output: markdown('## Team Dashboard

Open incidents: **3**'),
  metadata: { refreshSeconds: 60 },
})
```

### Widget + `mix()`

```typescript
return mix(
  text('Dashboard generated.'),
  widget({ props: { chart: chartData }, metadata: { theme: 'dark' } })
)
```

---

## Putting Helpers to Work

### Example: plain tool result

```typescript
server.tool({
  name: 'build-status',
  description: 'Return CI build status.',
}, async () => object({ status: 'green', durationSeconds: 187 }))
```

### Example: report with attachments

```typescript
server.tool(
  {
    name: 'generate-quarterly-report',
    description: 'Generate a quarterly report with chart.',
  },
  async () => {
    const chartBase64 = await renderChart()
    return mix(
      markdown('## Quarterly Report

Growth was **18%** quarter-over-quarter.'),
      image(chartBase64, 'image/png'),
      object({ revenue: [100, 118], growthRate: 0.18 })
    )
  }
)
```

### Example: binary file with user-facing explanation

```typescript
server.tool(
  {
    name: 'export-invoice-pdf',
    description: 'Export an invoice as a PDF.',
  },
  async () => {
    const pdfBase64 = await renderInvoicePdf()
    return mix(
      text('Invoice PDF generated.'),
      binary(pdfBase64, 'application/pdf')
    )
  }
)
```

---

## Selection Checklist

| Question | Helper |
|---|---|
| Do I want the model to reason over typed data? | `object()` or `array()` |
| Do I want the user to read a concise summary? | `text()` or `markdown()` |
| Do I need a file-like binary payload? | `binary()`, `image()`, or `audio()` |
| Is this a known failure? | `error()` |
| Do I need more than one content form? | `mix()` |
| Is the result for a widget/app surface? | `widget()` |
| Do I need to embed a resource? | `resource()` |

## Recommended defaults

1. Use `object()` for data.
2. Use `text()` or `markdown()` for summaries.
3. Use `error()` for expected failures.
4. Use `mix()` sparingly and intentionally.
5. Let helpers set `_meta.mimeType` for you.
