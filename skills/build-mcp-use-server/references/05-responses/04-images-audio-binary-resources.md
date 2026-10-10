# Images, audio, binary, and resources

*Read this when returning media (images, audio, PDFs) or embedded resources.*

## Images (PNG, JPEG, WebP)

Content block with `type: "image"`:

```typescript
return {
  content: [{
    type: "image",
    data: "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9ZQmcAAAAASUVORK5CYII=", // valid 1×1 PNG
    mimeType: "image/png",
  }],
};
```

**When:** Screenshots, charts, diagrams, generated visuals.

**Encoding:** Base64; use `Buffer.from(bytes).toString("base64")` in Node. `mimeType` is required on the wire schema — there is no default; always set it explicitly.

## Audio (MP3, WAV, OGG)

Audio has its own content-block discriminator:

```typescript
return {
  content: [{
    type: "audio",
    data: "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAIA+AAACABAAZGF0YQAAAAA=", // valid empty WAV
    mimeType: "audio/wav",
  }],
};
```

**When:** Speech synthesis, audio clips, podcasts. `mimeType` is required on the wire schema, same as images.

## Binary (PDF, ZIP, video)

`CallToolResult` supports embedding binary resources via `{ type: "resource", resource: { uri, mimeType, blob } }` where `blob` is a base64-encoded string. For external files, return the download URL in a `text` block or reference URI in an embedded resource:

```typescript
// External PDF: return download link in text block
return {
  content: [{
    type: "text",
    text: "Download the generated report: https://files.example.com/report.pdf",
  }],
};

// Inline PDF: embed real PDF bytes as base64.
return {
  content: [{
    type: "resource",
    resource: {
      uri: "generated://report.pdf",
      mimeType: "application/pdf",
      blob: base64Pdf,  // base64 string, not Uint8Array — same as ReadResourceResult.contents[].blob
    },
  }],
};
```

For inline resources, `resource.text` and `resource.blob` are mutually exclusive per block (the union has no combined variant) — pick the field that matches the actual payload. Use a text URL for an external file; use inline `blob` only for real bytes you've already sized under the guardrail below.

**When:** Downloadable files, documents, archives. Do not inline large files; serve them through a resource URI.

**Size guardrail:** Keep base64 payloads under 10 MB; larger files should be uploaded and referenced by URL.

## External References vs Embedded Resources

In standard MCP tool calls, use embedded `{ type: "resource", resource: { uri, mimeType, text | blob } }` when delivering content inline. For external files that the client should fetch separately (or via `resources/read`), return the target URI in a standard text content block or provide a link URL in `text`.

## Resources (reading static/dynamic content)

Resource callbacks return `ReadResourceResult`:

```typescript
server.resource(
  {
    name: "config",
    uri: "app://config",
    description: "Current app config",
  },
  async (uri, ctx) => ({
    contents: [{
      uri: uri.href,
      mimeType: "application/json",
      text: JSON.stringify({ version: "1.0.0" }),
    }],
  })
);
```

**Fields:**
- `uri` — resource URI (must match request URI)
- `mimeType` — MIME type of content (optional on the wire schema, but always set it in practice)
- `text` — string content (for text-based resources)
- `blob` — **base64-encoded string** (for binary resources) — not `Uint8Array`; encode with `Buffer.from(bytes).toString("base64")` in Node before assigning

Use `text` OR `blob`, not both — they are two variants of a discriminated union, not two optional fields on one shape.

**Returning a `CallToolResult`-shaped value from a resource callback:** if a resource (or prompt) callback returns a raw `CallToolResult` — e.g. by calling one of the deprecated helpers from `07-deprecated-v1-helpers.md` — mcp-use auto-converts it via `toResourceResult(result, uri)` (for resources) or `toPromptResult(result)` (for prompts), both from `response-conversion.ts`, wired in automatically by `server.resource()`/`server.prompt()`. `toResourceResult` maps each `ContentBlock`: `text` → a text resource-contents entry, `image`/`audio` `data` → `blob`, embedded `resource` → unwrapped directly,  an empty `content` with `structuredContent` set becomes a synthesized JSON text entry. You do not need to call these yourself — return a native `ReadResourceResult`/`GetPromptResult` directly, or a `CallToolResult`-shaped value and let the conversion happen.

## Media in tool results with text

Lead with context, then media:

```typescript
return {
  content: [
    { type: "text", text: "Generated image preview:" },
    { type: "image", data: "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9ZQmcAAAAASUVORK5CYII=", mimeType: "image/png" },
    { type: "text", text: "_Image dimensions: 1024x768_" },
  ],
};
```

**Rule:** Always pair media with a text label; never return binary alone.
