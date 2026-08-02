# What Are MCP Apps

*Read this when learning the umbrella term for interactive UI rendering in MCP servers.*

MCP Apps is the official name for interactive, model-visible user interfaces bound to MCP tools. The MCP Apps spec (`@modelcontextprotocol/ext-apps`) defines a standard protocol extension that lets server tools declare a view (React component) to render rich output when the tool runs.

## Core Concepts

**MCP Apps** (plural) — the umbrella term for the entire interactive UI framework in v2. Do not use the v1 term "widgets."

**Views** — the React component files that render tool output. One view per tool. Stored in `views/<name>/view.tsx`.

**Spec and wire** — the MCP Apps UI standard declares a MIME type `text/html;profile=mcp-app` and a URI scheme `ui://views/<name>.html` for rendered output. Metadata travels in the tool result's `_meta.ui` field.

**Host implementations** — MCP Apps hosts (MCP Desktop, Claude, ChatGPT) understand the spec and sandboxed view resources. Views render in an iframe with CSP-enforced sandbox permissions.

## ChatGPT Also Implements MCP Apps

ChatGPT ships its own MCP Apps support via the Apps SDK. The mcp-use framework auto-translates between the standard MCP Apps spec and ChatGPT's Apps SDK extensions, so one server definition emits both protocols. See `chatgpt-apps/` files for protocol differences.

## Registration Model

- Tool declares `view: { name }` binding to a view directory.
- Tool must define `outputSchema` — the view's `structuredContent` is typed by this schema.
- Server calls `registerViews(manifest, options?)` to prime the views registry at startup.
- MCP Apps spec auto-generates view resources at `ui://views/<name>.html` with CSP and permissions metadata.

## Rendering Flow

1. Client calls the tool via MCP.
2. Tool callback returns `{ content: [...], structuredContent: {...} }` (text for model, structured data for view).
3. Host renders the view in a sandboxed iframe.
4. View receives props (from `structuredContent`) and tool context via hooks.
5. View can call other tools, update state, request display-mode changes, or send follow-up messages.

## Key Differences from v1 Widgets

| v1 | v2 |
|-|-|
| `resources/` folder + `widget.tsx` | `views/` folder + `view.tsx` |
| `widgetMetadata` export | `viewConfig?: ViewConfig` export (optional) |
| `useWidget()` hook | `useToolContext<"tool-name">()` hook |
| `text/html+skybridge` MIME | `text/html;profile=mcp-app` MIME |
| `uiResource()` server API | Tool-level `view: { name, ... }` field |
| Manual view registration | Auto-generated from `views/` and `registerViews()` |

## File Conventions

```
my-server/
├── index.ts                    # Tools with `view` field + registerViews() call
├── views/
│   ├── product-search/
│   │   └── view.tsx            # React component (default export)
│   └── dashboard/
│       └── view.tsx
├── public/                      # Static assets served at /_mcp-use/public/
├── .mcp-use/build/             # Generated at build time
│   └── views/                   # Compiled view JS/CSS
└── package.json
```

## Next Steps

- **For the server side:** See `references/18-mcp-apps/server-surface/` (01-tool-view-field.md, 02-register-views.md, etc.)
- **For the React side:** See `references/18-mcp-apps/view-react/` (01-setup.md, 02-usetoolcontext.md, etc.)
- **For ChatGPT compatibility:** See `references/18-mcp-apps/chatgpt-apps/` files.
- **For canonical example:** See `canonical-anchor.md`.
