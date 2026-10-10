# ChatGPT Plugin Extensions Reference

*Authoritative guide for ChatGPT launch entrypoints, structured settings, deep links, tool icons, and model context attachments in mcp-use v2.*

Official reference: [ChatGPT Plugin Extensions](https://docs.mcp-use.com/v2/typescript/mcp-apps/chatgpt-extensions)

---

## 1. Typed Launch Entrypoints (`tool.view.entrypoints`)

ChatGPT supports opening MCP Apps directly from three launch surfaces:
1. `global`: App launcher in navigation. The tool input must accept `{}`.
2. `thread`: In-conversation app tab. The tool input must accept `{}`.
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
    content: [],
    structuredContent: { file },
  })
);
```

### Combined Entrypoints
To allow the same tool to open both as an empty launcher and as a file viewer, make the outer `file` field optional in the input schema:

```typescript
const combinedInput = fileInputSchema.partial();

server.tool({
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
}, async (args) => ({ content: [], structuredContent: args }));
```

---

## 2. Tool-Level Icons (`icons`)

Tools advertise top-level icons on `tools/list`:
- Set `icons: Icon[]` directly on `ToolDefinition`.
- Store SVGs in the project's `public/` directory (e.g. `public/icons/table.svg`). The framework automatically resolves them to absolute URLs.
- OpenAI Icon Guidelines: Monochrome SVGs with `currentColor`, transparent background, 20×20 viewBox, and 1.33px stroke width.

```xml
<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20">
  <path fill="none" stroke="currentColor" stroke-width="1.33" stroke-linecap="round" stroke-linejoin="round" d="M3 4h14v12H3zM3 8h14M8 8v8"/>
</svg>
```

---

## 3. Native Plugin Settings (`server.settings`)

`server.settings()` creates a pair of read and update tools (`settings.read` and `settings.update`) and advertises the `openai/settings` capability to ChatGPT.

```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({ name: "app", version: "1.0.0" });

let userSettings = {
  theme: "system" as "light" | "dark" | "system",
  compactMode: false,
};

// Optional helper tool for settings modal
server.tool(
  {
    name: "settings_help",
    title: "Settings Help",
    inputSchema: z.object({}),
    annotations: { readOnlyHint: true },
  },
  async () => ({
    content: [{ type: "text", text: "Configure view preferences and display options." }],
  })
);

server.settings({
  fields: {
    theme: {
      schema: z.enum(["light", "dark", "system"]),
      title: "Theme Preference",
      description: "Select visual appearance",
    },
    compactMode: {
      schema: z.boolean(),
      title: "Compact Density",
      description: "Reduce padding and spacing in tables",
    },
  },
  layout: [
    {
      kind: "group",
      title: "Appearance",
      items: [
        { kind: "property", property: "theme" },
        { kind: "property", property: "compactMode" },
        { kind: "tool", tool: "settings_help", title: "Learn more" },
      ],
    },
  ],
  read: async (ctx) => ({ ...userSettings }),
  update: async (patch, ctx) => {
    userSettings = { ...userSettings, ...patch };
    return { ...userSettings };
  },
});
```

---

## 4. Incoming Deep Links (`useDeepLink`)

When a global entrypoint is opened with a path or route, read it using `useDeepLink()` from `mcp-use/react`:

```tsx
import { useEffect, useState } from "react";
import { useDeepLink } from "mcp-use/react";

export default function AppView() {
  const { url } = useDeepLink();
  const [route, setRoute] = useState("/home");

  useEffect(() => {
    if (url !== undefined) {
      setRoute(url);
    }
  }, [url]);

  return <div>Active Route: {route}</div>;
}
```

Constructing Deep Links:
- Web: `https://chatgpt.com/plugins/<plugin-id>/app/<tool-name>?path=<encoded-path>`
- Desktop: `codex://plugins/<plugin-id>/app/<tool-name>?path=<encoded-path>`
- Mobile: `chatgpt://plugins/<plugin-id>/app/<tool-name>?path=<encoded-path>`

---

## 5. Selected Model Context Attachments (`useModelContext`)

Attach evidence (summaries, images, documents) to the next model turn when the user interacts with the UI:

```tsx
import { useModelContext } from "mcp-use/react";

export function AttachmentBar() {
  const { attachments, pending, error, add, remove, clearAttachments } = useModelContext();

  const handleAttach = async () => {
    await add("selected:report", {
      type: "text",
      title: "Q3 Sales Summary",
      text: "Revenue: $1.2M (+14% YoY). Gross Margin: 68%.",
      thumbnail: { src: "/icons/chart.png", mimeType: "image/png" },
    });
  };

  return (
    <div>
      <button onClick={handleAttach} disabled={pending}>
        Add Report to Chat
      </button>
      {attachments.map(({ key, block }) => (
        <span key={key}>
          {block.title}
          <button onClick={() => remove(key)}>×</button>
        </span>
      ))}
    </div>
  );
}
```

### Supported Attachment Content Blocks
1. **Text**: `{ type: "text", title: string, text: string, thumbnail?: { src, mimeType } }`
2. **Image**: `{ type: "image", title: string, src: string }` or `{ type: "image", title: string, data: string, mimeType: string }` (maximum 10 MiB decoded bytes).
3. **Resource Link**: `{ type: "resource_link", title: string, name: string, uri: string, mimeType: string }`
4. **Embedded Resource**: `{ type: "resource", title: string, resource: { uri, mimeType, text } }`

---

## 6. Resource Display Modes & `viewConfig`

Export a named `viewConfig` object directly from `views/<name>/view.tsx`:

```tsx
import type { ViewConfig } from "mcp-use/react";

export const viewConfig = {
  autoResize: true,
  displayModes: ["inline", "fullscreen"],
  preferredDisplayMode: "fullscreen",
} satisfies ViewConfig;
```

Requesting display modes dynamically at runtime:
```tsx
import { useDisplayMode } from "mcp-use/react";

export function MaximizeControl() {
  const { displayMode, availableDisplayModes, requestDisplayMode } = useDisplayMode();

  if (!availableDisplayModes.includes("fullscreen")) return null;

  return (
    <button onClick={() => void requestDisplayMode({ mode: "fullscreen" })}>
      Expand View
    </button>
  );
}
```
