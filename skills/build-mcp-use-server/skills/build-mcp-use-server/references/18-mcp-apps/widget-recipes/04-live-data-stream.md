# Recipe 04 — Live Streaming Code Preview

**What it demonstrates:** `partialToolInput` consumed live during the LLM's tool-call generation. The widget renders the user-visible preview before the server tool has even run.

This is the canonical use case for `useWidget().partialToolInput` and `useWidget().isStreaming`. See the deeper notes in `../streaming-tool-props/` once that cluster is populated; this recipe is the minimum reproducible example.

## File layout

```
resources/code-preview/
└── widget.tsx
src/tools/code.ts
```

## Server tool — `src/tools/code.ts`

```typescript
import { widget } from "mcp-use/server";
import type { MCPServer } from "mcp-use/server";
import { z } from "zod";

export function registerCodeTools(server: MCPServer) {
  server.tool(
    {
      name: "generate-code",
      description: "Generate code for a given task",
      schema: z.object({
        task: z.string().describe("What the code should do"),
        language: z.string().default("typescript").describe("Programming language"),
        code: z.string().describe("The generated code body"),
      }),
      widget: {
        name: "code-preview",
        invoking: "Generating code...",
        invoked: "Code ready",
      },
    },
    async ({ task, language, code }) => {
      return widget({
        props: { code, language, task, lineCount: code.split("\n").length },
        message: `Generated ${language} code for: ${task}`,
      });
    }
  );
}
```

`code` is part of the tool's input schema, not its output. That is intentional — `partialToolInput` only carries fields the LLM is **generating as input**. The widget reads the LLM's in-progress `code` field as it streams.

## Widget — `resources/code-preview/widget.tsx`

```tsx
import { useState } from "react";
import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

export const widgetMetadata: WidgetMetadata = {
  description: "Displays generated code with syntax highlighting, streaming preview, and copy to clipboard",
  props: z.object({
    code: z.string(),
    language: z.string(),
    task: z.string(),
    lineCount: z.number(),
  }),
  metadata: { prefersBorder: true },
};

interface CodeProps {
  code: string;
  language: string;
  task: string;
  lineCount: number;
}

interface CodeToolInput {
  task: string;
  language?: string;
  code?: string;
}

function CodePreviewContent() {
  const { props, isPending, isStreaming, partialToolInput, theme } =
    useWidget<CodeProps, Record<string, never>, CodeProps, Record<string, never>, CodeToolInput>();
  const [copied, setCopied] = useState(false);
  const isDark = theme === "dark";

  // Render in three stages:
  //   1. nothing yet      -> skeleton
  //   2. streaming        -> partialToolInput.code (live)
  //   3. tool resolved    -> props.code (final)
  const displayCode = isStreaming ? (partialToolInput?.code ?? "") : (props.code ?? "");
  const displayLanguage = (isStreaming ? partialToolInput?.language : props.language) ?? "text";
  const lines = displayCode.split("\n");

  const handleCopy = async () => {
    await navigator.clipboard.writeText(displayCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (isPending && !partialToolInput) {
    return (
      <div className={`p-4 rounded-lg font-mono ${isDark ? "bg-gray-900" : "bg-gray-50"}`}>
        <div className="animate-pulse space-y-2">
          {[1, 2, 3, 4, 5].map((i) => (
            <div
              key={i}
              className={`h-4 rounded ${isDark ? "bg-gray-800" : "bg-gray-200"}`}
              style={{ width: `${30 + Math.random() * 60}%` }}
            />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={`rounded-lg overflow-hidden ${isDark ? "bg-gray-900" : "bg-gray-50"}`}>
      <div className={`flex justify-between items-center px-4 py-2 ${isDark ? "bg-gray-800" : "bg-gray-200"}`}>
        <div className="flex items-center gap-2">
          <span className={`text-xs font-mono px-2 py-0.5 rounded ${isDark ? "bg-gray-700 text-gray-300" : "bg-gray-300 text-gray-700"}`}>
            {displayLanguage}
          </span>
          {isStreaming && (
            <span className="text-xs text-blue-400 animate-pulse">● Streaming...</span>
          )}
          {!isStreaming && props.lineCount && (
            <span className={`text-xs ${isDark ? "text-gray-500" : "text-gray-400"}`}>
              {props.lineCount} lines
            </span>
          )}
        </div>
        <button
          onClick={handleCopy}
          disabled={isStreaming}
          className={`text-xs px-3 py-1 rounded transition-colors ${
            copied
              ? "bg-green-500 text-white"
              : isDark
              ? "bg-gray-700 text-gray-300 hover:bg-gray-600"
              : "bg-gray-300 text-gray-700 hover:bg-gray-400"
          }`}
        >
          {copied ? "✓ Copied" : "Copy"}
        </button>
      </div>

      <div className="overflow-x-auto p-4">
        <pre className="text-sm">
          <code>
            {lines.map((line, i) => (
              <div key={i} className="flex">
                <span className={`select-none w-8 text-right mr-4 ${isDark ? "text-gray-600" : "text-gray-400"}`}>
                  {i + 1}
                </span>
                <span className={isDark ? "text-gray-200" : "text-gray-800"}>{line}</span>
              </div>
            ))}
            {isStreaming && <span className="text-blue-400 animate-pulse">▌</span>}
          </code>
        </pre>
      </div>
    </div>
  );
}

export default function Widget() {
  return (
    <McpUseProvider autoSize>
      <CodePreviewContent />
    </McpUseProvider>
  );
}
```

## What to copy when adapting

| Concern | Where it lives |
|---|---|
| Stream the LLM's input | The tool's **input** schema includes the streamed field (`code`); the widget reads `partialToolInput.code` |
| Type streamed input | Put the tool-input type in the **fifth** `useWidget` generic slot: `useWidget<Props, State, Output, Metadata, ToolInput>()` |
| Three-stage render | `isPending && !partialToolInput` -> skeleton; `isStreaming` -> partial; otherwise -> `props` |
| Disable destructive actions during streaming | Copy button is `disabled={isStreaming}` to avoid copying half-generated content |
| Display fallback | `displayLanguage = (isStreaming ? partialToolInput?.language : props.language) ?? "text"` |
| Cursor affordance | Animated `▌` while `isStreaming` so the user sees the LLM is still typing |
