# Canonical Example: End-to-End Tool + View + CSP

*Read this as the authoritative reference implementation for an MCP Apps tool with a view.*

This example shows a complete, minimal, production-ready tool + view + CSP setup. Use it as the template for your own tools.

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
    // Bind to view; declare CSP
    view: {
      name: "search-results",
      description: "Display search results in a clickable list",
      csp: {
        connectDomains: ["https://api.search-provider.com"],
      },
      prefersBorder: true,
    },
  },
  async ({ query, limit }) => {
    // Fetch results from external API (CSP allows this)
    const apiResponse = await fetch(
      `https://api.search-provider.com/search?q=${encodeURIComponent(query)}&limit=${limit}`,
      { headers: { "Authorization": `Bearer ${process.env.SEARCH_API_KEY}` } }
    );

    if (!apiResponse.ok) {
      return {
        isError: true,
        content: [{ type: "text", text: `Search failed: ${apiResponse.statusText}` }],
      };
    }

    const rawResults = await apiResponse.json();

    // Parse and shape results
    const results = rawResults.items.map((item) => ({
      id: item.id,
      title: item.title,
      url: item.url,
      snippet: item.description,
    }));

    // Return raw MCP result
    // - `content`: text for the model
    // - `structuredContent`: typed by outputSchema, passed to view as props
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
        totalCount: rawResults.totalCount,
      },
    };
  }
);

// Register views and start server
const viewsManifest = require("./.mcp-use/build/views-manifest.json");
server.registerViews(viewsManifest);

await server.listen(3000);
console.log("MCP server running on http://localhost:3000/mcp");
```

## View (views/search-results/view.tsx)

```typescript
import {
  useToolContext,
  useCallTool,
  ThemeProvider,
  ModelContext,
  ViewControls,
  type ViewConfig,
} from "mcp-use/react";

// Optional: export immutable view config
export const viewConfig: ViewConfig = {
  displayModes: ["inline", "fullscreen"],
  autoResize: true,
};

export default function SearchResultsView() {
  // Typed by tool's outputSchema
  const ctx = useToolContext<"search-web">();
  const { callTool: detailTool } = useCallTool("get-result-detail");

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

  // status === "ready"
  const { results, totalCount } = ctx.toolOutput;

  return (
    <ThemeProvider>
      <ModelContext
        content={`Search results for "${ctx.toolInput.query}": ${totalCount} found`}
      >
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
                  cursor: "pointer",
                }}
                onClick={async () => {
                  // Call another tool from the view
                  try {
                    await detailTool({ resultId: result.id });
                  } catch (err) {
                    console.error("Failed to get details:", err);
                  }
                }}
              >
                <a
                  href={result.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ textDecoration: "none", color: "blue" }}
                >
                  <h3 style={{ marginTop: 0 }}>{result.title}</h3>
                </a>
                <p style={{ margin: "0.5rem 0", fontSize: "0.9rem" }}>
                  {result.snippet}
                </p>
              </li>
            ))}
          </ul>

          <ViewControls>
            <button
              onClick={() => {
                // Model could also request more results
                console.log("Request more from model");
              }}
            >
              More Results
            </button>
          </ViewControls>
        </div>
      </ModelContext>
    </ThemeProvider>
  );
}
```

## Key Patterns

1. **Tool definition** has `outputSchema`, `view: { name }`, and `csp` for external APIs.
2. **Server result** returns raw `{ content, structuredContent }` matching the schema.
3. **View export** is the default component + optional `viewConfig`.
4. **Status guard** protects against crashes when `status !== "ready"`.
5. **useToolContext** is typed by the tool name (e.g., `"search-web"`).
6. **useCallTool** from the view invokes other tools with proper error handling.
7. **ModelContext** describes the current UI state to the model.
8. **CSP declaration** allows the server to fetch from external APIs safely.

## Environment Setup

Ensure these are set at deploy time:

```bash
# Server env vars
SEARCH_API_KEY=sk-xxxxx          # API credentials (only server sees)
MCP_URL=https://myserver.com     # Auto-added to CSP connectDomains

# CSP env vars (optional, overrides tool view.csp)
CSP_CONNECT_DOMAINS=https://api.search-provider.com
```

## Testing Locally

```bash
npm run dev
# Server at http://localhost:3000/mcp
# Inspector at http://localhost:3000/mcp/inspector

# Test via inspector: call search-web tool
# View renders at http://localhost:3000/mcp/views/search-results
```

## Cross-References

- **Server setup:** `references/18-mcp-apps/server-surface/01-tool-view-field.md`
- **CSP details:** `references/18-mcp-apps/server-surface/05-csp-metadata.md`
- **View hooks:** `references/18-mcp-apps/view-react/02-usetoolcontext.md`, `03-usecalltool.md`
- **Anti-patterns:** `references/18-mcp-apps/anti-patterns.md`
- **ChatGPT support:** `references/18-mcp-apps/02-mcp-apps-vs-chatgpt-apps-sdk.md`
