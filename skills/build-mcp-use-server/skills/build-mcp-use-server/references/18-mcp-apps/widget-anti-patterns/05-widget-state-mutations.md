# Anti-Pattern: Mutating `state` Directly

`state` from `useWidget()` is a snapshot. Mutating it in place is a React rules violation — React does not see the change, the host does not persist it, and the next render re-reads stale data.

## What goes wrong

```tsx
// BAD — mutates the snapshot, nothing persists
function TodoContent() {
  const { state } = useWidget<Props, { todos: Todo[] }>();

  const addTodo = (title: string) => {
    state.todos.push({ id: crypto.randomUUID(), title, done: false }); // mutation, no re-render
  };

  return /* ... */;
}
```

Symptoms:

- The new todo appears once you trigger another re-render, then disappears on reload
- `setState` updaters elsewhere in the tree see the wrong "previous" value
- The host never receives the change — it never makes it past the iframe's React tree

`state` is delivered to your component as a frozen-by-convention object. React's `===` check on render compares references; mutating in place keeps the same reference, so React skips the update.

## Always use `setState`

`setState(updater)` accepts either:

- A new object: `setState({ todos: [...] })`
- An updater function: `setState((prev) => ({ todos: [...(prev?.todos ?? []), newItem] }))`

Prefer the updater function when the new value depends on the previous one — it avoids stale closures.

```tsx
// GOOD — immutable update through setState
function TodoContent() {
  const { state, setState } = useWidget<Props, { todos: Todo[] }>();
  const todos = state?.todos ?? [];

  const addTodo = async (title: string) => {
    await setState((prev) => ({
      todos: [
        ...(prev?.todos ?? []),
        { id: crypto.randomUUID(), title, done: false },
      ],
    }));
  };

  const toggleTodo = async (id: string) => {
    await setState((prev) => ({
      todos: (prev?.todos ?? []).map((t) =>
        t.id === id ? { ...t, done: !t.done } : t
      ),
    }));
  };

  return /* ... */;
}
```

## Common mutation traps

| Mutation | Immutable replacement |
|---|---|
| `state.list.push(item)` | `setState((p) => ({ list: [...(p?.list ?? []), item] }))` |
| `state.list[0].field = "x"` | `setState((p) => ({ list: p.list.map((it, i) => i === 0 ? { ...it, field: "x" } : it) }))` |
| `state.map.set(k, v)` | `setState((p) => ({ map: { ...p.map, [k]: v } }))` |
| `state.list.splice(idx, 1)` | `setState((p) => ({ list: p.list.filter((_, i) => i !== idx) }))` |
| `delete state.obj.key` | `setState((p) => { const { key, ...rest } = p.obj; return { obj: rest }; })` |

## `setState` is async

`setState` returns a promise that resolves once the host has persisted the new state. If the next step depends on the persistence (e.g. you immediately call a tool that reads the state), `await` it:

```tsx
const handleAdd = async () => {
  await setState((prev) => ({ todos: [...(prev?.todos ?? []), newTodo] }));
  // Now the host has the updated state
  await callToolAsync({ todoId: newTodo.id });
};
```

If you do not need to wait, you can fire-and-forget — but never assume `state` has changed synchronously.

## Local state versus widget state

Use **local React `useState`** for ephemeral UI concerns (open modals, hovered row, current input value). Use `useWidget().setState` for things the host should persist across messages and re-renders (selected items, current page, filters).

```tsx
const { state, setState } = useWidget<Props, { selectedId: string | null }>();
const [draftTitle, setDraftTitle] = useState(""); // local — never persisted
```

## Severity

Medium-high. Direct mutation looks like it works in dev (because React strict-mode often hides it) but breaks in production reload, follow-up tool calls, and any host that round-trips state to the model. Treat `state` as deeply read-only.
