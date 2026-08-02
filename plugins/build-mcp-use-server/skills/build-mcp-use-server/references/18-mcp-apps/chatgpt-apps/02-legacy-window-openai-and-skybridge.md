# Legacy: window.openai API and Skybridge MIME

*Read this for historical context only. Do not implement these patterns yourself.*

Before the MCP Apps spec, ChatGPT had two proprietary protocols for widget rendering. mcp-use abstracts both automatically; you should never hand-roll them.

## Skybridge MIME Type

**v1 artifact:** `text/html+skybridge`

Skybridge was ChatGPT's internal MIME type for widget resources before the MCP Apps spec existed. It used `window.openai` JavaScript API for state management.

**v2 status:** Removed. Use `text/html;profile=mcp-app` instead.

**mcp-use handling:** The framework emits both MCP Apps protocol and legacy ChatGPT metadata, so old ChatGPT versions still work via compatibility layer. You do not touch this.

## window.openai API

**v1 artifact:** ChatGPT widgets used `window.openai.setWidgetState()` and `window.openai.widgetState` to communicate with the host.

```typescript
// v1 ChatGPT widget (LEGACY — DO NOT USE)
if (window.openai?.setWidgetState) {
  window.openai.setWidgetState({
    modelContent: "User selected item X",
  });
}

if (window.openai?.widgetState?.modelContent) {
  const state = window.openai.widgetState.modelContent;
}
```

**v2 status:** Still present in ChatGPT for backward compatibility, but mcp-use hooks handle it transparently.

**mcp-use replacement:** Use `useViewState()` instead.

```typescript
// v2 (mcp-use — always use this)
import { useViewState } from "mcp-use/react";

const [state, setState] = useViewState({ modelContent: "" });
setState({ modelContent: "User selected item X" });
```

The `useViewState()` hook detects if `window.openai` is available (ChatGPT) and stores state accordingly; on MCP Apps hosts, it uses the standard protocol. **You never call `window.openai` directly.**

## Legacy Widget Metadata

**v1 artifact:** Widgets exported `widgetMetadata` to declare shape and behavior.

```typescript
// v1 (LEGACY)
export const widgetMetadata: WidgetMetadata = {
  description: "Show results",
  props: z.object({
    results: z.array(z.object({ id: z.string() })),
  }),
  exposeAsTool: false,
};
```

**v2 replacement:** Use `viewConfig` export (optional) and server-side tool `view` field.

```typescript
// v2
export const viewConfig: ViewConfig = {
  displayModes: ["inline", "fullscreen"],
};

// Server-side (index.ts)
view: {
  name: "results",
  description: "Show results",
  csp: { /* ... */ },
}
```

## Why You Shouldn't Hand-Roll These

1. **Protocol fragmentation** — Skybridge is ChatGPT-only; MCP Apps is the standard spec. Mixing both is maintainable only via a framework.
2. **State sync bugs** — `window.openai.setWidgetState()` calls need precise timing and protocol ordering. mcp-use handles this.
3. **Capability detection** — You'd need to detect which host is running and emit different metadata. mcp-use does this.
4. **CSP conflicts** — Skybridge and MCP Apps have different sandbox rules; mcp-use merges them correctly.

## When You Might See These Terms

- **Documentation** — older MCP tutorials may reference `window.openai` or Skybridge; they describe v1 or early ChatGPT code.
- **Existing codebases** — legacy projects may have direct `window.openai` calls; migrate them to mcp-use hooks.
- **ChatGPT-only servers** — some internal ChatGPT systems still use Skybridge. mcp-use transparently supports them.

## Migration Path

If you have v1 or Apps SDK code:

| v1/Legacy | v2 + mcp-use |
|-|-|
| `window.openai.setWidgetState()` | `useViewState()` |
| `window.openai.widgetState` | `useViewState()` |
| `widgetMetadata` export | `viewConfig` export + server `view: { ... }` |
| `text/html+skybridge` MIME | `text/html;profile=mcp-app` MIME |
| `useWidget()` hook | `useToolContext<"tool-name">()` hook |
| Manual widget registration | Tool-level `view` field binding |

See `references/28-migration/06-v1-to-v2-widgets-to-views.md` for detailed migration steps.

## Do Not Implement

- ❌ Direct `window.openai` calls
- ❌ `text/html+skybridge` MIME type emission
- ❌ Checking `window.openai` presence to decide flow
- ❌ Manual `widgetMetadata` export (use `viewConfig` instead)

**Always use mcp-use hooks.** They handle all protocol differences, host detection, and backward compatibility.
