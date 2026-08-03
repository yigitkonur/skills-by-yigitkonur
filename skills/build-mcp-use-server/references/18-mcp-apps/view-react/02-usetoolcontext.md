# useToolContext

*Read this when you need to render the tool result in a view, or handle pending/error states while complete or partial tool input arrives.*

## Signature

```typescript
useToolContext<Name extends keyof RegisteredTools = never>(): ToolContextHandle<Name>

// Discriminated union — narrow on `status` before reading branch-specific fields.
type ToolContextHandle<Name> =
  | { status: "pending"; toolInput: DeepPartial<ToolInput> | undefined; toolOutput: undefined; content: undefined; meta: undefined }
  | { status: "ready"; toolInput: ToolInput | undefined; toolOutput: ToolOutput; content: ContentBlock[] | undefined; meta: Record<string, unknown> | undefined }
  | { status: "error"; toolInput: ToolInput | undefined; toolOutput: undefined; content: ContentBlock[] | undefined; meta: Record<string, unknown> | undefined; error: ToolContextError }
```

`ToolContextError` is the public alias of `ToolError` used by the error branch. Narrow on `status` before reading `error`, `toolOutput`, `content`, or `meta`.

## Result fields

- `toolOutput` is the terminal result's typed `structuredContent`.
- `content` is the terminal result's content-block array, when supplied.
- `meta` is the delivered result `_meta`, available only after a terminal success or error.

A handler may put arbitrary View-only data in `_meta`; it is not validated by `outputSchema` and does not enter model context. For a successful View-bound result, however, the delivered object is not necessarily identical to the handler's original `_meta`: mcp-use merges in the framework-owned View link keys:

```typescript
{
  ui: { resourceUri: "ui://views/<name>.html" },
  "ui/resourceUri": "ui://views/<name>.html"
}
```

Those resource-URI keys let the host associate the result with its View. Other UI configuration belongs elsewhere: tool visibility is advertised on the `tools/list` descriptor, while CSP, permissions, domain, and border preference are emitted on the View resource metadata. Do not expect those fields in `ctx.meta`.

## Lifecycle: pending → ready/error

The hook represents one rendering invocation for the lifetime of the mounted View:

1. It starts as `pending`.
2. Every complete `ontoolinput` or partial `ontoolinputpartial` notification received while pending replaces the current `toolInput` snapshot.
3. Each changed pending snapshot emits to the hook subscription, so the component rerenders with the latest partial input.
4. The first result with `structuredContent` becomes `ready`; the first result with `isError: true` becomes `error`.
5. That first terminal success or error is latched. Later input, result, error, or cancellation notifications do not overwrite it.

Content-only non-error results are ignored while pending because the protocol notifications do not include a tool name or request ID that would let the runtime correlate ambient tool activity. A cancellation notification also leaves this public context pending.

```typescript
import { useToolContext } from "mcp-use/react";

function ProductResults() {
  const ctx = useToolContext<"search-products">();

  if (ctx.status === "pending") {
    return <p>Searching for {ctx.toolInput?.query ?? "…"}</p>;
  }

  if (ctx.status === "error") {
    return <p>Error: {ctx.error.message}</p>;
  }

  return (
    <ul>
      {ctx.toolOutput.results.map((result) => (
        <li key={result.id}>{result.name}</li>
      ))}
    </ul>
  );
}
```

`useToolContext()` does not call tools. It only reads the invocation that caused the host to render this View. Use `useCallTool()` when the mounted View must initiate another server-tool call.

## Progressive input

Pending input is `DeepPartial<ToolInput>` because fields may be absent while the host progressively supplies arguments. Treat it as provisional display state: render previews, skeleton labels, or disabled controls, but do not perform irreversible actions from it.

```typescript
import { useToolContext } from "mcp-use/react";

function CheckoutPreview() {
  const ctx = useToolContext<"checkout">();

  if (ctx.status === "pending") {
    return (
      <section aria-busy="true">
        <p>Recipient: {ctx.toolInput?.recipient?.name ?? "Waiting…"}</p>
        <p>Address: {ctx.toolInput?.shippingAddress ?? "Waiting…"}</p>
      </section>
    );
  }

  if (ctx.status === "error") {
    return <p>Checkout failed: {ctx.error.message}</p>;
  }

  return <p>Order placed: {ctx.toolOutput.orderId}</p>;
}
```

Do not describe an `input_required` elicitation round as re-entering this same mounted View. The shipped runtime has no request correlation and latches the first terminal result/error; it does not establish a same-iframe multi-round elicitation lifecycle. Keep server elicitation design in `references/12-elicitation/04-multi-round-and-request-state.md`, and treat any host remount or later invocation as a separate host-managed lifecycle unless verified end to end.

## Typed tool names

Type the hook with an exported, registered tool name to get input/output inference:

```typescript
const ctx = useToolContext<"search-products">();
// pending toolInput: DeepPartial<{ query: string }> | undefined
// ready toolInput: { query: string } | undefined
// ready toolOutput: the tool outputSchema type
```

Once `mcp-env.d.ts` augments the exported `Register` interface, `RegisteredTools` becomes the strict map of exported server-tool names to their input and output types. Before any augmentation, its fallback is `Record<string, { input: Record<string, unknown>; output: unknown }>`, so non-scaffolded projects keep compiling. Generated registration declarations are the normal path; manually augment `Register` only in custom build setups that do not generate `mcp-env.d.ts`.

The type parameter is then constrained to `keyof RegisteredTools`. An unregistered or runtime-only name is a compile error. Unlike `useCallTool()`, `useToolContext()` has no dynamic-name variant; omit the type parameter and manually narrow `unknown` fields when static registration cannot describe the rendering tool.

## Gotchas

- **Pending partial input does rerender** → complete and partial input notifications replace the pending snapshot and emit when its reference changes.
- **Pending input is provisional** → `DeepPartial` means nested fields may be absent; never treat it as validated final input.
- **Ready input remains optional** → a terminal result can arrive before a complete input snapshot.
- **First terminal result wins** → the first structured success or tool error is latched for the mounted View's lifetime.
- **Content-only success is not terminal** → without `structuredContent` or `isError: true`, the runtime leaves the context pending.
- **Cancellation has no public branch** → an uncorrelated cancellation leaves the context pending.
