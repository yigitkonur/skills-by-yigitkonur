# Debugging MCP Apps Views and ChatGPT Compatibility

*Read this when verifying a View's standard MCP Apps behavior locally and its ChatGPT-specific behavior in the real host.*

Inspector is authoritative for the standard MCP Apps path it implements. It is not a ChatGPT emulator: current Inspector source has MCP Apps View controls and CSP diagnostics, but no verified MCP Apps-versus-ChatGPT host protocol toggle.

## Connect and Run a View-Backed Tool

For the CLI-owned development listener:

1. Start the project through its normal `mcp-use dev` script.
2. Open `<basePath>/inspector` (commonly `http://localhost:3000/mcp/inspector`).
3. Connect to the MCP endpoint (commonly `http://localhost:3000/mcp`).
4. Open **Tools**, select the View-backed tool, and call it with minimal valid input.

Direct `server.listen()`, `server.fetch`, and embedded Next.js handlers do not auto-mount Inspector. Use the external Inspector for those topologies, for example:

```bash
npx @mcp-use/inspector --url <mcp-url>
```

If no View appears, check:

- the tool's `view.name` matches `views/<name>/view.tsx`;
- the tool declares `outputSchema`;
- returned `structuredContent` matches that schema;
- the generated `ui://views/<name>.html` resource can be read;
- View compilation, asset, iframe, or runtime errors.

## What Inspector Proves

Use Inspector to verify the standard server wire and standard View runtime:

| Surface | Check |
|---|---|
| Tool descriptor | Standard `_meta.ui.resourceUri`, flat `ui/resourceUri`, and optional `_meta.ui.visibility` |
| Tool result | `content`, schema-valid `structuredContent`, result `_meta`, and stamped resource URI links on successful View-bound results |
| View resource | `text/html;profile=mcp-app`, `ui://views/<name>.html`, and standard resource `_meta.ui` |
| Host bridge | Standard capability gating for tool calls, messages, links, display modes, and other MCP Apps operations |
| Rendering | Ready/loading/error branches, assets, theme, sizing, safe area, and interaction behavior |
| CSP | Permissive diagnostics and Widget-Declared enforcement |

Some Inspector labels may still say “widget.” Map them to the v2 View contract; do not look for v1 `props`, `useWidget()`, or Skybridge resources.

## What Inspector Does Not Prove

Do not claim local Inspector verifies:

- real `window.openai.widgetState` restoration;
- real `openai:set_globals` timing;
- `window.openai.setWidgetState` persistence across ChatGPT renders;
- real ChatGPT file upload, file-library access, or temporary URL behavior;
- ChatGPT invocation status presentation;
- compatibility aliases;
- dedicated-domain submission acceptance;
- `openai/widgetCSP.redirect_domains` or other ChatGPT-only resource metadata.

Inspector source can supply optional mock OpenAI file helpers in an MCP Apps host. That is useful for exercising a local UI branch, but it is not a second host protocol and does not reproduce ChatGPT permissions, injection timing, persistence, library availability, or review policy.

A connection control for MCP protocol version changes MCP wire-version negotiation. It is not ChatGPT emulation.

## Inspect Input, Output, and Metadata

Compare the raw tool call/result with the View:

| Data | What to verify |
|---|---|
| Tool input | Complete and partial input appear through `useToolContext()` as expected |
| `structuredContent` | Matches `outputSchema` and the data the View renders |
| Text `content` | Provides a useful model/transcript fallback |
| Result `_meta` | Contains only View-private invocation data; no secrets intended for the model |
| View state | Contains only serializable UI/model-context state intended to persist |

Remember that framework-stamped resource URI keys may be present in delivered result `_meta` for a successful View-bound tool.

## Test Standard Host Interactions

Exercise each used hook over the standard bridge:

- `useCallTool()` for View-to-server tool calls;
- `useSendFollowUp()` when `hostCapabilities.message` is present;
- `useOpenExternal()` when `hostCapabilities.openLinks` is present;
- `useDisplayMode()` for requested and granted modes;
- `useSendSizeChanged()` for intrinsic sizing;
- `useViewTool()` for host/model-to-mounted-View actions;
- `useViewState()` for local state and standard model-context updates.

