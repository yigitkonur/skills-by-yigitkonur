# Vocabulary: Views

*Read this when clarifying what "views," "MCP Apps," and related terms mean in v2.*

## Official Terminology

**Views** — React component files (`.tsx`) stored in `views/<name>/view.tsx`. Each view renders one tool's output. Exported default component + optional `viewConfig` export.

**MCP Apps** (plural, umbrella) — the complete interactive UI system in v2, including views, hooks, CSP, state management, and the MCP Apps spec. Use "MCP Apps" when discussing the framework or standards.

**View (singular)** — one React component. Renders a specific tool's structured output.

**Tool-view binding** — the link between a tool definition (`view: { name }`) and a view directory. One tool, one view. Views are optional; a tool without a `view` field is tools-only.

## Related Terminology

**Views folder** — `views/` at the server root. Contains subdirectories (one per view), each with a `view.tsx` file.

**View module** — the JavaScript export from `view.tsx` after build. Includes the default component and optional `viewConfig`.

**View resource** — the MCP resource generated at `ui://views/<name>.html`, carrying CSP metadata and pointing to the view module.

**ViewConfig** — optional immutable runtime configuration exported from `view.tsx`. Controls display modes, auto-resize, and other view-level behavior.

**Structured content** — JSON data returned by a tool (the `structuredContent` field of its result). Passed as props to the view component via `useToolContext()`.

**Model context** — the declarative description of the current view UI, assembled from `<ModelContext>` components and `useViewState()` calls, merged into one JSON snapshot with a reserved `_uiContext` key holding the serialized `<ModelContext>` tree. This is NOT sent via `_meta` — `_meta` never reaches the model (view-only channel). On MCP Apps hosts the runtime sends the merged snapshot as `structuredContent` plus a JSON text `content` block through the `ui/update-model-context` request; on ChatGPT it writes to `modelContent` via `window.openai.setWidgetState`.

## Deprecated v1 Terminology (Do Not Use)

| v1 Term | v2 Term | Why Changed |
|-|-|-|
| Widget | View | Clearer that it's a React component file, not "widget" (UI toolkit term) |
| `resources/widget.tsx` | `views/view.tsx` | Distinct folder + consistent naming |
| `widgetMetadata` | `viewConfig` | Shorter, reflects immutable configuration pattern |
| `useWidget()` hook | `useToolContext()` hook | Reflects that it reads the tool invocation context, not generic widget state |
| `widgetState` | `useViewState()` + React `useState()` | Split model-visible (former) vs. ephemeral (latter) |
| MCP Widgets | MCP Apps | Widgets was overloaded; MCP Apps is the spec name and umbrella |

## Abbreviations

- **MCP** = Model Context Protocol (the underlying wire protocol)
- **MCP Apps** = MCP Applications (interactive UI extension standard)
- **CSP** = Content Security Policy (sandbox restrictions for views)
- **View resource** = the auto-generated MCP resource for a view (`ui://views/<name>.html`); the spec's underlying metadata shape is `McpUiResourceMeta` (`csp`, `permissions`, ...) from `@modelcontextprotocol/ext-apps` — not a symbol named `UIResource` exported by mcp-use

## Authority

All v2 terminology originates from the MCP Apps specification (`@modelcontextprotocol/ext-apps`) and the mcp-use framework documentation. Use these terms consistently across all new code and documentation.
