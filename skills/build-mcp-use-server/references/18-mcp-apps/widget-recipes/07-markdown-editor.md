# Recipe 07 — Markdown Editor With Live Preview

**What it demonstrates:** split editor + preview pane, debounced save via `useCallTool`, dirty-state tracking, sanitized HTML rendering.

Synthesized example. Pairs local `useState` for the editing buffer with a server-side save tool, while keeping the rendered preview client-only for snappiness.

## File layout

```
resources/markdown-editor/
└── widget.tsx
src/tools/notes.ts
```

## Server tools — `src/tools/notes.ts`

```typescript
import { widget, object } from "mcp-use/server";
import type { MCPServer } from "mcp-use/server";
import { z } from "zod";

export function registerNoteTools(server: MCPServer) {
  server.tool(
    {
      name: "open-note",
      description: "Open a markdown note in the editor",
      schema: z.object({
        noteId: z.string().describe("Note ID"),
      }),
      widget: {
        name: "markdown-editor",
        invoking: "Opening note...",
        invoked: "Note ready",
      },
    },
    async ({ noteId }) => {
      // Replace with a real note store
      const body = `# Note ${noteId}\n\nWrite your thoughts here.\n\n- bullet one\n- bullet two\n`;
      return widget({
        props: { noteId, title: `Note ${noteId}`, body },
        message: `Opened note ${noteId} in the editor.`,
      });
    }
  );

  server.tool(
    {
      name: "save-note",
      description: "Save the markdown body of a note",
      schema: z.object({
        noteId: z.string().describe("Note ID"),
        body: z.string().describe("Markdown body"),
      }),
    },
    async ({ noteId, body }) => {
      return object({
        noteId,
        savedAt: new Date().toISOString(),
        bytes: body.length,
      });
    }
  );
}
```

## Widget — `resources/markdown-editor/widget.tsx`

```tsx
import { useEffect, useMemo, useRef, useState } from "react";
import { McpUseProvider, useWidget, useCallTool, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

export const widgetMetadata: WidgetMetadata = {
  description: "Live markdown editor with split preview and autosave",
  props: z.object({
    noteId: z.string(),
    title: z.string(),
    body: z.string(),
  }),
  metadata: { prefersBorder: true },
};

interface NoteProps {
  noteId: string;
  title: string;
  body: string;
}

// Tiny markdown -> HTML converter. Production widgets should use a vetted
// library compiled into the bundle (e.g. micromark) — never `dangerouslySetInnerHTML`
// with user content from outside the widget.
function renderMarkdown(src: string): string {
  const escape = (s: string) => s.replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c] ?? c));
  return escape(src)
    .replace(/^### (.*)$/gm, "<h3>$1</h3>")
    .replace(/^## (.*)$/gm, "<h2>$1</h2>")
    .replace(/^# (.*)$/gm, "<h1>$1</h1>")
    .replace(/^- (.*)$/gm, "<li>$1</li>")
    .replace(/(<li>.*<\/li>\n?)+/g, "<ul>$&</ul>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\n{2,}/g, "</p><p>")
    .replace(/^(?!<h\d|<ul|<\/p|<p)(.+)$/gm, "<p>$1</p>");
}

function MarkdownEditorContent() {
  const { props, isPending, theme } = useWidget<NoteProps>();
  const { callToolAsync: save, isPending: saving } = useCallTool("save-note");

  const [body, setBody] = useState(props.body ?? "");
  const [savedBody, setSavedBody] = useState(props.body ?? "");
  const [error, setError] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isDark = theme === "dark";

  // Sync local buffer when the host re-hydrates with new props (e.g. switching notes)
  useEffect(() => {
    if (!isPending) {
      setBody(props.body ?? "");
      setSavedBody(props.body ?? "");
    }
  }, [isPending, props.body]);

  // Debounced autosave: only persist after the user has stopped typing for 1s.
  useEffect(() => {
    if (isPending || body === savedBody) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      try {
        await save({ noteId: props.noteId, body });
        setSavedBody(body);
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Save failed");
      }
    }, 1000);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [body, savedBody, isPending, props.noteId, save]);

  const html = useMemo(() => renderMarkdown(body), [body]);
  const dirty = body !== savedBody;

  if (isPending) {
    return (
      <div className="p-6 animate-pulse">
        <div className={`h-6 w-1/3 rounded mb-4 ${isDark ? "bg-gray-800" : "bg-gray-200"}`} />
        <div className="grid grid-cols-2 gap-4">
          <div className={`h-64 rounded ${isDark ? "bg-gray-800" : "bg-gray-200"}`} />
          <div className={`h-64 rounded ${isDark ? "bg-gray-800" : "bg-gray-200"}`} />
        </div>
      </div>
    );
  }

  return (
    <div className={`p-4 ${isDark ? "bg-gray-900 text-white" : "bg-white text-gray-900"}`}>
      <div className="flex justify-between items-center mb-3">
        <h2 className="text-lg font-bold">{props.title}</h2>
        <div className="flex items-center gap-2 text-xs">
          {saving && <span className={isDark ? "text-gray-400" : "text-gray-500"}>Saving…</span>}
          {!saving && dirty && <span className="text-amber-500">Unsaved</span>}
          {!saving && !dirty && <span className="text-green-500">✓ Saved</span>}
          {error && <span className="text-red-500">{error}</span>}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          spellCheck={false}
          className={`w-full h-72 p-3 rounded border font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            isDark ? "bg-gray-800 border-gray-700" : "bg-white border-gray-300"
          }`}
        />
        <div
          className={`w-full h-72 p-3 rounded border overflow-auto prose prose-sm ${
            isDark ? "bg-gray-800 border-gray-700 prose-invert" : "bg-gray-50 border-gray-200"
          }`}
          dangerouslySetInnerHTML={{ __html: html }}
        />
      </div>
    </div>
  );
}

export default function Widget() {
  return (
    <McpUseProvider autoSize>
      <MarkdownEditorContent />
    </McpUseProvider>
  );
}
```

## What to copy when adapting

| Concern | Where it lives |
|---|---|
| Local editing buffer | `useState(body)` — typing does not round-trip the server |
| Debounced save | `setTimeout(...)` 1s after the last keystroke; cleanup the timer on rerun |
| Dirty indicator | Compare `body !== savedBody` for the badge |
| Re-hydration on prop change | The `useEffect([props.body])` resets the buffer when the host opens a new note |
| Markdown sanitization | Escape input, then apply regex transforms — or import a real parser; **never** `dangerouslySetInnerHTML` raw user input |
| Live preview | `useMemo` so re-rendering does not re-parse on every keystroke |
