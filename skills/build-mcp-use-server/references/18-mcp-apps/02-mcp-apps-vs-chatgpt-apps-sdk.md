# MCP Apps vs. ChatGPT Apps SDK

*Read this when building a server that must support both ChatGPT and MCP Apps hosts.*

The MCP Apps spec and ChatGPT's Apps SDK are two separate but compatible implementations. The mcp-use framework emits both protocols from a single server definition, so your Views work in ChatGPT, Claude, and any MCP Apps host.

## One Server, Two Protocols

| Aspect | MCP Apps spec | ChatGPT Apps SDK | mcp-use Abstraction |
|-|-|-|-|
| **Wire protocol** | MCP (tools, resources, prompts, notifications) | ChatGPT custom extensions + window.openai API | Single tool def + auto-translation |
| **Result format** | `{ content: [...], structuredContent, _meta.ui }` | `window.openai.setWidgetState()` calls | Merged output from single handler |
| **View registration** | Tool `view: { name }` + auto-generated resource | Apps SDK metadata on tool result | Same tool definition, both emitted |
| **State persistence** | View-lifetime or request-scoped | ChatGPT restores `window.openai.widgetState.modelContent` across invocations | `useViewState()` hook handles both |
| **Hook compatibility** | `useToolContext`, `useCallTool`, `useSendFollowUp` | Apps SDK functions wrapped by mcp-use hooks | Identical hook surface |

## Mcp-use Auto-Translation

When you define a tool with a `view` field, mcp-use generates:

1. **Standard MCP Apps** — tool result carries `text/html;profile=mcp-app` resource + CSP metadata.
2. **ChatGPT metadata** — MCP Apps metadata auto-translates to ChatGPT Apps SDK fields (e.g., `_meta.ui.visibility` → `widgetState` hints).

Views written using mcp-use hooks (`useToolContext`, `useViewState`, etc.) work on both platforms. You never hand-roll ChatGPT-specific code.

## ChatGPT Legacy Protocol (Do Not Hand-Roll)

ChatGPT has an older protocol layer (`window.openai.widgetState`, `text/html+skybridge` MIME) used before Apps SDK standardization. **Never implement this yourself.** The mcp-use framework handles it transparently via the legacy layer; direct `window.openai` calls are anti-patterns (covered in `anti-patterns.md`).

See `02-legacy-window-openai-and-skybridge.md` for reference only — mcp-use abstracts this entirely.

## Platform-Specific Behavior

| Behavior | MCP Apps | ChatGPT | How mcp-use Handles It |
|-|-|-|-|
| Model-visible state | `useViewState()` persists for request lifetime | Restores across View invocations | `useViewState()` detects host and stores accordingly |
| Follow-up messages | `useSendFollowUp()` sent to conversation | Sent to same thread | Hook abstracts both |
| File picker | `useFiles()` uses `files` capability | ChatGPT file UI | Hook checks capability, delegates |
| Display mode | `useDisplayMode()` advisory; host decides | Display-mode hints | Hook polls both via unified `useHostContext()` |

## Migration from Apps SDK to MCP Apps

If you built with the Apps SDK, the mcp-use v2 approach subsumes it:

- **Apps SDK Views** (`view.tsx` with `window.openai` calls) → **mcp-use Views** (hooks-based, no `window.openai`)
- **Apps SDK tooling** (manual metadata) → **mcp-use tooling** (tool `view: { name }` field, auto-metadata)
- **No Apps SDK NPM package** → imports from `mcp-use/react`

All three (Apps SDK, MCP Apps spec, mcp-use framework) interoperate via the mcp-use translation layer. Write once for mcp-use; it ships both protocols.

## Capability Detection

Both platforms advertise their capabilities via `useHostContext().availableCapabilities`:

```typescript
const { availableCapabilities } = useHostContext();
if (availableCapabilities.includes("message")) {
  await useSendFollowUp({ prompt: "..." });
}
```

Query capabilities before using platform-specific APIs. See `05-host-capability-detection.md`.
