# Widget State Persistence — `state` and `setState`

`useWidget().state` and `setState` are the persistent slot for widget data that must survive across renders, follow-up tool calls, and host reloads. This is **not** React local state — that's `useState`.

```typescript
const { state, setState } = useWidget<P, MyState>();
```

## Persistent vs local state

| Concern | `setState` (persistent) | React `useState` (local) |
|---|---|---|
| Survives reload | Yes | No |
| Visible to the LLM | Yes (hosts may expose it as model context) | No |
| Async to commit | Yes — returns `Promise<void>` | No, synchronous |
| Right for | User preferences, saved selections, favorites, expanded rows you want to keep | Hover state, transient form input, modal open/closed |

## Signature

```typescript
setState(
  state: TState | ((prev: TState | null) => TState)
): Promise<void>;
```

- Either a full replacement value, or a functional updater.
- Always `await` if subsequent work depends on the persisted write being acknowledged.
- `state` is `null` until the user has set it once. Read defensively.

## Persistence wiring (per host)

| Host | Mechanism |
|---|---|
| ChatGPT Apps SDK | `window.openai.setWidgetState()` |
| MCP Apps | Updates local React state plus a `ui/update-model-context` notification to the host |

The hook signature is identical across both — the runtime is hidden.

## Functional updater pattern

Always use a functional updater when reading-then-writing:

```tsx
const addFavorite = async (id: string) => {
  await setState((prev) => ({
    ...prev,
    favorites: [...(prev?.favorites ?? []), id],
  }));
};
```

Reading `state` then calling `setState({ ...state, ... })` is racy — two events can land between the read and the write.

## Combined pattern — local for transient, persistent for durable

```tsx
import { useState } from "react";
import { useWidget } from "mcp-use/react";

const SearchWidget: React.FC = () => {
  const { state, setState, callTool } =
    useWidget<unknown, { history: string[] }>();
  const [query, setQuery] = useState("");        // transient
  const [isExpanded, setIsExpanded] = useState(false); // transient

  const handleSearch = async () => {
    await callTool("search", { query });
    await setState((prev) => ({
      history: [...(prev?.history ?? []), query].slice(-10),
    }));
    setQuery("");
  };

  return (
    <>
      <input value={query} onChange={(e) => setQuery(e.target.value)} />
      <button onClick={handleSearch}>Search</button>
      <button onClick={() => setIsExpanded((v) => !v)}>History</button>
      {isExpanded && <ul>{state?.history?.map((q, i) => <li key={i}>{q}</li>)}</ul>}
    </>
  );
};
```

## Don't put secrets in widget state

Some hosts expose persisted state to the LLM as model context. Do not put auth tokens, raw user PII, or anything you would not show the model.

## Type the second parameter

```typescript
useWidget<MyProps, MyState, MyOutput, MyMeta>();
```

Without the second type parameter, `state` is `UnknownObject | null` and `setState` loses your app-specific shape.
