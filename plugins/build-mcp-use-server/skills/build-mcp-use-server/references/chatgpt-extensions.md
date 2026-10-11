# ChatGPT Plugin Extensions Reference

*Authoritative guide for ChatGPT launch entrypoints, structured settings, deep links, tool icons, and model context attachments in mcp-use v2.*

Official reference: [ChatGPT Plugin Extensions](https://docs.mcp-use.com/v2/typescript/mcp-apps/chatgpt-extensions)

---

## 1. Typed Launch Entrypoints (`tool.view.entrypoints`)

ChatGPT supports launching MCP Apps directly from three distinct surfaces:
1. `global`: App launcher in global navigation. The tool input must accept `{}`.
2. `thread`: Context menu or action button in an active chat thread. The tool input must accept `{}`.
3. `file`: Custom viewer when opening matching file attachments. The tool input must accept `{ file: { name: string, resourceUri: string } }`.

```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({ name: "data-studio", version: "1.0.0" });

const fileInputSchema = z.object({
  file: z.object({
    name: z.string().min(1),
    resourceUri: z.string().min(1),
  }),
});

export const openViewer = server.tool(
  {
    name: "open-data-viewer",
    title: "Data Table Viewer",
    icons: [
      { src: "icons/table.svg", mimeType: "image/svg+xml", sizes: ["20x20"] },
    ],
    inputSchema: fileInputSchema,
    outputSchema: fileInputSchema,
    view: {
      name: "table-viewer",
      entrypoints: [
        { type: "file", extensions: [".csv", ".tsv", ".json"] },
      ],
    },
  },
  async ({ file }) => ({
    // Best Practice: Always return natural language in content so LLM understands what was displayed
    content: [{ type: "text", text: `Opened data viewer for file: ${file.name}` }],
    structuredContent: { file },
    _meta: { launchedVia: "file-entrypoint" },
  })
);
```

### Combined Entrypoints Pattern
To allow the same tool to open both as an empty launcher and as a file viewer, make the `file` field optional in the input schema:

```typescript
const combinedInput = fileInputSchema.partial();

export const openFlexibleViewer = server.tool(
  {
    name: "open-data-viewer",
    inputSchema: combinedInput,
    outputSchema: combinedInput,
    view: {
      name: "table-viewer",
      entrypoints: [
        { type: "global" },
        { type: "thread" },
        { type: "file", extensions: [".csv", ".tsv"] },
      ],
    },
  },
  async (args) => ({
    content: [
      {
        type: "text",
        text: args.file ? `Opened table viewer for ${args.file.name}` : "Opened blank table viewer.",
      },
    ],
    structuredContent: args,
  })
);
```

### Manifest Metadata Annotations on Tools
In ChatGPT App Extensions, tools can advertise extension metadata in `annotations` or `_meta`:
- `openai/outputTemplate`: Format template string guiding how ChatGPT displays or quotes tool output in conversation.
- `openai/widgetDescription`: Human- and model-facing description of the interactive widget.
- `openai/toolInvocation/ephemeral`: Boolean indicating whether the tool invocation is ephemeral in conversation history.

```typescript
server.tool({
  name: "render_chart",
  annotations: {
    "openai/outputTemplate": "Rendered interactive chart for {dataset}",
    "openai/widgetDescription": "Interactive financial line chart with pan/zoom",
    "openai/toolInvocation/ephemeral": false,
  },
  // ...
});
```

---

## 2. Tool-Level Icons (`icons`)

Tools advertise top-level icons on `tools/list`:
- Set `icons: Icon[]` directly on `server.tool({...})`.
- Store SVGs in the project's `public/` directory (e.g. `public/icons/table.svg`). The framework automatically resolves them to absolute URLs via `${basePath}/_mcp-use/public/`.
- **OpenAI Icon Guidelines**: Monochrome SVGs with `currentColor`, transparent background, 20×20 viewBox, and 1.33px stroke width.

```xml
<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20">
  <path fill="none" stroke="currentColor" stroke-width="1.33" stroke-linecap="round" stroke-linejoin="round" d="M3 4h14v12H3zM3 8h14M8 8v8"/>
</svg>
```

---

## 3. Native Plugin Settings (`server.settings`)

`mcp-use` provides a native settings engine exposed directly to ChatGPT and MCP hosts. It registers `settings.read` and `settings.update` tools and renders an official configuration sheet in ChatGPT.

### Official Settings Schema Specification
- `fields`: A map of setting keys to configuration descriptors:
  - `type`: `"string" | "number" | "boolean"`
  - `label`: Human-readable label displayed in settings UI
  - `description?`: Explanatory description
  - `secret?`: If `true`, the value is masked and treated as a write-only secret
  - `default?`: Default fallback value
- `layout`: An array of layout sections organizing fields:
  - `title`: Section header
  - `fields`: Array of field key names belonging to this section
- `read`: `async (ctx) => Promise<Record<string, unknown>>`
- `update`: `async (updates: Record<string, unknown>, ctx) => Promise<void>`

```typescript
import { MCPServer } from "mcp-use";

const server = new MCPServer({ name: "data-studio", version: "1.0.0" });

let currentSettings = {
  apiKey: process.env.STUDIO_API_KEY ?? "",
  refreshInterval: 30,
  enableNotifications: true,
};

server.settings({
  fields: {
    apiKey: {
      type: "string",
      label: "API Key",
      description: "Provider access token for external data sync",
      secret: true,
    },
    refreshInterval: {
      type: "number",
      label: "Auto-refresh Interval (seconds)",
      description: "Frequency of background metric updates",
      default: 30,
    },
    enableNotifications: {
      type: "boolean",
      label: "Real-time Notifications",
      description: "Receive alert notifications in conversation",
      default: true,
    },
  },
  layout: [
    {
      title: "Authentication",
      fields: ["apiKey"],
    },
    {
      title: "Preferences",
      fields: ["refreshInterval", "enableNotifications"],
    },
  ],
  read: async (ctx) => {
    return {
      apiKey: currentSettings.apiKey,
      refreshInterval: currentSettings.refreshInterval,
      enableNotifications: currentSettings.enableNotifications,
    };
  },
  update: async (updates, ctx) => {
    currentSettings = { ...currentSettings, ...updates };
    console.log("Settings updated:", Object.keys(updates));
  },
});
```

---

## 4. Incoming Deep Links (`useDeepLink`)

When a ChatGPT app is launched via a deep link or path, read it inside the view using `useDeepLink()` from `"mcp-use/react"`:

```tsx
import React, { useEffect, useState } from "react";
import { useDeepLink } from "mcp-use/react";

export default function AppView() {
  const { url } = useDeepLink();
  const [activeRoute, setActiveRoute] = useState("/home");

  useEffect(() => {
    if (url !== undefined) {
      try {
        const parsed = new URL(url);
        const routeParam = parsed.searchParams.get("route");
        if (routeParam) {
          setActiveRoute(routeParam);
        }
      } catch {
        setActiveRoute(url);
      }
    }
  }, [url]);

  return <div className="p-4">Active Route: {activeRoute}</div>;
}
```

### Deep Link URL Formats
- **Web**: `https://chatgpt.com/plugins/<plugin-id>/app/<tool-name>?route=<encoded-path>`
- **Desktop**: `codex://plugins/<plugin-id>/app/<tool-name>?route=<encoded-path>`
- **Mobile**: `chatgpt://plugins/<plugin-id>/app/<tool-name>?route=<encoded-path>`

---

## 5. Model Context Attachments (`useModelContext`)

The `useModelContext()` hook imperatively attaches evidence and contextual blocks to the active LLM conversation without creating a user turn.

> [!WARNING]
> **Object Iteration & Synchronous `add()` Invariants:**
> 1. `attachments` returned by `useModelContext()` is a `Record<string, ModelContextBlock>` (a plain JavaScript Object, **NOT an Array**). Calling `attachments.map()` throws `TypeError: attachments.map is not a function` at runtime and crashes the React tree. Always iterate using `Object.entries(attachments).map(([key, block]) => ...)`.
> 2. `add(key, block)` is synchronous (returns `void`). Do **NOT** `await add(...)`.

```tsx
import React from "react";
import { useModelContext } from "mcp-use/react";

export function AttachmentBar() {
  const { attachments, pending, error, add, remove, clearAttachments } = useModelContext();

  const handleAttachReport = () => {
    // add is synchronous void - do NOT await
    add("selected:report", {
      type: "text",
      text: "Revenue: $1.2M (+14% YoY). Gross Margin: 68%. Churn: 1.2%.",
    });
  };

  return (
    <div className="p-4 space-y-3">
      <div className="flex gap-2">
        <button
          onClick={handleAttachReport}
          disabled={pending}
          className="px-3 py-1.5 bg-primary text-white rounded text-sm"
        >
          Attach Report to Chat
        </button>
        <button
          onClick={clearAttachments}
          className="px-3 py-1.5 border rounded text-sm"
        >
          Clear All
        </button>
      </div>

      {/* attachments is a Record<string, ModelContextBlock> - iterate via Object.entries */}
      <div className="flex flex-wrap gap-2">
        {Object.entries(attachments).map(([key, block]) => (
          <span
            key={key}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-surface border text-xs"
          >
            <span>{key}: {block.type}</span>
            <button
              onClick={() => remove(key)}
              className="text-secondary hover:text-danger ml-1"
            >
              ×
            </button>
          </span>
        ))}
      </div>

      {error && <p className="text-xs text-danger">{error.message}</p>}
    </div>
  );
}
```

### Supported Attachment Content Blocks (`ModelContextBlock`)
1. **Text**: `{ type: "text", text: string }`
2. **Image**: `{ type: "image", data: string, mimeType: string }`
   - `data` is a base64-encoded string representing the image bytes (max 10 MiB decoded).
3. **Resource Link**: `{ type: "resource_link", uri: string, title?: string }`
   - Refers to an existing MCP resource URI.
4. **Embedded Resource**: `{ type: "resource", uri: string, mimeType: string, text?: string, blob?: string }`
   - Directly embeds full text or base64 blob content.

---

## 6. Resource Display Modes & `viewConfig`

Views can declare supported presentation modes and dynamically request mode transitions between `"inline"`, `"fullscreen"`, and `"pip"` (Picture-in-Picture).

### Static Configuration (`viewConfig`)
Export a named `viewConfig` object directly from `views/<name>/view.tsx`:

```tsx
import type { ViewConfig } from "mcp-use/react";

export const viewConfig = {
  autoResize: true,
  displayModes: ["inline", "fullscreen", "pip"],
  preferredDisplayMode: "inline",
} satisfies ViewConfig;
```

### Dynamic Mode Changes at Runtime (`useDisplayMode`)
```tsx
import React from "react";
import { useDisplayMode } from "mcp-use/react";

export function DisplayModeControls() {
  const { displayMode, availableDisplayModes, requestDisplayMode } = useDisplayMode();

  return (
    <div className="flex gap-2 text-xs">
      {availableDisplayModes.includes("fullscreen") && (
        <button
          onClick={() => void requestDisplayMode({
            mode: displayMode === "fullscreen" ? "inline" : "fullscreen",
          })}
          className="px-2 py-1 border rounded"
        >
          {displayMode === "fullscreen" ? "Exit Fullscreen" : "Fullscreen"}
        </button>
      )}

      {availableDisplayModes.includes("pip") && (
        <button
          onClick={() => void requestDisplayMode({ mode: "pip" })}
          className="px-2 py-1 border rounded"
        >
          Picture-in-Picture
        </button>
      )}
    </div>
  );
}
```
