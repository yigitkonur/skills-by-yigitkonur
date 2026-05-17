# Vocabulary

One-paragraph definitions for every term used across the `18-mcp-apps/` cluster. Bookmark this page when terms feel overloaded.

## Widget

The interactive UI component rendered by the host inside a sandboxed iframe in response to a tool call. "Widget" and "MCP App" refer to the same artifact; the term you'll see most often in mcp-use APIs is **widget**. A widget is just a React tree (or any JS) that renders into the iframe's `<div id="root">`.

## MCP App

The protocol-level name for an interactive widget delivered through the Model Context Protocol. SEP-1865 standardizes this. The server registers a `uiResource` with MIME `text/html;profile=mcp-app`; the host loads it into an iframe and exchanges JSON-RPC over `postMessage`.

## ChatGPT App

The OpenAI Apps SDK rendition of the same idea: a widget delivered to ChatGPT via the `text/html+skybridge` MIME type and the `window.openai.*` global API. mcp-use treats this as a second backend for the same widget code — registering with `type: "mcpApps"` produces both variants.

## UI resource

The HTML/template/script entry point registered on the server for a widget. Created via `server.uiResource(...)` with type-specific content fields such as `htmlTemplate` (`mcpApps` / `appsSdk`), `htmlContent` (`rawHtml`), or `script` (`remoteDom`). The host loads this into the iframe; the widget mounts inside it.

## `widget()` helper

Server-side function imported from `mcp-use/server`. Builds a `CallToolResult` with `props` (rendering data, becomes `structuredContent`), `output`/`message` (LLM-visible text, becomes `content`), and `metadata` (UI-only hydration, becomes `_meta`). Documented in detail at `server-surface/01-widget-helper.md`.

## `widgetMetadata`

The named export from a widget's `widget.tsx` file. Type `WidgetMetadata`. Carries optional `title`, `description`, `props` (preferred Zod schema or input descriptors), `toolOutput`, `exposeAsTool`, `appsSdkMetadata`, and unified `metadata` (CSP, `prefersBorder`, `domain`, `widgetDescription`, `autoResize`, `invoking`, `invoked`). The dev tooling reads this at startup to generate types and configure the host. Documented at `server-surface/06-widget-metadata-export.md`.

## Tool `widget` config

The optional `widget: { name, invoking?, invoked?, widgetAccessible?, resultCanProduceWidget? }` field on `server.tool()`. Links a tool to a widget by name; sets the status text and ChatGPT tool metadata for widget-capable results. The `name` must match a discovered `resources/<name>/widget.tsx` directory or a manual `server.uiResource({ name })`. Documented at `server-surface/03-tool-widget-config.md`.

## `useWidget`

Client-side React hook from `mcp-use/react`. Exposes a unified, protocol-agnostic API for the widget: `props`, `metadata`, `state`/`setState`, `callTool`, `sendFollowUpMessage`, `requestDisplayMode`, host context (`theme`, `locale`, `timeZone`, `safeArea`, `userAgent`), and lifecycle flags (`isPending`, `isStreaming`, `partialToolInput`). Detailed in the `widget-react/` cluster.

## `useCallTool`

Client-side hook for invoking server tools from inside a widget. Discriminated-union state machine (`idle | pending | success | error`) similar to TanStack Query. Two call modes: fire-and-forget `callTool(args, { onSuccess, onError })` and async `callToolAsync(args)`. Detailed in `widget-react/`.

## Bridge

The transport layer between the iframe widget and the host. mcp-use selects automatically: `McpAppsAdapter` over `postMessage` JSON-RPC for MCP Apps, `AppsSdkAdapter` over `window.openai` for ChatGPT. Widget code should normally stay on `useWidget` / `useCallTool` instead of touching the bridge directly.

## CSP (Content Security Policy)

The browser-level allowlist controlling which domains the iframe may fetch from, load scripts/styles from, embed, or be redirected to. Configured in `widgetMetadata.metadata.csp` using camelCase fields; mcp-use injects the server's own `baseUrl` automatically and converts to snake_case for ChatGPT. Documented at `server-surface/05-csp-metadata.md`.

## `baseUrl` / `MCP_URL`

Server-config or env value telling mcp-use where the deployed widget assets and MCP endpoint live. Auto-injected into widget CSP and used by the `<Image />` component for path resolution. Documented at `server-surface/04-baseurl-and-asset-serving.md`.

## `resources/<name>/widget.tsx`

The filesystem convention for auto-discovered widgets. The directory name **is** the widget name. Each `widget.tsx` exports a default React component plus `widgetMetadata`. Auto-registration replaces the need for manual `server.uiResource()` for the common case. Documented at `server-surface/07-resources-folder-conventions.md`.

## `exposeAsTool`

Field on `widgetMetadata` and `server.uiResource()`. When `true`, mcp-use auto-registers the widget as a callable tool using `props` as the input schema; set it to `false` when a custom `server.tool()` returns the widget with computed `props`.
