# Debugging Workflow

*Read this when a tool is failing or behaving unexpectedly.*

Use a tiered approach: start with the Inspector UI, escalate to logs, then to raw curl.

## Tier 1: Inspector UI

**Best for:** Visual feedback, schema validation, quick feedback loop.

1. Open `http://localhost:3000/mcp/inspector` (runs alongside `npm run dev`)
2. Go to **Tools** tab
3. Click the failing tool
4. Fill the form — Inspector validates input against schema in real-time
5. Click **Call**
6. If error, see the error message in the **Output** panel
7. Click **Debug Panels** (if available) to inspect `props`, `output`, `state`, `metadata`

For view rendering issues, Inspector shows view debug panels (see references/23-debug/03-view-debugging.md).

## Tier 2: Server Logs

**Best for:** Missing error messages, context-dependent failures, async debugging.

Run the server with logging enabled:

```bash
npm run dev
# Watch console for logs as you call tools from Inspector
```

Log server-side diagnostics from your tool with your application logger (or `console` during local debugging). Use `ctx.sendLog()` only for non-sensitive diagnostics that should be delivered to the MCP client:

```typescript
server.tool(
  { name: "my-tool", description: "...", inputSchema: ... },
  async (args, ctx) => {
    console.info("Tool called", { args });
    await ctx.sendLog("info", { event: "tool-called" });
    try {
      const result = await expensive_operation(args);
      console.info("Operation succeeded");
      return { content: [{ type: "text", text: JSON.stringify(result) }] };
    } catch (err) {
      console.error("Operation failed", err);
      return { isError: true, content: [{ type: "text", text: "Failed" }] };
    }
  }
);
```

`ctx.sendLog()` emits a client-facing MCP notification and bypasses `logging/setLevel`; never send secrets, tokens, or private payloads through it.

Debug panels in logs:
- Check `npm run dev` output for structured logs
- Line up timestamps between Inspector **Call** and server log entry

## Tier 3: curl Handshake

**Best for:** Isolating transport-level issues, reproducible examples, CI/CD testing.

Use the exact curl commands from references/22-validate/02-curl-handshake.md. Verify:

1. **Connection**: A GET/HEAD/DELETE request to the default stateless `/mcp` endpoint returns `204 No Content`; use POST protocol calls to test the server.
2. **Protocol**: Run the modern or legacy request sequence exactly as documented; required headers differ by wire mode.
3. **tools/list**: Confirm the registration code executed against the same `MCPServer` instance serving the request.
4. **tools/call**: Exercise the tool with schema-valid sample arguments.

If curl works but Inspector fails:
- Check Inspector connection settings (should auto-connect to localhost)
- Refresh browser tab
- Check browser console (DevTools F12) for WebSocket/CORS errors

## Request State & Elicitation

For `input_required` flows, verify the shipped helper path rather than looking for `ctx.elicit()` (which does not exist in beta.66):

1. The first call returns `inputRequired({ inputRequests, requestState? })`, whose wire envelope has `resultType: "input_required"`.
2. Each form request is built with `inputRequired.elicit({ message, requestedSchema })`; URL requests use `.elicitUrl({ message, url })`.
3. On re-entry, read the response with `inputResponse(ctx.inputResponses, key)` or `acceptedContent(...)`.
4. When a request-state verifier is configured, read decoded state by calling `ctx.requestState<T>()` — the property itself is an accessor function.

See `references/12-elicitation/01-overview.md` and `references/12-elicitation/04-multi-round-and-request-state.md` for complete patterns.

## Error Categories

| Error | Meaning | Check |
| --- | --- | --- |
| `Tool not found (in tools/list)` | Tool not registered | Did registration code execute before startup against the same `MCPServer` instance? Exporting the `ToolRef` affects generated view typing, not runtime registration. |
| `Invalid params` | Input schema mismatch | Tool schema `.describe()` on every field? Arguments match schema types? |
| `isError: true in result` | Tool threw or returned error | Tool handler catch block? Returned `{ isError: true, content: [...] }`? |
| `View not found` | Tool returned view but folder missing | `views/<view-name>/view.tsx` exists? Name matches tool `view.name` field? |
| `CSP violation` | Widget frame blocked by CSP | See references/23-debug/03-view-debugging.md for CSP debugging |

## When Stuck

1. Start with Inspector (visual, fastest)
2. Add application log calls to the tool handler; use `ctx.sendLog()` only for non-sensitive client-visible diagnostics
3. Run curl to isolate to transport (see references/22-validate/02-curl-handshake.md)
4. Check `npm run dev` output for startup errors (tools not registering, view compilation failures)

If none of these uncover the issue, hand the repro to `test-by-mcpc-cli` skill for protocol-level verification.

