# `useCallTool(name)` — Type-Safe Tool Calls from Widgets

TanStack Query–style hook for calling MCP tools. Manages loading / success / error states automatically. When paired with `mcp-use dev`, it is fully type-safe via the generated `.mcp-use/tool-registry.d.ts`.

```typescript
import { useCallTool } from "mcp-use/react";

const {
  callTool, callToolAsync,
  data, error, status,
  isIdle, isPending, isSuccess, isError,
} = useCallTool("tool-name");
```

## Why this hook over `useWidget().callTool`

| Concern | `useWidget().callTool` | `useCallTool(name)` |
|---|---|---|
| Loading / error state | You manage manually | Built-in state machine |
| Type inference | Untyped `Record<string, unknown>` | Inferred from the tool registry |
| Multiple in-flight calls | Shared global state | One state slot per hook instance |
| Promise vs callbacks | Promise only | Both `callTool` (callbacks) and `callToolAsync` (promise) |

Use `useCallTool` for any non-trivial interactive widget. Reach for `useWidget().callTool` only when you need a single one-off invocation with no state to render.

## Never use raw `fetch()`

The widget runs inside an iframe with a strict CSP. `fetch("/mcp")` from inside the widget will not work — it has no access to the host's MCP transport, no auth context, no session id. `useCallTool` (and `useWidget().callTool`) are the only correct routes to call back into the server.

## Return shape

| Property | Type | When |
|---|---|---|
| `status` | `"idle" \| "pending" \| "success" \| "error"` | Always |
| `isIdle` | `boolean` | No call yet |
| `isPending` | `boolean` | Call in flight |
| `isSuccess` | `boolean` | Last call succeeded |
| `isError` | `boolean` | Last call failed |
| `data` | `CallToolResponse \| undefined` | Defined when `isSuccess` |
| `error` | `unknown \| undefined` | Defined when `isError` |
| `callTool` | `(input?, callbacks?) => void` | Fire-and-forget; input is required only when the tool schema has required keys. |
| `callToolAsync` | `(input?) => Promise<CallToolResponse>` | Promise-based; input is required only when the tool schema has required keys. |

## Result shape

```typescript
interface CallToolResponse {
  content: Array<{ type: string; text?: string; [key: string]: any }>;
  isError?: boolean;
  structuredContent?: any;            // Strongly typed when registry types exist
  result: string;                      // Joined text convenience field
  _meta?: Record<string, unknown>;
}
```

`data.structuredContent` is the typed payload — that's what your widget consumes. `data.content` is the LLM-facing text/image blocks.

## Fire-and-forget

```tsx
const { callTool, data, isPending, isError, error } = useCallTool("search-products");

callTool({ query: "shoes", limit: 20 }, {
  onSuccess: (result, input) => console.log("found", result.structuredContent),
  onError:   (err, input)   => console.error("failed", err),
  onSettled: (result, err, input) => console.log("done"),
});
```

## Async/await

```tsx
const { callToolAsync, isPending } = useCallTool("add-to-cart");

const onAdd = async (productId: string) => {
  try {
    const result = await callToolAsync({ productId, quantity: 1 });
    showToast(`Added — total ${result.structuredContent.total}`);
  } catch (err) {
    showToast("Failed to add", "error");
  }
};
```

## Multiple tools in one widget

Each hook instance owns its own state — no collisions:

```tsx
const search   = useCallTool("search-products");
const favorite = useCallTool("add-favorite");
const details  = useCallTool("get-product-details");

// search.isPending and favorite.isPending update independently.
```

## Type generation

`mcp-use dev` writes `.mcp-use/tool-registry.d.ts` automatically from your tool schemas. After it runs, `useCallTool("search-products")` gets full IntelliSense for input args and `data.structuredContent`.

For projects without `mcp-use dev`, use `generateHelpers`:

```typescript
import { generateHelpers } from "mcp-use/react";

type Tools = {
  "search-products": {
    input: { query: string; limit?: number };
    output: { results: Array<{ id: string; name: string }> };
  };
};

const { useCallTool } = generateHelpers<Tools>();
const { callTool } = useCallTool("search-products"); // typed
```

## Anti-patterns

- Calling `callTool` inside a `useEffect` with no guard → infinite loop on every render.
- Relying on `isSuccess` to mean "the next render has the data" — read `data` directly; it tracks `isSuccess`.
- Stuffing all interactive logic into a single `useCallTool` for an umbrella tool — split tools by intent so each hook tracks one operation.
