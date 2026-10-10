# Responses and Deprecated Helpers

*Read this to migrate response shapes from legacy helper functions to raw MCP CallToolResult envelopes and understand the helper deprecation timeline.*

In `mcp-use v1`, tool callbacks typically returned helper functions (`text()`, `object()`, `mix()`, `widget()`) imported from `mcp-use/server`. These helpers automatically assembled JSON-RPC response envelopes.

In `mcp-use v2`, helper functions are **deprecated upgrade shims**. Canonical v2 tools return raw, type-safe **`CallToolResult` envelopes** directly. This aligns with the MCP specification (targeting protocol revisions such as `2026-07-28`), provides unambiguous separation between model-facing content and View-facing structured data, and guarantees deterministic typechecking against `outputSchema`.

---

## At a Glance: Responses & Helpers Diff

| Response Pattern | Legacy v1 (`mcp-use <= 1.34.5`) | Canonical v2 (`mcp-use >= 2.8.2`) | Impact / Action |
|---|---|---|---|
| **Text Result** | `return text("Success");` | `return { content: [{ type: "text", text: "Success" }] };` | Explicit `ContentBlock` array |
| **Object / JSON Result** | `return object({ count: 5 });` | `return { content: [{ type: "text", text: JSON.stringify({ count: 5 }) }], structuredContent: { count: 5 } };` | Explicit JSON string block + typed `structuredContent` |
| **Error Result** | `return error("Invalid ID");` | `return { content: [{ type: "text", text: "Invalid ID" }], isError: true };` | Set `isError: true` on envelope |
| **Multi-Block Result** | `return mix(text("A"), object(B));` | `return { content: [blockA, blockB], structuredContent: B };` | Single array containing all blocks |
| **Widget / View Result** | `return widget({ props, output });` | `return { content: [...], structuredContent: ..., _meta: ... };` | `structuredContent` for model/view; `_meta` for view-only data |
| **Image Block** | `image(data, "image/png")` | `{ type: "image", data: base64, mimeType: "image/png" }` | Raw image block in `content` array |
| **Audio Block** | `audio(dataOrPath, "audio/wav")` | `{ type: "audio", data: base64, mimeType: "audio/wav" }` | Raw audio block in `content` array; read files manually |
| **Embedded Resource** | `binary(data, "application/pdf")` | `{ type: "resource", resource: { uri, mimeType, blob } }` | Nested `resource` object with `uri`, `mimeType`, and `blob`/`text` |
| **Helper Status** | Primary return mechanism | **Deprecated shims**; retained for backward compatibility | Migrate to raw envelopes for full type safety |

---

## The Raw `CallToolResult` Envelope Structure

The wire specification for an MCP tool execution result is:

```typescript
type CallToolResult<TOutput = unknown> = {
  // Required: One or more content blocks displayed to model and host
  content: ContentBlock[];

  // Optional: Structured JSON payload validated against outputSchema
  structuredContent?: TOutput;

  // Optional: Flags operational failure without throwing JSON-RPC transport error
  isError?: boolean;

  // Optional: View-only or client-specific metadata (not sent to LLM context)
  _meta?: Record<string, unknown>;
};
```

### Content Block Variants

```typescript
type ContentBlock =
  | { type: "text"; text: string }
  | { type: "image"; data: string; mimeType: string } // data is base64 string
  | { type: "audio"; data: string; mimeType: string } // data is base64 string
  | {
      type: "resource";
      resource: {
        uri: string;
        mimeType?: string;
        text?: string;
        blob?: string; // base64 string
      };
    };
```

---

## Tool Results: From Helpers to Raw Envelopes

### 1. Plain Text Return
```typescript
// v1 (Deprecated)
return text("Task completed successfully.");

// v2 (Canonical)
return {
  content: [{ type: "text", text: "Task completed successfully." }],
};
```

### 2. Structured JSON Return
In v1, `object({ count: 5 })` automatically serialized the object to text while attaching it to structured data. In v2, you explicitly provide both the human/model-readable text block and the machine-readable `structuredContent`:

```typescript
// v1 (Deprecated)
return object({ id: "item_123", status: "active", count: 42 });

// v2 (Canonical)
const data = { id: "item_123", status: "active", count: 42 };
return {
  content: [{ type: "text", text: `Item ${data.id} is ${data.status} (Count: ${data.count})` }],
  structuredContent: data,
};
```

> **Why this matters**: Providing a concise, formatted text summary alongside `structuredContent` helps LLMs understand the key result without having to parse complex JSON payloads in raw prompt context.

### 3. Error Envelopes: `isError` vs. Throwing
In v1, `error("Item not found")` wrapped the error. In v2, return an explicit error envelope:

```typescript
// v1 (Deprecated)
return error("Account balance insufficient.");

// v2 (Canonical)
return {
  content: [{ type: "text", text: "Account balance insufficient." }],
  isError: true,
};
```

- **Returning `{ isError: true }`**: Informs the model that the tool failed operationally (e.g., validation error, missing record, insufficient balance). The conversation continues, and the model can retry or correct inputs.
- **Throwing `new Error(...)`**: Uncaught exceptions are automatically caught by the framework and converted to `{ isError: true, content: [{ type: "text", text: error.message }] }`. However, returning the envelope explicitly gives you full control over the model-facing text.

---

## Multi-Block Results & Media Envelopes

### Multi-Block Mixtures
In v1, returning multiple elements required `mix()`:

