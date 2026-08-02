# Setup and providers

*Read this when you create a new MCP Apps view and need to bootstrap React with theme, error handling, and model context.*

## Entry point

Place your view component at `views/<name>/view.tsx`. Export a default React component and optional `viewConfig`:

```typescript
import { useToolContext, ThemeProvider } from "mcp-use/react";
import type { ViewConfig } from "mcp-use/react";

export const viewConfig: ViewConfig = {
  displayModes: ["inline", "fullscreen"],
  autoResize: true,
};

export default function MyView() {
  return <ThemeProvider>Hello world</ThemeProvider>;
}
```

The framework calls `bootstrapView()` automatically during dev and production. Do not call it yourself in a view file.

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

Catches React errors and displays a fallback UI. Automatically activated by `bootstrapView()`.

**When to wrap manually** (rare):
```typescript
import { ErrorBoundary } from "mcp-use/react";

export default function View() {
  return (
    <ThemeProvider>
      <ErrorBoundary>
        <YourContent />
      </ErrorBoundary>
    </ThemeProvider>
  );
}
```

If a component throws, the boundary logs the error to the host and shows a recovery UI. Manual wrapping is optional; framework-injected boundary catches all unhandled errors.

## ModelContext

Describes the currently visible UI in natural language for the model. Reserved for marking what the user sees; do not use it for business logic.

**Minimal example:**
```typescript
import { ModelContext } from "mcp-use/react";

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

See `references/18-mcp-apps/view-react/04-useviewstate-and-model-context.md` for full semantics and imperative API.

## ViewConfig immutability

The `viewConfig` export is immutable at runtime. Set it once at module load; runtime changes are ignored.

```typescript
export const viewConfig = {
  displayModes: ["inline", "fullscreen"],
  autoResize: true,  // Host resizes iframe to content height
} satisfies ViewConfig;
```

Cross-reference `references/18-mcp-apps/server-surface/03-viewconfig.md` for the full schema.

## Next: rendering the tool result

Once providers are in place, use `useToolContext()` to read the tool invocation and render its structured data. See `references/18-mcp-apps/view-react/02-usetoolcontext.md`.
