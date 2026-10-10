# Migrating OpenAI Apps SDK & ChatGPT Widgets to MCP Apps

*Read this when migrating legacy ChatGPT Widgets, Skybridge implementations, or raw `window.openai` code to mcp-use v2 Views powered by `@openai/apps-sdk-ui`.*

In early ChatGPT Apps SDK and Skybridge architectures, custom UI extensions were served as raw HTML snippets with injected globals (`window.openai`), custom MIME types (`application/vnd.openai.chatgpt-app+html` or `text/html+skybridge`), and ad-hoc CSS styles.

`mcp-use v2` standardizes custom UI around the official **MCP Apps UI specification**. Servers declare View bindings directly on tools, bundle React components under `views/<name>/view.tsx`, style with official `@openai/apps-sdk-ui` design tokens and Tailwind 4, synchronize dark mode with `applyDocumentTheme()`, attach conversational evidence using `useModelContext()`, and declare typed file/thread entrypoints. The framework automatically serves `text/html;profile=mcp-app` while maintaining cross-host compatibility between ChatGPT, Claude, and standalone MCP Inspector environments.

---

## At a Glance: Apps SDK & Widget Migration Diff

| Capability / Surface | Legacy ChatGPT Widget / Skybridge | Canonical mcp-use v2 (MCP Apps & Apps SDK UI) | Impact / Action |
|---|---|---|---|
| **View Architecture** | Injected HTML string, raw template file, or `widget.tsx` | Modular React component at `views/<name>/view.tsx` | Auto-compiled with Vite; zero manual iframe or HTML wiring |
| **Tool Binding** | `_meta["openai/outputTemplate"] = "ui://widget/..."` | Declarative `view: { name: "<name>" }` + mandatory `outputSchema` | Framework binds View to tool and validates result against schema |
| **Host Communication** | Untyped global `window.openai.*` | Typed React hooks from `mcp-use/react` | Type-safe RPC across all MCP Apps and ChatGPT hosts |
| **Design System** | Ad-hoc CSS classes, arbitrary inline styles, unstyled markup | `@openai/apps-sdk-ui` + Tailwind 4 (`tailwindcss@^4`) | Native ChatGPT design tokens, accessible Radix components, consistent styling |
| **Root Provider** | None, or legacy `McpUseProvider autoSize` | `<AppsSDKUIProvider>` from `@openai/apps-sdk-ui/components/AppsSDKUIProvider` | Configures accessible link routing and design system foundations |
| **Theme / Dark Mode** | Manual `window.matchMedia` or broken dark mode | `useViewTheme()` synchronized with `applyDocumentTheme(theme)` | Automatic synchronization with ChatGPT `[data-theme]` root attribute |
| **View State** | `window.openai.widgetState` / `setWidgetState()` | `useViewState<T>()` (model-visible) + React `useState()` (ephemeral) | Root state **must be a JSON object**; model sees relevant state changes |
| **Evidence Attachments** | Untyped chat follow-up messages via `sendFollowUpMessage()` | `useModelContext().add("key", { type: "text" \| "image", ... })` | Attaches structured evidence directly to the model's next conversational turn |
| **Launch Entrypoints** | Deprecated `openai/fileParams` metadata | Typed `entrypoints: [{ type: "file", extensions: [...] }]` | Host launches view on matching file uploads, threads, or deep links |
| **MIME Type** | `text/html+skybridge` or `application/vnd.openai.chatgpt-app+html` | `text/html;profile=mcp-app` | Framework serves modern MCP Apps MIME type automatically |

---

## Prerequisites & Installation

To build ChatGPT MCP Apps with native design system fidelity, install `@openai/apps-sdk-ui`, Tailwind 4, and `@tailwindcss/vite`:

```bash
npm install mcp-use@2.8.2 zod@4 react react-dom @openai/apps-sdk-ui tailwindcss @tailwindcss/vite
```

**Environment floor**: Node.js `>= 22.22.2`, strictly ESM (`"type": "module"` in `package.json`).

### View Stylesheet Foundations (`views/main.css`)

In Tailwind 4, styles are configured using CSS `@import` and `@source` directives rather than `tailwind.config.js`. Create `views/main.css`:

```css
@import "tailwindcss";
@import "@openai/apps-sdk-ui/css";

/* CRITICAL: Instructs Tailwind to scan @openai/apps-sdk-ui components for class names */
@source "../node_modules/@openai/apps-sdk-ui";

/* Application-specific styles below */
```

