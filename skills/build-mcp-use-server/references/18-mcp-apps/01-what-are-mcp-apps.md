# What Are MCP Apps

*Read this when learning how an MCP tool discovers and renders an interactive View.*

MCP Apps is the standard protocol extension for interactive user interfaces attached to MCP tools. In `mcp-use` v2, an author binds a tool to a React **View**; the CLI builds that View, the server exposes it as an MCP resource, and a capable host renders the resource in a sandboxed iframe.

## Core Terms

**MCP Apps** — the standard UI extension defined by `@modelcontextprotocol/ext-apps`.

**View** — a React module discovered at `views/<name>/view.tsx`. Its default export is the component; it may also export `viewConfig`.

**View resource** — the generated MCP resource at `ui://views/<name>.html`, with MIME type `text/html;profile=mcp-app`.

**Host** — an MCP client that negotiates the UI extension, reads the View resource, and renders it. Detect features from negotiated capabilities, not a product name. See `05-host-capability-detection.md`.

## Metadata Lifecycle

View metadata does not live on one wire object. The framework emits it across four surfaces:

| Wire surface | Framework-emitted View data |
|-|-|
| Tool descriptor from `tools/list` | Nested `_meta.ui.resourceUri`, flat compatibility `_meta["ui/resourceUri"]`, and optional `_meta.ui.visibility` |
| Successful View-bound tool result | The same nested and flat resource URI keys; not stamped on `isError: true` or `input_required` results |
| View entry from `resources/list` | URI, `text/html;profile=mcp-app`, optional description, and resource `_meta.ui` |
| View content from `resources/read` | Synthesized HTML plus resource `_meta.ui` containing merged CSP and optional permissions, domain, and border preference |

Security and sandbox facts belong to the **resource** `_meta.ui`, not to the tool result. Handler-defined result `_meta` is preserved except where framework-owned resource URI keys collide.

## Registration and Build Model

1. A tool declares `view: { name: "product-search" }` and an `outputSchema`.
2. The CLI discovers exactly `views/product-search/view.tsx`.
3. Dev or build creates a `ViewsManifest` entry for the View.
4. Tooling primes the server registry before mount.
5. The server validates tool-to-View bindings, registers the generated resource, and synthesizes its HTML when the resource is read.

`registerViews` is a publicly exported symbol because CLI/build wrappers and custom tooling integrations need it. Normal application authors do not call it: use `mcp-use dev`, `mcp-use build`, `mcp-use start`, or the Next.js adapter and default-export the `MCPServer` instance. Do not call internal priming aliases.

## Rendering Flow

1. A client discovers the tool and its View resource URI.
2. The client calls the tool.
3. The callback returns model-visible `content` and schema-validated `structuredContent`.
4. On a successful terminal result, the server stamps the View resource URI into result `_meta`.
5. The host reads `ui://views/<name>.html`; the server synthesizes HTML from the primed manifest and emits resource security metadata.
6. The host renders the View. React hooks expose tool input, structured output, result content, result metadata, and negotiated host features.

Always return a useful text fallback in `content`; clients without MCP Apps support still call and list the same tools.

## ChatGPT Compatibility

The generated server wire is standard MCP Apps. Some client-side compatibility behavior and optional submission metadata are host-specific; the framework does not generally "translate two protocols" or duplicate every metadata field. Keep standard fields authoritative and use the dedicated guides for the narrow compatibility branches:

- `chatgpt-apps/01-dual-protocol.md`
- `chatgpt-apps/03-csp-differences.md`
- `chatgpt-apps/04-runtime-detection.md`

## File and Build Shape

```text
my-server/
├── index.ts                         # Default-exports the MCPServer
├── mcp-env.d.ts                     # CLI-generated tool type registration
├── views/
│   ├── product-search/
│   │   └── view.tsx
│   └── dashboard/
│       └── view.tsx
├── public/                          # Author-owned static assets
├── .mcp-use/
│   └── build/
│       ├── index.js                 # Built server entry
│       ├── manifest.json            # Includes the ViewsManifest
│       └── views/
│           ├── product-search/assets/  # External JS/CSS build only
│           ├── dashboard/assets/
│           └── public/              # Copied public/ assets
└── package.json
```

There are no required per-View `index.html` build artifacts. The server synthesizes each HTML document during `resources/read`; inline builds store JS/CSS in the manifest instead of writing separate View bundle assets.

## v1-to-v2 Vocabulary

| v1 | v2 |
|-|-|
| `resources/<name>/widget.tsx` | `views/<name>/view.tsx` |
| `widgetMetadata` | Optional `viewConfig` plus server-side `view` resource facts |
| `useWidget()` | `useToolContext<"tool-name">()` |
| `text/html+skybridge` | `text/html;profile=mcp-app` |
| `server.uiResource()` | Tool-level `view` binding and generated resource |

## Next Steps

- Tool binding and wire keys: `server-surface/01-tool-view-field.md`
- Discovery, tooling registration, and validation: `server-surface/02-register-views-and-folder-conventions.md`
- Runtime configuration: `server-surface/03-viewconfig.md`
- Build assets and synthesized HTML: `server-surface/04-assets-mcp-url-and-serving.md`
- CSP, permissions, and domain metadata: `server-surface/05-csp-metadata.md`
- Complete worked example: `canonical-anchor.md`