```typescript
// v1 (Deprecated)
return mix(
  text("Execution Summary:"),
  markdown("### Findings\n- Item 1\n- Item 2"),
  object({ total: 2 })
);

// v2 (Canonical)
return {
  content: [
    { type: "text", text: "Execution Summary:" },
    { type: "text", text: "### Findings\n- Item 1\n- Item 2" },
    { type: "text", text: JSON.stringify({ total: 2 }) },
  ],
  structuredContent: { total: 2 },
};
```

### Media Envelopes: Images, Audio, and Binary Resources

In v1, helpers accepted positional arguments (`image(data, mimeType)`). In v2, return explicit typed blocks:

```typescript
// 1. Image Block (base64 data without data: URI prefix)
return {
  content: [
    {
      type: "image",
      data: base64PngString,
      mimeType: "image/png",
    },
  ],
};

// 2. Audio Block
return {
  content: [
    {
      type: "audio",
      data: base64WavString,
      mimeType: "audio/wav",
    },
  ],
};

// 3. Embedded Resource Block (PDF, binary, or structured document)
return {
  content: [
    {
      type: "resource",
      resource: {
        uri: "file://reports/financial-q3.pdf",
        mimeType: "application/pdf",
        blob: base64PdfString,
      },
    },
  ],
};
```

---

## Widget Helper Migration: Separating Model vs. View Data

In v1, widgets were returned using `widget({ props, output })`:
- `props`: Sent to the widget component (hidden from the model).
- `output`: Model-visible text.

In `mcp-use v2`, this mechanism changed fundamentally:
- **`structuredContent`**: Validated against `outputSchema` and sent to **both the View and the model**.
- **`_meta`**: Arbitrary dictionary sent **only to the View** via `useToolContext().meta` (hidden from the model).

```typescript
// v1 (Deprecated)
return widget({
  props: { rawDatabaseRows: [...], internalDebugInfo: {...} },
  output: text("Found 5 records"),
});

// v2 (Canonical)
const records = await db.query(...);
return {
  content: [{ type: "text", text: `Found ${records.length} matching records.` }],
  structuredContent: { count: records.length, summary: "Matches found" }, // Model-visible, schema-checked
  _meta: { rawDatabaseRows: records }, // View-only, hidden from model context!
};
```

---

## Deprecated Helpers: Complete Reference Mapping

These helper functions are exported from `mcp-use` root solely as backward-compatibility shims. They will be removed in a future release:

| v1 Positional Helper | v2 Raw Envelope Replacement |
|---|---|
| `text(s)` | `{ content: [{ type: "text", text: s }] }` |
| `markdown(s)` | `{ content: [{ type: "text", text: s }] }` (No wire-level markdown MIME on text blocks) |
| `object(o)` | `{ content: [{ type: "text", text: JSON.stringify(o) }], structuredContent: o }` |
| `array(a)` | `{ content: [{ type: "text", text: JSON.stringify(a) }], structuredContent: a }` |
| `error(msg)` | `{ content: [{ type: "text", text: msg }], isError: true }` |
| `mix(...blocks)` | `{ content: [b1, b2, ...], structuredContent?: {...} }` |
| `image(data, mimeType?)` | `{ content: [{ type: "image", data, mimeType: mimeType ?? "image/png" }] }` |
| `audio(data, mimeType?)` | `{ content: [{ type: "audio", data, mimeType: mimeType ?? "audio/wav" }] }` |
| `binary(data, mimeType)` | `{ content: [{ type: "resource", resource: { uri: "...", mimeType, blob: data } }] }` |
| `widget({ props, output })` | `{ content: [...], structuredContent: {...}, _meta: props }` |

---

## Anti-Patterns and Common Response Traps

| Anti-Pattern | Root Mechanism & Failure Mode | Canonical v2 Fix |
|---|---|---|
| **Returning Unwrapped Strings or Objects** | Writing `return "Success"` or `return { count: 5 }` without `{ content: [...] }` violates the MCP protocol envelope. | Return an object containing `content: [{ type: "text", text: "..." }]`. |
| **Leaking Private View Data into `structuredContent`** | Placing massive raw database dumps or confidential internal IDs in `structuredContent` exposes them to the LLM context. | Put private or view-only data in `_meta: { ... }` and read it in the view via `ctx.meta`. |
| **Mismatched `structuredContent` and `outputSchema`** | Returning a `structuredContent` object that does not conform to the declared `outputSchema` triggers validation errors before the client receives the response. | Ensure `structuredContent` conforms exactly to your Zod `outputSchema`. |
| **Adding `mimeType` Directly to a Text ContentBlock** | Writing `{ type: "text", text: "...", mimeType: "text/markdown" }` violates wire schema; MCP text blocks do not have a `mimeType` property. | Plain text blocks only carry `type: "text"` and `text: string`. Describe format in the text or tool description. |
| **Throwing Unhandled Errors for Expected Failures** | Throwing `new Error("User not found")` logs internal runtime errors. Returning `{ isError: true }` signals model-level recovery. | Reserve `throw` for catastrophic infrastructural faults; return `{ isError: true }` for domain/input failures. |

---

## Next Steps & Cross-References

- **Authentication & Mixed Auth**: See `05-v1-to-v2-auth.md` for user context and security schemes.
- **Widgets to Views**: See `06-v1-to-v2-widgets-to-views.md` for consuming `structuredContent` and `_meta` in React Views.
- **Interactive Elicitation**: See `10-elicitation-and-state-evolution.md` for returning `InputRequiredResult` envelopes.