> **Warning**: Omitting `@source "../node_modules/@openai/apps-sdk-ui";` or `@import "@openai/apps-sdk-ui/css";` causes all Apps SDK UI components to render completely unstyled.

---

## Runtime Host Bridge: Mapping `window.openai` to `mcp-use/react`

Never access `window.openai` directly in View components. The table below details the exact hook replacements exported by `mcp-use/react`:

| Legacy `window.openai` API | Canonical `mcp-use/react` Replacement | Notes & Behavioral Nuances |
|---|---|---|
| `window.openai.toolInput` | `useToolContext<ToolName>().toolInput` | Available immediately on call start; permits rendering skeleton/streaming UI |
| `window.openai.toolOutput` | `useToolContext<ToolName>().toolOutput` | Typed output matching the tool's `outputSchema`; available once tool completes |
| `window.openai.status` | `useToolContext<ToolName>().status` | Returns `"pending" \| "ready" \| "error"` |
| `window.openai.widgetState` | `const [state, setState] = useViewState<T>(initial)` | Model-visible state. **Root must be a JSON object**, never a bare primitive |
| `window.openai.setWidgetState()` | `setState(nextState)` from `useViewState` | Serialized and sent to model; persists across host re-renders |
| `window.openai.callTool(name, args)` | `const tool = useCallTool("name"); tool.callTool(args)` | Invokes sibling MCP tool from View; typed via `mcp-env.d.ts` |
| `window.openai.sendFollowUpMessage(text)` | `const send = useSendFollowUp(); send(text)` | Injects a message into the conversation thread |
| `window.openai.openExternal(url)` | `const open = useOpenExternal(); open(url)` | Securely requests host to open external browser tab |
| `window.openai.requestDisplayMode(mode)` | `const setMode = useDisplayMode(); setMode("fullscreen")` | Requests `"inline"` or `"fullscreen"` display mode |
| `window.openai.theme` | `const { theme } = useViewTheme()` | Returns `"light" \| "dark"`; sync using `applyDocumentTheme(theme)` |
| *(No legacy equivalent)* | `const { add } = useModelContext()` | Attaches structured evidence (`text`, `image`) to next model turn |

---

## Launch Surfaces: Typed Entrypoints vs. `openai/fileParams`

In legacy Skybridge widgets, file triggers were configured using untyped tool metadata: `_meta: { "openai/fileParams": { extensions: [".csv"] } }`.

In `mcp-use v2`, launch entrypoints are declared directly on the tool definition's `view.entrypoints` property, and the tool's `inputSchema` receives a structured `{ file: { name, resourceUri } }` payload:

```typescript
// server.ts
export const analyzeData = server.tool(
  {
    name: "analyze-data",
    title: "Analyze Dataset",
    description: "Launch interactive data visualization from chat or uploaded file",
    inputSchema: z.object({
      file: z
        .object({
          name: z.string().describe("Filename of the uploaded document"),
          resourceUri: z.string().describe("MCP resource URI to read file contents"),
        })
        .optional(),
      filter: z.string().optional(),
    }),
    outputSchema: z.object({
      summary: z.string(),
      rowsCount: z.number(),
    }),
    view: {
      name: "data-analyzer",
      entrypoints: [
        { type: "global" },                                         // Global app launcher
        { type: "thread" },                                         // In-conversation widget
        { type: "file", extensions: [".csv", ".tsv", ".xlsx"] },    // File upload trigger
      ],
    },
  },
  async ({ file, filter }, ctx) => {
    // Process file if opened via file entrypoint...
    return {
      content: [{ type: "text", text: `Analyzing dataset ${file?.name ?? "default"}` }],
      structuredContent: { summary: "Analysis complete", rowsCount: 1500 },
    };
  }
);
```

---

## Runnable Before & After Code Transformation

### Before: Legacy ChatGPT Widget (`window.openai`, Ad-Hoc Styling)

The legacy widget relied on fragile `window.openai` globals, custom CSS classes, and manual resource registration:

