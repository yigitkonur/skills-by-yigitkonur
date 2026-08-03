# Response envelopes: decision table

*Read this when returning a result from a tool, resource, or prompt callback.*

v2 requires **raw MCP envelopes**. Choose by your output:

| You want to return | Envelope type | Shape | File |
|---|---|---|---|
| **Text (default fallback)** | `CallToolResult` | `{ content: [{ type: "text", text: "..." }] }` | `02-text-and-content-blocks.md` |
| **Structured data (with schema)** | `CallToolResult` | `{ content: [...], structuredContent: data }` | `03-structured-content-and-output-schema.md` |
| **Markdown / formatted text** | `CallToolResult` | `{ content: [{ type: "text", text: "# Title\n..." }] }` | `02-text-and-content-blocks.md` |
| **Error (validation/runtime)** | `CallToolResult` | `{ isError: true, content: [{ type: "text", text: "..." }] }` | `05-error-handling.md` |
| **Image (PNG/JPEG)** | `CallToolResult` | `{ content: [{ type: "image", data: "base64...", mimeType: "image/png" }] }` | `04-images-audio-binary-resources.md` |
| **Audio (MP3/WAV)** | `CallToolResult` | `{ content: [{ type: "audio", data: "base64...", mimeType: "audio/mpeg" }] }` | `04-images-audio-binary-resources.md` |
| **Binary (PDF/ZIP/video)** | `CallToolResult` | `{ content: [{ type: "resource", resource: { uri, mimeType: "application/pdf", blob: "base64..." } }] }` | `04-images-audio-binary-resources.md` |
| **Resource link (reference only, no embedded bytes)** | `CallToolResult` | `{ content: [{ type: "resource_link", uri, name, mimeType? }] }` | `04-images-audio-binary-resources.md` |
| **HTML (MCP App view)** | `CallToolResult` | `{ content: [{ type: "text", text: "..." }], structuredContent: props }` (no `mimeType` field on text blocks) | `03-structured-content-and-output-schema.md` |
| **Multiple blocks (mixed)** | `CallToolResult` | `{ content: [{ type: "text", ... }, { type: "image", ... }], ... }` | `02-text-and-content-blocks.md` |
| **Input required (re-run)** | `InputRequiredResult` | `{ resultType: "input_required", inputRequests?: { [key]: InputRequest }, requestState?: string }` | (See 12-elicitation) |
| **Resource read** | `ReadResourceResult` | `{ contents: [{ uri: "...", mimeType: "...", text?: "...", blob?: "base64..." }] }` (`blob` is a base64 string, not `Uint8Array`) | `04-images-audio-binary-resources.md` |
| **Prompt messages** | `GetPromptResult` | `{ messages: [{ role: "user" \| "assistant", content: ContentBlock }] }` (`content` is one block, not an array) | (See 07-prompts) |
| **Private UI-only data** | `CallToolResult` | `{ content: [...], _meta: { uiOnly: true, data: ... } }` | `06-meta-and-private-data.md` |

**Default:** `{ content: [{ type: "text", text: JSON.stringify(data) }], structuredContent: data }` works for most cases.
