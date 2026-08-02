# Responses and Deprecated Helpers

*Read this to migrate response shapes and understand the helper deprecation timeline.*

## Response envelope structure (unchanged wire format)

MCP wire format is the same in v1 and v2. The difference is **how you construct it**:
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

**v1**:
```typescript
return image({ data: base64ImageData, mimeType: "image/png" });
return audio({ data: base64AudioData });
return binary({ data: base64Binary, mimeType: "application/pdf" });
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
    mimeType: "audio/mpeg",
  }],
};

return {
  content: [{
    type: "resource",
    uri: "file://path/to/document.pdf",
    mimeType: "application/pdf",
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

| v1 Helper | v2 Equivalent Raw Envelope | Migration path |
|---|---|---|
| `text(s)` | `{ content: [{ type: "text", text: s }], structuredContent: {} }` | Inline the content block |
| `markdown(s)` | `{ content: [{ type: "text", text: s }] }` | Return Markdown as text; `ContentBlock` has no text-block `mimeType` field |
| `object(o)` | `{ content: [{ type: "text", text: JSON.stringify(o) }], structuredContent: o }` | Must include both blocks |
| `array(a)` | `{ content: [{ type: "text", text: JSON.stringify(a) }], structuredContent: a }` | Note: v1 wrapped as `{ data: a }`; v2 does not |
| `error(msg)` | `{ content: [{ type: "text", text: msg }], isError: true }` | Add `isError: true` |
| `mix(...)` | `{ content: [block1, block2, ...], structuredContent: {...} }` | Array of content blocks |
| `image({ data, mimeType })` | `{ content: [{ type: "image", data, mimeType }] }` | Explicit type |
| `audio({ data })` | `{ content: [{ type: "audio", data, mimeType: "audio/mpeg" }] }` | Explicit type + mimeType |
| `binary({ data, mimeType })` | `{ content: [{ type: "resource", uri: "...", mimeType }], text: base64 }` | Use `type: "resource"` for binaries |
| `html(html)` | `{ content: [{ type: "text", text: html, mimeType: "text/html" }] }` | Add `mimeType` |
| `javascript(js)` | `{ content: [{ type: "text", text: js, mimeType: "application/javascript" }] }` | Add `mimeType` |
| `css(css)` | `{ content: [{ type: "text", text: css, mimeType: "text/css" }] }` | Add `mimeType` |
| `xml(xml)` | `{ content: [{ type: "text", text: xml, mimeType: "application/xml" }] }` | Add `mimeType` |
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