```html
<!-- Legacy Skybridge Widget: Raw HTML, window.openai, ad-hoc styling -->
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body { font-family: -apple-system, sans-serif; margin: 12px; background: #ffffff; color: #111; }
    .card { border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px; max-width: 400px; }
    .title { font-size: 16px; font-weight: 600; margin-bottom: 8px; }
    .btn { background: #10a37f; color: #fff; border: none; padding: 8px 14px; border-radius: 4px; cursor: pointer; }
    .btn:hover { background: #0d8a6a; }
  </style>
</head>
<body>
  <div class="card">
    <div class="title" id="item-title">Loading...</div>
    <p id="item-desc"></p>
    <button class="btn" id="action-btn">Verify Item</button>
  </div>

  <script>
    // Fragile untyped globals
    const output = window.openai ? window.openai.toolOutput : null;
    let state = (window.openai && window.openai.widgetState) || { verified: false };

    if (output) {
      document.getElementById("item-title").innerText = output.name || "Unknown";
      document.getElementById("item-desc").innerText = output.description || "";
    }

    document.getElementById("action-btn").addEventListener("click", async () => {
      state.verified = true;
      if (window.openai) {
        await window.openai.setWidgetState(state);
        await window.openai.callTool("audit-log", { itemId: output.id });
        await window.openai.sendFollowUpMessage("Verified item " + output.name);
      }
      document.getElementById("action-btn").innerText = "Verified";
    });
  </script>
</body>
</html>
```

---

### After: Canonical mcp-use v2 Server & View Component

In canonical `mcp-use v2`, the server declares a typed tool with `outputSchema`, and the View is an accessible React component wrapped in `<AppsSDKUIProvider>` using native `@openai/apps-sdk-ui` components.

#### 1. Server Tool Definition (`server.ts`)

```typescript
// server.ts
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({
  name: "catalog-server",
  version: "2.0.0",
  basePath: "/mcp",
});

const CatalogItemSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  price: z.number(),
  category: z.string(),
});

export const inspectItem = server.tool(
  {
    name: "inspect-item",
    title: "Inspect Catalog Item",
    description: "Display interactive catalog item card with inspection controls",
    icons: [{ src: "icons/box.svg", mimeType: "image/svg+xml", sizes: ["20x20"] }],
    inputSchema: CatalogItemSchema,
    outputSchema: CatalogItemSchema,
    view: {
      name: "item-inspector",
      description: "Interactive item inspector using OpenAI Apps SDK UI",
      entrypoints: [{ type: "thread" }],
    },
  },
  async (item) => ({
    content: [{ type: "text", text: `Displaying item ${item.name} ($${item.price.toFixed(2)})` }],
    structuredContent: item,
  })
);

export default server;
```

#### 2. View Component (`views/item-inspector/view.tsx`)

```tsx
// views/item-inspector/view.tsx
import "../main.css";
import React, { useEffect, useState } from "react";
import {
  useToolContext,
  useViewState,
  useCallTool,
  useModelContext,
  useViewTheme,
} from "mcp-use/react";
import { AppsSDKUIProvider } from "@openai/apps-sdk-ui/components/AppsSDKUIProvider";
import { Button } from "@openai/apps-sdk-ui/components/Button";
import { Card } from "@openai/apps-sdk-ui/components/Card";
import { Badge } from "@openai/apps-sdk-ui/components/Badge";
import { Checkmark, Warning } from "@openai/apps-sdk-ui/components/Icon";
import { applyDocumentTheme } from "@openai/apps-sdk-ui/theme";

export default function ItemInspectorView() {
  const ctx = useToolContext<"inspect-item">();
  const { theme } = useViewTheme();
  
  // Model-visible view state (MUST be a JSON object, never a bare primitive)
  const [viewState, setViewState] = useViewState<{ verified: boolean }>({
    verified: false,
  });

  // Ephemeral component state (local only, model does not see this)
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Sibling tool hook
  const auditLogger = useCallTool("audit-log");
  
  // Model context hook for evidence attachments
  const { add: attachEvidence } = useModelContext();

  // 1. Dark mode synchronization with ChatGPT / host container
  useEffect(() => {
    if (theme) {
      applyDocumentTheme(theme);
    }
  }, [theme]);

  // 2. Loading state
  if (ctx.status === "pending") {
    return (
      <AppsSDKUIProvider>
        <div className="p-4 text-sm text-[var(--text-secondary)]">
          Loading catalog item details…
        </div>
      </AppsSDKUIProvider>
    );
  }

  // 3. Error state
  if (ctx.status === "error") {
    return (
      <AppsSDKUIProvider>
        <div className="p-4 flex items-center gap-2 text-sm text-[var(--text-error)]">
          <Warning className="size-4" />
          <span>Error loading item: {ctx.error.message}</span>
        </div>
      </AppsSDKUIProvider>
    );
  }

  const { id, name, description, price, category } = ctx.toolOutput;

  const handleVerify = async () => {
    setIsSubmitting(true);
    try {
      // Step A: Update model-visible state
      await setViewState({ verified: true });

      // Step B: Call companion audit tool
      await auditLogger.callTool({ itemId: id, action: "item_verified" });

      // Step C: Attach evidence block to the conversation turn
      await attachEvidence("verification-receipt", {
        type: "text",
        title: `Item Verification: ${name}`,
        text: `Item "${name}" (ID: ${id}, Category: ${category}) was inspected and verified by the user at price $${price.toFixed(2)}.`,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AppsSDKUIProvider>
      <Card className="p-5 max-w-sm border border-[var(--border-subtle)] bg-[var(--bg-surface)] rounded-xl shadow-xs">
        <div className="flex items-start justify-between gap-3 mb-2">
          <div>
            <h2 className="text-base font-semibold text-[var(--text-primary)]">{name}</h2>
            <span className="text-xs text-[var(--text-tertiary)]">{category}</span>
          </div>
          <Badge variant={viewState.verified ? "success" : "neutral"}>
            {viewState.verified ? (
              <span className="flex items-center gap-1">
                <Checkmark className="size-3" />
                Verified
              </span>
            ) : (
              "Pending Review"
            )}
          </Badge>
        </div>

        <p className="text-sm text-[var(--text-secondary)] mb-4">{description}</p>

        <div className="flex items-center justify-between pt-3 border-t border-[var(--border-subtle)]">
          <div className="text-lg font-semibold text-[var(--text-primary)]">
            ${price.toFixed(2)}
          </div>
          <Button
            variant="primary"
            disabled={isSubmitting || viewState.verified}
            onClick={handleVerify}
          >
            {viewState.verified ? "Verified" : "Verify Item"}
          </Button>
        </div>
      </Card>
    </AppsSDKUIProvider>
  );
}
```

