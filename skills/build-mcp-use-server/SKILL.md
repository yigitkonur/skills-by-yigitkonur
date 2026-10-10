---
name: build-mcp-use-server
description: "Use skill if you are building TypeScript MCP servers with mcp-use v2 — MCPServer base, OpenAI Apps SDK UI compliance, views, settings, mixed auth, elicitation, and migrations."
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

## Intent Routing & Migration Matrix

When migrating existing codebases, widgets, SDK implementations, or APIs, route directly to the authoritative reference guide:

| Developer Intent / Migration Vector | Key Symptoms or Legacy Signatures | Authoritative Guide File |
|---|---|---|
| **Vector 1: Full v1 → v2 Migration Overview** | Upgrading `mcp-use` 1.x server, reviewing breaking changes, upgrade checklist | `references/28-migration/02-v1-to-v2-overview.md` |
| **Vector 1: Imports, Server & Tools** | `Cannot find module 'mcp-use/server'`, Zod v3 schema errors, unexported tool refs | `references/28-migration/03-v1-to-v2-imports-server-and-tools.md` |
| **Vector 1: Responses & Result Envelopes** | Deprecated `text()`, `object()`, `widget()`, invalid CallToolResult shape | `references/28-migration/04-v1-to-v2-responses-and-helpers.md` |
| **Vector 1: Auth & OAuth Migration** | `ctx.auth.user.userId` undefined, `oauthProxy` missing, configuring `mixedAuth` | `references/28-migration/05-v1-to-v2-auth.md` |
| **Vector 1: Widgets → MCP Apps Views** | `resources/<name>/widget.tsx`, `useWidget`, `@mcp-use/react` not found | `references/28-migration/06-v1-to-v2-widgets-to-views.md` |
| **Vector 1: Stateless Transports & Stdio** | `stdio: true` failed, SSE session stores, `ctx.session` undefined | `references/28-migration/07-v1-to-v2-sessions-transports-stdio-sse.md` |
| **Vector 2: Raw `@modelcontextprotocol/sdk` → v2** | `new Server()`, `setRequestHandler()`, `StdioServerTransport`, manual JSON-RPC | `references/28-migration/01-from-modelcontextprotocol-sdk.md` |
| **Vector 3: ChatGPT Widgets → MCP Apps & Apps SDK UI** | `window.openai`, `text/html+skybridge`, raw CSS, `openai/fileParams` | `references/28-migration/08-appssdk-to-mcp-apps.md` |
| **Vector 4: REST APIs & OpenAPI Specifications → v2** | Converting REST endpoints, Swagger/OpenAPI specs, auth pass-through | `references/28-migration/09-openapi-and-rest-to-tools.md` |
| **Vector 5: Interactive Elicitation & State Evolution** | `ctx.elicit is not a function`, `ctx.sample`, multi-round state integrity | `references/28-migration/10-elicitation-and-state-evolution.md` |

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

### Reference Catalog

