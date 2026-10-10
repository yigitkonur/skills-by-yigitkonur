---
name: build-mcp-use-server
description: "Build TypeScript MCP servers and ChatGPT MCP Apps with mcp-use v2 — MCPServer base, OpenAI Apps SDK UI compliance by default, views, settings, entrypoints, model context, mixed auth, and official CLI."
disable-model-invocation: true
---

# Build mcp-use Server & ChatGPT Apps

Authoritative development guide for **mcp-use v2** TypeScript servers and **ChatGPT MCP Apps** (stable `2.8.x` on npm `latest`).

This skill grounds on the official [`MCPServer`](https://api-reference.mcp-use.com/classes/mcp-use.index.MCPServer.html) API surface, applies the philosophy of the official `mcp-use` skills, and makes every ChatGPT app compliant with the **OpenAI Apps SDK UI** (`@openai/apps-sdk-ui`) by default.

---

## When to Use This Skill

Trigger when building, refactoring, migrating, or verifying:
- **MCP Servers with `mcp-use` v2**: Creating servers with `new MCPServer({ name, version, ... })`, tools with Standard Schema (Zod v4, ArkType, Valibot), resources, prompts, middleware, and request context (`ctx`).
- **ChatGPT MCP Apps & Views**: Creating interactive frontend views at `views/<name>/view.tsx`, bound to tools with `outputSchema` and rendered inside ChatGPT or standard MCP Apps hosts.
- **OpenAI Apps SDK UI Compliance**: Styling ChatGPT apps using `@openai/apps-sdk-ui`, Tailwind 4, official design tokens, dark mode (`[data-theme]`), and the full Radix-backed component suite.
- **ChatGPT Plugin Extensions**: Implementing typed `entrypoints` (`global`, `thread`, `file`), native plugin `server.settings()`, tool-level `icons`, `useDeepLink()`, and `useModelContext()` evidence attachments.
- **Mixed Authentication**: Configuring `mixedAuth: true` on `MCPServer` with tool-level `securitySchemes` (`noauth` vs `oauth2`), OAuth provider adapters (`mcp-use/oauth/*`), or custom providers with `setup(host)`.
- **Interactive Elicitation**: Multi-round user input flows via `inputRequired.elicit()`, `inputRequired.elicitUrl()`, `inputResponse()`, and `acceptedContent()`.
- **Agent Skills over MCP (SEP-2640)**: Serving reusable instruction workflows from the conventional `skills/` directory.
- **Streamable HTTP Serving & Transports**: Deploying via `server.listen()`, `server.fetch`, Next.js (`mcp-use/next`), TanStack Start (`mcp-use/tanstack-start`), or Hono.
- **Tooling & CLI**: Scaffolding with `create-mcp-use-app`, running `mcp-use dev`, `build`, `typecheck`, `start`, `client connect --negotiate`, `screenshot`, and `mcp-use deploy`.

**Do not use this skill when:**
- Building app-side client connectors — route to `build-mcp-use-client`.
- Building LLM orchestration agents — route to `build-mcp-use-agent`.
- Serving raw official SDK servers over stdio — `mcp-use` v2 serves Streamable HTTP only.

---

## Core Invariants

1. **Package & Engine Floor**: `mcp-use` v2 is ESM-only and requires **Node.js >= 22.22.2**. Install with `npm install mcp-use @mcp-use/cli`.
2. **Root Server Import**: Always import `MCPServer` and server primitives from `mcp-use` (root). The legacy `mcp-use/server` import is obsolete.
3. **Definition-First Tools**: Define tools with `server.tool(definition, callback)`. Arguments use `inputSchema` (`schema` is an alias); prompts use `schema`. Always `.describe()` model-filled schema fields.
4. **Export Static Tool Refs**: Always export every static tool reference (`export const myTool = server.tool(...)`). The TypeScript compiler derives view contracts in `mcp-env.d.ts` from exported tool names.
5. **Default Server Export**: Always default-export the server instance (`export default server;`) so the CLI runner (`mcp-use dev`, `build`, `start`) can manage the listener, Vite view pipeline, and Inspector.
6. **Raw MCP Result Envelopes**: Tool callbacks must return raw `CallToolResult` envelopes (`{ content: [...], structuredContent?: ... }`). Do not use deprecated v1 helpers (`text()`, `object()`). Expected errors return `{ isError: true, content: [...] }`; unexpected errors throw.
7. **View Architecture**: Put views at `views/<name>/view.tsx`. Each view must have exactly one owning tool with `view: { name: "<name>" }` and a mandatory `outputSchema`. Return matching `structuredContent`.
8. **OpenAI Apps SDK UI by Default**: Every ChatGPT app must install `@openai/apps-sdk-ui`, import `@openai/apps-sdk-ui/css`, configure Tailwind 4, and wrap interactive roots with `<AppsSDKUIProvider>`.
9. **Stateless Request Model**: Server instances are rebuilt per request. Never use module globals or in-memory session maps for multi-request state or authentication. Use `ctx.requestState` or an external database.
10. **Strict CLI Flag Syntax**: Boolean CLI flags reject inline values in v2.7.2+ (`--tunnel=false` fails; use `--tunnel` or omit).

---

## Base MCPServer Architecture

Ground on [`MCPServer`](https://api-reference.mcp-use.com/classes/mcp-use.index.MCPServer.html) ([docs: Server](https://docs.mcp-use.com/v2/typescript/server)):

```typescript
import { MCPServer } from "mcp-use";

const server = new MCPServer({
  name: "inventory-app",
  version: "1.0.0",
  title: "Inventory & Catalog Manager",
  description: "Manage product catalog, stock levels, and customer orders.",
  instructions: "Use lookup-item before creating an order. Confirm stock availability.",
  basePath: "/mcp", // default route
  host: "127.0.0.1", // "0.0.0.0" for public hosting
  port: 3000,
  icons: [
    { src: "icon.svg", mimeType: "image/svg+xml", sizes: ["20x20"] }
  ],
  websiteUrl: "https://example.com",
  skills: true, // Auto-discover skills/ directory
  cors: {
    origin: "*",
    credentials: true,
  },
  logging: { level: "info" }, // "info" | "debug" | "trace"
});

export default server;
```

### Server Instance Methods & Surface
- `server.tool(definition, callback)`: Register tools; returns typed `ToolRef`.
- `server.settings(options)`: Register native ChatGPT plugin settings read/update tools.
- `server.resource(definition, callback)`: Register static resource at URI.
- `server.resourceTemplate(definition, callback)`: Register parameterized resource template.
- `server.prompt(definition, callback)`: Register model prompt template with `schema`.
- `server.use("mcp:<method>", middleware)`: Register typed protocol middleware.
- `server.on("mcp:<event>", listener)`: Register protocol event listeners.
- `server.proxy(servers)`: Mount and namespace upstream MCP servers.
- `server.notifyToolsChanged()`, `notifyResourcesChanged()`, `notifyPromptsChanged()`, `notifyResourceUpdated(uri)`: Publish live invalidations to subscribed clients.
- `server.listen(port?, options?)`: Start standalone Node.js HTTP listener.
- `server.fetch(request, env?, executionCtx?)`: Web-standard fetch handler for Edge/Workers/Hono.

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
      name: "product-card",
      description: "Interactive product display card",
      prefersBorder: true,
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
```

---

## ChatGPT Apps & OpenAI Apps SDK UI Compliance

Documentation:
- [ChatGPT Plugin Extensions](https://docs.mcp-use.com/v2/typescript/mcp-apps/chatgpt-extensions)
- [MCP Apps Quickstart](https://docs.mcp-use.com/v2/typescript/mcp-apps/quickstart)
- [OpenAI Apps SDK UI Repository](https://github.com/openai/apps-sdk-ui)
- [Apps SDK UI Storybook Docs](https://openai.github.io/apps-sdk-ui/?path=/docs/overview-introduction--docs)

### 1. Installation & Styles Setup
Every ChatGPT app project must install `@openai/apps-sdk-ui` with Tailwind 4:

```bash
npm install @openai/apps-sdk-ui tailwindcss @tailwindcss/vite
```

Configure stylesheet foundations (`views/main.css` or global stylesheet):

```css
@import "tailwindcss";
@import "@openai/apps-sdk-ui/css";
@source "../node_modules/@openai/apps-sdk-ui";

/* Custom view overrides */
```

### 2. View Component with Apps SDK UI & Theme Sync
Create `views/<name>/view.tsx`:

```tsx
import "./main.css";
import React, { useEffect } from "react";
import { useToolContext, useCallTool, useModelContext, useViewTheme, type ViewConfig } from "mcp-use/react";
import { AppsSDKUIProvider } from "@openai/apps-sdk-ui/components/AppsSDKUIProvider";
import { Button } from "@openai/apps-sdk-ui/components/Button";
import { Badge } from "@openai/apps-sdk-ui/components/Badge";
import { Card } from "@openai/apps-sdk-ui/components/Card";
import { applyDocumentTheme } from "@openai/apps-sdk-ui/theme";
import { Cart, Checkmark } from "@openai/apps-sdk-ui/components/Icon";

// Static viewConfig extracted at build time
export const viewConfig = {
  autoResize: true,
  displayModes: ["inline", "fullscreen"],
  preferredDisplayMode: "inline",
} satisfies ViewConfig;

export default function ProductCardView() {
  const { status, toolOutput, error } = useToolContext<"get-product">();
  const { theme } = useViewTheme();
  const { add } = useModelContext();

  // Synchronize host theme with Apps SDK UI data-theme attribute
  useEffect(() => {
    if (theme) applyDocumentTheme(theme);
  }, [theme]);

  if (status === "pending") {
    return <div className="p-4 text-secondary text-sm">Loading product…</div>;
  }

  if (status === "error") {
    return <div className="p-4 text-danger text-sm">Error: {error.message}</div>;
  }

  return (
    <AppsSDKUIProvider>
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
              // Attach verified evidence to next ChatGPT model turn
              void add("selected:product", {
                type: "text",
                title: toolOutput.title,
                text: `Selected SKU ${toolOutput.sku}: $${toolOutput.price}`,
              });
            }}
          >
            <Cart className="size-4" />
            Add to Chat
          </Button>
        </div>
      </div>
    </AppsSDKUIProvider>
  );
}
```

### 3. Complete Apps SDK UI Component Suite
All components are imported from `@openai/apps-sdk-ui/components/<Component>`:

| Category | Components | Purpose & Usage |
|---|---|---|
| **Feedback & Status** | `Alert`, `Badge`, `Indicator`, `EmptyMessage`, `ShimmerText` | Callouts, status tags, live badges, empty states, and loading shimmers. |
| **Identity & Icons** | `Avatar`, `AvatarGroup`, `Image`, `Icon` | User profiles, image assets, and 700+ native monochrome icons (`@openai/apps-sdk-ui/components/Icon`). |
| **Actions** | `Button`, `ButtonLink` | Primary, secondary, soft, and outline action buttons and router links. |
| **Form Inputs** | `Input`, `Textarea`, `Checkbox`, `Switch`, `RadioGroup`, `Slider`, `SegmentedControl`, `Select`, `SelectControl`, `TagInput` | Accessible inputs with validation states, labels, and grouped controls. |
| **Date Pickers** | `DatePicker`, `DateRangePicker` | Calendar popups and date range selectors. |
| **Overlays** | `Menu`, `Popover`, `Tooltip`, `CopyTooltip` | Dropdown menus, popovers, contextual tooltips, and one-click copy buttons. |
| **Typography & Content** | `Markdown`, `CodeBlock`, `TextLink` | Styled markdown renderer, syntax-highlighted code blocks, and themed hyperlinks. |
| **Motion & Transitions** | `Transition` (`Animate`, `AnimateLayout`, `AnimateLayoutGroup`, `SlotTransitionGroup`, `TransitionGroup`) | Smooth height, fade, and layout morph transitions optimized for iframes. |
| **Providers** | `AppsSDKUIProvider` | Root context providing router `linkComponent` configuration. |

### 4. Design Tokens & Breakpoints
- **Typography Scales**: Headings: `heading-5xl`, `heading-4xl`, `heading-3xl`, `heading-2xl`, `heading-xl`, `heading-lg`, `heading-md`, `heading-sm`, `heading-xs`. Body text: `text-lg`, `text-md`, `text-sm`, `text-xs`, `text-2xs`.
- **Colors & Surfaces**: Semantic classes `bg-surface`, `bg-surface-subtle`, `text-primary`, `text-secondary`, `border-default`, `border-subtle`.
- **Dark Mode**: Set via `<html data-theme="dark">` or `applyDocumentTheme("dark")` from `@openai/apps-sdk-ui/theme`.
- **Responsive Breakpoints**: `xs: 380px`, `sm: 576px`, `md: 768px`, `lg: 1024px`, `xl: 1280px`, `2xl: 1536px`. Use `useBreakpoint("md")` from `@openai/apps-sdk-ui/hooks/useBreakpoint`.

---

## ChatGPT Plugin Extensions (Entrypoints, Settings, Context)

Documentation: [ChatGPT Extensions Guide](https://docs.mcp-use.com/v2/typescript/mcp-apps/chatgpt-extensions)

### 1. Typed Launch Entrypoints
Declare manual launch locations on `tool.view.entrypoints`:
- `global`: Launches app from top-level ChatGPT navigation (input must accept `{}`).
- `thread`: Launches app within conversation tab (input must accept `{}`).
- `file`: Launches app as file viewer for matching extensions (input receives `{ file: { name: string, resourceUri: string } }`).

```typescript
export const openCsvViewer = server.tool(
  {
    name: "open-csv",
    title: "CSV Table Viewer",
    inputSchema: z.object({
      file: z.object({
        name: z.string(),
        resourceUri: z.string(),
      }),
    }),
    outputSchema: z.object({ file: z.object({ name: z.string(), resourceUri: z.string() }) }),
    view: {
      name: "csv-viewer",
      entrypoints: [{ type: "file", extensions: [".csv"] }],
    },
  },
  async ({ file }) => ({ content: [], structuredContent: { file } })
);
```

### 2. Native Plugin Settings (`server.settings`)
Register native ChatGPT settings with typed fields, layout groups, and action tools:

```typescript
server.settings({
  fields: {
    theme: { schema: z.enum(["light", "dark", "system"]), title: "Theme" },
    autoSync: { schema: z.boolean(), title: "Automatic Sync" },
  },
  layout: [
    {
      kind: "group",
      title: "Preferences",
      items: [
        { kind: "property", property: "theme" },
        { kind: "property", property: "autoSync" },
      ],
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
  const { url } = useDeepLink();
  // url e.g. "/items?tag=hardware"
}
```

### 4. Selected Model Context (`useModelContext`)
Manage evidence attachments sent with the next user model turn:

```tsx
import { useModelContext } from "mcp-use/react";

const { attachments, add, remove, clearAttachments } = useModelContext();

// Attach text summary
await add("summary", { type: "text", title: "Order Summary", text: "Total: $120.00" });

// Attach image (PNG/JPEG/GIF/WebP, max 10MB)
await add("receipt", { type: "image", title: "Receipt", src: "/receipts/101.png" });
```

---

## Authentication & Mixed Auth

Documentation: [Authentication](https://docs.mcp-use.com/v2/typescript/server/authentication) | [Mixed Auth](https://docs.mcp-use.com/v2/typescript/server/authentication/mixed-auth)

Configure `mixedAuth: true` to serve public discovery and optional/required sign-in tools from one endpoint:

```typescript
import { MCPServer } from "mcp-use";
import { oauthClerkProvider } from "mcp-use/oauth/clerk";
import { z } from "zod";

const server = new MCPServer({
  name: "store",
  version: "1.0.0",
  oauth: oauthClerkProvider(),
  mixedAuth: true, // Enables public tools/list discovery
});

// Public tool: Anyone may call without token
export const searchCatalog = server.tool(
  {
    name: "search-catalog",
    inputSchema: z.object({ query: z.string() }),
    securitySchemes: [{ type: "noauth" }],
  },
  async ({ query }, ctx) => {
    // ctx.auth is optional (present if signed in)
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
    // ctx.auth.user is guaranteed and verified
    const userId = ctx.auth.user.id;
    return { content: [{ type: "text", text: `Order placed for user ${userId}` }] };
  }
);
```

Supported Providers: Clerk (`mcp-use/oauth/clerk`), Auth0 (`mcp-use/oauth/auth0`), WorkOS (`mcp-use/oauth/workos`), Supabase (`mcp-use/oauth/supabase`), Keycloak (`mcp-use/oauth/keycloak`), Better Auth (`mcp-use/oauth/better-auth`), Scalekit (`mcp-use/oauth/scalekit`), Convex (`mcp-use/oauth/convex`), Custom (`oauthCustomProvider` with `setup(host)` hook), and `createJwtVerifier`.

---

## Interactive Elicitation

Documentation: [Elicitation](https://docs.mcp-use.com/v2/typescript/server/elicitation)

`ctx.elicit()` was removed in v2.4.3. Use official protocol primitives:

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

    // Side-effects execute only after validated confirmation
    await db.delete(id);
    return { content: [{ type: "text", text: `Deleted ${id}` }] };
  }
);
```

For URL authorization mode: `inputRequired.elicitUrl({ message: "...", url: authUrl })`.

---

## Skills over MCP (SEP-2640)

Documentation: [Skills over MCP](https://docs.mcp-use.com/v2/typescript/server/skills)

Serve repeatable instruction workflows alongside tools:
1. Place skills under `skills/<skill-name>/SKILL.md`.
2. Automatic discovery is enabled by default. Require with `skills: true` or disable with `skills: false` on `MCPServer`.
3. Hosts retrieve skill metadata via `skills/list` and `skills/get`.

---

## CLI & Tooling Reference

Documentation: [CLI Reference](https://docs.mcp-use.com/v2/typescript/api-reference/cli-reference) | [Tunneling](https://docs.mcp-use.com/tunneling)

```bash
# Scaffold new v2 project
npx create-mcp-use-app@latest my-server --template mcp-apps

# Start development with hot reload, Vite views pipeline, and Inspector
mcp-use dev

# Start development with authenticated public tunnel for testing in ChatGPT / Claude
mcp-use dev --tunnel

# Typecheck server and views
mcp-use typecheck

# Build for production
mcp-use build

# Start production server (with optional mounted inspector)
mcp-use start
mcp-use start --with-inspector

# Connect live client session with protocol negotiation
mcp-use client connect --negotiate http://localhost:3000/mcp

# Capture automated screenshot of view preview
mcp-use screenshot <view-name> --output preview.png

# Deploy to mcp-use cloud (requires git remote on github.com)
mcp-use deploy
```

---

## Canonical Links & Reference Routing

- **Official API Base**: [MCPServer Class Reference](https://api-reference.mcp-use.com/classes/mcp-use.index.MCPServer.html)
- **Official Docs**: [docs.mcp-use.com](https://docs.mcp-use.com)
  - [Server Quickstart & Core](https://docs.mcp-use.com/v2/typescript/server)
  - [Server Migration Guide](https://docs.mcp-use.com/v2/typescript/server/migration)
  - [Server Examples](https://docs.mcp-use.com/v2/typescript/server/examples)
  - [ChatGPT Plugin Extensions](https://docs.mcp-use.com/v2/typescript/mcp-apps/chatgpt-extensions)
  - [MCP Apps Interactivity](https://docs.mcp-use.com/v2/typescript/mcp-apps/interactivity)
  - [Model Context Attachments](https://docs.mcp-use.com/v2/typescript/mcp-apps/model-context)
  - [Content Security Policy](https://docs.mcp-use.com/v2/typescript/mcp-apps/content-security-policy)
  - [Mixed Authentication](https://docs.mcp-use.com/v2/typescript/server/authentication/mixed-auth)
  - [Interactive Elicitation](https://docs.mcp-use.com/v2/typescript/server/elicitation)
  - [Skills over MCP](https://docs.mcp-use.com/v2/typescript/server/skills)
  - [CLI Reference](https://docs.mcp-use.com/v2/typescript/api-reference/cli-reference)
  - [Changelog & Breaking Changes](https://docs.mcp-use.com/typescript/changelog/changelog)
- **OpenAI Apps SDK UI**:
  - [Apps SDK UI GitHub](https://github.com/openai/apps-sdk-ui)
  - [Apps SDK UI Storybook Docs](https://openai.github.io/apps-sdk-ui/?path=/docs/overview-introduction--docs)
