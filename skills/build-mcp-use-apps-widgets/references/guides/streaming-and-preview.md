# Streaming and Live Preview

How to use streaming tool arguments to show live previews as the LLM generates tool call parameters.

> **Host support required**: Streaming tool argument preview (`partialToolInput` / `isStreaming`) is supported by MCP Apps clients (Claude, Goose) and the MCP Inspector. ChatGPT (Apps SDK protocol) does not expose partial tool arguments to widgets — `isStreaming` will remain `false` and `partialToolInput` will remain `null` in that environment. Always implement a working `isPending` fallback for non-streaming hosts.

---

## How Streaming Works

When an LLM calls a tool, it generates the tool arguments token by token. With streaming enabled, the widget receives these partial arguments in real time before the tool handler executes on the server.

### Timeline

```
LLM starts generating tool args
  ↓
Widget receives partialToolInput (updates incrementally)
  ↓ isStreaming = true
  ↓ isPending = true
  ↓
LLM finishes generating args
  ↓ isStreaming = false
  ↓
Server tool handler executes
  ↓ isPending = true
  ↓
Server returns result
  ↓ isPending = false
  ↓ props = full data from structuredContent
```

### Key States

| State | `isPending` | `isStreaming` | `partialToolInput` | `props` |
|-------|-------------|--------------|-------------------|---------|
| Not started | `true` | `false` | `null` | `{}` |
| Streaming args | `true` | `true` | `Partial<TProps>` (growing) | `{}` |
| Executing tool | `true` | `false` | Last partial value or `null` | `{}` |
| Complete | `false` | `false` | `null` | Full props |

> **Tip:** Check `partialToolInput` presence (not just `isStreaming`) to detect when any data has arrived. The pattern `isPending && !isStreaming && !partialToolInput` means the widget is waiting before any streaming began.

---

## Server-Side Streaming Setup

**No special server code is needed.** Streaming of tool arguments is handled entirely by the MCP protocol and the LLM client — your server tool handler returns a normal `widget()` response.

### How It Works

1. The client connects to your MCP server via streamable HTTP transport.
2. When the LLM calls a tool, it **streams the JSON arguments** token by token.
3. The host sends `ui/notifications/tool-input-partial` notifications as the LLM generates each chunk.
4. mcp-use intercepts these partial arguments and delivers them to the widget's `useWidget()` hook as `partialToolInput`.
5. Once the LLM finishes generating arguments (signaled by a `tool-input` notification), `isStreaming` becomes `false` and your server tool handler executes normally.

The server tool handler never sees partial arguments — it only runs after the full tool input is assembled. Everything that powers `partialToolInput` and `isStreaming` on the client happens at the protocol layer via the `ui/notifications/tool-input-partial` MCP notification.

### Example: A Normal Tool Handler

```typescript
import { MCPServer, widget } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "summarize-server",
  version: "1.0.0",
});

server.tool(
  {
    name: "summarize",
    description: "Summarize a topic",
    schema: z.object({
      title: z.string(),
      body: z.string(),
      tags: z.array(z.string()),
    }),
    widget: {
      name: "summary-card",
      invoking: "Generating summary...",
      invoked: "Summary ready",
    },
  },
  async ({ title, body, tags }) => {
    // No streaming setup — just return a widget response.
    // The client already received partialToolInput while
    // the LLM was streaming { title, body, tags }.
    return widget({
      props: { title, body, tags },
      message: `Summary: ${title}`,
    });
  }
);
```

> **Key takeaway:** If your widget supports streaming preview, you only need client-side code (`useWidget()` with `isStreaming` / `partialToolInput`). The server side is unchanged.

---

## `isStreaming` and `partialToolInput`

These two values from `useWidget()` are the core of streaming preview:

```typescript
import { useWidget } from "mcp-use/react";

const { isStreaming, partialToolInput, isPending, props, toolInput } = useWidget<MyProps>();
```

