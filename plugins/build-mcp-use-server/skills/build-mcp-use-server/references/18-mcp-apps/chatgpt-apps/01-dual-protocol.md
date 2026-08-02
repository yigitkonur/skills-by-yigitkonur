# Dual-Protocol: One Server Definition, Both MCP Apps and ChatGPT

*Read this when understanding how mcp-use emits both protocols from one server definition.*

The mcp-use framework automatically translates your MCP Apps server definition into both the standard MCP Apps protocol and ChatGPT's proprietary Apps SDK format. You write once; both hosts receive compatible output.

## One Definition, Two Wires

When you define a tool with a view, mcp-use generates:

1. **MCP Apps protocol** — standard MCP wire with `text/html;profile=mcp-app` MIME, CSP metadata, and `structuredContent`.
2. **ChatGPT Extensions** — Apps SDK metadata and `window.openai.setWidgetState()` calls, emitted alongside MCP protocol messages.

Both are sent simultaneously; the host you connect to uses the protocol it understands.

## What Stays the Same

Your server code is entirely protocol-agnostic:

```typescript
export const search = server.tool(
  {
    name: "search",
    inputSchema: z.object({ query: z.string() }),
    outputSchema: searchSchema,
    view: { name: "results" },  // ONE definition
  },
  async ({ query }) => ({
    content: [{ type: "text", text: "..." }],
    structuredContent: { /* matches searchSchema */ },
  })
);
```

mcp-use:
- Emits this as standard MCP Apps to MCP Desktop, Claude Desktop, etc.
- Simultaneously emits it as ChatGPT Apps SDK metadata.

## What Translation Covers

| v2 Concept | MCP Apps | ChatGPT | Handled By |
|-|-|-|-|
| Tool definition | tools/list | Apps SDK tool | ✓ same |
| Input schema | `inputSchema` | Apps SDK schema | ✓ auto-mapped |
| Structured output | `structuredContent` | `window.openai.setWidgetState()` | ✓ auto-mapped |
| Model-visible state | `_meta.ui` | `window.openai.widgetState.modelContent` | ✓ auto-mapped |
| View rendering | `ui://views/<name>.html` | Apps SDK iframe | ✓ auto-mapped |
| CSP metadata | `_meta.ui.csp` | Apps SDK sandbox rules | ✓ auto-mapped |
| Visibility hint | `_meta.ui.visibility` | Apps SDK metadata | ✓ auto-mapped |

## View Code Compatibility

Your React view code uses mcp-use hooks, which work on both platforms:

```typescript
// views/results/view.tsx
import { useToolContext, useCallTool, useSendFollowUp } from "mcp-use/react";

export default function ResultsView() {
  const ctx = useToolContext<"search">();
  const { callTool } = useCallTool("refine-search");
  const sendFollowUp = useSendFollowUp();
  
  // Same code runs on:
  // - MCP Apps hosts (Claude, MCP Desktop)
  // - ChatGPT
}
```

**Never import or call `window.openai` directly.** The mcp-use hooks handle both protocol implementations.

## No Manual Protocol Selection

You do NOT need to:

- Detect which host is connected
- Emit different metadata per host
- Translate results yourself
- Support two separate code paths

mcp-use handles all translation. Write for v2; it ships both.

## ChatGPT-Specific Behavior (Captured by Hooks)

ChatGPT has platform-specific state restoration and widget-state handling. mcp-use's `useViewState()` hook detects the platform and stores state accordingly:

```typescript
const [filters, setFilters] = useViewState({ sort: "relevance" });

// On ChatGPT: state persists across View re-renders via window.openai.widgetState
// On MCP Apps hosts: state lives for the request lifetime
// Hook implementation handles both transparently
```

## Metadata Translation Example

**Your server code (one definition):**

```typescript
view: {
  name: "results",
  description: "Search results",
  csp: { connectDomains: ["https://api.example.com"] },
}
```

**MCP Apps protocol emitted:**

```json
{
  "type": "text",
  "uri": "ui://views/results.html",
  "mimeType": "text/html;profile=mcp-app",
  "_meta": {
    "ui": {
      "description": "Search results",
      "csp": {
        "connectDomains": ["https://api.example.com", "https://myserver.com"]
      }
    }
  }
}
```

**ChatGPT Apps SDK emitted simultaneously:**

```json
{
  "toolId": "search",
  "appMetadata": {
    "description": "Search results",
    "sandbox": {
      "connectSources": ["https://api.example.com", "https://myserver.com"]
    }
  }
}
```

Both arrive on the same wire; the host parses its version.

## Debugging

To see which protocol a connection is using, check the `mcp-use dev` logs. The Inspector UI shows both protocol capabilities.

For ChatGPT debugging specifically, see `04-runtime-detection.md`.

## See Also

- `02-legacy-window-openai-and-skybridge.md` — historical protocols (for reference only)
- `03-csp-differences.md` — how CSP metadata differs between protocols
- `04-runtime-detection.md` — detecting runtime environment in a view
