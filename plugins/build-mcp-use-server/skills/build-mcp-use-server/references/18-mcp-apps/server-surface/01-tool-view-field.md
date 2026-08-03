# The Tool `view` Field

*Read this when binding one server tool to one MCP Apps View.*

A v2 View is declared on the tool definition. From that binding, the framework derives the `ui://` resource, discovery metadata, successful-result link metadata, and resource security metadata.

## Shape

```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({ name: "catalog", version: "1.0.0" });

const productResultsSchema = z.object({
  query: z.string(),
  results: z.array(z.object({ id: z.string(), name: z.string() })),
});

server.tool(
  {
    name: "search-products",
    description: "Search the product catalog.",
    inputSchema: z.object({ query: z.string().describe("Search text") }),
    outputSchema: productResultsSchema,
    view: {
      name: "product-search",
      description: "Product results grid",
      csp: { connectDomains: ["https://api.example.com"] },
      permissions: {},
      domain: "views.example.com",
      prefersBorder: true,
    },
  },
  async ({ query }) => {
    const results = await search(query);
    return {
      content: [{ type: "text", text: `Found ${results.length} products.` }],
      structuredContent: { query, results },
    };
  }
);

export default server;
```

## Field Semantics

| Field | Meaning |
|-|-|
| `name` | View directory and manifest key; generates `ui://views/<name>.html` |
| `description` | Resource description emitted for the generated View resource |
| `csp` | Author domain allowlists merged into resource `_meta.ui.csp` |
| `permissions` | Requested sandbox capabilities emitted as resource `_meta.ui.permissions` |
| `domain` | Dedicated sandbox-origin hint emitted as resource `_meta.ui.domain`; format and validation are host-dependent |
| `prefersBorder` | Host rendering preference emitted as resource `_meta.ui.prefersBorder` |

Do not assume `domain` is a URL or that one host's accepted format works in another host. Consult the target host's requirements. ChatGPT-specific submission rules belong in `../chatgpt-apps/01-dual-protocol.md`; keep this standard field host-neutral.

## Binding Validation

The framework validates the contract in two phases.

**When the tool is registered:**

- A View-bound tool without `outputSchema` throws. For a View with no meaningful structured payload, use `outputSchema: z.object({})` and return `structuredContent: {}`.
- A second tool binding the same `view.name` throws. One View may have at most one owning tool.

**When the server is mounted or the CLI validates a build:**

- Any View-bound tool with no primed View registry throws.
- A bound `view.name` absent from the primed manifest throws.
- A built/primed View that no tool binds emits a warning: `[mcp-use] View "<name>" is registered but no tool binds it.`

A folder-name mismatch is therefore a hard mount/build error, not a silent missing resource.

## Visibility

`visibility` is a top-level tool field, not part of `view`:

```typescript
server.tool(
  {
    name: "refresh-products",
    inputSchema: z.object({ cursor: z.string().optional() }),
    outputSchema: productResultsSchema,
    visibility: "app",
    view: { name: "product-refresh" },
  },
  handler
);
```

- Omitted: host default; normally callable by the model and app.
- `"model"`: narrows visibility to the model side.
- `"app"`: app-private helper tool, callable by Views through a host that supports `serverTools`.

The server still includes every registered tool in `tools/list`; the host interprets `_meta.ui.visibility`.

## Literal Wire Metadata

For `view.name: "product-search"`, `tools/list` contains both the standard nested key and a flat compatibility key:

```json
{
  "_meta": {
    "ui": {
      "resourceUri": "ui://views/product-search.html"
    },
    "ui/resourceUri": "ui://views/product-search.html"
  }
}
```

If `visibility` is set, the nested object also contains `"visibility": ["model"]` or `"visibility": ["app"]`.

A successful terminal tool result gets the same two resource URI keys. The framework does **not** stamp them onto `isError: true` or `input_required` results. Other handler-defined result `_meta` keys survive, but the framework-owned nested `ui` and flat `ui/resourceUri` values win on collision.

The generated resource is advertised and read with:

- URI `ui://views/product-search.html`
- MIME `text/html;profile=mcp-app`
- optional resource description
- resource `_meta.ui.csp`, `.permissions`, `.domain`, and `.prefersBorder`

## Required Text Fallback

Return useful `content` alongside `structuredContent`. Hosts without MCP Apps support still receive the tool and may call it; capability negotiation does not remove tools from `tools/list`.

## Related

- Discovery, tooling registration, and validation: `02-register-views-and-folder-conventions.md`
- Runtime config: `03-viewconfig.md`
- Build assets and synthesized HTML: `04-assets-mcp-url-and-serving.md`
- CSP and permissions: `05-csp-metadata.md`
- Worked example: `../canonical-anchor.md`