- **`isStreaming`** — `true` while the LLM is actively generating tool arguments (i.e. `ui/notifications/tool-input-partial` notifications are arriving)
- **`partialToolInput`** — A `Partial<TProps>` object that grows as more tokens arrive. Fields appear one at a time as the LLM generates them. `null` before streaming starts.
- **`isPending`** — `true` during both streaming and server execution
- **`props`** — The full server-computed data (from `structuredContent`). Empty `{}` during streaming; populated after the server tool handler completes.
- **`toolInput`** — The complete tool call arguments after the LLM finishes generating them (what the model sent). Available once streaming ends. Distinct from `partialToolInput` (which is the growing partial view) and `props` (which is what the server computed and returned).

### `toolInput` vs `partialToolInput` vs `props`

| Value | When available | Contains |
|-------|---------------|----------|
| `partialToolInput` | During streaming (`isStreaming = true`) | Growing partial args from the LLM |
| `toolInput` | After streaming ends | Complete args the model sent to the tool |
| `props` | After server responds | Server-computed data (`structuredContent`) — LLM does not see this |

### Field Arrival Order

`partialToolInput` fields appear in the order the LLM generates them. For a schema like:

```typescript
z.object({
  title: z.string(),
  description: z.string(),
  code: z.string(),
})
```

You might see:
1. `{ title: "Hello" }` — only title so far
2. `{ title: "Hello World", description: "A" }` — description starts
3. `{ title: "Hello World", description: "A simple example", code: "con" }` — code starts
4. `{ title: "Hello World", description: "A simple example", code: "console.log('hello')" }` — all complete

---

## Live Preview Patterns

### Basic Streaming Preview

The real-world pattern reads `props` first (after server completes), then falls back to `partialToolInput` during streaming, giving a seamless experience:

```tsx
import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

const propSchema = z.object({
  title: z.string(),
  body: z.string(),
  author: z.string(),
});

export const widgetMetadata: WidgetMetadata = {
  description: "Article preview with streaming support",
  props: propSchema,
  metadata: { prefersBorder: true, autoResize: true },
};

type ArticleProps = z.infer<typeof propSchema>;

const ArticlePreview: React.FC = () => {
  const { props, isPending, isStreaming, partialToolInput, theme } =
    useWidget<ArticleProps>();

  const isDark = theme === "dark";

  // Prioritize full props, fall back to partial during streaming
  const displayTitle =
    props.title ||
    (partialToolInput as Partial<ArticleProps> | null)?.title ||
    "";
  const displayBody =
    props.body ||
    (partialToolInput as Partial<ArticleProps> | null)?.body ||
    "";
  const displayAuthor =
    props.author ||
    (partialToolInput as Partial<ArticleProps> | null)?.author ||
    "";

  // Loading state before any data arrives
  if (isPending && !isStreaming && !partialToolInput) {
    return (
      <McpUseProvider autoSize>
        <div className="animate-pulse p-4">Loading article...</div>
      </McpUseProvider>
    );
  }

  return (
    <McpUseProvider autoSize>
      <article className={`p-4 ${isDark ? "text-white" : "text-gray-900"}`}>
        <h1 className="text-2xl font-bold">
          {displayTitle || <span className={isDark ? "text-gray-500" : "text-gray-400"}>Untitled</span>}
        </h1>
        {displayAuthor && (
          <p className={`text-sm mt-1 ${isDark ? "text-gray-400" : "text-gray-500"}`}>
            By {displayAuthor}
          </p>
        )}
        <div className="mt-4">
          {displayBody}
          {isStreaming && <span className="animate-pulse text-blue-500">▌</span>}
        </div>
      </article>
    </McpUseProvider>
  );
};
```

### Three-Phase Rendering

A complete pattern handling all lifecycle phases:

