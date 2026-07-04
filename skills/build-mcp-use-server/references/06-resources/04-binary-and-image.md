# Binary and Image Resources

Use `image()`, `audio()`, or `binary()` for non-text content.

## Helper signatures

In current `mcp-use/server`, binary-style helpers are string-based. Convert `Buffer` or `Uint8Array` before returning them.

| Helper | Signature | Use for |
|---|---|---|
| `image(data, mimeType?)` | `(dataUrlOrBase64: string, mimeType?: string)` | PNG, JPEG, GIF, WebP, SVG |
| `audio(dataOrPath, mimeType?)` | `(base64OrPath: string, mimeType?: string)` | MP3, WAV, OGG |
| `binary(data, mimeType)` | `(base64: string, mimeType: string)` | PDF, ZIP, anything else |

`image()` defaults `mimeType` to `image/png`. `binary()` requires it.

## Images

```typescript
import { image } from "mcp-use/server";
import { readFile } from "node:fs/promises";

server.resource(
  { name: "logo", uri: "assets://logo.png", mimeType: "image/png" },
  async () => {
    const buffer = await readFile("./public/logo.png");
    return image(buffer.toString("base64"), "image/png");
  },
);
```

For dynamically generated images:

```typescript
server.resourceTemplate(
  { name: "chart", uriTemplate: "charts://{metric}.png", mimeType: "image/png" },
  async (uri, { metric }) => {
    const png = await renderChartPng(metric); // returns Buffer
    return image(png.toString("base64"), "image/png");
  },
);
```

## PDFs and other binary

```typescript
import { binary } from "mcp-use/server";

server.resourceTemplate(
  {
    name: "invoice",
    uriTemplate: "invoices://{id}.pdf",
    mimeType: "application/pdf",
  },
  async (uri, { id }) => {
    const pdf = await generateInvoicePdf(id);
    return binary(pdf.toString("base64"), "application/pdf");
  },
);
```

## Audio

```typescript
import { audio } from "mcp-use/server";
import { readFile } from "node:fs/promises";

server.resource(
  {
    name: "notification-sound",
    uri: "assets://notification.mp3",
    mimeType: "audio/mpeg",
  },
  async () => {
    const buffer = await readFile("./assets/notification.mp3");
    return audio(buffer.toString("base64"), "audio/mpeg");
  },
);
```

`audio()` also accepts a file path string and returns a Promise — convenient for static files.

## MIME type matrix

| Resource type | MIME |
|---|---|
| PNG | `image/png` |
| JPEG | `image/jpeg` |
| GIF | `image/gif` |
| WebP | `image/webp` |
| SVG | `image/svg+xml` |
| PDF | `application/pdf` |
| ZIP | `application/zip` |
| MP3 | `audio/mpeg` |
| WAV | `audio/wav` |
| OGG audio | `audio/ogg` |

## Common mistakes

| Wrong | Right |
|---|---|
| `image(buffer, "image/png")` | `image(buffer.toString("base64"), "image/png")` |
| `binary(arrayBuffer, "application/pdf")` | `binary(Buffer.from(arrayBuffer).toString("base64"), "application/pdf")` |
| `binary(base64)` | `binary(base64, "application/pdf")` |

## Performance

- Large binaries block the event loop while base64-encoding. For files >5 MB, consider serving via a separate URL and returning that URL in a `text()` response instead.
- Cache encoded payloads if the source rarely changes.
- Use `notifyResourceUpdated()` to invalidate client caches when content changes — see `06-subscriptions.md`.
