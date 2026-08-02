# Text and content blocks

*Read this when returning text-only or mixed-media results.*

v2 returns raw `CallToolResult` with `content` array. Each block declares its type.

## Plain text (type: "text")

```typescript
return {
  content: [{ type: "text", text: "Hello, world!" }]
};
```

**When:** Default for all single-text results. No MIME type = `text/plain` assumed.

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

SDK auto-appends JSON text block if `structuredContent` is scalar and no text block exists.

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
