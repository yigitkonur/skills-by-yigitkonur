# View Rendering Issues

*Read this when a v2 MCP App View is absent, blank, stuck, untyped, or works only in one host.*

## Confirm the server contract first

A View-bound tool needs all of these:

1. an exported module-level `ToolRef`;
2. `outputSchema`;
3. `view: { name: "..." }`;
4. matching `structuredContent` on successful calls; and
5. `views/<name>/view.tsx` with a default React component export.

```typescript
export const searchProducts = server.tool(
  {
    name: "search-products",
    description: "Search products and render the matching list.",
    inputSchema: z.object({
      query: z.string().describe("Product search phrase"),
    }),
    outputSchema: z.object({
      results: z.array(z.object({ id: z.string(), name: z.string() })),
    }),
    view: { name: "product-search" },
  },
  async ({ query }) => ({
    content: [{ type: "text", text: `Search results for ${query}.` }],
    structuredContent: { results: await search(query) },
  }),
);
```

See `references/18-mcp-apps/server-surface/01-tool-view-field.md`.

## View is not discovered

Check the exact name and path:

```text
view.name: product-search
file: views/product-search/view.tsx
```

Do not use the v1 path `resources/<name>/widget.tsx`, `widgetMetadata`, manual `uiResource()` registration, or the `widget:` tool field. See `references/28-migration/06-v1-to-v2-widgets-to-views.md`.

## React imports fail

There is no `@mcp-use/react` package. Import from the package subpath:

```tsx
import { ThemeProvider, useToolContext } from "mcp-use/react";
```

See `references/18-mcp-apps/view-react/01-setup-and-providers.md`.

## View remains pending or reads undefined output

`useToolContext()` follows a latched lifecycle. Do not read `toolOutput` before `status === "ready"`:

```tsx
export default function ProductSearchView() {
  const ctx = useToolContext<"search-products">();

  if (ctx.status === "pending") return <p>Loading…</p>;
  if (ctx.status === "error") return <p>{ctx.error.message}</p>;

  return (
    <ThemeProvider>
      <ul>
        {ctx.toolOutput.results.map((item) => (
          <li key={item.id}>{item.name}</li>
        ))}
      </ul>
    </ThemeProvider>
  );
}
```

See `references/18-mcp-apps/view-react/02-usetoolcontext.md`.

## View type is missing or stale

Check that the server tool is exported as a const. Then run:

```bash
mcp-use typecheck
```

Do not run the removed `mcp-use generate-types` command. If a tool is genuinely runtime-generated, call it with `useDynamicTool<Args, Result>()` and explicit types. See `references/18-mcp-apps/view-react/03-usecalltool.md`.

## View shows only text

The host may not advertise MCP Apps support. Confirm with the Inspector, then check host capabilities. Keep `content` useful as a fallback for hosts that ignore the View resource.

See `references/18-mcp-apps/05-host-capability-detection.md`.

## View is blank

Open the iframe/browser console. Separate these failure classes:

| Console symptom | Likely cause | Next reference |
|---|---|---|
| `connect-src` refusal | Missing `connectDomains` origin. | `references/27-troubleshooting/05-csp-violations.md` |
| Script/style/image/font refusal | Missing `resourceDomains` origin. | `references/27-troubleshooting/05-csp-violations.md` |
| Frame refusal | Missing `frameDomains` origin. | `references/27-troubleshooting/05-csp-violations.md` |
| Module/React exception | View bundle or component error. | `references/23-debug/03-view-debugging.md` |
| `toolOutput` undefined | Lifecycle or output-schema mismatch. | `references/18-mcp-apps/view-react/02-usetoolcontext.md` |

## View works in development but not production

Check these production-only differences:

1. `mcp-use build` produced the View bundle under `.mcp-use/build/`.
2. `mcp-use start` serves that build, not the TypeScript source.
3. `MCP_URL` identifies the public MCP origin.
4. `MCP_ASSETS_URL` identifies the public assets origin when assets are external.
5. CSP contains every production API and asset origin.

See `references/18-mcp-apps/server-surface/04-assets-mcp-url-and-serving.md`.

## Host interactions fail

Hooks such as `useSendFollowUp`, `useFiles`, and display-mode requests depend on host capabilities. Detect support and render a fallback instead of assuming every host supports every interaction. See `references/18-mcp-apps/view-react/07-host-context-files-and-size.md`.

## Working v2 View pattern

```tsx
import { ModelContext, ThemeProvider, useToolContext } from "mcp-use/react";

export default function ProductSearchView() {
  const ctx = useToolContext<"search-products">();

  if (ctx.status === "pending") return <p>Loading…</p>;
  if (ctx.status === "error") return <p>{ctx.error.message}</p>;

  return (
    <ThemeProvider>
      <ModelContext content={`Showing ${ctx.toolOutput.results.length} products`}>
        <ul>
          {ctx.toolOutput.results.map((item) => (
            <li key={item.id}>{item.name}</li>
          ))}
        </ul>
      </ModelContext>
    </ThemeProvider>
  );
}
```