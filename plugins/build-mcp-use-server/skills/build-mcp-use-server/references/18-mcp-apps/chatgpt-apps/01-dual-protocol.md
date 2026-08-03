# ChatGPT Compatibility: One Standard Wire, Narrow Runtime Branches

*Read this when making an mcp-use v2 View work in both standard MCP Apps hosts and ChatGPT.*

mcp-use emits **one standard MCP Apps server wire**. It does not emit a second ChatGPT payload and does not auto-translate standard metadata into a parallel proprietary protocol. ChatGPT-specific behavior exists only at narrow, verified client-runtime branches and through optional OpenAI metadata extensions that you choose explicitly.

## One Server Wire

For a View-bound tool, shipped mcp-use server source emits:

- a `tools/list` descriptor with standard `_meta.ui.resourceUri`, the flat `ui/resourceUri` compatibility key, and optional `_meta.ui.visibility`;
- completed, non-error tool results stamped with the same nested and flat resource URI links;
- a generated `ui://views/<name>.html` resource with MIME `text/html;profile=mcp-app` and standard resource `_meta.ui` fields for CSP, permissions, domain, and border preference.

Source boundary: `packages/server/src/views/wire.ts` (`buildToolUiMeta`, `buildToolResultUiMeta`, and `buildResourceUiMeta`). There is no server-side Skybridge emission or ChatGPT metadata translation in those functions.

```typescript
export const search = server.tool(
  {
    name: "search",
    inputSchema: z.object({ query: z.string() }),
    outputSchema: searchOutputSchema,
    view: {
      name: "results",
      description: "Interactive search results",
      domain: "https://components.example.com",
    },
  },
  async ({ query }) => ({
    content: [{ type: "text", text: `Results for ${query}` }],
    structuredContent: { query, results: [] },
  })
);
```

The same descriptor, result, and resource shapes are read by every host.

## Verified Client-Runtime Branches

Only these ChatGPT-specific branches are present in the shipped `mcp-use/react` runtime:

1. **View state/model context** — `model-context-store.ts` restores `window.openai.widgetState.modelContent`, listens for `openai:set_globals`, and writes through `window.openai.setWidgetState`. Without that API, it uses the standard MCP Apps `App.updateModelContext()` path when the host declares `updateModelContext`.
2. **Files** — `view-runtime.ts` exposes `useFiles()` through `window.openai.uploadFile(file)` and `window.openai.getFileDownloadUrl({ fileId })` when both functions exist.

Tool calls, follow-up messages, external links, display-mode requests, size notifications, and View tools use the standard MCP Apps `App` bridge. Do not describe every mcp-use hook as a `window.openai` wrapper.

## Standard First

Use the shipped standard hooks whenever they cover the operation:

- `useToolContext()` for invocation input and results;
- `useCallTool()` for View-to-server calls;
- `useSendFollowUp()` for follow-up messages;
- `useOpenExternal()` for host-mediated links;
- `useDisplayMode()` for presentation modes;
- `useViewTool()` for host/model-to-View actions;
- `useViewState()` for state without hand-written host branching.

Use `useFiles()` only when the ChatGPT-only file extension is needed and `isSupported` is true. Do not call `window.openai` directly when a shipped standard hook exists.

## Descriptor Metadata Matrix

The official OpenAI Plugin UI reference says to prefer MCP Apps standard fields and treats the `openai/*` descriptor fields as ChatGPT compatibility aliases or optional extensions. mcp-use `ToolDefinition._meta` passes author-supplied vendor keys through to `tools/list`, except framework-owned standard View/visibility keys derived from `view` and `visibility` take precedence.

| Key | Classification | When to use | mcp-use v2 beta.66 authoring surface |
|---|---|---|---|
| `_meta.ui.resourceUri` | Standard MCP Apps | Link a tool to its UI resource | Generated from `view.name`; do not set it manually |
| `_meta.ui.visibility` | Standard MCP Apps | Make a tool model- or app-facing | Generated from top-level `visibility` |
| `_meta["openai/outputTemplate"]` | Optional ChatGPT compatibility alias | Existing integrations that still require the OpenAI alias | Can pass through `ToolDefinition._meta`; normally omit because `view.name` generates the standard key |
| `_meta["openai/widgetAccessible"]` | Optional ChatGPT compatibility field | Existing ChatGPT UI integrations | Can pass through `ToolDefinition._meta`; prefer standard visibility plus `tools/call` |
| `_meta["openai/visibility"]` | Optional ChatGPT compatibility field | Existing integrations using `public`/`private` | Can pass through `ToolDefinition._meta`; prefer top-level `visibility` |
| `_meta["openai/toolInvocation/invoking"]` | Optional ChatGPT status text | Short text while a tool runs, at most 64 characters | Can pass through `ToolDefinition._meta` |
| `_meta["openai/toolInvocation/invoked"]` | Optional ChatGPT status text | Short text after a tool completes, at most 64 characters | Can pass through `ToolDefinition._meta` |
| `_meta["openai/fileParams"]` | ChatGPT-only, use-case-specific | Declare top-level tool inputs that ChatGPT should populate with file objects | Can pass through `ToolDefinition._meta` |