- **Core guides:** `references/server.md`, `references/chatgpt-apps-ui.md`, `references/chatgpt-extensions.md`
- **Root hubs:** `references/00-reference-index.md`, `references/00-symptom-index.md`, `references/00-version-drift.md`
- **01 Concepts:** `references/01-concepts/01-what-is-mcp-use.md`, `references/01-concepts/02-server-vs-client-vs-agent.md`, `references/01-concepts/03-transports-overview.md`, `references/01-concepts/04-stateless-model-and-request-state.md`, `references/01-concepts/05-mcp-spec-version-history.md`, `references/01-concepts/06-mcp-apps-and-views-terminology.md`, `references/01-concepts/07-this-skill-vs-build-mcp-use-client.md`
- **02 Setup:** `references/02-setup/01-prerequisites.md`, `references/02-setup/02-scaffold-with-create-mcp-use-app.md`, `references/02-setup/03-template-flags.md`, `references/02-setup/04-manual-http-server.md`, `references/02-setup/05-add-to-existing-app.md`, `references/02-setup/06-package-scripts.md`, `references/02-setup/07-tsconfig-and-types.md`, `references/02-setup/08-env-vars.md`
- **03 CLI:** `references/03-cli/01-overview.md`, `references/03-cli/02-create-mcp-use-app.md`, `references/03-cli/03-mcp-use-dev.md`, `references/03-cli/04-mcp-use-build-and-typecheck.md`, `references/03-cli/05-mcp-use-start.md`, `references/03-cli/06-mcp-use-deploy-and-cloud.md`, `references/03-cli/07-login-and-org.md`, `references/03-cli/08-client-and-screenshot.md`, `references/03-cli/09-flag-reference.md`, `references/03-cli/10-environment-variables.md`
- **04 Tools:** `references/04-tools/01-overview.md`, `references/04-tools/02-registering-a-tool.md`, `references/04-tools/03-schemas-standard-schema-and-zod-v4.md`, `references/04-tools/04-describe-and-annotations.md`, `references/04-tools/05-the-ctx-object.md`, `references/04-tools/06-validation-pipeline.md`, `references/04-tools/07-input-schema-vs-output-schema.md`, `references/04-tools/08-tool-anti-patterns.md`, `references/04-tools/canonical-anchor.md`
- **05 Responses:** `references/05-responses/01-overview-decision-table.md`, `references/05-responses/02-text-and-content-blocks.md`, `references/05-responses/03-structured-content-and-output-schema.md`, `references/05-responses/04-images-audio-binary-resources.md`, `references/05-responses/05-error-handling.md`, `references/05-responses/06-meta-and-private-data.md`, `references/05-responses/07-deprecated-v1-helpers.md`, `references/05-responses/canonical-anchor.md`
- **06 Resources:** `references/06-resources/01-overview.md`, `references/06-resources/02-static-resources.md`, `references/06-resources/03-resource-templates.md`, `references/06-resources/04-binary-and-image.md`, `references/06-resources/05-uri-conventions.md`, `references/06-resources/06-subscriptions-listen.md`, `references/06-resources/canonical-anchor.md`
- **07 Prompts:** `references/07-prompts/01-overview.md`, `references/07-prompts/02-static-prompts.md`, `references/07-prompts/03-prompt-templates.md`, `references/07-prompts/04-completable-arguments.md`, `references/07-prompts/05-prompt-engineering.md`
- **08 Server config:** `references/08-server-config/01-mcp-server-constructor.md`, `references/08-server-config/02-network-basepath-and-endpoints.md`, `references/08-server-config/03-cors-and-allowed-origins.md`, `references/08-server-config/04-dns-rebinding-and-host-validation.md`, `references/08-server-config/05-middleware.md`, `references/08-server-config/06-custom-routes.md`, `references/08-server-config/07-lifecycle-listen-fetch-shutdown.md`
- **09 Transports:** `references/09-transports/01-overview.md`, `references/09-transports/02-streamable-http.md`, `references/09-transports/03-stateless-and-request-state.md`, `references/09-transports/04-runtime-adapters-node-next-fetch.md`, `references/09-transports/05-no-stdio-and-sse-history.md`
- **10 Sessions & state:** `references/10-sessions/01-overview-stateless-truth.md`, `references/10-sessions/02-session-storage-roadmap.md`, `references/10-sessions/03-state-patterns-without-sessions.md`, `references/10-sessions/04-multi-instance-and-scaling.md`
- **11 Auth:** `references/11-auth/01-overview.md`, `references/11-auth/02-attaching-a-provider.md`, `references/11-auth/03-ctx-auth-and-user-context.md`, `references/11-auth/04-permission-guards.md`, `references/11-auth/05-custom-provider-oauthcustomprovider.md`, `references/11-auth/06-debugging-checklist.md`, `references/11-auth/07-oauth-proxy-removed.md`, `references/11-auth/providers/01-clerk.md`, `references/11-auth/providers/02-auth0.md`, `references/11-auth/providers/03-workos.md`, `references/11-auth/providers/04-supabase.md`, `references/11-auth/providers/05-keycloak.md`, `references/11-auth/providers/06-better-auth.md`, `references/11-auth/providers/07-scalekit.md`, `references/11-auth/providers/08-convex.md`
- **12 Elicitation:** `references/12-elicitation/01-overview.md`, `references/12-elicitation/02-form-mode.md`, `references/12-elicitation/03-url-mode.md`, `references/12-elicitation/04-multi-round-and-request-state.md`, `references/12-elicitation/05-anti-patterns.md`
- **13 Sampling:** `references/13-sampling/01-sampling-removed-in-v2.md`
- **14 Notifications:** `references/14-notifications/01-overview.md`, `references/14-notifications/02-ctx-sendnotification.md`, `references/14-notifications/03-progress-reporting.md`, `references/14-notifications/04-list-changed-events.md`, `references/14-notifications/05-subscriptions-delivery.md`, `references/14-notifications/canonical-anchor.md`
- **15 Logging:** `references/15-logging/01-overview.md`, `references/15-logging/02-ctx-sendlog.md`, `references/15-logging/03-server-and-request-logging.md`
- **16 Client introspection:** `references/16-client-introspection/01-overview.md`, `references/16-client-introspection/02-capabilities.md`, `references/16-client-introspection/03-apps-detection.md`, `references/16-client-introspection/canonical-anchor.md`
- **17 Advanced:** `references/17-advanced/01-proxy-and-gateway.md`, `references/17-advanced/02-proxy-auth-and-namespacing.md`, `references/17-advanced/03-openapi-fromopenapi.md`, `references/17-advanced/04-mcp-use-vs-official-sdk.md`, `references/17-advanced/canonical-anchor.md`
- **18 MCP Apps views:** `references/18-mcp-apps/01-what-are-mcp-apps.md`, `references/18-mcp-apps/02-mcp-apps-vs-chatgpt-apps-sdk.md`, `references/18-mcp-apps/03-vocabulary-views.md`, `references/18-mcp-apps/04-when-to-use-vs-tools-only.md`, `references/18-mcp-apps/05-host-capability-detection.md`, `references/18-mcp-apps/anti-patterns.md`, `references/18-mcp-apps/canonical-anchor.md`
- **18 MCP Apps server surface:** `references/18-mcp-apps/server-surface/01-tool-view-field.md`, `references/18-mcp-apps/server-surface/02-register-views-and-folder-conventions.md`, `references/18-mcp-apps/server-surface/03-viewconfig.md`, `references/18-mcp-apps/server-surface/04-assets-mcp-url-and-serving.md`, `references/18-mcp-apps/server-surface/05-csp-metadata.md`
- **18 MCP Apps React:** `references/18-mcp-apps/view-react/01-setup-and-providers.md`, `references/18-mcp-apps/view-react/02-usetoolcontext.md`, `references/18-mcp-apps/view-react/03-usecalltool.md`, `references/18-mcp-apps/view-react/04-useviewstate-and-model-context.md`, `references/18-mcp-apps/view-react/05-display-modes.md`, `references/18-mcp-apps/view-react/06-followups-and-open-external.md`, `references/18-mcp-apps/view-react/07-host-context-files-and-size.md`, `references/18-mcp-apps/view-react/08-theme-and-components.md`, `references/18-mcp-apps/view-react/09-useviewtool.md`
- **18 ChatGPT apps:** `references/18-mcp-apps/chatgpt-apps/01-dual-protocol.md`, `references/18-mcp-apps/chatgpt-apps/02-legacy-window-openai-and-skybridge.md`, `references/18-mcp-apps/chatgpt-apps/03-csp-differences.md`, `references/18-mcp-apps/chatgpt-apps/04-runtime-detection.md`
- **19 Next.js:** `references/19-nextjs-drop-in/01-overview-withmcpuse.md`, `references/19-nextjs-drop-in/02-route-and-file-placement.md`, `references/19-nextjs-drop-in/03-views-in-nextjs.md`, `references/19-nextjs-drop-in/04-deploying-on-vercel.md`
- **20 Inspector:** `references/20-inspector/01-overview.md`, `references/20-inspector/02-cli.md`, `references/20-inspector/03-connection-settings.md`, `references/20-inspector/04-url-parameters.md`, `references/20-inspector/05-keyboard-shortcuts-and-palette.md`, `references/20-inspector/06-integration-and-add-to-client.md`, `references/20-inspector/07-self-hosting.md`, `references/20-inspector/08-debugging-chatgpt-apps.md`, `references/20-inspector/09-changelog-pointer.md`
- **21 Tunneling:** `references/21-tunneling/01-overview.md`, `references/21-tunneling/02-when-to-tunnel-and-debugging.md`
- **22 Validate:** `references/22-validate/01-inspector-walkthrough.md`, `references/22-validate/02-curl-handshake.md`, `references/22-validate/03-connect-real-clients.md`, `references/22-validate/04-unit-testing-server-fetch.md`
- **23 Debug:** `references/23-debug/01-debugging-workflow.md`, `references/23-debug/02-transport-debugging.md`, `references/23-debug/03-view-debugging.md`
- **24 Production:** `references/24-production/01-env-config.md`, `references/24-production/02-error-strategy.md`, `references/24-production/03-health-and-custom-routes.md`, `references/24-production/04-security-hardening.md`, `references/24-production/05-scaling-stateless.md`
- **25 Deploy:** `references/25-deploy/01-decision-matrix.md`, `references/25-deploy/02-pre-deploy-checklist.md`, `references/25-deploy/03-docker.md`, `references/25-deploy/04-cli-and-org-management.md`, `references/25-deploy/platforms/01-mcp-use-cloud.md`, `references/25-deploy/platforms/02-vercel.md`, `references/25-deploy/platforms/03-cloudflare-workers.md`, `references/25-deploy/platforms/04-google-cloud-run.md`, `references/25-deploy/platforms/05-supabase.md`, `references/25-deploy/platforms/06-deno.md`, `references/25-deploy/platforms/07-bun.md`, `references/25-deploy/platforms/08-hono.md`, `references/25-deploy/platforms/09-railway.md`, `references/25-deploy/platforms/10-runtime-patterns.md`
- **26 Anti-patterns:** `references/26-anti-patterns/01-sdk-misuse.md`, `references/26-anti-patterns/02-tool-design.md`, `references/26-anti-patterns/03-schemas.md`, `references/26-anti-patterns/04-results.md`, `references/26-anti-patterns/05-security-and-cors.md`
- **27 Troubleshooting:** `references/27-troubleshooting/01-error-catalog.md`, `references/27-troubleshooting/02-quick-diagnostic-table.md`, `references/27-troubleshooting/03-oauth-issues.md`, `references/27-troubleshooting/04-view-rendering-issues.md`, `references/27-troubleshooting/05-csp-violations.md`, `references/27-troubleshooting/06-decision-tree.md`
- **28 Migration:** `references/28-migration/01-from-modelcontextprotocol-sdk.md`, `references/28-migration/02-v1-to-v2-overview.md`, `references/28-migration/03-v1-to-v2-imports-server-and-tools.md`, `references/28-migration/04-v1-to-v2-responses-and-helpers.md`, `references/28-migration/05-v1-to-v2-auth.md`, `references/28-migration/06-v1-to-v2-widgets-to-views.md`, `references/28-migration/07-v1-to-v2-sessions-transports-stdio-sse.md`, `references/28-migration/08-appssdk-to-mcp-apps.md`, `references/28-migration/09-openapi-and-rest-to-tools.md`, `references/28-migration/10-elicitation-and-state-evolution.md`
- **29 Templates:** `references/29-templates/01-overview-and-decision-matrix.md`, `references/29-templates/02-template-mcp-server.md`, `references/29-templates/03-template-mcp-apps.md`, `references/29-templates/04-template-blank-and-manual.md`
- **30 Workflows:** `references/30-workflows/01-greenfield-tool-server-to-vercel.md`, `references/30-workflows/02-views-app-chart-widget.md`, `references/30-workflows/03-oauth-protected-server-clerk.md`, `references/30-workflows/04-supabase-oauth-and-deploy.md`, `references/30-workflows/05-nextjs-drop-in.md`, `references/30-workflows/06-openapi-to-mcp.md`, `references/30-workflows/07-proxy-gateway.md`, `references/30-workflows/08-elicitation-input-required-flow.md`
- **31 Canonical examples:** `references/31-canonical-examples/00-how-to-use-this-cluster.md`, `references/31-canonical-examples/01-chart-builder.md`, `references/31-canonical-examples/02-diagram-builder.md`, `references/31-canonical-examples/03-example-inventory.md`
