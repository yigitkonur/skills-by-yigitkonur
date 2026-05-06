# The Three-Phase Render Pattern

Use three visible phases: **pending fallback**, **preview while pending with partials**, **complete**. In `mcp-use@1.26.0`, there is no separate exposed executing branch after partials arrive.

## The pattern

```tsx
import { useWidget } from "mcp-use/react";

interface ChartProps {
  title: string;
  data: Array<{ label: string; value: number }>;
  chartType: "bar" | "line" | "pie";
}

const ChartWidget: React.FC = () => {
  const { props, isPending, isStreaming, partialToolInput } =
    useWidget<ChartProps>();

  // Phase 1 — Complete: server result has arrived
  if (!isPending) {
    return (
      <div>
        <h2>{props.title}</h2>
        <p>{props.chartType} · {props.data.length} points</p>
        <BarChart data={props.data} />
      </div>
    );
  }

  // Phase 2 — Preview: partial data is available while pending
  if (partialToolInput) {
    return (
      <div>
        <h2>{partialToolInput?.title ?? "Generating chart..."}</h2>
        <p>{partialToolInput?.data?.length ?? 0} points received</p>
        {(partialToolInput?.data ?? []).map((d, i) => (
          <div key={i} style={{ height: `${d.value}%` }} />
        ))}
      </div>
    );
  }

  // Phase 3 — Pending fallback: no partials from this host
  return <Skeleton />;
};
```

## Read source per phase

| Phase | Read from |
|---|---|
| Complete | `props` after `isPending` is false |
| Preview while pending | `partialToolInput`; use `isStreaming` only for UI cues |
| Pending fallback | nothing, or safe defaults |

Don't treat `isStreaming` as the only preview gate. In the current runtime it is computed from whether `partialToolInput` is non-null.

## Variant — fallthrough using nullish OR

If the streaming UI and the complete UI are visually similar, you can fall through to the same render with merged data:

```tsx
const displayTitle = !isPending
  ? props.title
  : partialToolInput?.title ?? "";
const displayBody = !isPending
  ? props.body
  : partialToolInput?.body ?? "";

if (isPending && !partialToolInput) return <Skeleton />;

return (
  <article>
    <h1>{displayTitle || <span className="text-gray-400">Untitled</span>}</h1>
    <p>{displayBody}{isStreaming && <span className="animate-pulse">▌</span>}</p>
  </article>
);
```

This works well when the schema is small and the streaming preview is "the final UI minus some fields".

## Streaming UI cues

- Blinking cursor at the end of streaming text: `{isStreaming && <span className="animate-pulse">▌</span>}`.
- Pulse-indicator with item counter: `● Generating ({n} items)`.
- Dimmed opacity during streaming: `className={isStreaming ? "opacity-90" : ""}`.

These visual cues distinguish "still arriving" from "complete" without requiring the user to look at console output.

## Performance — keep streaming UI cheap

`partialToolInput` can update frequently. Don't sort, filter, or reflow expensively in the preview branch:

```tsx
// Bad — sorts on every streaming update.
const sorted = partialToolInput?.items?.sort(...);

// Good — defer expensive work to the complete phase.
const items = useMemo(() => {
  if (isPending && partialToolInput) return partialToolInput.items ?? [];
  return [...(props.items ?? [])].sort(byName);
}, [isPending, partialToolInput?.items, props.items]);
```

For non-critical updates, `useDeferredValue` lets React skip frames during rapid changes:

```tsx
const deferred = useDeferredValue(partialToolInput?.markdown ?? "");
```

## What about the executing phase?

The pattern above doesn't have an explicit `isPending && !isStreaming && partialToolInput` branch. That's intentional: `mcp-use@1.26.0` keeps the last partial until `tool-result`, so that predicate is not a reliable executing signal.

If you want to distinguish "still generating args" from "server is running", wait for a future runtime signal. For now, render `isPending && partialToolInput` as one preview/waiting phase, and render `isPending && !partialToolInput` as the non-streaming fallback.
