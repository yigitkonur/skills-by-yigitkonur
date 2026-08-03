# Responses and Deprecated Helpers

*Read this to migrate response shapes and understand the helper deprecation timeline.*

## Core response envelope structure

The core result-envelope concepts remain (`content`, `structuredContent`, `isError`, resource `contents`, prompt `messages`), but do not describe the entire MCP wire protocol as unchanged — protocol revisions and capabilities changed, and v2 targets date-string revisions such as `2026-07-28`. The migration difference here is **how you construct results**:
- **v1**: Use helpers (`text()`, `object()`, `widget()`)
- **v2**: Return raw `CallToolResult`/`ReadResourceResult`/`GetPromptResult` envelopes

## Tool results: CallToolResult

**v1** (helpers):
```typescript
import { text, object, error } from "mcp-use/server";

// Helpers returned an envelope automatically
return text("Hello");
return object({ count: 5 });
return error("Invalid input");
```

**v2** (raw, preferred):
```typescript
// Explicit envelope structure
return {
  content: [{ type: "text", text: "Hello" }],
  structuredContent: { /* optional structured data */ },
};

return {
  content: [{ type: "text", text: JSON.stringify({ count: 5 }) }],
  structuredContent: { count: 5 },
};

return {
  content: [{ type: "text", text: "Invalid input" }],
  isError: true,
};
```

## Multi-block results

**v1**:
```typescript
return mix(
  text("Summary:"),
  markdown("## Results\n- Item A\n- Item B"),
  object({ items: [...] })
);
```

**v2**:
```typescript
return {
  content: [
    { type: "text", text: "Summary:" },
    { type: "text", text: "## Results\n- Item A\n- Item B" },
    { type: "text", text: JSON.stringify({ items: [...] }) },
  ],
  structuredContent: { items: [...] },
};
```

Multiple content blocks travel in the same `content: [...]` array. Do not assume hosts hide later text blocks; make every model-facing block concise and consistent with `structuredContent`.

## Images, audio, and binary (media)

**v1** (positional args — `image(data, mimeType?)`, `audio(dataOrPath, mimeType?)`, `binary(base64Data, mimeType)`):
```typescript
return image(base64ImageData, "image/png");
return audio(base64AudioData, "audio/wav");
return binary(base64Binary, "application/pdf");
```

**v2**:
```typescript
return {
  content: [{
    type: "image",
    data: base64ImageData,
    mimeType: "image/png",
  }],
  structuredContent: { /* optional */ },
};

return {
  content: [{
    type: "audio",
    data: base64AudioData,
    mimeType: "audio/wav",
  }],
};

// Embedded resource block — `resource` is a nested object, not flat fields
return {
  content: [{
    type: "resource",
    resource: {
      uri: "file://path/to/document.pdf",
      mimeType: "application/pdf",
      blob: base64PdfData,
    },
  }],
};
```

## Widget helper → raw envelope

**v1**:
```typescript
import { widget } from "mcp-use/server";

return widget({
  props: { query: "search term", results: [...] },
  output: text("Found 5 results"),
});
```

**v2** (preferred):
```typescript
// Tool declares `view: { name: "results-view" }`
// Result includes both text (for model) and structuredContent (for View)
return {
  content: [{ type: "text", text: "Found 5 results" }],
  structuredContent: { query: "search term", results: [...] },
  _meta: { /* optional metadata */ },
};
```

Structured content is automatically passed to the View via `useToolContext().toolOutput`. No need for a `props` wrapper.

## Deprecated helpers: Full v1 → v2 mapping

These helpers remain as **deprecated shims** for backward compatibility. Migrate to raw envelopes; beta.66 does not specify a removal release.

All v1 helpers took **positional arguments** (`text(content)`, `image(data, mimeType?)`, `object(data)`), not an options object. `ContentBlock`'s `text` variant is `{ type: "text", text }` only — it carries no `mimeType` field at the wire level; v1's `markdown()`/`html()`/`css()`/`javascript()`/`xml()` helpers only ever set `mimeType` on the deprecated wrapper's `_meta`, which the model does not see. Prefer plain text content in v2 and describe the format in the tool/description text instead.

