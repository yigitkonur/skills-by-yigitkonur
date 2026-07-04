# Anti-Pattern: Rendering Before `isPending` Resolves

`useWidget()` returns partial `props` until the host has delivered the tool result. Reading required fields before that can crash the widget.

## What goes wrong

```tsx
// BAD — TypeError on first render
function MyWidgetContent() {
  const { props } = useWidget<{ items: Item[] }>();
  return (
    <ul>
      {props.items.map((it) => ( // ← `Cannot read properties of undefined (reading 'map')`
        <li key={it.id}>{it.title}</li>
      ))}
    </ul>
  );
}
```

Symptoms:

- Blank widget in the host (error boundary swallowed the throw)
- `Cannot read properties of undefined` in the iframe console
- Works in dev with HMR but fails on first hydration

## The `isPending` contract

`useWidget().isPending` is `true` while:

- The host has delivered tool input but not the tool result yet
- `props` is still `Partial<TProps>`

`isPending` is `false` once result-backed `props` is fully populated. **Always branch on it before reading required props.** `useCallTool()` has its own separate `isPending`.

```tsx
// GOOD — skeleton during pending, real UI after
function MyWidgetContent() {
  const { props, isPending } = useWidget<{ items: Item[] }>();

  if (isPending) {
    return (
      <div className="animate-pulse p-4 space-y-2">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-12 bg-gray-200 dark:bg-gray-700 rounded" />
        ))}
      </div>
    );
  }

  return (
    <ul>
      {props.items?.map((it) => (
        <li key={it.id}>{it.title}</li>
      ))}
    </ul>
  );
}
```

## Skeleton, not spinner

A spinner says "something is happening". A skeleton says "the layout will look like this." Skeletons:

- Reduce perceived latency
- Avoid layout shift when props arrive
- Convey the widget's shape to the user before data lands

Match the skeleton blocks to the real UI — same number of cards, same heights, same grid.

```tsx
// Bad skeleton — no match to actual layout
if (isPending) return <div>Loading...</div>;

// Good skeleton — matches the four-card summary the widget renders
if (isPending) {
  return (
    <div className="grid grid-cols-4 gap-4 p-4 animate-pulse">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="h-20 bg-gray-200 dark:bg-gray-700 rounded-lg" />
      ))}
    </div>
  );
}
```

## Combine with `partialToolInput` for streaming

If your widget consumes a streaming tool (LLM still generating), `isPending` is `true` but `partialToolInput` may already be populated. Render the partial preview rather than the skeleton when both are available:

```tsx
const { props, isPending, isStreaming, partialToolInput } = useWidget<Props>();

if (isPending && !partialToolInput) return <Skeleton />;

const displayValue = isStreaming
  ? (partialToolInput?.field ?? "")
  : (props.field ?? "");
```

## Severity

High. Without an `isPending` guard the widget either never renders or renders broken. This is the single most common bug in mcp-use widgets — every recipe in `widget-recipes/` opens with this guard for a reason.
