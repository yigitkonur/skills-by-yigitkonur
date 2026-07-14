# Fallback for Hosts That Don't Stream

Not every host exposes partial tool arguments. Always implement a working `isPending` fallback so the widget is correct in every environment.

## Hosts that don't stream

| Host | `isStreaming` | `partialToolInput` |
|---|---|---|
| ChatGPT (Apps SDK protocol) | always `false` | always `null` |
| Older MCP Apps clients without SEP-1865 partials | `false` | `null` |
| Hosts in offline / replay mode | `false` | `null` |

In these environments the user sees:

1. `isPending = true`, `partialToolInput = null` (the entire time the tool runs).
2. Then `isPending = false`, `props` populated.

There is no streaming preview at all. Whatever you render in the "skeleton" phase is what the user sees for the entire duration of the tool call.

## Rule — every streaming widget needs a non-streaming render path

The structure below is mandatory. The first branch is what runs on non-streaming hosts (and also covers the "before streaming starts" case on streaming hosts).

```tsx
if (isPending && !partialToolInput) {
  return <SkeletonOrSpinner />;          // Non-streaming host, the whole time
}

if (isStreaming) {
  return <StreamingPreview ... />;       // Streaming host only
}

return <CompleteUI ... />;                // Both, after server returns
```

## Make the skeleton meaningful

Because the `isPending && !partialToolInput` branch can be the *only* thing the user sees on non-streaming hosts, design it as a useful placeholder, not a generic "Loading...". Show:

- The widget's frame, padding, and title slot.
- Skeleton lines matching the eventual content shape.
- A subtle animation so the user knows it's alive.

```tsx
if (isPending && !partialToolInput) {
  return (
    <div className="p-6 rounded-lg bg-gray-50 dark:bg-gray-900">
      <div className="animate-pulse space-y-4">
        <div className="h-6 rounded w-1/3 bg-gray-200 dark:bg-gray-800" />
        <div className="h-48 rounded bg-gray-200 dark:bg-gray-800" />
      </div>
    </div>
  );
}
```

## Don't gate features on `isStreaming`

```tsx
// Bad — non-streaming hosts never see this content.
if (isStreaming) {
  return <Preview data={partialToolInput} />;
}
return <Skeleton />;
```

`isStreaming` is *opt-in enhancement*, not a load-bearing flag. If you build the streaming render and forget the `!isStreaming` complete render, ChatGPT users will see a permanent skeleton.

## Test in both modes

| Test | How |
|---|---|
| Streaming render | MCP Inspector or Claude Desktop with `mcp-use dev`. |
| Non-streaming render | ChatGPT (Developer Mode → Connectors), or stub `partialToolInput` to `null` in tests. |

Both paths must look correct on their own. The streaming preview is a bonus — the non-streaming path is the contract.