---

## Anti-Patterns and Common Apps SDK Migration Traps

| Anti-Pattern | Root Mechanism & Failure Mode | Canonical v2 Fix |
|---|---|---|
| **Importing from `@mcp-use/react`** | The scoped package `@mcp-use/react` does not exist on npm. Fails at build time: `Cannot find module '@mcp-use/react'`. | Import from the official subpath: `import { useToolContext } from "mcp-use/react";`. |
| **Direct Access to `window.openai.*`** | `window.openai` is undefined in non-ChatGPT hosts (Inspector, Claude, test harnesses) and causes `ReferenceError: window is not defined` during SSR. | Use React hooks from `mcp-use/react` (`useToolContext`, `useViewState`, `useCallTool`). |
| **Missing Tailwind 4 `@source` in CSS** | Tailwind 4 does not automatically scan `node_modules`. Components from `@openai/apps-sdk-ui` render unstyled with broken layouts. | Add `@source "../node_modules/@openai/apps-sdk-ui";` and `@import "@openai/apps-sdk-ui/css";` in `views/main.css`. |
| **Setting a Primitive in `useViewState`** | `useViewState("active")` or `useViewState(true)` throws a runtime error. Host protocol requires root state to be a JSON object dictionary. | Always pass an object: `useViewState<{ active: boolean }>({ active: true })`. |
| **Using Reserved Key `_uiContext`** | Keys starting with `_uiContext` are reserved for host window layout metadata. Writing to this key corrupts state synchronization. | Use non-reserved property names in state dictionaries. |
| **Serving Legacy MIME `text/html+skybridge`** | Declaring legacy MIME types prevents modern MCP hosts from recognizing the component as an interactive MCP App. | Do not register HTML resources manually. Declare `view: { name }` on the tool; mcp-use serves `text/html;profile=mcp-app`. |
| **Omitting `outputSchema` on UI Tools** | Tools bound to Views without an `outputSchema` cannot validate `toolOutput` and fail TypeScript checks in `mcp-env.d.ts`. | Always declare a Zod v4 `outputSchema` on every tool that declares a `view`. |

---

## Next Steps & Cross-References

- **Design System Catalog**: See `references/chatgpt-apps-ui.md` for the complete 29+ component inventory, icons, and tokens.
- **Plugin Extensions**: See `references/chatgpt-extensions.md` for settings, monochrome icons, and file entrypoints.
- **View Architecture**: See `06-v1-to-v2-widgets-to-views.md` for detailed View lifecycle, CSP configuration, and permissions.
