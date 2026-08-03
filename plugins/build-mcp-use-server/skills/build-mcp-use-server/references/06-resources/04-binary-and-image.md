# Binary and Image Resources

*Read this when serving binary or image resource content (base64 blob results).*

## Preferred shape: raw envelope with `blob`

Return binary resource content as a native `ReadResourceResult`: a `contents` array whose entries contain a base64 `blob`. Do not use the deprecated `image()`, `audio()`, or `binary()` response helpers in new resource code.

```typescript
import { MCPServer } from "mcp-use";
import { readFile } from "node:fs/promises";

const server = new MCPServer({
  name: "media-resources",
  version: "1.0.0",
});

server.resource(
  { name: "logo", uri: "assets://logo.png", mimeType: "image/png" },
  async (uri) => {
    const png = await readFile("./public/logo.png");
    return {
      contents: [{
        uri: uri.href,
        mimeType: "image/png",
        blob: png.toString("base64"),
      }],
    };
  },
);

const invoiceFiles = new Map([
  ["sample", "./assets/invoice-sample.pdf"],
]);

server.resourceTemplate(
  {
    name: "invoice",
    uriTemplate: "invoices://{id}.pdf",
    mimeType: "application/pdf",
  },
  async (uri, { id }) => {
    const invoiceId = Array.isArray(id) ? id[0] : id;
    const path = invoiceFiles.get(invoiceId);
    if (!path) throw new Error(`Invoice not found: ${invoiceId}`);

    const pdf = await readFile(path);
    return {
      contents: [{
        uri: uri.href,
        mimeType: "application/pdf",
        blob: pdf.toString("base64"),
      }],
    };
  },
);

server.resource(
  {
    name: "notification-sound",
    uri: "assets://notification.mp3",
    mimeType: "audio/mpeg",
  },
  async (uri) => {
    const mp3 = await readFile("./assets/notification.mp3");
    return {
      contents: [{
        uri: uri.href,
        mimeType: "audio/mpeg",
        blob: mp3.toString("base64"),
      }],
    };
  },
);

await server.listen(3000);
```

## Content rules

- `blob` must be a base64 string, not a `Buffer`, `Uint8Array`, `ArrayBuffer`, or file path.
- Set `mimeType` on both the resource definition and each returned content entry.
- Set each content entry's `uri` to the URI passed to the callback (`uri.href`).
- Return `text` for textual content or `blob` for binary content; do not put base64 binary data in `text`.
- Template parameters are `string | string[]`; narrow them before lookup or file generation.

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
| `blob: buffer` | `blob: buffer.toString("base64")` |
| `text: pdfBase64` | `blob: pdfBase64` |
| `uri: "assets://logo.png"` in every callback | `uri: uri.href` |
| Returning a deprecated media helper | Returning `{ contents: [{ uri, mimeType, blob }] }` |

## Performance

- Base64 increases payload size and encoding cost. For files above roughly 5 MB, prefer a separately hosted file and return a tool `resource_link` rather than embedding it in a resource read.
- Cache encoded payloads if the source rarely changes.
- Use `server.notifyResourceUpdated(uri)` to invalidate client caches when content changes — see `06-subscriptions-listen.md`.
