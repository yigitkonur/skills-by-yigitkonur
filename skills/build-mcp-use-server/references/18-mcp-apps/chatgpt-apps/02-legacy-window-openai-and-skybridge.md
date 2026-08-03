# Legacy `window.openai` and Skybridge

*Read this for historical context and migration only. Do not implement these patterns in a new mcp-use v2 View.*

Before standard MCP Apps UI, ChatGPT widgets used the proprietary `text/html+skybridge` MIME type and direct `window.openai` calls. mcp-use v2 generated Views do not emit Skybridge. ChatGPT still provides selected `window.openai` capabilities, but shipped mcp-use code uses them only at narrow compatibility branches.

## Skybridge Is Not the v2 Server Wire

Legacy resource MIME:

```text
text/html+skybridge
```

mcp-use v2 generated View resource MIME:

```text
text/html;profile=mcp-app
```

Shipped source boundary: `packages/server/src/views/wire.ts` builds one `ui://views/<name>.html` MCP Apps resource and does not emit a second Skybridge resource.

Do not:

- register a duplicate Skybridge resource for ChatGPT;
- return Skybridge HTML in a tool result;
- branch in the server based on the calling host;
- describe mcp-use as merging or translating two server protocols.

## Direct State Calls Are a Legacy Implementation Pattern

Older code may contain calls such as:

```typescript
// Historical example only — do not copy into a new mcp-use View.
window.openai?.setWidgetState({
  modelContent: { selectedId: "item-1" },
});
```

Use `useViewState()` instead:

```typescript
import { useViewState } from "mcp-use/react";

const [state, setState] = useViewState({ selectedId: null as string | null });
setState((previous) => ({ ...previous, selectedId: "item-1" }));
```

Verified shipped behavior in `model-context-store.ts`:

- when a usable `window.openai.setWidgetState` exists, mcp-use restores `widgetState.modelContent`, listens for `openai:set_globals`, and writes updated `modelContent`;
- otherwise it uses standard `App.updateModelContext()` when the host declares the capability;
- the server wire is unchanged in both cases.

This is the one state compatibility branch. It does not mean every hook calls `window.openai`.

## Standard Hooks Replace Direct Host Calls

Prefer the standard mcp-use hook whenever one exists:

| Direct or legacy pattern | mcp-use v2 path |
|---|---|
| `window.openai.setWidgetState()` / `widgetState` | `useViewState()` |
| `window.openai.callTool()` | `useCallTool()` |
| `window.openai.sendFollowUpMessage()` | `useSendFollowUp()` |
| `window.openai.openExternal()` | `useOpenExternal()` |
| `window.openai.requestDisplayMode()` | `useDisplayMode()` |
| manual input/output globals | `useToolContext()` |
| `useWidget()` | `useToolContext<"tool-name">()` |
| `widgetMetadata` export | server `view` field plus optional `viewConfig` |
| `text/html+skybridge` | generated `text/html;profile=mcp-app` View resource |

The first six replacement hooks use the standard MCP Apps bridge except for the verified `useViewState()` state branch. Do not add direct `window.openai` detection to select between them.

## The Shipped File Exception Is Narrow

`useFiles()` intentionally wraps only two optional ChatGPT methods:

```typescript
const { isSupported, upload, getDownloadUrl } = useFiles();
```

Shipped `view-runtime.ts` verifies both `window.openai.uploadFile` and `window.openai.getFileDownloadUrl` before setting `isSupported`. It does not wrap the official ChatGPT `{ library: true }` upload option or `selectFiles()` helper, and it captures support when the runtime is created rather than reacting to late API injection.

The official OpenAI Plugin UI reference is the authority for the wider `window.openai` surface. That wider surface is not evidence that mcp-use wraps each method.

## Metadata Migration Is Standard-First

Legacy Apps SDK projects may contain OpenAI-namespaced descriptor or resource metadata. Migrate to standard mcp-use fields where an equivalent exists:

| ChatGPT compatibility key | Preferred mcp-use v2 field |
|---|---|
| `openai/outputTemplate` | `view.name` → generated `_meta.ui.resourceUri` |
| `openai/visibility` / `openai/widgetAccessible` | top-level `visibility` and standard tool calls |
| `openai/widgetPrefersBorder` | `view.prefersBorder` |
| `openai/widgetDomain` | `view.domain` |
| legacy `openai/widgetCSP` standard categories | `view.csp` |

Some OpenAI extensions have no standard equivalent: invocation status strings, `openai/fileParams`, `openai/widgetDescription`, and `openai/widgetCSP.redirect_domains`. Tool-descriptor extensions can pass through `ToolDefinition._meta`; generated resource extensions cannot be authored through a public arbitrary resource `_meta` surface in beta.66. See `01-dual-protocol.md` and `03-csp-differences.md` for the exact boundary.

## Migration Checklist

1. Remove Skybridge MIME/resource registration.
2. Bind the tool with `view: { name }` and declare `outputSchema`.
3. Replace direct standard-equivalent host calls with mcp-use hooks.
4. Keep `useFiles()` capability-gated if the app needs the shipped ChatGPT file subset.
5. Move standard metadata to `view`, `visibility`, and other top-level mcp-use fields.
6. Add only the ChatGPT-specific tool `_meta` extensions the use case requires.
7. Treat unsupported resource-level OpenAI extensions as framework limitations, not hidden configuration fields.
8. Validate the standard View in Inspector, then validate ChatGPT-specific behavior in real ChatGPT.

See `references/28-migration/06-v1-to-v2-widgets-to-views.md` for the broader v1-to-v2 migration flow.
