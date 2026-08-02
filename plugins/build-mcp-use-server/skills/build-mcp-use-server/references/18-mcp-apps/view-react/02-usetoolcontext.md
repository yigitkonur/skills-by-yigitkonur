# useToolContext

*Read this when you need to render the tool result in a view, or handle pending/error states during tool execution and streaming partial inputs.*

## Signature

```typescript
useToolContext<ToolName extends string>(): ToolContextHandle<ToolName>

interface ToolContextHandle<N extends string> {
  status: "pending" | "ready" | "error";
  toolInput: ToolInput;                        // Partial during input_required streaming
  toolOutput: ToolOutput;                      // From structuredContent; typed by outputSchema
  content: ContentBlock[];                     // Text/image/etc.; typed by result schema
  meta: { ui?: { visibility, csp, ... } };    // View metadata (CSP, permissions, display hints)
  error: ToolError | null;                     // When status === "error"
}
```

## Lifecycle: pending → ready/error

The hook tracks a single latched tool invocation. `status` follows the request lifecycle:

- **pending** → tool executing on server (or streaming partial input)
- **ready** → result arrived; `toolOutput` + `content` populated
- **error** → server returned `isError: true` or threw; `error` field set

**Minimal render:**
```typescript
const ctx = useToolContext<"search-products">();

if (ctx.status === "pending") {
  return <p>Loading results...</p>;
}
if (ctx.status === "error") {
  return <p>Error: {ctx.error?.message}</p>;
}

return (
  <ul>
    {ctx.toolOutput.results.map((r) => (
      <li key={r.id}>{r.name}</li>
    ))}
  </ul>
);
```

`useToolContext` is **NOT** a hook for calling tools (see `useCallTool` for that). It only reads the result of the view's own tool invocation.

## Streaming and partial input

When the server returns `input_required` (asking the user to fill a form), the hook emits a pending lifecycle with **partial `toolInput`** containing the values collected so far.

**Streaming story** (replaces v1 "streaming tool props"):

1. View renders with partial input from streaming `useToolContext()` result
2. Form fields bind to the model-visible `useViewState()` (which the model can populate via follow-up messages)
3. Server re-runs handler with `ctx.inputResponses` and collects final input
4. Hook updates to `ready` with complete input and output

**Example:**
```typescript
const ctx = useToolContext<"checkout">();

if (ctx.status === "pending") {
  // During input_required round: toolInput contains partial data
  return (
    <form>
      <input
        value={ctx.toolInput?.address || ""}
        placeholder="Address"
        // Form updates useViewState, which model can populate
      />
      <p>Waiting for user...</p>
    </form>
  );
}

return <p>Order placed: {ctx.toolOutput.orderId}</p>;
```

The key difference from v1: **no ephemeral streaming state**. Model-visible choices live in `useViewState()`, partial server state flows through `toolInput`. This keeps the model informed on every re-entry.

Cross-reference `references/04-tools/05-the-ctx-object.md` for `ctx.inputResponses` server-side and `references/12-elicitation/04-multi-round-and-request-state.md` for the full protocol.

## Typed queries

Type the hook with the tool name to get full TypeScript inference:

```typescript
const ctx = useToolContext<"search-products">();
// ctx.toolOutput typed as { results: [...], query: string }
// ctx.toolInput typed as { query: string }
```

For runtime-only tools without prior definition, pass `unknown` and assert manually.

## Gotchas

- **No re-render on partial input update during streaming** → use `useViewState()` instead for reactive form bindings
- **`error` may be null even when `status === "error"`** → check status first; only then use `error.message`
- **State persists across re-runs** → clearing the view's iframe resets `useToolContext()` to initial pending state

