# Response Helpers Overview

Response helpers replace manual `CallToolResult` construction. Each helper sets the right MIME type, wraps content correctly, and returns a value you can `return` directly from a handler.

```typescript
// Manual — verbose, easy to get wrong
return { content: [{ type: "text", text: "Hello" }], _meta: { mimeType: "text/plain" } };

// Helper — one call
return text("Hello");
```

## Canonical import

```typescript
import {
  MCPServer,
  text,
  markdown,
  html,
  xml,
  css,
  javascript,
  object,
  array,
  image,
  audio,
  binary,
  resource,
  error,
  mix,
  widget,
} from "mcp-use/server";
```

Always import from `mcp-use/server`. Never from `@modelcontextprotocol/sdk` — the helpers are not the same.

Version note: `mcp-use@1.26.0` exports `array()` and `resource()`, but does **not** export response helpers named `json()`, `video()`, `file()`, or `stream()`. If docs or examples disagree, verify against `dist/src/server/index.d.ts` and `dist/src/server/utils/response-helpers.d.ts` in the published package.

## Decision table

| I want to return... | Use | File |
|---|---|---|
| Plain text | `text()` | `02-text-and-markdown.md` |
| Formatted text (lists, headings) | `markdown()` | `02-text-and-markdown.md` |
| Typed structured JSON | `object()` | `03-object-and-mix.md` |
| Array of items | `array()` | `03-object-and-mix.md` |
| Both readable text and structured JSON | `mix()` | `03-object-and-mix.md` |
| HTML markup | `html()` | `04-html-css-javascript-xml.md` |
| CSS stylesheet | `css()` | `04-html-css-javascript-xml.md` |
| JavaScript code | `javascript()` | `04-html-css-javascript-xml.md` |
| XML document | `xml()` | `04-html-css-javascript-xml.md` |
| Image (chart, screenshot) | `image()` | `05-image-audio-video-binary.md` |
| Audio (speech, sound) | `audio()` | `05-image-audio-video-binary.md` |
| Arbitrary binary (PDF, zip, video bytes) | `binary()` | `05-image-audio-video-binary.md` |
| Audio file from disk | `await audio(path)` | `05-image-audio-video-binary.md` |
| Embedded resource | `resource()` | `06-stream-and-file.md` |
| Expected failure (not found, invalid input) | `error()` | `07-error-handling.md` |
| Widget (MCP Apps / ChatGPT) | `widget()` | `../18-mcp-apps/server-surface/01-widget-helper.md` |

`widget()` is documented in the MCP Apps cluster — it has registration-time wiring beyond the response surface.

## Response surfaces

Every response has up to three surfaces:

| Surface | Field | Populated by |
|---|---|---|
| Content | `content[]` | All helpers |
| Structured | `structuredContent` | `object()`, `array()`, `widget({ props })`, `mix()` |
| Meta | `_meta` | MIME helpers, `widget({ metadata })`, direct metadata |

For ordinary tool results, `object()` and `array()` intentionally populate both readable `content` and typed `structuredContent`. For widget results, the docs say `content` is the LLM-visible summary, while `structuredContent` becomes widget props and `_meta` becomes widget metadata. See `08-content-vs-structured-content.md`.

For private or bulky UI-only data, use `_meta` — see `09-meta-private-data.md`.

## Composition

Use `mix()` to combine multiple helpers into one response. It merges `content`, `structuredContent`, and `_meta`.

```typescript
return mix(
  markdown("## Report\n\nGrowth was 18%."),
  image(chartBase64, "image/png"),
  object({ revenue: [100, 118], growthRate: 0.18 }),
);
```

Composition rules: lead with the readable surface, add structured second, add binaries only when the client benefits. See `03-object-and-mix.md`.

## Cross-primitive use

Helpers work in tools, prompts, and resources. The server auto-converts to `GetPromptResult` or `ReadResourceResult`.

```typescript
server.prompt({ name: "greeting", schema: z.object({ name: z.string() }) },
  async ({ name }) => text(`Hello, ${name}!`));

server.resource({ name: "config", uri: "config://app" },
  async () => object({ version: "1.0.0" }));
```

**Canonical doc:** [manufact.com/docs/typescript/server/response-helpers](https://manufact.com/docs/typescript/server/response-helpers)
