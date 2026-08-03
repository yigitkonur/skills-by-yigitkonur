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
import { useToolContext } from "mcp-use/react";

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
// WRONG: model-visible state must never contain secrets.
export default function MyView() {
  const [state] = useViewState({ apiKey: "" });

  const handleClick = async () => {
    await fetch("https://api.example.com/data", {
      headers: { "Authorization": `Bearer ${state.apiKey}` },
    });
  };
}
```

**Why:** `useViewState()` is model-visible state — it is sent to the model on every update, through `ui/update-model-context` on MCP Apps hosts or `window.openai.setWidgetState` on ChatGPT (never `_meta`, which is view-only and never reaches the model). Secrets placed there are exposed to the LLM and to the conversation transcript.

**Fix:** Call a server tool to fetch data with authentication. Never expose secrets client-side.

```typescript
// CORRECT
import { useCallTool } from "mcp-use/react";

export default function MyView() {
  const { callTool } = useCallTool("fetch-protected-data");

  const handleClick = async () => {
    // The server tool owns the API key.
    await callTool({});
  };

  return (
    <button type="button" onClick={() => void handleClick()}>
      Fetch protected data
    </button>
  );
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

  return (
    <button
      type="button"
      onClick={() => setState({ ...state, key: "updated" })}
    >
      Update model-visible state
    </button>
  );
}
```

## 4. Missing or Misapplied View CSP

**Anti-pattern:** Browser code in the sandboxed View fetches an external origin that the View resource CSP does not allow.

```typescript
// views/my-view/view.tsx
import { useEffect } from "react";

export default function FetchFromAPI() {
  useEffect(() => {
    void fetch("https://api.example.com/data") // View CSP does not allow this origin.
      .then((response) => response.json())
      .catch((error) => console.error(error));
  }, []);

  return <p>Loading external data...</p>;
}
```

**Why:** The host applies the emitted CSP to the View iframe, so the browser blocks undeclared connections.

**Fix for a View-side request:** Declare the external origin on the tool binding that owns the View resource.

```typescript
// index.ts
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({ name: "data-server", version: "1.0.0" });

export const getData = server.tool(
  {
    name: "get-data",
    description: "Open the data view",
    inputSchema: z.object({}),
    outputSchema: z.object({ endpoint: z.string().url() }),
    view: {
      name: "my-view",
      csp: {
        connectDomains: ["https://api.example.com"],
      },
    },
  },
  async () => ({
    content: [{ type: "text", text: "Opened the data view" }],
    structuredContent: { endpoint: "https://api.example.com/data" },
  })
);

export default server;
```

This CSP permits the sandboxed View to connect to `https://api.example.com`; it does not authorize or restrict `fetch()` inside the Node/server tool callback. If the server performs the external request and returns the data through `structuredContent`, keep credentials server-side and do not add the provider solely to View `connectDomains`.

See `references/18-mcp-apps/server-surface/05-csp-metadata.md` for View CSP fields and merge rules.

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
    // The resolved value is the full successful tool result.
    console.log(result.structuredContent);
  };

  if (error) return <p>Error: {error.message}</p>;
  if (!data) return <button onClick={() => void handleSearch("mcp")}>Search</button>;
  return <pre>{JSON.stringify(data.structuredContent, null, 2)}</pre>;
}
```

`callTool()` and `data` expose the full successful result envelope. Read the schema-typed payload from `structuredContent`; `content` and `_meta` remain available separately.

## 6. Mutating State Outside Hooks

**Anti-pattern:** Mutating view state via direct object assignment.

```typescript
// WRONG
interface Item {
  id: string;
  label: string;
}

const [state] = useViewState<{ items: Item[] }>({ items: [] });

const addItem = (item: Item) => {
  state.items.push(item); // Direct mutation; not propagated to the model.
};
```

**Fix:** Use `setState()` to update.

```typescript
// CORRECT
import { useViewState } from "mcp-use/react";

interface Item {
  id: string;
  label: string;
}

export default function ItemList() {
  const [state, setState] = useViewState<{ items: Item[] }>({ items: [] });

  const addItem = (item: Item) => {
    setState((previous) => ({
      ...previous,
      items: [...previous.items, item],
    }));
  };

  return (
    <button
      type="button"
      onClick={() => addItem({ id: crypto.randomUUID(), label: "New item" })}
    >
      Add item ({state.items.length})
    </button>
  );
}
```

Every `setState()` call sends the complete state snapshot to the model — via `ui/update-model-context` on MCP Apps hosts, or `window.openai.setWidgetState` on ChatGPT. Not `_meta`; `_meta` is view-only and never reaches the model.

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
import { useToolContext } from "mcp-use/react";

export default function LoadingGuard() {
  const ctx = useToolContext();
  if (ctx.status === "pending") return <p>Loading</p>;
  return null;
}
```

The `status` field is latched: once it transitions to `ready` or `error`, it stays there for the view's lifetime.

## Summary Checklist

- [ ] Always check `useToolContext().status` before accessing output
- [ ] Never store secrets in `useViewState()`
- [ ] Never call `window.openai` directly
- [ ] Declare CSP for external origins used by browser code in the sandboxed View
- [ ] Do not treat View CSP as authorization for server-side `fetch()`
- [ ] Use `useCallTool()`, never HTTP `fetch()`, to invoke MCP tools
- [ ] Mutate state only via `setState()`, never direct assignment
- [ ] Guard on `status`, not on a non-existent `isPending` flag