| v1 Helper (positional args) | v2 Equivalent Raw Envelope | Migration path |
|---|---|---|
| `text(s)` | `{ content: [{ type: "text", text: s }] }` | Inline the content block |
| `markdown(s)` | `{ content: [{ type: "text", text: s }] }` | Same as `text`; no wire-level `mimeType` on text blocks |
| `object(o)` | `{ content: [{ type: "text", text: JSON.stringify(o) }], structuredContent: o }` | Must include both blocks |
| `array(a)` | `{ content: [{ type: "text", text: JSON.stringify(a) }], structuredContent: a }` | v1 wrapped as `{ data: a }`; v2 does not — put `a` directly in `structuredContent` |
| `error(msg)` | `{ content: [{ type: "text", text: msg }], isError: true }` | Add `isError: true` |
| `mix(...)` | `{ content: [block1, block2, ...], structuredContent: {...} }` | Array of content blocks |
| `image(data, mimeType?)` | `{ content: [{ type: "image", data, mimeType }] }` | Explicit type; v1 default `mimeType` was `"image/png"` |
| `audio(dataOrPath, mimeType?)` | `{ content: [{ type: "audio", data, mimeType }] }` | Explicit type; v1 default `mimeType` was `"audio/wav"` (v1 also accepted a file path and read it async — v2 has no equivalent, read the file yourself) |
| `binary(base64Data, mimeType)` | `{ content: [{ type: "resource", resource: { uri, mimeType, blob: base64Data } }] }` | `resource` is a nested object with `uri`/`mimeType`/`text-or-blob`, not flat fields on the content block |
| `resource(uri, mimeType, text?)` | `{ content: [{ type: "resource", resource: { uri, mimeType, text } }] }` | Same nested shape |
| `html(html)` | `{ content: [{ type: "text", text: html }] }` | No wire-level `mimeType`; describe the format in tool text/description |
| `javascript(js)` | `{ content: [{ type: "text", text: js }] }` | No wire-level `mimeType` |
| `css(css)` | `{ content: [{ type: "text", text: css }] }` | No wire-level `mimeType` |
| `xml(xml)` | `{ content: [{ type: "text", text: xml }] }` | No wire-level `mimeType` |
| `widget(...)` | `{ content: [...], structuredContent: {...}, _meta: {...} }` | No wrapper; use View binding |

## Validation: Input and output

**v1**:
```typescript
server.tool({
  name: "add",
  schema: z.object({ a: z.number(), b: z.number() }),
  outputSchema: z.object({ sum: z.number() }),
  cb: async ({ a, b }) => { ... }
});
```

**v2** (same validation logic, clearer structure):
```typescript
export const add = server.tool(
  {
    name: "add",
    inputSchema: z.object({ a: z.number(), b: z.number() }),
    outputSchema: z.object({ sum: z.number() }),
  },
  async ({ a, b }) => {
    const sum = a + b;
    return {
      content: [{ type: "text", text: `${a} + ${b} = ${sum}` }],
      structuredContent: { sum },
    };
  }
);
```

SDK validates input against `inputSchema` before your callback runs. If `outputSchema` is set, SDK validates your result's `structuredContent` against it and rejects malformed results.

## Error handling: isError vs. throw

**Option 1: Return an error envelope** (preferred):
```typescript
if (!isValid) {
  return {
    content: [{ type: "text", text: "Invalid query" }],
    isError: true,
  };
}
```

**Option 2: Throw an error** (auto-wrapped):
```typescript
if (!isValid) {
  throw new Error("Invalid query");
}
// SDK converts to { content: [...], isError: true }
```

Both work. Returning an explicit envelope is cleaner and gives you control over the error message sent to the model.

---

**Next**: See `05-v1-to-v2-auth.md` for authentication and OAuth provider changes.
