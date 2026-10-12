# Multi-Host Deployment & Archestra Architecture

*Authoritative guide for running mcp-use MCP Apps across multiple host environments: ChatGPT, Claude Desktop, and Archestra.*

Grounded on the comprehensive 92-page production specification at `/root/dev/guide-to-mcp-apps` and verified implementations from production deployments (Ahrefs, SEMrush, Screaming Frog, Lighthouse).

---

## 1. Multi-Host Portability Model

In `mcp-use` v2, an MCP App is fundamentally a portable, standard-compliant UI extension (SEP-1865). The server packages the view as an MCP resource:
- **Resource URI**: `ui://views/<name>.html`
- **MIME Type**: `text/html;profile=mcp-app`
- **Extension ID**: `io.modelcontextprotocol/ui`

Because the view runs inside a standard sandboxed `<iframe>` and communicates via protocol messages, **the exact same `mcp-use` server and views can be consumed by different host platforms without altering server business logic**.

---

## 2. Archestra Host Architecture

Archestra provides two distinct routes for rendering applications: the **Installed-Server (Native Portable) Route** and the **Owned App Route**.

### Route A: Installed Portable MCP Apps (Recommended & Modern Path)

This is the primary route for `mcp-use` applications. Archestra directly connects to your running MCP server as an installed integration.

```
+---------------------------------------------------------------------------------+
|                                Archestra Host                                   |
|                                                                                 |
|  +------------------------+             +------------------------------------+  |
|  | Archestra Gallery      |             | Session-Authenticated Proxy Route  |  |
|  | (Apps from installed   |             | POST /api/mcp/server/:mcpServerId  |  |
|  |  MCP servers)          |             |                                    |  |
|  +-----------+------------+             +-----------------+------------------+  |
|              |                                            |                     |
+--------------|--------------------------------------------|---------------------+
               | iframe render                              | tool call proxy
               v                                            v
+---------------------------------------------------------------------------------+
|  mcp-use View Runtime                                     |                     |
|  (views/<name>/view.tsx)                                  |                     |
|  - Reads: ui://views/<name>.html                          |                     |
|  - Hooks: useToolContext(), useCallTool()                 |                     |
+-----------------------------------------------------------+                     |
                                                            v                     |
+---------------------------------------------------------------------------------+
|  mcp-use Server (Installed)                                                     |
|  - Validates installation upstream credentials                                  |
|  - Executes tool callback and returns CallToolResult                            |
+---------------------------------------------------------------------------------+
```

#### How Installed Apps Work in Archestra:
1. **Gallery Integration**: In the Archestra frontend (`page.client.tsx:128-131, 275-278`), installed servers with UI-bound tools are automatically rendered in the **"Apps from installed MCP servers"** section.
2. **Discovery & Binding**: When the server is installed or refreshed (`POST /api/mcp/server/:mcpServerId/refresh`), Archestra inspects `tools/list` and `resources/list`. Tools declaring `view: { name: "<name>" }` and a valid `outputSchema` are mapped to their corresponding view resource at `ui://views/<name>.html`.
3. **Execution & Credentials**: Tool calls from the view pass through Archestra's proxy (`POST /api/mcp/server/:mcpServerId`). **Important**: Tool calls use the *installation's own configured upstream credentials*, not the individual viewer's session tokens.
4. **Browser Runtime**: Views use standard, portable `mcp-use/react` hooks (`useToolContext`, `useCallTool`, `useViewState`). No host-proprietary runtime injection is required.
5. **Project Consolidation Evidence**: Production case studies reflect a complete transition to this path:
   - **SEMrush**: Formally retired its 4 owned apps on 2026-09-27 in favor of portable `views/` using the apps presentation profile (`/root/dev/semrush/mcp/archestra-apps/AGENTS.md:3`).
   - **Screaming Frog**: Designated its 5 older standalone HTML apps as legacy, adopting portable `views/` as modern (`/root/dev/screaming-frog/mcp/archestra/AGENTS.md:3`).
   - **Ahrefs**: Discovers portable views directly from the installed server (`/root/dev/ahrefs/mcp/AGENTS.md:3`).

---

### Route B: Owned Archestra Apps (Conditional Alternative)

An Owned App is a standalone, single-file HTML document stored and served directly by the Archestra platform database rather than by an external MCP server.

- **Browser API**: Authored against `window.archestra`, which Archestra injects before application scripts (`archestra.ready`, `archestra.tools.call()`, `archestra.storage`, `archestra.files`).
- **Platform CSP**: Enforces a strict, fixed CSP served by the platform (permits specific CDNs, strictly forbids external browser `fetch`).
- **Save Gate Validation**: Authored HTML is strictly validated at save-time by Archestra's Rust core (`app_html.rs`). It rejects self-bundled transport bootstraps or duplicate baseline stylesheets.
- **When to Use**: Only choose the owned route when the workflow strictly requires Archestra-proprietary features like platform-managed shared storage partitions, platform file handoff, or persistent viewer identity.

---

