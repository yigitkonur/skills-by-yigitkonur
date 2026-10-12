# Views (MCP Apps)

*Authoritative guide for interactive React Views in mcp-use v2.*

Official documentation:
- [MCP Apps Overview](https://docs.mcp-use.com/v2/typescript/mcp-apps)
- [MCP Apps Quickstart](https://docs.mcp-use.com/v2/typescript/mcp-apps/quickstart)
- [Interactivity](https://docs.mcp-use.com/v2/typescript/mcp-apps/interactivity)
- [Generative UI](https://docs.mcp-use.com/v2/typescript/mcp-apps/generative-ui)
- [Model Context](https://docs.mcp-use.com/v2/typescript/mcp-apps/model-context)
- [Content Security Policy](https://docs.mcp-use.com/v2/typescript/mcp-apps/content-security-policy)
- [Multi-Host Deployment & Archestra Architecture](archestra-and-multi-host.md)

---

## 1. Architecture & Standards Alignment

In `mcp-use` v2, MCP Apps comply with the MCP Apps standard extension proposal (SEP-1865). When a client invokes an MCP tool that has an attached view:
- **Resource Packaging**: The server automatically packages the view as an HTML resource served at URI `ui://views/<name>.html` with MIME type `text/html;profile=mcp-app` (constant `UI_MIME_TYPE`) under the extension identifier `io.modelcontextprotocol/ui` (constant `UI_EXTENSION_ID`).
- **Host Sandbox**: Host containers (Claude Desktop, ChatGPT, or custom MCP clients) render the view within a sandboxed `<iframe>` communicating over `window.parent.postMessage` using JSON-RPC or the OpenAI Apps SDK bridge (`window.openai`).
- **Assets & Routes**: Bundled view assets are served at `${basePath}/_mcp-use/views/<name>/...`, and static files from `public/` are served at `${basePath}/_mcp-use/public/...`.

---

## 2. Bind a View & 1:1 Invariant

Create `views/<name>/view.tsx`. Export the rendering tool ref, declare its `outputSchema`, bind `view: { name }`, and return matching `structuredContent`.

> [!IMPORTANT]
> **Strict 1:1 View-to-Tool Binding Invariant:**
> Each view directory under `views/` can be bound to at most **ONE** server tool. Registering multiple tools pointing to the same `view: { name }` throws a registration error at startup.
> Any secondary operations, background queries, or sub-actions needed by that view must be viewless tools invoked via `useCallTool` or client-side ephemeral tools via `useViewTool`.

### Server Tool Declaration (`src/index.ts`)
```tsx
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({
  name: "shop-server",
  version: "1.0.0",
});

// Always export tool references as named constants for mcp-env.d.ts type generation
export const showProduct = server.tool(
  {
    name: "show-product",
    description: "Display interactive product card with pricing and specs",
    inputSchema: z.object({ sku: z.string() }),
    outputSchema: z.object({
      sku: z.string(),
      title: z.string(),
      price: z.number(),
    }),
    view: {
      name: "product-card", // Matches views/product-card/view.tsx exactly
      description: "Interactive Product Card View",
      prefersBorder: true,
      csp: {
        connectDomains: ["https://api.inventory.example.com"],
        resourceDomains: ["https://cdn.example.com"],
        frameDomains: [],
        baseUriDomains: [],
      },
      entrypoints: [
        { type: "thread" },
        { type: "global" },
      ],
      permissions: [],
      domain: "shop.example.com",
    },
  },
  async ({ sku }) => {
    const data = { sku, title: "Precision Screwdriver", price: 29.99 };
    return {
      // 1. LLM Context: Concise natural language summary conserving context tokens
      content: [{ type: "text", text: `Product ${data.title} ($${data.price}) loaded.` }],
      // 2. Structured Channel: Matches outputSchema, delivered to both LLM and View
      structuredContent: data,
      // 3. View-Only Meta: Completely hidden from LLM context, delivered to useToolContext().meta
      _meta: { privateId: "internal_101", warehouseId: "wh_east_4" },
    };
  }
);

export default server;
```

### Complete `ToolViewConfig` Interface
```typescript
export interface ToolViewConfig {
  /** Name of the view folder under views/ (e.g. "product-card") */
  name: string;
  /** Human-readable description of what this view renders */
  description?: string;
  /** Whether host container should draw a native border around the iframe */
  prefersBorder?: boolean;
  /** Content Security Policy domain overrides for this view */
  csp?: {
    connectDomains?: string[];
    resourceDomains?: string[];
    frameDomains?: string[];
    baseUriDomains?: string[];
  };
  /** ChatGPT launch surfaces (global, thread, file) */
  entrypoints?: Array<
    | { type: "global" }
    | { type: "thread" }
    | { type: "file"; extensions: string[] }
  >;
  /** Permissions requested from the host container */
  permissions?: string[];
  /** Primary domain associated with this view */
  domain?: string;
}
```

---

## 3. Three-Channel Data Routing Model

Data returned by a tool execute handler is segmented across three dedicated channels:

| Channel | Destination | Purpose | Declaration & Access |
|---|---|---|---|
| `content` | LLM Only | Concise model explanation. Keeps conversation token usage minimal. | Returned as `content: [{ type: "text", text: "..." }]` |
| `structuredContent` | LLM & View UI | Structured JSON matching `outputSchema`. Used by model for reasoning and consumed by view UI. | Defined in `outputSchema`, accessed via `useToolContext().toolOutput` |
| `_meta` | View UI Only | View-specific metadata completely hidden from LLM context. Ideal for internal IDs, tokens, or large render flags. | Returned in `_meta: { ... }`, accessed via `useToolContext().meta` |

---

## 4. Read the Rendering Call (`useToolContext`)

`useToolContext<"tool-name">()` returns a `ToolContextHandle` discriminated union over `status`: `"pending" | "ready" | "error"`.

> [!WARNING]
> **TypeScript Discriminated Union Narrowing Invariant:**
> Never destructure `toolOutput` upfront (e.g. `const { status, toolOutput } = useToolContext()`). Under strict TypeScript checking, destructuring `toolOutput` into a local variable causes `Object is possibly 'undefined'` errors because `toolOutput` is `undefined` when `status` is `"pending"` or `"error"`.
> Assign the handle to a variable (e.g. `const context = useToolContext<"show-product">();`) and narrow on `context.status === "ready"` before reading `context.toolOutput`.

```tsx
import React from "react";
import { useToolContext, ToolCancelledError, type ViewConfig } from "mcp-use/react";

export const viewConfig = {
  autoResize: true,
  displayModes: ["inline", "fullscreen", "pip"],
  preferredDisplayMode: "inline",
} satisfies ViewConfig;

export default function ProductCard() {
  const context = useToolContext<"show-product">();

  // 1. Pending Phase: toolInput contains streamed partial arguments (DeepPartial<TInput>)
  if (context.status === "pending") {
    return (
      <div className="p-4 animate-pulse text-secondary">
        Loading SKU {context.toolInput?.sku ?? "..."}…
      </div>
    );
  }

  // 2. Error Phase: context.error is ToolError | ToolCancelledError
  if (context.status === "error") {
    if (context.error instanceof ToolCancelledError) {
      return (
        <div className="p-4 text-secondary">
          Action was cancelled by host ({context.error.reason}).
        </div>
      );
    }
    return (
      <div className="p-4 text-danger">
        Error ({context.error.code}): {context.error.message}
      </div>
    );
  }

  // 3. Ready Phase: TypeScript narrows context; toolOutput and meta are safe to access
  const { title, price } = context.toolOutput;
  const privateId = context.meta?.privateId as string | undefined;

  return (
    <div className="p-4 space-y-2">
      <h2 className="text-lg font-semibold">{title}</h2>
      <p className="text-secondary">${price.toFixed(2)}</p>
      {privateId && <span className="text-xs text-muted">ID: {privateId}</span>}
    </div>
  );
}
```

### Tool Error vs Cancellation Handling
- `ToolError`: standard execution failure returned by the tool or server. Contains `{ code: string; message: string; data?: unknown }`.
- `ToolCancelledError`: thrown or transitioned when the host user or client aborts the pending invocation. Contains `{ reason: string }`.

---

## 5. Complete React Hooks Suite (`mcp-use/react`)

All view hooks and components are imported from `"mcp-use/react"`.

### Interaction & Execution Hooks
- **`useCallTool<Name>(tool: Name | ToolRef)`**: Invokes another server tool from the view. Returns `CallToolHandle<Args, Result>`:
  - `callTool: (args: Args) => Promise<Result>`
  - `data: Result | undefined`
  - `error: ToolError | ToolCancelledError | undefined`
  - `isPending: boolean`, `isError: boolean`, `isSuccess: boolean`, `reset: () => void`
- **`useDynamicTool(name: string)`**: Untyped escape hatch returning `CallToolHandle<unknown, unknown>` for tools created at runtime.
- **`useViewTool(definition, handler)`**: Registers temporary, client-side ephemeral tools exposed to the model only while the view is mounted.
- **`useSendFollowUp()`**: Returns `(args: { prompt: string }) => Promise<void>` to inject a user turn into the chat conversation.
- **`useOpenExternal()`**: Returns `(args: { url: string }) => Promise<void>` requesting the host open a URL in the user's default browser.
- **`useSendSizeChanged()`**: Returns `(size: { width?: number; height?: number }) => Promise<void>` to explicitly notify the host iframe of updated dimensions.

### State & Context Hooks
- **`useViewState<T>(defaultState)`**: Persists JSON-serializable UI state across conversation turns and tab switches:
  ```tsx
  const [filter, setFilter] = useViewState({ search: "", page: 1 });
  ```
- **`useModelContext()`**: Imperatively attaches contextual blocks to the active conversation:
  ```tsx
  const { attachments, pending, error, add, remove, clearAttachments } = useModelContext();
  // add is synchronous void:
  add("selection", { type: "text", text: `User selected SKU: ${sku}` });
  ```
- **`<ModelContext content="...">`**: Declarative component wrapper that pushes visible state to the model without user messaging.
- **`useDisplayMode()`**: Returns `{ displayMode, availableDisplayModes, requestDisplayMode }` for switching between `"inline"`, `"fullscreen"`, and `"pip"`.
- **`useDeepLink()`**: Returns `{ url: string | undefined }` to extract ChatGPT deep link routes and query params.
- **`useHostContext()`**: Returns `{ theme, locale, timeZone, platform, displayMode, safeArea, maxHeight, maxWidth, hostCapabilities, isAvailable }`. Guard optional features using host capability flags.
- **`useViewTheme()`**: Returns reactive primitive string `"light" | "dark"` reflecting current host appearance.
- **`useFiles()`**: Returns `{ isSupported, upload(file), getDownloadUrl({ fileId }) }` for host-managed file storage.

### UI Helper Components
- **`<ThemeProvider defaultTheme="light">`**: Wraps children and sets `data-theme` attributes on `<html>` / `<body>` matching the host color scheme.
- **`<ViewControls showDisplayModeToggle />`**: Prebuilt overlay controls for display mode switching.
- **`<Image src="...">`**: Automatically resolves `/_mcp-use/public/` paths safely within host CSP restrictions.

---

## 6. Content Security Policy (CSP)

Host applications isolate MCP App views in sandboxed iframes. `mcp-use` enforces and generates Content Security Policy headers and meta tags automatically.

### The 4 CSP Categories
1. `connectDomains`: Governs `connect-src` (`fetch`, WebSockets, `EventSource`, `XMLHttpRequest`).
2. `resourceDomains`: Governs `img-src`, `media-src`, `font-src`, and `style-src` (remote images, fonts, CDNs).
3. `frameDomains`: Governs `frame-src` and `child-src` (embedded iframes).
4. `baseUriDomains`: Governs `base-uri` (allowed document base URLs).

### Environment Variables
Configure system-wide CSP rules without changing code:
- `CSP_CONNECT_DOMAINS`: Comma-separated API domains (e.g. `https://api.example.com`).
- `CSP_RESOURCE_DOMAINS`: Comma-separated media/asset domains (e.g. `https://cdn.example.com`).
- `CSP_FRAME_DOMAINS`: Comma-separated iframe domains.
- `CSP_BASE_URI_DOMAINS`: Comma-separated base URI domains.
- `CSP_URLS`: **Universal shortcut variable**. Automatically appends its domains to BOTH `connectDomains` and `resourceDomains`.

### Strict 3-Tier CSP Merging Hierarchy (`buildMergedResourceCsp`)
When building or serving views, `mcp-use` computes the final CSP string following a strict 3-tier precedence hierarchy:

```
+-------------------------------------------------------------------+
| Priority 1 (Highest): Tool Author Declaration (`view.csp`)        |
|   - connectDomains, resourceDomains, frameDomains, baseUriDomains |
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
| Priority 2: Process Environment Variables                         |
|   - CSP_CONNECT_DOMAINS, CSP_RESOURCE_DOMAINS, CSP_URLS, etc.     |
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
| Priority 3 (Automatic): MCP System Defaults                       |
|   - Server base origin added to connectDomains                    |
|   - MCP_URL added to connectDomains                               |
|   - MCP_ASSETS_URL added to resourceDomains                       |
|   - Localhost Vite HMR WebSockets allowed in dev mode             |
+-------------------------------------------------------------------+
```
All domains are normalized to protocol and origin, validated against CSP Level 3 rules, and deduplicated.

---

## 7. Multi-Host Deployment: ChatGPT, Claude Desktop & Archestra

Because `mcp-use` views conform to the standard MCP Apps specification (`ui://views/<name>.html`), the same view codebase can run across different host platforms:

- **ChatGPT**: Interacts with the view inside an iframe. Leverages `@openai/apps-sdk-ui` styling, `<AppsSDKUIProvider linkComponent="a">`, `useViewTheme()`, and conversational evidence injection via `useModelContext()`.
- **Claude Desktop**: Renders standard tool views within its sandboxed preview iframe, receiving `structuredContent` and executing secondary actions via `useCallTool()`.
- **Archestra**: Fully supported via the **Installed-Server (Native Portable) Route** ([Archestra Guide](archestra-and-multi-host.md)):
  - Discovered automatically by Archestra and displayed under **"Apps from installed MCP servers"** in the gallery (`page.client.tsx`).
  - Tool calls execute through Archestra's session proxy (`POST /api/mcp/server/:mcpServerId`) using the installation's upstream credentials.
  - Production case studies (Ahrefs, SEMrush, Screaming Frog) confirm installed portable views as the modern, unified path over legacy platform-owned HTML.

For detailed cross-host capability matrices and Archestra diagnostic sequences, see the [Multi-Host & Archestra Architecture Guide](archestra-and-multi-host.md).
