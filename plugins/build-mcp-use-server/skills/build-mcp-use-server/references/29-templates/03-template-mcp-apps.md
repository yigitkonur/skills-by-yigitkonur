# Template: mcp-apps

*Read this for a complete tree of the `mcp-apps` template and what it demonstrates.*

## Generated File Tree

```
my-project/
├── index.ts                                    # MCPServer entry; tools with view: field
├── views/
│   └── my-view/
│       ├── view.tsx                           # React component + viewConfig export
│       ├── view.css                           # Scoped styles (optional)
│       ├── MeshGradient.tsx                   # Helper component
│       ├── Tooltip.tsx                        # Helper component
│       └── icons.tsx                          # SVG icon exports
├── mcp-env.d.ts                               # Auto-generated type bridge
├── package.json                               # Includes React 19, dev scripts
├── tsconfig.json                              # ESM + React 19 + MCP types
├── gitignore
├── README.md
└── public/
    ├── icon.svg                               # Server icon
    └── logo-mcp-use.svg                       # Optional branding
```

## What `index.ts` Demonstrates

```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
});

const toolResultSchema = z.object({
  title: z.string(),
  message: z.string(),
  icon: z.string().optional(),
});

export const myViewTool = server.tool(
  {
    name: "my-view-tool",
    description: "Demonstrate an interactive view",
    inputSchema: z.object({
      name: z.string().describe("Your name"),
    }),
    outputSchema: toolResultSchema,  // REQUIRED for view binding
    view: {
      name: "my-view",                // Must match views/my-view/ folder name
      description: "Displays a greeting",
      csp: {
        connectDomains: [],           // APIs the view needs to call
        resourceDomains: [],          // CDNs for images/fonts/scripts
      },
    },
  },
  async ({ name }) => {
    // Model sees this text
    const modelText = `Greeted ${name}`;

    // React view receives this as structuredContent
    const uiData = { title: "Greeting", message: `Hello, ${name}!`, icon: "👋" };

    return {
      content: [{ type: "text", text: modelText }],
      structuredContent: uiData,
    };
  }
);

export default server;
server.listen();
```

## What `views/my-view/view.tsx` Demonstrates

```tsx
import { useToolContext, ThemeProvider, ModelContext } from "mcp-use/react";
import type { ViewConfig } from "mcp-use/react";
import styles from "./view.css";

export const viewConfig: ViewConfig = {
  displayModes: ["inline", "fullscreen"],
  autoResize: true,  // Height adapts to content
};

export default function MyView() {
  // Receives tool result data typed by outputSchema
  const ctx = useToolContext<"my-view-tool">();

  if (ctx.status === "pending") {
    return <ThemeProvider><p>Loading...</p></ThemeProvider>;
  }
  if (ctx.status === "error") {
    return <ThemeProvider><p>Error: {ctx.error?.message}</p></ThemeProvider>;
  }

  const { title, message, icon } = ctx.toolOutput;

  return (
    <ThemeProvider>
      <ModelContext content={`Showed: ${title} — ${message}`}>
        <div className={styles.container}>
          <h1>{title}</h1>
          {icon && <span>{icon}</span>}
          <p>{message}</p>
        </div>
      </ModelContext>
    </ThemeProvider>
  );
}
```

## Key Points

1. **Tool must declare `view: { name }`** — Exact match to folder in `views/`.
2. **Tool `outputSchema` is required** — React component receives data typed by this schema.
3. **`viewConfig` export** — Optional; controls display modes and auto-resize behavior.
4. **Use `useToolContext<"tool-name">()`** — Receives the tool's `toolOutput` (structuredContent) + lifecycle (`status`, `error`).
5. **`<ThemeProvider>`** — Applies host theme (light/dark); wrap top-level component.
6. **`<ModelContext>`** — Describes visible UI to model; enables smart follow-ups.

## Development

```bash
npm run dev
# Watches views/ and index.ts
# Changes trigger Vite HMR (instant reload in browser/Inspector)
# Inspector at http://127.0.0.1:3000/mcp/inspector shows views in real-time
```

## Styling

- `view.css` is scoped to the component (module system by default).
- Import and apply: `className={styles.container}`.
- Vite dev handles CSS auto-reload; production `mcp-use build` inlines or externals per `--inline` flag.

## Adding More Views

Create a new folder under `views/`:
```
views/product-search/
  └── view.tsx
```

In `index.ts`, add a tool with `view: { name: "product-search" }`. Auto-discovered by CLI.

## Next Steps

- Read `../18-mcp-apps/01-what-are-mcp-apps.md` for comprehensive MCP Apps concepts.
- Read `../18-mcp-apps/view-react/02-usetoolcontext.md` for hook reference.
- Read `../18-mcp-apps/view-react/01-setup-and-providers.md` for setup patterns.
- See `04-tools/canonical-anchor.md` for a full tool + view example.
