# Deprecated v1 response helpers

*Read this only if migrating v1 code or using legacy compatibility mode.*

v2 exports v1 helpers **for compatibility only**. They are marked `@deprecated`; no removal release or date is specified. New code should return raw MCP envelopes.

## Full v1→v2 mapping table

| v1 helper | v1 signature | v2 raw envelope | Status | Notes |
|---|---|---|---|---|
| `text(str)` | `text("hello")` | `{ content: [{ type: "text", text: "hello" }], _meta: { mimeType: "text/plain" } }` | Deprecated | Plain text; helper stores MIME metadata in result `_meta` |
| `markdown(str)` | `markdown("# Title")` | `{ content: [{ type: "text", text: "# Title" }], _meta: { mimeType: "text/markdown" } }` | Deprecated | MIME metadata is result-level, not a text-block field |
| `html(str)` | `html("<div>...</div>")` | `{ content: [{ type: "text", text: "..." }], _meta: { mimeType: "text/html" } }` | Deprecated | MIME metadata is result-level |
| `xml(str)` | `xml("<root>...</root>")` | `{ content: [{ type: "text", text: "..." }], _meta: { mimeType: "text/xml" } }` | Deprecated | MIME metadata is result-level |
| `css(str)` | `css("body { ... }")` | `{ content: [{ type: "text", text: "..." }], _meta: { mimeType: "text/css" } }` | Deprecated | MIME metadata is result-level |
| `javascript(str)` | `javascript("console.log(...)")` | `{ content: [{ type: "text", text: "..." }], _meta: { mimeType: "text/javascript" } }` | Deprecated | MIME metadata is result-level |
| `object(obj)` | `object({ a: 1 })` | `{ content: [{ type: "text", text: JSON.stringify(obj, null, 2) }], structuredContent: obj, _meta: { mimeType: "application/json" } }` | Deprecated | Structured data; populates content, schema, and result `_meta`. If `obj` is actually an array, `object()` forwards to `array()` instead |
| `array(arr)` | `array([1, 2])` | `{ content: [{ type: "text", text: JSON.stringify(arr, null, 2) }], structuredContent: arr }` | Deprecated | Manually adds its own text block (2026 any-JSON root — no `{ data }` wrap, unlike v1); does not rely on the SDK's auto-append |
| `image(base64, mime = "image/png")` | `image("iVBORw0...", "image/png")` | `{ content: [{ type: "image", data: "iVBORw0...", mimeType: "image/png" }], _meta: { mimeType: "image/png", isImage: true } }` | Deprecated | Base64 image data; `mimeType` defaults to `"image/png"` if omitted |
| `audio(base64, mime = "audio/wav")` | `audio("//NExAA...", "audio/wav")` | `{ content: [{ type: "audio", data: "//NExAA...", mimeType: "audio/wav" }], _meta: { mimeType: "audio/wav", isAudio: true } }` | Deprecated | Audio block uses the `audio` discriminator; `mimeType` defaults to `"audio/wav"` if omitted |
| `binary(base64, mime)` | `binary("JVBERi0...", "application/pdf")` | `{ content: [{ type: "text", text: "JVBERi0..." }], _meta: { mimeType: "application/pdf", isBinary: true } }` | Deprecated | Base64 text content block plus result `_meta`; `mimeType` is **required**, no default (unlike `image`/`audio`) |
| `resource(uri, mimeType?, text?)` | `resource("file://a.pdf", "application/pdf", "desc")` | `{ content: [{ type: "resource", resource: { uri, mimeType, text: text ?? "" } }] }` | Deprecated | Direct form; 2nd arg is `mimeType` (a string). `resource(uri, mimeType)` (2-arg) omits `text` (defaults to `""`); `resource(uri, mimeType, text)` (3-arg) sets both |
| `resource(uri, callToolResult)` | `resource("file://a.pdf", someResult)` | Extracts `mimeType` from `someResult._meta.mimeType` and text from `someResult.content[0]`, wraps as `{ content: [{ type: "resource", resource: { uri, mimeType?, text } }] }` | Deprecated | 2-arg extraction form — pulls MIME/text out of another helper's or tool's `CallToolResult` |
| `error(msg)` | `error("Not found")` | `{ isError: true, content: [{ type: "text", text: "Not found" }] }` | Deprecated | Error flag + message; no structuredContent |
| `widget(config)` | `widget({ props, metadata, message })` | `{ content: [...], structuredContent?: props, _meta?: metadata }` — see below | Deprecated | Not removed. `WidgetResponseConfig` has `props`, `data` (deprecated alias for `props`), `output` (a `CallToolResult` whose `content`/`structuredContent` take precedence), `metadata`, `message` |
| `mix(...)` | `mix(text(...), image(...))` | Concatenates every `content` array; shallow-merges every `structuredContent` object; shallow-merges every `_meta` object | Deprecated | Manual composition — `structuredContent`/`_meta` are dropped from the merge unless present and non-empty |

