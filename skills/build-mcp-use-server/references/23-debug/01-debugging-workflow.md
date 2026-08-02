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

For view rendering issues, Inspector shows widget debug panels (see references/23-debug/03-view-debugging.md).

## Tier 2: Server Logs

**Best for:** Missing error messages, context-dependent failures, async debugging.

Run the server with logging enabled:

```bash
npm run dev
# Watch console for logs as you call tools from Inspector
```

Log from your tool:

```typescript
server.tool(
  { name: "my-tool", description: "...", inputSchema: ... },
  async (args, ctx) => {
    ctx.log("info", "Tool called", { args });
    try {
      const result = await expensive_operation(args);
      ctx.log("info", "Operation succeeded", { result });
      return { content: [{ type: "text", text: JSON.stringify(result) }] };
    } catch (err) {
      ctx.log("error", "Operation failed", { error: err instanceof Error ? err.message : String(err) });
      return { isError: true, content: [{ type: "text", text: "Failed" }] };
    }
  }
);
```

Debug panels in logs:
- Check `npm run dev` output for structured logs
- Line up timestamps between Inspector **Call** and server log entry

## Tier 3: curl Handshake

**Best for:** Isolating transport-level issues, reproducible examples, CI/CD testing.

Use the exact curl commands from references/22-validate/02-curl-handshake.md. Verify:

1. **Connection**: `curl http://localhost:3000/mcp` returns `404` or `405`? Server not at that URL.
2. **Initialize**: First curl tests protocol handshake. Error in initialize means schema/config issue.
3. **tools/list**: Second curl lists registered tools. Missing tool? Not exported as `const`.
4. **tools/call**: Third curl exercises the tool with sample args.

If curl works but Inspector fails:
- Check Inspector connection settings (should auto-connect to localhost)
- Refresh browser tab
- Check browser console (DevTools F12) for WebSocket/CORS errors

## Request State & Elicitation

For tools that use `ctx.elicit()` (input_required flow):

1. Tool returns `{ isError: false, content: [...], input_required: { ... } }`
2. Client sends back `requestState` (echoed by tool handler)
3. Verify `requestState` is not corrupted across rounds:
   ```typescript
   const state = ctx.requestState;  // Verify codec if configured
   // Use state to track user interactions across elicit rounds
   ```

See references/12-elicitation/ for full patterns.

## Error Categories

| Error | Meaning | Check |
| --- | --- | --- |
| `Tool not found (in tools/list)` | Tool not registered | Export as `const` from index.ts? Registered with `server.tool()`? |
| `Invalid params` | Input schema mismatch | Tool schema `.describe()` on every field? Arguments match schema types? |
| `isError: true in result` | Tool threw or returned error | Tool handler catch block? Returned `{ isError: true, content: [...] }`? |
| `View not found` | Tool returned view but folder missing | `resources/<view-name>/view.tsx` exists? Name matches tool `widget.name` field? |
| `CSP violation` | Widget frame blocked by CSP | See references/23-debug/03-view-debugging.md for CSP debugging |

## When Stuck

1. Start with Inspector (visual, fastest)
2. Add `ctx.log()` calls to tool handler
3. Run curl to isolate to transport (see references/22-validate/02-curl-handshake.md)
4. Check `npm run dev` output for startup errors (tools not registering, view compilation failures)

If none of these uncover the issue, hand the repro to `test-by-mcpc-cli` skill for protocol-level verification.

