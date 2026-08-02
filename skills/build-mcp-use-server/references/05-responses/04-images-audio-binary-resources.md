# Images, audio, binary, and resources

*Read this when returning media (images, audio, PDFs) or embedded resources.*

## Images (PNG, JPEG, WebP)

Content block with `type: "image"`:

```typescript
return {
  content: [{
    type: "image",
    data: "iVBORw0KGgoAAAANSU...",  // base64
    mimeType: "image/png",
  }],
};
```

**When:** Screenshots, charts, diagrams, generated visuals.

**Encoding:** Base64; use `Buffer.from(bytes).toString("base64")` in Node.

## Audio (MP3, WAV, OGG)

Same envelope as image (SDK uses `type: "image"` for all binary):

```typescript
return {
  content: [{
    type: "image",
    data: "//NExAA...",  // base64 MP3
    mimeType: "audio/mpeg",
  }],
};
```

**When:** Speech synthesis, audio clips, podcasts.

## Binary (PDF, ZIP, video)

```typescript
return {
  content: [{
    type: "image",
    data: "JVBERi0xLjQ...",  // base64 PDF
    mimeType: "application/pdf",
  }],
};
```

**When:** Downloadable files, documents, archives. Do not use for large video files; stream via URL instead.

**Size guardrail:** Keep base64 payloads under 10 MB; larger files should be uploaded and referenced by URL.

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
- `mimeType` — MIME type of content
- `text` — string content (for text-based resources)
- `blob` — Uint8Array (for binary resources)

Use `text` OR `blob`, not both.

## Media in tool results with text

Lead with context, then media:

```typescript
return {
  content: [
    { type: "text", text: "Generated image preview:" },
    { type: "image", data: "iVBORw0K...", mimeType: "image/png" },
    { type: "text", text: "_Image dimensions: 1024x768_" },
  ],
};
```

**Rule:** Always pair media with a text label; never return binary alone.
