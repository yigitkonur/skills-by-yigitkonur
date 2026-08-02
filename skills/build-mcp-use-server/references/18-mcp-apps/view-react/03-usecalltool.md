# useCallTool

*Read this when a button or form inside a view should call another server tool and display loading/error state.*

## Signature

```typescript
useCallTool<ToolName extends string>(ref?: ToolRef<ToolName>): CallToolHandle<ToolInput, ToolOutput>
useCallTool(name: string): CallToolHandle<any, any>  // Runtime, untyped
useDynamicTool<Args, Result>(name: string): CallToolHandle<Args, Result>  // Explicit schema

interface CallToolHandle<I, O> {
  callTool(args: I): Promise<CallToolSuccess<O>>;
  data: CallToolSuccess<O> | null;
  error: ToolError | null;
  isPending: boolean;
}
```

## Basic usage

Call a tool from a button or form handler:

```typescript
import { useCallTool } from "mcp-use/react";

function DetailsButton({ productId }: { productId: string }) {
  const { callTool, data, isPending, error } = useCallTool("get-product-details");

  async function handleClick() {
    try {
      await callTool({ productId });
    } catch (e) {
      // Handle thrown ToolError
    }
  }

  return (
    <div>
      <button onClick={handleClick} disabled={isPending}>
        {isPending ? "Loading..." : "View details"}
      </button>
      {error && <p>Error: {error.message}</p>}
      {data && <pre>{JSON.stringify(data, null, 2)}</pre>}
    </div>
  );
}
```

## Typed calls via ToolRef

Import the exported tool reference from your server and pass it for full TypeScript inference:

```typescript
import { searchProducts } from "@/server/tools";  // ToolRef export from server
import { useCallTool } from "mcp-use/react";

const { callTool, data, isPending } = useCallTool(searchProducts);
// data typed as { results: [...], query: string }
// callTool arg typed as { query: string }

await callTool({ query: "headphones" });
```

See `references/04-tools/02-registering-a-tool.md` for server-side `ToolRef` export.

## Combining with view state

Use `useViewState()` for selections that should be visible to the model, then call tools on user actions:

```typescript
import { useViewState, useCallTool } from "mcp-use/react";

function FilteredSearch() {
  const [filter, setFilter] = useViewState({ category: "all" });
  const { callTool, data } = useCallTool("search-products");

  return (
    <div>
      <select onChange={(e) => setFilter({ category: e.target.value })}>
        <option>All categories</option>
        <option>Audio</option>
      </select>
      <button onClick={() => callTool({ category: filter.category })}>
        Search
      </button>
      {data && <Results results={data.results} />}
    </div>
  );
}
```

## Error handling

`callTool()` rejects with `ToolError` when the server returns `isError: true`. You can catch it:

```typescript
const { callTool } = useCallTool("risky-operation");

try {
  await callTool({});
} catch (e) {
  if (e instanceof ToolError) {
    console.error("Tool failed:", e.message);
  }
}
```

Or rely on the `error` field (preferred when rendering):

```typescript
const { error } = useCallTool("search");
if (error) <p>Search failed: {error.message}</p>;
```

## Gotchas

- **Multiple calls do not queue** → each `callTool()` replaces the previous result immediately; no history
- **`data` persists across calls** → clear it manually before a new call if needed
- **No `data` on error** → `data` stays null if the call throws; check `error` instead

