# `resource()` and Non-Exported Streaming/File Helpers

This file keeps the numbered cluster slot for older drafts that mentioned streaming and files. In `mcp-use@1.26.0`, `mcp-use/server` exports `resource()` but does **not** export response helpers named `stream()` or `file()`.

Use `resource()` for embedded MCP resources. For file bytes, read from disk and return `text()`, `markdown()`, `html()`, `image()`, `audio()`, or `binary()` yourself. For progress during long work, use `ctx.reportProgress()` or notifications; do not invent a response helper.

## `resource(uri, mimeType, text)`

Three-argument form embeds text content with an explicit MIME type:

```typescript
import { resource } from "mcp-use/server";

return resource(
  "config://app",
  "application/json",
  JSON.stringify({ api: "v2" })
);
```

Runtime shape:

```typescript
{
  content: [{
    type: "resource",
    resource: {
      uri: "config://app",
      mimeType: "application/json",
      text: "{\"api\":\"v2\"}"
    }
  }]
}
```

## `resource(uri, helperResult)`

Two-argument form embeds the first text block and MIME type from another response helper:

```typescript
import { resource, text, object } from "mcp-use/server";

return resource("test://greeting", text("Hello"));
return resource("data://user", object({ id: 1, name: "Alice" }));
```

Important runtime detail: this form extracts `resource.text` only from the first text content block and extracts `resource.mimeType` from `_meta.mimeType`. It does not preserve the helper's `structuredContent`.

Use this form for small embedded resources where the URI and readable resource payload are the important result.

## Filesystem alternatives

There is no exported `file(path)` response helper in `1.26.0`.

```typescript
import { binary, image, markdown } from "mcp-use/server";
import { readFile } from "node:fs/promises";

const pdf = await readFile("./reports/q3.pdf");
return binary(pdf.toString("base64"), "application/pdf");

const logo = await readFile("./assets/logo.png");
return image(logo.toString("base64"), "image/png");

const readme = await readFile("./README.md", "utf8");
return markdown(readme);
```

Exception: `audio(path)` is exported and reads audio files asynchronously. See `05-image-audio-video-binary.md`.

## Long-running work alternatives

There is no exported `stream(generator)` response helper in `1.26.0`.

For long-running handlers:

- Return a final `text()`, `markdown()`, `object()`, or `mix()` result when the work is complete.
- If the client supplied a progress token, call `await ctx.reportProgress(progress, total, message)`.
- For server-initiated events, use the notification APIs documented in `../14-notifications/`.
- For widget argument/result streaming, use `../18-mcp-apps/streaming-tool-props/`, not a response helper.

## Combined example

```typescript
import { mix, text, resource, object, binary } from "mcp-use/server";
import { readFile } from "node:fs/promises";

server.tool(
  { name: "generate-report-bundle" },
  async () => {
    const pdf = await readFile("./out/report.pdf");
    return mix(
      text("Report generated. PDF and metadata attached."),
      binary(pdf.toString("base64"), "application/pdf"),
      resource("data://report-summary", object({ rows: 42, generatedAt: Date.now() })),
    );
  }
);
```
