# Migrating OpenAI Apps SDK to MCP Apps

*Read this when converting an OpenAI Apps SDK application to mcp-use v2 Views.*

mcp-use v2 implements the MCP Apps UI standard and auto-translates to ChatGPT's protocol, so one server definition can work in ChatGPT and MCP Apps hosts.

## Master mapping

| OpenAI Apps SDK | mcp-use v2 |
|---|---|
| Widget resource | `views/<name>/view.tsx` |
| Tool `_meta["openai/outputTemplate"]` | Tool `view: { name }` |
| `window.openai.toolInput` | `useToolContext().toolInput` |
| `window.openai.toolOutput` | `useToolContext().toolOutput` |
| `window.openai.widgetState` | `useViewState()` |
| `window.openai.setWidgetState()` | `useViewState()` setter |
| `window.openai.callTool()` | `useCallTool()` |
| `window.openai.sendFollowUpMessage()` | `useSendFollowUp()` |
| `window.openai.openExternal()` | `useOpenExternal()` |
| `window.openai.requestDisplayMode()` | `useDisplayMode()` |
| `text/html+skybridge` | `text/html;profile=mcp-app` |

## Server: Apps SDK style → mcp-use v2

**Apps SDK style**:
```typescript
server.registerTool(
  "search",
  {
    title: "Search",
    inputSchema: { query: z.string() },
    _meta: { "openai/outputTemplate": "ui://widget/search.html" },
  },
  async ({ query }) => ({
    content: [{ type: "text", text: `Results for ${query}` }],
    structuredContent: { query, results: [] },
  }),
);

server.registerResource(
  "search-widget",
  "ui://widget/search.html",
  {},
  async () => ({
    contents: [{
      uri: "ui://widget/search.html",
      mimeType: "text/html+skybridge",
      text: widgetHtml,
    }],
  }),
);
```

**mcp-use v2**:
```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({ name: "search-app", version: "1.0.0" });

export const search = server.tool(
  {
    name: "search",
    description: "Search items",
    inputSchema: z.object({ query: z.string() }),
    outputSchema: z.object({
      query: z.string(),
      results: z.array(z.object({ id: z.string(), name: z.string() })),
    }),
    view: { name: "search", description: "Search results" },
  },
  async ({ query }) => ({
    content: [{ type: "text", text: `Results for ${query}` }],
    structuredContent: { query, results: [] },
  }),
);

export default server;
```

Do not register the HTML resource manually. Create `views/search/view.tsx`; mcp-use generates the `ui://views/search.html` resource with MIME `text/html;profile=mcp-app` and compatibility metadata.

## View: `window.openai` → hooks

**Apps SDK style**:
```tsx
export default function SearchWidget() {
  const [state, setState] = useState(window.openai?.widgetState ?? { selected: null });
  const output = window.openai?.toolOutput;

  const select = async (id: string) => {
    const next = { selected: id };
    setState(next);
    await window.openai?.setWidgetState(next);
    await window.openai?.callTool("get-details", { id });
  };

  return <Results items={output?.results ?? []} onSelect={select} />;
}
```

**mcp-use v2**:
```tsx
import {
  ModelContext,
  ThemeProvider,
  useCallTool,
  useToolContext,
  useViewState,
} from "mcp-use/react";

export default function SearchView() {
  const ctx = useToolContext<"search">();
  const [state, setState] = useViewState<{ selected: string | null }>({ selected: null });
  const details = useCallTool("get-details");

  if (ctx.status === "pending") return <ThemeProvider><p>Loading…</p></ThemeProvider>;
  if (ctx.status === "error") return <ThemeProvider><p>{ctx.error.message}</p></ThemeProvider>;

  const select = async (id: string) => {
    setState({ selected: id });
    await details.callTool({ id });
  };

  return (
    <ThemeProvider>
      <ModelContext content={`Selected item: ${state.selected ?? "none"}`}>
        <Results items={ctx.toolOutput.results} onSelect={select} />
      </ModelContext>
    </ThemeProvider>
  );
}
```

## Migration steps

1. Install `mcp-use@2.0.0-beta.66`, `zod@4`, React, and React DOM; require Node >=22.22.2 and ESM.
2. Replace raw Apps SDK tool/resource registration with `MCPServer` tools.
3. Give each UI tool an `outputSchema` and `view: { name }`.
4. Move each UI to `views/<name>/view.tsx`; delete manually registered HTML resources.
5. Replace `window.openai` reads and methods with hooks from `mcp-use/react`.
6. Replace widget state with `useViewState`; use React `useState` for model-invisible ephemeral state.
7. Wrap host-themed UI in `ThemeProvider`; expose current UI meaning with `ModelContext`.
8. Move static files into `public/` and resolve them with `getPublicBaseUrl()`.
9. Declare external origins under tool `view.csp`; do not hand-write CSP metadata.
10. Exercise both MCP Apps and ChatGPT compatibility paths in the Inspector before deployment.

## Gotchas

- Never import from a nonexistent `@mcp-use/react` package; use `mcp-use/react`.
- Never keep `text/html+skybridge`; v2 emits `text/html;profile=mcp-app`.
- Do not call `window.openai` directly in portable View code. mcp-use hooks handle host capability differences.
- `structuredContent` is View render data and must match `outputSchema`. Put private, non-schema data in `_meta` and read it through `useToolContext().meta`.
- `useViewState` is model-visible. Keep hover, animation, and other ephemeral values in React state.
- Host capabilities vary. Treat display-mode, files, messaging, and external-open requests as advisory/capability-gated.
- One tool binds to at most one View. Split tools if you need distinct UI surfaces.

See `references/18-mcp-apps/01-what-are-mcp-apps.md` for the full v2 Apps model.
