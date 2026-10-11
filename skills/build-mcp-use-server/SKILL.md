---
name: build-mcp-use-server
description: Use if building, modifying, debugging, or verifying TypeScript MCP servers and ChatGPT Apps with mcp-use v2, MCPServer, Apps SDK UI, Views, and Plugin Extensions.
disable-model-invocation: true
---

# Build with mcp-use & ChatGPT Apps

Treat the installed `mcp-use` package, its exported types, generated declarations (`mcp-env.d.ts`), and official documentation at [docs.mcp-use.com](https://docs.mcp-use.com) as the authoritative sources of truth.

This skill grounds on the official [`MCPServer`](https://api-reference.mcp-use.com/classes/mcp-use.index.MCPServer.html) API surface, applies the lean architecture of the official `mcp-use` skills, and ensures that every ChatGPT app built with `mcp-use` is compliant with the **OpenAI Apps SDK UI** (`@openai/apps-sdk-ui`) by default.

---

## Workflow

1. **Inspect Project**: Check `package.json`, server entry, exported tool refs, `views/`, `skills/`, and the installed `mcp-use` version (Node.js >= 22.22.2 required).
2. **Scaffold or Initialize**: For greenfield projects, scaffold with the official CLI:
   ```bash
   npx create-mcp-use-app@latest my-app --template mcp-apps
   ```
   (Use `--template mcp-server` for headless tool servers).
3. **Read Focused References**:
   - [Server](references/server.md): Tools, resources, prompts, middleware, request context, result envelopes, and `ServerConfig`.
   - [Views](references/views.md): MCP Apps, React hooks, interaction channels, host capabilities, and CSP.
   - [OpenAI Apps SDK UI Guide](references/chatgpt-apps-ui.md): Full 29 components, hooks, Tailwind 4 setup, design tokens, and theme sync.
   - [ChatGPT Plugin Extensions](references/chatgpt-extensions.md): Launch entrypoints (`global`, `thread`, `file`), native `server.settings()`, tool icons, `useDeepLink()`, and `useModelContext()`.
   - [Authentication](references/auth.md): OAuth provider adapters, `mixedAuth: true`, tool-level `securitySchemes`, and verified identity on `ctx.auth`.
   - [Skills over MCP](references/skills-over-mcp.md): Reusable agent workflows and conventions under `skills/`.
   - [Advanced Features](references/advanced-features.md): OpenAPI (`fromOpenAPI`), proxying, notifications, subscriptions, and interactive elicitation (`inputRequired`).
   - [Migration](references/migration.md): Upgrading legacy v1 patterns, deprecated imports, and obsolete helpers to v2.
   - [Verification](references/verification.md): Verification loop with `mcp-use typecheck`, `mcp-use dev`, `mcp-use client`, and `mcp-use screenshot`.
4. **Implement Against Installed Types**: Always export static tool references and default-export the server instance.
5. **Verify Deterministically**: Drive real tool calls through `mcp-use client` and capture view screenshots with `mcp-use screenshot`.

---

## Core Invariants

1. **Root Server Import**: Always import `MCPServer` and server primitives from `"mcp-use"` (the legacy `"mcp-use/server"` subpath is obsolete).
2. **Export Static Tool Refs**: Always export every tool reference (`export const myTool = server.tool(...)`). The TypeScript compiler derives view and client contracts in `mcp-env.d.ts` from exported tool names.
3. **Default Server Export**: Always default-export the server instance (`export default server;`). The CLI runner (`mcp-use dev`, `build`, `start`) owns the HTTP listener and Vite view pipeline.
4. **Definition-First Tools & Standard Schema**: Define tools with `server.tool(definition, callback)`. Tool arguments use `inputSchema`; model prompts use `schema`. Always describe model-filled schema fields.
5. **Raw Result Envelopes**: Tool callbacks must return raw `CallToolResult` envelopes (`{ content: [...], structuredContent?: ... }`). Do not use deprecated v1 helpers (`text()`, `object()`, `widget()`). Expected failures return `{ isError: true, content: [...] }`; unexpected failures throw.
6. **Views Architecture**: Put each view at `views/<name>/view.tsx`. Each view must have exactly one owning tool with matching `view: { name: "<name>" }` and a mandatory `outputSchema`. Return matching `structuredContent`.
7. **OpenAI Apps SDK UI Compliance**: Every ChatGPT app must install `@openai/apps-sdk-ui`, import `@openai/apps-sdk-ui/css`, configure Tailwind 4 with `@source`, and wrap interactive components with `<AppsSDKUIProvider linkComponent="a">`.
8. **Stateless Request Model**: Server instances are request-scoped. Never use module globals or in-memory session registries for multi-request state or authentication. Use `ctx.requestState` or an external database.
9. **Strict CLI Flag Syntax**: Boolean CLI flags reject inline values in v2.7.2+ (`--tunnel=false` fails; use `--tunnel` or omit).

---

## Guardrails & Common Anti-Patterns

- **Never import non-existent `@openai/apps-sdk-ui` components**:
  - `Card` does **not** exist in `@openai/apps-sdk-ui`. Surface cards are standard `<div>` elements styled with Tailwind utility classes (`rounded-2xl border border-default bg-surface p-4 shadow-sm`).
  - `AvatarGroup` and `CopyTooltip` **are** official `@openai/apps-sdk-ui` components (from `@openai/apps-sdk-ui/components/Avatar` and `@openai/apps-sdk-ui/components/Tooltip`).
  - `Cart` and `Checkmark` do **not** exist in `@openai/apps-sdk-ui/components/Icon`. Use `Check`, `CheckCircle`, `Search`, `Plus`, `Settings`, etc.
- **Never omit `linkComponent` on `<AppsSDKUIProvider>`**: The TypeScript contract requires `linkComponent` (e.g. `<AppsSDKUIProvider linkComponent="a">`).
- **Never read `useToolContext().toolOutput` un-narrowed**: `useToolContext()` is a discriminated union. When `status === "pending"`, `toolOutput` is `undefined`. Always handle `status === "pending"` and `status === "error"` before accessing `toolOutput`. Narrow `error instanceof ToolCancelledError` for cancelled actions.
- **Configure `websiteUrl`, `icons`, and `logging` at the top level of `MCPServer`**:
  - `icons?: Icon[]`, `websiteUrl?: string`, and `logging?: LoggingOptions` are top-level properties on `ServerConfig`. Do not nest them in a fictitious `branding: { ... }` object (`server.branding` is a read-only getter).
  - Server logging level is configured via `logging: { enabled: true, level: "info" }` or overridden by the `MCP_USE_LOG_LEVEL` environment variable.
- **Never use legacy v1 `ctx.elicit()`**: Removed in v2.0.0 during the transition to the stateless request model. Use official protocol primitives: `inputRequired`, `inputRequired.elicit`, `inputRequired.elicitUrl`, `inputResponse`, and `acceptedContent`.
- **Never use wrong CLI commands**:
  - Client connect syntax: `mcp-use client connect <name> <url> [options]` (e.g. `npx mcp-use client connect dev http://localhost:3000/mcp`).
  - Screenshot syntax: `mcp-use screenshot (--server <name> | --mcp <url>) --tool <name> [args...] [options]`.

---

## Base MCPServer Architecture

Ground on [`MCPServer`](https://api-reference.mcp-use.com/classes/mcp-use.index.MCPServer.html) and [Server Documentation](https://docs.mcp-use.com/v2/typescript/server):

```typescript
import { MCPServer } from "mcp-use";

const server = new MCPServer({
  name: "catalog-server",
  version: "1.0.0",
  title: "Inventory & Catalog Manager",
  description: "Manage product catalog, stock levels, and search items.",
  instructions: "Use lookup-item before creating an order. Confirm stock availability.",
  basePath: "/mcp", // default route
  host: "127.0.0.1", // "0.0.0.0" for public hosting
  port: 3000,
  legacy: "stateless", // "stateless" (default) or "reject"
  websiteUrl: "https://example.com",
  icons: [
    { src: "icons/logo.svg", mimeType: "image/svg+xml", sizes: ["20x20"] }
  ],
  logging: { enabled: true, level: "info" }, // Overridden by MCP_USE_LOG_LEVEL env var
  skills: true, // Auto-discover conventional skills/ directory
  cors: {
    origin: "*",
    credentials: true,
  },
});

export default server;
```

---

## Tool Definitions & Result Envelopes

Documentation: [Server Tools](https://docs.mcp-use.com/v2/typescript/server/tools)

```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({ name: "catalog", version: "1.0.0" });

export const getProduct = server.tool(
  {
    name: "get-product",
    title: "Get Product Details",
    description: "Fetch product metadata, pricing, and live inventory by SKU.",
    icons: [
      { src: "icons/product.svg", mimeType: "image/svg+xml", sizes: ["20x20"] }
    ],
    inputSchema: z.object({
      sku: z.string().describe("Stock Keeping Unit identifier (e.g. 'PROD-100')"),
    }),
    outputSchema: z.object({
      sku: z.string(),
      title: z.string(),
      price: z.number(),
      inStock: z.boolean(),
    }),
    annotations: {
      readOnlyHint: true,
      openWorldHint: false,
    },
    visibility: "model", // "model" (default) or "app" (hidden from LLM, visible to UI views)
    view: {
      name: "product-card", // binds to views/product-card/view.tsx
      description: "Interactive product display card",
    },
  },
  async ({ sku }, ctx) => {
    // Expected operational failure
    if (!sku.startsWith("PROD-")) {
      return {
        isError: true,
        content: [{ type: "text", text: `Invalid SKU format: ${sku}` }],
      };
    }

    const data = { sku, title: "Precision Screwdriver", price: 29.99, inStock: true };
    return {
      content: [{ type: "text", text: `Product ${data.title} (${sku}) is in stock at $${data.price}` }],
      structuredContent: data,
      _meta: { internalId: "db_98213" }, // Private to view, hidden from LLM
    };
  }
);

export default server;
```

---

## ChatGPT Apps & OpenAI Apps SDK UI Compliance

Documentation:
- [ChatGPT Plugin Extensions](https://docs.mcp-use.com/v2/typescript/mcp-apps/chatgpt-extensions)
- [OpenAI Apps SDK UI Repository](https://github.com/openai/apps-sdk-ui)
- [Apps SDK UI Storybook Docs](https://openai.github.io/apps-sdk-ui/?path=/docs/overview-introduction--docs)
- [ChatGPT Apps UI Reference](references/chatgpt-apps-ui.md)

### 1. Installation & Styles Setup
```bash
npm install @openai/apps-sdk-ui tailwindcss @tailwindcss/vite
```

In `views/main.css` (or view-specific CSS):
```css
@import "tailwindcss";
@import "@openai/apps-sdk-ui/css";
@source "../node_modules/@openai/apps-sdk-ui";
```

### 2. View Component with Apps SDK UI & Theme Sync
Create `views/product-card/view.tsx`:

```tsx
import "./main.css";
import React, { useEffect } from "react";
import { useToolContext, useModelContext, useViewTheme, ToolCancelledError, type ViewConfig } from "mcp-use/react";
import { AppsSDKUIProvider } from "@openai/apps-sdk-ui/components/AppsSDKUIProvider";
import { Button } from "@openai/apps-sdk-ui/components/Button";
import { Badge } from "@openai/apps-sdk-ui/components/Badge";
import { applyDocumentTheme } from "@openai/apps-sdk-ui/theme";
import { Check, Plus } from "@openai/apps-sdk-ui/components/Icon";

export const viewConfig = {
  autoResize: true,
  displayModes: ["inline", "fullscreen"],
  preferredDisplayMode: "inline",
} satisfies ViewConfig;

export default function ProductCardView() {
  const { status, toolInput, toolOutput, error } = useToolContext<"get-product">();
  const theme = useViewTheme();
  const { add } = useModelContext();

  // Synchronize host theme with Apps SDK UI data-theme attribute
  useEffect(() => {
    if (theme) applyDocumentTheme(theme);
  }, [theme]);

  if (status === "pending") {
    return <div className="p-4 text-secondary text-sm">Loading SKU {toolInput?.sku}…</div>;
  }

  if (status === "error") {
    if (error instanceof ToolCancelledError) {
      return <div className="p-4 text-secondary text-sm">Action cancelled: {error.reason}</div>;
    }
    return <div className="p-4 text-danger text-sm">Error: {error.message}</div>;
  }

  return (
    <AppsSDKUIProvider linkComponent="a">
      {/* Standard surface card styled with semantic tokens */}
      <div className="w-full max-w-md rounded-2xl border border-default bg-surface p-4 shadow-sm">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="heading-md">{toolOutput.title}</h2>
            <p className="text-secondary text-sm">SKU: {toolOutput.sku}</p>
          </div>
          <Badge color={toolOutput.inStock ? "success" : "warning"}>
            {toolOutput.inStock ? "In Stock" : "Backorder"}
          </Badge>
        </div>

        <div className="mt-4 flex items-center justify-between border-t border-subtle pt-3">
          <span className="text-lg font-semibold">${toolOutput.price.toFixed(2)}</span>
          <Button
            color="primary"
            onClick={() => {
              // Attach verified evidence to next ChatGPT model turn (synchronous void)
              add("selected:product", {
                type: "text",
                text: `Selected SKU ${toolOutput.sku}: $${toolOutput.price}`,
              });
            }}
          >
            <Plus className="size-4" />
            Add to Chat
          </Button>
        </div>
      </div>
    </AppsSDKUIProvider>
  );
}
```

### 3. Complete Apps SDK UI Component Inventory (29 Components)

All imported from `@openai/apps-sdk-ui/components/<Component>`:

| Category | Components | Purpose |
|---|---|---|
| **Feedback & Status** | `Alert`, `Badge`, `Indicator`, `EmptyMessage`, `ShimmerText` | Status banners, live badges, empty states, and loading shimmers. |
| **Identity & Icons** | `Avatar`, `Image`, `Icon` | User profiles, image fallbacks, and 700+ monochrome SVGs. |
| **Actions** | `Button`, `ButtonLink` (plus `CopyButton`) | Primary, secondary, soft, outline action buttons and copy controls. |
| **Form Inputs** | `Input`, `Textarea`, `Checkbox`, `Switch`, `RadioGroup`, `Slider`, `SegmentedControl`, `Select`, `SelectControl`, `TagInput` | Accessible, validated inputs and grouped controls. |
| **Date Pickers** | `DatePicker`, `DateRangePicker` | Calendar popups and date range selectors. |
| **Overlays** | `Menu`, `Popover`, `Tooltip` | Dropdown menus, anchored popovers, and contextual tooltips. |
| **Typography & Content** | `Markdown`, `CodeBlock`, `TextLink` | Styled markdown renderer, syntax-highlighted code blocks, and themed hyperlinks. |
| **Motion & Transitions** | `Transition` (`Animate`, `AnimateLayout`, `SlotTransitionGroup`, `TransitionGroup`) | Smooth height, fade, and layout morph transitions for iframes. |
| **Providers** | `AppsSDKUIProvider` | Root context providing router `linkComponent` configuration. |

### 4. Official Hooks Suite (`@openai/apps-sdk-ui/hooks`)
- `useBreakpoint(size: BreakpointName)`: Responsive breakpoint match boolean (e.g. `useBreakpoint("md")`).
- `useAutoGrowTextarea()`: Dynamic auto-growing textarea heights.
- `useAnimatedScrollTo()`: Smooth programmatic scrolling with cancellation.
- `useDocumentVisible()`: Tracks iframe visibility.
- `useIsMounted()`, `useLatestValue()`, `usePrevious()`, `useScrollable()`, `useSimulatedProgress()`, `useStableCallback()`, `useTextSelection()`, `useTrailingValue()`.

---

## ChatGPT Plugin Extensions

Documentation: [ChatGPT Plugin Extensions](https://docs.mcp-use.com/v2/typescript/mcp-apps/chatgpt-extensions) | [Extensions Reference](references/chatgpt-extensions.md)

### 1. Typed Launch Entrypoints
Declare launch surfaces on `tool.view.entrypoints`:
- `global`: Launches app from ChatGPT top-level launcher (input schema must accept `{}`).
- `thread`: Launches app within conversation tab (input schema must accept `{}`).
- `file`: Launches app as file viewer for matching extensions (input schema must receive `{ file: { name: string, resourceUri: string } }`).

```typescript
export const openCsvViewer = server.tool(
  {
    name: "open-csv",
    title: "CSV Table Viewer",
    inputSchema: z.object({
      file: z.object({ name: z.string(), resourceUri: z.string() }),
    }),
    outputSchema: z.object({ file: z.object({ name: z.string(), resourceUri: z.string() }) }),
    view: {
      name: "csv-viewer",
      entrypoints: [{ type: "file", extensions: [".csv", ".tsv"] }],
    },
  },
  async ({ file }) => ({ content: [], structuredContent: { file } })
);
```

### 2. Native Plugin Settings (`server.settings`)
Register native ChatGPT plugin settings with typed fields and layout sections:

```typescript
server.settings({
  fields: {
    theme: { type: "string", label: "Theme", default: "system" },
    autoSync: { type: "boolean", label: "Automatic Sync", default: true },
  },
  layout: [
    {
      title: "Preferences",
      fields: ["theme", "autoSync"],
    },
  ],
  read: async (ctx) => ({ theme: "system", autoSync: true }),
  update: async (patch, ctx) => ({ theme: "system", autoSync: true, ...patch }),
});
```

### 3. Incoming Deep Links (`useDeepLink`)
Read incoming URLs sent to global entrypoints:
```tsx
import { useDeepLink } from "mcp-use/react";

export function AppRouter() {
  const { url } = useDeepLink(); // e.g. "/items?tag=hardware"
}
```

### 4. Selected Model Context (`useModelContext`)
Manage evidence attachments sent with the next user model turn (`attachments` is `Record<string, ModelContextBlock>`, `add` is synchronous void):
```tsx
import { useModelContext } from "mcp-use/react";

const { attachments, add, remove, clearAttachments } = useModelContext();

// Attach text summary (synchronous void, no title)
add("summary", { type: "text", text: "Order Summary: Total $120.00" });

// Attach image with Base64 data (PNG/JPEG/GIF/WebP, max 10MB)
add("receipt", { type: "image", data: receiptBase64, mimeType: "image/png" });

// Enumerate attached blocks
Object.entries(attachments).map(([key, block]) => (
  <span key={key}>{key}: {block.type}</span>
));
```

---

## Authentication & Mixed Auth

Documentation: [Authentication](https://docs.mcp-use.com/v2/typescript/server/authentication) | [Mixed Auth](https://docs.mcp-use.com/v2/typescript/server/authentication/mixed-auth) | [Auth Reference](references/auth.md)

Configure `mixedAuth: true` on `MCPServer` to serve public discovery, optional auth, and protected tools from one endpoint:

```typescript
import { MCPServer } from "mcp-use";
import { oauthAuth0Provider } from "mcp-use/oauth/auth0";
import { z } from "zod";

const server = new MCPServer({
  name: "store",
  version: "1.0.0",
  oauth: oauthAuth0Provider({ domain: process.env.AUTH0_DOMAIN! }),
  mixedAuth: true, // Enables unauthenticated tools/list discovery
});

// Public tool: Anyone may call without token
export const searchCatalog = server.tool(
  {
    name: "search-catalog",
    inputSchema: z.object({ query: z.string() }),
    securitySchemes: [{ type: "noauth" }],
  },
  async ({ query }, ctx) => {
    return { content: [{ type: "text", text: `Results for ${query}` }] };
  }
);

// Protected tool: Requires sign-in with specific scopes
export const checkout = server.tool(
  {
    name: "checkout",
    inputSchema: z.object({ cartId: z.string() }),
    securitySchemes: [{ type: "oauth2", scopes: ["orders:write"] }],
  },
  async ({ cartId }, ctx) => {
    const userId = ctx.auth.user.id;
    return { content: [{ type: "text", text: `Order placed for user ${userId}` }] };
  }
);
```

Supported Providers: Clerk (`mcp-use/oauth/clerk`), Auth0 (`mcp-use/oauth/auth0`), WorkOS (`mcp-use/oauth/workos`), Supabase (`mcp-use/oauth/supabase`), Keycloak (`mcp-use/oauth/keycloak`), Better Auth (`mcp-use/oauth/better-auth`), Scalekit (`mcp-use/oauth/scalekit`), Convex (`mcp-use/oauth/convex`), and Custom (`oauthCustomProvider`).

---

## Interactive Elicitation

Documentation: [Elicitation](https://docs.mcp-use.com/v2/typescript/server/elicitation) | [Advanced Features](references/advanced-features.md)

`ctx.elicit()` was removed in v2.0.0 during the transition to the stateless request model. Use official protocol primitives:

```typescript
import { MCPServer, inputRequired, inputResponse, acceptedContent } from "mcp-use";
import { z } from "zod";

const confirmSchema = z.object({ approve: z.boolean().describe("Confirm action") });

server.tool(
  {
    name: "delete-resource",
    inputSchema: z.object({ id: z.string() }),
  },
  async ({ id }, ctx) => {
    const response = inputResponse(ctx.inputResponses, "delete-approval");
    if (response.kind === "elicit" && response.action !== "accept") {
      return { isError: true, content: [{ type: "text", text: "Action cancelled" }] };
    }

    const confirmation = acceptedContent(ctx.inputResponses, "delete-approval", confirmSchema);
    if (!confirmation) {
      return inputRequired({
        inputRequests: {
          "delete-approval": inputRequired.elicit({
            message: `Permanently delete resource ${id}?`,
            requestedSchema: confirmSchema,
          }),
        },
      });
    }

    if (!confirmation.approve) {
      return { isError: true, content: [{ type: "text", text: "Action rejected" }] };
    }

    // Side-effects execute only after confirmed, validated input
    await db.delete(id);
    return { content: [{ type: "text", text: `Deleted ${id}` }] };
  }
);
```

For external authorization: `inputRequired.elicitUrl({ message: "...", url: authUrl })`.

---

## Skills over MCP (SEP-2640)

Documentation: [Skills over MCP](https://docs.mcp-use.com/v2/typescript/server/skills) | [Skills Reference](references/skills-over-mcp.md)

Serve reusable instruction workflows alongside tools:
1. Place skills under `skills/<skill-name>/SKILL.md`.
2. Automatic discovery is enabled by default. Require with `skills: true` or disable with `skills: false` on `MCPServer`.
3. Hosts retrieve skill metadata via `skills/list` and `skills/get`.

---

## CLI & Tooling Reference

Documentation: [CLI Reference](https://docs.mcp-use.com/v2/typescript/api-reference/cli-reference) | [Client CLI](https://docs.mcp-use.com/v2/typescript/tooling/client-cli) | [Verification](references/verification.md)

```bash
# Scaffold new v2 project
npx create-mcp-use-app@latest my-server --template mcp-apps

# Start development with hot reload, Vite views pipeline, and Inspector
mcp-use dev

# Start development with authenticated public tunnel for live ChatGPT testing
mcp-use dev --tunnel

# Typecheck server and views
mcp-use typecheck

# Build for production
mcp-use build

# Start production server
mcp-use start

# Connect live client session straight from terminal
mcp-use client connect dev http://localhost:3000/mcp

# List tools and call with arguments
mcp-use client dev tools list
mcp-use client dev tools call get-product sku=PROD-100

# Capture automated screenshot of view preview
mcp-use screenshot --server dev --tool get-product sku=PROD-100

# Deploy to mcp-use cloud (requires GitHub repo)
mcp-use deploy
```

---

## Canonical Documentation Links

- **API Base**: [MCPServer Class Reference](https://api-reference.mcp-use.com/classes/mcp-use.index.MCPServer.html)
- **Official Docs**: [docs.mcp-use.com](https://docs.mcp-use.com)
  - [Server Quickstart & Core](https://docs.mcp-use.com/v2/typescript/server)
  - [Server Migration Guide](https://docs.mcp-use.com/v2/typescript/server/migration)
  - [Server Tools](https://docs.mcp-use.com/v2/typescript/server/tools)
  - [Server Examples](https://docs.mcp-use.com/v2/typescript/server/examples)
  - [MCP Apps Quickstart](https://docs.mcp-use.com/v2/typescript/mcp-apps/quickstart)
  - [ChatGPT Plugin Extensions](https://docs.mcp-use.com/v2/typescript/mcp-apps/chatgpt-extensions)
  - [MCP Apps Interactivity](https://docs.mcp-use.com/v2/typescript/mcp-apps/interactivity)
  - [Model Context Attachments](https://docs.mcp-use.com/v2/typescript/mcp-apps/model-context)
  - [Content Security Policy](https://docs.mcp-use.com/v2/typescript/mcp-apps/content-security-policy)
  - [Authentication & Mixed Auth](https://docs.mcp-use.com/v2/typescript/server/authentication/mixed-auth)
  - [Interactive Elicitation](https://docs.mcp-use.com/v2/typescript/server/elicitation)
  - [Skills over MCP](https://docs.mcp-use.com/v2/typescript/server/skills)
  - [CLI Reference](https://docs.mcp-use.com/v2/typescript/api-reference/cli-reference)
  - [Client CLI Guide](https://docs.mcp-use.com/v2/typescript/tooling/client-cli)
  - [Changelog & Breaking Changes](https://docs.mcp-use.com/typescript/changelog/changelog)
- **OpenAI Apps SDK UI**:
  - [Apps SDK UI GitHub](https://github.com/openai/apps-sdk-ui)
  - [Apps SDK UI Storybook Docs](https://openai.github.io/apps-sdk-ui/?path=/docs/overview-introduction--docs)