```tsx
import { useWidget } from "mcp-use/react";

interface ChartProps {
  title: string;
  data: Array<{ label: string; value: number }>;
  chartType: "bar" | "line" | "pie";
}

const ChartWidget: React.FC = () => {
  const { props, isPending, isStreaming, partialToolInput, theme } = useWidget<ChartProps>();
  const isDark = theme === "dark";

  // Phase 1: Skeleton — nothing received yet
  if (isPending && !partialToolInput) {
    return (
      <div className={`p-6 rounded-lg ${isDark ? "bg-gray-900" : "bg-gray-50"}`}>
        <div className="animate-pulse space-y-4">
          <div className={`h-6 rounded w-1/3 ${isDark ? "bg-gray-800" : "bg-gray-200"}`} />
          <div className={`h-48 rounded ${isDark ? "bg-gray-800" : "bg-gray-200"}`} />
        </div>
      </div>
    );
  }

  // Phase 2: Streaming — partial data available
  if (isStreaming) {
    return (
      <div className={`p-6 rounded-lg ${isDark ? "bg-gray-900" : "bg-gray-50"}`}>
        <h2 className="text-xl font-bold">
          {partialToolInput?.title ?? "Generating chart..."}
        </h2>
        <div className="mt-2 text-sm text-blue-500 animate-pulse">
          ● Streaming data... ({partialToolInput?.data?.length ?? 0} points received)
        </div>
        {partialToolInput?.chartType && (
          <p className={`text-sm mt-1 ${isDark ? "text-gray-400" : "text-gray-500"}`}>
            Type: {partialToolInput.chartType}
          </p>
        )}
        {/* Render partial chart as data arrives */}
        <div className="mt-4 flex items-end gap-1 h-32">
          {(partialToolInput?.data ?? []).map((d, i) => (
            <div
              key={i}
              className="flex-1 bg-blue-400 rounded-t transition-all duration-300"
              style={{ height: `${(d.value / 100) * 100}%` }}
              title={`${d.label}: ${d.value}`}
            />
          ))}
        </div>
      </div>
    );
  }

  // Phase 3: Complete — full props available
  return (
    <div className={`p-6 rounded-lg ${isDark ? "bg-gray-900" : "bg-gray-50"}`}>
      <h2 className="text-xl font-bold">{props.title}</h2>
      <p className={`text-sm ${isDark ? "text-gray-400" : "text-gray-500"}`}>
        {props.chartType} chart · {props.data?.length ?? 0} data points
      </p>
      <div className="mt-4 flex items-end gap-2 h-48">
        {props.data?.map((d, i) => (
          <div key={i} className="flex-1 flex flex-col items-center">
            <div
              className="w-full bg-blue-500 rounded-t transition-all duration-500"
              style={{ height: `${(d.value / Math.max(...props.data.map((x) => x.value))) * 100}%` }}
            />
            <span className={`text-xs mt-1 ${isDark ? "text-gray-400" : "text-gray-500"}`}>
              {d.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
```

---

## Code Preview Streaming

Streaming is especially effective for code generation — users see code appear as the LLM writes it:

```tsx
import { useWidget } from "mcp-use/react";

interface CodeProps {
  code: string;
  language: string;
  filename: string;
}

const StreamingCodeView: React.FC = () => {
  const { props, isPending, isStreaming, partialToolInput, theme } = useWidget<CodeProps>();
  const isDark = theme === "dark";

  const displayCode = isStreaming ? (partialToolInput?.code ?? "") : (props.code ?? "");
  const displayLang = (isStreaming ? partialToolInput?.language : props.language) ?? "text";
  const displayFile = (isStreaming ? partialToolInput?.filename : props.filename) ?? "";

  if (isPending && !partialToolInput) {
    return (
      <div className={`rounded-lg overflow-hidden ${isDark ? "bg-gray-900" : "bg-gray-100"}`}>
        <div className={`px-4 py-2 ${isDark ? "bg-gray-800" : "bg-gray-200"}`}>
          <div className="h-4 w-24 bg-gray-300 dark:bg-gray-700 rounded animate-pulse" />
        </div>
        <div className="p-4 space-y-2 animate-pulse">
          {[80, 60, 90, 40, 70].map((w, i) => (
            <div
              key={i}
              className={`h-4 rounded ${isDark ? "bg-gray-800" : "bg-gray-200"}`}
              style={{ width: `${w}%` }}
            />
          ))}
        </div>
      </div>
    );
  }

  const lines = displayCode.split("\n");

  return (
    <div className={`rounded-lg overflow-hidden ${isDark ? "bg-gray-900" : "bg-gray-100"}`}>
      {/* File header */}
      <div className={`flex items-center justify-between px-4 py-2 ${isDark ? "bg-gray-800" : "bg-gray-200"}`}>
        <div className="flex items-center gap-2">
          {displayFile && (
            <span className={`text-sm font-mono ${isDark ? "text-gray-300" : "text-gray-700"}`}>
              {displayFile}
            </span>
          )}
          <span className={`text-xs px-2 py-0.5 rounded ${isDark ? "bg-gray-700 text-gray-400" : "bg-gray-300 text-gray-600"}`}>
            {displayLang}
          </span>
        </div>
        {isStreaming && (
          <span className="text-xs text-blue-400 animate-pulse flex items-center gap-1">
            <span className="w-2 h-2 bg-blue-400 rounded-full animate-ping" />
            Writing...
          </span>
        )}
      </div>

      {/* Code content */}
      <div className="overflow-x-auto">
        <pre className="p-4 text-sm leading-relaxed">
          <code>
            {lines.map((line, i) => (
              <div key={i} className="flex">
                <span className={`select-none w-8 text-right mr-4 ${isDark ? "text-gray-700" : "text-gray-400"}`}>
                  {i + 1}
                </span>
                <span className={isDark ? "text-gray-200" : "text-gray-800"}>
                  {line}
                </span>
              </div>
            ))}
            {isStreaming && (
              <span className="text-blue-400 animate-pulse ml-12">▌</span>
            )}
          </code>
        </pre>
      </div>
    </div>
  );
};
```

---

## JSON Data Streaming

For structured data, show a progressively building display:

```tsx
import { useWidget } from "mcp-use/react";

interface ReportProps {
  title: string;
  sections: Array<{
    heading: string;
    content: string;
    metrics: Record<string, number>;
  }>;
  generatedAt: string;
}

const StreamingReport: React.FC = () => {
  const { props, isPending, isStreaming, partialToolInput, theme } = useWidget<ReportProps>();
  const isDark = theme === "dark";

  const data = isStreaming ? partialToolInput : props;
  const sections = data?.sections ?? [];

  if (isPending && !partialToolInput) {
    return <div className="animate-pulse p-6">Generating report...</div>;
  }

  return (
    <div className={`p-6 ${isDark ? "bg-gray-900 text-white" : "bg-white text-gray-900"}`}>
      <h1 className="text-2xl font-bold mb-2">{data?.title ?? "Report"}</h1>

      {isStreaming && (
        <div className="text-sm text-blue-500 mb-4 animate-pulse">
          ● Generating... ({sections.length} section{sections.length !== 1 ? "s" : ""} so far)
        </div>
      )}

      <div className="space-y-6">
        {sections.map((section, i) => (
          <div
            key={i}
            className={`p-4 rounded-lg border ${isDark ? "border-gray-700 bg-gray-800" : "border-gray-200 bg-gray-50"} ${
              isStreaming && i === sections.length - 1 ? "border-blue-300 dark:border-blue-700" : ""
            }`}
          >
            <h2 className="font-semibold mb-2">{section.heading}</h2>
            <p className={`text-sm ${isDark ? "text-gray-300" : "text-gray-600"}`}>
              {section.content}
              {isStreaming && i === sections.length - 1 && (
                <span className="text-blue-400 animate-pulse">▌</span>
              )}
            </p>
            {section.metrics && Object.keys(section.metrics).length > 0 && (
              <div className="flex gap-4 mt-3">
                {Object.entries(section.metrics).map(([key, val]) => (
                  <div key={key} className="text-center">
                    <div className="text-lg font-bold">{val}</div>
                    <div className={`text-xs ${isDark ? "text-gray-400" : "text-gray-500"}`}>{key}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {!isStreaming && data?.generatedAt && (
        <p className={`text-xs mt-4 ${isDark ? "text-gray-500" : "text-gray-400"}`}>
          Generated: {data.generatedAt}
        </p>
      )}
    </div>
  );
};
```