Gate each optional operation on its specific capability. Do not use `hostInfo.name` as a substitute.

## Test Layout and Display Modes

Use Inspector controls to exercise:

- inline, picture-in-picture, and fullscreen presentation;
- desktop, tablet, and mobile sizes;
- touch and hover assumptions;
- light and dark themes;
- locale and timezone formatting;
- safe-area insets.

The host may grant a different display mode from the one requested. Read the actual mode from `useDisplayMode()`.

## Test Declared CSP

Current Inspector source exposes:

- **Permissive** mode, which records would-be policy blocks;
- **Widget-Declared** mode, which enforces the resource metadata policy.

Test Widget-Declared mode before release. If a View works only in Permissive mode, inspect browser requests and map them to:

- `connectDomains` for browser fetch/XHR/WebSocket;
- `resourceDomains` for static assets;
- `frameDomains` for nested frames;
- `baseUriDomains` for `<base>` targets.

View CSP applies to the iframe, not to server-side tool callback fetches.

Inspector CSP checks validate standard `_meta.ui.csp`. They do not validate ChatGPT's remaining `openai/widgetCSP.redirect_domains` extension, which generated mcp-use View resources cannot author through a public arbitrary resource `_meta` surface in beta.66.

## Verify in Real ChatGPT

After the standard flow is green, connect the deployed HTTPS MCP server to real ChatGPT and verify the ChatGPT-only boundary:

1. Confirm the View loads from the same standard resource wire.
2. Change `useViewState()` state, remount/reinvoke as appropriate, and verify restoration and follow-up model context.
3. If using files, verify `useFiles().isSupported`, a real upload, and a fresh download URL.
4. Verify tools using `openai/fileParams` receive the documented snake_case file object fields.
5. Observe optional `openai/toolInvocation/invoking` and `openai/toolInvocation/invoked` strings.
6. Confirm the dedicated `view.domain` origin satisfies ChatGPT submission/review requirements.
7. Test every external-link and redirect flow in the actual host.

The literal ChatGPT metadata and file-schema requirements come from the official OpenAI Plugin UI reference. The availability of those keys in `ToolDefinition._meta` comes from shipped mcp-use tool types and `buildToolUiMeta()` pass-through behavior.

## Known beta.66 Limits to Record

- `useFiles()` wraps only upload and temporary-download-URL methods, not `selectFiles()` or upload `{ library: true }`.
- File support is captured when the View runtime is created; late method injection does not update `isSupported`.
- The standard MCP Apps `ui/download-file` operation has no public `mcp-use/react` hook.
- Generated View resources have no public arbitrary resource `_meta` authoring surface for `openai/widgetDescription` or `openai/widgetCSP.redirect_domains`.

Do not “verify” around these limits by inventing APIs or adding direct `window.openai` calls where a standard hook exists.

## Troubleshooting Split

| Symptom | First check |
|---|---|
| Tool result appears, no View | Standard descriptor/result/resource wire in Inspector |
| Blank View | Iframe console, generated assets, `useToolContext()` branches |
| Works only in Permissive CSP | Standard `view.csp` categories in Widget-Declared mode |
| Standard View works, ChatGPT state does not persist | Real ChatGPT `useViewState()` branch; Inspector cannot prove it |
| `useFiles().isSupported` is false in ChatGPT | Both real file methods must exist at runtime creation |
| ChatGPT file tool receives no file object | Literal `openai/fileParams` and required schema shape |
| Submission rejects UI domain | Dedicated unique `view.domain` and deployed origin |
| ChatGPT-only resource extension needed | Current generated-resource authoring limitation |

For deeper standard View diagnosis, continue with `references/23-debug/03-view-debugging.md`. For architecture and metadata classification, see `references/18-mcp-apps/chatgpt-apps/01-dual-protocol.md`.
