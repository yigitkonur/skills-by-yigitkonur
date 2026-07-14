# `image()`, `audio()`, `binary()`

Binary-adjacent helpers in `mcp-use@1.26.0`. The package exports `image()`, `audio()`, and `binary()`; it does **not** export response helpers named `video()` or `file()`.

Use `binary(base64, mimeType)` for video files, PDFs, zips, and other non-image/non-audio payloads. For files on disk, read the file yourself and pass base64 to the matching helper, except for audio paths, which `audio()` can read asynchronously.

## `image(data, mimeType?)`

Returns MCP image content from base64 data or a data URL. Default MIME: `image/png`.

```typescript
import { image } from "mcp-use/server";

server.tool({ name: "generate-chart" }, async ({ data }) => {
  const chart = await generateChart(data);  // base64 string
  return image(chart, "image/png");
});

return image(screenshotBase64, "image/jpeg");
return image(webpBase64, "image/webp");
```

Common MIME values: `image/png`, `image/jpeg`, `image/webp`, `image/gif`, `image/svg+xml`.

Runtime shape: `content[0]` has `{ type: "image", data, mimeType }`; `_meta` includes `mimeType` and `isImage: true`.

## `audio(dataOrPath, mimeType?)`

Accepts base64 data synchronously, or a filesystem path asynchronously. MIME defaults to `audio/wav` for base64 data and is inferred from common audio file extensions when a path is used.

```typescript
import { audio } from "mcp-use/server";

// Base64 — sync
server.tool({ name: "synth" }, async () => audio(base64Wav, "audio/wav"));

// File path — must await
server.resource({ name: "alert", uri: "audio://alert" }, async () =>
  await audio("./sounds/notification.wav")
);

return await audio("./out/greeting.wav", "audio/wav");
```

Supported file extensions in the helper: `.wav`, `.mp3`, `.ogg`, `.m4a`, `.webm`, `.flac`, `.aac`.

Runtime shape: `content[0]` has `{ type: "audio", data, mimeType }`; `_meta` includes `mimeType` and `isAudio: true`.

## `binary(base64Data, mimeType)`

Generic binary helper. Use for any base64 payload that isn't an image or audio — PDFs, zips, video bytes, octet streams.

```typescript
import { binary } from "mcp-use/server";

server.resource({ name: "doc", uri: "file://doc.pdf" }, async () => {
  const pdf = await readFile("./document.pdf");
  return binary(pdf.toString("base64"), "application/pdf");
});

return binary(zipBase64, "application/zip");
return binary(mp4Base64, "video/mp4");
return binary(buf.toString("base64"), "application/octet-stream");
```

Common MIME values: `application/pdf`, `application/zip`, `application/octet-stream`, `application/x-tar`, `video/mp4`, `video/webm`.

Runtime shape: `content[0]` is a text block containing the base64 string; `_meta` includes `mimeType` and `isBinary: true`. Do not expect a separate MCP `video` or `file` content block from this helper.

## Signatures and MIME

| Helper | Signature | Default MIME | Async? |
|---|---|---|---|
| `image` | `image(data, mimeType?)` | `image/png` | No |
| `audio` | `audio(dataOrPath, mimeType?)` | `audio/wav` for base64; inferred for paths | Only for paths |
| `binary` | `binary(base64Data, mimeType)` | none — pass explicit | No |

## Anti-patterns

- **Binary as `text(base64)`.** The client receives no binary metadata. Use `binary(base64, mimeType)`.
- **Forgetting `await` on file-path `audio()`.** File-path audio returns a `Promise<CallToolResult>`.
- **Inventing `video()` or `file()`.** They are not exported by `mcp-use/server` in `1.26.0`.
- **Not setting MIME on `binary()`.** It is required.
- **Using `image()` for non-image binaries.** `image()` defaults to `image/png`; use `binary()` instead.

## Mixed examples

Bundle the binary with a user-facing explanation using `mix()`:

```typescript
server.tool(
  { name: "export-invoice-pdf", description: "Export an invoice as a PDF." },
  async () => {
    const pdfBase64 = await renderInvoicePdf();
    return mix(
      text("Invoice PDF generated."),
      binary(pdfBase64, "application/pdf"),
    );
  }
);

server.tool(
  { name: "screenshot", schema: z.object({ url: z.string().url() }) },
  async ({ url }) => {
    const png = await capture(url);
    return mix(
      text(`Captured ${url}.`),
      image(png, "image/png"),
    );
  }
);
```
