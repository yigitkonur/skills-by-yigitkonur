# Validation Pipeline

*Read this when you need to understand when errors happen and how they surface.*

What happens between the client sending `tools/call` and your handler running.

## Pipeline

The shipped `tools/call` request handler resolves the tool, then wraps everything else in one `try`/`catch`:

```typescript
// Shape of the shipped handler (SDK internals, not user-facing API):
const tool = registeredTools[request.params.name];
if (!tool) throw new ProtocolError(InvalidParams, `Tool ${name} not found`);
if (!tool.enabled) throw new ProtocolError(InvalidParams, `Tool ${name} disabled`);
try {
  const args = await validateToolInput(tool, request.params.arguments, name); // throws on bad input
  const result = await executeToolHandler(tool, args, ctx);                  // your callback
  await validateToolOutput(tool, result, name);                              // throws on bad output
  return projectCallToolResult(result, tool.outputSchemaJson);
} catch (error) {
  return { content: [{ type: "text", text: error.message }], isError: true };
}
```

1. **Receive request.** The transport (streamable HTTP) parses the incoming JSON-RPC envelope. Malformed JSON or unknown methods are rejected as protocol errors before any tool code runs.
2. **Resolve tool by `name` and check `enabled`.** Both checks run **outside** the `try`/`catch` — a missing or disabled tool throws a genuine `ProtocolError`, which becomes a JSON-RPC-level error response. Your handler never runs.
3. **Validate input against `inputSchema`.** Runs **inside** the `try`. On failure it throws `ProtocolError(InvalidParams, "Input validation error: ...")`, which the `catch` converts into a normal `CallToolResult` with `isError: true` — not a JSON-RPC error.
4. **Run handler.** Your `async (input, ctx) => result` runs with fully typed, already-validated `input`. `ctx` (client info, auth, `sendLog`/`reportProgress`/`sendNotification`) is already built by request dispatch before this handler is invoked. Also runs **inside** the `try` — any thrown error (`Error`, custom class, anything) is caught the same way as an input-validation failure.
5. **Validate output against `outputSchema` (if set).** Runs **inside** the `try`. A schema mismatch, or a missing `structuredContent` when `outputSchema` is declared, throws `ProtocolError(InvalidParams, "Output validation error: ...")` — caught the same way.
6. **Format and emit.** On success, the raw result is projected against `outputSchemaJson` and serialized to wire format.

**The one rule that matters:** only "tool not found" and "tool disabled" become JSON-RPC protocol errors. Every failure that happens once the tool is confirmed to exist and be enabled — bad input, a thrown error in your handler, bad output — is caught and turned into a normal `CallToolResult` with `isError: true`. There is no server-side 500 path for handler throws; the SDK always converts them to a tool result the model can read and react to.

## What fails where

| Failure | Where it's thrown | Client sees |
|---|---|---|
| Malformed JSON | Transport, before dispatch | JSON-RPC parse error (`-32700`). |
| Unknown tool name | Outside the `try` | JSON-RPC error, `-32602 Invalid params`, `"Tool <name> not found"`. Handler never runs. |
| Tool disabled | Outside the `try` | JSON-RPC error, `-32602 Invalid params`, `"Tool <name> disabled"`. Handler never runs. |
| Missing required field / wrong type / unknown field on `.strict()` schema | Inside the `try` (`validateToolInput`) | `CallToolResult` with `isError: true`; `content[0].text` starts with `"Input validation error: Invalid arguments for tool <name>: ..."`. |
| Handler throws (any `Error`) | Inside the `try` (`executeToolHandler`) | `CallToolResult` with `isError: true`; `content[0].text` is `error.message` verbatim. |
| Handler returns `{ isError: true, ... }` directly | No throw — your own return value | `CallToolResult` with `isError: true`, exactly as you constructed it. |
| `outputSchema` set but `structuredContent` missing or invalid | Inside the `try` (`validateToolOutput`) | `CallToolResult` with `isError: true`; `content[0].text` starts with `"Output validation error: ..."`. |

## What the client sees on validation failure

Calling `fetch-weather` with `{ city: 42 }` when `inputSchema` is `z.object({ city: z.string().describe(...) })` returns a normal tool result, not a JSON-RPC error:

```json
{
  "content": [
    {
      "type": "text",
      "text": "Input validation error: Invalid arguments for tool fetch-weather: city: Invalid input: expected string, received number"
    }
  ],
  "isError": true
}
```

The message is a single string — the tool name plus every failing field joined by `", "` (`path: message` per issue, from the schema's `~standard.validate()` issues) — not a bulleted per-field list and not a top-level `error` object. The model reads `content[0].text` to retry with corrected arguments. Custom `.describe()` text and Zod custom error messages flow through into the issue messages, so use them to guide self-correction.

## Implications

- **Never re-validate input inside the handler.** By the time your callback runs, `args` is already validated and typed.
- **Use `.strict()` on every top-level schema.** Without it, hallucinated extra fields are accepted instead of becoming validation errors.
- **You do not need to catch your own errors for "expected failure" reporting.** A thrown `Error` and a returned `{ isError: true, content: [...] }` both reach the client as the same kind of `CallToolResult`. Prefer returning `{ isError: true, content: [...] }` directly when you can — it lets you control the exact message text instead of relying on `error.message`.
- **`outputSchema` failures are your bug, not the model's.** They mean the handler produced data that does not match its own declared contract — fix the handler, don't rely on the model to retry.