## 3. Multi-Host Feature & Capability Matrix

| Capability / Dimension | ChatGPT Host | Claude Desktop Host | Archestra Host (Installed Server) |
|---|---|---|---|
| **View Resource Source** | External MCP server (`ui://views/...`) | External MCP server (`ui://views/...`) | External MCP server (`ui://views/...`) |
| **Recommended UI System** | `@openai/apps-sdk-ui` + Tailwind 4 | Tailwind CSS / Standard Web Components | `@openai/apps-sdk-ui` or Tailwind CSS |
| **Primary Data Channel** | `structuredContent` via `useToolContext()` | `structuredContent` via `useToolContext()` | `structuredContent` via `useToolContext()` |
| **View-Only Metadata** | `_meta` via `useToolContext().meta` | `_meta` via `useToolContext().meta` | `_meta` via `useToolContext().meta` |
| **Secondary Tool Calls** | `useCallTool("tool-name")` | `useCallTool("tool-name")` | `useCallTool("tool-name")` via proxy |
| **Conversational Model Context** | `useModelContext()` (attaches to next turn) | Not supported (read-only view) | Not supported (standalone gallery view) |
| **Theme Synchronization** | `useViewTheme()` -> `applyDocumentTheme()` | `useViewTheme()` -> `data-theme` | `useViewTheme()` -> `data-theme` |
| **Plugin Settings** | `server.settings()` with native modal | Not supported | Handled via Archestra Server Config |
| **Launch Entrypoints** | `entrypoints: ["global", "thread", "file"]` | Standard tool picker | Gallery App catalog / pinned entries |
| **Display Modes** | `"inline"`, `"fullscreen"`, `"pip"` | Host window layout | Embedded gallery card / expanded modal |

---

## 4. Building Multi-Host Compatible Views

To ensure your `mcp-use` views render cleanly in ChatGPT, Claude Desktop, and Archestra simultaneously:

### 1. Always Guard Host-Specific Extensions
Never assume ChatGPT-specific hooks are active. Guard extensions gracefully:

```tsx
import React, { useEffect } from "react";
import { useToolContext, useModelContext, useViewTheme } from "mcp-use/react";
import { applyDocumentTheme } from "@openai/apps-sdk-ui/theme";

export default function AdaptiveView() {
  const context = useToolContext<"get-report">();
  const theme = useViewTheme();
  const modelContext = useModelContext(); // May be no-op in Archestra

  // 1. Theme sync works in all hosts providing theme info
  useEffect(() => {
    if (theme) {
      applyDocumentTheme(theme);
      document.documentElement.setAttribute("data-theme", theme);
    }
  }, [theme]);

  if (context.status !== "ready") return <div>Loading...</div>;

  const handleSelect = (item: any) => {
    // 2. Safe conversational context: will attach in ChatGPT, gracefully ignored elsewhere
    if (modelContext?.add) {
      modelContext.add("selection", {
        type: "text",
        text: `Selected report item: ${item.id}`,
      });
    }
  };

  return (
    <div className="p-4 bg-surface text-default">
      <h2>{context.toolOutput.title}</h2>
      <button onClick={() => handleSelect(context.toolOutput)}>
        Select Item
      </button>
    </div>
  );
}
```

### 2. Adhere to Standard SEP-1865 CSP Directives
Archestra and ChatGPT both enforce strict CSP on view iframes. Configure domains in `view.csp`:
```typescript
view: {
  name: "dashboard",
  csp: {
    connectDomains: ["https://api.my-service.com"],
    resourceDomains: ["https://cdn.my-service.com"],
  },
}
```

---

## 5. Archestra Diagnostic & Troubleshooting Playbook

When deploying or testing an `mcp-use` app on Archestra, follow this 5-step diagnostic sequence derived from `/root/dev/guide-to-mcp-apps/03-archestra/01-platform-overview-and-architecture.md`:

1. **Installation Visibility**:
   - Verify that the viewer has access to the server installation.
   - If inaccessible, Archestra's proxy (`/api/mcp/server/:mcpServerId`) returns HTTP 403.
2. **Live Discovery of Tool/View Binding**:
   - Confirm that the tool is listed in `tools/list` and contains the `view` property:
     ```json
     {
       "name": "audit-site",
       "view": { "name": "site-audit-report" }
     }
     ```
   - If missing, trigger a reload via Archestra's refresh route: `POST /api/mcp/server/:mcpServerId/refresh`.
3. **Resource Availability**:
   - Verify that `resources/list` advertises `ui://views/<name>.html` with MIME type `text/html;profile=mcp-app`.
   - Test that reading the resource returns valid bundled HTML containing `<script type="module">`.
4. **App Visibility & Policy Gate**:
   - Verify that the tool is not hidden by invocation policy (`visibility: "model"` vs `"app"`).
5. **Upstream Credential Validation**:
   - Remember that Archestra proxies tool calls using the *server installation credentials*. If tool calls fail with 401/403 while browsing the gallery, verify the API keys or OAuth tokens configured in the Archestra Server Settings modal.