## Migration strategy

### 1. For existing v1 code

If you're upgrading v1 code that uses helpers, the import works but triggers deprecation warnings:

```typescript
// v1 code (still works, but deprecated)
import { text, object, image } from "mcp-use";
return text("Hello");
return object({ count: 5 });
return image(base64, "image/png");
```

### 2. Preferred v2 style

```typescript
// v2 (no deprecation warning)
return { content: [{ type: "text", text: "Hello" }] };
return { 
  content: [{ type: "text", text: JSON.stringify({ count: 5 }) }],
  structuredContent: { count: 5 }
};
return { 
  content: [{ type: "image", data: base64, mimeType: "image/png" }]
};
```

### 3. Deprecation status

Helpers are marked `@deprecated` in `mcp-use@2.0.0-beta.66`. Plan migration to raw envelopes for new code.

## Do not copy tool envelopes into resource callbacks

The helpers above build **tool** results (`CallToolResult`: `content` array, `structuredContent`, `isError`). v1 code often reuses the same helper inside a `server.resource(...)` / `server.resourceTemplate(...)` callback — but resource reads return a **different** envelope, `{ contents: [...] }` (singular `contents`, each item `{ uri, mimeType?, text? | blob? }`). A tool envelope is not a valid resource result.

```typescript
// ✗ Wrong — tool envelope inside a resource callback
server.resource({ name: "settings", uri: "app://settings" }, async (uri) => {
  return { content: [{ type: "text", text: "{...}" }] }; // tool shape — invalid here
});

// ✓ Correct — resource envelope
server.resource({ name: "settings", uri: "app://settings" }, async (uri) => ({
  contents: [{ uri: uri.href, mimeType: "application/json", text: JSON.stringify({ theme: "dark" }) }],
}));
```

Map helper usage by call site: `text()`/`object()`/`markdown()` in a **tool** → raw `CallToolResult`; in a **resource** → raw `{ contents }`. See `../06-resources/01-overview.md`.

## Helper implementation (for reference)

Helpers are thin wrappers returning raw envelopes. No logic depends on them; SDK accepts both forms equally.

```typescript
// text() (actual source)
function text(content: string): ToolContentResult {
  return {
    content: [{ type: "text", text: content }],
    _meta: { mimeType: "text/plain" },
  };
}

// object() (actual source; forwards arrays to array())
function object<T extends Record<string, unknown>>(data: T): TypedCallToolResult<T> {
  if (Array.isArray(data)) return array(data) as unknown as TypedCallToolResult<T>;
  return {
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
    structuredContent: data,
    _meta: { mimeType: "application/json" },
  };
}
```

## Anti-pattern: helper nesting

Do not nest helpers; compose envelopes directly:

```typescript
// Bad (v1 style, deprecated)
return mix(text("Found users"), object({ count: 5 }));

// Good (v2 style)
return {
  content: [
    { type: "text", text: "Found users" },
    { type: "text", text: JSON.stringify({ count: 5 }) }
  ],
  structuredContent: { count: 5 }
};
```
