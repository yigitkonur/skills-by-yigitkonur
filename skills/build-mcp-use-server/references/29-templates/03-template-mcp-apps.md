# Template: mcp-apps

*Read this for a complete tree of the `mcp-apps` template and what it demonstrates.*

## Generated File Tree

```
my-project/
├── index.ts                                    # MCPServer entry; tools with view: field
├── views/
│   └── my-view/
│       ├── view.tsx                           # React component (default export)
│       ├── view.css                           # Global stylesheet, imported as a side effect
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

This is a trimmed version of the real generated file (comments condensed; `{{PROJECT_NAME}}` is substituted at scaffold time):

```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({
  name: "{{PROJECT_NAME}}",
  title: "{{PROJECT_NAME}}",
  version: "1.0.0",
  description: "an mcp-use app",
  instructions: "use show-app to open the app view",
  websiteUrl: "https://mcp-use.com",
  icons: [{ src: "icon.svg", mimeType: "image/svg+xml", sizes: ["512x512"] }],
  // basePath: "/mcp",                 // default; uncomment to customize
  // oauth: oauthClerkProvider(),      // import from mcp-use/oauth/*
  // publicLandingPage: true,          // keep /mcp landing page public when oauth is on
});

const showAppInputSchema = z.object({
  appName: z.string().optional().describe("Optional title shown in the MCP App card"),
});
const showAppOutputSchema = z.object({
  message: z.string().describe("Message to display in the MCP App"),
});

