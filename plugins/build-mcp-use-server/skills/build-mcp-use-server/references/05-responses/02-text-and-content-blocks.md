# Text and content blocks

*Read this when returning text-only or mixed-media results.*

v2 returns raw `CallToolResult` with `content` array — `content` is always an array, even for a single block. Each block declares its type via a `type` discriminator. The full `ContentBlock` union has 5 variants:

| `type` | Required fields | Notes |
|---|---|---|
| `"text"` | `text` | No `mimeType` field |
| `"image"` | `data` (base64), `mimeType` | `mimeType` required, no default at the wire schema level |
| `"audio"` | `data` (base64), `mimeType` | `mimeType` required, no default at the wire schema level |
| `"resource_link"` | `uri`, `name` | Reference only — no inline `text`/`blob`; optional `mimeType`, `description`, `size`, `title` |
| `"resource"` | `resource` (nested `{ uri, mimeType?, text }` or `{ uri, mimeType?, blob }`) | Embedded resource; see `04-images-audio-binary-resources.md` |

Every block variant also accepts optional `annotations` and a per-block `_meta: Record<string, unknown>` (distinct from the result-level `_meta` covered in `06-meta-and-private-data.md`).

## Plain text (type: "text")

```typescript
return {
  content: [{ type: "text", text: "Hello, world!" }]
};
```

**When:** Default for all single-text results. `TextContent` has no `mimeType` field at all — see below.

## Markdown (text block)

```typescript
return {
  content: [{
    type: "text",
    text: "## Report\n\n- Item 1\n- Item 2"
  }]
};
```

**When:** Multi-line output with headings, lists, or emphasis. Text content blocks do not have a `mimeType` field in the shipped `ContentBlock` contract.

## Combining text + structured data

When tool has `outputSchema`, pair `content` (readability) with `structuredContent` (typing):

```typescript
return {
  content: [{ type: "text", text: "Found 3 users: Alice, Bob, Carol" }],
  structuredContent: { count: 3, users: [...] }
};
```

SDK auto-appends a JSON text block when `structuredContent` is a non-object value (array, string, number, boolean, or `null`) and no `type: "text"` block is already present in `content`. Object-shaped `structuredContent` is never auto-appended — always add the text block yourself.

## Mixed media example

Multiple blocks sequence in order returned:

```typescript
return {
  content: [
    { type: "text", text: "Generated chart:" },
    { type: "image", data: "iVBORw0K...", mimeType: "image/png" },
    { type: "text", text: "_Chart shows revenue trend Q1-Q3._" }
  ],
  structuredContent: { q1: 100, q2: 118, q3: 145 }
};
```

Order: lead with readable label, media, then caption/summary.

**Rule:** Always include text block for context; don't rely on image/audio alone.
