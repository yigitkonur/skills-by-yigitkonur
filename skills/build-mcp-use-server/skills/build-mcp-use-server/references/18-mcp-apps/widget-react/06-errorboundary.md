# `<ErrorBoundary>` — Render-Error Catch

React error boundary for graceful widget failure. Auto-included by `<McpUseProvider>` — you only reach for this directly when composing providers manually.

```tsx
import { ErrorBoundary } from "mcp-use/react";

<ErrorBoundary>
  <RiskyComponent />
</ErrorBoundary>
```

## Props

| Prop | Type | Required | Description |
|---|---|---|---|
| `children` | `ReactNode` | Yes | The widget content to wrap. |
| `fallback` | `ReactNode \| ((error: Error) => ReactNode)` | No | Custom fallback UI. |
| `onError` | `(error: Error, errorInfo: React.ErrorInfo) => void` | No | Callback after an error is caught. |

## Behavior

- Catches render-time errors thrown by descendants — not async errors, not event-handler throws (catch those manually with `try/catch` in the handler).
- Renders a red-bordered fallback message containing the error description, with dark-mode-aware styling.
- Logs the error and component stack through the package logger, then calls `onError` if provided.
- Prevents a single component crash from blanking the entire widget iframe.

## When to add it manually

The default position is to rely on the boundary that `<McpUseProvider>` installs. Add a second boundary inside the tree only when:

- A specific subtree is known to throw on partial data (e.g. a chart component during streaming).
- You want a localized fallback UI for that subtree without blanking the whole widget.

```tsx
<McpUseProvider autoSize>
  <Header />
  <ErrorBoundary>
    <RiskyChart />        {/* fallback shows here if chart throws */}
  </ErrorBoundary>
  <Footer />
</McpUseProvider>
```

## What it does not do

- It does **not** catch tool-call errors. Use `useCallTool`'s `isError` / `error`, or `try/catch` around `callToolAsync`. See `04-usecalltool-hook.md`.
- It does **not** retry. The fallback is terminal until the next render with new props.
- It does **not** report to telemetry by default — wrap your own logging if needed.
