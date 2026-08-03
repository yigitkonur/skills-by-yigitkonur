# MCP Apps and ChatGPT Compatibility in mcp-use v2

*Read this when deciding what is standard, what is ChatGPT-only, and what mcp-use actually abstracts.*

mcp-use v2 is standard-first: the server emits one MCP Apps descriptor/result/resource wire for every host. ChatGPT does not receive a second generated payload. Compatibility comes from ChatGPT accepting the standard UI fields, two narrow client-runtime branches in `mcp-use/react`, and optional OpenAI extensions that an author may add when a ChatGPT-specific use case requires them.

## Architecture at a Glance

| Concern | Shipped mcp-use behavior | Classification |
|---|---|---|
| Tool/View link | `view.name` generates `_meta.ui.resourceUri` and flat `ui/resourceUri` | Standard MCP Apps |
| View resource | `ui://views/<name>.html`, `text/html;profile=mcp-app` | Standard MCP Apps |
| Resource policy | `view.csp`, `view.permissions`, `view.domain`, `view.prefersBorder` become resource `_meta.ui` | Standard MCP Apps |
| Tool result | `structuredContent`, `content`, result `_meta`; successful View-bound results get resource URI links | Standard MCP |
| State/model context | Standard `App.updateModelContext()`; ChatGPT branch uses `setWidgetState` and `openai:set_globals` | Standard path plus verified ChatGPT runtime branch |
| View files | `useFiles()` wraps only ChatGPT upload and temporary-download-URL methods | ChatGPT-only shipped subset |
| Other View interactions | Tool calls, follow-ups, links, display modes, size changes, View tools | Standard MCP Apps bridge |
| OpenAI descriptor extensions | Explicit `openai/*` keys in `ToolDefinition._meta` | Optional/use-case-specific ChatGPT metadata |
| OpenAI resource extensions | No public arbitrary generated-resource `_meta` authoring surface in beta.66 | Current framework limitation |

Server wire authority: shipped `packages/server/src/views/wire.ts`. Runtime branch authority: shipped `model-context-store.ts`, `view-runtime.ts`, and `use-files.ts`. ChatGPT extension authority: the official OpenAI Plugin UI reference.

## No Auto-Translation Layer

Do not describe mcp-use as doing any of the following:

- emitting both MCP Apps and ChatGPT protocols;
- converting `_meta.ui.visibility` into widget-state hints;
- placing HTML resource content or CSP on a tool result;
- generating OpenAI aliases from standard metadata;
- routing every React hook through `window.openai`.

The server emits one standard shape. `buildToolUiMeta()` preserves author tool `_meta` keys while deriving framework-owned resource URI and visibility fields. `buildResourceUiMeta()` emits only standard resource `_meta.ui` fields.

## Standard Hooks First

Write Views against `mcp-use/react`:

```typescript
import {
  useCallTool,
  useDisplayMode,
  useOpenExternal,
  useSendFollowUp,
  useToolContext,
  useViewState,
  useViewTool,
} from "mcp-use/react";
```

These standard hooks keep View code host-independent. `useViewState()` contains the verified ChatGPT state fallback internally. `useFiles()` is the explicit exception because it represents the narrower ChatGPT file extension.

## Optional ChatGPT Tool Metadata

The official OpenAI reference prefers standard `_meta.ui.resourceUri` and `_meta.ui.visibility`. Add OpenAI-namespaced descriptor metadata only when it serves a ChatGPT-specific purpose:

```typescript
server.tool(
  {
    name: "analyze-file",
    inputSchema: fileInputSchema,
    outputSchema: analysisSchema,
    view: { name: "analysis" },
    _meta: {
      "openai/fileParams": ["file"],
      "openai/toolInvocation/invoking": "Analyzing file…",
      "openai/toolInvocation/invoked": "Analysis ready",
    },
  },
  analyzeFile
);
```

Literal descriptor keys documented by the official OpenAI Plugin UI reference:

| Key | Classification |
|---|---|
| `openai/outputTemplate` | Optional compatibility alias for standard `_meta.ui.resourceUri` |
| `openai/widgetAccessible` | Optional compatibility field for existing UI integrations; prefer standard visibility/tool calls |
| `openai/visibility` | Optional compatibility field; prefer standard `_meta.ui.visibility` |
| `openai/toolInvocation/invoking` | Optional ChatGPT status text, at most 64 characters |
| `openai/toolInvocation/invoked` | Optional ChatGPT status text, at most 64 characters |
| `openai/fileParams` | ChatGPT-only declaration of top-level file input fields |

All can pass through `ToolDefinition._meta`. Do not manually set framework-owned standard View or visibility keys there; use `view` and `visibility`.

For `openai/fileParams`, the official reference requires each listed input field to resolve to a file object or array of file objects whose schema declares `download_url`, `file_id`, `mime_type`, and `file_name`. Only `download_url` and `file_id` are required values.

## Resource Metadata and Submission

Use the standard fields mcp-use exposes:

```typescript
view: {
  name: "results",
  description: "Interactive result browser",
  domain: "https://components.example.com",
  prefersBorder: true,
  csp: {
    connectDomains: ["https://api.example.com"],
  },
}
```

The official OpenAI reference says `_meta.ui.domain` is required for ChatGPT plugin submission with UI and must identify a dedicated origin unique to the plugin. Configure it with `view.domain` and verify submission in real ChatGPT.

The same reference documents optional resource extensions:

- `openai/widgetDescription`;
- compatibility aliases `openai/widgetPrefersBorder` and `openai/widgetDomain`;
- `openai/widgetCSP.redirect_domains` for trusted `window.openai.openExternal` redirect targets.

Generated mcp-use View resources in beta.66 do not expose a public arbitrary resource `_meta` authoring surface. `view.description` is the ordinary MCP resource description, not `openai/widgetDescription`. Use standard `view.prefersBorder`, `view.domain`, and `view.csp`; treat the remaining ChatGPT-only resource keys as framework limitations rather than inventing configuration.

For ordinary links, use `useOpenExternal()`, which follows the standard `App.openLink()` path. Do not replace it with direct `window.openai.openExternal` code.

## File Compatibility Boundary

`useFiles()` exposes only:

- `upload(file)` → ChatGPT `uploadFile(file)`;
- `getDownloadUrl({ fileId })` → ChatGPT `getFileDownloadUrl({ fileId })`;
- `isSupported`, true only when both methods were present when the runtime was created.

It does not wrap the official `{ library: true }` upload option or `selectFiles()`. Late injection does not update support in beta.66.

The standard MCP Apps protocol has a separate `ui/download-file` operation, but beta.66 has no public `mcp-use/react` hook for it. Do not claim `useFiles()` is a cross-host file abstraction.

## Verification

Inspector is the right place to validate:

- standard tool/resource/result metadata;
- View rendering and standard hook calls;
- host capability gating;
- layout and display modes;
- CSP in Permissive and Widget-Declared modes.

Current Inspector source does not provide a verified ChatGPT host-protocol toggle. Mock file helpers, when present, are not real ChatGPT emulation.

Use real ChatGPT to validate the state branch, file extension, invocation strings, optional aliases, dedicated-domain submission, and any ChatGPT-only redirect behavior.

## Further Reading

- `chatgpt-apps/01-dual-protocol.md` — detailed metadata matrix and source boundaries
- `chatgpt-apps/02-legacy-window-openai-and-skybridge.md` — historical and negative guidance
- `chatgpt-apps/03-csp-differences.md` — standard CSP plus redirect extension
- `chatgpt-apps/04-runtime-detection.md` — capability-first runtime decisions
