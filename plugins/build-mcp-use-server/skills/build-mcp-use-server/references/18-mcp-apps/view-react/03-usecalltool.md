# useCallTool

*Read this when a button or form inside a View should call another server tool and display its full result, loading state, or error.*

## Signature

```typescript
useCallTool<R extends ToolRef<string, unknown, unknown>>(ref: R): CallToolHandle<RefInput<R>, RefOutput<R>>
useCallTool<const Name extends string>(name: Name): CallToolHandle<RegisteredToolInput<Name>, RegisteredToolOutput<Name>>
useDynamicTool<Args extends Record<string, unknown>, Result = unknown>(name: string): CallToolHandle<Args, Result>

interface CallToolHandle<I, O> {
  callTool(args: I): Promise<CallToolSuccess<O>>;
  data: CallToolSuccess<O> | undefined;
  error: Error | undefined;
  isPending: boolean;
}
```

`CallToolSuccess<O>` is the complete successful `CallToolResult`, not just `O`. For a tool with an `outputSchema`, read the typed payload from `result.structuredContent` or `data.structuredContent`. The full result may also include `content`, `_meta`, and other standard result fields. Tool results with `isError: true` reject instead of becoming `data`.

Calling server tools requires the host's standard `serverTools` capability. Missing capability, transport, and RPC failures reject with `Error`.

## Basic usage

```typescript
import { useCallTool } from "mcp-use/react";

function DetailsButton({ productId }: { productId: string }) {
  const details = useCallTool("get-product-details");

  return (
    <div>
      <button
        type="button"
        disabled={details.isPending}
        onClick={() => void details.callTool({ productId })}
      >
        {details.isPending ? "Loading…" : "View details"}
      </button>

      {details.error && <p>Error: {details.error.message}</p>}
      {details.data && (
        <h2>{details.data.structuredContent.product.name}</h2>
      )}
    </div>
  );
}
```

For imperative code, use the resolved full result explicitly:

```typescript
const result = await details.callTool({ productId });
console.log(result.structuredContent.product);
console.log(result.content);
console.log(result._meta);
```

## Typed calls via ToolRef

Pass an exported `ToolRef` for direct input/output inference:

```typescript
import { useCallTool } from "mcp-use/react";
import { searchProducts } from "@/server/tools";

function SearchButton() {
  const search = useCallTool(searchProducts);

  async function runSearch() {
    const result = await search.callTool({ query: "headphones" });
    console.log(result.structuredContent.results);
  }

  return (
    <button type="button" onClick={() => void runSearch()}>
      Search
    </button>
  );
}
```

See `references/04-tools/02-registering-a-tool.md` for exporting the `ToolRef` returned by `server.tool()`.

## Combining with View state

Use `useViewState()` for selections that should be visible to the model, then call the tool from a user action:

```typescript
import { useCallTool, useViewState } from "mcp-use/react";

function FilteredSearch() {
  const [filter, setFilter] = useViewState({ category: "all" });
  const search = useCallTool("search-products");

  return (
    <div>
      <select
        value={filter.category}
        onChange={(event) => setFilter({ category: event.target.value })}
      >
        <option value="all">All categories</option>
        <option value="audio">Audio</option>
      </select>

      <button
        type="button"
        onClick={() => void search.callTool({ category: filter.category })}
      >
        Search
      </button>

      {search.data && (
        <Results results={search.data.structuredContent.results} />
      )}
    </div>
  );
}
```

## Dynamic registrations

Prefer `useCallTool()` for statically exported tools. Use `useDynamicTool()` only when a tool name comes from runtime configuration, a loop, or an OpenAPI-generated registration that cannot appear in `mcp-env.d.ts`. The caller supplies the contract, so TypeScript cannot verify it against the server:

```typescript
import { useDynamicTool } from "mcp-use/react";

type LookupInput = { id: string };
type LookupOutput = { value: string };

function RuntimeLookup({ toolName, id }: { toolName: string; id: string }) {
  const lookup = useDynamicTool<LookupInput, LookupOutput>(toolName);

  return (
    <button
      type="button"
      onClick={() => void lookup.callTool({ id })}
    >
      {lookup.data?.structuredContent.value ?? "Look up"}
    </button>
  );
}
```

## Tool errors and result text

`callTool()` rejects with `ToolError` when the server returns a result with `isError: true`. `ToolError.result` preserves that full delivered result. Its `message` is derived from the result's text content, or falls back to `"Tool returned an error."`.

```typescript
import { ToolError, toolResultText, useCallTool } from "mcp-use/react";

function RiskyOperation() {
  const operation = useCallTool("risky-operation");

  async function run() {
    try {
      await operation.callTool({});
    } catch (error) {
      if (error instanceof ToolError) {
        const text = toolResultText(error.result) ?? error.message;
        console.error("Tool failed:", text, error.result._meta);
        return;
      }
      console.error("Transport or protocol failure:", error);
    }
  }

  return <button onClick={() => void run()}>Run</button>;
}
```

`toolResultText(result)` is a public helper for successes and errors. It joins all `content` blocks with `type: "text"`, trims the result, and returns `undefined` when no non-empty text exists:

```typescript
import { toolResultText, useCallTool } from "mcp-use/react";

function CompletionMessage() {
  const operation = useCallTool("read-operation-status");

  async function readMessage() {
    const result = await operation.callTool({});
    return toolResultText(result) ?? "Operation completed.";
  }

  return <button onClick={() => void readMessage()}>Read status</button>;
}
```

For state-driven React rendering, the handle's `error` field is usually simpler:

```typescript
function SearchStatus() {
  const search = useCallTool("search");
  return search.error ? <p>Search failed: {search.error.message}</p> : null;
}
```

## Gotchas

- **`data` is the full success result** → read typed output at `data.structuredContent`, not `data` itself.
- **Schema-less tools may be content-only** → `structuredContent` is guaranteed and typed only when the tool declares an `outputSchema`.
- **Overlapping calls do not queue** → only the latest call updates `data`, `error`, and `isPending`; each returned promise still settles independently.
- **`data` persists across calls** → the last successful result remains while a newer call is pending or fails.
- **`error` clears on the next call** → it may be a `ToolError` or a transport/RPC/capability `Error`.
- **Unregistered literal names fail at compile time** → after `mcp-env.d.ts` registers tools, use an exported name/`ToolRef`; reserve `useDynamicTool()` for genuinely runtime-only contracts.

`useCallTool()` is the outbound direction: View → server tool. For host/model → mounted View tools, see `references/18-mcp-apps/view-react/09-useviewtool.md`.
