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
| `props` | `Record<string, any>` | Yes | Widget only (`structuredContent`) — LLM does **not** see |
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
| `widget` | `widget({ props, output?, metadata?, message? })` | `CallToolResult` | Props hidden from LLM |

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
