# Deprecated v1 response helpers

*Read this only if migrating v1 code or using legacy compatibility mode.*

v2 exports v1 helpers **for compatibility only**. They are marked `@deprecated` and will be removed in v3. New code should return raw MCP envelopes.

## Full v1→v2 mapping table

| v1 helper | v1 signature | v2 raw envelope | Status | Notes |
|---|---|---|---|---|
| `text(str)` | `text("hello")` | `{ content: [{ type: "text", text: "hello" }] }` | Deprecated | Plain text; MIME auto-set to text/plain |
| `markdown(str)` | `markdown("# Title")` | `{ content: [{ type: "text", text: "# Title", mimeType: "text/markdown" }] }` | Deprecated | Add mimeType to set client rendering mode |
| `html(str)` | `html("<div>...</div>")` | `{ content: [{ type: "text", text: "...", mimeType: "text/html" }] }` | Deprecated | Plaintext in block; mimeType signals parsing |
| `xml(str)` | `xml("<root>...</root>")` | `{ content: [{ type: "text", text: "...", mimeType: "text/xml" }] }` | Deprecated | XML payload; MIME type declaration |
| `css(str)` | `css("body { ... }")` | `{ content: [{ type: "text", text: "...", mimeType: "text/css" }] }` | Deprecated | CSS payload; MIME type signals parsing |
| `javascript(str)` | `javascript("console.log(...)")` | `{ content: [{ type: "text", text: "...", mimeType: "text/javascript" }] }` | Deprecated | JS source; MIME type declaration |
| `object(obj)` | `object({ a: 1 })` | `{ content: [{ type: "text", text: JSON.stringify(obj) }], structuredContent: obj }` | Deprecated | Structured data; populates both content and schema |
| `array(arr)` | `array([1, 2])` | `{ content: [{ type: "text", text: JSON.stringify(arr) }], structuredContent: arr }` | Deprecated | Array wrapper; auto-appends JSON text block |
| `image(base64, mime)` | `image("iVBORw0...", "image/png")` | `{ content: [{ type: "image", data: "iVBORw0...", mimeType: "image/png" }] }` | Deprecated | Base64 image data; MIME type signals encoding |
| `audio(base64, mime)` | `audio("//NExAA...", "audio/mpeg")` | `{ content: [{ type: "image", data: "//NExAA...", mimeType: "audio/mpeg" }] }` | Deprecated | Audio in binary; same envelope as image |
| `binary(base64, mime)` | `binary("JVBERi0...", "application/pdf")` | `{ content: [{ type: "image", data: "JVBERi0...", mimeType: "application/pdf" }] }` | Deprecated | Generic binary; MIME type signals type |
| `resource(obj)` | `resource(readResult)` | Return `ReadResourceResult` directly | Deprecated | Use `{ contents: [...] }` envelope for resources |
| `error(msg)` | `error("Not found")` | `{ isError: true, content: [{ type: "text", text: "Not found" }] }` | Deprecated | Error flag + message; no structuredContent |
| `widget(obj)` | `widget({ props, metadata })` | (Documented in 18-mcp-apps; uses `structuredContent` + `_meta`) | Removed | Widget term deprecated; use Views (MCP Apps) |
| `mix(...)` | `mix(text(...), image(...))` | Return single envelope with multiple `content` blocks | Deprecated | Manual composition of content array |

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

### 3. Removal timeline

Helpers will be removed in **mcp-use v3.0.0** (no announced date). Plan migration during v2 dev/beta window.

## Helper implementation (for reference)

Helpers are thin wrappers returning raw envelopes. No logic depends on them; SDK accepts both forms equally.

```typescript
// Example: how text() works (simplified)
function text(content: string): CallToolResult {
  return { content: [{ type: "text", text: content }] };
}

// Example: how object() works
function object(data: any): CallToolResult {
  return {
    content: [{ type: "text", text: JSON.stringify(data) }],
    structuredContent: data,
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
