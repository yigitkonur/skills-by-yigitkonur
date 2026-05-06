# Validation Pipeline

What happens between the client sending `tools/call` and your handler running. Knowing the order tells you where each kind of failure surfaces.

## Pipeline

1. **Receive request.** The transport (stdio, Streamable HTTP, SSE) parses the incoming JSON-RPC envelope. Malformed JSON or unknown methods are rejected here as protocol errors — your handler is never called.
2. **Resolve tool by `name`.** The server looks up the registered `ToolDefinition`. An unknown name returns `MethodNotFound` (`-32601`) without invoking any handler.
3. **Validate arguments against `schema`.** The Zod schema parses `params.arguments`. Failures emit a structured validation error; the handler does not run. The client sees a message like:
   ```
   Validation Error:
   - name: Required
   - age: Expected number, received string
   - email: Invalid email address
   ```
   This error is designed for the model to read and self-correct.
4. **Build the `ctx` object.** Client info, auth (if configured), and per-call helpers (`log`, `elicit`, `sample`) are wired up. Session helpers and `reportProgress` are present only when the request/session provides the needed metadata.
5. **Run the handler.** Your `async (args, ctx) => result` runs. `args` is fully typed and trusted at this point — defaults applied, optional fields normalized.
6. **Format and emit.** Response helpers (`text`, `object`, `mix`, etc.) ensure the wire shape is correct: `content[]`, optional `structuredContent`, optional `_meta`, `isError` flag. The transport serializes and sends.

## What fails where

| Failure | Caught at step | Client sees |
|---|---|---|
| Malformed JSON | 1 | JSON-RPC parse error. |
| Unknown tool name | 2 | `MethodNotFound`. |
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
- **Use `error()` for expected failures.** Step 5 throws become 500s; `error()` keeps the response shape intact (see `05-responses/07-error-handling.md`).
- **Test structured output yourself.** `mcp-use@1.26.0` accepts `outputSchema` in `ToolDefinition`, but the runtime does not forward it into SDK tool registration or validate handler output.
