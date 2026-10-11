# Views (MCP Apps)

*Authoritative guide for interactive React Views in mcp-use v2.*

Official documentation:
- [MCP Apps Overview](https://docs.mcp-use.com/v2/typescript/mcp-apps)
- [MCP Apps Quickstart](https://docs.mcp-use.com/v2/typescript/mcp-apps/quickstart)
- [Interactivity](https://docs.mcp-use.com/v2/typescript/mcp-apps/interactivity)
- [Generative UI](https://docs.mcp-use.com/v2/typescript/mcp-apps/generative-ui)
- [Model Context](https://docs.mcp-use.com/v2/typescript/mcp-apps/model-context)
- [Content Security Policy](https://docs.mcp-use.com/v2/typescript/mcp-apps/content-security-policy)

---

## 1. Bind a View

Create `views/<name>/view.tsx`. Export the rendering tool ref, declare its `outputSchema`, bind `view: { name }`, and return matching `structuredContent`. The directory name and `view.name` must match exactly.

```tsx
// Server tool definition in server entry
export const showProduct = server.tool(
  {
    name: "show-product",
    inputSchema: z.object({ sku: z.string() }),
    outputSchema: z.object({ sku: z.string(), title: z.string(), price: z.number() }),
    view: {
      name: "product-card", // points to views/product-card/view.tsx
    },
  },
  async ({ sku }) => {
    const data = { sku, title: "Precision Screwdriver", price: 29.99 };
    return {
      content: [{ type: "text", text: `Product ${data.title} ($${data.price})` }],
      structuredContent: data,
      _meta: { privateId: "internal_101" }, // View-only, hidden from model
    };
  }
);
```

---

## 2. Read the Rendering Call (`useToolContext`)

Destructure `useToolContext<"tool-name">()` and narrow its discriminated lifecycle before reading `toolOutput`:

```tsx
import { useToolContext, ToolCancelledError, type ViewConfig } from "mcp-use/react";

export const viewConfig = {
  autoResize: true,
  displayModes: ["inline", "fullscreen"],
  preferredDisplayMode: "inline",
} satisfies ViewConfig;

export default function ProductCard() {
  const { status, toolInput, toolOutput, error, meta } =
    useToolContext<"show-product">();

  if (status === "pending") {
    return <div className="p-4 text-secondary">Loading SKU {toolInput?.sku}…</div>;
  }

  if (status === "error") {
    if (error instanceof ToolCancelledError) {
      return <div className="p-4 text-secondary">Action was cancelled by host ({error.reason}).</div>;
    }
    return <div className="p-4 text-danger">Error: {error.message}</div>;
  }

  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold">{toolOutput.title}</h2>
      <p className="text-secondary">${toolOutput.price.toFixed(2)}</p>
    </div>
  );
}
```

---

## 3. Interaction Channels (`mcp-use/react`)

- `useCallTool("tool-name")`: Call an exported server tool with compiler-inferred argument and output types.
- `useDynamicTool`: Call a runtime-generated tool when no static ref exists.
- `useSendFollowUp`: Request a new model turn in the conversation.
- `useOpenExternal`: Ask the host to open a URL outside the sandbox.
- `useDisplayMode`: Inspect and request presentation mode (`inline`, `fullscreen`, `pip`).
- `useViewTool`: Expose a temporary client-side action that operates on the mounted UI.
- `useFiles`: Access host file capabilities after verifying support.
- `useDeepLink`: Read incoming ChatGPT deep-link URL.

Guard host actions with `useHostContext()` capability signals before calling optional host features.

---

## 4. State & Model Context

- **React Local State**: Use standard React state (`useState`, `useReducer`) for ephemeral UI details the model does not need.
- **Shared View State (`useViewState`)**: Use `useViewState(defaultObject)` for JSON-serializable selections, filters, or form drafts that future model turns should observe.
- **Declarative Model Context (`<ModelContext>`)**: Use `<ModelContext content="...">` to describe currently visible UI declaratively.
- **Durable Business State**: Always store orders, customer data, and records in an external database.

---

## 5. Content Security Policy (`view.csp`)

Declare required external origins in `view.csp`:
```ts
view: {
  name: "dashboard",
  csp: {
    connectDomains: ["https://api.example.com"],
    resourceDomains: ["https://cdn.example.com"],
    frameDomains: ["https://maps.example.com"],
  },
}
```
- `connectDomains`: Domains for `fetch`, `EventSource`, and `WebSocket`.
- `resourceDomains`: Domains for scripts, stylesheets, images, fonts, and media.
- `frameDomains`: Domains for embedded iframes.
