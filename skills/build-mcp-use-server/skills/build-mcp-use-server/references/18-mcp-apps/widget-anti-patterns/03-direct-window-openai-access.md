# Anti-Pattern: Reaching for `window.openai` Directly

`window.openai` is the legacy ChatGPT Apps SDK bridge. It only exists in ChatGPT. Touching it directly hard-codes your widget to one host and crashes everywhere else (Claude, Goose, MCP Inspector, custom MCP clients).

## What goes wrong

```tsx
// BAD — hard-coded to ChatGPT
function MyWidgetContent() {
  const handleClick = () => {
    window.openai.callTool("search", { query: "test" }); // undefined in non-ChatGPT hosts
  };
  return <button onClick={handleClick}>Search</button>;
}
```

Symptoms:

- `Cannot read properties of undefined (reading 'callTool')` in Claude
- `window.openai is undefined` in MCP Inspector
- Works in ChatGPT, looks broken everywhere else
- TypeScript compiles fine — the global `any` hides it

## Use the `useWidget` / `useCallTool` hooks

`mcp-use/react` abstracts the host bridge. The same hook calls work in:

- ChatGPT Apps SDK (Skybridge MIME)
- Claude / MCP Apps standard (`text/html;profile=mcp-app`)
- MCP Inspector
- Any future host that speaks MCP Apps over `postMessage`

```tsx
// GOOD — host-agnostic
import { useCallTool, useWidget } from "mcp-use/react";

function MyWidgetContent() {
  const { theme, displayMode } = useWidget();
  const { callTool, isPending } = useCallTool("search");

  return (
    <button onClick={() => callTool({ query: "test" })} disabled={isPending}>
      {isPending ? "Searching..." : "Search"}
    </button>
  );
}
```

## Quick mapping from `window.openai.*` to hooks

| `window.openai.*` | `mcp-use/react` equivalent |
|---|---|
| `window.openai.callTool(name, args)` | `useCallTool(name).callTool(args)` |
| `window.openai.toolInput` | `useWidget().toolInput` |
| `window.openai.toolOutput` | `useWidget().output` or `useWidget().props` for render-ready structured content |
| `window.openai.theme` | `useWidget().theme` |
| `window.openai.displayMode` | `useWidget().displayMode` |
| `window.openai.requestDisplayMode({ mode })` | `useWidget().requestDisplayMode(mode)` |
| `window.openai.sendFollowUpMessage({ prompt })` | `useWidget().sendFollowUpMessage(prompt)` |
| `window.openai.setWidgetState(state)` | `useWidget().setState(stateOrUpdater)` |
| `window.openai.widgetState` | `useWidget().state` |

If you find yourself searching for a `window.openai` capability that has no hook equivalent, file an issue against `mcp-use` rather than reaching past the abstraction.

## Migration recipe

1. Add `import { useWidget, useCallTool } from "mcp-use/react"` at the top of the widget file.
2. Wrap the default export in `<McpUseProvider autoSize>`; see `../widget-react/01-mcpuseprovider.md`.
3. Find every `window.openai.*` usage and map it via the table above.
4. Delete any `declare global { interface Window { openai: any } }` — no longer needed.
5. Verify in MCP Inspector and Claude, not just ChatGPT.

## Severity

Critical. A widget that only renders in ChatGPT is invisible to Claude users — the host crashes silently and the LLM falls back to text. Always go through `mcp-use/react` hooks.
