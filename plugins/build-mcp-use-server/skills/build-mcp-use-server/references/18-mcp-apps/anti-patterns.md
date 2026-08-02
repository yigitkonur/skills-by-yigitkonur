# Anti-Patterns in MCP Apps Views

*Read this when building views to avoid common pitfalls.*

## 1. Assuming Tool Context Always Ready

**Anti-pattern:** Accessing `useToolContext()` without checking `status`.

```typescript
// WRONG
export default function SearchResults() {
  const ctx = useToolContext<"search">();
  return <ul>{ctx.toolOutput.results.map(...)}</ul>; // crashes if pending
}
```

**Fix:** Guard on `status` and use latched lifecycle.

```typescript
// CORRECT
export default function SearchResults() {
  const ctx = useToolContext<"search">();
  
  if (ctx.status === "pending") return <p>Searching...</p>;
  if (ctx.status === "error") return <p>Error: {ctx.error.message}</p>;
  
  // status === "ready"
  return <ul>{ctx.toolOutput.results.map(r => <li key={r.id}>{r.name}</li>)}</ul>;
}
```

The `status` field transitions once: `pending` → `ready` or `error`. It does not toggle back.

## 2. Secrets in View State

**Anti-pattern:** Storing API keys, tokens, or private data in `useViewState()`.

```typescript
// WRONG
export default function MyView() {
  const [apiKey, setApiKey] = useViewState<string>("");
  
  const handleClick = async () => {
    const result = await fetch("https://api.example.com/data", {
      headers: { "Authorization": `Bearer ${apiKey}` },
    });
  };
}
```

**Why:** View state is model-visible and travels in `_meta.ui` to the LLM. Secrets are exposed.

**Fix:** Call a server tool to fetch data with authentication. Never expose secrets client-side.

```typescript
// CORRECT
export default function MyView() {
  const { callTool } = useCallTool("fetch-protected-data");
  
  const handleClick = async () => {
    // Server tool owns the API key
    const result = await callTool({});
  };
}
```

## 3. Direct `window.openai` Access

**Anti-pattern:** Calling `window.openai` APIs directly.

```typescript
// WRONG
if (window.openai?.setWidgetState) {
  window.openai.setWidgetState({ key: "value" });
}
```

**Why:** Only ChatGPT has `window.openai`; MCP Apps hosts don't. The mcp-use hooks abstract both.

**Fix:** Use mcp-use hooks only.

```typescript
// CORRECT
import { useViewState } from "mcp-use/react";

export default function MyView() {
  const [state, setState] = useViewState({ key: "value" });
  
  // Updates are sent to all hosts via the same mechanism
  setState({ key: "updated" });
}
```

## 4. Missing or Wrong CSP

**Anti-pattern:** Fetching from an external API without declaring CSP.

```typescript
// views/my-view/view.tsx
export default function FetchFromAPI() {
  useEffect(() => {
    fetch("https://api.example.com/data") // CSP not declared
      .then(r => r.json())
      .catch(err => console.error(err));
  }, []);
}
```

**Why:** Browser CSP blocks the fetch; view silently fails.

**Fix:** Declare CSP on the server-side tool binding.

```typescript
// Server (index.ts)
export const getData = server.tool(
  {
    name: "get-data",
    description: "Fetch data from API",
    outputSchema: z.object({ data: z.any() }),
    view: {
      name: "data-view",
      csp: {
        connectDomains: ["https://api.example.com"],
      },
    },
  },
  async () => ({
    content: [{ type: "text", text: "Data fetched" }],
    structuredContent: { data: await fetch("...").then(r => r.json()) },
  })
);
```

See `references/18-mcp-apps/server-surface/05-csp-metadata.md` for CSP merge rules.

## 5. Fetching Instead of useCallTool

**Anti-pattern:** Calling another tool via HTTP fetch.

```typescript
// WRONG
const handleSearch = async (query: string) => {
  const res = await fetch("http://localhost:3000/mcp/tools/search", {
    method: "POST",
    body: JSON.stringify({ query }),
  });
  const result = await res.json();
  setResults(result);
};
```

**Why:** Hardcoded URLs, no error handling, no typed results, tool not in call trace.

**Fix:** Use `useCallTool()`.

```typescript
// CORRECT
import { useCallTool } from "mcp-use/react";

export default function SearchView() {
  const { callTool, data, error } = useCallTool("search");
  
  const handleSearch = async (query: string) => {
    const result = await callTool({ query });
    // result is typed by tool's outputSchema
  };
  
  if (error) return <p>Error: {error.message}</p>;
  return <Results data={data} />;
}
```

## 6. Mutating State Outside Hooks

**Anti-pattern:** Mutating view state via direct object assignment.

```typescript
// WRONG
const [state, setState] = useViewState({ items: [] });

const addItem = (item) => {
  state.items.push(item);  // Direct mutation; not propagated to model
  // Model doesn't see this change
};
```

**Fix:** Use `setState()` to update.

```typescript
// CORRECT
const [state, setState] = useViewState({ items: [] });

const addItem = (item) => {
  setState((prev) => ({
    ...prev,
    items: [...prev.items, item],
  }));
  // Now model sees the updated state
};
```

All `useViewState()` updates travel to `_meta.ui` for the model to observe.

## 7. Guarding on `isPending` (v1 Anti-Pattern)

**Anti-pattern:** Checking a boolean `isPending` flag to guard UI.

```typescript
// WRONG (v1 style, doesn't exist in v2)
const ctx = useToolContext();
if (ctx.isPending) return <p>Loading</p>;
// This field doesn't exist in v2
```

**Fix:** Check the `status` field directly.

```typescript
// CORRECT (v2)
const ctx = useToolContext();
if (ctx.status === "pending") return <p>Loading</p>;
```

The `status` field is latched: once it transitions to `ready` or `error`, it stays there for the view's lifetime.

## Summary Checklist

- [ ] Always check `useToolContext().status` before accessing output
- [ ] Never store secrets in `useViewState()`
- [ ] Never call `window.openai` directly
- [ ] Always declare CSP for external APIs in the tool binding
- [ ] Use `useCallTool()`, never fetch() for tool calls
- [ ] Mutate state only via `setState()`, never direct assignment
- [ ] Guard on `status`, not on a non-existent `isPending` flag