---

## Skeleton-to-Content Transitions

Create smooth transitions from skeleton loading states to real content:

```tsx
import { useWidget } from "mcp-use/react";

const SmoothTransition: React.FC = () => {
  const { props, isPending, isStreaming, partialToolInput } = useWidget<{
    title: string;
    items: Array<{ id: string; name: string }>;
  }>();

  const data = isStreaming ? partialToolInput : isPending ? null : props;
  const itemCount = data?.items?.length ?? 3;

  return (
    <div className="p-4 space-y-3">
      {/* Title — skeleton or real */}
      <div className={`transition-all duration-300 ${data?.title ? "" : "animate-pulse"}`}>
        {data?.title ? (
          <h2 className="text-xl font-bold">{data.title}</h2>
        ) : (
          <div className="h-7 bg-gray-200 dark:bg-gray-700 rounded w-1/3" />
        )}
      </div>

      {/* Items — show skeleton placeholders for expected count */}
      <div className="space-y-2">
        {Array.from({ length: Math.max(itemCount, 3) }, (_, i) => {
          const item = data?.items?.[i];
          return (
            <div
              key={i}
              className={`p-3 rounded border transition-all duration-300 ${
                item
                  ? "border-gray-200 dark:border-gray-700"
                  : "border-transparent animate-pulse"
              }`}
            >
              {item ? (
                <span>{item.name}</span>
              ) : (
                <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded" style={{ width: `${40 + Math.random() * 40}%` }} />
              )}
            </div>
          );
        })}
      </div>

      {isStreaming && (
        <div className="flex items-center gap-2 text-sm text-blue-500">
          <div className="flex gap-1">
            <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
            <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
            <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
          </div>
          Loading more...
        </div>
      )}
    </div>
  );
};
```

---

## Performance Considerations

### Avoid Heavy Re-Renders During Streaming

Streaming updates `partialToolInput` rapidly (potentially every few hundred milliseconds). Avoid expensive operations in the render path:

```tsx
// ❌ BAD — sorts and filters on every streaming update
const StreamingWidget: React.FC = () => {
  const { partialToolInput, isStreaming } = useWidget<{ items: Item[] }>();
  const sorted = partialToolInput?.items?.sort((a, b) => a.name.localeCompare(b.name)); // ← sorts on every render
  return <div>{sorted?.map(/* ... */)}</div>;
};

// ✅ GOOD — defer expensive work until streaming completes
import { useMemo } from "react";

const StreamingWidget: React.FC = () => {
  const { props, partialToolInput, isStreaming } = useWidget<{ items: Item[] }>();

  // Only sort when streaming is done and full props are available
  const displayItems = useMemo(() => {
    if (isStreaming) return partialToolInput?.items ?? [];
    return [...(props.items ?? [])].sort((a, b) => a.name.localeCompare(b.name));
  }, [isStreaming, partialToolInput?.items, props.items]);

  return <div>{displayItems.map(/* ... */)}</div>;
};
```

### Keep Streaming UI Lightweight

```tsx
// ❌ BAD — heavy chart library re-renders on every streaming update
{isStreaming && <FullChartLibrary data={partialToolInput?.data} />}

// ✅ GOOD — lightweight preview during streaming, full chart after
{isStreaming ? (
  <SimpleBarPreview data={partialToolInput?.data ?? []} />
) : (
  <FullChartLibrary data={props.data} />
)}
```

### Debounce Optional Updates

For non-critical UI updates during streaming:

```tsx
import { useDeferredValue } from "react";
import { useWidget } from "mcp-use/react";

const StreamingWidget: React.FC = () => {
  const { partialToolInput, isStreaming } = useWidget<{ markdown: string }>();

  // React defers this value during rapid updates
  const deferredContent = useDeferredValue(partialToolInput?.markdown ?? "");

  return (
    <div className={isStreaming ? "opacity-90" : ""}>
      <div dangerouslySetInnerHTML={{ __html: renderMarkdown(deferredContent) }} />
    </div>
  );
};
```