Source boundary: the literal keys, status-string limit, alias classifications, and file-parameter behavior come from the official OpenAI Plugin UI reference, sections “Tool descriptor parameters” and “Define file inputs.” The pass-through boundary comes from shipped mcp-use `ToolDefinition._meta` and `buildToolUiMeta()`.

Example with optional ChatGPT descriptor extensions:

```typescript
export const analyzeFile = server.tool(
  {
    name: "analyze-file",
    inputSchema: z.object({
      file: z.object({
        download_url: z.string(),
        file_id: z.string(),
        mime_type: z.string().optional(),
        file_name: z.string().optional(),
      }),
    }),
    outputSchema: analysisSchema,
    view: { name: "analysis" },
    _meta: {
      "openai/fileParams": ["file"],
      "openai/toolInvocation/invoking": "Analyzing file…",
      "openai/toolInvocation/invoked": "Analysis ready",
    },
  },
  async ({ file }) => {
    // ChatGPT supplies download_url and file_id. Treat the URL as temporary.
    return analyzeUploadedFile(file);
  }
);
```

For each field named by `openai/fileParams`, the official OpenAI reference requires the file-object schema to declare `download_url`, `file_id`, `mime_type`, and `file_name`; only `download_url` and `file_id` are required values. A top-level file field may also be an array of that object shape.

## Resource Metadata and Current Framework Limits

| Key | Classification | mcp-use v2 beta.66 status |
|---|---|---|
| `_meta.ui.domain` | Standard, host-validated | Set through `view.domain` |
| `_meta.ui.prefersBorder` | Standard | Set through `view.prefersBorder` |
| `_meta.ui.csp` | Standard | Set through `view.csp` and merged by mcp-use |
| `_meta["openai/widgetDescription"]` | Optional ChatGPT-only resource extension | No public arbitrary generated-resource `_meta` authoring surface |
| `_meta["openai/widgetPrefersBorder"]` | Optional ChatGPT compatibility alias | Not publicly configurable on generated View resources; use `view.prefersBorder` |
| `_meta["openai/widgetDomain"]` | Optional ChatGPT compatibility alias | Not publicly configurable on generated View resources; use `view.domain` |
| `_meta["openai/widgetCSP"].redirect_domains` | ChatGPT-only redirect extension | No public generated-resource `_meta` authoring surface; see `03-csp-differences.md` |

The official OpenAI reference requires a dedicated, unique component origin when submitting a plugin with UI. Configure the standard field with `view.domain`; do not invent a ChatGPT metadata API. Host validation and submission acceptance must be checked in real ChatGPT.

`view.description` becomes the MCP resource's ordinary `description`. It does **not** author the ChatGPT-only `openai/widgetDescription` key. beta.66's generated View resource builder returns only framework-owned `_meta.ui`; therefore arbitrary resource-level OpenAI extensions are a current framework limitation.

## File API Boundary

`useFiles()` is narrower than the full official ChatGPT file API:

- wrapped: `uploadFile(file)` and `getFileDownloadUrl({ fileId })`;
- not wrapped: the upload `{ library: true }` option and `selectFiles()`;
- support is captured when the View runtime is created, so late injection of `window.openai` file methods does not update `isSupported` in beta.66.

The standard MCP Apps protocol separately defines host-mediated `ui/download-file`, but beta.66 does not expose it through a public `mcp-use/react` hook. Do not equate that standard protocol method with `useFiles()`.

## Verification Boundary

Use Inspector to validate the standard MCP Apps wire, View rendering, hook behavior over the standard bridge, and declared CSP. Current Inspector source has no verified ChatGPT protocol toggle. Its optional mock file helpers do not reproduce the full ChatGPT host lifecycle.

Verify these in real ChatGPT:

- `window.openai` state restoration and `openai:set_globals` updates;
- `useFiles()` against real uploads and temporary download URLs;
- invocation status strings and compatibility aliases;
- dedicated-domain submission acceptance;
- any ChatGPT-only resource metadata or redirect behavior.

## See Also

- `02-legacy-window-openai-and-skybridge.md` — historical APIs and migration boundaries
- `03-csp-differences.md` — standard CSP plus the remaining ChatGPT redirect extension
- `04-runtime-detection.md` — capability-first runtime decisions
- `../02-mcp-apps-vs-chatgpt-apps-sdk.md` — concise architecture comparison
