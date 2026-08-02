# Validation Pipeline

*Read this when you need to understand when errors happen and how they surface.*

What happens between the client sending `tools/call` and your handler running.

## Pipeline

1. **Receive request.** The transport (streamable HTTP) parses the incoming JSON-RPC envelope. Malformed JSON or unknown methods are rejected as protocol errors — your handler never runs.
2. **Resolve tool by `name`.** The server looks up the registered `ToolDefinition`. Unknown tool name → error response (MCP spec allows either tool-not-found error or parameter error).
3. **Validate input against `inputSchema`.** SDK uses Zod (or Standard Schema v1) to parse and validate `params.arguments`. Failures emit a structured validation error before the handler runs.
4. **Build `ctx` object.** Client info, auth (if OAuth configured), and per-request helpers (`sendLog`, `reportProgress`, `sendNotification`) are wired.
5. **Run handler.** Your `async (input, ctx) => result` runs. `input` is fully typed and trusted — defaults applied, optional fields normalized.
6. **Validate output against `outputSchema` (if set).** SDK validates `structuredContent` against the schema. Mismatch → error response.
7. **Format and emit.** Raw result shape gets serialized to wire format and sent via transport.

## What fails where

| Failure | Caught at step | Client sees |
|---|---|---|
| Malformed JSON | 1 | JSON-RPC parse error. |
| Unknown tool name | 2 | `CallToolResult` with `isError: true` (preferred) or JSON-RPC `-32602 Invalid params`. |
| Missing required field | 3 | Structured validation error per field. |
| Wrong type | 3 | Structured validation error per field. |
| Unknown field on a `.strict()` schema | 3 | Structured validation error. |
| Handler throws | 5 | Server error (500). Use `error()` for expected failures instead. |
| `error()` returned | 6 | `CallToolResult` with `isError: true`. Model can self-correct. |

## What the client sees on validation failure

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32602,
    "message": "Invalid params: Validation Error:\n- name: Required\n- age: Expected number, received string"
  }
}
```

The model uses this to retry with corrected arguments. Custom `.describe()` text and Zod custom error messages flow through, so use them to guide self-correction.

## Implications

- **Never re-validate input inside the handler.** By step 5, `args` is already validated and typed.
- **Use `.strict()` on every top-level schema.** Without it, hallucinated extra fields are accepted instead of becoming validation errors.
- **Use explicit error envelopes for expected failures.** Step 5 throws become transport/server errors; return `{ isError: true, content: [...] }` to report a graceful tool failure (see `../05-responses/05-error-handling.md`).
- **Test structured output yourself.** `outputSchema` validates `structuredContent` at runtime in v2 when set on a tool definition.
