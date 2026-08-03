# useViewTool

*Read this when the model or host should be able to act directly on a mounted view — highlighting an item, toggling a filter, or driving any UI state the view already owns.*

`useCallTool()` lets the View call the server. `useViewTool()` is the inverse: it lets the host or model call the mounted View.

## Signature

```typescript
useViewTool<const TDef extends ViewToolDefinition>(
  definition: TDef,
  handler: (
    args: InferToolInput<TDef>
  ) => Exclude<ToolResult<InferToolOutput<TDef>>, InputRequiredResult>
      | Promise<Exclude<ToolResult<InferToolOutput<TDef>>, InputRequiredResult>>
): void

type ViewToolDefinition = Pick<
  ToolDefinition,
  "name" | "title" | "description" | "inputSchema" | "schema" | "outputSchema" | "annotations"
> & {
  /** When `false`, the tool stays registered but is not listed or callable. @defaultValue true */
  enabled?: boolean;
};
```

`ViewToolDefinition` is the same shape as a server `ToolDefinition` (see `references/04-tools/02-registering-a-tool.md`) minus `_meta`, `visibility`, and `view` — a view tool cannot bind another view or set framework-owned metadata. `schema` is accepted as an alias for `inputSchema`, same as server tools.

## Basic usage

Register an ephemeral tool that mutates local React state while the component is mounted:

```typescript
import { useViewTool } from "mcp-use/react";
import { useState } from "react";
import { z } from "zod";

function FruitResults() {
  const [selectedFruit, setSelectedFruit] = useState<string>();

  useViewTool(
    {
      name: "highlight-fruit",
      description: "Highlight a fruit in the current results",
      inputSchema: z.object({ fruit: z.string() }),
    },
    async ({ fruit }) => {
      setSelectedFruit(fruit);
      return {
        content: [{ type: "text", text: `Highlighted ${fruit}` }],
      };
    }
  );

  return (
    <p>{selectedFruit === undefined ? "No fruit selected" : `Selected: ${selectedFruit}`}</p>
  );
}
```

The handler closes over current React state via a ref internally — it always sees the latest `selectedFruit` setter, not a stale one from the render that first registered the tool.

## Registration and cleanup semantics

- **Keyed by `name` only.** The effect dependency is `[runtime, name]` — changing `inputSchema` or `outputSchema` without changing `name` does **not** re-register. Ext-apps fixes the callback arity at registration time, so a schema change on the same name is a no-op; register under a new `name` to change a tool's schema.
- **Registers on mount, removes on unmount.** Cleanup captures the specific registration handle inside the effect, so an older cleanup can never remove a newer registration after a rapid `name` change.
- **`title`, `description`, `annotations` update in place** via the registration handle's `update()` when those values change between renders — no re-registration needed.
- **`enabled` toggles without re-registering.** Setting `enabled: false` calls the handle's `disable()`; the tool stays registered internally but is not listed or callable until re-enabled. Default is `true`.
- **The handler cannot return `InputRequiredResult`.** View tools are excluded from the elicitation `input_required` flow — the return type is `Exclude<ToolResult<TOutput>, InputRequiredResult>`.
- **Registration failures are logged, not thrown.** If the runtime's `registerViewTool` call fails, `useViewTool` logs `[mcp-use] useViewTool failed to register tool "<name>":` via `console.error` and leaves no half-registered state; it does not throw into the render.

## Gotchas

- **Not a replacement for `useCallTool`** → `useViewTool` exposes an action *to* the host/model; `useCallTool` calls *out to* the server. Most interactive views use both: `useCallTool` to fetch/mutate server data, `useViewTool` to let the model drive the already-rendered UI.
- **Two components cannot register the same tool name safely** → since registration is keyed by name only, mounting two `useViewTool` calls with the same `name` in the same view races on registration/cleanup. Use distinct names per mounted instance.
- **Schema changes require a new name** → rename the tool (e.g. `highlight-fruit-v2`) instead of expecting a schema edit to take effect on re-render.
- **No server-side registration** → a view tool exists only while its component is mounted in the guest iframe; it never appears in the server's own `tools/list` and cannot be called via `useCallTool`/`useDynamicTool` from a *different* view.

Cross-reference `references/18-mcp-apps/view-react/03-usecalltool.md` for the outbound direction (View → server tool).
