# Setup and providers

*Read this when you create a new MCP Apps view and need to bootstrap React with theme, error handling, and model context.*

## Entry point

Place your view component at `views/<name>/view.tsx`. Export a default React component and optional `viewConfig`:

```typescript
import { ThemeProvider } from "mcp-use/react";
import type { ViewConfig } from "mcp-use/react";

export const viewConfig: ViewConfig = {
  displayModes: ["inline", "fullscreen"],
  autoResize: true,
};

export default function MyView() {
  return <ThemeProvider>Hello world</ThemeProvider>;
}
```

The framework calls `bootstrapView()` automatically during dev and production. Do not call it yourself in a normal `view.tsx` file.

### Advanced lifecycle exports

`bootstrapView`, `disposeView`, and the `ViewModule` type are public because generated modules, custom tooling, tests, and HMR integrations use them. They are **normally tooling-managed**, not the recommended authoring path.

`disposeView(): Promise<void>` unmounts the document's React root, then closes the guest MCP App runtime and transport. It is a no-op when nothing is mounted. Use it only for manual embedding or deterministic test/HMR teardown; after it resolves, a custom integration may call `bootstrapView()` to create a fresh runtime.

## ThemeProvider

Wraps your component tree and applies host theme (light/dark), CSS variables, and system fonts.

**Signature:**
```typescript
<ThemeProvider colorScheme?: boolean>
```

**What it provides:**
- CSS custom properties for colors, spacing, typography (host-adapted)
- Dark/light theme toggle support (if host is in auto mode)
- No margin or padding on root; integrate sizing via `viewConfig.autoResize` or `useSendSizeChanged()`

**Always use it:**
```typescript
export default function View() {
  return (
    <ThemeProvider>
      <YourContent />
    </ThemeProvider>
  );
}
```

Do not nest `ThemeProvider` — use one at the root.

## ErrorBoundary

Catches React errors and displays a fallback UI. `bootstrapView()` always wraps the rendered `View` in its own top-level `<ErrorBoundary>` (with no `fallback`/`onError` props) — a view-authored `<ErrorBoundary>` nests inside that one and lets you customize the fallback for a specific subtree instead of the framework's generic error card.

**Signature:**
```typescript
interface ErrorBoundaryProps {
  children: React.ReactNode;
  /** Custom fallback when an error is caught. Receives the error when it's a function. */
  fallback?: React.ReactNode | ((error: Error) => React.ReactNode);
  /** Called with the error and React's componentDidCatch errorInfo. */
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}
```

**Wrap a subtree with a custom fallback:**
```typescript
import { ErrorBoundary, ThemeProvider } from "mcp-use/react";

export default function View() {
  return (
    <ThemeProvider>
      <ErrorBoundary
        fallback={(error) => <p>Chart failed to render: {error.message}</p>}
        onError={(error, errorInfo) => reportToAnalytics(error, errorInfo)}
      >
        <YourContent />
      </ErrorBoundary>
    </ThemeProvider>
  );
}
```

Without a `fallback`, a caught error renders a built-in red error card showing `error.message`. Every catch also logs `[mcp-use] View error:` to the console via `console.error`, in addition to any `onError` callback. Manual wrapping is optional — the framework-injected top-level boundary already catches all unhandled errors — but it lets a chart or widget fail without taking down the whole view.

## ModelContext

Describes the currently visible UI in natural language for the model. Reserved for marking what the user sees; do not use it for business logic.

**Minimal example:**
```typescript
import { ModelContext, ThemeProvider } from "mcp-use/react";

export default function Dashboard() {
  return (
    <ThemeProvider>
      <ModelContext content="Dashboard with 3 charts and 5 alerts">
        {/* content */}
      </ModelContext>
    </ThemeProvider>
  );
}
```

See `references/18-mcp-apps/view-react/04-useviewstate-and-model-context.md` for full semantics.

## ViewConfig mount semantics

The framework normalizes and reads `viewConfig` when it creates the mounted runtime. It does not freeze the exported object, but changing `autoResize` or `displayModes` during HMR does not reconfigure the existing runtime; the framework warns and keeps the original normalized configuration. Reload the iframe, or in a custom tooling flow dispose and bootstrap again, for configuration changes to take effect.

```typescript
export const viewConfig = {
  displayModes: ["inline", "fullscreen"],
  autoResize: true,  // Host resizes iframe to content height
} satisfies ViewConfig;
```

Cross-reference `references/18-mcp-apps/server-surface/03-viewconfig.md` for the full schema.

## Next: rendering the tool result

Once providers are in place, use `useToolContext()` to read the tool invocation and render its structured data. See `references/18-mcp-apps/view-react/02-usetoolcontext.md`.
