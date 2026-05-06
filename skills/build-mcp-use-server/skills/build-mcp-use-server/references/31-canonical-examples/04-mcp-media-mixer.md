# Canonical: `mcp-use/mcp-media-mixer`

**URL:** https://github.com/mcp-use/mcp-media-mixer
**Hosted demo:** https://wandering-breeze-nuipu.run.mcp-use.com/mcp

The response-helpers reference. A single server that exercises every content-type helper exported by `mcp-use/server` — `image`, `audio`, `binary`, `html`, `css`, `javascript`, `xml`, `markdown`, `object`, `array`, `text`, `mix`, `resource`, `error`. One tool per helper.

## Load-bearing files

| File | What to read it for |
|---|---|
| `index.ts` | Each helper used in isolation, with the smallest possible producer (e.g. SVG → image, 1 s silent WAV → audio, hand-built PDF → binary) |

## Patterns demonstrated

| Helper | Producer in the repo |
|---|---|
| `image(base64, mime)` | Hand-built SVG, base64-encoded |
| `audio(base64, mime)` | 1 s of silence at 8 kHz mono WAV |
| `binary(base64, mime)` | Minimal valid PDF (literal byte-by-byte) |
| `html(content)` | Inline HTML snippet |
| `css(content)` | Stylesheet content |
| `javascript(content)` | Script content |
| `xml(content)` | XML config sample |
| `markdown(content)` | Markdown summary |
| `object(...)`, `array(...)` | Structured content |
| `text(content)` | Plain text |
| `mix(...children)` | Multi-content response (image + caption + structured data) |
| `resource(uri, content)` | Exposing a tool result as a resource pointer |
| `error(message)` | Structured error path |

Annotations like `readOnlyHint: true` are set on every tool because nothing here mutates anything.

## Clusters this complements

- `../05-responses/` — every helper documented in detail
- `../06-resources/` — `resource(uri, content)` helper variant
- `../04-tools/` — tool annotations

## When to study this repo

- You are unsure which helper to return for a given content type.
- You need a worked example of `mix(...)` combining several helpers.
- You are returning binary content (PDF, image, audio) and want to confirm encoding and MIME wiring.
- You want to verify what `error()` looks like on the wire vs throwing.

## Local run

```bash
gh repo clone mcp-use/mcp-media-mixer
cd mcp-media-mixer
npm install
npm run dev
```
