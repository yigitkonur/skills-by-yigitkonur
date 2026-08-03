# useViewState and ModelContext

*Read this when you need to persist user choices (filters, selections, drafts) across re-renders, or describe the visible UI to the model.*

## useViewState: model-visible state

Persists a JSON object across the view's lifetime and makes it visible to the model.

**Signature:**
```typescript
useViewState<T extends Record<string, unknown>>(
  defaultState: T | (() => T)
): readonly [T, (state: SetStateAction<T>) => void]
```

**Example:**
```typescript
import { useViewState } from "mcp-use/react";

function Filters() {
  const [state, setState] = useViewState({
    selectedCategory: "all",
    sortBy: "newest",
  });

  return (
    <div>
      <select onChange={(e) => setState({ ...state, selectedCategory: e.target.value })}>
        <option value="all">All categories</option>
        <option value="audio">Audio</option>
      </select>
      <button onClick={() => setState({ ...state, sortBy: "price" })}>
        Sort by price
      </button>
    </div>
  );
}
```

**What the model sees** (the merged snapshot):

Every call to `setState()` sends this JSON to the host:

```json
{
  "selectedCategory": "audio",
  "sortBy": "price",
  "_uiContext": "- Filters\n  - Dashboard visible"
}
```

The `_uiContext` field is reserved for `ModelContext` (see below). `useViewState` automatically filters it out of application state.

**State restoration** (ChatGPT only):

On ChatGPT, `window.openai.widgetState.modelContent` contains the previous state when the view re-mounts. Other MCP Apps hosts keep state for the current iframe lifetime.

## ModelContext: UI description for the model

Describes what the user currently sees in natural language. Serializes to the `_uiContext` field in the merged snapshot.

**Declarative (JSX):**
```typescript
import { useState } from "react";
import { ModelContext } from "mcp-use/react";

function Dashboard() {
  const [selectedTab, setSelectedTab] = useState("overview");

  return (
    <ModelContext content="Dashboard">
      <ModelContext content={`Tab: ${selectedTab} is active`}>
        {selectedTab === "overview" && <OverviewTab />}
      </ModelContext>
    </ModelContext>
  );
}
```

Nesting produces an indented tree:

```text
- Dashboard
  - Tab: overview is active
    - Shows 5 revenue streams
```

There is no exported imperative `modelContext.set/remove` API. Compose `<ModelContext>` nodes declaratively so registration and cleanup follow React lifecycle.

## Combining useViewState and ModelContext

Use both for complete model context:

```typescript
function FilteredResults() {
  const [filters, setFilters] = useViewState({
    category: "all",
    maxPrice: 100,
  });

  return (
    <ModelContext content={`Filters: category=${filters.category}, maxPrice=$${filters.maxPrice}`}>
      <ModelContext content="Search results list visible">
        {/* content */}
      </ModelContext>
    </ModelContext>
  );
}
```

The model sees:

```json
{
  "category": "audio",
  "maxPrice": 50,
  "_uiContext": "- Filters: category=audio, maxPrice=$50\n  - Search results list visible"
}
```

## Reserved key: _uiContext

`useViewState` rejects state objects with a `_uiContext` key. The runtime reserves it for the merged `ModelContext` tree.

```typescript
// This throws:
setState({ _uiContext: "something" });  // Error: reserved key
```

## Gotchas

- **State is JSON-serializable only** → no functions, no circular refs, no `Date` objects (use ISO strings)
- **All components in one view share the same state** → separate views have isolated state
- **ChatGPT state restoration is limited** → only ChatGPT restores via `window.openai.widgetState`; other hosts maintain state only during current iframe session
- **No re-render on incoming `_uiContext` updates** → `ModelContext` updates are sent to the model, not fed back to the view

See `references/18-mcp-apps/view-react/01-setup-and-providers.md` for `<ModelContext>` component and imperative API details.