export const showApp = server.tool(
  {
    name: "show-app",
    title: "Show MCP App",
    description: "Display the MCP App starter view",
    inputSchema: showAppInputSchema,
    outputSchema: showAppOutputSchema,  // REQUIRED for view binding
    view: {
      name: "my-view",                 // Must match views/my-view/ folder name
      description: "MCP App starter card with interactive demo hooks",
      prefersBorder: false,
      csp: {
        resourceDomains: ["https://fonts.googleapis.com", "https://fonts.gstatic.com"],
      },
    },
    annotations: { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
  },
  async ({ appName }, ctx) => {
    await new Promise((resolve) => setTimeout(resolve, 1500)); // pending skeleton is visible in dev
    const data = { message: `The MCP App starter for ${appName} is ready!` };
    return { content: [{ type: "text", text: data.message }], structuredContent: data };
  }
);

// say-hello — plain tool (no view); called from my-view via useCallTool
export const sayHello = server.tool(
  {
    name: "say-hello",
    title: "Say hello",
    description: "Returns a greeting for the Say Hello button demo",
    inputSchema: z.object({ name: z.string().describe("Name to greet") }),
    outputSchema: z.object({ greeting: z.string().describe("Greeting to display") }),
    annotations: { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
  },
  async ({ name }) => {
    const data = { greeting: `Hello, ${name}!` };
    return { content: [{ type: "text", text: data.greeting }], structuredContent: data };
  }
);

export default server;
```

No `server.listen()` call — `mcp-use dev`/`mcp-use start` own the socket.

## What `views/my-view/view.tsx` Demonstrates

The real generated view is 377 lines and imports every hook the runtime ships. Condensed to the wiring that matters:

```tsx
import {
  Image, ModelContext, ThemeProvider,
  useCallTool, useDisplayMode, useHostContext,
  useOpenExternal, useSendFollowUp, useToolContext,
  useViewTheme, useViewTool,
} from "mcp-use/react";
import { useState } from "react";
import { z } from "zod";
import "./view.css";

export default function McpApp() {
  const view = useToolContext<"show-app">();               // pending / error / result lifecycle
  const { hostCapabilities, platform, displayMode, locale, timeZone } = useHostContext();
  const theme = useViewTheme();
  const { availableDisplayModes, requestDisplayMode } = useDisplayMode();
  const openExternal = useOpenExternal();
  const sendFollowUp = useSendFollowUp();
  const sayHello = useCallTool("say-hello");                 // invoke a server tool from the view

  const [count, setCount] = useState(0);

  // useViewTool registers a tool the host/model can call while this view is mounted
  useViewTool(
    {
      name: "set-counter",
      description: "Set the counter displayed in the MCP App card",
      inputSchema: z.object({ value: z.number().int().min(0) }),
    },
    async ({ value }) => {
      setCount(value);
      return { content: [{ type: "text", text: `Counter set to ${value}` }] };
    }
  );

  const pending = view.status === "pending";
  const callResult = sayHello.data?.structuredContent?.greeting;

  return (
    <ThemeProvider>
      <Image src="icon.svg" alt="" />                       {/* resolves against public/ */}
      {pending ? <p>Loading...</p> : <p>{view.toolOutput?.message}</p>}
      <ModelContext content={`MCP App counter: ${count}`} /> {/* pushes state the model can read */}
      {/* theme, platform, locale, timeZone drive host-context display chips */}
      {/* requestDisplayMode({ mode: "pip" | "fullscreen" | "inline" }) switches modes */}
      {/* openExternal(url) and sendFollowUp(text) call back into the host */}
    </ThemeProvider>
  );
}
```

The full file also renders host-context chips (theme/platform/locale/timezone), a display-mode switcher, and an "Open external" / "Send follow-up" demo — read it at `dist/templates/mcp-apps/views/my-view/view.tsx` in the `create-mcp-use-app` package for the complete UI, or `references/18-mcp-apps/view-react/` for hook-by-hook docs.

## Key Points

1. **Tool must declare `view: { name }`** — Exact match to folder in `views/`. `view` also carries `description`, `prefersBorder`, and `csp: { resourceDomains, connectDomains }`.
2. **Tool `outputSchema` is required** — The view reads `structuredContent` typed by this schema via `useToolContext<"tool-name">().toolOutput`.
3. **`useToolContext<"show-app">()`** — Generic argument is the tool name (typed against `mcp-env.d.ts`'s `Register.tools`); returns `{ status: "pending" | "error" | "result", toolOutput, error }`.
4. **`useCallTool("say-hello")`** — Lets the view invoke a plain (non-view) server tool and read its result.
5. **`useViewTool(definition, callback)`** — Registers a tool that only exists while the view is mounted (here `set-counter`); distinct from a server-registered tool.
6. **`useHostContext()` / `useViewTheme()` / `useDisplayMode()`** — Read host platform, locale, timezone, theme, and available/request display modes (`inline`, `fullscreen`, `pip`).
7. **`useOpenExternal()` / `useSendFollowUp()`** — Open a URL via the host, or send a follow-up prompt back to the host conversation.
8. **`<ThemeProvider>`** — Applies host theme (light/dark); wrap the top-level component.
9. **`<ModelContext content={...}>`** — Pushes UI state text the model can read, independent of the tool's own `structuredContent`.
10. **`<Image src="icon.svg" />`** — Resolves root-relative paths against the served `public/` directory.

## Development

```bash
npm run dev
# Watches views/ and index.ts
# Changes trigger Vite HMR (instant reload in browser/Inspector)
# Inspector at http://127.0.0.1:3000/mcp/inspector shows views in real-time
```

## Styling

- `view.css` is imported as a plain side-effect stylesheet (`import "./view.css";`) — global scope, not CSS Modules. Use Tailwind utility classes or scoped selectors inside the file to avoid collisions.
- Vite dev handles CSS auto-reload; `mcp-use build --inline` embeds each view's bundled JS and CSS directly in its MCP resource instead of serving them as external assets (default: external).

## Adding More Views

Create a new folder under `views/`:
```
views/product-search/
  └── view.tsx
```

In `index.ts`, add a tool with `view: { name: "product-search" }`. Auto-discovered by CLI.

## Next Steps

- Read `references/18-mcp-apps/01-what-are-mcp-apps.md` for comprehensive MCP Apps concepts.
- Read `references/18-mcp-apps/view-react/02-usetoolcontext.md` for hook reference.
- Read `references/18-mcp-apps/view-react/01-setup-and-providers.md` for setup patterns.
- Read `references/04-tools/canonical-anchor.md` for a full tool + view example.
