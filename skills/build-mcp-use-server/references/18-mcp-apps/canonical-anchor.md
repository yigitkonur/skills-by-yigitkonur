# Canonical Example: Minimal End-to-End Tool + View

*Read this as the authoritative minimal reference implementation for an MCP Apps tool with a view.*

This example shows a small, copy-paste-oriented tool + view baseline. Add authentication, provider-response validation, host-specific metadata, and deployment controls when your application requires them.

## Server (index.ts)

```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";

// Define the result schema — REQUIRED for views
const searchResultSchema = z.object({
  query: z.string().describe("The search query"),
  results: z.array(
    z.object({
      id: z.string(),
      title: z.string(),
      url: z.string(),
      snippet: z.string(),
    })
  ),
  totalCount: z.number(),
});

const server = new MCPServer({
  name: "search-server",
  version: "1.0.0",
});

// Export tool for View typing
export const searchWeb = server.tool(
  {
    name: "search-web",
    description: "Search the web for information",
    inputSchema: z.object({
      query: z.string().describe("Search query"),
      limit: z.number().int().min(1).max(20).describe("Results to return").default(10),
    }),
    outputSchema: searchResultSchema,
    // Bind the tool result to the View.
    view: {
      name: "search-results",
      description: "Display search results in a list",
      prefersBorder: true,
    },
  },
  async ({ query, limit }) => {
    // Keep the baseline self-contained. Replace this with your database or
    // server-side provider call; View CSP does not authorize or restrict work
    // performed inside this server callback.
    const results = Array.from({ length: limit }, (_, index) => ({
      id: `result-${index + 1}`,
      title: `${query} result ${index + 1}`,
      url: `https://example.com/search?q=${encodeURIComponent(query)}`,
      snippet: "Replace this generated row with data from your server-side source.",
    }));

    // Return raw MCP result
    // - `content`: text for the model
    // - `structuredContent`: typed by outputSchema and exposed as View toolOutput
    return {
      content: [
        {
          type: "text",
          text: `Found ${results.length} results for "${query}"`,
        },
      ],
      structuredContent: {
        query,
        results,
        totalCount: results.length,
      },
    };
  }
);

// No registerViews() call and no listen() call here. `mcp-use dev` and
// `mcp-use build` own view discovery/build and the server socket — the
// entry file's only job is this default export.
export default server;
```

## View (views/search-results/view.tsx)

```typescript
import {
  useToolContext,
  useHostContext,
  useOpenExternal,
  ThemeProvider,
  ModelContext,
  type ViewConfig,
} from "mcp-use/react";

// Optional: export pre-render view config
export const viewConfig: ViewConfig = {
  displayModes: ["inline", "fullscreen"],
  autoResize: true,
};

export default function SearchResultsView() {
  const ctx = useToolContext<"search-web">();
  const openExternal = useOpenExternal();
  const { hostCapabilities } = useHostContext();

  // Guard on status
  if (ctx.status === "pending") {
    return (
      <ThemeProvider>
        <div style={{ padding: "1rem", textAlign: "center" }}>
          <p>Searching...</p>
        </div>
      </ThemeProvider>
    );
  }

  if (ctx.status === "error") {
    return (
      <ThemeProvider>
        <div style={{ padding: "1rem", color: "red" }}>
          <p>Error: {ctx.error?.message}</p>
        </div>
      </ThemeProvider>
    );
  }

  // status === "ready"; toolInput can still be undefined, so use the query
  // returned in structuredContent instead of dereferencing toolInput.
  const { query, results, totalCount } = ctx.toolOutput;
  const canOpenLinks = hostCapabilities?.openLinks !== undefined;

  return (
    <ThemeProvider>
      <ModelContext content={`Search results for "${query}": ${totalCount} found`}>
        <div style={{ padding: "1rem" }}>
          <h2>Results ({results.length})</h2>
          <ul style={{ listStyle: "none", padding: 0 }}>
            {results.map((result) => (
              <li
                key={result.id}
                style={{
                  marginBottom: "1rem",
                  borderBottom: "1px solid #ccc",
                  paddingBottom: "1rem",
                }}
              >
                <h3 style={{ marginTop: 0 }}>{result.title}</h3>
                <p style={{ margin: "0.5rem 0", fontSize: "0.9rem" }}>
                  {result.snippet}
                </p>
                {canOpenLinks && (
                  <button
                    type="button"
                    onClick={() => {
                      void openExternal({ url: result.url }).catch((error) => {
                        console.error("Host could not open result:", error);
                      });
                    }}
                  >
                    Open result
                  </button>
                )}
              </li>
            ))}
          </ul>
        </div>
      </ModelContext>
    </ThemeProvider>
  );
}
```

## Key Patterns

1. **Tool definition** has `outputSchema` and `view: { name }`.
2. **Server result** returns raw `{ content, structuredContent }` matching the schema.
3. **View export** is the default component + optional `viewConfig`.
4. **Status guard** protects against access before `status === "ready"`.
5. **Ready input remains optional**; render from `toolOutput` when the output already carries the needed value.
6. **useToolContext** is typed by the exported tool name (`"search-web"`).
7. **External navigation** goes through `useOpenExternal` and is shown only when the host advertises `openLinks`.
8. **ModelContext** describes the current UI state to the model.
9. **View CSP is an iframe boundary.** Add `view.csp.connectDomains` only when browser code in the View calls an external origin. It does not authorize or constrain the server callback's `fetch`.

## When to Add View CSP

This baseline does not fetch from third-party origins in browser code, so it declares no third-party View CSP domains. If the View itself later calls `https://api.example.com`, add that origin to `view.csp.connectDomains`. A database or provider request performed inside the server callback is outside the View iframe's CSP boundary.

## Testing Locally

```bash
npm run dev
# Server at http://localhost:3000/mcp
# Inspector at http://localhost:3000/mcp/inspector

# Test via inspector: call search-web tool, then confirm the
# search-results view renders below the tool result in the inspector's
# tool-call panel. There is no standalone browsable URL for a view — it
# renders only inside a host (the Inspector or a real MCP client), fetched
# as the ui://views/search-results.html resource the tool result points to.
```

## Cross-References

- **Server setup:** `references/18-mcp-apps/server-surface/01-tool-view-field.md`
- **CSP details:** `references/18-mcp-apps/server-surface/05-csp-metadata.md`
- **View hooks:** `references/18-mcp-apps/view-react/02-usetoolcontext.md`, `references/18-mcp-apps/view-react/06-followups-and-open-external.md`, `references/18-mcp-apps/view-react/07-host-context-files-and-size.md`
- **Anti-patterns:** `references/18-mcp-apps/anti-patterns.md`
- **ChatGPT support:** `references/18-mcp-apps/02-mcp-apps-vs-chatgpt-apps-sdk.md`
